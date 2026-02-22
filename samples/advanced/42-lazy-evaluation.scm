; サンプル 42: 遅延評価
; promise と force を使った遅延計算

; 遅延フィボナッチ（メモ化付き）
(define (memo-fib n)
  (define memo-table (make-vector (+ n 1) #f))
  (define (fib i)
    (or (vector-ref memo-table i)
        (let ((result (if (< i 2)
                          i
                          (+ (fib (- i 1)) (fib (- i 2))))))
          (vector-set! memo-table i result)
          result)))
  (fib n))

(display (memo-fib 50))  ; => 12586269025
(newline)

; 遅延リストでの素数生成
(define-syntax cons-stream
  (syntax-rules ()
    ((cons-stream a b) (cons a (delay b)))))

(define (stream-car s) (car s))
(define (stream-cdr s) (force (cdr s)))

(define (sieve s)
  (cons-stream
    (stream-car s)
    (sieve (stream-filter
             (lambda (x) (not (= (modulo x (stream-car s)) 0)))
             (stream-cdr s)))))

(define (stream-filter pred s)
  (if (pred (stream-car s))
      (cons-stream (stream-car s)
                   (stream-filter pred (stream-cdr s)))
      (stream-filter pred (stream-cdr s))))

(define (integers-from n)
  (cons-stream n (integers-from (+ n 1))))

(define primes (sieve (integers-from 2)))

(define (stream-take n s)
  (if (= n 0) '()
      (cons (stream-car s)
            (stream-take (- n 1) (stream-cdr s)))))

(display (stream-take 10 primes))
; => (2 3 5 7 11 13 17 19 23 29)
(newline)
