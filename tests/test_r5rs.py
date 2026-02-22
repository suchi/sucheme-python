"""R5RS compliance tests for sucheme.

Tests that verify compliance with R5RS standard.
"""

import pytest
from sucheme.interpreter import Interpreter
from sucheme.types import TRUE, FALSE, NIL, VOID, Symbol, Pair, SchemeString


@pytest.fixture
def interp():
    return Interpreter()


def ev(interp, s):
    return interp.eval_string_last(s)


class TestR5RSSection6_1:
    """R5RS 6.1: Equivalence predicates."""

    def test_eqv_symbols(self, interp):
        assert ev(interp, "(eqv? 'a 'a)") is TRUE

    def test_eqv_numbers(self, interp):
        assert ev(interp, "(eqv? 1 1)") is TRUE

    def test_eqv_different_types(self, interp):
        assert ev(interp, "(eqv? 1 1.0)") is FALSE

    def test_eqv_booleans(self, interp):
        assert ev(interp, "(eqv? #t #t)") is TRUE
        assert ev(interp, "(eqv? #f #f)") is TRUE

    def test_eqv_empty_list(self, interp):
        assert ev(interp, "(eqv? '() '())") is TRUE

    def test_equal_strings(self, interp):
        assert ev(interp, '(equal? "abc" "abc")') is TRUE

    def test_equal_lists(self, interp):
        assert ev(interp, "(equal? '(a (b) c) '(a (b) c))") is TRUE

    def test_equal_vectors(self, interp):
        assert ev(interp, "(equal? '#(1 2) '#(1 2))") is TRUE


class TestR5RSSection6_2:
    """R5RS 6.2: Numbers."""

    def test_integer_predicate(self, interp):
        assert ev(interp, "(integer? 3)") is TRUE
        assert ev(interp, "(integer? 3.0)") is TRUE
        assert ev(interp, "(integer? 3.2)") is FALSE

    def test_rational_predicate(self, interp):
        assert ev(interp, "(rational? 6/10)") is TRUE
        assert ev(interp, "(rational? 6)") is TRUE

    def test_exact_predicate(self, interp):
        assert ev(interp, "(exact? 3)") is TRUE
        assert ev(interp, "(inexact? 3.0)") is TRUE

    def test_number_to_string_radix(self, interp):
        r = ev(interp, "(number->string 255 16)")
        assert r.value == "ff"

    def test_string_to_number(self, interp):
        assert ev(interp, '(string->number "100" 16)') == 256

    def test_modulo_signs(self, interp):
        assert ev(interp, "(modulo -13 4)") == 3
        assert ev(interp, "(remainder -13 4)") == -1

    def test_floor_exact(self, interp):
        assert ev(interp, "(floor -4.3)") == -5.0

    def test_numerator_denominator(self, interp):
        assert ev(interp, "(numerator 6/4)") == 3
        assert ev(interp, "(denominator 6/4)") == 2


class TestR5RSSection6_3:
    """R5RS 6.3: Other data types."""

    def test_boolean_predicate(self, interp):
        assert ev(interp, "(boolean? #f)") is TRUE
        assert ev(interp, "(boolean? 0)") is FALSE

    def test_pair_operations(self, interp):
        assert ev(interp, "(car '(a b c))") == Symbol("a")
        r = ev(interp, "(cdr '(a b c))")
        assert r.car == Symbol("b")

    def test_list_operations(self, interp):
        assert ev(interp, "(length '(a b c))") == 3
        r = ev(interp, "(list-tail '(a b c d) 2)")
        assert r.car == Symbol("c")


class TestR5RSSection6_4:
    """R5RS 6.4: Symbols."""

    def test_symbol_to_string(self, interp):
        r = ev(interp, "(symbol->string 'flying-fish)")
        assert isinstance(r, SchemeString)
        assert r.value == "flying-fish"

    def test_string_to_symbol(self, interp):
        r = ev(interp, '(string->symbol "mISSISSIPPI")')
        assert isinstance(r, Symbol)


class TestR5RSSection6_5:
    """R5RS 6.5: Characters."""

    def test_char_to_integer(self, interp):
        assert ev(interp, "(char->integer #\\a)") == 97

    def test_integer_to_char(self, interp):
        from sucheme.types import Char
        r = ev(interp, "(integer->char 65)")
        assert isinstance(r, Char)
        assert r.char == "A"

    def test_char_comparisons(self, interp):
        assert ev(interp, "(char<? #\\a #\\b)") is TRUE
        assert ev(interp, "(char=? #\\a #\\a)") is TRUE

    def test_char_alphabetic(self, interp):
        assert ev(interp, "(char-alphabetic? #\\a)") is TRUE
        assert ev(interp, "(char-alphabetic? #\\1)") is FALSE

    def test_char_case(self, interp):
        from sucheme.types import Char
        r = ev(interp, "(char-upcase #\\a)")
        assert isinstance(r, Char)
        assert r.char == "A"


class TestR5RSSection6_6:
    """R5RS 6.6: Strings."""

    def test_make_string(self, interp):
        r = ev(interp, "(make-string 5 #\\a)")
        assert r.value == "aaaaa"

    def test_string_copy(self, interp):
        r = ev(interp, '(string-copy "hello")')
        assert r.value == "hello"


class TestR5RSSection6_7:
    """R5RS 6.7: Vectors."""

    def test_make_vector_fill(self, interp):
        from sucheme.types import Vector
        r = ev(interp, "(make-vector 3 'a)")
        assert isinstance(r, Vector)
        assert all(x == Symbol("a") for x in r.data)


class TestR5RSSection6_9:
    """R5RS 6.9: Control features."""

    def test_apply_varargs(self, interp):
        assert ev(interp, "(apply + 1 2 '(3 4 5))") == 15

    def test_map_multiple_lists(self, interp):
        r = ev(interp, "(map + '(1 2 3) '(4 5 6))")
        assert list(r) == [5, 7, 9]

    def test_for_each(self, interp):
        ev(interp, "(define v (make-vector 3 0))")
        ev(interp, "(for-each (lambda (i) (vector-set! v i (* i i))) '(0 1 2))")
        r = ev(interp, "v")
        assert r.data == [0, 1, 4]


class TestR5RSAppendix:
    """R5RS Appendix: Derived expression syntax."""

    def test_let_named(self, interp):
        """Named let form."""
        code = """
        (let fact ((n 5) (acc 1))
          (if (= n 0)
              acc
              (fact (- n 1) (* acc n))))
        """
        assert ev(interp, code) == 120

    def test_do_basic(self, interp):
        code = """
        (do ((vec (make-vector 5))
             (i 0 (+ i 1)))
            ((= i 5) vec)
          (vector-set! vec i i))
        """
        r = ev(interp, code)
        assert r.data == [0, 1, 2, 3, 4]

    def test_cond_arrow(self, interp):
        assert ev(interp, "(cond ((assv 2 '((1 one) (2 two) (3 three))) => cadr))") == Symbol("two")

    def test_case_multiple(self, interp):
        code = """
        (case (* 2 3)
          ((2 3 5 7) 'prime)
          ((1 4 6 8 9) 'composite))
        """
        assert ev(interp, code) == Symbol("composite")

    def test_and_short_circuit(self, interp):
        ev(interp, "(define x 0)")
        ev(interp, "(and #f (set! x 1))")
        assert ev(interp, "x") == 0  # (set! x 1) should not be evaluated

    def test_or_short_circuit(self, interp):
        ev(interp, "(define y 0)")
        ev(interp, "(or 1 (set! y 1))")
        assert ev(interp, "y") == 0  # (set! y 1) should not be evaluated


class TestSchemeFeatures:
    """Additional Scheme feature tests."""

    def test_mutual_recursion(self, interp):
        code = """
        (define (is-even? n)
          (if (= n 0) #t (is-odd? (- n 1))))
        (define (is-odd? n)
          (if (= n 0) #f (is-even? (- n 1))))
        (list (is-even? 4) (is-odd? 3))
        """
        r = ev(interp, code)
        assert list(r) == [TRUE, TRUE]

    def test_higher_order_functions(self, interp):
        code = """
        (define (twice f)
          (lambda (x) (f (f x))))
        ((twice (lambda (x) (* x 2))) 3)
        """
        assert ev(interp, code) == 12

    def test_church_numerals(self, interp):
        """Church encoding of numbers."""
        code = """
        (define zero (lambda (f) (lambda (x) x)))
        (define (succ n) (lambda (f) (lambda (x) (f ((n f) x)))))
        (define (church->int n) ((n (lambda (x) (+ x 1))) 0))
        (define one (succ zero))
        (define two (succ one))
        (define three (succ two))
        (church->int three)
        """
        assert ev(interp, code) == 3

    def test_ackermann(self, interp):
        """Ackermann function (tests deep recursion)."""
        code = """
        (define (ackermann m n)
          (cond ((= m 0) (+ n 1))
                ((= n 0) (ackermann (- m 1) 1))
                (else (ackermann (- m 1) (ackermann m (- n 1))))))
        (ackermann 3 3)
        """
        assert ev(interp, code) == 61

    def test_streams_with_delay(self, interp):
        """Lazy stream using delay/force."""
        code = """
        (define-syntax cons-stream
          (syntax-rules ()
            ((cons-stream a b) (cons a (delay b)))))
        (define (stream-car s) (car s))
        (define (stream-cdr s) (force (cdr s)))
        (define (stream-take n s)
          (if (= n 0)
              '()
              (cons (stream-car s)
                    (stream-take (- n 1) (stream-cdr s)))))
        (define (integers-from n)
          (cons-stream n (integers-from (+ n 1))))
        (define nats (integers-from 0))
        (stream-take 5 nats)
        """
        r = ev(interp, code)
        assert list(r) == [0, 1, 2, 3, 4]
