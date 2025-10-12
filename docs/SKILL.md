# Autocoll プロジェクト開発ルール

このスキルは、Autocoll（マルチ店舗管理システム）の開発時に**必ず守るべきルール**を定義しています。



# 🎯 Multi-Store App 開発ガイドライン

このドキュメントは、開発時に**必ず守るべき統一基準**をまとめたものです。  
AIによって実装がバラバラにならないよう、すべての開発者（AI含む）はこの基準に従ってください。

---

## 📊 データベース接続

### ✅ 使用するライブラリ

**psycopg3 (`psycopg`) を使用**

```python
import psycopg
from psycopg.rows import dict_row
```

❌ **psycopg2 は使用しない**（過去の遺物）

---

### ✅ データベース接続の取得

**必ず `database.connection` の `get_db()` または `get_connection()` を使用**

```python
from database.connection import get_db

# SQLiteライクな使い方
db = get_db()
cursor = db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cursor.fetchone()  # 自動的に辞書形式で返る
db.close()
```

または

```python
from database.connection import get_connection

# 標準的なpsycopg3の使い方
conn = get_connection()
cur = conn.cursor(row_factory=dict_row)
cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cur.fetchone()  # 辞書形式
cur.close()
conn.close()
```

---

### ✅ PostgreSQLConnectionWrapper について

`get_db()` が返すのは **PostgreSQLConnectionWrapper** オブジェクトです。

**特徴：**
- `cursor()` メソッドは**自動的に `dict_row` を返す**
- `execute()` メソッドで直接SQL実行可能
- SQLiteライクな書き方ができる

```python
# ❌ 間違い（二重にdict_rowを指定）
cursor = db.cursor(row_factory=dict_row)  # エラー！

# ✅ 正しい
cursor = db.cursor()  # 自動的にdict_rowになる
```

---

### ✅ SQL構文の注意点

#### プレースホルダー

PostgreSQLでは `%s` を使用（MySQLの `?` ではない）

```python
# ✅ 正しい
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ 間違い
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

#### COMMENT構文

PostgreSQLでは別途COMMENTコマンドを使用

```sql
-- ✅ 正しい（PostgreSQL）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

COMMENT ON COLUMN users.id IS 'ユーザーID';
COMMENT ON COLUMN users.name IS 'ユーザー名';

-- ❌ 間違い（MySQL構文）
CREATE TABLE users (
    id SERIAL PRIMARY KEY COMMENT 'ユーザーID',
    name VARCHAR(100) NOT NULL COMMENT 'ユーザー名'
);
```

---

## 🛣️ ルート定義

### ✅ ルート登録の形式

**`register_XXX_routes(app)` 関数形式を使用**

❌ **Blueprint形式ではない**

```python
# routes/example.py

from flask import request, jsonify, session
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
    ✅ この関数の中にすべてのルートを定義する
    """
    
    @app.route('/<store>/example')
    @admin_required
    def example_page(store):
        return render_template('example.html', store=store)
    
    
    @app.route('/<store>/example/create', methods=['POST'])
    @admin_required
    def create_example(store):
        data = request.get_json()
        # 処理...
        return jsonify({'success': True})
    
    # すべてのエンドポイントをこの関数内に定義


# ❌ 関数の外にエンドポイントを書かない
# @app.route('/<store>/example/error')  # これはエラーになる！
```

---

### ✅ app.py での登録

```python
# app.py

from routes.settings import register_settings_routes
from routes.example import register_example_routes

# ルートを登録
register_settings_routes(app)
register_example_routes(app)
```

---

## 🏢 店舗ID の扱い

### ✅ 現在の仕様

**店舗IDは将来の拡張用で、現在は使用していない**

```python
def get_card_fee_rate(store_id=None):
    """
    カード手数料率を取得
    
    Args:
        store_id (int, optional): 店舗ID（将来の拡張用、現在は未使用）
    
    Returns:
        float: カード手数料率
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        # 店舗IDでフィルタせず、全店舗共通の設定を取得
        cur.execute("""
            SELECT setting_value
            FROM store_settings
            WHERE setting_key = 'card_fee_rate'
            LIMIT 1
        """)
        
        result = cur.fetchone()
        return float(result['setting_value']) if result else 5.0
        
    finally:
        cur.close()
        conn.close()
```

**将来の拡張時には：**
- `WHERE setting_key = 'card_fee_rate' AND store_id = %s` のようにフィルタを追加
- 関数の引数 `store_id` を実際に使用

---

## 📝 コーディング規約

### ✅ インポート順序

```python
# 1. 標準ライブラリ
from datetime import datetime
import os

# 2. サードパーティ
from flask import request, jsonify
import psycopg
from psycopg.rows import dict_row

# 3. プロジェクト内モジュール
from database.connection import get_db
from config import DATABASE_CONFIG
```

---

### ✅ エラーハンドリング

```python
try:
    # 処理
    conn = get_db()
    # ...
    
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

---

## 🚨 よくある間違い

### ❌ 間違い1: psycopg2を使おうとする

```python
# ❌ 間違い
import psycopg2

# ✅ 正しい
import psycopg
```

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

---

### ❌ 間違い3: 関数の外にエンドポイントを定義

```python
# ❌ 間違い
def register_routes(app):
    @app.route('/test')
    def test():
        return 'OK'

@app.route('/error')  # これはエラー！app が定義されていない
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

---

## 📚 参考

### データベース関連ファイル
- `database/connection.py` - 接続管理
- `database/db_connection.py` - 旧形式（互換性維持）
- `config.py` - データベース設定

### ルート関連ファイル
- `routes/settings.py` - 設定管理
- `routes/customer.py` - 顧客管理
- `app.py` - メインアプリケーション

---

## 🎯 まとめ

1. **psycopg3 (`psycopg`) を使用**
2. **`get_db()` または `get_connection()` で接続取得**
3. **`cursor()` は自動的に `dict_row`**
4. **エンドポイントは `register_XXX_routes(app)` 関数内に定義**
5. **店舗IDは将来の拡張用（現在未使用）**

---

**このガイドラインに従って開発してください！** 🚀



### 1. デバッグコードの削除

#### ✅ 正しい
```javascript
// デバッグ終了後は削除
// console.log('debug:', data);  ← これは残さない
```

#### ❌ 間違い
```javascript
console.log('debug:', data);  // 本番環境に残す
```

#### ルール
デバッグが終わったら`console.log()`、`print()`などは全て削除

---

### 3. CSS クラス名

#### ✅ 正しい
```css
.customer-input {
    padding: 8px;
}
```

#### ❌ 間違い
```css
input {  /* クラス名なし */
    padding: 8px;
}
```

#### ルール
**必ずクラス名を付ける**

---

### 4. CSS スコープ

#### ❌ 禁止
```css
body {
    font-size: 14px;  /* 全体に影響する */
}

h1 {
    color: #333;  /* 全体に影響する */
}
```

#### ✅ 正しい
```css
.customer-container {
    font-size: 14px;  /* スコープを限定 */
}

.customer-title {
    color: #333;  /* スコープを限定 */
}
```

#### ルール
`body`, `h1`, `p`, `div` などの**タグ直接指定は禁止**
必ずクラス名でスコープを限定すること

---

## 🎨 デザインルール

### ボタンの角丸
```css
border-radius: 4px;  /* すべて4pxで統一 */
```

### 理由
プロジェクト全体で統一されたデザイン

---

## 📌 重要な注意事項

このルールは**例外なく適用**されます。
ユーザーから特別な指示がない限り、必ずこのルールに従ってコードを作成してください。

---

## ✅ チェックリスト

コード作成前に必ず確認：
- [ ] store_idは動的取得しているか
- [ ] デバッグコードは削除したか
- [ ] CSSにクラス名を付けているか
- [ ] CSSでタグ直接指定をしていないか
