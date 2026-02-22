# Schemeチュートリアル

sucheme を使ってSchemeプログラミングを学びましょう。

## 目次

1. [基礎編](#基礎編)
2. [中級編](#中級編)
3. [上級編](#上級編)
4. [実用編](#実用編)

---

## 基礎編

### 1. 式と評価

Schemeはすべてが式（expression）です。

```scheme
; 数値は自己評価
42        ; => 42
3.14      ; => 3.14

; 演算はプレフィックス記法
(+ 1 2)   ; => 3
(* 3 4)   ; => 12
(- 10 3)  ; => 7
(/ 10 2)  ; => 5

; ネストした式
(+ (* 2 3) (* 4 5))  ; => 26
```

### 2. 変数

`define` で変数を定義します。

```scheme
(define x 10)
(define y 20)
(define message "Hello!")

x               ; => 10
(+ x y)         ; => 30
message         ; => "Hello!"

; 変数の更新
(set! x 100)
x               ; => 100
```

### 3. 関数

```scheme
; 関数定義
(define (square n)
  (* n n))

(square 5)    ; => 25
(square 10)   ; => 100

; 複数引数
(define (add a b)
  (+ a b))

(add 3 4)    ; => 7

; ラムダ（無名関数）
(define double (lambda (x) (* x 2)))
(double 7)   ; => 14

; 短縮記法
((lambda (x y) (+ x y)) 3 4)  ; => 7
```

### 4. 条件式

```scheme
; if
(if (> 5 3) "yes" "no")   ; => "yes"
(if (= 1 2) "yes" "no")   ; => "no"

; cond（複数条件）
(define (grade score)
  (cond ((>= score 90) "A")
        ((>= score 80) "B")
        ((>= score 70) "C")
        (else "F")))

(grade 85)  ; => "B"

; case（値の一致）
(define (weekday? n)
  (case n
    ((1 2 3 4 5) "weekday")
    ((6 7) "weekend")
    (else "invalid")))

(weekday? 3)  ; => "weekday"
(weekday? 6)  ; => "weekend"
```

### 5. リスト

```scheme
; リストの作成
(list 1 2 3)     ; => (1 2 3)
'(1 2 3)         ; => (1 2 3) (quote)

; 基本操作
(car '(1 2 3))   ; => 1 (先頭)
(cdr '(1 2 3))   ; => (2 3) (残り)
(cons 0 '(1 2))  ; => (0 1 2) (追加)

; 高次関数
(map (lambda (x) (* x x)) '(1 2 3 4 5))
; => (1 4 9 16 25)

(filter even? '(1 2 3 4 5 6))
; => (2 4 6)

(fold-left + 0 '(1 2 3 4 5))
; => 15
```

### 6. 再帰

```scheme
; 再帰的な長さ計算
(define (my-length lst)
  (if (null? lst)
      0
      (+ 1 (my-length (cdr lst)))))

(my-length '(a b c d))  ; => 4

; 末尾再帰（効率的）
(define (my-length-tail lst)
  (let loop ((l lst) (n 0))
    (if (null? l)
        n
        (loop (cdr l) (+ n 1)))))

(my-length-tail '(a b c d))  ; => 4
```

---

## 中級編

### 7. クロージャと高階関数

```scheme
; 関数を返す関数
(define (make-adder n)
  (lambda (x) (+ x n)))

(define add5 (make-adder 5))
(define add10 (make-adder 10))

(add5 3)   ; => 8
(add10 7)  ; => 17

; 関数合成
(define (compose f g)
  (lambda (x) (f (g x))))

(define inc-then-double (compose (lambda (x) (* x 2))
                                  (lambda (x) (+ x 1))))
(inc-then-double 3)  ; => 8

; 状態を持つクロージャ
(define (make-counter)
  (let ((count 0))
    (lambda ()
      (set! count (+ count 1))
      count)))

(define counter (make-counter))
(counter)  ; => 1
(counter)  ; => 2
(counter)  ; => 3
```

### 8. マクロ

```scheme
; syntax-rules でマクロを定義
(define-syntax my-and
  (syntax-rules ()
    ((my-and) #t)
    ((my-and e) e)
    ((my-and e1 e2 ...)
     (if e1 (my-and e2 ...) #f))))

(my-and 1 2 3)      ; => 3
(my-and 1 #f 3)     ; => #f

; whileループ
(define-syntax while
  (syntax-rules ()
    ((while test body ...)
     (let loop ()
       (when test body ... (loop))))))

(define i 0)
(while (< i 5)
  (display i)
  (set! i (+ i 1)))
; => 01234
(newline)
```

### 9. 継続（call/cc）

```scheme
; 非局所脱出
(define (search pred lst)
  (call/cc
    (lambda (return)
      (for-each (lambda (x)
                  (when (pred x) (return x)))
                lst)
      #f)))

(search even? '(1 3 5 4 7))  ; => 4
(search even? '(1 3 5 7))    ; => #f
```

### 10. 遅延評価

```scheme
; delay/force
(define p (delay (begin
                   (display "evaluated!")
                   (+ 1 2))))

; まだ評価されない
(force p)  ; "evaluated!" => 3
(force p)  ; 再評価されない => 3 (メモ化)

; 無限ストリーム
(define-syntax cons-stream
  (syntax-rules ()
    ((cons-stream a b) (cons a (delay b)))))

(define (stream-car s) (car s))
(define (stream-cdr s) (force (cdr s)))

(define nats
  (let loop ((n 0))
    (cons-stream n (loop (+ n 1)))))

(stream-car nats)           ; => 0
(stream-car (stream-cdr nats))  ; => 1
```

---

## 上級編

### 11. CPS（継続渡しスタイル）

```scheme
; 通常スタイル
(define (factorial n)
  (if (= n 0) 1 (* n (factorial (- n 1)))))

; CPSスタイル
(define (factorial-cps n k)
  (if (= n 0)
      (k 1)
      (factorial-cps (- n 1)
                     (lambda (result) (k (* n result))))))

(factorial-cps 5 display)  ; => 120
(newline)
```

### 12. Y コンビネータ

```scheme
; Y コンビネータ（不動点コンビネータ）
(define Y
  (lambda (f)
    ((lambda (x) (f (lambda (v) ((x x) v))))
     (lambda (x) (f (lambda (v) ((x x) v)))))))

; 再帰なしで定義した階乗
(define factorial
  (Y (lambda (self)
       (lambda (n)
         (if (<= n 1) 1 (* n (self (- n 1))))))))

(factorial 10)  ; => 3628800
```

### 13. レコード型

```scheme
(define-record-type person
  (make-person name age)
  person?
  (name person-name)
  (age person-age set-person-age!))

(define alice (make-person "Alice" 30))

(person-name alice)  ; => "Alice"
(person-age alice)   ; => 30

(set-person-age! alice 31)
(person-age alice)   ; => 31
```

---

## 実用編

### 14. ファイル処理

```scheme
; ファイルへの書き込み
(call-with-output-file "/tmp/test.txt"
  (lambda (port)
    (display "Hello, File!" port)
    (newline port)))

; ファイルの読み込み
(call-with-input-file "/tmp/test.txt"
  (lambda (port)
    (display (read-line port))
    (newline)))
```

### 15. エラーハンドリング

```scheme
; guard による例外処理
(define (safe-car lst)
  (guard (exn (#t #f))
    (car lst)))

(safe-car '(1 2 3))  ; => 1
(safe-car '())       ; => #f

; カスタムエラー
(define (positive-sqrt x)
  (when (< x 0)
    (error "negative argument" x))
  (sqrt x))

(positive-sqrt 4)   ; => 2
; (positive-sqrt -1)  ; => Error: negative argument -1
```

## サンプルファイル一覧

サンプルプログラムは `samples/` ディレクトリに用意しています。

```
samples/
├── basic/          # 基礎サンプル (01-30)
├── intermediate/   # 中級サンプル (31-60)
└── advanced/       # 上級サンプル (61-100)
```

```bash
# サンプルを実行する
uv run sucheme samples/basic/01-hello-world.scm
uv run sucheme samples/intermediate/11-tail-recursion.scm
```
