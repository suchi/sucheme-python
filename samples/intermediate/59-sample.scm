; サンプル 59: 練習問題 59
; fold / map / filter / recursion の組み合わせ

; サンプル59: 59の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 59 (* 59 5)))
(newline)
