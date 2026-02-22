; サンプル 14: 継続（call/cc）
; call-with-current-continuation の活用

; 基本的なescape
(define (list-product lst)
  (call/cc
    (lambda (exit)
      (let loop ((l lst))
        (cond ((null? l) 1)
              ((= (car l) 0) (exit 0))  ; ショートサーキット
              (else (* (car l) (loop (cdr l)))))))))

(display (list-product '(1 2 3 4 5)))  ; => 120
(newline)
(display (list-product '(1 2 0 4 5)))  ; => 0 (早期終了)
(newline)

; 最初の要素を見つける
(define (find-first pred lst)
  (call/cc
    (lambda (return)
      (for-each (lambda (x)
                  (when (pred x) (return x)))
                lst)
      #f)))

(display (find-first even? '(1 3 5 4 7)))  ; => 4
(newline)
(display (find-first even? '(1 3 5 7)))    ; => #f
(newline)

; バックトラッキング（AMB operator の基礎）
(define *fail* #f)

(define (try-each . thunks)
  (call/cc
    (lambda (k)
      (for-each
        (lambda (thunk)
          (call/cc
            (lambda (fail)
              (set! *fail* fail)
              (k (thunk)))))
        thunks))))

(display "Continuations work!")
(newline)
