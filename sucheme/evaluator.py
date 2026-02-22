"""
Evaluator for sucheme.

Implements R5RS evaluation with:
- Tail-call optimization (TCO) via trampoline
- Proper tail recursion
- Hygienic macros (syntax-rules)
- call/cc (continuations)
- Multiple values (values / call-with-values)
- Dynamic wind
"""

from __future__ import annotations

import sys
from typing import Any

from sucheme.types import (
    NIL, VOID, TRUE, FALSE,
    Symbol, Boolean, Pair, Vector, Char, SchemeString,
    LambdaProcedure, PrimitiveProcedure, MacroProcedure, ContinuationProcedure,
    Values,
    TailCall, TailApply,
    ContinuationException,
    SchemeError, SchemeSyntaxError, SchemeRuntimeError, SchemeTypeError,
    SchemeNameError, SchemeArityError,
    scheme_bool, list_to_scheme, scheme_to_list, cons,
    VOID as _VOID,
)
from sucheme.environment import Environment

# Recursion limit guard
sys.setrecursionlimit(10000)

# Global counter for continuation IDs
_cont_id = 0


def _next_cont_id() -> int:
    global _cont_id
    _cont_id += 1
    return _cont_id


# Dynamic wind stack (list of (before, after) thunks)
_wind_stack: list[tuple[Any, Any]] = []


def eval_expr(expr: Any, env: Environment) -> Any:
    """Evaluate an expression with TCO via trampoline."""
    while True:
        result = _eval_one(expr, env)
        if isinstance(result, TailCall):
            expr = result.expr
            env = result.env
        elif isinstance(result, TailApply):
            proc = result.proc
            args = result.args
            if isinstance(proc, LambdaProcedure):
                env = proc.env.extend(proc.params, args)
                # Evaluate body in sequence, tail-call last
                for body_expr in proc.body[:-1]:
                    eval_expr(body_expr, env)
                expr = proc.body[-1]
                # continue loop (TCO)
            elif isinstance(proc, PrimitiveProcedure):
                return proc(*args)
            elif isinstance(proc, ContinuationProcedure):
                return proc(*args)
            elif callable(proc):
                return proc(*args)
            else:
                raise SchemeTypeError(f"Not a procedure: {proc!r}")
        else:
            return result


def _eval_one(expr: Any, env: Environment) -> Any:
    """Single-step evaluation. May return TailCall/TailApply for TCO."""
    # Self-evaluating
    if expr is NIL or expr is VOID or expr is TRUE or expr is FALSE:
        return expr
    if isinstance(expr, (int, float, complex)):
        return expr
    from fractions import Fraction
    if isinstance(expr, Fraction):
        return expr
    if isinstance(expr, (SchemeString, Char, Vector, Boolean)):
        return expr

    # Variable reference
    if isinstance(expr, Symbol):
        return env.lookup(expr.name)

    # Not a pair => error
    if not isinstance(expr, Pair):
        raise SchemeTypeError(f"Cannot evaluate: {expr!r}")

    # List form
    head = expr.car
    args_expr = expr.cdr

    # Special forms
    if isinstance(head, Symbol):
        name = head.name

        if name == "quote":
            return _get_arg(args_expr, 0)

        if name == "if":
            return _eval_if(args_expr, env)

        if name == "cond":
            return _eval_cond(args_expr, env)

        if name == "and":
            return _eval_and(args_expr, env)

        if name == "or":
            return _eval_or(args_expr, env)

        if name == "when":
            return _eval_when(args_expr, env)

        if name == "unless":
            return _eval_unless(args_expr, env)

        if name == "lambda":
            return _eval_lambda(args_expr, env)

        if name == "define":
            return _eval_define(args_expr, env)

        if name == "define-syntax":
            return _eval_define_syntax(args_expr, env)

        if name == "let-syntax":
            return _eval_let_syntax(args_expr, env, False)

        if name == "letrec-syntax":
            return _eval_let_syntax(args_expr, env, True)

        if name == "set!":
            return _eval_set(args_expr, env)

        if name == "begin":
            return _eval_begin(args_expr, env)

        if name == "let":
            return _eval_let(args_expr, env)

        if name == "let*":
            return _eval_let_star(args_expr, env)

        if name == "letrec":
            return _eval_letrec(args_expr, env)

        if name == "letrec*":
            return _eval_letrec_star(args_expr, env)

        if name == "do":
            return _eval_do(args_expr, env)

        if name == "delay":
            return _eval_delay(args_expr, env)

        if name == "delay-force":
            return _eval_delay_force(args_expr, env)

        if name == "force":
            arg = eval_expr(_get_arg(args_expr, 0), env)
            return _force_promise(arg)

        if name == "quasiquote":
            return _eval_quasiquote(_get_arg(args_expr, 0), env, 0)

        if name == "define-record-type":
            return _eval_define_record_type(args_expr, env)

        if name == "values":
            vals = [eval_expr(a, env) for a in args_expr]
            if len(vals) == 1:
                return vals[0]
            return Values(*vals)

        if name == "call-with-values":
            producer = eval_expr(_get_arg(args_expr, 0), env)
            consumer = eval_expr(_get_arg(args_expr, 1), env)
            result = _apply(producer, [])
            if isinstance(result, Values):
                return TailApply(consumer, result.values)
            return TailApply(consumer, [result])

        if name == "receive":  # SRFI-8 style
            return _eval_receive(args_expr, env)

    # Macro application check
    if isinstance(head, Symbol):
        try:
            val = env.lookup(head.name)
            if isinstance(val, MacroProcedure):
                expanded = _macro_expand(val, expr)
                return TailCall(expanded, env)
        except SchemeNameError:
            pass

    # Procedure application
    proc = eval_expr(head, env)
    if isinstance(proc, MacroProcedure):
        expanded = _macro_expand(proc, expr)
        return TailCall(expanded, env)

    args = [eval_expr(a, env) for a in args_expr]
    return TailApply(proc, args)


# ---------------------------------------------------------------------------
# Special form helpers
# ---------------------------------------------------------------------------

def _get_arg(args: Any, idx: int) -> Any:
    """Get the nth element of a list."""
    cur = args
    for _ in range(idx):
        if not isinstance(cur, Pair):
            raise SchemeSyntaxError(f"Too few arguments")
        cur = cur.cdr
    if not isinstance(cur, Pair):
        raise SchemeSyntaxError(f"Too few arguments")
    return cur.car


def _args_to_list(args: Any) -> list:
    result = []
    cur = args
    while isinstance(cur, Pair):
        result.append(cur.car)
        cur = cur.cdr
    return result


def _eval_if(args: Any, env: Environment) -> Any:
    lst = _args_to_list(args)
    if len(lst) < 2:
        raise SchemeSyntaxError("if: too few expressions")
    cond_val = eval_expr(lst[0], env)
    if cond_val is not FALSE:  # everything except #f is true
        return TailCall(lst[1], env)
    elif len(lst) >= 3:
        return TailCall(lst[2], env)
    else:
        return VOID


def _eval_cond(args: Any, env: Environment) -> Any:
    cur = args
    while isinstance(cur, Pair):
        clause = cur.car
        cur = cur.cdr
        if not isinstance(clause, Pair):
            raise SchemeSyntaxError("cond: bad clause")
        test = clause.car
        body = clause.cdr

        if isinstance(test, Symbol) and test.name == "else":
            # else clause
            if body is NIL:
                return VOID
            return _eval_sequence_tco(body, env)

        test_val = eval_expr(test, env)
        if test_val is not FALSE:
            if body is NIL:
                return test_val
            # => clause
            if isinstance(body, Pair) and isinstance(body.car, Symbol) and body.car.name == "=>":
                proc = eval_expr(_get_arg(body, 1), env)
                return TailApply(proc, [test_val])
            return _eval_sequence_tco(body, env)
    return VOID


def _eval_and(args: Any, env: Environment) -> Any:
    cur = args
    if cur is NIL:
        return TRUE
    while isinstance(cur, Pair):
        val = eval_expr(cur.car, env)
        if val is FALSE:
            return FALSE
        if cur.cdr is NIL:
            return val
        cur = cur.cdr
    return TRUE


def _eval_or(args: Any, env: Environment) -> Any:
    cur = args
    if cur is NIL:
        return FALSE
    while isinstance(cur, Pair):
        val = eval_expr(cur.car, env)
        if val is not FALSE:
            if cur.cdr is NIL:
                return val
            return val
        cur = cur.cdr
    return FALSE


def _eval_when(args: Any, env: Environment) -> Any:
    test = eval_expr(_get_arg(args, 0), env)
    if test is not FALSE:
        return _eval_sequence_tco(args.cdr, env)
    return VOID


def _eval_unless(args: Any, env: Environment) -> Any:
    test = eval_expr(_get_arg(args, 0), env)
    if test is FALSE:
        return _eval_sequence_tco(args.cdr, env)
    return VOID


def _eval_lambda(args: Any, env: Environment) -> Any:
    params = _get_arg(args, 0)
    body = _args_to_list(args.cdr)
    if not body:
        raise SchemeSyntaxError("lambda: empty body")
    return LambdaProcedure(params, body, env)


def _eval_define(args: Any, env: Environment) -> Any:
    first = _get_arg(args, 0)
    if isinstance(first, Symbol):
        # (define name expr)
        if args.cdr is NIL:
            env.define(first.name, VOID)
        else:
            val = eval_expr(_get_arg(args, 1), env)
            if isinstance(val, LambdaProcedure) and not val.name:
                val.name = first.name
            env.define(first.name, val)
    elif isinstance(first, Pair):
        # (define (name . params) body...)
        name = first.car
        params = first.cdr
        body = _args_to_list(args.cdr)
        if not body:
            raise SchemeSyntaxError("define: empty body")
        proc = LambdaProcedure(params, body, env, name=name.name)
        env.define(name.name, proc)
    else:
        raise SchemeSyntaxError(f"define: bad first argument: {first!r}")
    return VOID


def _eval_set(args: Any, env: Environment) -> Any:
    name = _get_arg(args, 0)
    if not isinstance(name, Symbol):
        raise SchemeSyntaxError(f"set!: not a symbol: {name!r}")
    val = eval_expr(_get_arg(args, 1), env)
    env.set(name.name, val)
    return VOID


def _eval_begin(args: Any, env: Environment) -> Any:
    if args is NIL:
        return VOID
    return _eval_sequence_tco(args, env)


def _eval_sequence_tco(exprs: Any, env: Environment) -> Any:
    """Evaluate a sequence, returning TailCall for the last."""
    cur = exprs
    while isinstance(cur, Pair):
        if cur.cdr is NIL:
            return TailCall(cur.car, env)
        eval_expr(cur.car, env)
        cur = cur.cdr
    return VOID


def _eval_let(args: Any, env: Environment) -> Any:
    first = _get_arg(args, 0)
    # Named let: (let name ((var val) ...) body...)
    if isinstance(first, Symbol):
        name = first.name
        bindings = _get_arg(args, 1)
        body = _args_to_list(args.cdr.cdr)
        params = []
        vals = []
        cur = bindings
        while isinstance(cur, Pair):
            b = cur.car
            params.append(b.car)
            vals.append(eval_expr(_get_arg(b, 1), env))
            cur = cur.cdr
        child = Environment(parent=env)
        param_list = list_to_scheme(params)
        proc = LambdaProcedure(param_list, body, child, name=name)
        child.define(name, proc)
        return TailApply(proc, vals)

    # Normal let
    bindings = first
    body = _args_to_list(args.cdr)
    child = Environment(parent=env)
    cur = bindings
    while isinstance(cur, Pair):
        b = cur.car
        varname = b.car.name
        val = eval_expr(_get_arg(b, 1), env)
        child.define(varname, val)
        cur = cur.cdr
    if not body:
        raise SchemeSyntaxError("let: empty body")
    for expr in body[:-1]:
        eval_expr(expr, child)
    return TailCall(body[-1], child)


def _eval_let_star(args: Any, env: Environment) -> Any:
    bindings = _get_arg(args, 0)
    body = _args_to_list(args.cdr)
    child = Environment(parent=env)
    cur = bindings
    while isinstance(cur, Pair):
        b = cur.car
        varname = b.car.name
        val = eval_expr(_get_arg(b, 1), child)
        child.define(varname, val)
        cur = cur.cdr
    if not body:
        raise SchemeSyntaxError("let*: empty body")
    for expr in body[:-1]:
        eval_expr(expr, child)
    return TailCall(body[-1], child)


def _eval_letrec(args: Any, env: Environment) -> Any:
    bindings = _get_arg(args, 0)
    body = _args_to_list(args.cdr)
    child = Environment(parent=env)
    # First, define all variables as undefined
    names = []
    exprs = []
    cur = bindings
    while isinstance(cur, Pair):
        b = cur.car
        names.append(b.car.name)
        exprs.append(_get_arg(b, 1))
        child.define(b.car.name, VOID)
        cur = cur.cdr
    # Then evaluate and set
    for n, e in zip(names, exprs):
        val = eval_expr(e, child)
        child.set(n, val)
    if not body:
        raise SchemeSyntaxError("letrec: empty body")
    for expr in body[:-1]:
        eval_expr(expr, child)
    return TailCall(body[-1], child)


def _eval_letrec_star(args: Any, env: Environment) -> Any:
    bindings = _get_arg(args, 0)
    body = _args_to_list(args.cdr)
    child = Environment(parent=env)
    cur = bindings
    while isinstance(cur, Pair):
        b = cur.car
        varname = b.car.name
        child.define(varname, VOID)
        val = eval_expr(_get_arg(b, 1), child)
        child.set(varname, val)
        cur = cur.cdr
    if not body:
        raise SchemeSyntaxError("letrec*: empty body")
    for expr in body[:-1]:
        eval_expr(expr, child)
    return TailCall(body[-1], child)


def _eval_do(args: Any, env: Environment) -> Any:
    """(do ((var init step) ...) (test expr...) body...)"""
    var_specs = _args_to_list(_get_arg(args, 0))
    term_clause = _get_arg(args, 1)
    body = _args_to_list(args.cdr.cdr)

    child = Environment(parent=env)
    # Initialize variables
    vars_info = []
    for spec in var_specs:
        var = spec.car.name
        init_val = eval_expr(_get_arg(spec, 1), env)
        step = _get_arg(spec, 2) if isinstance(spec.cdr.cdr, Pair) else spec.car
        child.define(var, init_val)
        vars_info.append((var, step))

    test_expr = term_clause.car
    result_exprs = _args_to_list(term_clause.cdr)

    while True:
        test_val = eval_expr(test_expr, child)
        if test_val is not FALSE:
            if not result_exprs:
                return VOID
            for e in result_exprs[:-1]:
                eval_expr(e, child)
            return TailCall(result_exprs[-1], child)
        # Execute body
        for b in body:
            eval_expr(b, child)
        # Step
        new_vals = [eval_expr(step, child) for _, step in vars_info]
        for (var, _), val in zip(vars_info, new_vals):
            child.set(var, val)


class _Promise:
    """Lazy promise (delay/force)."""

    def __init__(self, thunk: Any, is_lazy: bool = False) -> None:
        self._thunk = thunk
        self._value = None
        self._forced = False
        self._is_lazy = is_lazy

    def force(self) -> Any:
        if not self._forced:
            if callable(self._thunk):
                val = self._thunk()
            else:
                val = self._thunk
            # Handle iterative force (delay-force)
            while isinstance(val, _Promise) and val._is_lazy:
                if val._forced:
                    val = val._value
                else:
                    val = val.force()
            self._value = val
            self._forced = True
        return self._value

    def __repr__(self) -> str:
        return "#<promise>"


def _eval_delay(args: Any, env: Environment) -> Any:
    expr = _get_arg(args, 0)
    return _Promise(lambda: eval_expr(expr, env))


def _eval_delay_force(args: Any, env: Environment) -> Any:
    expr = _get_arg(args, 0)
    p = _Promise(lambda: eval_expr(expr, env), is_lazy=True)
    return p


def _force_promise(val: Any) -> Any:
    if isinstance(val, _Promise):
        return val.force()
    return val


def _eval_quasiquote(tmpl: Any, env: Environment, depth: int) -> Any:
    if isinstance(tmpl, Pair):
        if isinstance(tmpl.car, Symbol):
            if tmpl.car.name == "quasiquote":
                return cons(Symbol("quasiquote"),
                            cons(_eval_quasiquote(_get_arg(tmpl, 1), env, depth + 1), NIL))
            if tmpl.car.name == "unquote":
                if depth == 0:
                    return eval_expr(_get_arg(tmpl, 1), env)
                return cons(Symbol("unquote"),
                            cons(_eval_quasiquote(_get_arg(tmpl, 1), env, depth - 1), NIL))
            if tmpl.car.name == "unquote-splicing":
                raise SchemeSyntaxError("unquote-splicing: invalid context")

        # Check for ,@ in car
        if isinstance(tmpl.car, Pair) and isinstance(tmpl.car.car, Symbol) \
                and tmpl.car.car.name == "unquote-splicing" and depth == 0:
            spliced = eval_expr(_get_arg(tmpl.car, 1), env)
            rest = _eval_quasiquote(tmpl.cdr, env, depth)
            # append spliced to rest
            return _append_lists(spliced, rest)

        return cons(
            _eval_quasiquote(tmpl.car, env, depth),
            _eval_quasiquote(tmpl.cdr, env, depth),
        )
    if isinstance(tmpl, Vector):
        items = [_eval_quasiquote(x, env, depth) for x in tmpl.data]
        return Vector(items)
    return tmpl


def _append_lists(a: Any, b: Any) -> Any:
    if a is NIL:
        return b
    if not isinstance(a, Pair):
        raise SchemeTypeError(f"unquote-splicing: not a list: {a!r}")
    return cons(a.car, _append_lists(a.cdr, b))


def _eval_define_record_type(args: Any, env: Environment) -> Any:
    """(define-record-type name (constructor field...) pred (field accessor [modifier])...)"""
    lst = _args_to_list(args)
    name = lst[0].name
    ctor_spec = lst[1]
    pred_name = lst[2].name
    field_specs = lst[3:]

    ctor_name = ctor_spec.car.name
    ctor_fields = [x.name for x in _args_to_list(ctor_spec.cdr)]

    all_fields = []
    for spec in field_specs:
        spec_list = _args_to_list(spec)
        field = spec_list[0].name
        accessor = spec_list[1].name
        modifier = spec_list[2].name if len(spec_list) > 2 else None
        all_fields.append((field, accessor, modifier))

    # Create record class
    all_field_names = [f for f, _, _ in all_fields]

    class Record:
        _type_name = name
        _fields = all_field_names

        def __init__(self, **kwargs: Any) -> None:
            self._data = kwargs

        def __repr__(self) -> str:
            return f"#<{self._type_name}>"

    Record.__name__ = name
    Record.__qualname__ = name

    # Constructor
    def make_record(*args: Any) -> Record:
        if len(args) != len(ctor_fields):
            raise SchemeArityError(
                f"{ctor_name}: expected {len(ctor_fields)} args, got {len(args)}"
            )
        r = Record(**dict(zip(ctor_fields, args)))
        return r

    env.define(ctor_name, PrimitiveProcedure(make_record, ctor_name))

    # Predicate
    record_type = Record

    def pred(obj: Any) -> Boolean:
        return scheme_bool(isinstance(obj, record_type))

    env.define(pred_name, PrimitiveProcedure(pred, pred_name))

    # Accessors and mutators
    for field, accessor, modifier in all_fields:
        f = field  # capture

        def make_accessor(fn: str) -> PrimitiveProcedure:
            def acc(obj: Any) -> Any:
                if not isinstance(obj, record_type):
                    raise SchemeTypeError(f"{accessor}: not a {name}")
                return obj._data[fn]
            return PrimitiveProcedure(acc, accessor)

        env.define(accessor, make_accessor(f))

        if modifier:
            def make_modifier(fn: str) -> PrimitiveProcedure:
                def mod(obj: Any, val: Any) -> Any:
                    if not isinstance(obj, record_type):
                        raise SchemeTypeError(f"{modifier}: not a {name}")
                    obj._data[fn] = val
                    return VOID
                return PrimitiveProcedure(mod, modifier)
            env.define(modifier, make_modifier(f))

    return VOID


def _eval_receive(args: Any, env: Environment) -> Any:
    """(receive formals expression body...) - SRFI-8"""
    formals = _get_arg(args, 0)
    expr = _get_arg(args, 1)
    body = _args_to_list(args.cdr.cdr)
    val = eval_expr(expr, env)
    if isinstance(val, Values):
        vals = val.values
    else:
        vals = [val]
    child = env.extend(formals, vals)
    for e in body[:-1]:
        eval_expr(e, child)
    return TailCall(body[-1], child)


# ---------------------------------------------------------------------------
# Macro system (syntax-rules)
# ---------------------------------------------------------------------------

class SyntaxRules:
    """Hygienic macro transformer (syntax-rules)."""

    def __init__(self, literals: list, rules: list, definition_env: Environment) -> None:
        self.literals = literals  # list of symbol names
        self.rules = rules  # list of (pattern, template)
        self.definition_env = definition_env

    def transform(self, form: Any, use_env: Environment) -> Any:
        for pattern, template in self.rules:
            bindings: dict[str, Any] = {}
            if _match_pattern(pattern, form, self.literals, bindings):
                return _expand_template(template, bindings, self.definition_env)
        raise SchemeRuntimeError(f"No matching syntax-rules pattern for: {form!r}")


def _eval_define_syntax(args: Any, env: Environment) -> Any:
    name = _get_arg(args, 0)
    transformer_expr = _get_arg(args, 1)
    transformer = _eval_transformer(transformer_expr, env)
    env.define(name.name, MacroProcedure(transformer, env, name=name.name))
    return VOID


def _eval_let_syntax(args: Any, env: Environment, is_letrec: bool) -> Any:
    bindings = _get_arg(args, 0)
    body = _args_to_list(args.cdr)
    child = Environment(parent=env)
    cur = bindings
    while isinstance(cur, Pair):
        b = cur.car
        macro_name = b.car.name
        trans_expr = _get_arg(b, 1)
        trans_env = child if is_letrec else env
        transformer = _eval_transformer(trans_expr, trans_env)
        child.define(macro_name, MacroProcedure(transformer, trans_env, name=macro_name))
        cur = cur.cdr
    if not body:
        raise SchemeSyntaxError("let-syntax: empty body")
    for e in body[:-1]:
        eval_expr(e, child)
    return TailCall(body[-1], child)


def _eval_transformer(expr: Any, env: Environment) -> SyntaxRules:
    """Evaluate a syntax-rules form to a SyntaxRules object."""
    if not isinstance(expr, Pair):
        raise SchemeSyntaxError(f"Expected syntax-rules, got: {expr!r}")
    if not (isinstance(expr.car, Symbol) and expr.car.name == "syntax-rules"):
        raise SchemeSyntaxError(f"Expected syntax-rules, got: {expr.car!r}")
    rest = expr.cdr
    literals_expr = _get_arg(rest, 0)
    literals = [x.name for x in _args_to_list(literals_expr)]
    rules = []
    cur = rest.cdr
    while isinstance(cur, Pair):
        rule = cur.car
        pattern = _get_arg(rule, 0)
        template = _get_arg(rule, 1)
        rules.append((pattern, template))
        cur = cur.cdr
    return SyntaxRules(literals, rules, env)


def _macro_expand(macro: MacroProcedure, form: Any) -> Any:
    return macro.transformer.transform(form, macro.env)


def _match_pattern(
    pattern: Any,
    form: Any,
    literals: list,
    bindings: dict,
    ellipsis_context: dict | None = None,
) -> bool:
    """Match a syntax-rules pattern against a form."""
    if isinstance(pattern, Symbol):
        if pattern.name == "_":
            return True
        if pattern.name in literals:
            # Must be the same symbol
            return isinstance(form, Symbol) and form.name == pattern.name
        # Pattern variable
        bindings[pattern.name] = form
        return True

    if isinstance(pattern, (bool, int, float)) or pattern is NIL or pattern is TRUE or pattern is FALSE:
        return pattern == form

    if isinstance(pattern, Boolean):
        return pattern is form

    if isinstance(pattern, Pair):
        # Check for ellipsis
        if isinstance(pattern.cdr, Pair) and isinstance(pattern.cdr.car, Symbol) \
                and pattern.cdr.car.name == "...":
            # Match zero or more of pattern.car
            rest_pattern = pattern.cdr.cdr
            sub_pattern = pattern.car

            # Collect pattern variables in sub_pattern
            pvars = _pattern_vars(sub_pattern, literals)

            # How many forms to consume?
            form_list = _to_list_for_match(form)
            if form_list is None:
                return False

            # Count minimum required by rest_pattern
            rest_len = _pattern_list_len(rest_pattern)
            if rest_len is None:
                return False
            repeat_count = len(form_list) - rest_len
            if repeat_count < 0:
                return False

            # Initialize ellipsis bindings
            ellipsis_lists: dict[str, list] = {v: [] for v in pvars}

            for i in range(repeat_count):
                sub_bindings: dict[str, Any] = {}
                if not _match_pattern(sub_pattern, form_list[i], literals, sub_bindings):
                    return False
                for v in pvars:
                    ellipsis_lists[v].append(sub_bindings.get(v))

            for v, lst in ellipsis_lists.items():
                bindings[v] = lst

            # Match rest
            rest_form = _list_tail(form, repeat_count)
            return _match_pattern(rest_pattern, rest_form, literals, bindings)

        # Normal pair matching
        if not isinstance(form, Pair):
            # Allow matching NIL against empty pattern list
            if pattern is NIL and form is NIL:
                return True
            return False
        return (
            _match_pattern(pattern.car, form.car, literals, bindings)
            and _match_pattern(pattern.cdr, form.cdr, literals, bindings)
        )

    if pattern is NIL:
        return form is NIL

    # Literal datum (string, char, etc.)
    if isinstance(pattern, SchemeString):
        return isinstance(form, SchemeString) and pattern.value == form.value

    return pattern == form


def _pattern_vars(pattern: Any, literals: list) -> list:
    """Collect all pattern variables (non-literal symbols) in a pattern."""
    if isinstance(pattern, Symbol):
        if pattern.name == "_" or pattern.name == "...":
            return []
        if pattern.name in literals:
            return []
        return [pattern.name]
    if isinstance(pattern, Pair):
        result = _pattern_vars(pattern.car, literals)
        # Skip ellipsis
        if isinstance(pattern.cdr, Pair) and isinstance(pattern.cdr.car, Symbol) \
                and pattern.cdr.car.name == "...":
            result += _pattern_vars(pattern.cdr.cdr, literals)
        else:
            result += _pattern_vars(pattern.cdr, literals)
        return result
    return []


def _pattern_list_len(pattern: Any) -> int | None:
    """Count number of elements in a pattern list (not counting ellipsis groups)."""
    n = 0
    cur = pattern
    while isinstance(cur, Pair):
        if isinstance(cur.cdr, Pair) and isinstance(cur.cdr.car, Symbol) \
                and cur.cdr.car.name == "...":
            return None  # variable length
        n += 1
        cur = cur.cdr
    return n


def _to_list_for_match(form: Any) -> list | None:
    """Convert form to list for ellipsis matching. Returns None if not a list."""
    result = []
    cur = form
    while isinstance(cur, Pair):
        result.append(cur.car)
        cur = cur.cdr
    if cur is NIL:
        return result
    return None


def _list_tail(lst: Any, n: int) -> Any:
    cur = lst
    for _ in range(n):
        if not isinstance(cur, Pair):
            return NIL
        cur = cur.cdr
    return cur


def _expand_template(template: Any, bindings: dict, env: Environment) -> Any:
    """Expand a syntax-rules template with bindings."""
    if isinstance(template, Symbol):
        if template.name in bindings:
            val = bindings[template.name]
            if isinstance(val, list):
                # This shouldn't be returned directly; used via ellipsis
                raise SchemeSyntaxError(f"Template variable {template.name!r} used outside of ellipsis")
            return val
        return template

    if isinstance(template, Pair):
        # Check for ellipsis in cdr
        if isinstance(template.cdr, Pair) and isinstance(template.cdr.car, Symbol) \
                and template.cdr.car.name == "...":
            # Expand ellipsis
            pvars = _template_ellipsis_vars(template.car, bindings)
            if not pvars:
                raise SchemeSyntaxError("Ellipsis with no pattern variables")

            count = len(bindings[pvars[0]])
            result = _expand_template(template.cdr.cdr, bindings, env)
            for i in range(count - 1, -1, -1):
                sub_bindings = dict(bindings)
                for v in pvars:
                    sub_bindings[v] = bindings[v][i]
                expanded = _expand_template(template.car, sub_bindings, env)
                result = cons(expanded, result)
            return result

        return cons(
            _expand_template(template.car, bindings, env),
            _expand_template(template.cdr, bindings, env),
        )

    if isinstance(template, Vector):
        items = [_expand_template(x, bindings, env) for x in template.data]
        return Vector(items)

    return template


def _template_ellipsis_vars(template: Any, bindings: dict) -> list:
    """Find pattern variables used in template that have list bindings."""
    if isinstance(template, Symbol):
        if template.name in bindings and isinstance(bindings[template.name], list):
            return [template.name]
        return []
    if isinstance(template, Pair):
        return _template_ellipsis_vars(template.car, bindings) + \
               _template_ellipsis_vars(template.cdr, bindings)
    return []


# ---------------------------------------------------------------------------
# Apply helper
# ---------------------------------------------------------------------------

def _apply(proc: Any, args: list) -> Any:
    """Apply a procedure to args (with TCO)."""
    if isinstance(proc, LambdaProcedure):
        env = proc.env.extend(proc.params, args)
        for expr in proc.body[:-1]:
            eval_expr(expr, env)
        return eval_expr(proc.body[-1], env)
    if isinstance(proc, PrimitiveProcedure):
        return proc(*args)
    if isinstance(proc, ContinuationProcedure):
        return proc(*args)
    if callable(proc):
        return proc(*args)
    raise SchemeTypeError(f"Not a procedure: {proc!r}")


# ---------------------------------------------------------------------------
# call/cc implementation
# ---------------------------------------------------------------------------

def make_callcc_primitive() -> PrimitiveProcedure:
    """Create the call-with-current-continuation primitive."""

    def call_cc(proc: Any) -> Any:
        cont_id = _next_cont_id()
        result_holder: list = []

        def continuation(*args: Any) -> Any:
            if len(args) == 0:
                val = VOID
            elif len(args) == 1:
                val = args[0]
            else:
                val = Values(*args)
            raise ContinuationException(cont_id, [val])

        cont = ContinuationProcedure(continuation)
        try:
            return _apply(proc, [cont])
        except ContinuationException as e:
            if e.cont_id == cont_id:
                if len(e.values) == 1:
                    return e.values[0]
                return Values(*e.values)
            raise

    return PrimitiveProcedure(call_cc, "call-with-current-continuation")


# ---------------------------------------------------------------------------
# dynamic-wind
# ---------------------------------------------------------------------------

def make_dynamic_wind_primitive() -> PrimitiveProcedure:
    def dynamic_wind(before: Any, thunk: Any, after: Any) -> Any:
        _apply(before, [])
        _wind_stack.append((before, after))
        try:
            result = _apply(thunk, [])
        except ContinuationException:
            _wind_stack.pop()
            _apply(after, [])
            raise
        except Exception:
            _wind_stack.pop()
            _apply(after, [])
            raise
        else:
            _wind_stack.pop()
            _apply(after, [])
            return result

    return PrimitiveProcedure(dynamic_wind, "dynamic-wind")
