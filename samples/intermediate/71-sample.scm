; サンプル 71: 練習問題 71
; fold / map / filter / recursion の組み合わせ

; サンプル71: 71の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 71 (* 71 5)))
(newline)
