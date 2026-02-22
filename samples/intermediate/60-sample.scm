; サンプル 60: 練習問題 60
; fold / map / filter / recursion の組み合わせ

; サンプル60: 60の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 60 (* 60 5)))
(newline)
