; サンプル 10: let, let*, letrec, named let

; let: 並列束縛
(let ((x 1)
      (y 2))
  (display (+ x y)))  ; => 3
(newline)

; let*: 順次束縛（前の束縛を参照可能）
(let* ((x 1)
       (y (* x 2))
       (z (+ x y)))
  (display z))  ; => 3
(newline)

; letrec: 相互再帰
(letrec ((even? (lambda (n) (if (= n 0) #t (odd? (- n 1)))))
         (odd?  (lambda (n) (if (= n 0) #f (even? (- n 1))))))
  (display (even? 10))  ; => #t
  (newline)
  (display (odd? 7)))   ; => #t
(newline)

; named let: ループとして使う
(define (sum-to n)
  (let loop ((i 0) (acc 0))
    (if (> i n)
        acc
        (loop (+ i 1) (+ acc i)))))

(display (sum-to 100))  ; => 5050
(newline)
