; サンプル 31: 木構造
; 二分木の実装

; 木ノードの作成と操作
(define (make-tree val left right) (list val left right))
(define (tree-val t) (car t))
(define (tree-left t) (cadr t))
(define (tree-right t) (caddr t))
(define (leaf? t) (and (null? (tree-left t)) (null? (tree-right t))))

; 二分探索木への挿入
(define (bst-insert t val)
  (cond ((null? t) (make-tree val '() '()))
        ((< val (tree-val t))
         (make-tree (tree-val t)
                    (bst-insert (tree-left t) val)
                    (tree-right t)))
        ((> val (tree-val t))
         (make-tree (tree-val t)
                    (tree-left t)
                    (bst-insert (tree-right t) val)))
        (else t)))  ; already exists

; 中順走査
(define (inorder t)
  (if (null? t)
      '()
      (append (inorder (tree-left t))
              (list (tree-val t))
              (inorder (tree-right t)))))

; テスト
(define bst
  (fold-left bst-insert '() '(5 3 7 1 4 6 8)))

(display (inorder bst))  ; => (1 3 4 5 6 7 8) (ソート済み)
(newline)
