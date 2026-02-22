"""Tests for the lexer."""

import pytest
from fractions import Fraction

from sucheme.lexer import tokenize, TokenType, Token, LexerError


def tokens(source):
    """Tokenize and return list without EOF."""
    toks = tokenize(source)
    return [t for t in toks if t.type != TokenType.EOF]


def token_types(source):
    return [t.type for t in tokens(source)]


def token_values(source):
    return [t.value for t in tokens(source)]


class TestAtoms:
    def test_integer(self):
        assert token_values("42") == [42]
        assert token_values("-3") == [-3]
        assert token_values("+7") == [7]

    def test_float(self):
        vals = token_values("3.14")
        assert abs(vals[0] - 3.14) < 1e-10
        vals = token_values("1e5")
        assert vals[0] == 1e5

    def test_rational(self):
        vals = token_values("3/4")
        assert vals[0] == Fraction(3, 4)

    def test_hex_integer(self):
        vals = token_values("#xff")
        assert vals[0] == 255

    def test_binary_integer(self):
        vals = token_values("#b1010")
        assert vals[0] == 10

    def test_octal_integer(self):
        vals = token_values("#o17")
        assert vals[0] == 15

    def test_bool_true(self):
        t = tokens("#t")[0]
        assert t.type == TokenType.HASH_TRUE
        assert t.value is True

    def test_bool_false(self):
        t = tokens("#f")[0]
        assert t.type == TokenType.HASH_FALSE
        assert t.value is False

    def test_string(self):
        t = tokens('"hello"')[0]
        assert t.type == TokenType.STRING
        assert t.value == "hello"

    def test_string_escapes(self):
        t = tokens('"a\\nb"')[0]
        assert t.value == "a\nb"

    def test_symbol(self):
        t = tokens("foo")[0]
        assert t.type == TokenType.SYMBOL
        assert t.value == "foo"

    def test_char_space(self):
        t = tokens("#\\space")[0]
        assert t.type == TokenType.CHAR
        assert t.value == " "

    def test_char_newline(self):
        t = tokens("#\\newline")[0]
        assert t.value == "\n"

    def test_char_letter(self):
        t = tokens("#\\a")[0]
        assert t.value == "a"


class TestDelimiters:
    def test_parens(self):
        tts = token_types("()")
        assert tts == [TokenType.LPAREN, TokenType.RPAREN]

    def test_quote(self):
        tts = token_types("'x")
        assert tts == [TokenType.QUOTE, TokenType.SYMBOL]

    def test_quasiquote(self):
        tts = token_types("`x")
        assert tts == [TokenType.QUASIQUOTE, TokenType.SYMBOL]

    def test_unquote(self):
        tts = token_types(",x")
        assert tts == [TokenType.UNQUOTE, TokenType.SYMBOL]

    def test_unquote_splicing(self):
        tts = token_types(",@x")
        assert tts == [TokenType.UNQUOTE_SPLICING, TokenType.SYMBOL]

    def test_vector_hash(self):
        tts = token_types("#(1 2 3)")
        assert tts[0] == TokenType.HASH_LPAREN

    def test_dot(self):
        tts = token_types(".")
        assert tts == [TokenType.DOT]


class TestComments:
    def test_line_comment(self):
        tts = token_types("; comment\n42")
        assert len(tts) == 1
        assert token_values("; comment\n42") == [42]

    def test_block_comment(self):
        vals = token_values("#| block |# 42")
        assert vals == [42]

    def test_datum_comment(self):
        # #; skips next datum
        tts = token_types("#; 42 hello")
        # Should have DATUM_COMMENT, INTEGER, SYMBOL
        assert tts[0] == TokenType.DATUM_COMMENT

    def test_multiline_string(self):
        t = tokens('"line1\nline2"')[0]
        assert t.value == "line1\nline2"


class TestSpecialNumbers:
    def test_inf(self):
        import math
        vals = token_values("+inf.0")
        assert math.isinf(vals[0]) and vals[0] > 0

    def test_neg_inf(self):
        import math
        vals = token_values("-inf.0")
        assert math.isinf(vals[0]) and vals[0] < 0

    def test_nan(self):
        import math
        vals = token_values("+nan.0")
        assert math.isnan(vals[0])


class TestErrorCases:
    def test_unterminated_block_comment_raises(self):
        with pytest.raises(LexerError) as exc_info:
            tokenize("#| unclosed block comment")
        # Error should report the start position, not 0:0
        assert exc_info.value.line > 0

    def test_rational_division_by_zero_raises(self):
        with pytest.raises(LexerError) as exc_info:
            tokenize("1/0")
        # Error should report a meaningful line:col (not 0:0)
        assert exc_info.value.line > 0
        assert exc_info.value.col > 0

    def test_nested_block_comment_terminated(self):
        # Nested #| |# should work
        vals = token_values("#| outer #| inner |# still outer |# 99")
        assert vals == [99]

    def test_nested_block_comment_unterminated(self):
        with pytest.raises(LexerError):
            tokenize("#| outer #| inner |# not closed")
