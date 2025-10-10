# database/reservation_db.py
from datetime import datetime
from typing import List, Dict
from database.connection import get_connection

# =========================
# 予約方法の管理
# =========================

def get_all_reservation_methods(store_id: int) -> List[Dict]:
    """すべての予約方法を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT method_id, store_id, method_name, is_active, display_order, created_at, updated_at
        FROM reservation_methods
        WHERE store_id = %s
        ORDER BY display_order ASC
    """, (store_id,))
    
    columns = [desc[0] for desc in cursor.description]
    methods = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return methods

def add_reservation_method(store_id: int, method_name: str, is_active: bool = True) -> int:
    """予約方法を追加"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
        FROM reservation_methods
        WHERE store_id = %s
    """, (store_id,))
    
    result = cursor.fetchone()
    next_order = result[0] if result else 1
    
    cursor.execute("""
        INSERT INTO reservation_methods (store_id, method_name, is_active, display_order)
        VALUES (%s, %s, %s, %s)
        RETURNING method_id
    """, (store_id, method_name, is_active, next_order))
    
    method_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    return method_id

def update_reservation_method(method_id: int, method_name: str, is_active: bool) -> bool:
    """予約方法を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE reservation_methods
        SET method_name = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
        WHERE method_id = %s
    """, (method_name, is_active, method_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_reservation_method(method_id: int) -> bool:
    """予約方法を削除"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM reservation_methods WHERE method_id = %s", (method_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def reorder_reservation_methods(store_id: int, method_ids: List[int]) -> bool:
    """予約方法の表示順序を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for order, method_id in enumerate(method_ids, start=1):
            cursor.execute("""
                UPDATE reservation_methods
                SET display_order = %s, updated_at = CURRENT_TIMESTAMP
                WHERE method_id = %s AND store_id = %s
            """, (order, method_id, store_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error reordering methods: {e}")
        return False
    finally:
        conn.close()

# =========================
# キャンセル理由の管理
# =========================

def get_all_cancellation_reasons(store_id: int) -> List[Dict]:
    """すべてのキャンセル理由を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT reason_id, store_id, reason_name, is_active, display_order, created_at, updated_at
        FROM cancellation_reasons
        WHERE store_id = %s
        ORDER BY display_order ASC
    """, (store_id,))
    
    columns = [desc[0] for desc in cursor.description]
    reasons = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return reasons

def add_cancellation_reason(store_id: int, reason_text: str, is_active: bool = True) -> int:
    """キャンセル理由を追加"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
        FROM cancellation_reasons
        WHERE store_id = %s
    """, (store_id,))
    
    result = cursor.fetchone()
    next_order = result[0] if result else 1
    
    cursor.execute("""
        INSERT INTO cancellation_reasons (store_id, reason_name, is_active, display_order)
        VALUES (%s, %s, %s, %s)
        RETURNING reason_id
    """, (store_id, reason_text, is_active, next_order))
    
    reason_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    return reason_id

def update_cancellation_reason(reason_id: int, reason_name: str = None, is_active: bool = None) -> bool:
    """キャンセル理由を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 更新する項目を動的に構築
    updates = []
    params = []
    
    if reason_name is not None:
        updates.append("reason_name = %s")
        params.append(reason_name)
    
    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(reason_id)
    
    query = f"""
        UPDATE cancellation_reasons
        SET {', '.join(updates)}
        WHERE reason_id = %s
    """
    
    cursor.execute(query, params)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_cancellation_reason(reason_id: int) -> bool:
    """キャンセル理由を削除"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cancellation_reasons WHERE reason_id = %s", (reason_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def reorder_cancellation_reasons(store_id: int, reason_ids: List[int]) -> bool:
    """キャンセル理由の表示順序を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for order, reason_id in enumerate(reason_ids, start=1):
            cursor.execute("""
                UPDATE cancellation_reasons
                SET display_order = %s, updated_at = CURRENT_TIMESTAMP
                WHERE reason_id = %s AND store_id = %s
            """, (order, reason_id, store_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error reordering reasons: {e}")
        return False
    finally:
        conn.close()