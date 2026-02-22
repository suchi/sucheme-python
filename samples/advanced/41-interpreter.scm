; サンプル 41: Schemeで実装するミニインタプリタ
; Scheme in Scheme

(define (my-eval expr env)
  (cond ((number? expr) expr)
        ((string? expr) expr)
        ((boolean? expr) expr)
        ((symbol? expr) (lookup expr env))
        ((pair? expr)
         (case (car expr)
           ((quote) (cadr expr))
           ((if) (if (my-eval (cadr expr) env)
                     (my-eval (caddr expr) env)
                     (if (null? (cdddr expr))
                         #f
                         (my-eval (cadddr expr) env))))
           ((lambda) (list 'closure (cadr expr) (cddr expr) env))
           ((define)
            (let ((val (my-eval (caddr expr) env)))
              (set-env! env (cadr expr) val)
              val))
           (else
            (let ((proc (my-eval (car expr) env))
                  (args (map (lambda (a) (my-eval a env)) (cdr expr))))
              (my-apply proc args)))))
        (else (error "Unknown expression" expr))))

(define (my-apply proc args)
  (if (procedure? proc)
      (apply proc args)
      (let ((params (cadr proc))
            (body (caddr proc))
            (env (cadddr proc)))
        (let ((new-env (extend-env env params args)))
          (let loop ((exprs body))
            (if (null? (cdr exprs))
                (my-eval (car exprs) new-env)
                (begin (my-eval (car exprs) new-env)
                       (loop (cdr exprs)))))))))

(define (lookup sym env)
  (cond ((null? env) (error "Unbound variable" sym))
        ((eq? (caar env) sym) (cdar env))
        (else (lookup sym (cdr env)))))

(define (set-env! env sym val)
  (set-car! env (cons sym val)))

(define (extend-env env params args)
  (append (map cons params args) env))

; テスト
(define base-env
  (list (cons '+ +)
        (cons '- -)
        (cons '* *)
        (cons '= =)
        (cons '< <)))

(display (my-eval '(+ 1 2) base-env))  ; => 3
(newline)
(display (my-eval '(if (< 3 5) 'yes 'no) base-env))  ; => yes
(newline)
