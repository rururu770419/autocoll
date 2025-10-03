import json

def get_all_rating_items(db):
    """全ての評価項目を取得（表示順でソート）"""
    try:
        cursor = db.execute("""
            SELECT item_id, item_name, item_type, options, display_order, is_active
            FROM rating_items
            ORDER BY display_order ASC, item_id ASC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_all_rating_items: {e}")
        return []

def add_rating_item(db, item_name, item_type, options_json):
    """新しい評価項目を追加"""
    try:
        # 最大の display_order を取得
        cursor = db.execute("""
            SELECT COALESCE(MAX(display_order), 0) as max_order
            FROM rating_items
        """)
        
        max_order = cursor.fetchone()['max_order']
        new_order = max_order + 1
        
        # 新規項目を挿入
        db.execute("""
            INSERT INTO rating_items 
            (item_name, item_type, options, display_order, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, (item_name, item_type, options_json, new_order, True))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in add_rating_item: {e}")
        db.rollback()
        return False

def update_rating_item(db, item_id, item_name, item_type, options_json, is_active):
    """評価項目を更新"""
    try:
        db.execute("""
            UPDATE rating_items
            SET item_name = %s, item_type = %s, options = %s, is_active = %s
            WHERE item_id = %s
        """, (item_name, item_type, options_json, is_active, item_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in update_rating_item: {e}")
        db.rollback()
        return False

def delete_rating_item(db, item_id):
    """評価項目を削除"""
    try:
        # 削除する項目の display_order を取得
        cursor = db.execute("""
            SELECT display_order
            FROM rating_items
            WHERE item_id = %s
        """, (item_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        deleted_order = row['display_order']
        
        # 項目を削除
        db.execute("DELETE FROM rating_items WHERE item_id = %s", (item_id,))
        
        # 削除した項目より後ろの display_order を詰める
        db.execute("""
            UPDATE rating_items
            SET display_order = display_order - 1
            WHERE display_order > %s
        """, (deleted_order,))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in delete_rating_item: {e}")
        db.rollback()
        return False

def update_item_order(db, item_id, direction):
    """評価項目の表示順を変更（up: 上へ, down: 下へ）"""
    try:
        # 現在の項目情報を取得
        cursor = db.execute("""
            SELECT item_id, display_order
            FROM rating_items
            WHERE item_id = %s
        """, (item_id,))
        
        current_item = cursor.fetchone()
        if not current_item:
            return False
        
        current_order = current_item['display_order']
        
        # 入れ替え対象の項目を取得
        if direction == 'up':
            cursor = db.execute("""
                SELECT item_id, display_order
                FROM rating_items
                WHERE display_order < %s
                ORDER BY display_order DESC
                LIMIT 1
            """, (current_order,))
        else:  # direction == 'down'
            cursor = db.execute("""
                SELECT item_id, display_order
                FROM rating_items
                WHERE display_order > %s
                ORDER BY display_order ASC
                LIMIT 1
            """, (current_order,))
        
        target_item = cursor.fetchone()
        if not target_item:
            return True
        
        target_order = target_item['display_order']
        target_id = target_item['item_id']
        
        # display_order を入れ替え
        db.execute("""
            UPDATE rating_items
            SET display_order = %s
            WHERE item_id = %s
        """, (target_order, item_id))
        
        db.execute("""
            UPDATE rating_items
            SET display_order = %s
            WHERE item_id = %s
        """, (current_order, target_id))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error in update_item_order: {e}")
        db.rollback()
        return False

def get_rating_item_by_id(db, item_id):
    """IDで評価項目を1件取得"""
    try:
        cursor = db.execute("""
            SELECT item_id, item_name, item_type, options, display_order, is_active
            FROM rating_items
            WHERE item_id = %s
        """, (item_id,))
        
        return cursor.fetchone()
    except Exception as e:
        print(f"Error in get_rating_item_by_id: {e}")
        return None