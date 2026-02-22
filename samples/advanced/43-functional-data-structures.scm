; サンプル 43: 関数的データ構造
; 不変データ構造

; 関数的スタック
(define (make-stack) '())
(define (stack-push stack val) (cons val stack))
(define (stack-pop stack) (values (car stack) (cdr stack)))
(define (stack-empty? stack) (null? stack))

(let* ((s (make-stack))
       (s (stack-push s 1))
       (s (stack-push s 2))
       (s (stack-push s 3)))
  (call-with-values
    (lambda () (stack-pop s))
    (lambda (top rest)
      (display top)   ; => 3
      (newline)
      (display rest)  ; => (2 1)
      (newline))))

; 関数的キュー（2つのリストによる実装）
(define (make-queue) (cons '() '()))
(define (queue-empty? q) (and (null? (car q)) (null? (cdr q))))
(define (enqueue q val) (cons (car q) (cons val (cdr q))))
(define (dequeue q)
  (if (null? (car q))
      (let ((front (reverse (cdr q))))
        (values (car front) (cons (cdr front) '())))
      (values (caar q) (cons (cdar q) (cdr q)))))

(let* ((q (make-queue))
       (q (enqueue q 1))
       (q (enqueue q 2))
       (q (enqueue q 3)))
  (call-with-values
    (lambda () (dequeue q))
    (lambda (val rest)
      (display val)  ; => 1
      (newline))))
