; サンプル 75: 練習問題 75
; fold / map / filter / recursion の組み合わせ

; サンプル75: 75の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 75 (* 75 5)))
(newline)
