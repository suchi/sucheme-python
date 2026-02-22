; サンプル 17: オブジェクト指向プログラミング
; クロージャによるOOPの実装

; メッセージパッシングによるOOP
(define (make-account balance)
  (define (withdraw amount)
    (if (>= balance amount)
        (begin (set! balance (- balance amount))
               balance)
        (error "Insufficient funds")))
  (define (deposit amount)
    (set! balance (+ balance amount))
    balance)
  (define (get-balance) balance)
  (lambda (msg . args)
    (cond ((eq? msg 'withdraw) (apply withdraw args))
          ((eq? msg 'deposit) (apply deposit args))
          ((eq? msg 'balance) (get-balance))
          (else (error "Unknown message" msg)))))

(define acc (make-account 100))
(display (acc 'balance))         ; => 100
(newline)
(display (acc 'deposit 50))      ; => 150
(newline)
(display (acc 'withdraw 30))     ; => 120
(newline)

; 継承のシミュレーション
(define (make-savings-account balance interest-rate)
  (let ((base (make-account balance)))
    (lambda (msg . args)
      (if (eq? msg 'accrue-interest)
          (base 'deposit (* (base 'balance) interest-rate))
          (apply base msg args)))))

(define savings (make-savings-account 1000 0.05))
(display (savings 'balance))          ; => 1000
(display (savings 'accrue-interest))  ; => 1050
(newline)
