; サンプル 44: 練習問題 44
; fold / map / filter / recursion の組み合わせ

; サンプル44: 44の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 44 (* 44 5)))
(newline)
