; サンプル 23: ブール値演算
(display (and #t #t))   ; => #t
(newline)
(display (and #t #f))   ; => #f
(newline)
(display (or #f #t))    ; => #t
(newline)
(display (or #f #f))    ; => #f
(newline)
(display (not #t))      ; => #f
(newline)
(display (not #f))      ; => #t
(newline)
(display (not 0))       ; => #f (0 は真)
(newline)
(display (boolean? #t)) ; => #t
(newline)
