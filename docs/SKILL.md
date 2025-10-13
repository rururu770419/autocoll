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

### 2️⃣ ルート定義（最重要）

#### 🚨 このプロジェクトのルート定義パターン

**このプロジェクトはBlueprintを使用しており、`main.py`で個別関数をインポートする形式です。**

絶対に `register_XXX_routes(app)` 形式で書かないでください！

---

#### ✅ 正しい書き方（Blueprintパターン）

**Step 1: routes/example.py - 個別関数として定義**

```python
# routes/example.py

from flask import request, jsonify, session, redirect, render_template
from functools import wraps
from database.connection import get_db, get_display_name

def admin_required(f):
    """管理者権限チェック"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


# ========== 画面表示用の関数 ==========

def example_management(store):
    """一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    items = get_all_items(db)
    
    return render_template(
        'example_management.html',
        store=store,
        display_name=display_name,
        items=items
    )


# ========== API用の関数 ==========

def get_items_api(store):
    """一覧取得API"""
    try:
        db = get_db()
        items = get_all_items(db)
        return jsonify({'success': True, 'items': [dict(i) for i in items]})
    except Exception as e:
        print(f"エラー: {e}")
        return jsonify({'success': False, 'message': '取得に失敗しました'}), 500


def register_item_api(store):
    """登録API"""
    try:
        data = request.get_json()
        db = get_db()
        
        # バリデーション
        if not data.get('name'):
            return jsonify({'success': False, 'message': '名前は必須です'}), 400
        
        # 登録実行
        result = register_item(db, data)
        
        if result:
            return jsonify({'success': True, 'message': '登録しました'})
        else:
            return jsonify({'success': False, 'message': '登録に失敗しました'}), 500
    except Exception as e:
        print(f"エラー: {e}")
        return jsonify({'success': False, 'message': '登録に失敗しました'}), 500


def update_item_api(store, item_id):
    """更新API"""
    try:
        data = request.get_json()
        db = get_db()
        
        success = update_item(db, item_id, data)
        
        if success:
            return jsonify({'success': True, 'message': '更新しました'})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
    except Exception as e:
        print(f"エラー: {e}")
        return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
```

**Step 2: routes/main.py - インポートとルート登録**

```python
# routes/main.py

from flask import Blueprint

# インポート（個別関数をインポート）
from .example import (
    example_management,
    get_items_api,
    register_item_api,
    update_item_api
)

# Blueprint作成
main_routes = Blueprint('main_routes', __name__)

# ルート登録（画面）
main_routes.add_url_rule('/<store>/example_management', 'example_management', example_management, methods=['GET'])

# ルート登録（API）
main_routes.add_url_rule('/<store>/example_management/api/list', 'get_items_api', get_items_api, methods=['GET'])
main_routes.add_url_rule('/<store>/example_management/api/register', 'register_item_api', register_item_api, methods=['POST'])
main_routes.add_url_rule('/<store>/example_management/api/update/<int:item_id>', 'update_item_api', update_item_api, methods=['POST'])
```

---

#### 🚨 間違った書き方（絶対に禁止！）

```python
# ❌ 間違い：register_XXX_routes(app)形式
def register_example_routes(app):
    @app.route('/<store>/example')
    def example_page(store):
        return render_template('example.html', store=store)

# ❌ 間違い：main.pyでこの関数を呼び出そうとする
from .example import register_example_routes
register_example_routes(app)  # これは動かない！
```

**理由：** このプロジェクトはBlueprintを使っているため、`app`オブジェクトは直接利用できません。必ず`main.py`の`add_url_rule`でルート登録する必要があります。

---

#### ✅ ポイント

1. **routes/xxx.py** では個別関数として定義
2. **routes/main.py** でインポート＆ルート登録
3. `register_XXX_routes(app)` 形式は**絶対に使わない**
4. 各関数は必ず `store` 引数を受け取る
5. `@admin_required` デコレーターを各関数に付ける（main.pyではなく）

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

### 4️⃣ デザイン統一（重要）

#### 🚨 新しい機能を作るときは既存ページと同じデザインにする

**理由：** プロジェクト全体のデザインを統一し、メンテナンス性を向上させる

---

#### ✅ 基本原則

1. **既存の類似ページを確認する**
   - 例：割引管理を作る → オプション管理を参照
   - 例：顧客管理を作る → キャスト管理を参照

2. **HTML構造をコピーする**
   - セクション構成
   - フォームレイアウト
   - テーブル構造
   - ボタン配置

3. **CSS/JSファイル名だけ変更する**
   - options.css → discount.css
   - options.js → discount.js
   - クラス名も統一（`.option-` → `.discount-`）

4. **アイコンとボタンを統一する**
   - 並び順：↑↓ボタン
   - 編集：鉛筆アイコン（fas fa-pen）
   - 削除：ゴミ箱アイコン（fas fa-trash）

---

#### ✅ 具体例：割引管理（オプション管理と同じデザイン）

**Step 1: オプション管理を確認**
```
http://localhost:5001/nagano/options
```

**特徴：**
- 登録フォームがページ上部に常に表示
- 編集はモーダル
- 並び順は↑↓ボタン
- 編集列と削除列が分かれている
- トグルスイッチで状態切替

**Step 2: HTMLをコピーして改造**
```html
<!-- オプション管理のテンプレートをベースに -->
<div class="discount-container">  <!-- option-container から変更 -->
    <!-- 登録フォーム（常に表示） -->
    <div class="discount-register-section">
        <h3>割引登録</h3>
        <form>...</form>
    </div>
    
    <!-- 一覧テーブル -->
    <div class="discount-list-section">
        <table class="discount-table">
            <thead>
                <tr>
                    <th>並び順</th>
                    <th>割引名</th>
                    <th>種類</th>
                    <th>割引値</th>
                    <th>状態</th>
                    <th>編集</th>
                    <th>削除</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>
                        <button onclick="moveDiscount(id, 'up')">
                            <i class="fas fa-chevron-up"></i>
                        </button>
                        <button onclick="moveDiscount(id, 'down')">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </td>
                    <td>{{ name }}</td>
                    <td>固定金額</td>
                    <td>3,000円</td>
                    <td>有効</td>
                    <td>
                        <button onclick="showEditModal(id)">
                            <i class="fas fa-pen"></i>
                        </button>
                    </td>
                    <td>
                        <button onclick="deleteDiscount(id)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<!-- 編集モーダル -->
<div id="discount-edit-modal" class="discount-modal">
    ...
</div>
```

**Step 3: CSSをコピーして改造**
```css
/* options.cssをベースに */
.discount-container { }  /* .option-container から変更 */
.discount-title { }
.discount-register-section { }
.discount-form { }
.discount-table { }
.discount-btn-icon { }
```

**Step 4: JavaScriptをコピーして改造**
```javascript
// options.jsをベースに
function submitRegister(event) { }  // 登録
function showEditModal(id) { }      // 編集モーダル表示
function deleteDiscount(id) { }     // 削除
function moveDiscount(id, dir) { }  // 並び順変更
```

---

#### ✅ 詳細確認チェックリスト

新機能を作成した後、必ず以下を確認してください：

**HTML構造**
- [ ] タイトルは外の上部に配置（セクション内ではない）
- [ ] 登録フォームはページ上部に常に表示（モーダルではない）
- [ ] 編集だけモーダル
- [ ] テーブルの列構成が既存ページと同じ
- [ ] アイコンが既存ページと同じ（fa-pencil-alt、fa-trash-alt）

**CSS**
- [ ] 登録セクションの背景色：`#f5f5f5`
- [ ] テーブルヘッダー背景色：`#5a5a5a`
- [ ] トグルスイッチ：丸型（border-radius: 24px / 50%）
- [ ] 並び順ボタン：`padding: 4px 8px`、`font-size: 16px`
- [ ] アクセントカラー：`#00BCD4`
- [ ] 編集アイコン色：`#00BCD4`
- [ ] 削除アイコン色：`#dc3545`
- [ ] 状態表示：丸いボタン型（border-radius: 20px）、背景色付き、白文字

**JavaScript**
- [ ] 種類ボタンの切り替え機能が動作する
- [ ] トグルスイッチの状態取得が正しい
- [ ] モーダルの開閉が正しく動作する
- [ ] 並び順変更が正しく動作する

**動作確認**
- [ ] ブラウザで既存ページと並べて表示し、デザインが完全一致することを確認
- [ ] 登録フォームが正常に動作する
- [ ] 編集モーダルが正常に動作する
- [ ] 削除が正常に動作する
- [ ] 並び順変更が正常に動作する

---

#### 🚨 間違った箇所の例と修正方法

**間違い1：登録フォームの配置**
```html
<!-- ❌ 間違い：フォーム順序が違う -->
<div class="discount-form-grid">
    <div>割引名</div>
    <div>状態</div>  <!-- これは右下に配置すべき -->
    <div>種類</div>
    <div>割引値</div>
</div>

<!-- ✅ 正しい：オプション管理と同じ配置 -->
<div class="discount-form-grid">
    <div>割引名</div>
    <div>割引値</div>
    <div>種類</div>
    <div>状態</div>
</div>
```

**間違い2：トグルスイッチのデザイン**
```css
/* ❌ 間違い：角型 */
.discount-toggle-slider {
    border-radius: 0;
}
.discount-toggle-slider:before {
    border-radius: 0;
}

/* ✅ 正しい：丸型 */
.discount-toggle-slider {
    border-radius: 24px;
}
.discount-toggle-slider:before {
    border-radius: 50%;
}
```

**間違い3：テーブルヘッダーの色**
```css
/* ❌ 間違い */
.discount-table thead th {
    background-color: #495057;  /* 違う色 */
}

/* ✅ 正しい */
.discount-table thead th {
    background-color: #5a5a5a;  /* オプションと同じ */
}
```

**間違い4：アイコン名**
```html
<!-- ❌ 間違い -->
<i class="fas fa-pen"></i>     <!-- これは短い名前 -->
<i class="fas fa-trash"></i>

<!-- ✅ 正しい -->
<i class="fas fa-pencil-alt"></i>  <!-- オプションと同じ -->
<i class="fas fa-trash-alt"></i>
```

**間違い5：並び順ボタンのサイズ**
```css
/* ❌ 間違い */
.discount-sort-btn {
    padding: 6px 10px;
    font-size: 14px;
}

/* ✅ 正しい */
.discount-sort-btn {
    padding: 4px 8px;
    font-size: 16px;
}
```

**間違い6：状態表示のデザイン**
```css
/* ❌ 間違い：ただの色付きテキスト */
.discount-status-active {
    color: #28a745;
    font-weight: bold;
}

/* ✅ 正しい：丸いボタン型・背景色付き・白文字 */
.discount-status-active {
    display: inline-block;
    padding: 4px 12px;
    background-color: #28a745;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;
    text-align: center;
    white-space: nowrap;
}

.discount-status-inactive {
    display: inline-block;
    padding: 4px 12px;
    background-color: #dc3545;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;
    text-align: center;
    white-space: nowrap;
}
```

---

#### 📐 重要なデザイン要素一覧（必ず守る）

新機能を作る際は、以下の要素を**必ず**このスペックで実装してください。

---

##### 🎨 メインカラー

**プロジェクト全体で統一するカラー**

```css
/* メインカラー：水色 */
#00BCD4

/* 使用箇所 */
- ボタンの背景色（登録、更新など）
- アクセントカラー（リンク、アイコンなど）
- トグルスイッチの有効時
- 並び順ボタンの背景色
- 編集アイコンの色
- フォーカス時のボーダー色
```

---

##### 📝 タイトル（h1）

```css
.xxx-title {
    font-size: 1.75rem;
    margin: 0;              /* 必ず0 */
    padding-bottom: 30px;
    color: #333;
}
```

**重要：** タイトルのmarginは**必ず0**にする

---

##### 📋 登録フォームカード

```css
.xxx-form-card {
    background-color: #f5f5f5;  /* 必ずこの色 */
    border: 1px solid #dee2e6;
    border-radius: 0;
    padding: 25px;
    margin-bottom: 30px;
}
```

**重要：** 背景色は**必ず #f5f5f5** （薄いグレー）

---

##### 🔘 トグルスイッチ

```css
/* スイッチ本体 */
.xxx-toggle-switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}

/* スライダー */
.xxx-toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: 0.3s;
    border-radius: 24px;  /* 丸型 */
}

.xxx-toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;  /* 丸型 */
}

/* チェック時（有効時） */
.xxx-toggle-checkbox:checked + .xxx-toggle-slider {
    background-color: #00BCD4;  /* メインカラー */
}

.xxx-toggle-checkbox:checked + .xxx-toggle-slider:before {
    transform: translateX(26px);
}
```

**重要ポイント：**
- スライダー：`border-radius: 24px`（丸型）
- つまみ：`border-radius: 50%`（完全な円）
- 有効時の色：`#00BCD4`（メインカラー）

---

##### 📊 テーブルヘッダー

```css
.xxx-table thead th {
    background-color: #5a5a5a;  /* 必ずこの色 */
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    padding: 14px 10px;
    text-align: center;
    border-bottom: none;
}
```

**重要：** 背景色は**必ず #5a5a5a**（濃いグレー）

---

##### 🔼 並び順ボタン

```css
.xxx-sort-btn {
    display: inline-block;
    padding: 4px 8px;          /* 必ずこのサイズ */
    background-color: #00BCD4; /* メインカラー */
    color: #fff;
    border: none;
    border-radius: 0;
    font-size: 16px;           /* 必ずこのサイズ */
    cursor: pointer;
    margin: 0 2px;
    text-decoration: none;
    transition: background-color 0.2s ease;
}

.xxx-sort-btn:hover {
    background-color: #00a8b8;
    color: #fff;
    text-decoration: none;
}
```

**重要ポイント：**
- padding: `4px 8px`
- font-size: `16px`
- background-color: `#00BCD4`（メインカラー）

---

##### ✏️ 編集アイコン

```html
<!-- HTML -->
<a href="javascript:void(0);" class="xxx-action-btn" onclick="openEditModal(id)" title="編集">
    <i class="fas fa-pencil-alt xxx-edit-icon"></i>
</a>
```

```css
/* CSS */
.xxx-action-btn {
    display: inline-block;
    padding: 8px 12px;
    margin: 0 3px;
    font-size: 16px;
    cursor: pointer;
    transition: opacity 0.2s ease;
    text-decoration: none;
    vertical-align: middle;
}

.xxx-action-btn:hover {
    opacity: 0.7;
    text-decoration: none;
}

.xxx-edit-icon {
    color: #00BCD4;  /* メインカラー */
}
```

**重要ポイント：**
- アイコン名：`fa-pencil-alt`（`fa-pen`ではない）
- 色：`#00BCD4`（メインカラー）

---

##### 🗑️ 削除アイコン

```html
<!-- HTML -->
<a href="javascript:void(0);" class="xxx-action-btn" onclick="deleteXXX(id, name)" title="削除">
    <i class="fas fa-trash-alt xxx-delete-icon"></i>
</a>
```

```css
/* CSS */
.xxx-delete-icon {
    color: #dc3545;  /* 赤色 */
}
```

**重要ポイント：**
- アイコン名：`fa-trash-alt`（`fa-trash`ではない）
- 色：`#dc3545`（赤色）

---

##### 🟢 状態表示（ステータス）

```html
<!-- HTML -->
{% if item.is_active %}
    <span class="xxx-status-active">有効</span>
{% else %}
    <span class="xxx-status-inactive">無効</span>
{% endif %}
```

```css
/* CSS */
.xxx-status-active {
    display: inline-block;
    padding: 4px 12px;          /* 必ずこのサイズ */
    background-color: #28a745;  /* 緑色 */
    color: #ffffff;             /* 白文字 */
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;        /* 丸型 */
    text-align: center;
    white-space: nowrap;
}

.xxx-status-inactive {
    display: inline-block;
    padding: 4px 12px;          /* 必ずこのサイズ */
    background-color: #dc3545;  /* 赤色 */
    color: #ffffff;             /* 白文字 */
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;        /* 丸型 */
    text-align: center;
    white-space: nowrap;
}
```

**重要ポイント：**
- padding: `4px 12px`
- border-radius: `20px`（丸型）
- 背景色付き＋白文字（`#ffffff`）
- 有効：緑色（`#28a745`）
- 無効：赤色（`#dc3545`）

---

#### 🚨 禁止事項

```html
<!-- ❌ 間違い：独自デザインで作る -->
<div class="my-custom-container">
    <button class="my-btn">新規登録</button>  <!-- 既存と違う -->
</div>

<!-- ✅ 正しい：既存デザインを踏襲 -->
<div class="discount-container">
    <button class="discount-btn-submit">登録</button>  <!-- 既存と同じ -->
</div>
```

---

#### ✅ チェックリスト

新機能を作る前に必ず確認：

- [ ] 類似する既存ページを特定した
- [ ] 既存ページのHTML構造を確認した
- [ ] 既存ページのCSS/JSファイルをコピーした
- [ ] クラス名を新機能名に一括置換した（`.option-` → `.discount-`）
- [ ] アイコンが既存ページと同じか確認した
- [ ] ボタンの配置が既存ページと同じか確認した
- [ ] テーブルの列構成が既存ページと同じか確認した
- [ ] 実際にブラウザで既存ページと見比べて確認した

---

### 5️⃣ HTMLテンプレート構造

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
- [ ] 個別関数として定義しているか（`register_XXX_routes(app)`形式は禁止）
- [ ] `routes/main.py` でインポートしたか
- [ ] `main.py` で `add_url_rule` を使ってルート登録したか
- [ ] 各関数に `@admin_required` デコレーターを付けたか

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
# routes/feature.py

from flask import render_template, request, jsonify, session, redirect
from functools import wraps
from database.connection import get_db, get_display_name

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


# 画面表示
def feature_management(store):
    """一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    items = get_all_items(db)
    
    return render_template('feature.html', store=store, items=items)


# API
def register_item_api(store):
    """登録API"""
    try:
        data = request.get_json()
        db = get_db()
        
        result = register_item(db, data)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False}), 500
```

```python
# routes/main.py

from .feature import feature_management, register_item_api

# ルート登録
main_routes.add_url_rule('/<store>/feature', 'feature_management', feature_management, methods=['GET'])
main_routes.add_url_rule('/<store>/feature/api/register', 'register_item_api', register_item_api, methods=['POST'])
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

### ❌ 間違い3: register_XXX_routes(app)形式を使う

```python
# ❌ 間違い（このプロジェクトでは使えない！）
def register_example_routes(app):
    @app.route('/<store>/example')
    def example_page(store):
        return render_template('example.html', store=store)


# ✅ 正しい（Blueprintパターン）
# routes/example.py
def example_management(store):
    """個別関数として定義"""
    return render_template('example.html', store=store)

# routes/main.py
from .example import example_management
main_routes.add_url_rule('/<store>/example', 'example_management', example_management, methods=['GET'])
```

**原因：** このプロジェクトはBlueprintを使っているため、`app`オブジェクトは直接利用できない  
**解決：** 個別関数として定義し、`main.py`でルート登録する

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
3. **ルートは個別関数で定義し、main.pyでadd_url_rule登録**（`register_XXX_routes(app)`禁止）
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