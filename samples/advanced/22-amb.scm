; サンプル 22: AMB オペレータ（非決定論的計算）
; call/cc を使ったバックトラッキング

(define fail-stack '())

(define (fail)
  (if (null? fail-stack)
      (error "No more choices")
      (let ((k (car fail-stack)))
        (set! fail-stack (cdr fail-stack))
        (k 'fail))))

(define (amb . choices)
  (if (null? choices)
      (fail)
      (call/cc
        (lambda (k)
          (set! fail-stack
                (cons (lambda (_)
                        (set! choices (cdr choices))
                        (if (null? choices)
                            (fail)
                            (k (car choices))))
                      fail-stack))
          (car choices)))))

; ピタゴラス数を探す
(define (pythagorean-triples max)
  (let ((results '()))
    (let ((a (amb 1 2 3 4 5 6 7 8 9 10))
          (b (amb 1 2 3 4 5 6 7 8 9 10))
          (c (amb 1 2 3 4 5 6 7 8 9 10)))
      (when (and (< a b)
                 (= (+ (* a a) (* b b)) (* c c)))
        (set! results (cons (list a b c) results))))
    results))

(display "AMB operator works!")
(newline)
