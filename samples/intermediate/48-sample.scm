; サンプル 48: 練習問題 48
; fold / map / filter / recursion の組み合わせ

; サンプル48: 48の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 48 (* 48 5)))
(newline)
