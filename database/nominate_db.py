from database.connection import get_db

# ==== 指名種類マスタ管理関数 ====

def get_all_nomination_types(store_id=None):
    """全指名種類を並び順で取得"""
    try:
        db = get_db()
        if db is None:
            return []

        cursor = db.cursor()

        if store_id:
            cursor.execute("""
                SELECT nomination_type_id, type_name, additional_fee, back_amount,
                       display_order, is_active, created_at, updated_at, store_id
                FROM nomination_types
                WHERE store_id = %s
                ORDER BY display_order ASC, nomination_type_id ASC
            """, (store_id,))
        else:
            cursor.execute("""
                SELECT nomination_type_id, type_name, additional_fee, back_amount,
                       display_order, is_active, created_at, updated_at, store_id
                FROM nomination_types
                ORDER BY display_order ASC, nomination_type_id ASC
            """)

        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"指名種類一覧取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_nomination_type_by_id(nomination_type_id):
    """特定の指名種類を取得"""
    try:
        db = get_db()
        if db is None:
            return None

        cursor = db.cursor()
        cursor.execute("""
            SELECT nomination_type_id, type_name, additional_fee, back_amount,
                   display_order, is_active, created_at, updated_at, store_id
            FROM nomination_types
            WHERE nomination_type_id = %s
        """, (nomination_type_id,))
        result = cursor.fetchone()
        return result if result else None
    except Exception as e:
        print(f"指名種類取得エラー (nomination_type_id: {nomination_type_id}): {e}")
        return None

def add_nomination_type(type_name, additional_fee, back_amount, store_id=1, is_active=True):
    """新しい指名種類を追加"""
    try:
        db = get_db()
        if db is None:
            return False

        cursor = db.cursor()

        # 店舗ごとの最大display_orderを取得
        cursor.execute("""
            SELECT COALESCE(MAX(display_order), 0) + 1 as next_display_order
            FROM nomination_types
            WHERE store_id = %s
        """, (store_id,))
        max_sort_result = cursor.fetchone()
        display_order = max_sort_result['next_display_order'] if max_sort_result else 1

        cursor.execute("""
            INSERT INTO nomination_types
            (type_name, additional_fee, back_amount, display_order, store_id, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (type_name, additional_fee, back_amount, display_order, store_id, is_active))

        db.commit()
        return True
    except Exception as e:
        print(f"指名種類登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_nomination_type(nomination_type_id, type_name, additional_fee, back_amount, is_active):
    """指名種類情報を更新"""
    try:
        db = get_db()
        if db is None:
            return False

        cursor = db.cursor()
        cursor.execute("""
            UPDATE nomination_types
            SET type_name = %s, additional_fee = %s, back_amount = %s, is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE nomination_type_id = %s
        """, (type_name, additional_fee, back_amount, is_active, nomination_type_id))

        db.commit()
        return True
    except Exception as e:
        print(f"指名種類更新エラー (nomination_type_id: {nomination_type_id}): {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_nomination_type(nomination_type_id):
    """指名種類を削除"""
    try:
        db = get_db()
        if db is None:
            return False

        cursor = db.cursor()
        cursor.execute("DELETE FROM nomination_types WHERE nomination_type_id = %s", (nomination_type_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"指名種類削除エラー (nomination_type_id: {nomination_type_id}): {e}")
        return False

def move_nomination_type_up(nomination_type_id):
    """指名種類の並び順を上に移動"""
    try:
        db = get_db()
        if db is None:
            return False

        current_nomination = get_nomination_type_by_id(nomination_type_id)
        if not current_nomination:
            return False

        current_display_order = current_nomination['display_order']
        current_store_id = current_nomination['store_id']

        cursor = db.cursor()

        # 同じ店舗内で一つ上の並び順を取得
        cursor.execute("""
            SELECT nomination_type_id, display_order
            FROM nomination_types
            WHERE display_order < %s AND store_id = %s
            ORDER BY display_order DESC
            LIMIT 1
        """, (current_display_order, current_store_id))
        result = cursor.fetchone()

        if not result:
            return False

        prev_nomination_id = result['nomination_type_id']
        prev_display_order = result['display_order']

        # 並び順を入れ替え
        cursor.execute("""
            UPDATE nomination_types
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE nomination_type_id = %s
        """, (prev_display_order, nomination_type_id))

        cursor.execute("""
            UPDATE nomination_types
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE nomination_type_id = %s
        """, (current_display_order, prev_nomination_id))

        db.commit()
        return True
    except Exception as e:
        print(f"指名種類並び順変更エラー (上移動, nomination_type_id: {nomination_type_id}): {e}")
        import traceback
        traceback.print_exc()
        return False

def move_nomination_type_down(nomination_type_id):
    """指名種類の並び順を下に移動"""
    try:
        db = get_db()
        if db is None:
            return False

        current_nomination = get_nomination_type_by_id(nomination_type_id)
        if not current_nomination:
            return False

        current_display_order = current_nomination['display_order']
        current_store_id = current_nomination['store_id']

        cursor = db.cursor()

        # 同じ店舗内で一つ下の並び順を取得
        cursor.execute("""
            SELECT nomination_type_id, display_order
            FROM nomination_types
            WHERE display_order > %s AND store_id = %s
            ORDER BY display_order ASC
            LIMIT 1
        """, (current_display_order, current_store_id))
        result = cursor.fetchone()

        if not result:
            return False

        next_nomination_id = result['nomination_type_id']
        next_display_order = result['display_order']

        # 並び順を入れ替え
        cursor.execute("""
            UPDATE nomination_types
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE nomination_type_id = %s
        """, (next_display_order, nomination_type_id))

        cursor.execute("""
            UPDATE nomination_types
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE nomination_type_id = %s
        """, (current_display_order, next_nomination_id))

        db.commit()
        return True
    except Exception as e:
        print(f"指名種類並び順変更エラー (下移動, nomination_type_id: {nomination_type_id}): {e}")
        import traceback
        traceback.print_exc()
        return False
