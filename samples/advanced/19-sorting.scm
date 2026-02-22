; サンプル 19: ソートアルゴリズム

; クイックソート
(define (quicksort lst)
  (if (or (null? lst) (null? (cdr lst)))
      lst
      (let ((pivot (car lst))
            (rest (cdr lst)))
        (let ((less (filter (lambda (x) (< x pivot)) rest))
              (greater (filter (lambda (x) (>= x pivot)) rest)))
          (append (quicksort less)
                  (list pivot)
                  (quicksort greater))))))

; マージソート
(define (mergesort lst)
  (define (merge l1 l2)
    (cond ((null? l1) l2)
          ((null? l2) l1)
          ((< (car l1) (car l2))
           (cons (car l1) (merge (cdr l1) l2)))
          (else
           (cons (car l2) (merge l1 (cdr l2))))))
  (define (split lst)
    (if (or (null? lst) (null? (cdr lst)))
        (values lst '())
        (call-with-values
          (lambda () (split (cddr lst)))
          (lambda (a b)
            (values (cons (car lst) a)
                    (cons (cadr lst) b))))))
  (if (or (null? lst) (null? (cdr lst)))
      lst
      (call-with-values
        (lambda () (split lst))
        (lambda (a b)
          (merge (mergesort a) (mergesort b))))))

(define test '(3 1 4 1 5 9 2 6 5 3 5))

(display (quicksort test))   ; => (1 1 2 3 3 4 5 5 5 6 9)
(newline)
(display (mergesort test))   ; => (1 1 2 3 3 4 5 5 5 6 9)
(newline)
