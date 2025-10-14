# 📘 Autocoll 開発ガイド

Autocoll（マルチ店舗管理システム）の開発ルールをまとめたドキュメントです。

---

## 📑 目次

1. [🚨 絶対に守るべきルール](#-絶対に守るべきルール)
2. [🎨 デザイン規約](#-デザイン規約)
3. [✅ 開発前チェックリスト](#-開発前チェックリスト)
4. [🚫 よくある間違い](#-よくある間違い)

---

## 🚨 絶対に守るべきルール

### 1️⃣ データベース接続

**psycopg3を使用（psycopg2ではない）**

```python
from database.connection import get_db

db = get_db()
cursor = db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cursor.fetchone()  # 自動的に辞書形式
db.close()
```

**重要：**
- `get_db()`は既に`dict_row`設定済み → `cursor(row_factory=dict_row)`は不要
- プレースホルダーは`%s`を使用（`?`ではない）
- **結果は辞書形式** → `result['column_name']`でアクセス（`result.column_name`ではない）

```python
# ❌ 間違い：属性アクセス
result.max_order      # エラー
current.sort_order    # エラー

# ✅ 正しい：辞書アクセス
result['max_order']   # OK
current['sort_order'] # OK
```

---

### 2️⃣ ルート定義（Blueprintパターン）

**❌ 間違い：** `register_XXX_routes(app)`形式
**✅ 正しい：** 個別関数 + `main.py`でルート登録

```python
# routes/example.py - 個別関数として定義
def example_management(store):
    return render_template('example.html', store=store)

# routes/main.py - インポート＆ルート登録
from .example import example_management
main_routes.add_url_rule('/<store>/example', 'example_management', 
                         example_management, methods=['GET'])
```

---

### 3️⃣ 店舗データ分離

**すべてのテーブルに`store_id`を追加**

```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,  -- 必須
    customer_name VARCHAR(100)
);

CREATE INDEX idx_customers_store_id ON customers(store_id);
```

```python
# 必ず WHERE store_id = %s でフィルタ
cursor.execute("SELECT * FROM customers WHERE store_id = %s", (store_id,))
```

---

## 🎨 デザイン規約

### 📐 メインカラー

```
#00BCD4（水色）
```

すべてのボタン、アクセント、アイコンに使用

---

### 🎨 デザイン要素一覧

新機能を作る際は、既存ページ（オプション管理など）と**完全に同じデザイン**にする。

| 要素 | スペック |
|------|---------|
| **メインカラー** | `#00BCD4` |
| **タイトル** | `margin: 0` |
| **フォームカード背景** | `#f5f5f5` |
| **テーブルヘッダー背景** | `#5a5a5a` |
| **テーブルセルパディング** | `6px` |
| **トグルスイッチ** | 丸型（`border-radius: 24px` / つまみ`50%`）、有効時`#00BCD4` |
| **並び順ボタン** | `padding: 2px 6px`, `font-size: 14px`, 背景`#00BCD4` |
| **編集アイコン** | `fa-pencil-alt`, 色`#00BCD4` |
| **削除アイコン** | `fa-trash-alt`, 色`#dc3545` |
| **状態表示** | `padding: 4px 12px`, `border-radius: 20px`, 背景色付き＋白文字 |

---

### 📝 状態表示（重要）

```css
.xxx-status-active {
    display: inline-block;
    padding: 4px 12px;
    background-color: #28a745;  /* 緑 */
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;
}

.xxx-status-inactive {
    display: inline-block;
    padding: 4px 12px;
    background-color: #dc3545;  /* 赤 */
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;
}
```

**ポイント：** 丸いボタン型、背景色付き、白文字

---

### 🔘 トグルスイッチ

```css
.xxx-toggle-slider {
    border-radius: 24px;  /* 丸型 */
}

.xxx-toggle-slider:before {
    border-radius: 50%;  /* 完全な円 */
}

.xxx-toggle-checkbox:checked + .xxx-toggle-slider {
    background-color: #00BCD4;  /* メインカラー */
}
```

**ポイント：** 角型ではなく丸型

---

### 🔼 並び順ボタン

```html
<button onclick="moveUp(...)" 
        class="xxx-sort-btn {% if loop.first %}xxx-sort-btn-disabled{% endif %}"
        {% if loop.first %}disabled{% endif %}>
    <i class="fas fa-chevron-up"></i>
</button>
<button onclick="moveDown(...)" 
        class="xxx-sort-btn {% if loop.last %}xxx-sort-btn-disabled{% endif %}"
        {% if loop.last %}disabled{% endif %}>
    <i class="fas fa-chevron-down"></i>
</button>
```

```css
.xxx-sort-btn {
    padding: 4px 8px;
    font-size: 16px;
    background-color: #00BCD4;
    color: white;
    border: none;
    cursor: pointer;
}

.xxx-sort-btn-disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}
```

**ポイント:**
- 一番上の項目では「上に移動」をdisabled
- 一番下の項目では「下に移動」をdisabled
- `{% if loop.first %}`と`{% if loop.last %}`を使用
- disabled時はクラス追加とdisabled属性の両方を設定

---

### 🎯 デザイン統一の手順

1. **既存の類似ページを確認**（例：オプション管理）
2. **HTML/CSS/JSをコピー**
3. **クラス名を一括置換**（`.option-` → `.discount-`）
4. **ブラウザで既存ページと並べて確認**

---

## ✅ 開発前チェックリスト

### データベース
- [ ] psycopg3（`psycopg`）を使用
- [ ] `get_db()`で接続取得
- [ ] プレースホルダーは`%s`

### 店舗データ分離
- [ ] テーブルに`store_id`カラムがある
- [ ] `WHERE store_id = %s`でフィルタ

### ルート定義
- [ ] 個別関数として定義
- [ ] `main.py`でインポート＆ルート登録
- [ ] `register_XXX_routes(app)`形式は使わない

### デザイン
- [ ] 既存ページと同じデザイン
- [ ] メインカラー`#00BCD4`を使用
- [ ] テーブルヘッダー`#5a5a5a`
- [ ] トグルスイッチは丸型
- [ ] 状態表示は丸いボタン型
- [ ] アイコンは`fa-pencil-alt`、`fa-trash-alt`
- [ ] 並び順ボタンは`loop.first`/`loop.last`でdisabled

### HTML
- [ ] `{% extends "base.html" %}`
- [ ] `{% block content %}`で囲む
- [ ] CSSは`{% block extra_head %}`
- [ ] JSは`{% block extra_scripts %}`

### CSS
- [ ] クラス名を使用（タグ直接指定禁止）
- [ ] 角丸は使わない（`border-radius: 0`）

---

## 🚫 よくある間違い

### ❌ 間違い1：psycopg2を使う
```python
# ❌ 間違い
import psycopg2

# ✅ 正しい
import psycopg
```

---

### ❌ 間違い2：二重にdict_rowを指定
```python
# ❌ 間違い
db = get_db()
cursor = db.cursor(row_factory=dict_row)  # エラー

# ✅ 正しい
db = get_db()
cursor = db.cursor()  # 自動的にdict_row
```

---

### ❌ 間違い3：属性アクセスで辞書にアクセス
```python
# ❌ 間違い
cursor.execute("SELECT MAX(sort_order) as max_order FROM discounts")
result = cursor.fetchone()
next_order = result.max_order + 1  # AttributeError

# ✅ 正しい
cursor.execute("SELECT MAX(sort_order) as max_order FROM discounts")
result = cursor.fetchone()
next_order = result['max_order'] + 1  # OK
```

**重要：** `get_db()`は辞書形式で返すため、必ず`result['column_name']`でアクセスする

---

### ❌ 間違い4：register_XXX_routes(app)形式
```python
# ❌ 間違い
def register_example_routes(app):
    @app.route('/<store>/example')
    def example_page(store):
        return render_template('example.html', store=store)

# ✅ 正しい
def example_management(store):
    return render_template('example.html', store=store)
```

---

### ❌ 間違い5：store_idでフィルタしない
```python
# ❌ 間違い
cursor.execute("SELECT * FROM customers")  # 全店舗のデータが取れる

# ✅ 正しい
cursor.execute("SELECT * FROM customers WHERE store_id = %s", (store_id,))
```

---

### ❌ 間違い6：デザインが既存ページと違う

**必ず既存ページ（オプション管理など）と同じデザインにする**

| 要素 | ❌ 間違い | ✅ 正しい |
|------|-----------|----------|
| トグルスイッチ | 角型 | 丸型（border-radius: 24px） |
| テーブルヘッダー | `#495057` | `#5a5a5a` |
| 編集アイコン | `fa-pen` | `fa-pencil-alt` |
| 削除アイコン | `fa-trash` | `fa-trash-alt` |
| 並び順ボタン | `padding: 6px 10px` | `padding: 4px 8px` |
| 状態表示 | 色付きテキスト | 丸いボタン型、背景色付き |

---

### ❌ 間違い7：並び順ボタンのdisabled処理を忘れる

**一番上/下の項目でもボタンが押せてしまう**

```html
<!-- ❌ 間違い：disabledなし -->
<button onclick="moveUp(...)" class="xxx-sort-btn">
    <i class="fas fa-chevron-up"></i>
</button>

<!-- ✅ 正しい：loop.firstでdisabled -->
<button onclick="moveUp(...)" 
        class="xxx-sort-btn {% if loop.first %}xxx-sort-btn-disabled{% endif %}"
        {% if loop.first %}disabled{% endif %}>
    <i class="fas fa-chevron-up"></i>
</button>
```

**重要:** クラス追加とdisabled属性の両方を設定する

---

## 📚 クイックリファレンス

### データベース接続
```python
from database.connection import get_db
db = get_db()
cursor = db.execute("SELECT * FROM table WHERE id = %s", (id,))
result = cursor.fetchone()
db.close()
```

### ルート定義
```python
# routes/example.py
def example_management(store):
    return render_template('example.html', store=store)

# routes/main.py
from .example import example_management
main_routes.add_url_rule('/<store>/example', 'example_management', 
                         example_management, methods=['GET'])
```

### HTMLテンプレート
```html
{% extends "base.html" %}

{% block extra_head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/xxx.css') }}">
{% endblock %}

{% block title %}タイトル{% endblock %}

{% block content %}
<div class="xxx-container">
  <!-- コンテンツ -->
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{{ url_for('static', filename='js/xxx.js') }}"></script>
{% endblock %}
```

### CSS基本
```css
/* クラス名でスコープを限定 */
.xxx-container { }
.xxx-title { margin: 0; }
.xxx-form-card { background-color: #f5f5f5; }
.xxx-table thead th { background-color: #5a5a5a; }

/* タグ直接指定は禁止 */
/* body { } ← NG */
/* h1 { } ← NG */
```

---

## 🎯 まとめ

### 最重要ポイント

1. **psycopg3**（`psycopg`）を使用
2. **個別関数でルート定義**、`main.py`でルート登録
3. **すべてのテーブルに`store_id`**を追加
4. **既存ページと同じデザイン**にする
5. **メインカラー`#00BCD4`**を使用
6. **状態表示は丸いボタン型**（背景色付き＋白文字）
7. **トグルスイッチは丸型**（角型ではない）
8. **並び順ボタンは`loop.first`/`loop.last`でdisabled処理**

---

## 📞 サポート

不明な点があれば、このドキュメントを参照してください。