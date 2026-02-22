; サンプル 12: クロージャ
; クロージャによる状態の保持

; カウンタ
(define (make-counter)
  (let ((count 0))
    (lambda ()
      (set! count (+ count 1))
      count)))

(define c1 (make-counter))
(define c2 (make-counter))

(display (c1))  ; => 1
(display (c1))  ; => 2
(display (c1))  ; => 3
(display (c2))  ; => 1 (独立したカウンタ)
(newline)

; アキュムレータ
(define (make-accumulator n)
  (lambda (amount)
    (set! n (+ n amount))
    n))

(define acc (make-accumulator 5))
(display (acc 10))  ; => 15
(display (acc 10))  ; => 25
(newline)

; メモ化
(define (memoize f)
  (let ((table '()))
    (lambda args
      (let ((cached (assoc args table)))
        (if cached
            (cdr cached)
            (let ((result (apply f args)))
              (set! table (cons (cons args result) table))
              result))))))

(define fib-memo
  (memoize
    (lambda (n)
      (if (< n 2)
          n
          (+ (fib-memo (- n 1)) (fib-memo (- n 2)))))))

(display (fib-memo 30))  ; => 832040 (高速)
(newline)
