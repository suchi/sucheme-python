"""
CLI for sucheme.

Provides a command-line interface for the Scheme interpreter.
"""

from __future__ import annotations

import argparse
import os
import sys

from sucheme import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sucheme",
        description="sucheme - A R5RS-compliant Scheme interpreter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sucheme                           Start interactive REPL
  sucheme script.scm                Execute a Scheme file
  sucheme -e "(display (+ 1 2))"   Evaluate an expression
  sucheme --load lib.scm script.scm Load library then run script
  sucheme -i script.scm             Load script then start REPL
""",
    )

    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Scheme source file to execute",
    )

    parser.add_argument(
        "-e", "--eval",
        metavar="EXPR",
        help="Evaluate EXPR and exit",
        dest="eval_expr",
    )

    parser.add_argument(
        "-l", "--load",
        metavar="FILE",
        action="append",
        default=[],
        help="Load FILE before main file or REPL (can be repeated)",
        dest="load_files",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start REPL after loading file(s)",
    )

    parser.add_argument(
        "--no-stdlib",
        action="store_true",
        help="Do not load the standard library",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"sucheme {__version__}",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress startup banner in REPL",
    )

    parser.add_argument(
        "--r5rs",
        action="store_true",
        help="Strict R5RS mode (disable extensions)",
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: exit after evaluation, do not start REPL",
    )

    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        metavar="ARGS",
        help="Arguments passed to the Scheme script as (command-line-arguments)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.debug:
        os.environ["SUCHEME_DEBUG"] = "1"

    from sucheme.interpreter import Interpreter
    from sucheme.types import VOID, SchemeError, SchemeString, list_to_scheme, scheme_repr

    # --no-stdlib and --r5rs both suppress the extension standard library
    use_stdlib = not (ns.no_stdlib or ns.r5rs)
    interp = Interpreter(load_stdlib=use_stdlib)

    # Make command-line args available
    scheme_args = list_to_scheme([SchemeString(a) for a in (ns.args or [])])
    interp.env.define("*program-name*", SchemeString(ns.file or ""))
    interp.env.define("command-line", lambda: scheme_args)
    interp.env.define(
        "command-line-arguments",
        __import__("sucheme.types", fromlist=["PrimitiveProcedure"]).PrimitiveProcedure(
            lambda: scheme_args, "command-line-arguments"
        ),
    )

    # Load preload files
    for load_file in ns.load_files:
        try:
            interp.load_file(load_file)
        except FileNotFoundError:
            print(f"sucheme: cannot open file {load_file!r}", file=sys.stderr)
            return 1
        except SchemeError as e:
            print(f"sucheme: error in {load_file!r}: {e}", file=sys.stderr)
            if ns.debug:
                import traceback
                traceback.print_exc()
            return 1

    # Evaluate expression
    if ns.eval_expr:
        try:
            results = interp.eval_string(ns.eval_expr)
            for r in results:
                if r is not VOID:
                    print(scheme_repr(r))
        except SchemeError as e:
            print(f"sucheme: {e}", file=sys.stderr)
            return 1
        if not ns.interactive or ns.batch:
            return 0

    # Execute file
    if ns.file:
        try:
            interp.load_file(ns.file)
        except FileNotFoundError:
            print(f"sucheme: cannot open file {ns.file!r}", file=sys.stderr)
            return 1
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0
        except SchemeError as e:
            print(f"sucheme: {ns.file}: {e}", file=sys.stderr)
            if ns.debug:
                import traceback
                traceback.print_exc()
            return 1
        if not ns.interactive or ns.batch:
            return 0

    # --batch without a file or expression: just exit
    if ns.batch:
        return 0

    # Start REPL
    from sucheme.repl import REPL
    repl = REPL(interp)
    if ns.quiet:
        # Suppress banner by monkey-patching
        import sucheme.repl as repl_module
        repl_module.BANNER = ""
    repl.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
