; サンプル 28: 例外処理
; guard と with-exception-handler

; guard によるパターンマッチ例外処理
(define (safe-divide a b)
  (guard (exn
          (#t (display "Error: division by zero") (newline) 0))
    (/ a b)))

(display (safe-divide 10 2))   ; => 5
(newline)
(display (safe-divide 10 0))   ; => Error: ... 0
(newline)

; with-exception-handler
(with-exception-handler
  (lambda (e)
    (display "Caught: ")
    (display e)
    (newline))
  (lambda ()
    (error "Something went wrong" 42)))
