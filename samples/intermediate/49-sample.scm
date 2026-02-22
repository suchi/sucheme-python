; サンプル 49: 練習問題 49
; fold / map / filter / recursion の組み合わせ

; サンプル49: 49の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 49 (* 49 5)))
(newline)
