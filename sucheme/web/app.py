"""
Web UI for sucheme.

Provides a simple Flask web application with a Scheme REPL interface.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>sucheme - Scheme Web REPL</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Courier New', monospace;
      background: #1a1a2e;
      color: #e0e0e0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #16213e;
      padding: 12px 20px;
      display: flex;
      align-items: center;
      gap: 10px;
      border-bottom: 1px solid #0f3460;
    }
    header h1 { color: #e94560; font-size: 1.4rem; }
    header span { color: #a0a0c0; font-size: 0.85rem; }
    .container {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 12px;
      gap: 8px;
      overflow: hidden;
    }
    #output {
      flex: 1;
      background: #0d0d1a;
      border: 1px solid #2a2a4a;
      border-radius: 4px;
      padding: 10px;
      overflow-y: auto;
      font-size: 0.9rem;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .output-line { margin: 2px 0; }
    .output-input { color: #64b5f6; }
    .output-result { color: #a5d6a7; }
    .output-error { color: #ef9a9a; }
    .output-print { color: #e0e0e0; }
    .input-row {
      display: flex;
      gap: 8px;
    }
    #prompt-label { color: #e94560; padding: 8px 4px; font-weight: bold; }
    #input {
      flex: 1;
      background: #0d0d1a;
      border: 1px solid #2a2a4a;
      border-radius: 4px;
      padding: 8px;
      color: #e0e0e0;
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      resize: vertical;
      min-height: 40px;
    }
    #input:focus { border-color: #e94560; }
    button {
      background: #e94560;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      cursor: pointer;
      font-family: inherit;
      align-self: flex-end;
    }
    button:hover { background: #c73652; }
    .examples {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    .example-btn {
      background: #16213e;
      color: #64b5f6;
      border: 1px solid #2a2a4a;
      padding: 3px 8px;
      font-size: 0.8rem;
      cursor: pointer;
      border-radius: 3px;
    }
    .example-btn:hover { background: #1a2a50; }
    .toolbar {
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }
    .toolbar button {
      background: #16213e;
      color: #a0a0c0;
      border: 1px solid #2a2a4a;
      padding: 4px 10px;
      font-size: 0.8rem;
    }
    .toolbar button:hover { background: #1e2a50; }
  </style>
</head>
<body>
  <header>
    <h1>🔵 sucheme</h1>
    <span>R5RS Scheme Interpreter</span>
  </header>
  <div class="container">
    <div id="output">
      <div class="output-print">sucheme Web REPL - Type Scheme expressions and press Enter or click Run.</div>
      <div class="output-print">Examples: (+ 1 2 3)  (map car '((a 1) (b 2)))  (define (fact n) (if (&lt;= n 1) 1 (* n (fact (- n 1)))))</div>
    </div>
    <div class="toolbar">
      <span style="color:#a0a0c0;font-size:0.8rem">Examples:</span>
      <button class="example-btn" onclick="setInput('(+ 1 2 3)')">(+ 1 2 3)</button>
      <button class="example-btn" onclick="setInput(&quot;(define (fact n) (if (&lt;= n 1) 1 (* n (fact (- n 1)))))\n(fact 10)&quot;)">(fact 10)</button>
      <button class="example-btn" onclick="setInput(&quot;(map (lambda (x) (* x x)) '(1 2 3 4 5))&quot;)">map</button>
      <button class="example-btn" onclick="setInput(&quot;(define (fib n) (let loop ((i 0) (a 0) (b 1)) (if (= i n) a (loop (+ i 1) b (+ a b)))))\n(fib 20)&quot;)">fibonacci</button>
      <button class="example-btn" onclick="clearOutput()">Clear</button>
    </div>
    <div class="input-row">
      <span id="prompt-label">λ></span>
      <textarea id="input" rows="2" placeholder="Enter Scheme expression..." 
        onkeydown="handleKey(event)"></textarea>
      <button onclick="runCode()">Run</button>
    </div>
  </div>
  <script>
    const output = document.getElementById('output');
    const input = document.getElementById('input');
    let history = [];
    let histIdx = -1;

    function appendOutput(text, cls) {
      const div = document.createElement('div');
      div.className = 'output-line ' + cls;
      div.textContent = text;
      output.appendChild(div);
      output.scrollTop = output.scrollHeight;
    }

    function clearOutput() {
      output.innerHTML = '';
    }

    function setInput(text) {
      input.value = text;
      input.focus();
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        runCode();
      } else if (e.key === 'ArrowUp' && e.ctrlKey) {
        e.preventDefault();
        if (histIdx < history.length - 1) {
          histIdx++;
          input.value = history[history.length - 1 - histIdx];
        }
      } else if (e.key === 'ArrowDown' && e.ctrlKey) {
        e.preventDefault();
        if (histIdx > 0) {
          histIdx--;
          input.value = history[history.length - 1 - histIdx];
        } else {
          histIdx = -1;
          input.value = '';
        }
      }
    }

    async function runCode() {
      const code = input.value.trim();
      if (!code) return;
      history.push(code);
      histIdx = -1;
      appendOutput('λ> ' + code.replace(/\\n/g, ' '), 'output-input');
      input.value = '';
      try {
        const resp = await fetch('/eval', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({expr: code})
        });
        const data = await resp.json();
        if (data.output) {
          appendOutput(data.output, 'output-print');
        }
        if (data.result !== undefined && data.result !== '') {
          appendOutput(data.result, 'output-result');
        }
        if (data.error) {
          appendOutput('Error: ' + data.error, 'output-error');
        }
      } catch (e) {
        appendOutput('Network error: ' + e, 'output-error');
      }
    }
  </script>
</body>
</html>
"""


# Session-based interpreter (one per process)
_interp = None
_captured_output: list[str] = []


def _get_interpreter():
    global _interp
    if _interp is None:
        from sucheme.interpreter import Interpreter
        _interp = Interpreter()
        # Patch print to capture output
        _install_output_capture(_interp)
    return _interp


def _install_output_capture(interp) -> None:
    """Redirect display/write/newline to capture output."""
    from sucheme.types import (
        PrimitiveProcedure, VOID, SchemeString, Char, SchemeTypeError,
        scheme_display, scheme_repr, Port
    )

    def capture_display(*args):
        _check_args(args, "display")
        s = scheme_display(args[0])
        _captured_output.append(s)
        return VOID

    def capture_write(*args):
        _check_args(args, "write")
        s = scheme_repr(args[0])
        _captured_output.append(s)
        return VOID

    def capture_newline(*args):
        _captured_output.append("\n")
        return VOID

    def capture_write_char(*args):
        if not args:
            return VOID
        ch = args[0]
        if isinstance(ch, Char):
            _captured_output.append(ch.char)
        return VOID

    def _check_args(args, name):
        if not args:
            raise SchemeTypeError(f"{name}: no arguments")

    interp.env.define("display", PrimitiveProcedure(capture_display, "display"))
    interp.env.define("write", PrimitiveProcedure(capture_write, "write"))
    interp.env.define("newline", PrimitiveProcedure(capture_newline, "newline"))
    interp.env.define("write-char", PrimitiveProcedure(capture_write_char, "write-char"))


@app.route("/")
def index():
    return render_template_string(_HTML)


@app.route("/eval", methods=["POST"])
def eval_endpoint():
    from sucheme.types import VOID, SchemeError, scheme_repr, Values

    data = request.get_json(force=True, silent=True) or {}
    expr = data.get("expr", "")

    if not expr or not expr.strip():
        return jsonify({"result": "", "output": "", "error": ""})

    interp = _get_interpreter()
    _captured_output.clear()

    try:
        results = interp.eval_string(expr)
        output_str = "".join(_captured_output)
        result_parts = []
        for r in results:
            if r is not VOID:
                if isinstance(r, Values):
                    result_parts.extend(scheme_repr(v) for v in r.values)
                else:
                    result_parts.append(scheme_repr(r))
        return jsonify({
            "result": "\n".join(result_parts),
            "output": output_str,
            "error": "",
        })
    except SystemExit:
        return jsonify({"result": "", "output": "", "error": "exit called"})
    except SchemeError as e:
        return jsonify({"result": "", "output": "".join(_captured_output), "error": str(e)})
    except Exception as e:
        return jsonify({"result": "", "output": "".join(_captured_output), "error": f"Internal error: {e}"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": __import__("sucheme").__version__})


def main():
    import argparse
    parser = argparse.ArgumentParser(description="sucheme Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    ns = parser.parse_args()

    print(f"Starting sucheme Web UI at http://{ns.host}:{ns.port}/")
    app.run(host=ns.host, port=ns.port, debug=ns.debug)


if __name__ == "__main__":
    main()
