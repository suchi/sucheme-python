; サンプル 13: マクロ（syntax-rules）
; 衛生的マクロの定義と使用

; シンプルなマクロ
(define-syntax my-if
  (syntax-rules ()
    ((my-if test then else)
     (cond (test then) (else else)))))

(display (my-if (> 5 3) "yes" "no"))  ; => yes
(newline)

; while ループマクロ
(define-syntax while
  (syntax-rules ()
    ((while test body ...)
     (let loop ()
       (when test
         body ...
         (loop))))))

(define x 0)
(while (< x 5)
  (set! x (+ x 1)))
(display x)  ; => 5
(newline)

; swap! マクロ
(define-syntax swap!
  (syntax-rules ()
    ((swap! a b)
     (let ((tmp a))
       (set! a b)
       (set! b tmp)))))

(define a 1)
(define b 2)
(swap! a b)
(display a)  ; => 2
(display " ")
(display b)  ; => 1
(newline)

; リストパターンマッチ風マクロ
(define-syntax my-list
  (syntax-rules ()
    ((my-list) '())
    ((my-list x ...) (list x ...))))

(display (my-list 1 2 3 4))  ; => (1 2 3 4)
(newline)
