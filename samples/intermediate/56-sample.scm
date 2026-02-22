; サンプル 56: 練習問題 56
; fold / map / filter / recursion の組み合わせ

; サンプル56: 56の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 56 (* 56 5)))
(newline)
