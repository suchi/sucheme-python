# ADR-0003: アーキテクチャ設計

**ステータス**: 承認済み
**日付**: 2026-02-22
**担当**: suchi

## コンテキスト

R5RS準拠Schemeインタプリタの全体アーキテクチャを設計する。

## 決定

**レキサー → パーサー → 評価器** のパイプライン構造で実装する。
ASTは中間表現を持たず、S式をそのまま評価する（tree-walking interpreter）。

## アーキテクチャ全体図

```mermaid
graph TB
    subgraph 入力
        SRC[Scheme ソースコード]
        FILE[.scm ファイル]
        REPL_IN[REPL入力]
        WEB_IN[Web UI入力]
    end

    subgraph コア
        LEX["lexer.py<br/>字句解析<br/>Token列を生成"]
        PAR["parser.py<br/>構文解析<br/>S式ツリーを生成"]
        EVL["evaluator.py<br/>評価器<br/>TCO + macro展開"]
        PRI["primitives.py<br/>組み込み関数<br/>200+ procedures"]
        ENV["environment.py<br/>環境チェーン<br/>レキシカルスコープ"]
        TYP["types.py<br/>型システム<br/>R5RS型階層"]
        INT["interpreter.py<br/>統合インタプリタ"]
    end

    subgraph インターフェース
        CLI_OUT["cli.py<br/>コマンドライン"]
        REPL_OUT["repl.py<br/>インタラクティブREPL"]
        WEB_OUT["web/app.py<br/>Flask Web UI"]
    end

    SRC & FILE & REPL_IN & WEB_IN --> LEX
    LEX --> PAR
    PAR --> EVL
    EVL <--> ENV
    EVL <--> PRI
    TYP --> LEX & PAR & EVL & PRI
    PRI & EVL --> INT
    INT --> CLI_OUT & REPL_OUT & WEB_OUT
```

## 型システム設計

```mermaid
classDiagram
    class SchemeObject {
        <<abstract>>
    }
    class Symbol { name: str }
    class Boolean { value: bool }
    class Pair { car: Any, cdr: Any }
    class Vector { data: list }
    class Char { char: str }
    class SchemeString { value: str }
    class Procedure { <<abstract>> }
    class LambdaProcedure { params, body, env, name }
    class PrimitiveProcedure { _fn, name }
    class ContinuationProcedure { _fn }
    class MacroProcedure { transformer, env }
    class _Nil { <<singleton>> }
    class _Void { <<singleton>> }
    class Port { _file, mode }

    SchemeObject <|-- Symbol
    SchemeObject <|-- Boolean
    SchemeObject <|-- Pair
    SchemeObject <|-- Vector
    SchemeObject <|-- Char
    SchemeObject <|-- SchemeString
    SchemeObject <|-- Procedure
    Procedure <|-- LambdaProcedure
    Procedure <|-- PrimitiveProcedure
    Procedure <|-- ContinuationProcedure
    SchemeObject <|-- MacroProcedure
    SchemeObject <|-- _Nil
    SchemeObject <|-- _Void
    SchemeObject <|-- Port
```

## 数値タワー

```mermaid
graph TB
    N[number] --> C[complex]
    C --> R[real]
    R --> Q[rational]
    Q --> Z[integer]
    N --> E[exact]
    N --> I[inexact]
    Z & Q --> E
    R & C --> I
    style E fill:#e8f5e9
    style I fill:#e3f2fd
```

| Schemeの型 | Pythonでの表現 |
|-----------|---------------|
| 整数（exact） | `int` |
| 有理数（exact） | `fractions.Fraction` |
| 実数（inexact） | `float` |
| 複素数 | `complex` |

## 環境チェーン（レキシカルスコープ）

```mermaid
graph LR
    G[グローバル環境<br/>+, -, car, cdr...] --> L1[ローカル環境1<br/>x=1, y=2]
    L1 --> L2[ローカル環境2<br/>z=3]
    L2 -. 変数参照時: 上位を探索 .-> L1
    L1 -. 見つからない場合 .-> G
```

## マクロ展開

```mermaid
sequenceDiagram
    participant E as 評価器
    participant M as マクロプロセッサ
    participant T as syntax-rules変換器
    
    E->>M: マクロ適用を検出
    M->>T: パターンマッチング
    T->>T: テンプレート展開
    T->>E: 展開されたS式
    E->>E: 展開結果を再評価
```

## 影響

- AST中間表現を持たないため、実装はシンプルだが最適化の余地が少ない
- マクロ展開はインライン（評価時に展開）で行う
- 継続（call/cc）はContinuationException例外でスタックを巻き戻す方式
