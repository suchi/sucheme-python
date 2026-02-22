; サンプル 24: 文字操作
(display #\a)                        ; => a
(newline)
(display (char->integer #\A))        ; => 65
(newline)
(display (integer->char 97))         ; => a
(newline)
(display (char-alphabetic? #\a))     ; => #t
(newline)
(display (char-numeric? #\5))        ; => #t
(newline)
(display (char-whitespace? #\space)) ; => #t
(newline)
(display (char-upcase #\a))          ; => A
(newline)
(display (char-downcase #\Z))        ; => z
(newline)
(display (char<? #\a #\b))           ; => #t
(newline)
