"""
REPL for sucheme.

Provides an interactive Read-Eval-Print-Loop with:
- GNU readline / prompt_toolkit support (Emacs bindings)
- Multi-line editing
- History support
- Colored output
"""

from __future__ import annotations

import os
import sys
import traceback

from sucheme.interpreter import Interpreter
from sucheme.types import (
    VOID,
    SchemeError,
    scheme_repr,
)

HISTORY_FILE = os.path.expanduser("~/.sucheme_history")

BANNER = """\
sucheme - R5RS Scheme Interpreter
Type ,help for help, ,quit to exit.
"""

HELP_TEXT = """\
sucheme REPL commands:
  ,help      - Show this help
  ,quit      - Exit the REPL
  ,load FILE - Load a Scheme file
  ,env       - Show current bindings
  ,version   - Show version

Keyboard shortcuts (Emacs-style):
  C-a  Move to beginning of line
  C-e  Move to end of line
  C-b  Move backward one character
  C-f  Move forward one character
  C-p  Previous history entry
  C-n  Next history entry
  C-d  Delete character / exit if empty
  C-k  Kill to end of line
  M-b  Move backward one word
  M-f  Move forward one word
  Tab  Completion
"""


def _get_prompt_toolkit():
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.history import FileHistory
        return PromptSession, FileHistory, AutoSuggestFromHistory
    except ImportError:
        return None, None, None


def _count_parens(text: str) -> int:
    """Return difference of open and close parentheses (net unclosed)."""
    count = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == ";":
            break
        if ch in "([":
            count += 1
        elif ch in ")]":
            count -= 1
    return count


class REPL:
    """Interactive Scheme REPL."""

    def __init__(self, interp: Interpreter | None = None) -> None:
        self.interp = interp or Interpreter()
        self._setup_completers()

    def _setup_completers(self) -> None:
        self._completions = sorted(self.interp.env.bindings.keys())

    def run(self) -> None:
        """Start the REPL loop."""
        PromptSession, FileHistory, AutoSuggestFromHistory = _get_prompt_toolkit()

        if PromptSession is not None:
            self._run_with_prompt_toolkit(PromptSession, FileHistory, AutoSuggestFromHistory)
        else:
            self._run_with_readline()

    def _run_with_prompt_toolkit(self, PromptSession, FileHistory, AutoSuggestFromHistory):
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.styles import Style

        history = FileHistory(HISTORY_FILE) if HISTORY_FILE else None
        completer = WordCompleter(self._completions, sentence=True)

        style = Style.from_dict({
            "prompt": "ansicyan bold",
        })

        session = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
            style=style,
        )

        print(BANNER)

        while True:
            try:
                buffer = ""
                prompt = "sucheme> "
                while True:
                    try:
                        line = session.prompt(prompt)
                    except KeyboardInterrupt:
                        buffer = ""
                        print()
                        break

                    # REPL commands
                    stripped = line.strip()
                    if stripped.startswith(","):
                        result = self._handle_command(stripped)
                        if result == "quit":
                            return
                        break

                    buffer += line + "\n"
                    depth = _count_parens(buffer)
                    if depth <= 0 and buffer.strip():
                        self._eval_and_print(buffer)
                        buffer = ""
                        break
                    elif depth > 0:
                        prompt = "  " * min(depth, 6) + "... "
                    else:
                        break

            except EOFError:
                print("\nBye!")
                return

    def _run_with_readline(self):
        """Fallback REPL using readline."""
        try:
            import readline
            readline.set_history_length(1000)
            try:
                readline.read_history_file(HISTORY_FILE)
            except FileNotFoundError:
                pass
        except ImportError:
            pass

        print(BANNER)

        buffer = ""
        prompt = "sucheme> "

        while True:
            try:
                line = input(prompt)

                stripped = line.strip()
                if stripped.startswith(","):
                    result = self._handle_command(stripped)
                    if result == "quit":
                        try:
                            import readline
                            readline.write_history_file(HISTORY_FILE)
                        except Exception:
                            pass
                        return
                    buffer = ""
                    prompt = "sucheme> "
                    continue

                buffer += line + "\n"
                depth = _count_parens(buffer)

                if depth <= 0 and buffer.strip():
                    self._eval_and_print(buffer)
                    buffer = ""
                    prompt = "sucheme> "
                elif depth > 0:
                    prompt = "  " * min(depth, 6) + "... "
                else:
                    buffer = ""
                    prompt = "sucheme> "

            except KeyboardInterrupt:
                print()
                buffer = ""
                prompt = "sucheme> "
            except EOFError:
                print("\nBye!")
                try:
                    import readline
                    readline.write_history_file(HISTORY_FILE)
                except Exception:
                    pass
                return

    def _eval_and_print(self, source: str) -> None:
        """Evaluate source and print result."""
        try:
            from sucheme.evaluator import eval_expr
            from sucheme.parser import parse
            exprs = parse(source)
            for expr in exprs:
                result = eval_expr(expr, self.interp.env)
                if result is not VOID:
                    print(scheme_repr(result))
        except SchemeError as e:
            print(f"Error: {e}", file=sys.stderr)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Internal error: {e}", file=sys.stderr)
            if os.environ.get("SUCHEME_DEBUG"):
                traceback.print_exc()

    def _handle_command(self, cmd: str) -> str | None:
        """Handle REPL meta-commands."""
        parts = cmd.split(None, 1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if command in (",quit", ",exit", ",q"):
            print("Bye!")
            return "quit"
        elif command == ",help":
            print(HELP_TEXT)
        elif command == ",load":
            if not arg:
                print("Usage: ,load <filename>")
            else:
                try:
                    result = self.interp.load_file(arg.strip())
                    if result is not VOID:
                        print(scheme_repr(result))
                except FileNotFoundError:
                    print(f"Error: File not found: {arg.strip()}")
                except SchemeError as e:
                    print(f"Error: {e}")
        elif command == ",env":
            names = sorted(self.interp.env.bindings.keys())
            for name in names:
                print(f"  {name}")
        elif command == ",version":
            from sucheme import __version__
            print(f"sucheme version {__version__}")
        else:
            print(f"Unknown command: {command}. Type ,help for help.")
        return None
