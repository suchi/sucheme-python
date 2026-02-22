; サンプル 04: 条件式
; if, cond, when, unless, case

; if
(display (if (> 5 3) "yes" "no"))  ; => yes
(newline)

; cond
(define (classify n)
  (cond ((< n 0) "negative")
        ((= n 0) "zero")
        ((< n 10) "small")
        (else "large")))

(display (classify -5))   ; => negative
(newline)
(display (classify 0))    ; => zero
(newline)
(display (classify 7))    ; => small
(newline)
(display (classify 100))  ; => large
(newline)

; case
(define (day-name n)
  (case n
    ((1) "Monday")
    ((2) "Tuesday")
    ((3) "Wednesday")
    ((4) "Thursday")
    ((5) "Friday")
    ((6) "Saturday")
    ((7) "Sunday")
    (else "Unknown")))

(display (day-name 3))   ; => Wednesday
(newline)
