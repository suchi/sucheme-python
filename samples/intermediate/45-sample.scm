; サンプル 45: 練習問題 45
; fold / map / filter / recursion の組み合わせ

; サンプル45: 45の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 45 (* 45 5)))
(newline)
