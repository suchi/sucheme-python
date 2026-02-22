; サンプル 27: 多値
; values と call-with-values

(define (div-and-mod a b)
  (values (quotient a b) (remainder a b)))

(call-with-values
  (lambda () (div-and-mod 17 5))
  (lambda (q r)
    (display "商: ") (display q) (newline)
    (display "余: ") (display r) (newline)))

; 多値を使った min/max 同時返却
(define (minmax lst)
  (values (apply min lst) (apply max lst)))

(call-with-values
  (lambda () (minmax (quote (3 1 4 1 5 9 2 6))))
  (lambda (lo hi)
    (display "min=") (display lo)
    (display " max=") (display hi)
    (newline)))
