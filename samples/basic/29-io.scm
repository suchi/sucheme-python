; サンプル 29: 入出力
; write, display, newline の違い

(display "hello")    ; => hello (文字列の引用符なし)
(newline)
(write "hello")      ; => "hello" (文字列の引用符あり)
(newline)
(display #\a)        ; => a
(newline)
(write #\a)          ; => #\a
(newline)
(display (quote (1 2 3)))  ; => (1 2 3)
(newline)
(write (quote (1 2 3)))    ; => (1 2 3)
(newline)

; open-output-string によるキャプチャ
(define port (open-output-string))
(display "captured" port)
(display "!" port)
(display (get-output-string port))
(newline)
