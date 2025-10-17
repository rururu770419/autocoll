from database.connection import get_db

# ==== 延長マスタ管理関数 ====

def get_all_extensions(db, store_id=None, active_only=False):
    """延長マスタ一覧を取得（並び順でソート）"""
    cursor = db.cursor()

    query = "SELECT * FROM extensions WHERE 1=1"
    params = []

    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)

    if active_only:
        query += " AND is_active = TRUE"

    query += " ORDER BY sort_order ASC, extension_id ASC"

    cursor.execute(query, params)
    return cursor.fetchall()

def get_extension_by_id(db, extension_id):
    """特定の延長マスタを取得"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM extensions WHERE extension_id = %s", (extension_id,))
    return cursor.fetchone()

def find_extension_by_name(db, name, store_id=None):
    """名前で延長マスタを検索"""
    cursor = db.cursor()
    if store_id:
        cursor.execute(
            "SELECT * FROM extensions WHERE extension_name = %s AND store_id = %s",
            (name, store_id)
        )
    else:
        cursor.execute("SELECT * FROM extensions WHERE extension_name = %s", (name,))
    return cursor.fetchone()

def register_extension(db, extension_data):
    """新しい延長マスタを登録"""
    cursor = None
    try:
        cursor = db.cursor()

        # 重複チェック
        existing = find_extension_by_name(db, extension_data['extension_name'], extension_data.get('store_id'))
        if existing:
            print(f"延長マスタ登録エラー: 延長名「{extension_data['extension_name']}」は既に登録されています")
            return False

        # 最大のsort_orderを取得
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) as max_order FROM extensions WHERE store_id = %s",
                      (extension_data.get('store_id', 1),))
        result = cursor.fetchone()
        next_order = result['max_order'] + 1 if result else 1

        cursor.execute("""
            INSERT INTO extensions (
                extension_name, extension_minutes, extension_fee, back_amount,
                is_active, store_id, sort_order, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING extension_id
        """, (
            extension_data['extension_name'],
            extension_data['extension_minutes'],
            extension_data['extension_fee'],
            extension_data['back_amount'],
            extension_data.get('is_active', True),
            extension_data.get('store_id', 1),
            next_order
        ))

        result = cursor.fetchone()
        print(f"INSERT結果: {result}")  # デバッグ用
        if result and 'extension_id' in result:
            new_extension_id = result['extension_id']
            print(f"登録成功: extension_id={new_extension_id}")  # デバッグ用
            return new_extension_id
        else:
            print(f"登録失敗: resultがNoneまたはextension_idが含まれていません")
            return False

    except Exception as e:
        print(f"延長マスタ登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_extension(db, extension_id, extension_data):
    """延長マスタを更新"""
    try:
        cursor = db.cursor()

        update_fields = []
        params = []

        # 更新するフィールド
        for field in ['extension_name', 'extension_minutes', 'extension_fee', 'back_amount', 'is_active']:
            if field in extension_data:
                update_fields.append(f"{field} = %s")
                params.append(extension_data[field])

        # 更新日時
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        # extension_idを最後に追加
        params.append(extension_id)

        if update_fields:
            query = f"UPDATE extensions SET {', '.join(update_fields)} WHERE extension_id = %s"
            cursor.execute(query, params)
            db.commit()
            return True

        return False

    except Exception as e:
        print(f"延長マスタ更新エラー: {e}")
        db.rollback()
        return False

def move_extension_order(db, extension_id, direction):
    """
    延長の並び順を変更

    Args:
        db: データベース接続
        extension_id: 移動する延長のID
        direction: 'up'（上へ）または 'down'（下へ）

    Returns:
        bool: 成功したらTrue
    """
    try:
        cursor = db.cursor()

        # 現在の延長を取得
        cursor.execute("""
            SELECT extension_id, sort_order, store_id
            FROM extensions
            WHERE extension_id = %s
        """, (extension_id,))
        current = cursor.fetchone()

        if not current:
            return False

        # 交換先の延長を取得（同じstore_id内で）
        if direction == 'up':
            # より小さいsort_orderの中で最大のものを取得
            cursor.execute("""
                SELECT extension_id, sort_order
                FROM extensions
                WHERE sort_order < %s AND store_id = %s
                ORDER BY sort_order DESC
                LIMIT 1
            """, (current['sort_order'], current['store_id']))
        else:  # down
            # より大きいsort_orderの中で最小のものを取得
            cursor.execute("""
                SELECT extension_id, sort_order
                FROM extensions
                WHERE sort_order > %s AND store_id = %s
                ORDER BY sort_order ASC
                LIMIT 1
            """, (current['sort_order'], current['store_id']))

        target = cursor.fetchone()

        if not target:
            # 交換先がない（既に最上位または最下位）
            return False

        # sort_orderを交換
        cursor.execute("""
            UPDATE extensions
            SET sort_order = %s
            WHERE extension_id = %s
        """, (target['sort_order'], current['extension_id']))

        cursor.execute("""
            UPDATE extensions
            SET sort_order = %s
            WHERE extension_id = %s
        """, (current['sort_order'], target['extension_id']))

        db.commit()
        return True

    except Exception as e:
        print(f"並び順変更エラー: {e}")
        db.rollback()
        return False

def delete_extension_permanently(db, extension_id):
    """延長マスタを完全削除"""
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM extensions WHERE extension_id = %s", (extension_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"延長マスタ削除エラー: {e}")
        db.rollback()
        return False
