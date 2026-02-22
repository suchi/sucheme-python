; サンプル 74: 練習問題 74
; fold / map / filter / recursion の組み合わせ

; サンプル74: 74の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 74 (* 74 5)))
(newline)
