; サンプル 46: 練習問題 46
; fold / map / filter / recursion の組み合わせ

; サンプル46: 46の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 46 (* 46 5)))
(newline)
