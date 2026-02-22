# Copilot Instructions for sucheme-python

This file records all instructions and conventions for AI agents (GitHub Copilot, Claude Code, Codex, etc.) working on this repository.

## Project Overview

**sucheme-python** is a R5RS-compliant Scheme interpreter implemented in Python.
- Repository: https://github.com/suchi/sucheme-python
- Language: Python 3.10+
- License: MIT

## Communication Guidelines

- **Progress reports**: Japanese
- **Commit messages**: English, imperative mood (e.g., "Add unit tests for X")
- **Source code messages** (logs, errors, UI labels): English
- **Documentation (*.md)**: Japanese
- **PR descriptions**: Japanese

## Architecture

```
sucheme/
├── types.py        # Scheme type hierarchy
├── lexer.py        # Tokenizer
├── parser.py       # S-expression parser
├── environment.py  # Lexical scope frames
├── evaluator.py    # Tree-walking evaluator with TCO
├── primitives.py   # R5RS built-in procedures
├── interpreter.py  # High-level interpreter API
├── repl.py         # Interactive REPL
├── cli.py          # Command-line interface
└── web/app.py      # Flask web UI
```

## Key Design Decisions

### TCO (Tail-Call Optimization)
- Uses **trampoline pattern** since Python doesn't support TCO natively
- `TailCall(expr, env)` signals a tail expression
- `TailApply(proc, args)` signals a tail application
- The `eval_expr()` loop continues until a non-tail value is returned

### Macro System
- Hygienic macros via `syntax-rules` with pattern variables and ellipsis (`...`)
- Macros are stored as `MacroProcedure` objects in the environment
- Expansion happens at evaluation time (not compile time)

### Number Tower
- Exact integers: Python `int`
- Exact rationals: Python `fractions.Fraction`
- Inexact reals: Python `float`
- Complex: Python `complex`

### Continuations
- `call/cc` implemented via `ContinuationException`
- Stack unwinding via Python exception propagation
- `dynamic-wind` tracks before/after thunks

## Coding Conventions

- **Python version**: 3.10+ (use `match` sparingly, prefer `isinstance`)
- **Type hints**: Use `from __future__ import annotations` and `Any` for Scheme values
- **Error types**: Use `SchemeError` hierarchy (`SchemeRuntimeError`, `SchemeTypeError`, etc.)
- **Tests**: pytest, fixtures in `@pytest.fixture`, parametrize where appropriate
- **No magic strings**: Use constants or symbols for Scheme names

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=sucheme --cov-report=html

# Specific module
pytest tests/test_evaluator.py -v
```

## R5RS Compliance

Target: Full R5RS compliance including Appendix macros.
See `docs/r5rs-compliance.md` for current status.

## Diagrams

- **Always use Mermaid** for diagrams in Markdown (no ASCII art)
- Use `flowchart`, `sequenceDiagram`, `graph`, `classDiagram`, `gantt`, `pie`

## Sample Programs

- 100+ sample programs in `samples/` directory
- Organized by difficulty: `basic/`, `intermediate/`, `advanced/`
- Each sample should be runnable: `sucheme samples/basic/01-hello-world.scm`

## Release Process

1. Update `sucheme/__init__.py` version
2. Update `CHANGELOG.md`
3. Tag with `git tag v0.x.y`
4. Push tag → GitHub Actions creates release automatically

## Security Considerations

- Never execute arbitrary Python `eval()` from Scheme `eval`
- Sanitize file paths in `load` and file I/O procedures
- The Web UI runs locally by default (127.0.0.1)

## Original Problem Statement

This project was created based on the following requirements:
- R5RS-compliant Scheme interpreter in Python
- Named "sucheme-python" (reflecting repository owner "suchi")
- Interactive REPL with Emacs bindings and multi-line editing
- Web UI for browser-based execution
- CLI with standard Scheme interpreter options
- 100+ sample programs from basic to advanced
- Full documentation in Japanese with Mermaid diagrams
- GitHub Actions CI/CD with GitHub Releases
- ADR (Architecture Decision Records)
- SOW (Statement of Work)
- R5RS compliance table
- Test coverage (visual HTML report)
