; サンプル 08: 高階関数
; map, filter, for-each, apply

; map: 各要素に関数を適用
(display (map (lambda (x) (* x x)) '(1 2 3 4 5)))
; => (1 4 9 16 25)
(newline)

; filter: 条件を満たす要素を選択
(display (filter even? '(1 2 3 4 5 6)))
; => (2 4 6)
(newline)

; for-each: 副作用のための反復
(for-each
  (lambda (x) (display x) (display " "))
  '(1 2 3 4 5))
(newline)

; apply: リストを引数として関数適用
(display (apply + '(1 2 3 4 5)))  ; => 15
(newline)
(display (apply max '(3 1 4 1 5 9 2 6)))  ; => 9
(newline)

; 関数を返す関数
(define (make-adder n)
  (lambda (x) (+ x n)))

(define add5 (make-adder 5))
(define add10 (make-adder 10))

(display (add5 3))   ; => 8
(newline)
(display (add10 7))  ; => 17
(newline)
