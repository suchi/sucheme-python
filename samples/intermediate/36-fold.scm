; サンプル 36: fold（畳み込み）
; fold-left, fold-right の使い方

; fold-left（左畳み込み）
(display (fold-left + 0 '(1 2 3 4 5)))  ; => 15
(newline)
(display (fold-left * 1 '(1 2 3 4 5)))  ; => 120
(newline)
(display (fold-left (lambda (acc x) (cons x acc)) '() '(1 2 3)))
; => (3 2 1) (reverse)
(newline)

; fold-right（右畳み込み）
(display (fold-right cons '() '(1 2 3)))  ; => (1 2 3) (copy)
(newline)
(display (fold-right + 0 '(1 2 3 4 5)))   ; => 15
(newline)

; reduce
(display (reduce + 0 '(1 2 3 4 5)))  ; => 15
(newline)

; fold を使った flatten
(define (flatten lst)
  (fold-right
    (lambda (x acc)
      (if (pair? x)
          (append (flatten x) acc)
          (cons x acc)))
    '()
    lst))

(display (flatten '(1 (2 3) (4 (5 6)))))  ; => (1 2 3 4 5 6)
(newline)
