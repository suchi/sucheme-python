; サンプル 09: 文字列操作

(define s "Hello, World!")

(display (string-length s))          ; => 13
(newline)
(display (substring s 0 5))          ; => Hello
(newline)
(display (string-append "foo" "bar")) ; => foobar
(newline)
(display (string-upcase "hello"))    ; => HELLO
(newline)
(display (string-downcase "WORLD"))  ; => world
(newline)
(display (string->list "abc"))       ; => (a b c)
(newline)
(display (list->string '(#\h #\i)))  ; => hi
(newline)
(display (string->number "42"))      ; => 42
(newline)
(display (number->string 255 16))    ; => ff
(newline)
