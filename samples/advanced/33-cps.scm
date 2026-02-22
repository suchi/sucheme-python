; サンプル 33: 継続渡しスタイル（CPS）
; Continuation Passing Style

; CPS 変換した階乗
(define (factorial-cps n k)
  (if (<= n 1)
      (k 1)
      (factorial-cps (- n 1)
                     (lambda (result) (k (* n result))))))

(factorial-cps 10 display)  ; => 3628800
(newline)

; CPS 変換したmap
(define (map-cps f lst k)
  (if (null? lst)
      (k '())
      (f (car lst)
         (lambda (head)
           (map-cps f (cdr lst)
                    (lambda (tail)
                      (k (cons head tail))))))))

(map-cps (lambda (x k) (k (* x x)))
         '(1 2 3 4 5)
         display)  ; => (1 4 9 16 25)
(newline)
