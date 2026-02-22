; サンプル 20: チャーチ数
; ラムダ計算によるチャーチ数のエンコーディング

; チャーチ数の定義
(define zero (lambda (f) (lambda (x) x)))
(define (succ n) (lambda (f) (lambda (x) (f ((n f) x)))))

; 基本数値
(define one   (succ zero))
(define two   (succ one))
(define three (succ two))
(define four  (succ three))
(define five  (succ four))

; チャーチ数 -> 整数の変換
(define (church->int n)
  ((n (lambda (x) (+ x 1))) 0))

; 演算
(define (church-add m n)
  (lambda (f) (lambda (x) ((m f) ((n f) x)))))

(define (church-mul m n)
  (lambda (f) (n (m f))))

; テスト
(display (church->int zero))   ; => 0
(newline)
(display (church->int three))  ; => 3
(newline)
(display (church->int (church-add two three)))  ; => 5
(newline)
(display (church->int (church-mul two three)))  ; => 6
(newline)
