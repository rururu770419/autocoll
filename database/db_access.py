from database.connection import get_db, close_connection, get_display_name
from database.hotel_db import *
from database.cast_db import *
from database.user_db import *
from database.pickup_db import *
from database.course_db import *
import psycopg
from psycopg.rows import dict_row
import os
from flask import g

# PostgreSQL接続設定を読み込み
from config import DATABASE_CONFIG

# ❌ 削除: find_hotel_by_name_category_area は hotel_db.py にあるので重複

def get_staff_list(db, store_id=None):
    """スタッフ一覧を取得（ダッシュボード用）"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT login_id, name, color FROM users WHERE is_active = true AND store_id = %s ORDER BY name", (store_id,))
    else:
        cursor.execute("SELECT login_id, name, color FROM users WHERE is_active = true ORDER BY name")
    staff = cursor.fetchall()
    return staff

# ==== お知らせ関連の関数 ====

def create_announcements_table(db):
    """お知らせテーブルを作成する（存在しない場合のみ）"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                store_name TEXT NOT NULL,
                content TEXT DEFAULT '',
                is_visible BOOLEAN DEFAULT FALSE
            )
        """)
        db.commit()
        print("お知らせテーブルの確認/作成が完了しました")
    except Exception as e:
        print(f"お知らせテーブル作成エラー: {e}")

def get_announcement(db, store_name):
    """指定した店舗のお知らせを取得する"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, store_name, content, is_visible
            FROM announcements
            WHERE store_name = %s
        """, (store_name,))
        
        announcement = cursor.fetchone()
        
        if not announcement:
            cursor.execute("""
                INSERT INTO announcements (store_name, content, is_visible)
                VALUES (%s, '', FALSE)
                RETURNING id, store_name, content, is_visible
            """, (store_name,))
            db.commit()
            announcement = cursor.fetchone()
        
        return announcement
        
    except Exception as e:
        print(f"お知らせ取得エラー: {e}")
        return None

def update_announcement(db, store_name, field, value):
    """指定した店舗のお知らせを更新する"""
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM announcements
            WHERE store_name = %s
        """, (store_name,))
        
        count_result = cursor.fetchone()
        count = count_result.count
        
        if count == 0:
            cursor.execute("""
                INSERT INTO announcements (store_name, content, is_visible)
                VALUES (%s, '', FALSE)
            """, (store_name,))
            db.commit()
        
        if field not in ['content', 'is_visible']:
            print(f"無効なフィールド名: {field}")
            return False
        
        if field == 'is_visible':
            value = bool(value)
        
        if field == 'content':
            cursor.execute("""
                UPDATE announcements
                SET content = %s
                WHERE store_name = %s
            """, (value, store_name))
        else:
            cursor.execute("""
                UPDATE announcements
                SET is_visible = %s
                WHERE store_name = %s
            """, (value, store_name))
        
        db.commit()
        
        if cursor.rowcount > 0:
            print(f"お知らせ更新成功: {store_name} - {field} = {value}")
            return True
        else:
            print(f"お知らせ更新失敗: 該当レコードが見つかりません")
            return False
            
    except Exception as e:
        print(f"お知らせ更新エラー: {e}")
        return False

def cleanup_old_announcement_records(db, days=30):
    """古いお知らせ記録を自動削除（30日以上前）"""
    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM announcements WHERE announcement_date < CURRENT_DATE - INTERVAL '%s days'", 
            (days,)
        )
        db.commit()
        return True
    except Exception as e:
        print(f"Error in cleanup_old_announcement_records: {e}")
        return False

def cleanup_all_old_records(db):
    """すべての古いレコードを一括削除"""
    try:
        cleanup_old_pickup_records(db, 7)
        cleanup_old_money_records(db, 7)
        cleanup_old_announcement_records(db, 30)
        return True
    except Exception as e:
        print(f"Error in cleanup_all_old_records: {e}")
        return False

def should_run_cleanup(db):
    """クリーンアップが必要かどうかを判定"""
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleanup_log (
                id SERIAL PRIMARY KEY,
                last_cleanup TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM cleanup_log")
        count_result = cursor.fetchone()
        count = count_result.count
        
        if count == 0:
            cursor.execute("""
                INSERT INTO cleanup_log (last_cleanup) 
                VALUES (CURRENT_TIMESTAMP - INTERVAL '2 days')
            """)
            db.commit()
        
        cursor.execute("""
            SELECT COUNT(*) as should_cleanup
            FROM cleanup_log 
            WHERE last_cleanup < CURRENT_TIMESTAMP - INTERVAL '1 day'
            OR last_cleanup IS NULL
        """)
        
        result = cursor.fetchone()
        return result.should_cleanup > 0
        
    except Exception as e:
        print(f"Error in should_run_cleanup: {e}")
        return False

def update_cleanup_timestamp(db):
    """クリーンアップ実行時刻を更新"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cleanup_log 
            SET last_cleanup = CURRENT_TIMESTAMP
        """)
        db.commit()
        return True
    except Exception as e:
        print(f"Error in update_cleanup_timestamp: {e}")
        return False

def auto_cleanup_if_needed(db):
    """必要に応じて自動クリーンアップを実行"""
    try:
        if should_run_cleanup(db):
            print("24時間以上経過しているため、データクリーンアップを実行します...")
            
            cleanup_old_pickup_records(db, 7)
            cleanup_old_money_records(db, 7)
            cleanup_old_announcement_records(db, 30)
            
            update_cleanup_timestamp(db)
            
            print("データクリーンアップが完了しました")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error in auto_cleanup_if_needed: {e}")
        return False

# ==========================
# オプション管理関数
# ==========================

def get_all_options():
    """全オプションを並び順で取得"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT option_id, name, price, cast_back_amount, sort_order, is_active, created_at, updated_at 
            FROM options 
            ORDER BY sort_order ASC, option_id ASC
        """)
        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"オプション一覧取得エラー: {e}")
        return []

def get_option_by_id(option_id):
    """特定のオプションを取得"""
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        cursor.execute("SELECT option_id, name, price, cast_back_amount, sort_order, is_active, created_at, updated_at FROM options WHERE option_id = %s", (option_id,))
        result = cursor.fetchone()
        return result if result else None
    except Exception as e:
        print(f"オプション取得エラー (option_id: {option_id}): {e}")
        return None

def add_option(name, price, cast_back_amount, store_id=1, is_active=True):
    """新しいオプションを追加"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 as next_sort_order FROM options")
        max_sort_result = cursor.fetchone()
        sort_order = max_sort_result['next_sort_order'] if max_sort_result else 1
        
        cursor.execute("""
            INSERT INTO options (name, price, cast_back_amount, sort_order, store_id, is_active, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (name, price, cast_back_amount, sort_order, store_id, is_active))
        
        db.commit()
        return True
    except Exception as e:
        print(f"オプション登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_option(option_id, name, price, cast_back_amount, is_active):
    """オプション情報を更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            UPDATE options 
            SET name = %s, price = %s, cast_back_amount = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE option_id = %s
        """, (name, price, cast_back_amount, is_active, option_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"オプション更新エラー (option_id: {option_id}): {e}")
        return False

def delete_option(option_id):
    """オプションを削除"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("DELETE FROM options WHERE option_id = %s", (option_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"オプション削除エラー (option_id: {option_id}): {e}")
        return False

def move_option_up(option_id):
    """オプションの並び順を上に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        current_option = get_option_by_id(option_id)
        if not current_option:
            return False
        
        current_sort = current_option['sort_order']
        
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT option_id, sort_order 
            FROM options 
            WHERE sort_order < %s 
            ORDER BY sort_order DESC 
            LIMIT 1
        """, (current_sort,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        prev_option_id = result['option_id']
        prev_sort = result['sort_order']
        
        cursor.execute("UPDATE options SET sort_order = %s, updated_at = CURRENT_TIMESTAMP WHERE option_id = %s", (prev_sort, option_id))
        cursor.execute("UPDATE options SET sort_order = %s, updated_at = CURRENT_TIMESTAMP WHERE option_id = %s", (current_sort, prev_option_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"オプション並び順変更エラー (上移動, option_id: {option_id}): {e}")
        return False

def move_option_down(option_id):
    """オプションの並び順を下に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        current_option = get_option_by_id(option_id)
        if not current_option:
            return False
        
        current_sort = current_option['sort_order']
        
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT option_id, sort_order 
            FROM options 
            WHERE sort_order > %s 
            ORDER BY sort_order ASC 
            LIMIT 1
        """, (current_sort,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        next_option_id = result['option_id']
        next_sort = result['sort_order']
        
        cursor.execute("UPDATE options SET sort_order = %s, updated_at = CURRENT_TIMESTAMP WHERE option_id = %s", (next_sort, option_id))
        cursor.execute("UPDATE options SET sort_order = %s, updated_at = CURRENT_TIMESTAMP WHERE option_id = %s", (current_sort, next_option_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"オプション並び順変更エラー (下移動, option_id: {option_id}): {e}")
        return False