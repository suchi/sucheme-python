; サンプル 35: ジェネレータ
; クロージャを使った状態を持つジェネレータ

; 範囲ジェネレータ
(define (make-range-generator start end . args)
  (let ((step (if (null? args) 1 (car args)))
        (current start))
    (lambda ()
      (if (>= current end)
          'done
          (let ((val current))
            (set! current (+ current step))
            val)))))

(define gen (make-range-generator 0 5))
(let loop ((val (gen)))
  (unless (eq? val 'done)
    (display val) (display " ")
    (loop (gen))))
(newline)  ; => 0 1 2 3 4

; フィボナッチジェネレータ
(define (make-fib-generator)
  (let ((a 0) (b 1))
    (lambda ()
      (let ((val a))
        (set! a b)
        (set! b (+ val b))
        val))))

(define fib-gen (make-fib-generator))
(do ((i 0 (+ i 1)))
    ((= i 10))
  (display (fib-gen)) (display " "))
(newline)  ; => 0 1 1 2 3 5 8 13 21 34
