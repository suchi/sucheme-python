"""
Main interpreter for sucheme.

Provides the Interpreter class that ties together lexer, parser,
evaluator, and the global environment.
"""

from __future__ import annotations

import sys
from typing import Any

from sucheme.environment import Environment
from sucheme.evaluator import (
    _apply,
    eval_expr,
    make_callcc_primitive,
    make_dynamic_wind_primitive,
)
from sucheme.parser import parse
from sucheme.primitives import register_primitives
from sucheme.types import (
    NIL,
    VOID,
    Pair,
    PrimitiveProcedure,
    SchemeString,
    SchemeTypeError,
)

# Standard library Scheme code (bootstrap macros / functions)
_STDLIB_SCM = r"""
; ---- R5RS standard library implemented in Scheme ----

; not (already in primitives but define here for completeness)

; boolean utils
(define (boolean=? . bools)
  (or (null? bools)
      (let loop ((b (car bools)) (rest (cdr bools)))
        (if (null? rest)
            #t
            (and (eq? b (car rest))
                 (loop b (cdr rest)))))))

; caar cdar etc. handled in primitives

; R5RS Appendix: derived expressions as macros

(define-syntax and
  (syntax-rules ()
    ((and) #t)
    ((and e) e)
    ((and e1 e2 ...)
     (if e1 (and e2 ...) #f))))

(define-syntax or
  (syntax-rules ()
    ((or) #f)
    ((or e) e)
    ((or e1 e2 ...)
     (let ((t e1))
       (if t t (or e2 ...))))))

(define-syntax when
  (syntax-rules ()
    ((when test body ...)
     (if test (begin body ...) (void)))))

(define-syntax unless
  (syntax-rules ()
    ((unless test body ...)
     (if test (void) (begin body ...)))))

(define-syntax cond
  (syntax-rules (else =>)
    ((cond (else e ...)) (begin e ...))
    ((cond (test => proc) rest ...)
     (let ((t test))
       (if t (proc t) (cond rest ...))))
    ((cond (test) rest ...)
     (or test (cond rest ...)))
    ((cond (test e ...) rest ...)
     (if test (begin e ...) (cond rest ...)))
    ((cond) (void))))

(define-syntax case
  (syntax-rules (else)
    ((case key
       (else e ...))
     (begin e ...))
    ((case key
       ((datum ...) e ...)
       rest ...)
     (if (memv key '(datum ...))
         (begin e ...)
         (case key rest ...)))
    ((case key) (void))))

(define-syntax let
  (syntax-rules ()
    ; Named let
    ((let name ((var val) ...) body ...)
     ((letrec ((name (lambda (var ...) body ...)))
        name)
      val ...))
    ; Normal let
    ((let ((var val) ...) body ...)
     ((lambda (var ...) body ...) val ...))))

(define-syntax let*
  (syntax-rules ()
    ((let* () body ...)
     (let () body ...))
    ((let* ((var val) rest ...) body ...)
     (let ((var val))
       (let* (rest ...) body ...)))))

(define-syntax letrec
  (syntax-rules ()
    ((letrec ((var init) ...) body ...)
     (let ((var (void)) ...)
       (set! var init) ...
       body ...))))

(define-syntax letrec*
  (syntax-rules ()
    ((letrec* ((var init) ...) body ...)
     (let ((var (void)) ...)
       (set! var init) ...
       body ...))))

(define-syntax do
  (syntax-rules ()
    ((do ((var init step ...) ...)
         (test expr ...)
       command ...)
     (let loop ((var init) ...)
       (if test
           (begin expr ...)
           (begin
             command ...
             (loop (if (null? '(step ...))
                       var
                       (car '(step ...)))
                   ...)))))))

(define-syntax delay
  (syntax-rules ()
    ((delay expr)
     (make-promise (lambda () expr)))))

(define-syntax delay-force
  (syntax-rules ()
    ((delay-force expr)
     (make-promise (lambda () expr)))))

(define-syntax parameterize
  (syntax-rules ()
    ((parameterize ((param val) ...) body ...)
     (let ((old (list (param) ...))
           (params (list param ...))
           (vals (list val ...)))
       (dynamic-wind
         (lambda ()
           (for-each (lambda (p v) (p v)) params vals))
         (lambda () body ...)
         (lambda ()
           (for-each (lambda (p v) (p v)) params old)))))))

(define-syntax guard
  (syntax-rules (else)
    ((guard (var clause ... (else e ...)) body ...)
     (call-with-current-continuation
       (lambda (k)
         (with-exception-handler
           (lambda (var)
             (cond clause ... (else (k (begin e ...)))))
           (lambda () body ...)))))
    ((guard (var clause ...) body ...)
     (call-with-current-continuation
       (lambda (k)
         (with-exception-handler
           (lambda (var)
             (cond clause ... (else (raise var))))
           (lambda () body ...)))))))

(define-syntax receive
  (syntax-rules ()
    ((receive formals expression body ...)
     (call-with-values (lambda () expression)
       (lambda formals body ...)))))

(define-syntax fluid-let
  (syntax-rules ()
    ((fluid-let ((var val) ...) body ...)
     (let ((old-vals (list var ...)))
       (dynamic-wind
         (lambda () (set! var val) ...)
         (lambda () body ...)
         (lambda ()
           (for-each (lambda (v ov) (set! v ov))
                     (list var ...) old-vals)))))))

; Common list procedures

(define (list-head lst k)
  (if (= k 0)
      '()
      (cons (car lst) (list-head (cdr lst) (- k 1)))))

(define (append! . lsts)
  (apply append lsts))

(define (list-copy lst)
  (if (null? lst)
      '()
      (cons (car lst) (list-copy (cdr lst)))))

; Numeric
(define (square x) (* x x))
(define (cube x) (* x x x))
(define (average x y) (/ (+ x y) 2))

; Higher-order
(define (compose . fns)
  (if (null? fns)
      (lambda (x) x)
      (let ((fn (car fns))
            (rest (apply compose (cdr fns))))
        (lambda args
          (fn (apply rest args))))))

(define (identity x) x)
(define (const x) (lambda _ x))
(define (negate pred) (lambda (x) (not (pred x))))
(define (complement pred) (lambda args (not (apply pred args))))

(define (flip f) (lambda (a b) (f b a)))

(define (curry f . args)
  (lambda rest-args
    (apply f (append args rest-args))))

; Number predicates
(define (natural? n) (and (integer? n) (>= n 0)))
(define (positive-integer? n) (and (integer? n) (> n 0)))

; Association list
(define (alist-cons key val alist) (cons (cons key val) alist))
(define (alist-copy alist) (map (lambda (pair) (cons (car pair) (cdr pair))) alist))
(define (alist-delete key alist)
  (filter (lambda (pair) (not (equal? (car pair) key))) alist))

; String
(define (string-repeat str n)
  (let loop ((i 0) (acc ""))
    (if (= i n) acc (loop (+ i 1) (string-append acc str)))))

(define (string-reverse s)
  (list->string (reverse (string->list s))))

(define (number->padded-string n width)
  (let ((s (number->string n)))
    (if (>= (string-length s) width)
        s
        (string-append (make-string (- width (string-length s)) #\0) s))))

; I/O helpers
(define (writeln x)
  (write x)
  (newline))

(define (displayln x)
  (display x)
  (newline))

(define (with-string-output-port thunk)
  (let ((port (open-output-string)))
    (with-output-to-port port thunk)
    (get-output-string port)))

; Tail-recursive list utilities
(define (append-reverse rev-head tail)
  (if (null? rev-head)
      tail
      (append-reverse (cdr rev-head) (cons (car rev-head) tail))))

(define (concatenate lsts) (apply append lsts))

; Math helpers
(define pi (* 4 (atan 1)))
(define (degrees->radians d) (* d (/ pi 180)))
(define (radians->degrees r) (* r (/ 180 pi)))

(define (factorial n)
  (let loop ((i n) (acc 1))
    (if (<= i 0) acc (loop (- i 1) (* acc i)))))

(define (fibonacci n)
  (let loop ((i 0) (a 0) (b 1))
    (if (= i n) a (loop (+ i 1) b (+ a b)))))

; Tail position version of map
(define (map-tail f lst)
  (let loop ((rest lst) (acc '()))
    (if (null? rest)
        (reverse acc)
        (loop (cdr rest) (cons (f (car rest)) acc)))))

; Void predicate
(define (void? x) (eq? x (void)))
"""


class Interpreter:
    """R5RS Scheme interpreter."""

    def __init__(self, load_stdlib: bool = True) -> None:
        self.env = self._make_global_env()
        if load_stdlib:
            self._load_stdlib()

    def _make_global_env(self) -> Environment:
        env = Environment()
        register_primitives(env)

        # call/cc
        callcc = make_callcc_primitive()
        env.define("call-with-current-continuation", callcc)
        env.define("call/cc", callcc)

        # dynamic-wind
        env.define("dynamic-wind", make_dynamic_wind_primitive())

        # eval: use this interpreter
        interp = self

        def scheme_eval(expr: Any, *args: Any) -> Any:
            return interp.eval_expr(expr)

        env.define("eval", PrimitiveProcedure(scheme_eval, "eval"))

        # load
        def scheme_load(path: Any) -> Any:
            s = path.value if isinstance(path, SchemeString) else str(path)
            return interp.load_file(s)

        env.define("load", PrimitiveProcedure(scheme_load, "load"))

        # with-output-to-port
        def with_output_to_port(port: Any, thunk: Any) -> Any:
            from sucheme.types import Port
            if isinstance(port, Port):
                old_stdout = sys.stdout
                sys.stdout = port.file
                try:
                    return _apply(thunk, [])
                finally:
                    sys.stdout = old_stdout
            return _apply(thunk, [])

        env.define("with-output-to-port", PrimitiveProcedure(with_output_to_port, "with-output-to-port"))

        # environment procedures
        def interaction_environment() -> Any:
            return env

        def make_report_environment(n: Any) -> Any:
            """Return a new environment with R5RS standard bindings (copy)."""
            new_env = Environment(parent=None)
            # Copy all bindings as a snapshot; modifications won't affect the original
            frame: Environment | None = env
            while frame is not None:
                for k, v in frame.bindings.items():
                    if k not in new_env.bindings:
                        new_env.bindings[k] = v
                frame = frame.parent
            return new_env

        def make_null_environment(n: Any) -> Any:
            """Return an empty environment (no standard bindings)."""
            return Environment(parent=None)

        env.define("interaction-environment", PrimitiveProcedure(interaction_environment, "interaction-environment"))
        env.define("scheme-report-environment", PrimitiveProcedure(make_report_environment, "scheme-report-environment"))
        env.define("null-environment", PrimitiveProcedure(make_null_environment, "null-environment"))

        # Re-define eval properly
        def eval_in_env(expr: Any, env_arg: Any = None) -> Any:
            target_env = env if env_arg is None or not isinstance(env_arg, Environment) else env_arg
            return interp.eval_expr(expr, target_env)

        env.define("eval", PrimitiveProcedure(eval_in_env, "eval"))

        # apply
        def scheme_apply_top(proc: Any, *args: Any) -> Any:
            from sucheme.primitives import _apply_proc
            if not args:
                raise SchemeTypeError("apply: no arguments")
            actual_args = list(args[:-1])
            last = args[-1]
            cur = last
            while isinstance(cur, Pair):
                actual_args.append(cur.car)
                cur = cur.cdr
            if cur is not NIL:
                raise SchemeTypeError("apply: last argument not a proper list")
            return _apply_proc(proc, actual_args)

        env.define("apply", PrimitiveProcedure(scheme_apply_top, "apply"))

        return env

    def _load_stdlib(self) -> None:
        """Load the standard library implemented in Scheme."""
        try:
            exprs = parse(_STDLIB_SCM)
            for expr in exprs:
                eval_expr(expr, self.env)
        except Exception as e:
            # Don't fail on stdlib errors - just warn
            print(f"Warning: stdlib error: {e}", file=sys.stderr)

    def eval_expr(self, expr: Any, env: Environment | None = None) -> Any:
        """Evaluate a parsed expression."""
        target = env if env is not None else self.env
        return eval_expr(expr, target)

    def eval_string(self, source: str) -> list[Any]:
        """Parse and evaluate a source string, returning all results."""
        exprs = parse(source)
        results = []
        for expr in exprs:
            result = eval_expr(expr, self.env)
            results.append(result)
        return results

    def eval_string_last(self, source: str) -> Any:
        """Parse and evaluate a source string, returning the last result."""
        results = self.eval_string(source)
        if not results:
            return VOID
        return results[-1]

    def load_file(self, path: str) -> Any:
        """Load and execute a Scheme file."""
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        results = self.eval_string(source)
        return results[-1] if results else VOID
