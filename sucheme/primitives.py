"""
R5RS built-in procedures for sucheme.

Implements all standard Scheme procedures as per R5RS section 6.
"""

from __future__ import annotations

import math
import os
import sys
from fractions import Fraction
from typing import Any

from sucheme.types import (
    NIL, VOID, TRUE, FALSE,
    Symbol, Boolean, Pair, Vector, Char, SchemeString,
    LambdaProcedure, PrimitiveProcedure, MacroProcedure, ContinuationProcedure,
    Values, Port,
    SchemeError, SchemeRuntimeError, SchemeTypeError, SchemeArityError,
    SchemeNameError,
    scheme_bool, scheme_repr, scheme_display,
    list_to_scheme, scheme_to_list, cons, car, cdr,
    is_exact, is_inexact, exact_to_inexact, inexact_to_exact, normalize_number,
    is_integer_val,
)
from sucheme.environment import Environment


def register_primitives(env: Environment) -> None:
    """Register all R5RS primitives into an environment."""
    prims = _build_primitives()
    for name, proc in prims.items():
        env.define(name, proc)


def _build_primitives() -> dict[str, Any]:
    p: dict[str, Any] = {}

    def prim(name: str):
        def decorator(fn):
            p[name] = PrimitiveProcedure(fn, name)
            return fn
        return decorator

    # -------------------------------------------------------------------------
    # Equivalence predicates (R5RS 6.1)
    # -------------------------------------------------------------------------

    @prim("eq?")
    def scheme_eq(a: Any, b: Any) -> Boolean:
        if a is b:
            return TRUE
        # Numbers: exact same object or same value for small ints
        if type(a) == type(b) and isinstance(a, int) and a == b:
            return TRUE
        return FALSE

    @prim("eqv?")
    def scheme_eqv(a: Any, b: Any) -> Boolean:
        if a is b:
            return TRUE
        if isinstance(a, Boolean) and isinstance(b, Boolean):
            return scheme_bool(a is b)
        if isinstance(a, (int, Fraction)) and isinstance(b, (int, Fraction)):
            return scheme_bool(a == b and is_exact(a) == is_exact(b))
        if isinstance(a, float) and isinstance(b, float):
            # eqv? for inexact: same bit pattern
            if math.isnan(a) and math.isnan(b):
                return FALSE  # NaN != NaN
            return scheme_bool(a == b)
        if isinstance(a, Char) and isinstance(b, Char):
            return scheme_bool(a.char == b.char)
        if isinstance(a, Symbol) and isinstance(b, Symbol):
            return scheme_bool(a is b)
        if a is NIL and b is NIL:
            return TRUE
        return FALSE

    @prim("equal?")
    def scheme_equal(a: Any, b: Any) -> Boolean:
        return scheme_bool(_equal(a, b))

    def _equal(a: Any, b: Any) -> bool:
        if a is b:
            return True
        if isinstance(a, Boolean) and isinstance(b, Boolean):
            return a is b
        if isinstance(a, (int, float, Fraction)) and isinstance(b, (int, float, Fraction)):
            return a == b
        if isinstance(a, Char) and isinstance(b, Char):
            return a.char == b.char
        if isinstance(a, SchemeString) and isinstance(b, SchemeString):
            return a.value == b.value
        if isinstance(a, Symbol) and isinstance(b, Symbol):
            return a is b
        if isinstance(a, Pair) and isinstance(b, Pair):
            return _equal(a.car, b.car) and _equal(a.cdr, b.cdr)
        if isinstance(a, Vector) and isinstance(b, Vector):
            return len(a.data) == len(b.data) and all(_equal(x, y) for x, y in zip(a.data, b.data))
        if a is NIL and b is NIL:
            return True
        return False

    # -------------------------------------------------------------------------
    # Number types (R5RS 6.2)
    # -------------------------------------------------------------------------

    @prim("number?")
    def number_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, (int, float, Fraction, complex)))

    @prim("complex?")
    def complex_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, (int, float, Fraction, complex)))

    @prim("real?")
    def real_p(x: Any) -> Boolean:
        if isinstance(x, complex):
            return scheme_bool(x.imag == 0)
        return scheme_bool(isinstance(x, (int, float, Fraction)))

    @prim("rational?")
    def rational_p(x: Any) -> Boolean:
        if isinstance(x, complex):
            return FALSE
        if isinstance(x, float):
            return scheme_bool(not math.isinf(x) and not math.isnan(x))
        return scheme_bool(isinstance(x, (int, Fraction)))

    @prim("integer?")
    def integer_p(x: Any) -> Boolean:
        return scheme_bool(is_integer_val(x))

    @prim("exact?")
    def exact_p(x: Any) -> Boolean:
        _check_num(x, "exact?")
        return scheme_bool(is_exact(x))

    @prim("inexact?")
    def inexact_p(x: Any) -> Boolean:
        _check_num(x, "inexact?")
        return scheme_bool(is_inexact(x))

    @prim("exact->inexact")
    def exact_to_inexact_prim(x: Any) -> float:
        _check_num(x, "exact->inexact")
        return exact_to_inexact(x)

    @prim("inexact->exact")
    def inexact_to_exact_prim(x: Any) -> Any:
        _check_num(x, "inexact->exact")
        return inexact_to_exact(x)

    # R7RS aliases
    p["exact"] = PrimitiveProcedure(lambda x: inexact_to_exact(x), "exact")
    p["inexact"] = PrimitiveProcedure(lambda x: exact_to_inexact(x), "inexact")

    @prim("zero?")
    def zero_p(x: Any) -> Boolean:
        _check_num(x, "zero?")
        return scheme_bool(x == 0)

    @prim("positive?")
    def positive_p(x: Any) -> Boolean:
        _check_real(x, "positive?")
        return scheme_bool(x > 0)

    @prim("negative?")
    def negative_p(x: Any) -> Boolean:
        _check_real(x, "negative?")
        return scheme_bool(x < 0)

    @prim("odd?")
    def odd_p(x: Any) -> Boolean:
        _check_int(x, "odd?")
        return scheme_bool(int(x) % 2 != 0)

    @prim("even?")
    def even_p(x: Any) -> Boolean:
        _check_int(x, "even?")
        return scheme_bool(int(x) % 2 == 0)

    @prim("max")
    def scheme_max(*args: Any) -> Any:
        _check_min_args(args, 1, "max")
        for a in args:
            _check_real(a, "max")
        has_inexact = any(is_inexact(a) for a in args)
        result = args[0]
        for a in args[1:]:
            if a > result:
                result = a
        if has_inexact:
            return exact_to_inexact(result)
        return result

    @prim("min")
    def scheme_min(*args: Any) -> Any:
        _check_min_args(args, 1, "min")
        for a in args:
            _check_real(a, "min")
        has_inexact = any(is_inexact(a) for a in args)
        result = args[0]
        for a in args[1:]:
            if a < result:
                result = a
        if has_inexact:
            return exact_to_inexact(result)
        return result

    @prim("+")
    def scheme_add(*args: Any) -> Any:
        result: Any = 0
        for a in args:
            _check_num(a, "+")
            result = _num_add(result, a)
        return normalize_number(result)

    @prim("*")
    def scheme_mul(*args: Any) -> Any:
        result: Any = 1
        for a in args:
            _check_num(a, "*")
            result = _num_mul(result, a)
        return normalize_number(result)

    @prim("-")
    def scheme_sub(*args: Any) -> Any:
        _check_min_args(args, 1, "-")
        if len(args) == 1:
            return normalize_number(_num_neg(args[0]))
        result = args[0]
        for a in args[1:]:
            _check_num(a, "-")
            result = _num_sub(result, a)
        return normalize_number(result)

    @prim("/")
    def scheme_div(*args: Any) -> Any:
        _check_min_args(args, 1, "/")
        if len(args) == 1:
            return normalize_number(_num_inv(args[0]))
        result = args[0]
        for a in args[1:]:
            _check_num(a, "/")
            result = _num_div(result, a)
        return normalize_number(result)

    @prim("abs")
    def scheme_abs(x: Any) -> Any:
        _check_real(x, "abs")
        if isinstance(x, int):
            return abs(x)
        if isinstance(x, Fraction):
            return Fraction(abs(x.numerator), x.denominator)
        return abs(x)

    @prim("quotient")
    def scheme_quotient(a: Any, b: Any) -> Any:
        _check_int(a, "quotient")
        _check_int(b, "quotient")
        if b == 0:
            raise SchemeRuntimeError("quotient: division by zero")
        if isinstance(a, float) or isinstance(b, float):
            return float(int(a) // int(b)) if a * b > 0 else float(-(-int(a) // int(b)))
        q = int(a) // int(b)
        # quotient truncates toward zero
        if a * b < 0 and int(a) % int(b) != 0:
            q += 1
        return q

    @prim("remainder")
    def scheme_remainder(a: Any, b: Any) -> Any:
        _check_int(a, "remainder")
        _check_int(b, "remainder")
        if b == 0:
            raise SchemeRuntimeError("remainder: division by zero")
        ia, ib = int(a), int(b)
        r = ia % ib
        if ia < 0 and r > 0:
            r -= abs(ib)
        elif ia > 0 and r < 0:
            r += abs(ib)
        if isinstance(a, float) or isinstance(b, float):
            return float(r)
        return r

    @prim("modulo")
    def scheme_modulo(a: Any, b: Any) -> Any:
        _check_int(a, "modulo")
        _check_int(b, "modulo")
        if b == 0:
            raise SchemeRuntimeError("modulo: division by zero")
        ia, ib = int(a), int(b)
        r = ia % ib
        if isinstance(a, float) or isinstance(b, float):
            return float(r)
        return r

    @prim("gcd")
    def scheme_gcd(*args: Any) -> Any:
        if not args:
            return 0
        result = 0
        for a in args:
            _check_int(a, "gcd")
            result = math.gcd(abs(int(result)), abs(int(a)))
        if any(isinstance(a, float) for a in args):
            return float(result)
        return result

    @prim("lcm")
    def scheme_lcm(*args: Any) -> Any:
        if not args:
            return 1
        result = 1
        for a in args:
            _check_int(a, "lcm")
            ia = abs(int(a))
            if ia == 0:
                result = 0
            else:
                result = result * ia // math.gcd(result, ia)
        if any(isinstance(a, float) for a in args):
            return float(result)
        return result

    @prim("numerator")
    def scheme_numerator(x: Any) -> Any:
        if isinstance(x, int):
            return x
        if isinstance(x, Fraction):
            return x.numerator
        if isinstance(x, float):
            f = Fraction(x).limit_denominator(10**15)
            return float(f.numerator)
        raise SchemeTypeError(f"numerator: not a rational: {x!r}")

    @prim("denominator")
    def scheme_denominator(x: Any) -> Any:
        if isinstance(x, int):
            return 1
        if isinstance(x, Fraction):
            return x.denominator
        if isinstance(x, float):
            f = Fraction(x).limit_denominator(10**15)
            return float(f.denominator)
        raise SchemeTypeError(f"denominator: not a rational: {x!r}")

    @prim("floor")
    def scheme_floor(x: Any) -> Any:
        _check_real(x, "floor")
        if isinstance(x, int):
            return x
        if isinstance(x, Fraction):
            return int(math.floor(float(x)))
        return float(math.floor(x))

    @prim("ceiling")
    def scheme_ceiling(x: Any) -> Any:
        _check_real(x, "ceiling")
        if isinstance(x, int):
            return x
        if isinstance(x, Fraction):
            return int(math.ceil(float(x)))
        return float(math.ceil(x))

    @prim("truncate")
    def scheme_truncate(x: Any) -> Any:
        _check_real(x, "truncate")
        if isinstance(x, int):
            return x
        if isinstance(x, Fraction):
            return int(math.trunc(float(x)))
        return float(math.trunc(x))

    @prim("round")
    def scheme_round(x: Any) -> Any:
        _check_real(x, "round")
        if isinstance(x, int):
            return x
        if isinstance(x, Fraction):
            return int(round(float(x)))
        return float(round(x))

    @prim("exact-round")
    def exact_round(x: Any) -> int:
        _check_real(x, "exact-round")
        return int(round(float(x)))

    @prim("exact-floor")
    def exact_floor(x: Any) -> int:
        _check_real(x, "exact-floor")
        return int(math.floor(float(x)))

    @prim("exact-ceiling")
    def exact_ceiling(x: Any) -> int:
        _check_real(x, "exact-ceiling")
        return int(math.ceil(float(x)))

    @prim("exact-truncate")
    def exact_truncate(x: Any) -> int:
        _check_real(x, "exact-truncate")
        return int(math.trunc(float(x)))

    @prim("expt")
    def scheme_expt(base: Any, exp: Any) -> Any:
        _check_num(base, "expt")
        _check_num(exp, "expt")
        if isinstance(exp, int) and exp >= 0 and isinstance(base, (int, Fraction)):
            return normalize_number(base ** exp)
        result = float(base) ** float(exp)
        if is_exact(base) and is_exact(exp) and isinstance(exp, int) and exp < 0:
            # exact result: 1/(base^(-exp))
            return normalize_number(Fraction(1, base ** (-exp)))
        return result

    @prim("sqrt")
    def scheme_sqrt(x: Any) -> Any:
        _check_num(x, "sqrt")
        if isinstance(x, int) and x >= 0:
            s = math.isqrt(x)
            if s * s == x:
                return s
        return math.sqrt(float(x)) if not isinstance(x, complex) else cmath_sqrt(x)

    def cmath_sqrt(x: Any) -> Any:
        import cmath
        return cmath.sqrt(x)

    @prim("exp")
    def scheme_exp(x: Any) -> float:
        _check_num(x, "exp")
        return math.exp(float(x))

    @prim("log")
    def scheme_log(*args: Any) -> float:
        _check_min_args(args, 1, "log")
        x = args[0]
        _check_num(x, "log")
        if len(args) == 2:
            base = args[1]
            _check_num(base, "log")
            return math.log(float(x), float(base))
        return math.log(float(x))

    @prim("sin")
    def scheme_sin(x: Any) -> float:
        return math.sin(float(x))

    @prim("cos")
    def scheme_cos(x: Any) -> float:
        return math.cos(float(x))

    @prim("tan")
    def scheme_tan(x: Any) -> float:
        return math.tan(float(x))

    @prim("asin")
    def scheme_asin(x: Any) -> float:
        return math.asin(float(x))

    @prim("acos")
    def scheme_acos(x: Any) -> float:
        return math.acos(float(x))

    @prim("atan")
    def scheme_atan(*args: Any) -> float:
        if len(args) == 1:
            return math.atan(float(args[0]))
        elif len(args) == 2:
            return math.atan2(float(args[0]), float(args[1]))
        raise SchemeArityError("atan: expected 1 or 2 args")

    @prim("floor/")
    def floor_div(a: Any, b: Any) -> Values:
        q = int(math.floor(float(a) / float(b)))
        r = a - q * b
        return Values(q, normalize_number(r))

    @prim("floor-quotient")
    def floor_quotient(a: Any, b: Any) -> Any:
        return int(math.floor(float(a) / float(b)))

    @prim("floor-remainder")
    def floor_remainder(a: Any, b: Any) -> Any:
        q = int(math.floor(float(a) / float(b)))
        return normalize_number(a - q * b)

    @prim("truncate/")
    def truncate_div(a: Any, b: Any) -> Values:
        q = int(math.trunc(float(a) / float(b)))
        r = a - q * b
        return Values(q, normalize_number(r))

    @prim("truncate-quotient")
    def truncate_quotient(a: Any, b: Any) -> Any:
        return int(math.trunc(float(a) / float(b)))

    @prim("truncate-remainder")
    def truncate_remainder(a: Any, b: Any) -> Any:
        q = int(math.trunc(float(a) / float(b)))
        return normalize_number(a - q * b)

    @prim("make-rectangular")
    def make_rectangular(r: Any, i: Any) -> complex:
        return complex(float(r), float(i))

    @prim("make-polar")
    def make_polar(r: Any, theta: Any) -> complex:
        return complex(float(r) * math.cos(float(theta)), float(r) * math.sin(float(theta)))

    @prim("real-part")
    def real_part(z: Any) -> Any:
        if isinstance(z, complex):
            return z.real
        return z

    @prim("imag-part")
    def imag_part(z: Any) -> Any:
        if isinstance(z, complex):
            return z.imag
        return 0

    @prim("magnitude")
    def magnitude(z: Any) -> Any:
        if isinstance(z, complex):
            return abs(z)
        return abs(z)

    @prim("angle")
    def angle(z: Any) -> Any:
        if isinstance(z, complex):
            return math.atan2(z.imag, z.real)
        return 0.0 if z >= 0 else math.pi

    # Numeric comparison
    for op_name, op in [("=", lambda a, b: a == b),
                        ("<", lambda a, b: a < b),
                        (">", lambda a, b: a > b),
                        ("<=", lambda a, b: a <= b),
                        (">=", lambda a, b: a >= b)]:
        def make_cmp(op_fn, nm):
            def cmp(*args):
                _check_min_args(args, 2, nm)
                for a in args:
                    _check_num(a, nm)
                return scheme_bool(all(op_fn(args[i], args[i+1]) for i in range(len(args)-1)))
            return PrimitiveProcedure(cmp, nm)
        p[op_name] = make_cmp(op, op_name)

    @prim("number->string")
    def number_to_string(*args: Any) -> SchemeString:
        _check_min_args(args, 1, "number->string")
        x = args[0]
        radix = int(args[1]) if len(args) > 1 else 10
        if isinstance(x, int):
            if radix == 10:
                return SchemeString(str(x))
            elif radix == 16:
                return SchemeString(hex(x)[2:])
            elif radix == 8:
                return SchemeString(oct(x)[2:])
            elif radix == 2:
                return SchemeString(bin(x)[2:])
        if isinstance(x, float):
            if math.isinf(x):
                return SchemeString("+inf.0" if x > 0 else "-inf.0")
            if math.isnan(x):
                return SchemeString("+nan.0")
            return SchemeString(repr(x))
        return SchemeString(scheme_repr(x))

    @prim("string->number")
    def string_to_number(*args: Any) -> Any:
        _check_min_args(args, 1, "string->number")
        s = _check_str(args[0], "string->number")
        radix = int(args[1]) if len(args) > 1 else 10
        from sucheme.lexer import _parse_number
        if radix != 10:
            s = f"#{['', '', 'b', '', '', '', '', '', 'o', '', '', '', '', '', '', '', 'x'][radix]}{s}"
        val = _parse_number(s)
        return val if val is not None else FALSE

    # -------------------------------------------------------------------------
    # Boolean (R5RS 6.3)
    # -------------------------------------------------------------------------

    @prim("not")
    def scheme_not(x: Any) -> Boolean:
        return scheme_bool(x is FALSE)

    @prim("boolean?")
    def boolean_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Boolean))

    @prim("boolean=?")
    def boolean_eq(*args: Any) -> Boolean:
        _check_min_args(args, 2, "boolean=?")
        return scheme_bool(all(a is args[0] for a in args[1:]))

    # -------------------------------------------------------------------------
    # Pairs and lists (R5RS 6.4)
    # -------------------------------------------------------------------------

    @prim("pair?")
    def pair_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Pair))

    @prim("cons")
    def scheme_cons(a: Any, b: Any) -> Pair:
        return Pair(a, b)

    @prim("car")
    def scheme_car(x: Any) -> Any:
        if not isinstance(x, Pair):
            raise SchemeTypeError(f"car: not a pair: {x!r}")
        return x.car

    @prim("cdr")
    def scheme_cdr(x: Any) -> Any:
        if not isinstance(x, Pair):
            raise SchemeTypeError(f"cdr: not a pair: {x!r}")
        return x.cdr

    @prim("set-car!")
    def set_car(p: Any, v: Any) -> Any:
        if not isinstance(p, Pair):
            raise SchemeTypeError(f"set-car!: not a pair: {p!r}")
        p.car = v
        return VOID

    @prim("set-cdr!")
    def set_cdr(p: Any, v: Any) -> Any:
        if not isinstance(p, Pair):
            raise SchemeTypeError(f"set-cdr!: not a pair: {p!r}")
        p.cdr = v
        return VOID

    @prim("null?")
    def null_p(x: Any) -> Boolean:
        return scheme_bool(x is NIL)

    @prim("list?")
    def list_p(x: Any) -> Boolean:
        # Proper list detection (handles cycles)
        slow = x
        fast = x
        while True:
            if fast is NIL:
                return TRUE
            if not isinstance(fast, Pair):
                return FALSE
            fast = fast.cdr
            if fast is NIL:
                return TRUE
            if not isinstance(fast, Pair):
                return FALSE
            fast = fast.cdr
            slow = slow.cdr
            if slow is fast:
                return FALSE

    @prim("list")
    def scheme_list(*args: Any) -> Any:
        return list_to_scheme(list(args))

    @prim("length")
    def scheme_length(lst: Any) -> int:
        from sucheme.types import list_length
        return list_length(lst)

    @prim("append")
    def scheme_append(*args: Any) -> Any:
        if not args:
            return NIL
        if len(args) == 1:
            return args[0]
        result = args[-1]
        for lst in reversed(args[:-1]):
            cur = lst
            items = []
            while isinstance(cur, Pair):
                items.append(cur.car)
                cur = cur.cdr
            if cur is not NIL:
                raise SchemeTypeError(f"append: not a proper list: {lst!r}")
            for item in reversed(items):
                result = Pair(item, result)
        return result

    @prim("reverse")
    def scheme_reverse(lst: Any) -> Any:
        result = NIL
        cur = lst
        while isinstance(cur, Pair):
            result = Pair(cur.car, result)
            cur = cur.cdr
        if cur is not NIL:
            raise SchemeTypeError(f"reverse: not a proper list: {lst!r}")
        return result

    @prim("list-tail")
    def list_tail(lst: Any, k: int) -> Any:
        _check_int(k, "list-tail")
        for _ in range(int(k)):
            if not isinstance(lst, Pair):
                raise SchemeRuntimeError(f"list-tail: index out of range")
            lst = lst.cdr
        return lst

    @prim("list-ref")
    def list_ref(lst: Any, k: int) -> Any:
        _check_int(k, "list-ref")
        for _ in range(int(k)):
            if not isinstance(lst, Pair):
                raise SchemeRuntimeError(f"list-ref: index out of range")
            lst = lst.cdr
        if not isinstance(lst, Pair):
            raise SchemeRuntimeError(f"list-ref: index out of range")
        return lst.car

    @prim("list-set!")
    def list_set(lst: Any, k: int, v: Any) -> Any:
        _check_int(k, "list-set!")
        for _ in range(int(k)):
            if not isinstance(lst, Pair):
                raise SchemeRuntimeError(f"list-set!: index out of range")
            lst = lst.cdr
        if not isinstance(lst, Pair):
            raise SchemeRuntimeError(f"list-set!: index out of range")
        lst.car = v
        return VOID

    @prim("list-copy")
    def list_copy(lst: Any) -> Any:
        if lst is NIL:
            return NIL
        if not isinstance(lst, Pair):
            return lst
        items = []
        cur = lst
        while isinstance(cur, Pair):
            items.append(cur.car)
            cur = cur.cdr
        return list_to_scheme(items) if cur is NIL else _build_dotted(items, cur)

    def _build_dotted(items: list, tail: Any) -> Any:
        result = tail
        for item in reversed(items):
            result = Pair(item, result)
        return result

    # caar cadr etc.
    for combo in ["aa", "ad", "da", "dd",
                  "aaa", "aad", "ada", "add", "daa", "dad", "dda", "ddd",
                  "aaaa", "aaad", "aada", "aadd", "adaa", "adad", "adda", "addd",
                  "daaa", "daad", "dada", "dadd", "ddaa", "ddad", "ddda", "dddd"]:
        def make_cxr(c: str) -> PrimitiveProcedure:
            nm = f"c{c}r"
            def cxr(x: Any) -> Any:
                for op in reversed(c):
                    if op == "a":
                        x = car(x)
                    else:
                        x = cdr(x)
                return x
            return PrimitiveProcedure(cxr, nm)
        p[f"c{combo}r"] = make_cxr(combo)

    @prim("assoc")
    def scheme_assoc(key: Any, alist: Any) -> Any:
        cur = alist
        while isinstance(cur, Pair):
            pair = cur.car
            if isinstance(pair, Pair) and _equal(pair.car, key):
                return pair
            cur = cur.cdr
        return FALSE

    @prim("assv")
    def scheme_assv(key: Any, alist: Any) -> Any:
        cur = alist
        while isinstance(cur, Pair):
            pair = cur.car
            if isinstance(pair, Pair) and scheme_eqv(pair.car, key) is TRUE:
                return pair
            cur = cur.cdr
        return FALSE

    @prim("assq")
    def scheme_assq(key: Any, alist: Any) -> Any:
        cur = alist
        while isinstance(cur, Pair):
            pair = cur.car
            if isinstance(pair, Pair) and scheme_eq(pair.car, key) is TRUE:
                return pair
            cur = cur.cdr
        return FALSE

    @prim("member")
    def scheme_member(elem: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            if _equal(cur.car, elem):
                return cur
            cur = cur.cdr
        return FALSE

    @prim("memv")
    def scheme_memv(elem: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            if scheme_eqv(cur.car, elem) is TRUE:
                return cur
            cur = cur.cdr
        return FALSE

    @prim("memq")
    def scheme_memq(elem: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            if scheme_eq(cur.car, elem) is TRUE:
                return cur
            cur = cur.cdr
        return FALSE

    # -------------------------------------------------------------------------
    # Symbols (R5RS 6.5)
    # -------------------------------------------------------------------------

    @prim("symbol?")
    def symbol_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Symbol))

    @prim("symbol->string")
    def symbol_to_string(x: Any) -> SchemeString:
        if not isinstance(x, Symbol):
            raise SchemeTypeError(f"symbol->string: not a symbol: {x!r}")
        return SchemeString(x.name)

    @prim("string->symbol")
    def string_to_symbol(x: Any) -> Symbol:
        s = _check_str(x, "string->symbol")
        return Symbol(s)

    @prim("symbol=?")
    def symbol_eq(*args: Any) -> Boolean:
        _check_min_args(args, 2, "symbol=?")
        return scheme_bool(all(isinstance(a, Symbol) and a is args[0] for a in args))

    # -------------------------------------------------------------------------
    # Characters (R5RS 6.6)
    # -------------------------------------------------------------------------

    @prim("char?")
    def char_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char))

    @prim("char->integer")
    def char_to_int(x: Any) -> int:
        if not isinstance(x, Char):
            raise SchemeTypeError(f"char->integer: not a char: {x!r}")
        return ord(x.char)

    @prim("integer->char")
    def int_to_char(n: Any) -> Char:
        _check_int(n, "integer->char")
        return Char(chr(int(n)))

    @prim("char-alphabetic?")
    def char_alpha(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char) and x.char.isalpha())

    @prim("char-numeric?")
    def char_num(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char) and x.char.isdigit())

    @prim("char-whitespace?")
    def char_ws(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char) and x.char in " \t\n\r\f\v")

    @prim("char-upper-case?")
    def char_upper(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char) and x.char.isupper())

    @prim("char-lower-case?")
    def char_lower(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Char) and x.char.islower())

    @prim("char-upcase")
    def char_upcase(x: Any) -> Char:
        if not isinstance(x, Char):
            raise SchemeTypeError(f"char-upcase: not a char: {x!r}")
        return Char(x.char.upper())

    @prim("char-downcase")
    def char_downcase(x: Any) -> Char:
        if not isinstance(x, Char):
            raise SchemeTypeError(f"char-downcase: not a char: {x!r}")
        return Char(x.char.lower())

    for op_name, op in [("char=?", lambda a, b: a == b),
                        ("char<?", lambda a, b: a < b),
                        ("char>?", lambda a, b: a > b),
                        ("char<=?", lambda a, b: a <= b),
                        ("char>=?", lambda a, b: a >= b)]:
        def make_char_cmp(op_fn, nm):
            def char_cmp(*args):
                _check_min_args(args, 2, nm)
                for a in args:
                    if not isinstance(a, Char):
                        raise SchemeTypeError(f"{nm}: not a char: {a!r}")
                return scheme_bool(all(op_fn(args[i].char, args[i+1].char) for i in range(len(args)-1)))
            return PrimitiveProcedure(char_cmp, nm)
        p[op_name] = make_char_cmp(op, op_name)

    for op_name, op in [("char-ci=?", lambda a, b: a.lower() == b.lower()),
                        ("char-ci<?", lambda a, b: a.lower() < b.lower()),
                        ("char-ci>?", lambda a, b: a.lower() > b.lower()),
                        ("char-ci<=?", lambda a, b: a.lower() <= b.lower()),
                        ("char-ci>=?", lambda a, b: a.lower() >= b.lower())]:
        def make_char_ci_cmp(op_fn, nm):
            def char_ci_cmp(*args):
                _check_min_args(args, 2, nm)
                for a in args:
                    if not isinstance(a, Char):
                        raise SchemeTypeError(f"{nm}: not a char: {a!r}")
                return scheme_bool(all(op_fn(args[i].char, args[i+1].char) for i in range(len(args)-1)))
            return PrimitiveProcedure(char_ci_cmp, nm)
        p[op_name] = make_char_ci_cmp(op, op_name)

    # -------------------------------------------------------------------------
    # Strings (R5RS 6.7)
    # -------------------------------------------------------------------------

    @prim("string?")
    def string_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, SchemeString))

    @prim("make-string")
    def make_string(*args: Any) -> SchemeString:
        _check_min_args(args, 1, "make-string")
        n = int(args[0])
        ch = args[1].char if len(args) > 1 else "\x00"
        return SchemeString(ch * n)

    @prim("string")
    def scheme_string(*args: Any) -> SchemeString:
        for a in args:
            if not isinstance(a, Char):
                raise SchemeTypeError(f"string: not a char: {a!r}")
        return SchemeString("".join(a.char for a in args))

    @prim("string-length")
    def string_length(x: Any) -> int:
        s = _check_str(x, "string-length")
        return len(s)

    @prim("string-ref")
    def string_ref(x: Any, k: int) -> Char:
        s = _check_str(x, "string-ref")
        _check_int(k, "string-ref")
        i = int(k)
        if i < 0 or i >= len(s):
            raise SchemeRuntimeError(f"string-ref: index {i} out of range for string of length {len(s)}")
        return Char(s[i])

    @prim("string-set!")
    def string_set(x: Any, k: int, ch: Any) -> Any:
        if not isinstance(x, SchemeString):
            raise SchemeTypeError(f"string-set!: not a string: {x!r}")
        if not isinstance(ch, Char):
            raise SchemeTypeError(f"string-set!: not a char: {ch!r}")
        _check_int(k, "string-set!")
        i = int(k)
        lst = list(x.value)
        lst[i] = ch.char
        x.value = "".join(lst)
        return VOID

    @prim("string=?")
    def string_eq(*args: Any) -> Boolean:
        _check_min_args(args, 2, "string=?")
        strs = [_check_str(a, "string=?") for a in args]
        return scheme_bool(all(strs[i] == strs[i+1] for i in range(len(strs)-1)))

    for sop_name, sop in [("string<?", lambda a, b: a < b),
                          ("string>?", lambda a, b: a > b),
                          ("string<=?", lambda a, b: a <= b),
                          ("string>=?", lambda a, b: a >= b)]:
        def make_str_cmp(op_fn, nm):
            def str_cmp(*args):
                _check_min_args(args, 2, nm)
                strs = [_check_str(a, nm) for a in args]
                return scheme_bool(all(op_fn(strs[i], strs[i+1]) for i in range(len(strs)-1)))
            return PrimitiveProcedure(str_cmp, nm)
        p[sop_name] = make_str_cmp(sop, sop_name)

    for sop_name, sop in [("string-ci=?", lambda a, b: a.lower() == b.lower()),
                          ("string-ci<?", lambda a, b: a.lower() < b.lower()),
                          ("string-ci>?", lambda a, b: a.lower() > b.lower()),
                          ("string-ci<=?", lambda a, b: a.lower() <= b.lower()),
                          ("string-ci>=?", lambda a, b: a.lower() >= b.lower())]:
        def make_str_ci_cmp(op_fn, nm):
            def str_ci_cmp(*args):
                _check_min_args(args, 2, nm)
                strs = [_check_str(a, nm) for a in args]
                return scheme_bool(all(op_fn(strs[i], strs[i+1]) for i in range(len(strs)-1)))
            return PrimitiveProcedure(str_ci_cmp, nm)
        p[sop_name] = make_str_ci_cmp(sop, sop_name)

    @prim("substring")
    def scheme_substring(x: Any, start: int, end: int = None) -> SchemeString:
        s = _check_str(x, "substring")
        _check_int(start, "substring")
        i = int(start)
        if end is None:
            return SchemeString(s[i:])
        _check_int(end, "substring")
        j = int(end)
        return SchemeString(s[i:j])

    # Fix: substring with optional end
    p["substring"] = PrimitiveProcedure(
        lambda *args: SchemeString(_check_str(args[0], "substring")[int(args[1]):int(args[2]) if len(args) > 2 else None]),
        "substring"
    )

    @prim("string-append")
    def string_append(*args: Any) -> SchemeString:
        return SchemeString("".join(_check_str(a, "string-append") for a in args))

    @prim("string->list")
    def string_to_list(*args: Any) -> Any:
        _check_min_args(args, 1, "string->list")
        s = _check_str(args[0], "string->list")
        start = int(args[1]) if len(args) > 1 else 0
        end = int(args[2]) if len(args) > 2 else len(s)
        return list_to_scheme([Char(c) for c in s[start:end]])

    @prim("list->string")
    def list_to_string(lst: Any) -> SchemeString:
        chars = []
        cur = lst
        while isinstance(cur, Pair):
            if not isinstance(cur.car, Char):
                raise SchemeTypeError(f"list->string: not a char: {cur.car!r}")
            chars.append(cur.car.char)
            cur = cur.cdr
        return SchemeString("".join(chars))

    @prim("string-copy")
    def string_copy(*args: Any) -> SchemeString:
        _check_min_args(args, 1, "string-copy")
        s = _check_str(args[0], "string-copy")
        start = int(args[1]) if len(args) > 1 else 0
        end = int(args[2]) if len(args) > 2 else len(s)
        return SchemeString(s[start:end])

    @prim("string-fill!")
    def string_fill(x: Any, ch: Any) -> Any:
        if not isinstance(x, SchemeString):
            raise SchemeTypeError(f"string-fill!: not a string")
        if not isinstance(ch, Char):
            raise SchemeTypeError(f"string-fill!: not a char")
        x.value = ch.char * len(x.value)
        return VOID

    @prim("string-upcase")
    def string_upcase(x: Any) -> SchemeString:
        return SchemeString(_check_str(x, "string-upcase").upper())

    @prim("string-downcase")
    def string_downcase(x: Any) -> SchemeString:
        return SchemeString(_check_str(x, "string-downcase").lower())

    @prim("string-contains")
    def string_contains(haystack: Any, needle: Any) -> Any:
        h = _check_str(haystack, "string-contains")
        n = _check_str(needle, "string-contains")
        idx = h.find(n)
        return idx if idx >= 0 else FALSE

    @prim("string-split")
    def string_split(s: Any, sep: Any) -> Any:
        sv = _check_str(s, "string-split")
        sp = _check_str(sep, "string-split")
        parts = sv.split(sp)
        return list_to_scheme([SchemeString(p) for p in parts])

    # -------------------------------------------------------------------------
    # Vectors (R5RS 6.8)
    # -------------------------------------------------------------------------

    @prim("vector?")
    def vector_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Vector))

    @prim("make-vector")
    def make_vector(*args: Any) -> Vector:
        _check_min_args(args, 1, "make-vector")
        n = int(args[0])
        fill = args[1] if len(args) > 1 else 0
        return Vector([fill] * n)

    @prim("vector")
    def scheme_vector(*args: Any) -> Vector:
        return Vector(list(args))

    @prim("vector-length")
    def vector_length(v: Any) -> int:
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector-length: not a vector: {v!r}")
        return len(v.data)

    @prim("vector-ref")
    def vector_ref(v: Any, k: int) -> Any:
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector-ref: not a vector: {v!r}")
        _check_int(k, "vector-ref")
        i = int(k)
        if i < 0 or i >= len(v.data):
            raise SchemeRuntimeError(f"vector-ref: index {i} out of range")
        return v.data[i]

    @prim("vector-set!")
    def vector_set(v: Any, k: int, val: Any) -> Any:
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector-set!: not a vector: {v!r}")
        _check_int(k, "vector-set!")
        i = int(k)
        if i < 0 or i >= len(v.data):
            raise SchemeRuntimeError(f"vector-set!: index {i} out of range")
        v.data[i] = val
        return VOID

    @prim("vector->list")
    def vector_to_list(*args: Any) -> Any:
        _check_min_args(args, 1, "vector->list")
        v = args[0]
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector->list: not a vector: {v!r}")
        start = int(args[1]) if len(args) > 1 else 0
        end = int(args[2]) if len(args) > 2 else len(v.data)
        return list_to_scheme(v.data[start:end])

    @prim("list->vector")
    def list_to_vector(lst: Any) -> Vector:
        return Vector(scheme_to_list(lst))

    @prim("vector-fill!")
    def vector_fill(v: Any, val: Any) -> Any:
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector-fill!: not a vector")
        for i in range(len(v.data)):
            v.data[i] = val
        return VOID

    @prim("vector-copy")
    def vector_copy(*args: Any) -> Vector:
        _check_min_args(args, 1, "vector-copy")
        v = args[0]
        if not isinstance(v, Vector):
            raise SchemeTypeError(f"vector-copy: not a vector")
        start = int(args[1]) if len(args) > 1 else 0
        end = int(args[2]) if len(args) > 2 else len(v.data)
        return Vector(list(v.data[start:end]))

    @prim("vector-append")
    def vector_append(*args: Any) -> Vector:
        data = []
        for a in args:
            if not isinstance(a, Vector):
                raise SchemeTypeError(f"vector-append: not a vector: {a!r}")
            data.extend(a.data)
        return Vector(data)

    @prim("vector-map")
    def vector_map(proc: Any, *vecs: Any) -> Vector:
        if not vecs:
            raise SchemeArityError("vector-map: no vectors")
        length = len(vecs[0].data)
        result = []
        for i in range(length):
            args = [v.data[i] for v in vecs]
            result.append(_apply_proc(proc, args))
        return Vector(result)

    @prim("vector-for-each")
    def vector_for_each(proc: Any, *vecs: Any) -> Any:
        if not vecs:
            raise SchemeArityError("vector-for-each: no vectors")
        length = len(vecs[0].data)
        for i in range(length):
            args = [v.data[i] for v in vecs]
            _apply_proc(proc, args)
        return VOID

    # -------------------------------------------------------------------------
    # Control features (R5RS 6.9)
    # -------------------------------------------------------------------------

    @prim("procedure?")
    def procedure_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, (LambdaProcedure, PrimitiveProcedure,
                                         MacroProcedure, ContinuationProcedure)) or callable(x))

    @prim("apply")
    def scheme_apply(proc: Any, *args: Any) -> Any:
        if not args:
            raise SchemeArityError("apply: no arguments")
        # Last arg must be a list
        actual_args = list(args[:-1])
        last = args[-1]
        cur = last
        while isinstance(cur, Pair):
            actual_args.append(cur.car)
            cur = cur.cdr
        if cur is not NIL:
            raise SchemeTypeError("apply: last argument not a proper list")
        return _apply_proc(proc, actual_args)

    @prim("map")
    def scheme_map(proc: Any, *lsts: Any) -> Any:
        if not lsts:
            raise SchemeArityError("map: no lists")
        result = []
        iters = list(lsts)
        while all(isinstance(l, Pair) for l in iters):
            cars = [l.car for l in iters]
            result.append(_apply_proc(proc, cars))
            iters = [l.cdr for l in iters]
        return list_to_scheme(result)

    @prim("for-each")
    def scheme_for_each(proc: Any, *lsts: Any) -> Any:
        if not lsts:
            raise SchemeArityError("for-each: no lists")
        iters = list(lsts)
        while all(isinstance(l, Pair) for l in iters):
            cars = [l.car for l in iters]
            _apply_proc(proc, cars)
            iters = [l.cdr for l in iters]
        return VOID

    @prim("filter")
    def scheme_filter(pred: Any, lst: Any) -> Any:
        result = []
        cur = lst
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is not FALSE:
                result.append(cur.car)
            cur = cur.cdr
        return list_to_scheme(result)

    @prim("reduce")
    def scheme_reduce(proc: Any, init: Any, lst: Any) -> Any:
        cur = lst
        if cur is NIL:
            return init
        result = cur.car
        cur = cur.cdr
        while isinstance(cur, Pair):
            result = _apply_proc(proc, [result, cur.car])
            cur = cur.cdr
        return result

    @prim("fold-left")
    def fold_left(proc: Any, init: Any, lst: Any) -> Any:
        result = init
        cur = lst
        while isinstance(cur, Pair):
            result = _apply_proc(proc, [result, cur.car])
            cur = cur.cdr
        return result

    @prim("fold-right")
    def fold_right(proc: Any, init: Any, lst: Any) -> Any:
        items = scheme_to_list(lst)
        result = init
        for item in reversed(items):
            result = _apply_proc(proc, [item, result])
        return result

    @prim("for-all")
    def for_all(pred: Any, lst: Any) -> Any:
        cur = lst
        last = TRUE
        while isinstance(cur, Pair):
            last = _apply_proc(pred, [cur.car])
            if last is FALSE:
                return FALSE
            cur = cur.cdr
        return last

    @prim("there-exists?")
    def there_exists(pred: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            val = _apply_proc(pred, [cur.car])
            if val is not FALSE:
                return val
            cur = cur.cdr
        return FALSE

    @prim("sort")
    def scheme_sort(lst: Any, less_p: Any) -> Any:
        items = scheme_to_list(lst)

        def key_fn(x: Any) -> Any:
            return x

        import functools

        def compare(a: Any, b: Any) -> int:
            if _apply_proc(less_p, [a, b]) is not FALSE:
                return -1
            if _apply_proc(less_p, [b, a]) is not FALSE:
                return 1
            return 0

        items.sort(key=functools.cmp_to_key(compare))
        return list_to_scheme(items)

    @prim("sort!")
    def scheme_sort_bang(lst: Any, less_p: Any) -> Any:
        return p["sort"]._fn(lst, less_p)

    @prim("iota")
    def scheme_iota(*args: Any) -> Any:
        _check_min_args(args, 1, "iota")
        count = int(args[0])
        start = args[1] if len(args) > 1 else 0
        step = args[2] if len(args) > 2 else 1
        return list_to_scheme([start + i * step for i in range(count)])

    @prim("call-with-current-continuation")
    def call_cc_alias(*args):
        # Will be replaced by real call/cc in make_global_env
        raise SchemeRuntimeError("call/cc not initialized")

    p["call/cc"] = p["call-with-current-continuation"]

    # -------------------------------------------------------------------------
    # Input/Output (R5RS 6.10)
    # -------------------------------------------------------------------------

    @prim("display")
    def scheme_display_prim(*args: Any) -> Any:
        _check_min_args(args, 1, "display")
        s = scheme_display(args[0])
        port = args[1] if len(args) > 1 else None
        if port is not None and isinstance(port, Port):
            port.file.write(s)
        else:
            print(s, end="")
        return VOID

    @prim("write")
    def scheme_write_prim(*args: Any) -> Any:
        _check_min_args(args, 1, "write")
        s = scheme_repr(args[0])
        port = args[1] if len(args) > 1 else None
        if port is not None and isinstance(port, Port):
            port.file.write(s)
        else:
            print(s, end="")
        return VOID

    @prim("newline")
    def scheme_newline(*args: Any) -> Any:
        port = args[0] if args else None
        if port is not None and isinstance(port, Port):
            port.file.write("\n")
        else:
            print()
        return VOID

    @prim("write-char")
    def write_char(*args: Any) -> Any:
        _check_min_args(args, 1, "write-char")
        ch = args[0]
        if not isinstance(ch, Char):
            raise SchemeTypeError(f"write-char: not a char: {ch!r}")
        port = args[1] if len(args) > 1 else None
        if port is not None and isinstance(port, Port):
            port.file.write(ch.char)
        else:
            print(ch.char, end="")
        return VOID

    @prim("read")
    def scheme_read(*args: Any) -> Any:
        port = args[0] if args else None
        try:
            if port is not None and isinstance(port, Port):
                line = port.file.readline()
            else:
                line = input()
            if not line:
                return Symbol("eof-object")  # simplified
            from sucheme.parser import parse_one
            return parse_one(line)
        except EOFError:
            return Symbol("eof-object")

    @prim("read-char")
    def read_char(*args: Any) -> Any:
        port = args[0] if args else None
        try:
            if port is not None and isinstance(port, Port):
                ch = port.file.read(1)
            else:
                # Read from stdin
                import sys
                ch = sys.stdin.read(1)
            if not ch:
                return Symbol("eof-object")
            return Char(ch)
        except EOFError:
            return Symbol("eof-object")

    @prim("peek-char")
    def peek_char(*args: Any) -> Any:
        return Symbol("eof-object")  # simplified

    @prim("read-line")
    def read_line(*args: Any) -> Any:
        port = args[0] if args else None
        try:
            if port is not None and isinstance(port, Port):
                line = port.file.readline()
            else:
                line = input()
            if line is None:
                return Symbol("eof-object")
            return SchemeString(line)
        except EOFError:
            return Symbol("eof-object")

    @prim("eof-object?")
    def eof_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Symbol) and x.name == "eof-object")

    @prim("eof-object")
    def eof_obj() -> Symbol:
        return Symbol("eof-object")

    @prim("char-ready?")
    def char_ready(*args: Any) -> Boolean:
        return TRUE

    @prim("open-input-file")
    def open_input_file(path: Any) -> Port:
        s = _check_str(path, "open-input-file")
        return Port(open(s, "r", encoding="utf-8"), "r")

    @prim("open-output-file")
    def open_output_file(path: Any) -> Port:
        s = _check_str(path, "open-output-file")
        return Port(open(s, "w", encoding="utf-8"), "w")

    @prim("close-input-port")
    def close_input_port(port: Any) -> Any:
        if isinstance(port, Port):
            port.close()
        return VOID

    @prim("close-output-port")
    def close_output_port(port: Any) -> Any:
        if isinstance(port, Port):
            port.close()
        return VOID

    @prim("close-port")
    def close_port(port: Any) -> Any:
        if isinstance(port, Port):
            port.close()
        return VOID

    @prim("input-port?")
    def input_port_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Port) and x.mode == "r")

    @prim("output-port?")
    def output_port_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Port) and x.mode == "w")

    @prim("port?")
    def port_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, Port))

    @prim("current-input-port")
    def current_input_port() -> Port:
        return Port(sys.stdin, "r")

    @prim("current-output-port")
    def current_output_port() -> Port:
        return Port(sys.stdout, "w")

    @prim("current-error-port")
    def current_error_port() -> Port:
        return Port(sys.stderr, "w")

    @prim("with-input-from-file")
    def with_input_from_file(path: Any, thunk: Any) -> Any:
        s = _check_str(path, "with-input-from-file")
        with open(s, "r", encoding="utf-8") as f:
            old_stdin = sys.stdin
            sys.stdin = f
            try:
                return _apply_proc(thunk, [])
            finally:
                sys.stdin = old_stdin

    @prim("with-output-to-file")
    def with_output_to_file(path: Any, thunk: Any) -> Any:
        s = _check_str(path, "with-output-to-file")
        with open(s, "w", encoding="utf-8") as f:
            old_stdout = sys.stdout
            sys.stdout = f
            try:
                return _apply_proc(thunk, [])
            finally:
                sys.stdout = old_stdout

    @prim("call-with-port")
    def call_with_port(port: Any, proc: Any) -> Any:
        try:
            return _apply_proc(proc, [port])
        finally:
            if isinstance(port, Port):
                port.close()

    @prim("call-with-input-file")
    def call_with_input_file(path: Any, proc: Any) -> Any:
        s = _check_str(path, "call-with-input-file")
        port = Port(open(s, "r", encoding="utf-8"), "r")
        try:
            return _apply_proc(proc, [port])
        finally:
            port.close()

    @prim("call-with-output-file")
    def call_with_output_file(path: Any, proc: Any) -> Any:
        s = _check_str(path, "call-with-output-file")
        port = Port(open(s, "w", encoding="utf-8"), "w")
        try:
            return _apply_proc(proc, [port])
        finally:
            port.close()

    @prim("open-input-string")
    def open_input_string(s: Any) -> Port:
        import io
        sv = _check_str(s, "open-input-string")
        return Port(io.StringIO(sv), "r")

    @prim("open-output-string")
    def open_output_string() -> Port:
        import io
        return Port(io.StringIO(), "w")

    @prim("get-output-string")
    def get_output_string(port: Any) -> SchemeString:
        if not isinstance(port, Port):
            raise SchemeTypeError(f"get-output-string: not a port")
        return SchemeString(port.file.getvalue())

    @prim("with-exception-handler")
    def with_exception_handler(handler: Any, thunk: Any) -> Any:
        try:
            return _apply_proc(thunk, [])
        except SchemeError as e:
            return _apply_proc(handler, [SchemeString(str(e))])
        except Exception as e:
            return _apply_proc(handler, [SchemeString(str(e))])

    @prim("raise")
    def scheme_raise(obj: Any) -> Any:
        raise SchemeRuntimeError(scheme_display(obj))

    @prim("raise-continuable")
    def raise_continuable(obj: Any) -> Any:
        raise SchemeRuntimeError(scheme_display(obj))

    @prim("error")
    def scheme_error(msg: Any, *irritants: Any) -> Any:
        m = _check_str(msg, "error") if isinstance(msg, SchemeString) else scheme_display(msg)
        if irritants:
            parts = " ".join(scheme_repr(i) for i in irritants)
            raise SchemeRuntimeError(f"{m} {parts}")
        raise SchemeRuntimeError(m)

    @prim("error-message")
    def error_message(e: Any) -> SchemeString:
        if isinstance(e, SchemeString):
            return e
        return SchemeString(str(e))

    @prim("guard")
    def guard_form(*args: Any) -> Any:
        # guard is actually a special form; this placeholder should not be called directly
        raise SchemeRuntimeError("guard: must be used as special form")

    # -------------------------------------------------------------------------
    # System / misc
    # -------------------------------------------------------------------------

    @prim("exit")
    def scheme_exit(*args: Any) -> Any:
        code = int(args[0]) if args else 0
        raise SystemExit(code)

    @prim("load")
    def scheme_load(path: Any, env: Any = None) -> Any:
        s = _check_str(path, "load")
        from sucheme.interpreter import Interpreter
        # This will be called with an interpreter context; simplified here
        with open(s, "r", encoding="utf-8") as f:
            source = f.read()
        return SchemeString(f"loaded {s}")

    @prim("eval")
    def scheme_eval_prim(expr: Any, *args: Any) -> Any:
        # Simplified: evaluate in global env
        raise SchemeRuntimeError("eval: use interpreter.eval instead")

    @prim("interaction-environment")
    def interaction_env() -> Any:
        return Symbol("interaction-environment")

    @prim("scheme-report-environment")
    def scheme_report_env(n: Any) -> Any:
        return Symbol("scheme-report-environment")

    @prim("null-environment")
    def null_env(n: Any) -> Any:
        return Symbol("null-environment")

    @prim("void")
    def scheme_void(*args: Any) -> Any:
        return VOID

    @prim("gensym")
    def scheme_gensym(*args: Any) -> Symbol:
        prefix = _check_str(args[0], "gensym") if args else "g"
        import uuid
        return Symbol(f"{prefix}{uuid.uuid4().hex[:8]}")

    @prim("format")
    def scheme_format(*args: Any) -> Any:
        """(format dest fmt args...)"""
        _check_min_args(args, 1, "format")
        dest = args[0]
        if isinstance(dest, Boolean) and dest is FALSE:
            # return string
            fmt = args[1]
            fmt_args = args[2:]
            result = _format_string(_check_str(fmt, "format"), fmt_args)
            return SchemeString(result)
        elif isinstance(dest, Boolean) and dest is TRUE:
            fmt = args[1]
            fmt_args = args[2:]
            result = _format_string(_check_str(fmt, "format"), fmt_args)
            print(result, end="")
            return VOID
        elif isinstance(dest, SchemeString):
            # dest is format string, rest are args
            result = _format_string(dest.value, args[1:])
            return SchemeString(result)
        else:
            fmt = args[1]
            fmt_args = args[2:]
            result = _format_string(_check_str(fmt, "format"), fmt_args)
            print(result, end="")
            return VOID

    def _format_string(fmt: str, args: tuple) -> str:
        result = []
        arg_iter = iter(args)
        i = 0
        while i < len(fmt):
            if fmt[i] == "~":
                i += 1
                if i >= len(fmt):
                    break
                c = fmt[i]
                if c == "a":
                    result.append(scheme_display(next(arg_iter)))
                elif c == "s":
                    result.append(scheme_repr(next(arg_iter)))
                elif c == "%":
                    result.append("\n")
                elif c == "~":
                    result.append("~")
                elif c == "b":
                    result.append(scheme_display(next(arg_iter)))
                else:
                    result.append(f"~{c}")
            else:
                result.append(fmt[i])
            i += 1
        return "".join(result)

    @prim("pretty-print")
    def pretty_print(x: Any) -> Any:
        print(scheme_repr(x))
        return VOID

    @prim("pp")
    def pp(x: Any) -> Any:
        print(scheme_repr(x))
        return VOID

    @prim("print")
    def scheme_print(x: Any) -> Any:
        print(scheme_display(x))
        return VOID

    @prim("println")
    def scheme_println(x: Any) -> Any:
        print(scheme_display(x))
        return VOID

    # -------------------------------------------------------------------------
    # Type predicates
    # -------------------------------------------------------------------------

    @prim("promise?")
    def promise_p(x: Any) -> Boolean:
        from sucheme.evaluator import _Promise
        return scheme_bool(isinstance(x, _Promise))

    @prim("make-promise")
    def make_promise(x: Any) -> Any:
        from sucheme.evaluator import _Promise
        if isinstance(x, _Promise):
            return x
        p2 = _Promise(None)
        p2._forced = True
        p2._value = x
        return p2

    @prim("force")
    def force_prim(x: Any) -> Any:
        from sucheme.evaluator import _force_promise
        return _force_promise(x)

    # -------------------------------------------------------------------------
    # Multiple values
    # -------------------------------------------------------------------------

    @prim("values")
    def values_prim(*args: Any) -> Any:
        if len(args) == 1:
            return args[0]
        return Values(*args)

    @prim("call-with-values")
    def call_with_values(producer: Any, consumer: Any) -> Any:
        result = _apply_proc(producer, [])
        if isinstance(result, Values):
            return _apply_proc(consumer, result.values)
        return _apply_proc(consumer, [result])

    # -------------------------------------------------------------------------
    # Tail calls
    # -------------------------------------------------------------------------

    @prim("not-pair?")
    def not_pair_p(x: Any) -> Boolean:
        return scheme_bool(not isinstance(x, Pair))

    @prim("last-pair")
    def last_pair(lst: Any) -> Any:
        if not isinstance(lst, Pair):
            raise SchemeTypeError(f"last-pair: not a pair: {lst!r}")
        while isinstance(lst.cdr, Pair):
            lst = lst.cdr
        return lst

    @prim("list*")
    def list_star(*args: Any) -> Any:
        if not args:
            return NIL
        if len(args) == 1:
            return args[0]
        result = args[-1]
        for item in reversed(args[:-1]):
            result = Pair(item, result)
        return result

    p["cons*"] = p["list*"]

    @prim("any")
    def scheme_any(pred: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            val = _apply_proc(pred, [cur.car])
            if val is not FALSE:
                return val
            cur = cur.cdr
        return FALSE

    @prim("every")
    def scheme_every(pred: Any, lst: Any) -> Any:
        cur = lst
        last = TRUE
        while isinstance(cur, Pair):
            last = _apply_proc(pred, [cur.car])
            if last is FALSE:
                return FALSE
            cur = cur.cdr
        return last

    @prim("count")
    def scheme_count(pred: Any, lst: Any) -> int:
        n = 0
        cur = lst
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is not FALSE:
                n += 1
            cur = cur.cdr
        return n

    @prim("take")
    def scheme_take(lst: Any, n: int) -> Any:
        _check_int(n, "take")
        items = []
        cur = lst
        for _ in range(int(n)):
            if not isinstance(cur, Pair):
                raise SchemeRuntimeError("take: list too short")
            items.append(cur.car)
            cur = cur.cdr
        return list_to_scheme(items)

    @prim("drop")
    def scheme_drop(lst: Any, n: int) -> Any:
        _check_int(n, "drop")
        cur = lst
        for _ in range(int(n)):
            if not isinstance(cur, Pair):
                raise SchemeRuntimeError("drop: list too short")
            cur = cur.cdr
        return cur

    @prim("zip")
    def scheme_zip(*lsts: Any) -> Any:
        if not lsts:
            return NIL
        result = []
        iters = list(lsts)
        while all(isinstance(l, Pair) for l in iters):
            result.append(list_to_scheme([l.car for l in iters]))
            iters = [l.cdr for l in iters]
        return list_to_scheme(result)

    @prim("flatten")
    def scheme_flatten(lst: Any) -> Any:
        result = []
        def flatten_helper(x: Any) -> None:
            if x is NIL:
                return
            if isinstance(x, Pair):
                flatten_helper(x.car)
                flatten_helper(x.cdr)
            else:
                result.append(x)
        flatten_helper(lst)
        return list_to_scheme(result)

    @prim("delete-duplicates")
    def delete_duplicates(lst: Any) -> Any:
        seen = []
        result = []
        cur = lst
        while isinstance(cur, Pair):
            if not any(_equal(cur.car, s) for s in seen):
                seen.append(cur.car)
                result.append(cur.car)
            cur = cur.cdr
        return list_to_scheme(result)

    @prim("list-index")
    def list_index(pred: Any, lst: Any) -> Any:
        cur = lst
        i = 0
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is not FALSE:
                return i
            cur = cur.cdr
            i += 1
        return FALSE

    @prim("find")
    def scheme_find(pred: Any, lst: Any) -> Any:
        cur = lst
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is not FALSE:
                return cur.car
            cur = cur.cdr
        return FALSE

    @prim("remove")
    def scheme_remove(pred: Any, lst: Any) -> Any:
        result = []
        cur = lst
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is FALSE:
                result.append(cur.car)
            cur = cur.cdr
        return list_to_scheme(result)

    @prim("partition")
    def scheme_partition(pred: Any, lst: Any) -> Values:
        yes, no = [], []
        cur = lst
        while isinstance(cur, Pair):
            if _apply_proc(pred, [cur.car]) is not FALSE:
                yes.append(cur.car)
            else:
                no.append(cur.car)
            cur = cur.cdr
        return Values(list_to_scheme(yes), list_to_scheme(no))

    @prim("append-map")
    def append_map(proc: Any, lst: Any) -> Any:
        result = NIL
        items = []
        cur = lst
        while isinstance(cur, Pair):
            val = _apply_proc(proc, [cur.car])
            items.append(val)
            cur = cur.cdr
        # append all
        result = NIL
        for v in reversed(items):
            cur2 = v
            while isinstance(cur2, Pair):
                result = Pair(cur2.car, result)
                cur2 = cur2.cdr
        return result

    @prim("flat-map")
    def flat_map(proc: Any, lst: Any) -> Any:
        return p["append-map"]._fn(proc, lst)

    @prim("string-join")
    def string_join(lst: Any, *args: Any) -> SchemeString:
        sep = _check_str(args[0], "string-join") if args else ""
        parts = []
        cur = lst
        while isinstance(cur, Pair):
            parts.append(_check_str(cur.car, "string-join"))
            cur = cur.cdr
        return SchemeString(sep.join(parts))

    @prim("string-trim")
    def string_trim(*args: Any) -> SchemeString:
        _check_min_args(args, 1, "string-trim")
        s = _check_str(args[0], "string-trim")
        return SchemeString(s.lstrip())

    @prim("string-trim-right")
    def string_trim_right(*args: Any) -> SchemeString:
        _check_min_args(args, 1, "string-trim-right")
        s = _check_str(args[0], "string-trim-right")
        return SchemeString(s.rstrip())

    @prim("string-pad-left")
    def string_pad_left(s: Any, n: Any, *args: Any) -> SchemeString:
        sv = _check_str(s, "string-pad-left")
        ch = args[0].char if args else " "
        return SchemeString(sv.rjust(int(n), ch))

    @prim("string-pad-right")
    def string_pad_right(s: Any, n: Any, *args: Any) -> SchemeString:
        sv = _check_str(s, "string-pad-right")
        ch = args[0].char if args else " "
        return SchemeString(sv.ljust(int(n), ch))

    @prim("string-prefix?")
    def string_prefix(prefix: Any, s: Any) -> Boolean:
        return scheme_bool(_check_str(s, "string-prefix?").startswith(_check_str(prefix, "string-prefix?")))

    @prim("string-suffix?")
    def string_suffix(suffix: Any, s: Any) -> Boolean:
        return scheme_bool(_check_str(s, "string-suffix?").endswith(_check_str(suffix, "string-suffix?")))

    # -------------------------------------------------------------------------
    # Association list helpers
    # -------------------------------------------------------------------------

    @prim("alist->hash-table")
    def alist_to_hash(alist: Any) -> dict:
        result = {}
        cur = alist
        while isinstance(cur, Pair):
            pair = cur.car
            if isinstance(pair, Pair):
                result[pair.car] = pair.cdr
            cur = cur.cdr
        return result

    # -------------------------------------------------------------------------
    # Hash tables (basic)
    # -------------------------------------------------------------------------

    @prim("make-hash-table")
    def make_hash_table(*args: Any) -> dict:
        return {}

    @prim("make-equal-hash-table")
    def make_equal_hash_table(*args: Any) -> dict:
        return {}

    @prim("hash-table?")
    def hash_table_p(x: Any) -> Boolean:
        return scheme_bool(isinstance(x, dict))

    @prim("hash-table-set!")
    def hash_table_set(ht: Any, key: Any, val: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table-set!: not a hash table")
        ht[_hash_key(key)] = val
        return VOID

    @prim("hash-table/put!")
    def hash_table_put(ht: Any, key: Any, val: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table/put!: not a hash table")
        ht[_hash_key(key)] = val
        return VOID

    @prim("hash-table-ref")
    def hash_table_ref(ht: Any, key: Any, *args: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table-ref: not a hash table")
        k = _hash_key(key)
        if k in ht:
            return ht[k]
        if args:
            return _apply_proc(args[0], [])
        raise SchemeRuntimeError(f"hash-table-ref: key not found: {key!r}")

    @prim("hash-table/get")
    def hash_table_get(ht: Any, key: Any, default: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table/get: not a hash table")
        return ht.get(_hash_key(key), default)

    @prim("hash-table-ref/default")
    def hash_table_ref_default(ht: Any, key: Any, default: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table-ref/default: not a hash table")
        return ht.get(_hash_key(key), default)

    @prim("hash-table-delete!")
    def hash_table_delete(ht: Any, key: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table-delete!: not a hash table")
        ht.pop(_hash_key(key), None)
        return VOID

    @prim("hash-table-size")
    def hash_table_size(ht: Any) -> int:
        return len(ht)

    @prim("hash-table->alist")
    def hash_table_to_alist(ht: Any) -> Any:
        if not isinstance(ht, dict):
            raise SchemeTypeError("hash-table->alist: not a hash table")
        return list_to_scheme([Pair(_unhash_key(k), v) for k, v in ht.items()])

    @prim("hash-table-keys")
    def hash_table_keys(ht: Any) -> Any:
        return list_to_scheme([_unhash_key(k) for k in ht.keys()])

    @prim("hash-table-values")
    def hash_table_values(ht: Any) -> Any:
        return list_to_scheme(list(ht.values()))

    @prim("hash-table-walk")
    def hash_table_walk(ht: Any, proc: Any) -> Any:
        for k, v in ht.items():
            _apply_proc(proc, [_unhash_key(k), v])
        return VOID

    def _hash_key(key: Any) -> Any:
        if isinstance(key, SchemeString):
            return ("string", key.value)
        if isinstance(key, Symbol):
            return ("symbol", key.name)
        if isinstance(key, (int, float, bool)):
            return key
        return id(key)

    def _unhash_key(key: Any) -> Any:
        if isinstance(key, tuple) and key[0] == "string":
            return SchemeString(key[1])
        if isinstance(key, tuple) and key[0] == "symbol":
            return Symbol(key[1])
        return key

    # -------------------------------------------------------------------------
    # Numeric utilities
    # -------------------------------------------------------------------------

    @prim("random")
    def scheme_random(n: Any) -> Any:
        import random
        if isinstance(n, int):
            return random.randint(0, n - 1)
        return random.random()

    @prim("current-time")
    def current_time() -> float:
        import time
        return time.time()

    @prim("runtime")
    def runtime() -> float:
        import time
        return time.process_time()

    @prim("with-values")
    def with_values(producer: Any, consumer: Any) -> Any:
        return p["call-with-values"]._fn(producer, consumer)

    # -------------------------------------------------------------------------
    # Dynamic binding
    # -------------------------------------------------------------------------

    @prim("make-parameter")
    def make_parameter(init: Any, *args: Any) -> Any:
        """Create a parameter object (SRFI-39)."""
        converter = args[0] if args else None
        val = [converter(init) if converter else init]

        def param(*pargs: Any) -> Any:
            if not pargs:
                return val[0]
            val[0] = pargs[0]
            return VOID

        return PrimitiveProcedure(param, "parameter")

    @prim("parameterize")
    def parameterize_prim(*args: Any) -> Any:
        raise SchemeRuntimeError("parameterize must be used as special form")

    # -------------------------------------------------------------------------
    # Tail call
    # -------------------------------------------------------------------------

    @prim("char-foldcase")
    def char_foldcase(x: Any) -> Char:
        if not isinstance(x, Char):
            raise SchemeTypeError(f"char-foldcase: not a char")
        return Char(x.char.lower())

    @prim("string-foldcase")
    def string_foldcase(x: Any) -> SchemeString:
        return SchemeString(_check_str(x, "string-foldcase").casefold())

    # -------------------------------------------------------------------------
    # Boolean
    # -------------------------------------------------------------------------
    p["#t"] = TRUE
    p["#f"] = FALSE

    return p


# ---------------------------------------------------------------------------
# Helper checkers
# ---------------------------------------------------------------------------

def _check_num(x: Any, name: str) -> None:
    if not isinstance(x, (int, float, complex, Fraction)):
        raise SchemeTypeError(f"{name}: not a number: {x!r}")


def _check_real(x: Any, name: str) -> None:
    if isinstance(x, complex):
        raise SchemeTypeError(f"{name}: complex not allowed: {x!r}")
    if not isinstance(x, (int, float, Fraction)):
        raise SchemeTypeError(f"{name}: not a real number: {x!r}")


def _check_int(x: Any, name: str) -> None:
    if not is_integer_val(x):
        raise SchemeTypeError(f"{name}: not an integer: {x!r}")


def _check_str(x: Any, name: str) -> str:
    if isinstance(x, SchemeString):
        return x.value
    raise SchemeTypeError(f"{name}: not a string: {x!r}")


def _check_min_args(args: tuple, n: int, name: str) -> None:
    if len(args) < n:
        raise SchemeArityError(f"{name}: expected at least {n} args, got {len(args)}")


def _apply_proc(proc: Any, args: list) -> Any:
    """Apply a procedure to args (bridges to evaluator)."""
    from sucheme.evaluator import _apply
    return _apply(proc, args)


# ---------------------------------------------------------------------------
# Arithmetic helpers
# ---------------------------------------------------------------------------

def _num_add(a: Any, b: Any) -> Any:
    from fractions import Fraction as F
    if isinstance(a, complex) or isinstance(b, complex):
        return complex(a) + complex(b)
    if isinstance(a, float) or isinstance(b, float):
        return float(a) + float(b)
    if isinstance(a, F) or isinstance(b, F):
        return F(a) + F(b)
    return a + b


def _num_sub(a: Any, b: Any) -> Any:
    from fractions import Fraction as F
    if isinstance(a, complex) or isinstance(b, complex):
        return complex(a) - complex(b)
    if isinstance(a, float) or isinstance(b, float):
        return float(a) - float(b)
    if isinstance(a, F) or isinstance(b, F):
        return F(a) - F(b)
    return a - b


def _num_mul(a: Any, b: Any) -> Any:
    from fractions import Fraction as F
    if isinstance(a, complex) or isinstance(b, complex):
        return complex(a) * complex(b)
    if isinstance(a, float) or isinstance(b, float):
        return float(a) * float(b)
    if isinstance(a, F) or isinstance(b, F):
        return F(a) * F(b)
    return a * b


def _num_div(a: Any, b: Any) -> Any:
    from fractions import Fraction as F
    if isinstance(b, int) and b == 0:
        raise SchemeRuntimeError("/: division by zero")
    if isinstance(a, complex) or isinstance(b, complex):
        return complex(a) / complex(b)
    if isinstance(a, float) or isinstance(b, float):
        if float(b) == 0.0:
            raise SchemeRuntimeError("/: division by zero")
        return float(a) / float(b)
    # exact division: return fraction
    return normalize_number(F(a) / F(b))


def _num_neg(a: Any) -> Any:
    from fractions import Fraction as F
    if isinstance(a, complex):
        return -a
    if isinstance(a, float):
        return -a
    if isinstance(a, F):
        return F(-a.numerator, a.denominator)
    return -a


def _num_inv(a: Any) -> Any:
    from fractions import Fraction as F
    if a == 0:
        raise SchemeRuntimeError("/: division by zero")
    if isinstance(a, complex):
        return 1 / a
    if isinstance(a, float):
        return 1.0 / a
    return normalize_number(F(1, a) if isinstance(a, int) else F(1) / F(a))
