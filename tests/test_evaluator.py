"""Tests for the evaluator / interpreter."""

import pytest
from fractions import Fraction

from sucheme.interpreter import Interpreter
from sucheme.types import (
    NIL, VOID, TRUE, FALSE,
    Symbol, Pair, Vector, Char, SchemeString,
    SchemeError, SchemeRuntimeError, SchemeTypeError, SchemeNameError,
    scheme_repr,
)


@pytest.fixture
def interp():
    return Interpreter()


def ev(interp, s):
    """Evaluate string and return last result."""
    return interp.eval_string_last(s)


def ev_all(interp, s):
    """Evaluate string and return all results."""
    return interp.eval_string(s)


class TestSelfEvaluating:
    def test_integer(self, interp):
        assert ev(interp, "42") == 42

    def test_negative(self, interp):
        assert ev(interp, "-7") == -7

    def test_float(self, interp):
        assert abs(ev(interp, "3.14") - 3.14) < 1e-10

    def test_string(self, interp):
        r = ev(interp, '"hello"')
        assert isinstance(r, SchemeString)
        assert r.value == "hello"

    def test_bool_true(self, interp):
        assert ev(interp, "#t") is TRUE

    def test_bool_false(self, interp):
        assert ev(interp, "#f") is FALSE

    def test_nil(self, interp):
        assert ev(interp, "'()") is NIL

    def test_char(self, interp):
        r = ev(interp, "#\\a")
        assert isinstance(r, Char)
        assert r.char == "a"


class TestArithmetic:
    def test_add(self, interp):
        assert ev(interp, "(+ 1 2 3)") == 6

    def test_sub(self, interp):
        assert ev(interp, "(- 10 3)") == 7

    def test_mul(self, interp):
        assert ev(interp, "(* 2 3 4)") == 24

    def test_div(self, interp):
        assert ev(interp, "(/ 10 2)") == 5

    def test_div_rational(self, interp):
        result = ev(interp, "(/ 1 3)")
        assert result == Fraction(1, 3)

    def test_exact_to_inexact(self, interp):
        result = ev(interp, "(exact->inexact 1/3)")
        assert abs(result - 0.3333333333333333) < 1e-10

    def test_modulo(self, interp):
        assert ev(interp, "(modulo 10 3)") == 1

    def test_remainder(self, interp):
        assert ev(interp, "(remainder -7 3)") == -1

    def test_quotient(self, interp):
        assert ev(interp, "(quotient 10 3)") == 3

    def test_abs(self, interp):
        assert ev(interp, "(abs -5)") == 5

    def test_max(self, interp):
        assert ev(interp, "(max 1 3 2)") == 3

    def test_min(self, interp):
        assert ev(interp, "(min 1 3 2)") == 1

    def test_expt(self, interp):
        assert ev(interp, "(expt 2 10)") == 1024

    def test_sqrt(self, interp):
        assert ev(interp, "(sqrt 4)") == 2

    def test_gcd(self, interp):
        assert ev(interp, "(gcd 12 8)") == 4

    def test_lcm(self, interp):
        assert ev(interp, "(lcm 4 6)") == 12

    def test_floor(self, interp):
        assert ev(interp, "(floor 3.7)") == 3.0

    def test_ceiling(self, interp):
        assert ev(interp, "(ceiling 3.2)") == 4.0

    def test_round(self, interp):
        assert ev(interp, "(round 3.5)") == 4.0

    def test_truncate(self, interp):
        assert ev(interp, "(truncate -3.7)") == -3.0


class TestComparisons:
    def test_eq_numbers(self, interp):
        assert ev(interp, "(= 1 1)") is TRUE

    def test_lt(self, interp):
        assert ev(interp, "(< 1 2 3)") is TRUE
        assert ev(interp, "(< 1 3 2)") is FALSE

    def test_gt(self, interp):
        assert ev(interp, "(> 3 2 1)") is TRUE

    def test_le(self, interp):
        assert ev(interp, "(<= 1 1 2)") is TRUE

    def test_ge(self, interp):
        assert ev(interp, "(>= 3 3 1)") is TRUE


class TestBooleans:
    def test_not_false(self, interp):
        assert ev(interp, "(not #f)") is TRUE

    def test_not_true(self, interp):
        assert ev(interp, "(not #t)") is FALSE

    def test_not_zero(self, interp):
        # In Scheme, 0 is truthy
        assert ev(interp, "(not 0)") is FALSE

    def test_and_empty(self, interp):
        assert ev(interp, "(and)") is TRUE

    def test_and_false(self, interp):
        assert ev(interp, "(and 1 #f 3)") is FALSE

    def test_and_last(self, interp):
        assert ev(interp, "(and 1 2 3)") == 3

    def test_or_empty(self, interp):
        assert ev(interp, "(or)") is FALSE

    def test_or_first_true(self, interp):
        assert ev(interp, "(or #f 2 3)") == 2

    def test_or_all_false(self, interp):
        assert ev(interp, "(or #f #f)") is FALSE


class TestDefine:
    def test_define_var(self, interp):
        ev(interp, "(define x 42)")
        assert ev(interp, "x") == 42

    def test_define_fn(self, interp):
        ev(interp, "(define (square x) (* x x))")
        assert ev(interp, "(square 5)") == 25

    def test_define_lambda(self, interp):
        ev(interp, "(define double (lambda (x) (* x 2)))")
        assert ev(interp, "(double 7)") == 14

    def test_set_bang(self, interp):
        ev(interp, "(define x 1)")
        ev(interp, "(set! x 99)")
        assert ev(interp, "x") == 99


class TestLambda:
    def test_basic(self, interp):
        assert ev(interp, "((lambda (x) (* x x)) 5)") == 25

    def test_closure(self, interp):
        ev(interp, "(define (make-adder n) (lambda (x) (+ x n)))")
        ev(interp, "(define add5 (make-adder 5))")
        assert ev(interp, "(add5 3)") == 8

    def test_varargs(self, interp):
        ev(interp, "(define (sum . args) (apply + args))")
        assert ev(interp, "(sum 1 2 3 4)") == 10

    def test_rest_args(self, interp):
        ev(interp, "(define (f x . rest) rest)")
        r = ev(interp, "(f 1 2 3)")
        assert isinstance(r, Pair)

    def test_no_args(self, interp):
        ev(interp, "(define (f) 42)")
        assert ev(interp, "(f)") == 42


class TestConditionals:
    def test_if_true(self, interp):
        assert ev(interp, "(if #t 1 2)") == 1

    def test_if_false(self, interp):
        assert ev(interp, "(if #f 1 2)") == 2

    def test_if_no_else(self, interp):
        assert ev(interp, "(if #f 1)") is VOID

    def test_cond_basic(self, interp):
        assert ev(interp, "(cond (#f 1) (#t 2) (else 3))") == 2

    def test_cond_else(self, interp):
        assert ev(interp, "(cond (#f 1) (else 99))") == 99

    def test_case(self, interp):
        code = "(case 2 ((1) 'one) ((2) 'two) (else 'other))"
        r = ev(interp, code)
        assert isinstance(r, Symbol)
        assert r.name == "two"

    def test_when_true(self, interp):
        ev(interp, "(define x 0)")
        ev(interp, "(when #t (set! x 1))")
        assert ev(interp, "x") == 1

    def test_unless_false(self, interp):
        ev(interp, "(define y 0)")
        ev(interp, "(unless #f (set! y 2))")
        assert ev(interp, "y") == 2


class TestLet:
    def test_let(self, interp):
        assert ev(interp, "(let ((x 1) (y 2)) (+ x y))") == 3

    def test_let_star(self, interp):
        assert ev(interp, "(let* ((x 1) (y (+ x 1))) y)") == 2

    def test_letrec(self, interp):
        code = """(letrec ((even? (lambda (n)
                                    (if (= n 0) #t (odd? (- n 1)))))
                           (odd? (lambda (n)
                                   (if (= n 0) #f (even? (- n 1))))))
                   (even? 10))"""
        assert ev(interp, code) is TRUE

    def test_named_let(self, interp):
        code = "(let loop ((i 0) (acc 0)) (if (> i 5) acc (loop (+ i 1) (+ acc i))))"
        assert ev(interp, code) == 15


class TestLists:
    def test_cons(self, interp):
        r = ev(interp, "(cons 1 2)")
        assert isinstance(r, Pair)
        assert r.car == 1
        assert r.cdr == 2

    def test_car(self, interp):
        assert ev(interp, "(car '(1 2 3))") == 1

    def test_cdr(self, interp):
        r = ev(interp, "(cdr '(1 2 3))")
        assert isinstance(r, Pair)
        assert r.car == 2

    def test_list(self, interp):
        r = ev(interp, "(list 1 2 3)")
        assert isinstance(r, Pair)

    def test_length(self, interp):
        assert ev(interp, "(length '(1 2 3))") == 3

    def test_append(self, interp):
        r = ev(interp, "(append '(1 2) '(3 4))")
        assert ev(interp, "(length (append '(1 2) '(3 4)))") == 4

    def test_reverse(self, interp):
        r = ev(interp, "(reverse '(1 2 3))")
        assert r.car == 3

    def test_map(self, interp):
        code = "(map (lambda (x) (* x x)) '(1 2 3))"
        r = ev(interp, code)
        vals = list(r)
        assert vals == [1, 4, 9]

    def test_filter(self, interp):
        code = "(filter odd? '(1 2 3 4 5))"
        r = ev(interp, code)
        vals = list(r)
        assert vals == [1, 3, 5]

    def test_for_each(self, interp):
        ev(interp, "(define result '())")
        ev(interp, "(for-each (lambda (x) (set! result (cons x result))) '(1 2 3))")
        r = ev(interp, "result")
        assert list(r) == [3, 2, 1]

    def test_assoc(self, interp):
        code = "(assoc 'b '((a 1) (b 2) (c 3)))"
        r = ev(interp, code)
        assert isinstance(r, Pair)
        assert r.car.name == "b"

    def test_member(self, interp):
        code = "(member 3 '(1 2 3 4))"
        r = ev(interp, code)
        assert isinstance(r, Pair)
        assert r.car == 3

    def test_list_ref(self, interp):
        assert ev(interp, "(list-ref '(a b c d) 2)") == Symbol("c")

    def test_list_tail(self, interp):
        r = ev(interp, "(list-tail '(a b c d) 2)")
        assert r.car == Symbol("c")


class TestStrings:
    def test_string_length(self, interp):
        assert ev(interp, '(string-length "hello")') == 5

    def test_string_ref(self, interp):
        r = ev(interp, '(string-ref "hello" 1)')
        assert isinstance(r, Char)
        assert r.char == "e"

    def test_substring(self, interp):
        r = ev(interp, '(substring "hello" 1 3)')
        assert isinstance(r, SchemeString)
        assert r.value == "el"

    def test_string_append(self, interp):
        r = ev(interp, '(string-append "hello" " " "world")')
        assert r.value == "hello world"

    def test_string_to_list(self, interp):
        r = ev(interp, '(string->list "abc")')
        chars = list(r)
        assert [c.char for c in chars] == ["a", "b", "c"]

    def test_list_to_string(self, interp):
        r = ev(interp, "(list->string (list #\\a #\\b #\\c))")
        assert r.value == "abc"

    def test_string_upcase(self, interp):
        assert ev(interp, '(string-upcase "hello")').value == "HELLO"

    def test_string_downcase(self, interp):
        assert ev(interp, '(string-downcase "HELLO")').value == "hello"

    def test_string_to_number(self, interp):
        assert ev(interp, '(string->number "42")') == 42
        assert ev(interp, '(string->number "3.14")') is not FALSE

    def test_number_to_string(self, interp):
        r = ev(interp, "(number->string 42)")
        assert isinstance(r, SchemeString)
        assert r.value == "42"


class TestVectors:
    def test_make_vector(self, interp):
        r = ev(interp, "(make-vector 3 0)")
        assert isinstance(r, Vector)
        assert r.data == [0, 0, 0]

    def test_vector_ref(self, interp):
        assert ev(interp, "(vector-ref #(10 20 30) 1)") == 20

    def test_vector_set(self, interp):
        ev(interp, "(define v (vector 1 2 3))")
        ev(interp, "(vector-set! v 1 99)")
        assert ev(interp, "(vector-ref v 1)") == 99

    def test_vector_length(self, interp):
        assert ev(interp, "(vector-length #(a b c))") == 3

    def test_vector_to_list(self, interp):
        r = ev(interp, "(vector->list #(1 2 3))")
        assert list(r) == [1, 2, 3]

    def test_list_to_vector(self, interp):
        r = ev(interp, "(list->vector '(1 2 3))")
        assert isinstance(r, Vector)
        assert r.data == [1, 2, 3]


class TestQuasiquote:
    def test_basic(self, interp):
        ev(interp, "(define x 42)")
        r = ev(interp, "`(a ,x c)")
        vals = list(r)
        assert vals[0].name == "a"
        assert vals[1] == 42
        assert vals[2].name == "c"

    def test_splicing(self, interp):
        ev(interp, "(define lst '(2 3))")
        r = ev(interp, "`(1 ,@lst 4)")
        vals = list(r)
        assert vals == [1, 2, 3, 4]

    def test_nested(self, interp):
        r = ev(interp, "``(a ,(+ 1 2))")
        assert r is not NIL  # nested quasiquote should return something


class TestTailCalls:
    def test_tail_recursion(self, interp):
        """Test that tail calls don't stack overflow."""
        code = """
        (define (count n acc)
          (if (= n 0)
              acc
              (count (- n 1) (+ acc 1))))
        (count 100000 0)
        """
        assert ev(interp, code) == 100000

    def test_mutual_tail_recursion(self, interp):
        code = """
        (define (my-even? n)
          (if (= n 0) #t (my-odd? (- n 1))))
        (define (my-odd? n)
          (if (= n 0) #f (my-even? (- n 1))))
        (my-even? 10000)
        """
        assert ev(interp, code) is TRUE


class TestContinuations:
    def test_callcc_basic(self, interp):
        code = "(call-with-current-continuation (lambda (k) 42))"
        assert ev(interp, code) == 42

    def test_callcc_escape(self, interp):
        code = """
        (define (product lst)
          (call/cc
            (lambda (exit)
              (let loop ((l lst))
                (cond ((null? l) 1)
                      ((= (car l) 0) (exit 0))
                      (else (* (car l) (loop (cdr l)))))))))
        (product '(1 2 3 4 5))
        """
        assert ev(interp, code) == 120

    def test_callcc_zero(self, interp):
        code = """
        (define (product lst)
          (call/cc
            (lambda (exit)
              (let loop ((l lst))
                (cond ((null? l) 1)
                      ((= (car l) 0) (exit 0))
                      (else (* (car l) (loop (cdr l)))))))))
        (product '(1 2 0 4 5))
        """
        assert ev(interp, code) == 0


class TestMacros:
    def test_define_syntax(self, interp):
        code = """
        (define-syntax my-if
          (syntax-rules ()
            ((my-if test then else)
             (cond (test then) (else else)))))
        (my-if #t 1 2)
        """
        assert ev(interp, code) == 1

    def test_syntax_ellipsis(self, interp):
        code = """
        (define-syntax my-list
          (syntax-rules ()
            ((my-list x ...) (list x ...))))
        (my-list 1 2 3)
        """
        r = ev(interp, code)
        assert list(r) == [1, 2, 3]

    def test_let_syntax(self, interp):
        code = """
        (let-syntax ((swap! (syntax-rules ()
                              ((swap! a b)
                               (let ((tmp a))
                                 (set! a b)
                                 (set! b tmp))))))
          (let ((x 1) (y 2))
            (swap! x y)
            (list x y)))
        """
        r = ev(interp, code)
        assert list(r) == [2, 1]

    def test_and_macro(self, interp):
        assert ev(interp, "(and 1 2 3)") == 3
        assert ev(interp, "(and 1 #f 3)") is FALSE

    def test_or_macro(self, interp):
        assert ev(interp, "(or #f #f 3)") == 3
        assert ev(interp, "(or #f #f #f)") is FALSE


class TestDo:
    def test_do_loop(self, interp):
        code = """
        (let ((v (make-vector 5)))
          (do ((i 0 (+ i 1)))
              ((= i 5) v)
            (vector-set! v i (* i i))))
        """
        r = ev(interp, code)
        assert isinstance(r, Vector)
        assert r.data == [0, 1, 4, 9, 16]

    def test_do_sum(self, interp):
        code = """
        (do ((i 1 (+ i 1))
             (sum 0 (+ sum i)))
            ((> i 10) sum))
        """
        assert ev(interp, code) == 55


class TestValues:
    def test_values(self, interp):
        code = """
        (call-with-values
          (lambda () (values 1 2 3))
          (lambda (a b c) (+ a b c)))
        """
        assert ev(interp, code) == 6

    def test_receive(self, interp):
        code = """
        (define (div-and-mod a b)
          (values (quotient a b) (remainder a b)))
        (call-with-values
          (lambda () (div-and-mod 10 3))
          list)
        """
        r = ev(interp, code)
        assert list(r) == [3, 1]


class TestDelay:
    def test_delay_force(self, interp):
        code = """
        (define p (delay (+ 1 2)))
        (force p)
        """
        assert ev(interp, code) == 3

    def test_delay_memoized(self, interp):
        ev(interp, "(define count 0)")
        ev(interp, "(define p (delay (begin (set! count (+ count 1)) count)))")
        ev(interp, "(force p)")
        ev(interp, "(force p)")
        assert ev(interp, "count") == 1  # evaluated only once


class TestRecordTypes:
    def test_define_record(self, interp):
        code = """
        (define-record-type point
          (make-point x y)
          point?
          (x point-x)
          (y point-y))
        (define p (make-point 3 4))
        (list (point? p) (point-x p) (point-y p))
        """
        r = ev(interp, code)
        vals = list(r)
        assert vals[0] is TRUE
        assert vals[1] == 3
        assert vals[2] == 4


class TestEquivalence:
    def test_eq(self, interp):
        assert ev(interp, "(eq? 'a 'a)") is TRUE
        assert ev(interp, "(eq? '() '())") is TRUE

    def test_eqv(self, interp):
        assert ev(interp, "(eqv? 1 1)") is TRUE
        assert ev(interp, "(eqv? 1 1.0)") is FALSE

    def test_equal(self, interp):
        assert ev(interp, '(equal? "abc" "abc")') is TRUE
        assert ev(interp, "(equal? '(1 2 3) '(1 2 3))") is TRUE
        assert ev(interp, "(equal? '#(1 2) '#(1 2))") is TRUE


class TestPredicates:
    def test_null(self, interp):
        assert ev(interp, "(null? '())") is TRUE
        assert ev(interp, "(null? '(1))") is FALSE

    def test_pair(self, interp):
        assert ev(interp, "(pair? '(1 2))") is TRUE
        assert ev(interp, "(pair? '())") is FALSE

    def test_list(self, interp):
        assert ev(interp, "(list? '(1 2 3))") is TRUE
        assert ev(interp, "(list? '())") is TRUE
        assert ev(interp, "(list? (cons 1 2))") is FALSE

    def test_number(self, interp):
        assert ev(interp, "(number? 42)") is TRUE
        assert ev(interp, "(number? 'x)") is FALSE

    def test_string(self, interp):
        assert ev(interp, '(string? "hello")') is TRUE
        assert ev(interp, "(string? 42)") is FALSE

    def test_symbol(self, interp):
        assert ev(interp, "(symbol? 'foo)") is TRUE

    def test_procedure(self, interp):
        assert ev(interp, "(procedure? car)") is TRUE
        assert ev(interp, "(procedure? (lambda (x) x))") is TRUE

    def test_char(self, interp):
        assert ev(interp, "(char? #\\a)") is TRUE

    def test_vector(self, interp):
        assert ev(interp, "(vector? #(1 2 3))") is TRUE

    def test_boolean(self, interp):
        assert ev(interp, "(boolean? #t)") is TRUE
        assert ev(interp, "(boolean? 1)") is FALSE


class TestApply:
    def test_apply_basic(self, interp):
        assert ev(interp, "(apply + '(1 2 3))") == 6

    def test_apply_mixed(self, interp):
        assert ev(interp, "(apply + 1 2 '(3 4))") == 10

    def test_apply_lambda(self, interp):
        assert ev(interp, "(apply (lambda (x y) (- x y)) '(10 3))") == 7


class TestHigherOrder:
    def test_compose(self, interp):
        code = """
        (define (compose f g) (lambda (x) (f (g x))))
        (define inc (lambda (x) (+ x 1)))
        (define double (lambda (x) (* x 2)))
        ((compose inc double) 5)
        """
        assert ev(interp, code) == 11

    def test_fold(self, interp):
        code = "(fold-left + 0 '(1 2 3 4 5))"
        assert ev(interp, code) == 15

    def test_sort(self, interp):
        code = "(sort '(3 1 4 1 5 9 2 6) <)"
        r = ev(interp, code)
        assert list(r) == [1, 1, 2, 3, 4, 5, 6, 9]


class TestErrors:
    def test_unbound_variable(self, interp):
        with pytest.raises(SchemeNameError):
            ev(interp, "undefined-variable-xyz")

    def test_type_error(self, interp):
        with pytest.raises(SchemeTypeError):
            ev(interp, "(car 42)")

    def test_arity_error(self, interp):
        with pytest.raises(Exception):
            ev(interp, "((lambda (x) x) 1 2)")


class TestStdlib:
    def test_factorial(self, interp):
        assert ev(interp, "(factorial 10)") == 3628800

    def test_fibonacci(self, interp):
        assert ev(interp, "(fibonacci 10)") == 55

    def test_square(self, interp):
        assert ev(interp, "(square 7)") == 49

    def test_compose(self, interp):
        code = "((compose (lambda (x) (* x 2)) (lambda (x) (+ x 1))) 3)"
        assert ev(interp, code) == 8

    def test_identity(self, interp):
        assert ev(interp, "(identity 42)") == 42
