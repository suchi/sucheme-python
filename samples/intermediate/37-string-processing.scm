; サンプル 37: 文字列処理
; 実践的な文字列操作

; 単語の分割（簡易版）
(define (split-words str)
  (let loop ((chars (string->list str))
             (current '())
             (words '()))
    (cond ((null? chars)
           (reverse
             (if (null? current)
                 words
                 (cons (list->string (reverse current)) words))))
          ((char=? (car chars) #\space)
           (loop (cdr chars)
                 '()
                 (if (null? current)
                     words
                     (cons (list->string (reverse current)) words))))
          (else
           (loop (cdr chars)
                 (cons (car chars) current)
                 words)))))

(display (split-words "hello world foo bar"))
; => (hello world foo bar)
(newline)

; 文字列の逆順
(define (string-reverse s)
  (list->string (reverse (string->list s))))

(display (string-reverse "hello"))  ; => olleh
(newline)

; パリンドローム判定
(define (palindrome? s)
  (let ((lst (string->list (string-downcase s))))
    (equal? lst (reverse lst))))

(display (palindrome? "racecar"))  ; => #t
(newline)
(display (palindrome? "hello"))    ; => #f
(newline)
