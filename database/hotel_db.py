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

# ==== カテゴリ関連の関数 ====
def get_all_categories(db):
    """データベースから全てのカテゴリ情報を取得"""
    cursor = db.cursor()
    cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    return categories

def register_category(db, name):
    """新しいカテゴリをデータベースに登録"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COALESCE(MAX(category_id), 0) + 1 as next_id FROM categories")
        result = cursor.fetchone()
        new_category_id = result['next_id']
        
        cursor.execute("INSERT INTO categories (category_id, name) VALUES (%s, %s)", (new_category_id, name))
        db.commit()
        return True  # ✅ 追加
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"カテゴリ登録エラー: {e}")
        return False

def find_category_by_id(db, category_id):
    """IDでカテゴリを検索"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
    category = cursor.fetchone()
    return category if category else None

def find_category_by_name(db, name):
    """名前でカテゴリを検索（重複チェック用）"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM categories WHERE name = %s", (name,))
    category = cursor.fetchone()
    return category if category else None

def update_category(db, category_id, name):
    """カテゴリ情報を更新"""
    try:
        cursor = db.cursor()
        cursor.execute("UPDATE categories SET name = %s WHERE category_id = %s", (name, category_id))
        db.commit()
        return True  # ✅ 追加
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"カテゴリ更新エラー: {e}")
        return False

def delete_category_by_id(db, category_id):
    """IDでカテゴリを削除"""
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"カテゴリ削除エラー: {e}")
        return False

# ==== エリア関連の関数 ====
def get_all_areas(db):
    """データベースから全てのエリア情報を取得（交通費・所要時間含む）"""
    cursor = db.cursor()
    cursor.execute("SELECT area_id, name, transportation_fee, travel_time_minutes, sort_order FROM areas ORDER BY sort_order ASC, name")
    areas = cursor.fetchall()
    return areas

def register_area(db, name, transportation_fee=0, travel_time_minutes=0):
    """新しいエリアをデータベースに登録（所要時間対応）"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COALESCE(MAX(area_id), 0) + 1 as next_id FROM areas")
        result = cursor.fetchone()
        new_area_id = result['next_id']
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 as next_sort FROM areas")
        sort_result = cursor.fetchone()
        next_sort_order = sort_result['next_sort'] if sort_result else 1
        
        cursor.execute("""
            INSERT INTO areas (area_id, name, transportation_fee, travel_time_minutes, sort_order) 
            VALUES (%s, %s, %s, %s, %s)
        """, (new_area_id, name, transportation_fee, travel_time_minutes, next_sort_order))
        db.commit()
        return True
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"エリア登録エラー: {e}")
        return False

def find_area_by_id(db, area_id):
    """IDでエリアを検索"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM areas WHERE area_id = %s", (area_id,))
    area = cursor.fetchone()
    return area if area else None

def find_area_by_name(db, name):
    """名前でエリアを検索（重複チェック用）"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM areas WHERE name = %s", (name,))
    area = cursor.fetchone()
    return area if area else None

def update_area(db, area_id, name, transportation_fee=0, travel_time_minutes=0):
    """エリア情報を更新（所要時間対応）"""
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE areas 
            SET name = %s, transportation_fee = %s, travel_time_minutes = %s 
            WHERE area_id = %s
        """, (name, transportation_fee, travel_time_minutes, area_id))
        
        db.commit()
        return True
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"エリア更新エラー: {e}")
        return False

def delete_area_by_id(db, area_id):
    """IDでエリアを削除"""
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM areas WHERE area_id = %s", (area_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"エリア削除エラー: {e}")
        return False

def move_area_up(db, area_id):
    """エリアの並び順を上に移動"""
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order FROM areas WHERE area_id = %s", (area_id,))
        current = cursor.fetchone()
        
        if not current:
            return False
        
        current_order = current['sort_order']
        
        cursor.execute("""
            SELECT area_id, sort_order FROM areas 
            WHERE sort_order < %s 
            ORDER BY sort_order DESC LIMIT 1
        """, (current_order,))
        upper = cursor.fetchone()
        
        if upper:
            upper_id = upper['area_id']
            upper_order = upper['sort_order']
            
            cursor.execute("UPDATE areas SET sort_order = %s WHERE area_id = %s", (upper_order, area_id))
            cursor.execute("UPDATE areas SET sort_order = %s WHERE area_id = %s", (current_order, upper_id))
            
            db.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"エリア並び順上移動エラー: {e}")
        return False

def move_area_down(db, area_id):
    """エリアの並び順を下に移動"""
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order FROM areas WHERE area_id = %s", (area_id,))
        current = cursor.fetchone()
        
        if not current:
            return False
        
        current_order = current['sort_order']
        
        cursor.execute("""
            SELECT area_id, sort_order FROM areas 
            WHERE sort_order > %s 
            ORDER BY sort_order ASC LIMIT 1
        """, (current_order,))
        lower = cursor.fetchone()
        
        if lower:
            lower_id = lower['area_id']
            lower_order = lower['sort_order']
            
            cursor.execute("UPDATE areas SET sort_order = %s WHERE area_id = %s", (lower_order, area_id))
            cursor.execute("UPDATE areas SET sort_order = %s WHERE area_id = %s", (current_order, lower_id))
            
            db.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"エリア並び順下移動エラー: {e}")
        return False

# ==== ホテル関連の関数 ====
def get_all_hotels_with_details(db, sort_by='sort_order'):
    """ホテル一覧を詳細情報付きで取得する"""
    cursor = db.cursor()
    
    if sort_by == 'sort_order':
        query = """
        SELECT 
            h.hotel_id,
            h.name as hotel_name,
            h.category_id,
            h.area_id,
            h.base_price,
            h.additional_time,
            h.is_active,
            h.sort_order,
            c.name as category_name,
            a.name as area_name,
            a.transportation_fee,
            a.travel_time_minutes
        FROM hotels h
        LEFT JOIN categories c ON h.category_id = c.category_id
        LEFT JOIN areas a ON h.area_id = a.area_id
        ORDER BY h.sort_order ASC, h.hotel_id ASC
        """
    elif sort_by == 'category_name_hotel_name':
        query = """
        SELECT 
            h.hotel_id,
            h.name as hotel_name,
            h.category_id,
            h.area_id,
            h.base_price,
            h.additional_time,
            h.is_active,
            h.sort_order,
            c.name as category_name,
            a.name as area_name,
            a.transportation_fee,
            a.travel_time_minutes
        FROM hotels h
        LEFT JOIN categories c ON h.category_id = c.category_id
        LEFT JOIN areas a ON h.area_id = a.area_id
        ORDER BY c.category_id, a.area_id, h.name
        """
    else:
        query = """
        SELECT 
            h.hotel_id,
            h.name as hotel_name,
            h.category_id,
            h.area_id,
            h.base_price,
            h.additional_time,
            h.is_active,
            h.sort_order,
            c.name as category_name,
            a.name as area_name,
            a.transportation_fee,
            a.travel_time_minutes
        FROM hotels h
        LEFT JOIN categories c ON h.category_id = c.category_id
        LEFT JOIN areas a ON h.area_id = a.area_id
        ORDER BY h.hotel_id
        """
    
    cursor.execute(query)
    return cursor.fetchall()

def find_hotel_by_id(db, hotel_id):
    """IDでホテルを検索"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            h.hotel_id,
            h.name as hotel_name,
            h.category_id,
            h.area_id,
            h.base_price,
            h.additional_time,
            h.is_active,
            h.sort_order,
            c.name as category_name,
            a.name as area_name,
            a.transportation_fee,
            a.travel_time_minutes
        FROM hotels h
        LEFT JOIN categories c ON h.category_id = c.category_id
        LEFT JOIN areas a ON h.area_id = a.area_id
        WHERE h.hotel_id = %s
    """, (hotel_id,))
    return cursor.fetchone()

def register_hotel(db, name, category_id, area_id, base_price=0, additional_time=0):
    """新しいホテルをデータベースに登録"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COALESCE(MAX(hotel_id), 0) + 1 as next_id FROM hotels")
        result = cursor.fetchone()
        new_hotel_id = result['next_id']
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 as next_sort FROM hotels")
        sort_result = cursor.fetchone()
        next_sort_order = sort_result['next_sort'] if sort_result else 1
        
        cursor.execute("""
            INSERT INTO hotels (hotel_id, name, category_id, area_id, base_price, additional_time, sort_order, is_active, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (new_hotel_id, name, category_id, area_id, base_price, additional_time, next_sort_order, True))
        db.commit()
        return True
    except Exception as e:
        print(f"ホテル登録エラー: {e}")
        return False

def update_hotel(db, hotel_id, name, category_id, area_id, base_price=None, additional_time=None, is_active=True):
    """ホテル情報を更新"""
    try:
        cursor = db.cursor()
        
        if base_price is not None and additional_time is not None:
            cursor.execute("""
                UPDATE hotels 
                SET name = %s, category_id = %s, area_id = %s, base_price = %s, additional_time = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE hotel_id = %s
            """, (name, category_id, area_id, base_price, additional_time, is_active, hotel_id))
        else:
            cursor.execute("""
                UPDATE hotels 
                SET name = %s, category_id = %s, area_id = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE hotel_id = %s
            """, (name, category_id, area_id, is_active, hotel_id))
        
        db.commit()
        return True
    except Exception as e:
        print(f"ホテル更新エラー: {e}")
        return False

def find_hotel_by_name_category_area(db, name, category_id, area_id):
    """名前・カテゴリ・エリアの組み合わせでホテルを検索"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT hotel_id, name, category_id, area_id FROM hotels WHERE name = %s AND category_id = %s AND area_id = %s",
        (name, category_id, area_id)
    )
    return cursor.fetchone()

def delete_hotel_by_id(db, hotel_id):
    """ホテルIDでホテルを削除"""
    try:
        if db is None:
            db = get_db()
        
        cursor = db.cursor()
        cursor.execute("DELETE FROM hotels WHERE hotel_id = %s", (hotel_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"ホテル削除エラー: {e}")
        return False

def move_hotel_up(hotel_id):
    """ホテルの並び順を上に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order FROM hotels WHERE hotel_id = %s", (hotel_id,))
        current_hotel = cursor.fetchone()
        
        if not current_hotel:
            return False
        
        current_order = current_hotel['sort_order']
        
        cursor.execute("""
            SELECT hotel_id, sort_order FROM hotels 
            WHERE sort_order < %s 
            ORDER BY sort_order DESC LIMIT 1
        """, (current_order,))
        upper_hotel = cursor.fetchone()
        
        if upper_hotel:
            upper_hotel_id = upper_hotel['hotel_id']
            upper_order = upper_hotel['sort_order']
            
            cursor.execute("UPDATE hotels SET sort_order = %s WHERE hotel_id = %s", (upper_order, hotel_id))
            cursor.execute("UPDATE hotels SET sort_order = %s WHERE hotel_id = %s", (current_order, upper_hotel_id))
            
            db.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"ホテル並び順上移動エラー: {e}")
        return False

def move_hotel_down(hotel_id):
    """ホテルの並び順を下に移動"""
    try:
        db = get_db()
        if db is None:
            return False
        
        cursor = db.cursor()
        
        cursor.execute("SELECT sort_order FROM hotels WHERE hotel_id = %s", (hotel_id,))
        current_hotel = cursor.fetchone()
        
        if not current_hotel:
            return False
        
        current_order = current_hotel['sort_order']
        
        cursor.execute("""
            SELECT hotel_id, sort_order FROM hotels 
            WHERE sort_order > %s 
            ORDER BY sort_order ASC LIMIT 1
        """, (current_order,))
        lower_hotel = cursor.fetchone()
        
        if lower_hotel:
            lower_hotel_id = lower_hotel['hotel_id']
            lower_order = lower_hotel['sort_order']
            
            cursor.execute("UPDATE hotels SET sort_order = %s WHERE hotel_id = %s", (lower_order, hotel_id))
            cursor.execute("UPDATE hotels SET sort_order = %s WHERE hotel_id = %s", (current_order, lower_hotel_id))
            
            db.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"ホテル並び順下移動エラー: {e}")
        return False