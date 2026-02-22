"""Tests for the parser."""

import pytest

from sucheme.parser import parse, parse_one
from sucheme.types import (
    NIL, TRUE, FALSE, Symbol, Pair, Vector, Char, SchemeString,
    SchemeSyntaxError,
)


def p1(s):
    return parse_one(s)


class TestAtoms:
    def test_integer(self):
        assert p1("42") == 42

    def test_negative(self):
        assert p1("-3") == -3

    def test_float(self):
        import math
        assert abs(p1("3.14") - 3.14) < 1e-10

    def test_bool_true(self):
        assert p1("#t") is TRUE

    def test_bool_false(self):
        assert p1("#f") is FALSE

    def test_symbol(self):
        x = p1("hello")
        assert isinstance(x, Symbol)
        assert x.name == "hello"

    def test_string(self):
        x = p1('"hello"')
        assert isinstance(x, SchemeString)
        assert x.value == "hello"

    def test_char(self):
        x = p1("#\\a")
        assert isinstance(x, Char)
        assert x.char == "a"

    def test_nil(self):
        assert p1("()") is NIL


class TestLists:
    def test_simple_list(self):
        x = p1("(1 2 3)")
        assert isinstance(x, Pair)
        assert x.car == 1
        assert x.cdr.car == 2
        assert x.cdr.cdr.car == 3
        assert x.cdr.cdr.cdr is NIL

    def test_dotted_pair(self):
        x = p1("(1 . 2)")
        assert isinstance(x, Pair)
        assert x.car == 1
        assert x.cdr == 2

    def test_nested_list(self):
        x = p1("((1 2) (3 4))")
        assert isinstance(x, Pair)
        inner = x.car
        assert inner.car == 1

    def test_quote_shorthand(self):
        x = p1("'hello")
        assert isinstance(x, Pair)
        assert x.car.name == "quote"
        assert x.cdr.car.name == "hello"

    def test_quasiquote(self):
        x = p1("`hello")
        assert x.car.name == "quasiquote"

    def test_unquote(self):
        x = p1(",hello")
        assert x.car.name == "unquote"

    def test_unquote_splicing(self):
        x = p1(",@hello")
        assert x.car.name == "unquote-splicing"


class TestVectors:
    def test_vector(self):
        x = p1("#(1 2 3)")
        assert isinstance(x, Vector)
        assert x.data == [1, 2, 3]

    def test_empty_vector(self):
        x = p1("#()")
        assert isinstance(x, Vector)
        assert x.data == []


class TestMultiple:
    def test_multiple_exprs(self):
        exprs = parse("(define x 1) (define y 2)")
        assert len(exprs) == 2

    def test_comments_ignored(self):
        exprs = parse("; comment\n42")
        assert exprs == [42]

    def test_datum_comment(self):
        # #; ignores next datum
        exprs = parse("#; 1 2")
        assert exprs == [2]


class TestErrors:
    def test_unterminated_list(self):
        with pytest.raises(Exception):
            parse("(1 2 3")

    def test_unexpected_close(self):
        with pytest.raises(Exception):
            parse_one(")")

    def test_parse_one_trailing_tokens_raises(self):
        from sucheme.parser import ParseError
        with pytest.raises(ParseError):
            parse_one("1 2")

    def test_mismatched_bracket_raises(self):
        from sucheme.parser import ParseError
        with pytest.raises(ParseError):
            parse("(1 2]")

    def test_mismatched_paren_raises(self):
        from sucheme.parser import ParseError
        with pytest.raises(ParseError):
            parse("[1 2)")

    def test_dotted_pair_bracket_error_message(self):
        from sucheme.parser import ParseError
        with pytest.raises(ParseError) as exc_info:
            parse("[a . b)")
        assert "]" in str(exc_info.value)
