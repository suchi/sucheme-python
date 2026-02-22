"""
Environment (frame) for sucheme.

Implements lexical scoping with frame-based environments.
"""

from __future__ import annotations

from typing import Any

from sucheme.types import SchemeNameError


class Environment:
    """A lexical scope frame."""

    def __init__(self, parent: "Environment | None" = None) -> None:
        self.bindings: dict[str, Any] = {}
        self.parent = parent

    def lookup(self, name: str) -> Any:
        env: Environment | None = self
        while env is not None:
            if name in env.bindings:
                return env.bindings[name]
            env = env.parent
        raise SchemeNameError(f"Unbound variable: {name!r}")

    def define(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def set(self, name: str, value: Any) -> None:
        """set! - mutate an existing binding."""
        env: Environment | None = self
        while env is not None:
            if name in env.bindings:
                env.bindings[name] = value
                return
            env = env.parent
        raise SchemeNameError(f"Unbound variable: {name!r}")

    def extend(self, params: Any, args: list) -> "Environment":
        """Create a child frame with params bound to args."""
        from sucheme.types import NIL, Pair, Symbol
        child = Environment(parent=self)

        if isinstance(params, Symbol):
            # (lambda args body) - rest parameter
            from sucheme.types import list_to_scheme
            child.define(params.name, list_to_scheme(args))
        elif params is NIL:
            if args:
                from sucheme.types import SchemeArityError
                raise SchemeArityError(f"Expected 0 args, got {len(args)}")
        else:
            # params is a list (possibly improper for rest args)
            required = []
            rest_param = None
            cur = params
            while isinstance(cur, Pair):
                required.append(cur.car.name)
                cur = cur.cdr
            if cur is NIL:
                pass
            elif isinstance(cur, Symbol):
                rest_param = cur.name
            else:
                from sucheme.types import SchemeTypeError
                raise SchemeTypeError(f"Invalid parameter list: {params!r}")

            if rest_param is None:
                if len(args) != len(required):
                    from sucheme.types import SchemeArityError
                    raise SchemeArityError(
                        f"Expected {len(required)} args, got {len(args)}"
                    )
                for name, val in zip(required, args):
                    child.define(name, val)
            else:
                if len(args) < len(required):
                    from sucheme.types import SchemeArityError
                    raise SchemeArityError(
                        f"Expected at least {len(required)} args, got {len(args)}"
                    )
                for name, val in zip(required, args):
                    child.define(name, val)
                from sucheme.types import list_to_scheme
                child.define(rest_param, list_to_scheme(args[len(required):]))

        return child

    def __repr__(self) -> str:
        keys = list(self.bindings.keys())[:5]
        return f"<Env {keys}...>"
