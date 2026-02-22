; サンプル 55: 練習問題 55
; fold / map / filter / recursion の組み合わせ

; サンプル55: 55の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 55 (* 55 5)))
(newline)
