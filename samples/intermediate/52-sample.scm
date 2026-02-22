; サンプル 52: 練習問題 52
; fold / map / filter / recursion の組み合わせ

; サンプル52: 52の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 52 (* 52 5)))
(newline)
