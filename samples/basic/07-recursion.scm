; サンプル 07: 再帰
; 基本的な再帰プログラム

; 階乗
(define (factorial n)
  (if (<= n 1)
      1
      (* n (factorial (- n 1)))))

(display (factorial 10))   ; => 3628800
(newline)

; フィボナッチ数
(define (fib n)
  (cond ((= n 0) 0)
        ((= n 1) 1)
        (else (+ (fib (- n 1)) (fib (- n 2))))))

(display (fib 10))  ; => 55
(newline)

; べき乗（再帰）
(define (power base exp)
  (cond ((= exp 0) 1)
        ((even? exp)
         (let ((half (power base (/ exp 2))))
           (* half half)))
        (else (* base (power base (- exp 1))))))

(display (power 2 20))  ; => 1048576
(newline)
