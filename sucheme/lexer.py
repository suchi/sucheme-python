"""
Lexer/Tokenizer for sucheme.

Tokenizes Scheme source code into a flat token stream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator


class TokenType(Enum):
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACKET = auto()      # [  (R6RS-style, allowed for readability)
    RBRACKET = auto()      # ]
    QUOTE = auto()         # '
    QUASIQUOTE = auto()    # `
    UNQUOTE = auto()       # ,
    UNQUOTE_SPLICING = auto()  # ,@
    HASH_LPAREN = auto()   # #(
    HASH_TRUE = auto()     # #t
    HASH_FALSE = auto()    # #f
    DOT = auto()           # .
    SYMBOL = auto()
    INTEGER = auto()
    RATIONAL = auto()
    FLOAT = auto()
    COMPLEX = auto()
    STRING = auto()
    CHAR = auto()
    EOF = auto()
    DATUM_COMMENT = auto() # #;


@dataclass
class Token:
    type: TokenType
    value: object  # Python value
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int) -> None:
        super().__init__(f"Line {line}, col {col}: {msg}")
        self.line = line
        self.col = col


_CHAR_NAMES: dict[str, str] = {
    "space": " ",
    "newline": "\n",
    "tab": "\t",
    "return": "\r",
    "null": "\x00",
    "nul": "\x00",
    "backspace": "\x08",
    "delete": "\x7f",
    "escape": "\x1b",
    "altmode": "\x1b",
    "rubout": "\x7f",
    "page": "\x0c",
}

# Regex patterns
_DELIMITER = r'[\s()\[\]";]|$'
_INT_RE = re.compile(
    r'^([+-]?\d+)$|'
    r'^#b([+-]?[01]+)$|'
    r'^#o([+-]?[0-7]+)$|'
    r'^#d([+-]?\d+)$|'
    r'^#x([+-]?[0-9a-fA-F]+)$|'
    r'^#e([+-]?\d+)$|'
    r'^#i([+-]?\d+)$'
)
_RAT_RE = re.compile(r'^([+-]?\d+)/(\d+)$')
_FLOAT_RE = re.compile(
    r'^[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?$|'
    r'^[+-]?\d+[eE][+-]?\d+$|'
    r'^\+inf\.0$|^-inf\.0$|^\+nan\.0$|^-nan\.0$'
)
_COMPLEX_RE = re.compile(
    r'^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)?([+-](?:\d+\.?\d*|\.\d+)?(?:[eE][+-]?\d+)?)i$'
)


def tokenize(source: str) -> list[Token]:
    """Tokenize a full source string and return list of tokens."""
    return list(_tokenize_iter(source))


def _tokenize_iter(source: str) -> Iterator[Token]:
    pos = 0
    line = 1
    col = 1
    n = len(source)

    def advance(count: int = 1) -> str:
        nonlocal pos, line, col
        s = source[pos:pos + count]
        for c in s:
            if c == "\n":
                line += 1
                col = 1
            else:
                col += 1
        pos += count
        return s

    def peek(offset: int = 0) -> str:
        i = pos + offset
        return source[i] if i < n else ""

    def read_until_delimiter() -> tuple[str, int, int]:
        start_line, start_col = line, col
        buf = ""
        while pos < n and not re.match(_DELIMITER, source[pos]):
            buf += advance()
        return buf, start_line, start_col

    while pos < n:
        c = peek()
        start_line, start_col = line, col

        # Whitespace
        if c in " \t\r\n":
            advance()
            continue

        # Line comment
        if c == ";":
            while pos < n and peek() != "\n":
                advance()
            continue

        # Block comment #| ... |#
        if c == "#" and peek(1) == "|":
            advance(2)
            depth = 1
            while pos < n and depth > 0:
                if peek() == "#" and peek(1) == "|":
                    advance(2)
                    depth += 1
                elif peek() == "|" and peek(1) == "#":
                    advance(2)
                    depth -= 1
                else:
                    advance()
            if depth > 0:
                raise LexerError("Unterminated block comment", start_line, start_col)
            continue

        # Datum comment #;
        if c == "#" and peek(1) == ";":
            advance(2)
            yield Token(TokenType.DATUM_COMMENT, "#;", start_line, start_col)
            continue

        # #( vector
        if c == "#" and peek(1) == "(":
            advance(2)
            yield Token(TokenType.HASH_LPAREN, "#(", start_line, start_col)
            continue

        # #t #f #true #false
        if c == "#":
            buf, sl, sc = read_until_delimiter()
            lo = buf.lower()
            if lo in ("#t", "#true"):
                yield Token(TokenType.HASH_TRUE, True, sl, sc)
            elif lo in ("#f", "#false"):
                yield Token(TokenType.HASH_FALSE, False, sl, sc)
            elif lo.startswith("#\\"):
                # Character
                char_part = buf[2:]
                if len(char_part) == 0:
                    # #\ followed by space (next char)
                    if pos < n:
                        ch = advance()
                        yield Token(TokenType.CHAR, ch, sl, sc)
                    else:
                        raise LexerError("Unexpected end after #\\", sl, sc)
                elif len(char_part) == 1:
                    yield Token(TokenType.CHAR, char_part, sl, sc)
                else:
                    named = _CHAR_NAMES.get(char_part.lower())
                    if named is not None:
                        yield Token(TokenType.CHAR, named, sl, sc)
                    elif char_part.startswith("x") or char_part.startswith("X"):
                        try:
                            code = int(char_part[1:], 16)
                            yield Token(TokenType.CHAR, chr(code), sl, sc)
                        except ValueError:
                            raise LexerError(f"Unknown char name: {char_part}", sl, sc)
                    else:
                        raise LexerError(f"Unknown char name: {char_part}", sl, sc)
            else:
                # Try as number with prefix
                try:
                    val = _parse_number(buf)
                except ValueError as e:
                    raise LexerError(str(e), sl, sc) from e
                if val is not None:
                    yield _number_token(val, sl, sc)
                else:
                    raise LexerError(f"Unknown # token: {buf}", sl, sc)
            continue

        # String
        if c == '"':
            advance()
            buf = ""
            while pos < n:
                ch = peek()
                if ch == '"':
                    advance()
                    break
                if ch == "\\":
                    advance()
                    esc = advance()
                    if esc == "n":
                        buf += "\n"
                    elif esc == "t":
                        buf += "\t"
                    elif esc == "r":
                        buf += "\r"
                    elif esc == '"':
                        buf += '"'
                    elif esc == "\\":
                        buf += "\\"
                    elif esc == "0":
                        buf += "\0"
                    elif esc == "a":
                        buf += "\x07"
                    elif esc == "b":
                        buf += "\x08"
                    elif esc == "x":
                        # Hex escape \xNN;
                        hex_buf = ""
                        while pos < n and peek() != ";":
                            hex_buf += advance()
                        if pos < n:
                            advance()  # consume ;
                        try:
                            buf += chr(int(hex_buf, 16))
                        except ValueError:
                            raise LexerError(f"Invalid hex escape: {hex_buf}", start_line, start_col)
                    else:
                        buf += esc
                else:
                    buf += advance()
            else:
                raise LexerError("Unterminated string", start_line, start_col)
            yield Token(TokenType.STRING, buf, start_line, start_col)
            continue

        # ( ) [ ]
        if c == "(":
            advance()
            yield Token(TokenType.LPAREN, "(", start_line, start_col)
            continue
        if c == ")":
            advance()
            yield Token(TokenType.RPAREN, ")", start_line, start_col)
            continue
        if c == "[":
            advance()
            yield Token(TokenType.LBRACKET, "[", start_line, start_col)
            continue
        if c == "]":
            advance()
            yield Token(TokenType.RBRACKET, "]", start_line, start_col)
            continue

        # Quote shortcuts
        if c == "'":
            advance()
            yield Token(TokenType.QUOTE, "'", start_line, start_col)
            continue
        if c == "`":
            advance()
            yield Token(TokenType.QUASIQUOTE, "`", start_line, start_col)
            continue
        if c == "," and peek(1) == "@":
            advance(2)
            yield Token(TokenType.UNQUOTE_SPLICING, ",@", start_line, start_col)
            continue
        if c == ",":
            advance()
            yield Token(TokenType.UNQUOTE, ",", start_line, start_col)
            continue

        # Symbol or number
        buf, sl, sc = read_until_delimiter()
        if not buf:
            raise LexerError(f"Unexpected character: {c!r}", start_line, start_col)

        if buf == ".":
            yield Token(TokenType.DOT, ".", sl, sc)
            continue

        # Try to parse as number
        try:
            val = _parse_number(buf)
        except ValueError as e:
            raise LexerError(str(e), sl, sc) from e
        if val is not None:
            yield _number_token(val, sl, sc)
        else:
            yield Token(TokenType.SYMBOL, buf, sl, sc)

    yield Token(TokenType.EOF, None, line, col)


def _number_token(val: object, line: int, col: int) -> Token:
    from fractions import Fraction
    if isinstance(val, int):
        return Token(TokenType.INTEGER, val, line, col)
    if isinstance(val, Fraction):
        return Token(TokenType.RATIONAL, val, line, col)
    if isinstance(val, float):
        return Token(TokenType.FLOAT, val, line, col)
    if isinstance(val, complex):
        return Token(TokenType.COMPLEX, val, line, col)
    return Token(TokenType.FLOAT, val, line, col)


def _parse_number(s: str) -> object | None:
    """Try to parse a string as a Scheme number. Returns None if not a number."""
    from fractions import Fraction

    if not s:
        return None

    lo = s.lower()

    # Special values
    if lo in ("+inf.0", "inf.0"):
        return float("inf")
    if lo == "-inf.0":
        return float("-inf")
    if lo in ("+nan.0", "-nan.0", "nan.0"):
        return float("nan")

    # Radix prefixes: #b #o #d #x, exactness #e #i
    exact = None
    radix = 10
    rest = s
    while rest.startswith("#"):
        prefix = rest[:2].lower()
        rest = rest[2:]
        if prefix == "#b":
            radix = 2
        elif prefix == "#o":
            radix = 8
        elif prefix == "#d":
            radix = 10
        elif prefix == "#x":
            radix = 16
        elif prefix == "#e":
            exact = True
        elif prefix == "#i":
            exact = False
        else:
            return None

    # Try integer
    try:
        val: object = int(rest, radix)
        if exact is False:
            val = float(val)  # type: ignore[arg-type]
        return val
    except ValueError:
        pass

    # Try rational (only base 10 for now)
    if radix == 10:
        m = _RAT_RE.match(rest)
        if m:
            num, den = int(m.group(1)), int(m.group(2))
            if den == 0:
                raise ValueError("Division by zero in rational literal")
            val = Fraction(num, den)
            if exact is False:
                return float(val)
            from sucheme.types import normalize_number
            return normalize_number(val)

        # Try float
        if _FLOAT_RE.match(rest):
            try:
                fval = float(rest)
                if exact is True:
                    return Fraction(fval).limit_denominator(10**15)
                return fval
            except ValueError:
                pass

        # Try complex
        m = _COMPLEX_RE.match(rest)
        if m:
            real_s = m.group(1) or "0"
            imag_s = m.group(2)
            if imag_s in ("+", "-"):
                imag_s += "1"
            try:
                return complex(float(real_s), float(imag_s))
            except ValueError:
                pass

    return None
