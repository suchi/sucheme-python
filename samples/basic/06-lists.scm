; サンプル 06: リスト操作
; cons, car, cdr, list, 基本的なリスト操作

; リストの作成
(define lst '(1 2 3 4 5))

(display (car lst))    ; => 1
(newline)
(display (cdr lst))    ; => (2 3 4 5)
(newline)
(display (cadr lst))   ; => 2
(newline)

; cons によるリスト構築
(display (cons 0 lst))  ; => (0 1 2 3 4 5)
(newline)

; リスト操作
(display (length lst))           ; => 5
(newline)
(display (reverse lst))          ; => (5 4 3 2 1)
(newline)
(display (append '(a b) '(c d))) ; => (a b c d)
(newline)
(display (list-ref lst 2))       ; => 3
(newline)

; 述語
(display (null? '()))    ; => #t
(newline)
(display (null? lst))    ; => #f
(newline)
(display (pair? lst))    ; => #t
(newline)
(display (list? lst))    ; => #t
(newline)
