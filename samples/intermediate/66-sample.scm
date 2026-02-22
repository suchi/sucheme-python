; サンプル 66: 練習問題 66
; fold / map / filter / recursion の組み合わせ

; サンプル66: 66の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 66 (* 66 5)))
(newline)
