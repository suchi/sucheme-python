; サンプル 61: 練習問題 61
; fold / map / filter / recursion の組み合わせ

; サンプル61: 61の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 61 (* 61 5)))
(newline)
