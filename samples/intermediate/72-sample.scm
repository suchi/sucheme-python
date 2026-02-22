; サンプル 72: 練習問題 72
; fold / map / filter / recursion の組み合わせ

; サンプル72: 72の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 72 (* 72 5)))
(newline)
