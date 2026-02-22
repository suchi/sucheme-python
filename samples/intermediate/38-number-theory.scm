; サンプル 38: 数論
; 素数、GCD、LCM

; 素数判定
(define (prime? n)
  (if (< n 2)
      #f
      (let loop ((i 2))
        (cond ((> (* i i) n) #t)
              ((= (modulo n i) 0) #f)
              (else (loop (+ i 1)))))))

; エラトステネスの篩
(define (sieve limit)
  (let ((is-prime (make-vector (+ limit 1) #t)))
    (vector-set! is-prime 0 #f)
    (vector-set! is-prime 1 #f)
    (do ((i 2 (+ i 1)))
        ((> (* i i) limit))
      (when (vector-ref is-prime i)
        (do ((j (* i i) (+ j i)))
            ((> j limit))
          (vector-set! is-prime j #f))))
    (filter (lambda (n) (vector-ref is-prime n))
            (iota (- limit 1) 2))))

(display (sieve 50))
; => (2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)
(newline)

; 拡張ユークリッドアルゴリズム
(define (extended-gcd a b)
  (if (= b 0)
      (values a 1 0)
      (call-with-values
        (lambda () (extended-gcd b (modulo a b)))
        (lambda (g x y)
          (values g y (- x (* (quotient a b) y)))))))

(call-with-values
  (lambda () (extended-gcd 35 15))
  (lambda (g x y)
    (display "gcd=") (display g)
    (display " x=") (display x)
    (display " y=") (display y)
    (newline)))
