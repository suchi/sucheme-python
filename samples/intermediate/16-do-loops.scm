; サンプル 16: do ループ
; do フォームによる命令型ループ

; 基本的なdo
(display
  (do ((i 0 (+ i 1))
       (sum 0 (+ sum i)))
      ((= i 10) sum)))
; => 45
(newline)

; ベクタの初期化
(define v (make-vector 5))
(do ((i 0 (+ i 1)))
    ((= i 5))
  (vector-set! v i (* i i)))

(display v)  ; => #(0 1 4 9 16)
(newline)

; 文字列を逆順に
(define (string-reverse s)
  (let* ((n (string-length s))
         (result (make-string n)))
    (do ((i 0 (+ i 1)))
        ((= i n) result)
      (string-set! result i (string-ref s (- n i 1))))))

(display (string-reverse "hello"))  ; => olleh
(newline)

; リストを走査してカウント
(define (count-matching pred lst)
  (do ((l lst (cdr l))
       (count 0 (if (pred (car l)) (+ count 1) count)))
      ((null? l) count)))

(display (count-matching even? '(1 2 3 4 5 6 7 8)))  ; => 4
(newline)
