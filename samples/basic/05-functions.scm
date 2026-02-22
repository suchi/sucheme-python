; サンプル 05: 関数定義
; define, lambda の使い方

; 関数定義 (define shorthand)
(define (square x)
  (* x x))

(define (cube x)
  (* x x x))

(define (circle-area r)
  (* 3.14159265 r r))

(display (square 5))       ; => 25
(newline)
(display (cube 3))         ; => 27
(newline)
(display (circle-area 5))  ; => 78.5398...
(newline)

; ラムダ式
(define double (lambda (x) (* x 2)))
(display (double 7))       ; => 14
(newline)

; 複数の引数
(define (sum-of-squares a b)
  (+ (square a) (square b)))

(display (sum-of-squares 3 4))  ; => 25
(newline)
