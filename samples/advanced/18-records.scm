; サンプル 18: レコード型
; define-record-type の使用

(define-record-type point
  (make-point x y)
  point?
  (x point-x)
  (y point-y))

(define-record-type circle
  (make-circle center radius)
  circle?
  (center circle-center)
  (radius circle-radius))

; ユーティリティ関数
(define (point-distance p1 p2)
  (let ((dx (- (point-x p2) (point-x p1)))
        (dy (- (point-y p2) (point-y p1))))
    (sqrt (+ (* dx dx) (* dy dy)))))

(define (circle-area c)
  (* 3.14159265 (circle-radius c) (circle-radius c)))

(define (point-in-circle? p c)
  (<= (point-distance p (circle-center c))
      (circle-radius c)))

; テスト
(define p1 (make-point 0 0))
(define p2 (make-point 3 4))
(define c (make-circle (make-point 0 0) 5))

(display (point-distance p1 p2))    ; => 5.0
(newline)
(display (circle-area c))            ; => 78.5398...
(newline)
(display (point-in-circle? p2 c))   ; => #t
(newline)
(display (point-in-circle? (make-point 4 4) c))  ; => #f (5.656 > 5)
(newline)
