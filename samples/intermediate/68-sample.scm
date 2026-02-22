; サンプル 68: 練習問題 68
; fold / map / filter / recursion の組み合わせ

; サンプル68: 68の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 68 (* 68 5)))
(newline)
