; サンプル 34: 動的プログラミング
; ハッシュテーブルを使ったメモ化DP

; 最長共通部分列（LCS）
(define (lcs str1 str2)
  (let* ((n (string-length str1))
         (m (string-length str2))
         (dp (make-vector (* (+ n 1) (+ m 1)) 0)))
    (define (idx i j) (+ (* i (+ m 1)) j))
    (do ((i 1 (+ i 1)))
        ((> i n))
      (do ((j 1 (+ j 1)))
          ((> j m))
        (if (char=? (string-ref str1 (- i 1))
                    (string-ref str2 (- j 1)))
            (vector-set! dp (idx i j)
                        (+ 1 (vector-ref dp (idx (- i 1) (- j 1)))))
            (vector-set! dp (idx i j)
                        (max (vector-ref dp (idx (- i 1) j))
                             (vector-ref dp (idx i (- j 1))))))))
    (vector-ref dp (idx n m))))

(display (lcs "ABCBDAB" "BDCAB"))  ; => 4
(newline)

; コイン問題（最小枚数）
(define (min-coins coins amount)
  (let ((dp (make-vector (+ amount 1) +inf.0)))
    (vector-set! dp 0 0)
    (do ((i 1 (+ i 1)))
        ((> i amount))
      (for-each
        (lambda (coin)
          (when (<= coin i)
            (let ((prev (vector-ref dp (- i coin))))
              (when (< (+ prev 1) (vector-ref dp i))
                (vector-set! dp i (+ prev 1))))))
        coins))
    (let ((result (vector-ref dp amount)))
      (if (= result +inf.0) -1 (exact->inexact result)))))

(display (min-coins '(1 5 10 25) 41))  ; => 4.0 (25+10+5+1)
(newline)
