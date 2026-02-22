; サンプル 73: 練習問題 73
; fold / map / filter / recursion の組み合わせ

; サンプル73: 73の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 73 (* 73 5)))
(newline)
