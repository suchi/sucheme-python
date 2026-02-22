; サンプル 64: 練習問題 64
; fold / map / filter / recursion の組み合わせ

; サンプル64: 64の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 64 (* 64 5)))
(newline)
