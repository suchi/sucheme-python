# Changelog

このドキュメントはsucheme-pythonの全ての重要な変更を記録します。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に従います。
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に従います。

## [Unreleased]

## [0.1.0] - 2026-02-22

### 追加
- R5RS準拠のSchemeインタプリタ実装
  - レキサー（字句解析器）
  - パーサー（構文解析器）
  - 評価器（トランポリン方式TCO）
  - 組み込み関数 160以上
  - 衛生的マクロ（syntax-rules）
  - 継続（call/cc）
  - 数値タワー（exact/inexact）
  - レコード型（define-record-type）
- インタラクティブREPL（prompt_toolkit / readline対応）
  - Emacsキーバインド
  - 括弧の自動補完
  - 履歴
  - `,help`, `,quit`, `,load`, `,env` コマンド
- CLI（suchemeコマンド）
  - ファイル実行
  - `-e` / `--eval` でインライン評価
  - `--version` / `--no-banner` オプション
  - `--load` でファイルを読み込み後にREPL
  - `-q` / `--quiet` サイレントモード
- Web UI（Flask）
  - ブラウザからSchemeを実行
  - 構文ハイライト
  - ヘルスチェックエンドポイント
- 108以上のサンプルプログラム
- ドキュメント
  - SOW（作業範囲定義書）
  - ADR（アーキテクチャ決定記録）x3
  - オンボーディングガイド
  - R5RS対応状況表
  - チュートリアル
- GitHub Actions CI/CD
  - Python 3.10/3.11/3.12 でのテスト
  - カバレッジレポート
  - タグ → GitHub Release 自動化
- プロジェクト設定
  - `.editorconfig`
  - `.gitignore`
  - `pyproject.toml`

[Unreleased]: https://github.com/suchi/sucheme-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/suchi/sucheme-python/releases/tag/v0.1.0
