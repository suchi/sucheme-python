; サンプル 58: 練習問題 58
; fold / map / filter / recursion の組み合わせ

; サンプル58: 58の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 58 (* 58 5)))
(newline)
