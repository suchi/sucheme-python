; サンプル 32: パターンマッチング風マクロ
; cond と destructuring を使ったパターンマッチング

; 型ディスパッチのパターンマッチ
(define (describe x)
  (cond ((null? x) "empty list")
        ((pair? x)
         (string-append "list of length "
                       (number->string (length x))))
        ((number? x)
         (string-append "number: " (number->string x)))
        ((string? x)
         (string-append "string: " x))
        ((symbol? x)
         (string-append "symbol: " (symbol->string x)))
        (else "unknown")))

(display (describe '()))       ; => empty list
(newline)
(display (describe '(1 2 3)))  ; => list of length 3
(newline)
(display (describe 42))        ; => number: 42
(newline)
(display (describe "hello"))   ; => string: hello
(newline)
(display (describe 'foo))      ; => symbol: foo
(newline)
