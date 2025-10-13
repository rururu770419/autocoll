from database.connection import get_db

# ==== 割引マスタ管理関数 ====

def get_all_discounts(db, store_id=None, active_only=False):
    """割引マスタ一覧を取得（並び順でソート）"""
    cursor = db.cursor()
    
    query = "SELECT * FROM discounts WHERE 1=1"
    params = []
    
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    
    if active_only:
        query += " AND is_active = TRUE"
    
    query += " ORDER BY sort_order ASC, discount_id ASC"
    
    cursor.execute(query, params)
    return cursor.fetchall()

def get_discount_by_id(db, discount_id):
    """特定の割引マスタを取得"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM discounts WHERE discount_id = %s", (discount_id,))
    return cursor.fetchone()

def find_discount_by_name(db, name, store_id=None):
    """名前で割引マスタを検索"""
    cursor = db.cursor()
    if store_id:
        cursor.execute(
            "SELECT * FROM discounts WHERE name = %s AND store_id = %s", 
            (name, store_id)
        )
    else:
        cursor.execute("SELECT * FROM discounts WHERE name = %s", (name,))
    return cursor.fetchone()

def register_discount(db, discount_data):
    """新しい割引マスタを登録"""
    try:
        cursor = db.cursor()
        
        # 最大のsort_orderを取得
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) as max_order FROM discounts")
        result = cursor.fetchone()
        next_order = result.max_order + 1 if result else 1
        
        cursor.execute("""
            INSERT INTO discounts (
                name, discount_type, value, is_active, store_id,
                sort_order, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING discount_id
        """, (
            discount_data['name'],
            discount_data['discount_type'],
            discount_data['value'],
            discount_data.get('is_active', True),
            discount_data.get('store_id', 1),
            next_order
        ))
        
        result = cursor.fetchone()
        if result:
            new_discount_id = result.discount_id
            db.commit()
            return new_discount_id
        else:
            db.rollback()
            return False
        
    except Exception as e:
        print(f"割引マスタ登録エラー: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

def update_discount(db, discount_id, discount_data):
    """割引マスタを更新"""
    try:
        cursor = db.cursor()
        
        update_fields = []
        params = []
        
        # 更新するフィールド
        for field in ['name', 'discount_type', 'value', 'is_active']:
            if field in discount_data:
                update_fields.append(f"{field} = %s")
                params.append(discount_data[field])
        
        # 更新日時
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # discount_idを最後に追加
        params.append(discount_id)
        
        if update_fields:
            query = f"UPDATE discounts SET {', '.join(update_fields)} WHERE discount_id = %s"
            cursor.execute(query, params)
            db.commit()
            return True
        
        return False
        
    except Exception as e:
        print(f"割引マスタ更新エラー: {e}")
        db.rollback()
        return False

def move_discount_order(db, discount_id, direction):
    """
    割引の並び順を変更
    
    Args:
        db: データベース接続
        discount_id: 移動する割引のID
        direction: 'up'（上へ）または 'down'（下へ）
    
    Returns:
        bool: 成功したらTrue
    """
    try:
        cursor = db.cursor()
        
        # 現在の割引を取得
        cursor.execute("""
            SELECT discount_id, sort_order 
            FROM discounts 
            WHERE discount_id = %s
        """, (discount_id,))
        current = cursor.fetchone()
        
        if not current:
            return False
        
        # 交換先の割引を取得
        if direction == 'up':
            # より小さいsort_orderの中で最大のものを取得
            cursor.execute("""
                SELECT discount_id, sort_order 
                FROM discounts 
                WHERE sort_order < %s 
                ORDER BY sort_order DESC 
                LIMIT 1
            """, (current.sort_order,))
        else:  # down
            # より大きいsort_orderの中で最小のものを取得
            cursor.execute("""
                SELECT discount_id, sort_order 
                FROM discounts 
                WHERE sort_order > %s 
                ORDER BY sort_order ASC 
                LIMIT 1
            """, (current.sort_order,))
        
        target = cursor.fetchone()
        
        if not target:
            # 交換先がない（既に最上位または最下位）
            return False
        
        # sort_orderを交換
        cursor.execute("""
            UPDATE discounts 
            SET sort_order = %s 
            WHERE discount_id = %s
        """, (target.sort_order, current.discount_id))
        
        cursor.execute("""
            UPDATE discounts 
            SET sort_order = %s 
            WHERE discount_id = %s
        """, (current.sort_order, target.discount_id))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"並び順変更エラー: {e}")
        db.rollback()
        return False

def delete_discount(db, discount_id):
    """割引マスタを無効化（論理削除）"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE discounts 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE discount_id = %s
        """, (discount_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"割引マスタ削除エラー: {e}")
        db.rollback()
        return False

def is_discount_used(db, discount_id):
    """割引が予約で使用されているかチェック"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM reservation_discounts
        WHERE discount_id = %s
    """, (discount_id,))
    result = cursor.fetchone()
    return result.count > 0 if result else False

def delete_discount_permanently(db, discount_id):
    """割引マスタを完全削除（予約で未使用の場合のみ）"""
    try:
        # 使用チェック
        if is_discount_used(db, discount_id):
            return False
        
        cursor = db.cursor()
        cursor.execute("DELETE FROM discounts WHERE discount_id = %s", (discount_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"割引マスタ削除エラー: {e}")
        db.rollback()
        return False

def calculate_discount_amount(discount, course_price):
    """
    割引金額を計算
    
    Args:
        discount: 割引マスタレコード
        course_price: コース料金
    
    Returns:
        int: 割引金額
    """
    if discount.discount_type == 'fixed':
        # 固定金額割引
        return min(int(discount.value), course_price)
    elif discount.discount_type == 'percent':
        # パーセント割引
        return int(course_price * (discount.value / 100))
    return 0

# ==== 予約-割引関連関数 ====

def add_discount_to_reservation(db, reservation_id, discount_id, applied_value):
    """予約に割引を適用"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO reservation_discounts (
                reservation_id, discount_id, applied_value, created_at
            ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (reservation_id, discount_id, applied_value))
        db.commit()
        return True
    except Exception as e:
        print(f"予約割引適用エラー: {e}")
        db.rollback()
        return False

def get_reservation_discounts(db, reservation_id):
    """予約に適用された割引一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT rd.*, d.name, d.discount_type, d.value
        FROM reservation_discounts rd
        JOIN discounts d ON rd.discount_id = d.discount_id
        WHERE rd.reservation_id = %s
        ORDER BY rd.created_at
    """, (reservation_id,))
    return cursor.fetchall()

def remove_discount_from_reservation(db, reservation_id, discount_id):
    """予約から割引を削除"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM reservation_discounts 
            WHERE reservation_id = %s AND discount_id = %s
        """, (reservation_id, discount_id))
        db.commit()
        return True
    except Exception as e:
        print(f"予約割引削除エラー: {e}")
        db.rollback()
        return False