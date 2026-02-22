; サンプル 11: 末尾再帰
; 末尾呼び出し最適化（TCO）の活用

; 末尾再帰の階乗（アキュムレータパターン）
(define (factorial n)
  (let loop ((i n) (acc 1))
    (if (<= i 0)
        acc
        (loop (- i 1) (* acc i)))))

(display (factorial 20))  ; => 2432902008176640000
(newline)

; 末尾再帰のフィボナッチ
(define (fib n)
  (let loop ((i n) (a 0) (b 1))
    (if (= i 0)
        a
        (loop (- i 1) b (+ a b)))))

(display (fib 100))  ; 大きな数も正確に計算
(newline)

; 末尾再帰のリスト処理
(define (my-length lst)
  (let loop ((l lst) (n 0))
    (if (null? l)
        n
        (loop (cdr l) (+ n 1)))))

(display (my-length (iota 1000)))  ; => 1000
(newline)

; 大規模な末尾再帰（スタックオーバーフローしない）
(define (count-down n)
  (if (= n 0)
      'done
      (count-down (- n 1))))

(display (count-down 100000))  ; => done
(newline)
