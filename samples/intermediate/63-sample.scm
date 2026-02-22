; サンプル 63: 練習問題 63
; fold / map / filter / recursion の組み合わせ

; サンプル63: 63の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 63 (* 63 5)))
(newline)
