; サンプル 15: 遅延ストリーム
; delay/force と無限リスト

; ストリームの基本操作
(define-syntax cons-stream
  (syntax-rules ()
    ((cons-stream a b) (cons a (delay b)))))

(define stream-car car)
(define (stream-cdr s) (force (cdr s)))
(define stream-null? null?)
(define the-empty-stream '())

; ストリームの先頭n個を取得
(define (stream-take n s)
  (if (or (= n 0) (stream-null? s))
      '()
      (cons (stream-car s)
            (stream-take (- n 1) (stream-cdr s)))))

; 自然数のストリーム
(define (integers-from n)
  (cons-stream n (integers-from (+ n 1))))

(define nats (integers-from 0))

(display (stream-take 10 nats))
; => (0 1 2 3 4 5 6 7 8 9)
(newline)

; フィルタリングストリーム
(define (stream-filter pred s)
  (cond ((stream-null? s) the-empty-stream)
        ((pred (stream-car s))
         (cons-stream (stream-car s)
                      (stream-filter pred (stream-cdr s))))
        (else (stream-filter pred (stream-cdr s)))))

; 偶数のストリーム
(define evens (stream-filter even? (integers-from 0)))
(display (stream-take 5 evens))
; => (0 2 4 6 8)
(newline)

; フィボナッチのストリーム
(define fibs
  (let loop ((a 0) (b 1))
    (cons-stream a (loop b (+ a b)))))

(display (stream-take 10 fibs))
; => (0 1 1 2 3 5 8 13 21 34)
(newline)
