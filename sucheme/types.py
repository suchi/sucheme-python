"""
Scheme type definitions for sucheme.

Implements the R5RS type hierarchy:
  Boolean, Number (exact/inexact), Character, String, Symbol,
  Pair (list), Vector, Port, Procedure, Void
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Callable, Optional


class SchemeError(Exception):
    """Base class for Scheme runtime errors."""


class SchemeSyntaxError(SchemeError):
    """Raised for syntax/parse errors."""


class SchemeRuntimeError(SchemeError):
    """Raised for runtime evaluation errors."""


class SchemeTypeError(SchemeRuntimeError):
    """Raised for type mismatch errors."""


class SchemeArityError(SchemeRuntimeError):
    """Raised when wrong number of arguments are passed."""


class SchemeNameError(SchemeRuntimeError):
    """Raised when an unbound variable is referenced."""


class SchemeContinuationError(SchemeRuntimeError):
    """Raised for continuation-related errors."""


# ---------------------------------------------------------------------------
# Sentinel / Void
# ---------------------------------------------------------------------------

class _Void:
    """Represents the void/unspecified value in Scheme."""
    _instance: Optional["_Void"] = None

    def __new__(cls) -> "_Void":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "#<void>"

    def __bool__(self) -> bool:
        return True  # void is not #f


VOID = _Void()


class _Nil:
    """Represents the empty list '() in Scheme."""
    _instance: Optional["_Nil"] = None

    def __new__(cls) -> "_Nil":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "()"

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __bool__(self) -> bool:
        return True  # '() is not #f in Scheme


NIL = _Nil()


# ---------------------------------------------------------------------------
# Symbol
# ---------------------------------------------------------------------------

_symbol_table: dict[str, "Symbol"] = {}


class Symbol:
    """Interned symbol type."""
    __slots__ = ("name",)

    def __new__(cls, name: str) -> "Symbol":
        if name in _symbol_table:
            return _symbol_table[name]
        obj = super().__new__(cls)
        obj.name = name
        _symbol_table[name] = obj
        return obj

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return self is other


def symbol(name: str) -> Symbol:
    """Create or retrieve an interned Symbol."""
    return Symbol(name)


# ---------------------------------------------------------------------------
# Boolean
# ---------------------------------------------------------------------------

class Boolean:
    """Scheme boolean type. Only #t and #f exist."""
    _true: Optional["Boolean"] = None
    _false: Optional["Boolean"] = None

    def __new__(cls, value: bool) -> "Boolean":
        if value:
            if cls._true is None:
                cls._true = super().__new__(cls)
                cls._true.value = True
            return cls._true
        else:
            if cls._false is None:
                cls._false = super().__new__(cls)
                cls._false.value = False
            return cls._false

    def __repr__(self) -> str:
        return "#t" if self.value else "#f"

    def __bool__(self) -> bool:
        return self.value

    def __eq__(self, other: object) -> bool:
        return self is other


TRUE = Boolean(True)
FALSE = Boolean(False)


def scheme_bool(v: bool) -> Boolean:
    return TRUE if v else FALSE


# ---------------------------------------------------------------------------
# Number
# ---------------------------------------------------------------------------

# R5RS numeric tower: integer (exact), rational (exact), real (inexact), complex
# We represent exact integers as Python int, exact rationals as Fraction,
# inexact reals as float.  Complex uses Python complex.

Number = int | Fraction | float | complex


def is_exact(n: Any) -> bool:
    return isinstance(n, (int, Fraction))


def is_inexact(n: Any) -> bool:
    return isinstance(n, (float, complex))


def is_integer_val(n: Any) -> bool:
    if isinstance(n, int):
        return True
    if isinstance(n, Fraction):
        return n.denominator == 1
    if isinstance(n, float):
        return n == math.floor(n) and not math.isinf(n)
    return False


def exact_to_inexact(n: Any) -> float:
    if isinstance(n, int):
        return float(n)
    if isinstance(n, Fraction):
        return float(n)
    return n


def inexact_to_exact(n: Any) -> int | Fraction:
    if isinstance(n, int):
        return n
    if isinstance(n, Fraction):
        return n
    if isinstance(n, float):
        if math.isinf(n) or math.isnan(n):
            raise SchemeRuntimeError(f"Cannot convert {n} to exact")
        return Fraction(n).limit_denominator(10**15)
    raise SchemeTypeError(f"inexact->exact: not a number: {n!r}")


def normalize_number(n: Any) -> Any:
    """Normalize Fraction with denominator 1 to int."""
    if isinstance(n, Fraction) and n.denominator == 1:
        return n.numerator
    return n


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------

class Char:
    """Scheme character type."""
    __slots__ = ("char",)
    _cache: dict[str, "Char"] = {}

    def __new__(cls, c: str) -> "Char":
        assert len(c) == 1
        if c in cls._cache:
            return cls._cache[c]
        obj = super().__new__(cls)
        obj.char = c
        cls._cache[c] = obj
        return obj

    def __repr__(self) -> str:
        names = {
            " ": "#\\space",
            "\n": "#\\newline",
            "\t": "#\\tab",
            "\r": "#\\return",
            "\x00": "#\\null",
            "\x08": "#\\backspace",
            "\x0c": "#\\page",
            "\x1b": "#\\escape",
            "\x7f": "#\\delete",
            "\x0b": "#\\altmode",
        }
        if self.char in names:
            return names[self.char]
        return f"#\\{self.char}"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return hash(self.char)


# ---------------------------------------------------------------------------
# Pair / List
# ---------------------------------------------------------------------------

class Pair:
    """Scheme cons cell."""
    __slots__ = ("car", "cdr")

    def __init__(self, car: Any, cdr: Any) -> None:
        self.car = car
        self.cdr = cdr

    def __repr__(self) -> str:
        return f"({_pair_repr(self)})"

    def __iter__(self):
        """Iterate as a proper list."""
        cur = self
        while isinstance(cur, Pair):
            yield cur.car
            cur = cur.cdr
        if cur is not NIL:
            raise SchemeTypeError("Not a proper list")

    def to_list(self) -> list:
        return list(self)


def _pair_repr(p: Any) -> str:
    parts = []
    cur = p
    while isinstance(cur, Pair):
        parts.append(scheme_repr(cur.car))
        cur = cur.cdr
    if cur is NIL:
        return " ".join(parts)
    parts.append(".")
    parts.append(scheme_repr(cur))
    return " ".join(parts)


def cons(a: Any, b: Any) -> Pair:
    return Pair(a, b)


def car(p: Any) -> Any:
    if not isinstance(p, Pair):
        raise SchemeTypeError(f"car: not a pair: {p!r}")
    return p.car


def cdr(p: Any) -> Any:
    if not isinstance(p, Pair):
        raise SchemeTypeError(f"cdr: not a pair: {p!r}")
    return p.cdr


def list_to_scheme(lst: list) -> Any:
    result = NIL
    for item in reversed(lst):
        result = Pair(item, result)
    return result


def scheme_to_list(obj: Any) -> list:
    result = []
    while isinstance(obj, Pair):
        result.append(obj.car)
        obj = obj.cdr
    if obj is not NIL:
        raise SchemeTypeError(f"Not a proper list: {obj!r}")
    return result


def list_length(obj: Any) -> int:
    n = 0
    while isinstance(obj, Pair):
        obj = obj.cdr
        n += 1
    if obj is not NIL:
        raise SchemeTypeError("Not a proper list")
    return n


# ---------------------------------------------------------------------------
# Vector
# ---------------------------------------------------------------------------

class Vector:
    """Scheme vector type."""
    __slots__ = ("data",)

    def __init__(self, data: list) -> None:
        self.data = data

    def __repr__(self) -> str:
        return "#(" + " ".join(scheme_repr(x) for x in self.data) + ")"

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, i: int) -> Any:
        return self.data[i]

    def __setitem__(self, i: int, v: Any) -> None:
        self.data[i] = v


# ---------------------------------------------------------------------------
# String (mutable in R5RS)
# ---------------------------------------------------------------------------

class SchemeString:
    """Mutable Scheme string."""
    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        # Escape special characters
        s = self.value
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("\n", "\\n")
        s = s.replace("\r", "\\r")
        s = s.replace("\t", "\\t")
        s = s.replace("\0", "\\0")
        return f'"{s}"'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SchemeString):
            return self.value == other.value
        return False

    def __len__(self) -> int:
        return len(self.value)

    def __hash__(self) -> int:
        return hash(self.value)


# ---------------------------------------------------------------------------
# Procedure types
# ---------------------------------------------------------------------------

class Procedure:
    """Base class for all callable procedures."""

    def __call__(self, *args: Any) -> Any:
        raise NotImplementedError


class PrimitiveProcedure(Procedure):
    """Built-in (primitive) procedure implemented in Python."""

    def __init__(self, fn: Callable, name: str = "") -> None:
        self._fn = fn
        self.name = name

    def __call__(self, *args: Any) -> Any:
        return self._fn(*args)

    def __repr__(self) -> str:
        return f"#<primitive {self.name}>"


class LambdaProcedure(Procedure):
    """User-defined lambda procedure."""

    def __init__(self, params: Any, body: list, env: Any, name: str = "") -> None:
        self.params = params   # Symbol | list of Symbol | dotted list
        self.body = body       # list of expressions
        self.env = env         # closure environment
        self.name = name

    def __repr__(self) -> str:
        n = self.name if self.name else "lambda"
        return f"#<procedure {n}>"


class MacroProcedure:
    """Syntax-rules macro transformer."""

    def __init__(self, transformer: Any, env: Any, name: str = "") -> None:
        self.transformer = transformer  # SyntaxRules object
        self.env = env
        self.name = name

    def __repr__(self) -> str:
        n = self.name if self.name else "macro"
        return f"#<macro {n}>"


class ContinuationProcedure(Procedure):
    """First-class continuation (from call/cc)."""

    def __init__(self, fn: Callable) -> None:
        self._fn = fn

    def __call__(self, *args: Any) -> Any:
        return self._fn(*args)

    def __repr__(self) -> str:
        return "#<continuation>"


# ---------------------------------------------------------------------------
# Port
# ---------------------------------------------------------------------------

class Port:
    """Scheme I/O port."""

    def __init__(self, file_obj: Any, mode: str) -> None:
        self._file = file_obj
        self.mode = mode  # "r" or "w"
        self.closed = False

    def __repr__(self) -> str:
        direction = "input" if self.mode == "r" else "output"
        name = getattr(self._file, "name", "?")
        return f"#<{direction}-port {name}>"

    def close(self) -> None:
        self._file.close()
        self.closed = True

    @property
    def file(self) -> Any:
        return self._file


# ---------------------------------------------------------------------------
# Tail-call trampoline
# ---------------------------------------------------------------------------

class TailCall:
    """Represents a pending tail call for TCO."""
    __slots__ = ("expr", "env")

    def __init__(self, expr: Any, env: Any) -> None:
        self.expr = expr
        self.env = env


class TailApply:
    """Represents a pending procedure application for TCO."""
    __slots__ = ("proc", "args")

    def __init__(self, proc: Any, args: list) -> None:
        self.proc = proc
        self.args = args


# ---------------------------------------------------------------------------
# Continuation exception (used for call/cc)
# ---------------------------------------------------------------------------

class ContinuationException(Exception):
    """Used to unwind the stack for call/cc."""

    def __init__(self, cont_id: int, values: list) -> None:
        self.cont_id = cont_id
        self.values = values


# ---------------------------------------------------------------------------
# Values (multiple return values)
# ---------------------------------------------------------------------------

class Values:
    """Multiple return values."""

    def __init__(self, *values: Any) -> None:
        self.values = list(values)

    def __repr__(self) -> str:
        return " ".join(scheme_repr(v) for v in self.values)


# ---------------------------------------------------------------------------
# Display / write helpers
# ---------------------------------------------------------------------------

def scheme_repr(obj: Any) -> str:
    """Return the 'write' representation of a Scheme object."""
    if obj is NIL:
        return "()"
    if obj is VOID:
        return ""
    if obj is TRUE:
        return "#t"
    if obj is FALSE:
        return "#f"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, Fraction):
        return f"{obj.numerator}/{obj.denominator}"
    if isinstance(obj, float):
        if math.isinf(obj):
            return "+inf.0" if obj > 0 else "-inf.0"
        if math.isnan(obj):
            return "+nan.0"
        # Format without unnecessary trailing zeros
        s = repr(obj)
        return s
    if isinstance(obj, complex):
        r = scheme_repr(obj.real)
        i = obj.imag
        sign = "+" if i >= 0 else ""
        return f"{r}{sign}{i}i"
    if isinstance(obj, (Symbol, Boolean, Pair, Vector, Char, SchemeString,
                        Procedure, MacroProcedure, ContinuationProcedure,
                        Port, Values, _Void, _Nil)):
        return repr(obj)
    # Fallback for Python native types passed through
    return repr(obj)


def scheme_display(obj: Any) -> str:
    """Return the 'display' representation of a Scheme object (no string quotes)."""
    if isinstance(obj, SchemeString):
        return obj.value
    if isinstance(obj, Char):
        return obj.char
    if obj is VOID:
        return ""
    return scheme_repr(obj)
