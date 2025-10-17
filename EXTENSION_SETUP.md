# 延長管理機能 セットアップガイド

## 概要

延長管理機能が実装されました。この機能は、各店舗の延長時間オプション（例：30分延長、60分延長など）を管理するための機能です。

## 作成されたファイル

### 1. フロントエンド
- **templates/extension.html** - 延長管理ページのHTMLテンプレート
- **static/css/extension.css** - 延長管理ページ専用のスタイルシート
- **static/js/extension.js** - 延長管理ページのJavaScript

### 2. バックエンド
- **database/extension_db.py** - 延長マスタのデータベース操作関数
- **routes/extension.py** - 延長管理のルート定義
- **routes/main.py** - ルート登録（更新済み）

### 3. データベース
- **create_extensions_table.sql** - extensionsテーブル作成用SQLスクリプト

## セットアップ手順

### ステップ1: データベーステーブルの作成

PostgreSQLに接続して、以下のコマンドでテーブルを作成してください：

```bash
psql -U postgres -d pickup_system -f create_extensions_table.sql
```

または、psqlコンソールで直接実行：

```sql
\i create_extensions_table.sql
```

### ステップ2: アプリケーションの再起動

Flaskアプリケーションを再起動してください：

```bash
python app.py
```

### ステップ3: 動作確認

ブラウザで以下のURLにアクセスして動作確認：

```
http://localhost:5001/nagano/extension
```

## 機能説明

### 主な機能

1. **延長登録**
   - 延長名（例：30分延長）
   - 金額（円）
   - バック金額（キャストへの報酬、円）
   - 時間（分単位）
   - 有効/無効の切り替え

2. **延長一覧表示**
   - 並び順の変更（上へ/下へ移動）
   - 有効/無効のステータス表示
   - 編集機能（モーダル）
   - 削除機能

3. **並び順変更**
   - 一覧画面で表示順序を変更可能
   - 上下の矢印ボタンで操作

### バリデーション

- 延長名は必須
- 金額は0以上の整数
- バック金額は金額以下
- 時間は1分以上

## データベーステーブル構造

```sql
CREATE TABLE extensions (
    extension_id SERIAL PRIMARY KEY,           -- 延長ID
    extension_name VARCHAR(255) NOT NULL,      -- 延長名
    extension_minutes INTEGER NOT NULL,        -- 延長時間（分）
    extension_fee INTEGER NOT NULL,            -- 延長料金（円）
    back_amount INTEGER NOT NULL,              -- バック金額（円）
    is_active BOOLEAN DEFAULT TRUE,            -- 有効/無効
    store_id INTEGER NOT NULL,                 -- 店舗ID
    sort_order INTEGER DEFAULT 0,              -- 並び順
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## URL構造

| URL | メソッド | 機能 |
|-----|---------|------|
| `/<store>/extension` | GET | 延長管理ページ表示 |
| `/<store>/extension/register` | POST | 延長登録 |
| `/<store>/extension/<id>/update` | POST | 延長更新 |
| `/<store>/extension/<id>/delete` | GET | 延長削除 |
| `/<store>/extension/<id>/move_up` | GET | 並び順上移動 |
| `/<store>/extension/<id>/move_down` | GET | 並び順下移動 |

## デザイン仕様

- オプション管理ページ（options.html）と同じデザイン
- テーブルヘッダー: `#5a5a5a`
- アクションボタン: `#00BCD4`
- 削除ボタン: `#dc3545`
- ステータスバッジ: 丸型（border-radius: 20px）
  - 有効: 緑背景（`#28a745`）
  - 無効: 赤背景（`#dc3545`）

## 使用例

### 延長データの登録例

1. 延長名: 30分延長
2. 金額: 3000円
3. バック金額: 1500円
4. 時間: 30分
5. 状態: 有効

## トラブルシューティング

### 「店舗が見つかりません」エラー
→ URL の store パラメータが正しいか確認してください（nagano, isesaki, globalwork）

### テーブルが存在しないエラー
→ `create_extensions_table.sql` を実行してください

### スタイルが適用されない
→ ブラウザのキャッシュをクリアしてください

### JavaScript エラー
→ ブラウザの開発者ツールでコンソールを確認してください

## 今後の拡張

将来的に以下の機能追加が可能です：

1. 予約システムとの連携（延長料金の自動計算）
2. 延長履歴の記録
3. 統計情報の表示（人気の延長時間など）
4. CSV エクスポート機能

## サポート

問題が発生した場合は、以下を確認してください：

1. PostgreSQL が起動しているか
2. データベース `pickup_system` が存在するか
3. `extensions` テーブルが作成されているか
4. Flask アプリケーションが正常に起動しているか

## 変更履歴

- 2025-10-17: 初版作成
  - 延長管理機能の実装
  - オプション管理ページのデザインを踏襲
