# 📘 Autocoll プロジェクト開発ガイド

このドキュメントは、Autocoll（マルチ店舗管理システム）の開発時に**必ず守るべきルール**をまとめたものです。

---

## 📑 目次

1. [🚨 絶対に守るべきルール](#-絶対に守るべきルール必須)
2. [📝 コーディング規約](#-コーディング規約)
3. [✅ 開発前チェックリスト](#-開発前チェックリスト)
4. [📚 クイックリファレンス](#-クイックリファレンス)
5. [🚫 よくある間違い集](#-よくある間違い集)

---

## 🚨 絶対に守るべきルール（必須）

### 1️⃣ データベース接続

#### ✅ 必ず使用するもの

**psycopg3** (`psycopg`) を使用

```python
import psycopg
from psycopg.rows import dict_row
from database.connection import get_db
```

#### ✅ 接続方法

**パターン1: SQLiteライクな書き方（推奨）**
```python
from database.connection import get_db

db = get_db()
cursor = db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cursor.fetchone()  # 自動的に辞書形式
db.close()
```

**パターン2: 標準的なpsycopg3の書き方**
```python
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)
cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cur.fetchone()
cur.close()
conn.close()
```

#### 🚨 重要な注意点

1. **プレースホルダーは `%s`**（`?` ではない）
2. **`get_db()` のcursor()は自動的にdict_row**（二重指定しない）
3. **psycopg2は使用禁止**

```python
# ❌ 間違い
cursor = db.cursor(row_factory=dict_row)  # 二重指定！

# ✅ 正しい
cursor = db.cursor()  # 自動的にdict_row
```

---

### 2️⃣ ルート定義

#### ✅ 必ず使用する形式

**`register_XXX_routes(app)` 関数形式**

```python
# routes/example.py

from flask import request, jsonify, session, redirect, render_template
from functools import wraps

def admin_required(f):
    """管理者権限チェック"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


def register_example_routes(app):
    """
    ✅ すべてのエンドポイントをこの関数内に定義
    """
    
    @app.route('/<store>/example')
    @admin_required
    def example_page(store):
        return render_template('example.html', store=store)
    
    @app.route('/<store>/example/api', methods=['POST'])
    @admin_required
    def example_api(store):
        data = request.get_json()
        return jsonify({'success': True})
```

#### 🚨 禁止事項

```python
# ❌ 関数の外にエンドポイントを書くのは禁止！
@app.route('/error')  # appが定義されていない
def error_route():
    return 'NG'
```

---

### 3️⃣ 店舗データ分離（最重要）

#### ✅ 基本原則

**すべてのデータは店舗ごとに分けて管理する**

#### テーブル設計

```sql
-- ✅ 正しい
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,        -- 必須！
    customer_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_store_id ON customers(store_id);

-- ❌ 間違い
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),       -- store_idがない！
    created_at TIMESTAMP
);
```

#### クエリの書き方

```python
# ✅ 正しい（store_idでフィルタ）
cursor.execute("""
    SELECT * FROM customers 
    WHERE store_id = %s AND customer_name LIKE %s
""", (store_id, f"%{search_term}%"))

# ❌ 間違い（store_idでフィルタしていない）
cursor.execute("""
    SELECT * FROM customers 
    WHERE customer_name LIKE %s
""", (f"%{search_term}%",))
```

#### 🚨 例外：現在のstore_id運用

**将来の拡張用として引数にあるが、現在は使用していない**

```python
def get_card_fee_rate(store_id=None):
    """
    Args:
        store_id: 将来の拡張用（現在未使用）
    """
    # store_idでフィルタせず、全店舗共通の設定を取得
    cursor.execute("""
        SELECT setting_value FROM store_settings
        WHERE setting_key = 'card_fee_rate'
        LIMIT 1
    """)
```

将来的には `WHERE ... AND store_id = %s` を追加する予定。

---

### 4️⃣ HTMLテンプレート構造

#### ✅ 必須の構造

**すべてのHTMLテンプレートは以下の順序を守る**

```html
{% extends "base.html" %}

<!-- 1. extra_head: CSS読み込み -->
{% block extra_head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/xxx.css') }}">
{% endblock %}

<!-- 2. title: ページタイトル -->
{% block title %}ページタイトル{% endblock %}

<!-- 3. content: メインコンテンツ（必須！） -->
{% block content %}
<div class="container">
  <!-- ここにページの内容を書く -->
</div>
{% endblock %}

<!-- 4. JavaScript読み込み（base.htmlのブロック名を確認！） -->
{% block extra_scripts %}
<script src="{{ url_for('static', filename='js/xxx.js') }}"></script>
{% endblock %}
```

#### 🚨 重要な注意点

1. **`{% block content %}` は必須**（これがないとコンテンツが表示されない）
2. **JavaScriptのブロック名はbase.htmlと一致させる**
   - base.htmlが `{% block extra_scripts %}` なら `extra_scripts` を使用
   - base.htmlが `{% block extra_js %}` なら `extra_js` を使用
3. **ブロック名が間違っていてもエラーが出ない**ため、動作確認必須

---

## 📝 コーディング規約

### Python

#### インポート順序

```python
# 1. 標準ライブラリ
from datetime import datetime
import os

# 2. サードパーティ
from flask import request, jsonify, render_template
import psycopg
from psycopg.rows import dict_row

# 3. プロジェクト内モジュール
from database.connection import get_db
from routes.auth import admin_required
```

#### エラーハンドリング

```python
try:
    conn = get_db()
    # 処理
    
except Exception as e:
    print(f"Error in function_name: {e}")
    import traceback
    traceback.print_exc()
    
    return jsonify({
        'success': False,
        'message': '処理に失敗しました'
    }), 500
    
finally:
    if conn:
        conn.close()
```

#### デバッグコード

```python
# ✅ 開発中
print(f"Debug: {data}")

# ✅ 本番前に完全削除
# print(f"Debug: {data}")  ← コメントアウトでも残さない
```

**本番環境にデバッグコードは絶対に残さない**

---

### JavaScript

#### デバッグログ

```javascript
// ✅ 開発中のみ
console.log('🔍 データ:', data);

// ✅ 本番前に完全削除
```

---

### CSS

#### ✅ 必ずクラス名を使用

```css
/* ✅ 正しい */
.customer-input {
    padding: 8px;
    border-radius: 0;  /* 角丸なし */
}

.customer-title {
    font-size: 18px;
    color: #333;
}

/* ❌ 間違い（タグ直接指定は禁止） */
input {
    padding: 8px;
}

body {
    font-size: 14px;  /* 全体に影響するため禁止 */
}

h1 {
    color: #333;  /* 全体に影響するため禁止 */
}
```

#### ✅ 個別CSSを使用（最重要）

**共通CSS（common.css）は使わない**

```
static/
├── css/
│   ├── base.css              👈 ヘッダーとサイドバー専用
│   ├── gantt_chart.css       👈 ガントチャート専用
│   ├── customer.css          👈 顧客管理専用
│   └── ...                   👈 各ページごとに作成
```

**理由：**
- ❌ 共通CSS：クラス名が被る、スタイルが競合する、管理が複雑
- ✅ 個別CSS：探しやすい、修正の影響範囲が明確、メンテナンスしやすい

#### ルール

1. **クラス名にページ名をつける**
```css
/* ✅ 正しい */
.customer-list { }
.customer-item { }

/* ❌ 間違い */
.list { }      /* 他のページと被る */
```

2. **必ずクラス名でスコープを限定**
3. `body`, `h1`, `p`, `div` などのタグ直接指定は禁止
4. 角丸は使わない（`border-radius: 0;`）
5. 配色統一：
   - ヘッダー・アクセント：`#00BCD4`
   - サイドバー：`#e9ecef`
   - テキスト：`#333`

詳細は「CSS管理方針.md」を参照。

---

## ✅ 開発前チェックリスト

新機能を作る前に必ず確認：

### データベース
- [ ] psycopg3 (`psycopg`) を使用しているか
- [ ] `get_db()` または `get_connection()` で接続取得しているか
- [ ] プレースホルダーは `%s` を使用しているか
- [ ] `get_db().cursor()` に `row_factory=dict_row` を指定していないか

### 店舗データ分離
- [ ] テーブルに `store_id` カラムがあるか
- [ ] `store_id` にインデックスを作成したか
- [ ] SELECTクエリで `WHERE store_id = %s` をつけているか
- [ ] INSERTで `store_id` を指定しているか

### ルート定義
- [ ] `register_XXX_routes(app)` 関数形式で定義しているか
- [ ] エンドポイントは全て関数内に書いているか
- [ ] `app.py` で `register_XXX_routes(app)` を呼び出したか

### HTMLテンプレート
- [ ] `{% extends "base.html" %}` がファイルの先頭にあるか
- [ ] `{% block content %}` と `{% endblock %}` で囲まれているか
- [ ] CSSは `{% block extra_head %}` に配置しているか
- [ ] JavaScriptのブロック名がbase.htmlと一致しているか
- [ ] すべてのブロックが正しく閉じられているか

### コーディング
- [ ] デバッグコードを削除したか
- [ ] CSSにクラス名を付けているか
- [ ] CSSでタグ直接指定をしていないか
- [ ] エラーハンドリングを実装したか

---

## 📚 クイックリファレンス

### データベース接続テンプレート

```python
from database.connection import get_db

def get_customers(store_id, search_term=None):
    """顧客一覧を取得"""
    db = get_db()
    
    try:
        query = """
            SELECT * FROM customers 
            WHERE store_id = %s
        """
        params = [store_id]
        
        if search_term:
            query += " AND customer_name LIKE %s"
            params.append(f"%{search_term}%")
        
        cursor = db.execute(query, params)
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error in get_customers: {e}")
        return []
    finally:
        db.close()
```

### ルート定義テンプレート

```python
from flask import render_template, request, jsonify, session, redirect
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


def register_feature_routes(app):
    
    @app.route('/<store>/feature')
    @admin_required
    def feature_page(store):
        return render_template('feature.html', store=store)
    
    @app.route('/<store>/feature/api', methods=['POST'])
    @admin_required
    def feature_api(store):
        try:
            data = request.get_json()
            # 処理
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'success': False}), 500
```

### HTMLテンプレートテンプレート

```html
{% extends "base.html" %}

{% block extra_head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/feature.css') }}">
{% endblock %}

{% block title %}機能名{% endblock %}

{% block content %}
<div class="feature-container">
  <h1 class="feature-title">機能名</h1>
  
  <!-- コンテンツ -->
  
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{{ url_for('static', filename='js/feature.js') }}"></script>
{% endblock %}
```

### 新規テーブル作成テンプレート

```sql
-- テーブル作成
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_table_name_store_id ON table_name(store_id);

-- コメント
COMMENT ON TABLE table_name IS 'テーブルの説明';
COMMENT ON COLUMN table_name.id IS 'ID';
COMMENT ON COLUMN table_name.store_id IS '店舗ID';
COMMENT ON COLUMN table_name.name IS '名前';
```

---

## 🚫 よくある間違い集

### ❌ 間違い1: psycopg2を使おうとする

```python
# ❌ 間違い
import psycopg2

# ✅ 正しい
import psycopg
```

**原因：** 古いプロジェクトから移植するときに起こりやすい  
**解決：** psycopg3を使用する

---

### ❌ 間違い2: 二重にdict_rowを指定

```python
# ❌ 間違い
db = get_db()
cursor = db.cursor(row_factory=dict_row)  # エラー！

# ✅ 正しい
db = get_db()
cursor = db.cursor()  # 自動的にdict_row
```

**原因：** `get_db()` は既にdict_rowを設定済み  
**解決：** `cursor()` をそのまま呼び出す

---

### ❌ 間違い3: 関数の外にエンドポイント定義

```python
# ❌ 間違い
def register_routes(app):
    @app.route('/test')
    def test():
        return 'OK'

@app.route('/error')  # appが定義されていない！
def error_route():
    return 'NG'


# ✅ 正しい
def register_routes(app):
    @app.route('/test')
    def test():
        return 'OK'
    
    @app.route('/success')  # 関数の中に書く
    def success_route():
        return 'OK'
```

**原因：** `app` 変数が関数の外では存在しない  
**解決：** すべてのルートを `register_XXX_routes(app)` 内に定義

---

### ❌ 間違い4: store_idでフィルタしない

```python
# ❌ 間違い
cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))

# ✅ 正しい
cursor.execute("""
    SELECT * FROM customers 
    WHERE store_id = %s AND name = %s
""", (store_id, name))
```

**原因：** 店舗データ分離を忘れている  
**解決：** すべてのクエリに `WHERE store_id = %s` を追加

---

### ❌ 間違い5: CSSでタグ直接指定

```css
/* ❌ 間違い */
body {
    font-size: 14px;
}

input {
    padding: 8px;
}

/* ✅ 正しい */
.my-container {
    font-size: 14px;
}

.my-input {
    padding: 8px;
}
```

**原因：** タグ指定は全ページに影響する  
**解決：** 必ずクラス名を使用してスコープを限定

---

### ❌ 間違い6: デバッグコードを残す

```python
# ❌ 間違い（本番環境にデバッグコードが残る）
print(f"Debug: {data}")
console.log('debug:', data);

# ✅ 正しい（本番前に完全削除）
```

**原因：** 本番デプロイ前のチェック不足  
**解決：** 本番前に必ず全ファイルを検索して削除

---

### ❌ 間違い7: {% block content %} を忘れる

```html
<!-- ❌ 間違い -->
{% extends "base.html" %}

{% block title %}ページタイトル{% endblock %}

<!-- {% block content %} がない！ -->

<div class="container">
  <!-- コンテンツ -->
</div>

{% endblock %}


<!-- ✅ 正しい -->
{% extends "base.html" %}

{% block title %}ページタイトル{% endblock %}

{% block content %}
<div class="container">
  <!-- コンテンツ -->
</div>
{% endblock %}
```

**原因：** テンプレート構造の理解不足  
**解決：** 必ず `{% block content %}` で囲む

**症状：**
- ページが真っ白になる
- コンテンツが表示されない
- エラーメッセージが出ない

---

### ❌ 間違い8: base.htmlのブロック名と一致しない

```html
<!-- ❌ 間違い -->
<!-- base.htmlは {% block extra_scripts %} なのに... -->

{% block extra_js %}
<script src="{{ url_for('static', filename='js/example.js') }}"></script>
{% endblock %}


<!-- ✅ 正しい -->
<!-- base.htmlと同じブロック名を使用 -->

{% block extra_scripts %}
<script src="{{ url_for('static', filename='js/example.js') }}"></script>
{% endblock %}
```

**原因：** base.htmlのブロック名を確認せずに記述  
**解決：** 新規テンプレート作成時に必ずbase.htmlを確認

**症状：**
- JavaScriptが読み込まれない
- `typeof 関数名` が `"undefined"`
- Networkタブでファイルが表示されない
- エラーメッセージが出ない

**デバッグ方法：**
```bash
# base.htmlのブロック名を確認
grep "{% block" templates/base.html
```

```javascript
// コンソールで関数が読み込まれているか確認
typeof initializeFunction  // "undefined" なら読み込まれていない
```

---

## 🎯 まとめ

### 最重要ポイント

1. **psycopg3** (`psycopg`) を使用
2. **`get_db()` で接続取得**、cursor()は自動的にdict_row
3. **エンドポイントは `register_XXX_routes(app)` 内に定義**
4. **すべてのテーブルに `store_id` を追加**してフィルタ
5. **HTMLは `{% block content %}` で囲む**
6. **JavaScriptのブロック名はbase.htmlと一致させる**
7. **CSSは必ずクラス名を使用**、タグ直接指定禁止
8. **デバッグコードは本番前に完全削除**

---

## 📞 サポート

質問がある場合は、このドキュメントを参照してください。
それでも不明な場合は、既存のコードを参考にしてください。

**参考ファイル：**
- `database/connection.py` - 接続管理
- `routes/settings.py` - ルート定義の例
- `routes/customer.py` - CRUD処理の例
- `templates/base.html` - ベーステンプレート
- `app.py` - ルート登録の例

---

**このガイドラインに従って開発してください！** 🚀