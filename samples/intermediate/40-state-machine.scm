; サンプル 40: 状態機械
; 有限オートマトン

; 状態機械の定義
; 数字列の検証（整数の簡易バリデーション）
(define (valid-integer? str)
  (define (transition state char)
    (case state
      ((start)
       (cond ((char=? char #\+) 'sign)
             ((char=? char #\-) 'sign)
             ((char-numeric? char) 'digits)
             (else 'error)))
      ((sign)
       (if (char-numeric? char) 'digits 'error))
      ((digits)
       (if (char-numeric? char) 'digits 'error))
      ((error) 'error)))
  (define (accepting? state) (eq? state 'digits))
  (let loop ((chars (string->list str))
             (state 'start))
    (cond ((null? chars) (accepting? state))
          ((eq? state 'error) #f)
          (else (loop (cdr chars)
                      (transition state (car chars)))))))

(display (valid-integer? "123"))   ; => #t
(newline)
(display (valid-integer? "+42"))   ; => #t
(newline)
(display (valid-integer? "-7"))    ; => #t
(newline)
(display (valid-integer? "3.14")) ; => #f
(newline)
(display (valid-integer? ""))      ; => #f
(newline)
