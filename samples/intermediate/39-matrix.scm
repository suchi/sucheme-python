; サンプル 39: 行列演算
; ベクタのベクタによる行列

; 行列の作成
(define (make-matrix rows cols init)
  (let ((m (make-vector rows)))
    (do ((i 0 (+ i 1)))
        ((= i rows) m)
      (vector-set! m i (make-vector cols init)))))

(define (matrix-ref m i j)
  (vector-ref (vector-ref m i) j))

(define (matrix-set! m i j val)
  (vector-set! (vector-ref m i) j val))

; 行列積
(define (matrix-multiply a b rows-a cols-a cols-b)
  (let ((result (make-matrix rows-a cols-b 0)))
    (do ((i 0 (+ i 1)))
        ((= i rows-a) result)
      (do ((j 0 (+ j 1)))
          ((= j cols-b))
        (do ((k 0 (+ k 1)))
            ((= k cols-a))
          (matrix-set! result i j
                       (+ (matrix-ref result i j)
                          (* (matrix-ref a i k)
                             (matrix-ref b k j)))))))))

; 2x2 行列テスト
(define a (make-matrix 2 2 0))
(matrix-set! a 0 0 1) (matrix-set! a 0 1 2)
(matrix-set! a 1 0 3) (matrix-set! a 1 1 4)

(define b (make-matrix 2 2 0))
(matrix-set! b 0 0 5) (matrix-set! b 0 1 6)
(matrix-set! b 1 0 7) (matrix-set! b 1 1 8)

(define c (matrix-multiply a b 2 2 2))
(display (matrix-ref c 0 0))  ; => 19 (1*5+2*7)
(newline)
(display (matrix-ref c 1 1))  ; => 50 (3*6+4*8)
(newline)
