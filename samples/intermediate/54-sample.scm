; サンプル 54: 練習問題 54
; fold / map / filter / recursion の組み合わせ

; サンプル54: 54の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 54 (* 54 5)))
(newline)
