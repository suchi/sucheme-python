; サンプル 53: 練習問題 53
; fold / map / filter / recursion の組み合わせ

; サンプル53: 53の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 53 (* 53 5)))
(newline)
