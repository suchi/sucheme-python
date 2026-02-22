"""
Parser for sucheme.

Converts a token stream into Scheme s-expressions (AST).
"""

from __future__ import annotations

from typing import Any

from sucheme.lexer import Token, TokenType, tokenize, LexerError
from sucheme.types import (
    NIL, TRUE, FALSE, Symbol, Pair, Vector, Char, SchemeString,
    list_to_scheme, cons, SchemeSyntaxError,
)


class ParseError(SchemeSyntaxError):
    pass


class Parser:
    """Recursive descent Scheme parser."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_all(self) -> list[Any]:
        """Parse all top-level expressions."""
        exprs = []
        while self.peek().type != TokenType.EOF:
            exprs.append(self._parse_expr())
        return exprs

    def _parse_expr(self) -> Any:
        tok = self.peek()

        # Datum comment: skip next datum
        if tok.type == TokenType.DATUM_COMMENT:
            self.consume()
            self._parse_expr()  # discard
            return self._parse_expr()

        if tok.type == TokenType.LPAREN or tok.type == TokenType.LBRACKET:
            close = TokenType.RPAREN if tok.type == TokenType.LPAREN else TokenType.RBRACKET
            return self._parse_list(close)

        if tok.type == TokenType.HASH_LPAREN:
            return self._parse_vector()

        if tok.type in (TokenType.QUOTE, TokenType.QUASIQUOTE,
                        TokenType.UNQUOTE, TokenType.UNQUOTE_SPLICING):
            names = {
                TokenType.QUOTE: "quote",
                TokenType.QUASIQUOTE: "quasiquote",
                TokenType.UNQUOTE: "unquote",
                TokenType.UNQUOTE_SPLICING: "unquote-splicing",
            }
            self.consume()
            inner = self._parse_expr()
            return list_to_scheme([Symbol(names[tok.type]), inner])

        if tok.type == TokenType.HASH_TRUE:
            self.consume()
            return TRUE

        if tok.type == TokenType.HASH_FALSE:
            self.consume()
            return FALSE

        if tok.type in (TokenType.INTEGER, TokenType.RATIONAL,
                        TokenType.FLOAT, TokenType.COMPLEX):
            self.consume()
            return tok.value

        if tok.type == TokenType.STRING:
            self.consume()
            return SchemeString(tok.value)

        if tok.type == TokenType.CHAR:
            self.consume()
            return Char(tok.value)

        if tok.type == TokenType.SYMBOL:
            self.consume()
            return Symbol(tok.value)

        if tok.type == TokenType.DOT:
            raise ParseError(
                f"Unexpected '.' at {tok.line}:{tok.col}", tok.line, tok.col
            )

        if tok.type == TokenType.EOF:
            raise ParseError("Unexpected end of input", tok.line, tok.col)

        raise ParseError(
            f"Unexpected token {tok.type.name!r} at {tok.line}:{tok.col}",
            tok.line, tok.col,
        )

    def _parse_list(self, close: TokenType) -> Any:
        self.consume()  # consume (
        items = []
        while True:
            tok = self.peek()
            if tok.type in (TokenType.EOF,):
                raise ParseError("Unterminated list", tok.line, tok.col)
            if tok.type == close:
                self.consume()
                return list_to_scheme(items)
            if tok.type == TokenType.RPAREN and close == TokenType.RBRACKET:
                self.consume()
                return list_to_scheme(items)
            if tok.type == TokenType.RBRACKET and close == TokenType.RPAREN:
                self.consume()
                return list_to_scheme(items)
            # Dotted pair
            if tok.type == TokenType.DOT:
                self.consume()
                if not items:
                    raise ParseError("Dot at start of list", tok.line, tok.col)
                cdr = self._parse_expr()
                # consume closing paren
                close_tok = self.peek()
                if close_tok.type not in (TokenType.RPAREN, TokenType.RBRACKET):
                    raise ParseError(
                        f"Expected ) after dotted pair, got {close_tok!r}",
                        close_tok.line, close_tok.col,
                    )
                self.consume()
                # Build dotted list
                result = cdr
                for item in reversed(items):
                    result = cons(item, result)
                return result
            items.append(self._parse_expr())

    def _parse_vector(self) -> Vector:
        self.consume()  # consume #(
        items = []
        while True:
            tok = self.peek()
            if tok.type == TokenType.RPAREN:
                self.consume()
                return Vector(items)
            if tok.type == TokenType.EOF:
                raise ParseError("Unterminated vector", tok.line, tok.col)
            items.append(self._parse_expr())


def parse(source: str) -> list[Any]:
    """Parse a Scheme source string into a list of expressions."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse_all()


def parse_one(source: str) -> Any:
    """Parse a single Scheme expression."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    expr = parser._parse_expr()
    return expr
