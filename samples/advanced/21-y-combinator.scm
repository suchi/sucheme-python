; サンプル 21: Y コンビネータ
; 不動点コンビネータによる再帰

; Y コンビネータ（遅延評価版）
(define Y
  (lambda (f)
    ((lambda (x) (f (lambda (v) ((x x) v))))
     (lambda (x) (f (lambda (v) ((x x) v)))))))

; Y コンビネータを使った階乗
(define factorial
  (Y (lambda (self)
       (lambda (n)
         (if (<= n 1) 1 (* n (self (- n 1))))))))

(display (factorial 10))  ; => 3628800
(newline)

; Y コンビネータを使ったフィボナッチ
(define fib
  (Y (lambda (self)
       (lambda (n)
         (if (< n 2)
             n
             (+ (self (- n 1)) (self (- n 2))))))))

(display (fib 10))  ; => 55
(newline)
