; サンプル 25: ベクタ操作
(define v (vector 1 2 3 4 5))
(display v)                    ; => #(1 2 3 4 5)
(newline)
(display (vector-length v))    ; => 5
(newline)
(display (vector-ref v 2))     ; => 3
(newline)
(vector-set! v 2 99)
(display v)                    ; => #(1 2 99 4 5)
(newline)
(display (vector->list v))     ; => (1 2 99 4 5)
(newline)
(display (list->vector (quote (a b c))))  ; => #(a b c)
(newline)
(define v2 (make-vector 3 0))
(display v2)                   ; => #(0 0 0)
(newline)
