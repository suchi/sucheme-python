; サンプル 70: 練習問題 70
; fold / map / filter / recursion の組み合わせ

; サンプル70: 70の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 70 (* 70 5)))
(newline)
