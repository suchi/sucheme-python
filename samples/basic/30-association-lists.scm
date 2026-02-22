; サンプル 30: 連想リスト（alist）

(define alist (quote ((a . 1) (b . 2) (c . 3))))

(display (assq (quote b) alist))   ; => (b . 2)
(newline)
(display (assv 2 (quote ((1 . "one") (2 . "two") (3 . "three")))))
; => (2 . "two")
(newline)
(display (assoc "b" (quote (("a" . 1) ("b" . 2) ("c" . 3)))))
; => ("b" . 2)
(newline)

; alist の更新
(define (alist-update key val alist)
  (cons (cons key val)
        (filter (lambda (pair) (not (equal? (car pair) key)))
                alist)))

(define updated (alist-update (quote b) 99 alist))
(display (assq (quote b) updated))  ; => (b . 99)
(newline)
