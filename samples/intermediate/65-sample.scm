; サンプル 65: 練習問題 65
; fold / map / filter / recursion の組み合わせ

; サンプル65: 65の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 65 (* 65 5)))
(newline)
