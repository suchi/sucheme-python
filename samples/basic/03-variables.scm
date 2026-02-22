; サンプル 03: 変数の定義と使用
; define と set! の使い方

(define x 10)
(define y 20)
(define sum (+ x y))

(display sum)    ; => 30
(newline)

; 変数を更新
(set! x 100)
(display x)      ; => 100
(newline)
