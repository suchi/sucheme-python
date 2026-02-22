; サンプル 57: 練習問題 57
; fold / map / filter / recursion の組み合わせ

; サンプル57: 57の倍数リストを生成
(define (multiples-of n limit)
  (filter (lambda (x) (= (modulo x n) 0))
          (iota limit 1)))

(display (multiples-of 57 (* 57 5)))
(newline)
