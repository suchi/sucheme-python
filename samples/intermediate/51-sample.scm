; サンプル 51: 練習問題 51
; fold / map / filter / recursion の組み合わせ

; サンプル51: 51の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 51 (* 51 5)))
(newline)
