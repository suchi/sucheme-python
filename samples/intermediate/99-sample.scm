; サンプル 99: 実践練習 99

; 99の桁数を計算する
(define (digit-count n)
  (if (= n 0)
      1
      (let loop ((x (abs n)) (count 0))
        (if (= x 0)
            count
            (loop (quotient x 10) (+ count 1))))))

(display (digit-count 99))
(newline)

; 99の因数分解
(define (prime-factors n)
  (let loop ((n n) (d 2) (factors '()))
    (cond ((> (* d d) n)
           (if (> n 1)
               (reverse (cons n factors))
               (reverse factors)))
          ((= (modulo n d) 0)
           (loop (/ n d) d (cons d factors)))
          (else
           (loop n (+ d 1) factors)))))

(display (prime-factors 99))
(newline)
