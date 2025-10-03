import psycopg
from psycopg.rows import dict_row
from database.db_connection import get_db_connection

def get_all_parking_lots():
    """全駐車場を取得"""
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT * FROM parking_lots 
            WHERE is_active = TRUE
            ORDER BY display_order, parking_id
        """)
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error in get_all_parking_lots: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_parking_lot(parking_id):
    """特定の駐車場を取得"""
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT * FROM parking_lots 
            WHERE parking_id = %s AND is_active = TRUE
        """, (parking_id,))
        result = cur.fetchone()
        return dict(result) if result else None
    except Exception as e:
        print(f"Error in get_parking_lot: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def create_parking_lot(parking_name, display_order=0):
    """駐車場を新規作成"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO parking_lots (parking_name, display_order)
            VALUES (%s, %s)
            RETURNING parking_id
        """, (parking_name, display_order))
        
        parking_id = cur.fetchone()[0]
        conn.commit()
        return parking_id
    except Exception as e:
        conn.rollback()
        print(f"Error in create_parking_lot: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def update_parking_lot(parking_id, parking_name=None, display_order=None):
    """駐車場情報を更新"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if parking_name is not None:
            updates.append("parking_name = %s")
            params.append(parking_name)
        
        if display_order is not None:
            updates.append("display_order = %s")
            params.append(display_order)
        
        if not updates:
            return True
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(parking_id)
        
        sql = f"""
            UPDATE parking_lots 
            SET {', '.join(updates)}
            WHERE parking_id = %s
        """
        
        cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error in update_parking_lot: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def delete_parking_lot(parking_id):
    """駐車場を削除（論理削除）"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE parking_lots 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE parking_id = %s
        """, (parking_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error in delete_parking_lot: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_parking_enabled():
    """駐車場機能が有効かどうか"""
    from database.settings_db import get_setting
    return get_setting('parking_enabled') == 'true'