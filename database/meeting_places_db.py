# database/meeting_places_db.py
from datetime import datetime
from typing import List, Dict
from database.connection import get_connection

# =========================
# 待ち合わせ場所の管理
# =========================

def get_all_meeting_places(store_id: int) -> List[Dict]:
    """すべての待ち合わせ場所を取得（is_active=trueのみ）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT place_id, store_id, place_name, is_active, display_order, created_at, updated_at
        FROM meeting_places
        WHERE store_id = %s AND is_active = true
        ORDER BY display_order ASC
    """, (store_id,))

    columns = [desc[0] for desc in cursor.description]
    places = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return places

def add_meeting_place(store_id: int, place_name: str, is_active: bool = True) -> int:
    """待ち合わせ場所を追加"""
    conn = get_connection()
    cursor = conn.cursor()

    # 最大のdisplay_orderを取得して+1
    cursor.execute("""
        SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
        FROM meeting_places
        WHERE store_id = %s
    """, (store_id,))

    result = cursor.fetchone()
    next_order = result[0] if result else 1

    # 新規追加
    cursor.execute("""
        INSERT INTO meeting_places (store_id, place_name, is_active, display_order, created_at, updated_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING place_id
    """, (store_id, place_name, is_active, next_order))

    place_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return place_id

def update_meeting_place(place_id: int, place_name: str = None, is_active: bool = None) -> bool:
    """待ち合わせ場所を更新"""
    conn = get_connection()
    cursor = conn.cursor()

    # 更新する項目を動的に構築
    updates = []
    params = []

    if place_name is not None:
        updates.append("place_name = %s")
        params.append(place_name)

    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(place_id)

    query = f"""
        UPDATE meeting_places
        SET {', '.join(updates)}
        WHERE place_id = %s
    """

    cursor.execute(query, params)

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success

def delete_meeting_place(place_id: int) -> bool:
    """待ち合わせ場所を論理削除（is_active = false）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meeting_places
        SET is_active = false, updated_at = CURRENT_TIMESTAMP
        WHERE place_id = %s
    """, (place_id,))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success

def reorder_meeting_places(store_id: int, place_ids: List[int]) -> bool:
    """待ち合わせ場所の表示順序を更新"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for order, place_id in enumerate(place_ids, start=1):
            cursor.execute("""
                UPDATE meeting_places
                SET display_order = %s, updated_at = CURRENT_TIMESTAMP
                WHERE place_id = %s AND store_id = %s
            """, (order, place_id, store_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error reordering meeting places: {e}")
        return False
    finally:
        conn.close()
