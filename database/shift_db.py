# -*- coding: utf-8 -*-
"""
シフト種別・シフト登録関連のデータベース操作
"""

from database.connection import get_db
import psycopg
from psycopg.rows import dict_row

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シフト種別マスタ関連
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_all_shift_types():
    """全シフト種別を取得（並び順）"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT shift_type_id, shift_name, is_work_day, color, sort_order, is_active
            FROM shift_types
            WHERE is_active = TRUE
            ORDER BY sort_order ASC, shift_type_id ASC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_all_shift_types: {e}")
        return []


def get_shift_type_by_id(shift_type_id):
    """特定のシフト種別を取得"""
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT shift_type_id, shift_name, is_work_day, color, sort_order, is_active
            FROM shift_types
            WHERE shift_type_id = %s
        """, (shift_type_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error in get_shift_type_by_id: {e}")
        return None


def create_shift_type(shift_name, is_work_day=True, color='#808080'):
    """新しいシフト種別を追加"""
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        
        # 最大のsort_orderを取得
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 as next_order FROM shift_types")
        result = cursor.fetchone()
        sort_order = result['next_order']
        
        # 挿入
        cursor.execute("""
            INSERT INTO shift_types (shift_name, is_work_day, color, sort_order)
            VALUES (%s, %s, %s, %s)
            RETURNING shift_type_id
        """, (shift_name, is_work_day, color, sort_order))
        
        db.commit()
        result = cursor.fetchone()
        return result['shift_type_id']
    except Exception as e:
        print(f"Error in create_shift_type: {e}")
        if db:
            db.rollback()
        return None


def update_shift_type(shift_type_id, shift_name=None, is_work_day=None, color=None):
    """シフト種別を更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        # 更新するフィールドを動的に構築
        updates = []
        params = []
        
        if shift_name is not None:
            updates.append("shift_name = %s")
            params.append(shift_name)
        
        if is_work_day is not None:
            updates.append("is_work_day = %s")
            params.append(is_work_day)
        
        if color is not None:
            updates.append("color = %s")
            params.append(color)
        
        if not updates:
            return False
        
        params.append(shift_type_id)
        
        query = f"UPDATE shift_types SET {', '.join(updates)} WHERE shift_type_id = %s"
        cursor.execute(query, params)
        db.commit()
        
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error in update_shift_type: {e}")
        if db:
            db.rollback()
        return False


def delete_shift_type(shift_type_id):
    """シフト種別を削除（論理削除）"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            UPDATE shift_types
            SET is_active = FALSE
            WHERE shift_type_id = %s
        """, (shift_type_id,))
        
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error in delete_shift_type: {e}")
        if db:
            db.rollback()
        return False


def move_shift_type_order(shift_type_id, direction):
    """シフト種別の並び順を変更"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        # 現在の並び順を取得
        cursor.execute("""
            SELECT shift_type_id, sort_order
            FROM shift_types
            WHERE shift_type_id = %s AND is_active = TRUE
        """, (shift_type_id,))
        
        current = cursor.fetchone()
        if not current:
            return False
        
        current_order = current['sort_order']
        
        # 入れ替え対象を検索
        if direction == 'up':
            cursor.execute("""
                SELECT shift_type_id, sort_order
                FROM shift_types
                WHERE sort_order < %s AND is_active = TRUE
                ORDER BY sort_order DESC
                LIMIT 1
            """, (current_order,))
        else:  # down
            cursor.execute("""
                SELECT shift_type_id, sort_order
                FROM shift_types
                WHERE sort_order > %s AND is_active = TRUE
                ORDER BY sort_order ASC
                LIMIT 1
            """, (current_order,))
        
        target = cursor.fetchone()
        if not target:
            return False
        
        # 入れ替え
        target_id = target['shift_type_id']
        target_order = target['sort_order']
        
        cursor.execute("UPDATE shift_types SET sort_order = %s WHERE shift_type_id = %s", (target_order, shift_type_id))
        cursor.execute("UPDATE shift_types SET sort_order = %s WHERE shift_type_id = %s", (current_order, target_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in move_shift_type_order: {e}")
        if db:
            db.rollback()
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シフト登録関連
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_shifts_by_month(year, month):
    """指定月のシフトを全件取得"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT s.shift_id, s.staff_id, s.shift_date, s.shift_type_id, 
                   s.start_time, s.end_time, s.parking_id, s.memo,
                   st.shift_name, st.is_work_day, st.color,
                   u.name as staff_name, u.role
            FROM shifts s
            LEFT JOIN shift_types st ON s.shift_type_id = st.shift_type_id
            LEFT JOIN users u ON s.staff_id = u.login_id
            WHERE EXTRACT(YEAR FROM s.shift_date) = %s
            AND EXTRACT(MONTH FROM s.shift_date) = %s
            ORDER BY s.shift_date, u.name
        """, (year, month))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_shifts_by_month: {e}")
        return []


def upsert_shift(staff_id, shift_date, shift_type_id, start_time=None, end_time=None, parking_id=None, memo=None):
    """シフトを登録または更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO shifts (staff_id, shift_date, shift_type_id, start_time, end_time, parking_id, memo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (staff_id, shift_date)
            DO UPDATE SET
                shift_type_id = EXCLUDED.shift_type_id,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                parking_id = EXCLUDED.parking_id,
                memo = EXCLUDED.memo
        """, (staff_id, shift_date, shift_type_id, start_time, end_time, parking_id, memo))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in upsert_shift: {e}")
        if db:
            db.rollback()
        return False


def delete_shift(staff_id, shift_date):
    """シフトを削除"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM shifts
            WHERE staff_id = %s AND shift_date = %s
        """, (staff_id, shift_date))
        
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error in delete_shift: {e}")
        if db:
            db.rollback()
        return False


def get_working_staff_by_date(shift_date):
    """指定日の出勤スタッフを取得（駐車場割り当て用）"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT s.staff_id, s.parking_id, u.name as staff_name, st.shift_name
            FROM shifts s
            JOIN users u ON s.staff_id = u.login_id
            JOIN shift_types st ON s.shift_type_id = st.shift_type_id
            WHERE s.shift_date = %s
            AND st.is_work_day = TRUE
            ORDER BY u.name
        """, (shift_date,))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_working_staff_by_date: {e}")
        return []


def update_parking_assignment(staff_id, shift_date, parking_id):
    """駐車場割り当てを更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            UPDATE shifts
            SET parking_id = %s
            WHERE staff_id = %s AND shift_date = %s
        """, (parking_id, staff_id, shift_date))
        
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error in update_parking_assignment: {e}")
        if db:
            db.rollback()
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 日付別備考関連
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_date_memos_by_month(year, month):
    """指定月の日付別備考を取得"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT memo_date, memo_text
            FROM date_memos
            WHERE EXTRACT(YEAR FROM memo_date) = %s
            AND EXTRACT(MONTH FROM memo_date) = %s
            ORDER BY memo_date
        """, (year, month))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_date_memos_by_month: {e}")
        return []


def upsert_date_memo(memo_date, memo_text):
    """日付別備考を登録または更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        # 空文字の場合は削除
        if not memo_text or memo_text.strip() == '':
            cursor.execute("""
                DELETE FROM date_memos
                WHERE memo_date = %s
            """, (memo_date,))
        else:
            cursor.execute("""
                INSERT INTO date_memos (memo_date, memo_text)
                VALUES (%s, %s)
                ON CONFLICT (memo_date)
                DO UPDATE SET
                    memo_text = EXCLUDED.memo_text,
                    updated_at = CURRENT_TIMESTAMP
            """, (memo_date, memo_text))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error in upsert_date_memo: {e}")
        if db:
            db.rollback()
        return False