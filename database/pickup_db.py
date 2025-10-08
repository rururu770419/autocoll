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
from datetime import datetime, timedelta

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

# ==== 送迎記録関連の関数 ====

def register_pickup_record(db, type, cast_id=None, hotel_id=None, course_id=None, entry_time=None, content=None, nomination_type=None, record_date=None):
    """送迎記録を登録する関数"""
    try:
        print(f"register_pickup_record started with parameters:")
        print(f"   type: {type}")
        print(f"   cast_id: {cast_id}")
        print(f"   hotel_id: {hotel_id}")
        print(f"   course_id: {course_id}")
        print(f"   entry_time: {entry_time}")
        print(f"   content: {content}")
        print(f"   nomination_type: {nomination_type}")
        print(f"   record_date: {record_date}")
        
        cursor = db.cursor()
        print("Database cursor created")
        
        print("Getting max record_id...")
        cursor.execute("SELECT COALESCE(MAX(record_id), 0) + 1 as next_id FROM pickup_records")
        result = cursor.fetchone()
        print(f"   Query result type: {result.__class__.__name__}")
        print(f"   Query result: {result}")
        
        new_record_id = result['next_id']
        print(f"New record_id: {new_record_id}")
        
        # record_dateの判定を変更
        use_current_date_sql = (record_date is None or record_date == 'CURRENT_DATE')
        
        if use_current_date_sql:
            actual_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Using CURRENT_DATE (actual: {actual_date})")
        else:
            actual_date = str(record_date)
            print(f"Using specified date: {actual_date}")
        
        if type == 'pickup':
            print("Processing pickup registration...")
            
            # entry_timeをTIMESTAMP形式に変換
            entry_time_full = actual_date + ' ' + entry_time
            print(f"   Entry time (TIMESTAMP): {entry_time_full}")
            
            print("Creating entry record...")
            if use_current_date_sql:
                cursor.execute(
                    """INSERT INTO pickup_records 
                       (record_id, type, cast_id, hotel_id, course_id, entry_time, is_entry, created_date, nomination_type) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)""",
                    (new_record_id, type, cast_id, hotel_id, course_id, entry_time_full, True, nomination_type)
                )
            else:
                cursor.execute(
                    """INSERT INTO pickup_records 
                       (record_id, type, cast_id, hotel_id, course_id, entry_time, is_entry, created_date, nomination_type) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (new_record_id, type, cast_id, hotel_id, course_id, entry_time_full, True, record_date, nomination_type)
                )
            print("Entry record created")
            
            print("Getting course duration...")
            cursor.execute("SELECT time_minutes FROM courses WHERE course_id = %s", (course_id,))
            course_result = cursor.fetchone()
            print(f"   Course query result: {course_result}")
            
            if course_result:
                course_minutes = course_result['time_minutes']
                print(f"Course duration: {course_minutes} minutes")
                
                print("Calculating exit time...")
                entry_dt = datetime.strptime(entry_time, '%H:%M')
                exit_dt = entry_dt + timedelta(minutes=course_minutes)
                
                # exit_timeもTIMESTAMP形式で作成
                exit_time = actual_date + ' ' + exit_dt.strftime('%H:%M')
                
                print(f"   Entry time: {entry_time}")
                print(f"   Exit time (TIMESTAMP): {exit_time}")
                
                print("Creating exit record...")
                exit_record_id = new_record_id + 1
                print(f"   Exit record_id: {exit_record_id}")
                
                if use_current_date_sql:
                    cursor.execute(
                        """INSERT INTO pickup_records 
                           (record_id, type, cast_id, hotel_id, course_id, entry_time, exit_time, is_entry, created_date, nomination_type) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)""",
                        (exit_record_id, type, cast_id, hotel_id, course_id, entry_time_full, exit_time, False, nomination_type)
                    )
                else:
                    cursor.execute(
                        """INSERT INTO pickup_records 
                           (record_id, type, cast_id, hotel_id, course_id, entry_time, exit_time, is_entry, created_date, nomination_type) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (exit_record_id, type, cast_id, hotel_id, course_id, entry_time_full, exit_time, False, record_date, nomination_type)
                    )
                print("Exit record created")
                print(f"   Entry time stored: {entry_time_full}")
                print(f"   Exit time stored: {exit_time}")
            else:
                print("Course not found - skipping exit record creation")
            
        elif type == 'other':
            print("Processing other type registration...")
            
            # entry_timeをTIMESTAMP形式に変換
            entry_time_full = actual_date + ' ' + entry_time
            print(f"   Entry time (TIMESTAMP): {entry_time_full}")
            
            if use_current_date_sql:
                print("   Using CURRENT_DATE")
                cursor.execute(
                    """INSERT INTO pickup_records 
                       (record_id, type, content, entry_time, is_entry, created_date) 
                       VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)""",
                    (new_record_id, type, content, entry_time_full, True)
                )
            else:
                print(f"   Using specific date: {record_date}")
                cursor.execute(
                    """INSERT INTO pickup_records 
                       (record_id, type, content, entry_time, is_entry, created_date) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (new_record_id, type, content, entry_time_full, True, record_date)
                )
            print("Other type record created")
        
        print("Committing transaction...")
        db.commit()
        print("register_pickup_record completed successfully")
        return True
        
    except Exception as e:
        print(f"Error in register_pickup_record:")
        print(f"   Exception: {str(e)}")
        
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        print("Rolling back transaction...")
        try:
            db.rollback()
            print("Rollback completed")
        except Exception as rollback_error:
            print(f"Rollback failed: {rollback_error}")
        
        return False

def get_pickup_records_by_date(db, date=None):
    """指定日の送迎記録を時間順で取得"""
    cursor = db.cursor()
    
    if date is None:
        query = """
            SELECT p.record_id, p.type, p.cast_id, p.hotel_id, p.course_id, p.staff_id,
                   p.entry_time, p.exit_time, p.content, p.is_entry, p.is_completed, p.memo,
                   p.memo_expanded, p.nomination_type,
                   c.name as cast_name,
                   h.name as hotel_name,
                   u.name as staff_name, u.color as staff_color
            FROM pickup_records p
            LEFT JOIN casts c ON p.cast_id = c.cast_id
            LEFT JOIN hotels h ON p.hotel_id = h.hotel_id
            LEFT JOIN users u ON p.staff_id = u.login_id
            WHERE p.created_date = CURRENT_DATE
            ORDER BY 
                CASE WHEN p.is_entry = true THEN p.entry_time ELSE p.exit_time END ASC
        """
        cursor.execute(query)
    else:
        query = """
            SELECT p.record_id, p.type, p.cast_id, p.hotel_id, p.course_id, p.staff_id,
                   p.entry_time, p.exit_time, p.content, p.is_entry, p.is_completed, p.memo,
                   p.memo_expanded, p.nomination_type,
                   c.name as cast_name,
                   h.name as hotel_name,
                   u.name as staff_name, u.color as staff_color
            FROM pickup_records p
            LEFT JOIN casts c ON p.cast_id = c.cast_id
            LEFT JOIN hotels h ON p.hotel_id = h.hotel_id
            LEFT JOIN users u ON p.staff_id = u.login_id
            WHERE p.created_date = %s
            ORDER BY 
                CASE WHEN p.is_entry = true THEN p.entry_time ELSE p.exit_time END ASC
        """
        cursor.execute(query, (date,))
    
    records = cursor.fetchall()
    return records

def update_pickup_record(db, record_id, field, value):
    """送迎記録の特定フィールドを更新"""
    try:
        cursor = db.cursor()
        
        allowed_fields = [
            'staff_id', 'is_completed', 'memo', 
            'entry_time', 'exit_time', 'cast_id', 'hotel_id', 'content',
            'memo_expanded', 'nomination_type'
        ]
        if field not in allowed_fields:
            return False
        
        if field in ['cast_id', 'hotel_id']:
            if value == '' or value is None:
                value = None
            else:
                try:
                    value = int(value)
                except ValueError:
                    return False
        
        elif field in ['is_completed']:
            if isinstance(value, str):
                value = value.lower() in ['true', '1', 'yes']
            elif not isinstance(value, bool):
                value = bool(value)
                
        elif field == 'memo_expanded':
            try:
                value = int(value) if value is not None else 0
            except ValueError:
                value = 0
        
        elif field in ['entry_time', 'exit_time']:
            import re
            from datetime import datetime
            if value and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', str(value)):
                return False
            
            # TIMESTAMP型に変換（今日の日付 + 時刻）
            if value:
                today = datetime.now().strftime('%Y-%m-%d')
                value = f"{today} {value}"
        
        elif field == 'nomination_type':
            valid_nominations = ['本指名', '店リピ', '新規', 'フリー']
            if value not in valid_nominations:
                return False
        
        elif field in ['memo', 'content']:
            value = str(value) if value is not None else None
        
        elif field == 'staff_id':
            if value == '':
                value = None
        
        query = f"UPDATE pickup_records SET {field} = %s WHERE record_id = %s"
        cursor.execute(query, (value, record_id))
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error in update_pickup_record: {e}")
        return False

def delete_pickup_record(db, record_id):
    """送迎記録を削除する"""
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM pickup_records WHERE record_id = %s", (record_id,))
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting pickup record: {e}")
        db.rollback()
        return False

def get_pickup_records_by_cast(db, cast_id, limit=10):
    """キャスト別の送迎記録を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.record_id, p.type, p.entry_time, p.exit_time, p.nomination_type, p.created_date,
               h.name as hotel_name, c.name as course_name
        FROM pickup_records p
        LEFT JOIN hotels h ON p.hotel_id = h.hotel_id  
        LEFT JOIN courses c ON p.course_id = c.course_id
        WHERE p.cast_id = %s
        ORDER BY p.created_date DESC, p.entry_time DESC
        LIMIT %s
    """, (cast_id, limit))
    return cursor.fetchall()

def get_pickup_statistics(db, start_date=None, end_date=None):
    """送迎統計を取得"""
    cursor = db.cursor()
    
    date_filter = ""
    params = []
    
    if start_date and end_date:
        date_filter = "WHERE p.created_date BETWEEN %s AND %s"
        params = [start_date, end_date]
    elif start_date:
        date_filter = "WHERE p.created_date >= %s" 
        params = [start_date]
    elif end_date:
        date_filter = "WHERE p.created_date <= %s"
        params = [end_date]
    
    query = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT p.cast_id) as unique_casts,
            COUNT(CASE WHEN p.type = 'pickup' THEN 1 END) as pickup_count,
            COUNT(CASE WHEN p.type = 'other' THEN 1 END) as other_count,
            COUNT(CASE WHEN p.is_completed = true THEN 1 END) as completed_count
        FROM pickup_records p
        {date_filter}
    """
    
    cursor.execute(query, params)
    return cursor.fetchone()

def cleanup_old_pickup_records(db, days=7):
    """古い送迎記録を自動削除（7日以上前）"""
    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM pickup_records WHERE created_date < CURRENT_DATE - INTERVAL '%s days'", 
            (days,)
        )
        db.commit()
        deleted_count = cursor.rowcount
        print(f"古い送迎記録を{deleted_count}件削除しました")
        return True
    except Exception as e:
        print(f"Error in cleanup_old_pickup_records: {e}")
        return False

# ==== 金銭管理関連の関数 ====
def register_money_record(db, cast_id, exit_time, received_amount, change_amount, payment_method, staff_id):
    """金銭記録を登録"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COALESCE(MAX(record_id), 0) + 1 as next_id FROM money_records")
        result = cursor.fetchone()
        new_record_id = result['next_id']
        
        cursor.execute(
            """INSERT INTO money_records 
               (record_id, cast_id, exit_time, received_amount, change_amount, payment_method, staff_id, created_date) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)""",
            (new_record_id, cast_id, exit_time, received_amount, change_amount, payment_method, staff_id)
        )
        db.commit()
        return True
    except Exception as e:
        print(f"Error in register_money_record: {e}")
        return False

def get_money_records_by_date(db, date=None):
    """指定日の金銭記録を取得"""
    cursor = db.cursor()
    
    if date is None:
        query = """
            SELECT m.record_id, m.cast_id, m.exit_time, m.received_amount, 
                   m.change_amount, m.payment_method, m.staff_id,
                   c.name as cast_name, u.name as staff_name
            FROM money_records m
            LEFT JOIN casts c ON m.cast_id = c.cast_id
            LEFT JOIN users u ON m.staff_id = u.login_id
            WHERE m.created_date = CURRENT_DATE
            ORDER BY c.name, m.exit_time
        """
        cursor.execute(query)
    else:
        query = """
            SELECT m.record_id, m.cast_id, m.exit_time, m.received_amount, 
                   m.change_amount, m.payment_method, m.staff_id,
                   c.name as cast_name, u.name as staff_name
            FROM money_records m
            LEFT JOIN casts c ON m.cast_id = c.cast_id
            LEFT JOIN users u ON m.staff_id = u.login_id
            WHERE m.created_date = %s
            ORDER BY c.name, m.exit_time
        """
        cursor.execute(query, (date,))
    
    return cursor.fetchall()

def delete_money_record_by_id(db, record_id):
    """金銭記録を削除"""
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM money_records WHERE record_id = %s", (record_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"Error in delete_money_record: {e}")
        return False

def cleanup_old_money_records(db, days=7):
    """古い金銭記録を自動削除（7日以上前）"""
    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM money_records WHERE created_date < CURRENT_DATE - INTERVAL '%s days'", 
            (days,)
        )
        db.commit()
        deleted_count = cursor.rowcount
        print(f"古い金銭記録を{deleted_count}件削除しました")
        return True
    except Exception as e:
        print(f"Error in cleanup_old_money_records: {e}")
        return False

def get_money_summary_by_cast(db, date=None):
    """キャスト別金銭サマリーを取得"""
    cursor = db.cursor()
    
    if date is None:
        query = """
            SELECT 
                c.name as cast_name,
                COUNT(m.record_id) as record_count,
                SUM(m.received_amount) as total_received,
                SUM(m.change_amount) as total_change,
                SUM(m.received_amount - m.change_amount) as net_amount
            FROM money_records m
            JOIN casts c ON m.cast_id = c.cast_id
            WHERE m.created_date = CURRENT_DATE
            GROUP BY c.cast_id, c.name
            ORDER BY net_amount DESC
        """
        cursor.execute(query)
    else:
        query = """
            SELECT 
                c.name as cast_name,
                COUNT(m.record_id) as record_count,
                SUM(m.received_amount) as total_received,
                SUM(m.change_amount) as total_change,
                SUM(m.received_amount - m.change_amount) as net_amount
            FROM money_records m
            JOIN casts c ON m.cast_id = c.cast_id
            WHERE m.created_date = %s
            GROUP BY c.cast_id, c.name
            ORDER BY net_amount DESC
        """
        cursor.execute(query, (date,))
    
    return cursor.fetchall()