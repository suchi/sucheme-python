; サンプル 50: 練習問題 50
; fold / map / filter / recursion の組み合わせ

; サンプル50: 50の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 50 (* 50 5)))
(newline)
