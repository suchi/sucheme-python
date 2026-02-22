; サンプル 47: 練習問題 47
; fold / map / filter / recursion の組み合わせ

; サンプル47: 47の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 47 (* 47 5)))
(newline)
