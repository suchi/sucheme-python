; サンプル 26: 準クォート
(define x 10)
(define lst (quote (1 2 3)))

(display `(a ,x c))          ; => (a 10 c)
(newline)
(display `(a ,@lst d))       ; => (a 1 2 3 d)
(newline)
(display `(,x ,(+ x 1) ,(* x 2)))  ; => (10 11 20)
(newline)

; ネストした準クォート
(define (make-let bindings body)
  `(let ,bindings ,@body))

(display (make-let (quote ((x 1) (y 2))) (quote ((+ x y)))))
; => (let ((x 1) (y 2)) (+ x y))
(newline)
