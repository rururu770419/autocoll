# -*- coding: utf-8 -*-
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

from database.connection import get_db
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

def get_db_connection(store_code):
    """データベース接続を取得"""
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname='pickup_system',  # 固定
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'diary8475ftkb')
    )
    return conn

# ==========================
# コース管理関数
# ==========================

def get_all_courses(db=None):
    """全コースをJOINでカテゴリ名付きで取得"""
    try:
        if db is None:
            db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                c.course_id, 
                c.name, 
                c.category_id,
                cc.category_name,
                c.time_minutes, 
                c.price, 
                c.cast_back_amount, 
                c.sort_order, 
                c.is_active,
                c.created_at,
                c.updated_at
            FROM courses c 
            LEFT JOIN course_categories cc ON c.category_id = cc.category_id
            ORDER BY c.sort_order ASC, c.course_id ASC
        """)
        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"コース一覧取得エラー: {e}")
        return []

def get_course_by_id(course_id, db=None):
    """特定のコースを取得"""
    try:
        if db is None:
            db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                c.course_id, 
                c.name, 
                c.category_id,
                cc.category_name,
                c.time_minutes, 
                c.price, 
                c.cast_back_amount, 
                c.sort_order, 
                c.is_active
            FROM courses c 
            LEFT JOIN course_categories cc ON c.category_id = cc.category_id
            WHERE c.course_id = %s
        """, (course_id,))
        result = cursor.fetchone()
        return result if result else None
    except Exception as e:
        print(f"コース取得エラー (course_id: {course_id}): {e}")
        return None

def add_course(name, category_id, time_minutes, price=None, cast_back_amount=None, is_active=True, store_id=1):
    """新しいコースを追加"""
    try:
        db = get_db()
        if db is None:
            print("データベース接続エラー")
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) as max_sort FROM courses WHERE store_id = %s", (store_id,))
        result = cursor.fetchone()
        
        if result:
            next_order = (result['max_sort'] if result['max_sort'] is not None else 0) + 1
        else:
            next_order = 1
        
        print(f"コース追加: {name}, カテゴリID: {category_id}, 並び順: {next_order}")
        
        cursor.execute("""
            INSERT INTO courses (name, category_id, time_minutes, price, cast_back_amount, sort_order, store_id, is_active, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (name, category_id, time_minutes, price, cast_back_amount, next_order, store_id, is_active))
        
        db.commit()
        print(f"コース追加成功: {name}")
        return True
    except Exception as e:
        print(f"コース追加エラー - 詳細: {e}")
        print(f"エラータイプ: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

def update_course(course_id, name, category_id, time_minutes, price=None, cast_back_amount=None, is_active=True):
    """コース情報を更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("""
            UPDATE courses 
            SET name = %s, category_id = %s, time_minutes = %s, price = %s, cast_back_amount = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE course_id = %s
        """, (name, category_id, time_minutes, price, cast_back_amount, is_active, course_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"コース更新エラー: {e}")
        return False

def delete_course(course_id):
    """コースを削除"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"コース削除エラー: {e}")
        return False

def move_course_up(course_id):
    """コースの並び順を上に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order, store_id FROM courses WHERE course_id = %s", (course_id,))
        current_course = cursor.fetchone()
        if not current_course:
            return False
        
        current_order = current_course['sort_order']
        store_id = current_course['store_id']
        
        cursor.execute("""
            SELECT course_id, sort_order FROM courses 
            WHERE sort_order < %s AND store_id = %s 
            ORDER BY sort_order DESC LIMIT 1
        """, (current_order, store_id))
        upper_course = cursor.fetchone()
        
        if upper_course:
            upper_course_id = upper_course['course_id']
            upper_order = upper_course['sort_order']
            
            cursor.execute("UPDATE courses SET sort_order = %s WHERE course_id = %s", (upper_order, course_id))
            cursor.execute("UPDATE courses SET sort_order = %s WHERE course_id = %s", (current_order, upper_course_id))
            db.commit()
            print(f"コース並び順上移動成功: course_id {course_id}")
            return True
        return False
    except Exception as e:
        print(f"コース並び順上移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def move_course_down(course_id):
    """コースの並び順を下に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order, store_id FROM courses WHERE course_id = %s", (course_id,))
        current_course = cursor.fetchone()
        if not current_course:
            return False
        
        current_order = current_course['sort_order']
        store_id = current_course['store_id']
        
        cursor.execute("""
            SELECT course_id, sort_order FROM courses 
            WHERE sort_order > %s AND store_id = %s 
            ORDER BY sort_order ASC LIMIT 1
        """, (current_order, store_id))
        lower_course = cursor.fetchone()
        
        if lower_course:
            lower_course_id = lower_course['course_id']
            lower_order = lower_course['sort_order']
            
            cursor.execute("UPDATE courses SET sort_order = %s WHERE course_id = %s", (lower_order, course_id))
            cursor.execute("UPDATE courses SET sort_order = %s WHERE course_id = %s", (current_order, lower_course_id))
            db.commit()
            print(f"コース並び順下移動成功: course_id {course_id}")
            return True
        return False
    except Exception as e:
        print(f"コース並び順下移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==========================
# コースカテゴリ管理関数
# ==========================

def get_all_course_categories():
    """全コースカテゴリを取得"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("SELECT category_id, category_name, sort_order, is_active FROM course_categories ORDER BY sort_order ASC, category_id ASC")
        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"コースカテゴリ一覧取得エラー: {e}")
        return []

def get_course_category_by_id(category_id):
    """特定のコースカテゴリを取得"""
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        cursor.execute("SELECT category_id, category_name, sort_order, is_active FROM course_categories WHERE category_id = %s", (category_id,))
        result = cursor.fetchone()
        return result if result else None
    except Exception as e:
        print(f"コースカテゴリ取得エラー (category_id: {category_id}): {e}")
        return None

def add_course_category(category_name, is_active=True, store_id=1):
    """新しいコースカテゴリを追加"""
    try:
        db = get_db()
        if db is None:
            print("データベース接続エラー")
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) as max_sort FROM course_categories WHERE store_id = %s", (store_id,))
        result = cursor.fetchone()
        
        if result:
            next_order = (result['max_sort'] if result['max_sort'] is not None else 0) + 1
        else:
            next_order = 1
        
        print(f"カテゴリ追加: {category_name}, 並び順: {next_order}")
        
        cursor.execute("INSERT INTO course_categories (category_name, sort_order, is_active, store_id) VALUES (%s, %s, %s, %s)", 
                      (category_name, next_order, is_active, store_id))
        db.commit()
        
        print(f"カテゴリ追加成功: {category_name}")
        return True
    except Exception as e:
        print(f"コースカテゴリ追加エラー - 詳細: {e}")
        print(f"エラータイプ: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

def update_course_category(category_id, category_name, is_active=True):
    """コースカテゴリを更新"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("UPDATE course_categories SET category_name = %s, is_active = %s WHERE category_id = %s", (category_name, is_active, category_id))
        db.commit()
        return True
    except Exception as e:
        print(f"コースカテゴリ更新エラー: {e}")
        return False

def delete_course_category(category_id):
    """コースカテゴリを削除"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        cursor.execute("DELETE FROM course_categories WHERE category_id = %s", (category_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"コースカテゴリ削除エラー: {e}")
        return False

def move_course_category_up(category_id):
    """コースカテゴリの並び順を上に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order, store_id FROM course_categories WHERE category_id = %s", (category_id,))
        current_category = cursor.fetchone()
        if not current_category:
            return False
        
        current_order = current_category['sort_order']
        store_id = current_category['store_id']
        
        cursor.execute("""
            SELECT category_id, sort_order FROM course_categories 
            WHERE sort_order < %s AND store_id = %s 
            ORDER BY sort_order DESC LIMIT 1
        """, (current_order, store_id))
        upper_category = cursor.fetchone()
        
        if upper_category:
            upper_category_id = upper_category['category_id']
            upper_order = upper_category['sort_order']
            
            cursor.execute("UPDATE course_categories SET sort_order = %s WHERE category_id = %s", (upper_order, category_id))
            cursor.execute("UPDATE course_categories SET sort_order = %s WHERE category_id = %s", (current_order, upper_category_id))
            db.commit()
            print(f"コースカテゴリ並び順上移動成功: category_id {category_id}")
            return True
        return False
    except Exception as e:
        print(f"コースカテゴリ並び順上移動エラー: {e}")
        return False

def move_course_category_down(category_id):
    """コースカテゴリの並び順を下に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order, store_id FROM course_categories WHERE category_id = %s", (category_id,))
        current_category = cursor.fetchone()
        if not current_category:
            return False
        
        current_order = current_category['sort_order']
        store_id = current_category['store_id']
        
        cursor.execute("""
            SELECT category_id, sort_order FROM course_categories 
            WHERE sort_order > %s AND store_id = %s 
            ORDER BY sort_order ASC LIMIT 1
        """, (current_order, store_id))
        lower_category = cursor.fetchone()
        
        if lower_category:
            lower_category_id = lower_category['category_id']
            lower_order = lower_category['sort_order']
            
            cursor.execute("UPDATE course_categories SET sort_order = %s WHERE category_id = %s", (lower_order, category_id))
            cursor.execute("UPDATE course_categories SET sort_order = %s WHERE category_id = %s", (current_order, lower_category_id))
            db.commit()
            print(f"コースカテゴリ並び順下移動成功: category_id {category_id}")
            return True
        return False
    except Exception as e:
        print(f"コースカテゴリ並び順下移動エラー: {e}")
        return False

def find_course_category_by_name(category_name, store_id=1):
    """カテゴリ名でコースカテゴリを検索"""
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor()
        cursor.execute("SELECT category_id, category_name, sort_order, is_active FROM course_categories WHERE category_name = %s AND store_id = %s", (category_name, store_id))
        result = cursor.fetchone()
        return result if result else None
    except Exception as e:
        print(f"コースカテゴリ名検索エラー: {e}")
        return None

def get_courses_by_category(category_id):
    """特定カテゴリのコース一覧を取得"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                c.course_id, 
                c.name, 
                c.category_id,
                cc.category_name,
                c.time_minutes, 
                c.price, 
                c.cast_back_amount, 
                c.sort_order, 
                c.is_active
            FROM courses c 
            LEFT JOIN course_categories cc ON c.category_id = cc.category_id
            WHERE c.category_id = %s AND c.is_active = true
            ORDER BY c.sort_order ASC, c.course_id ASC
        """, (category_id,))
        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"カテゴリ別コース取得エラー (category_id: {category_id}): {e}")
        return []