# -*- coding: utf-8 -*-
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

def get_db_connection():
    """データベース接続を取得"""
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname='pickup_system',  # 固定
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'diary8475ftkb'),
        row_factory=dict_row
    )
    return conn

def get_weekly_schedules(store_id, start_date):
    """
    週間出勤スケジュールを取得
    
    Args:
        store_id: 店舗ID
        start_date: 週の開始日（YYYY-MM-DD形式）
    
    Returns:
        dict: キャストごとの出勤情報
        {
            cast_id: {
                'cast_name': 'あやみ',
                'furigana': 'あやみ',
                'schedules': {
                    '2025-10-10': {'start_time': '10:00', 'end_time': '13:00', 'status': 'confirmed'},
                    '2025-10-11': {'status': 'off'},
                    ...
                }
            }
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 週間日付リストを生成
        dates = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        for i in range(7):
            dates.append((current_date + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        # キャスト一覧を取得（本日出勤中を優先）
        cur.execute("""
            SELECT DISTINCT
                c.cast_id,
                c.name as cast_name,
                c.furigana,
                cs_today.start_time as today_start_time,
                CASE WHEN cs_today.start_time IS NOT NULL THEN 0 ELSE 1 END as sort_priority
            FROM casts c
            LEFT JOIN cast_schedules cs_today ON c.cast_id = cs_today.cast_id
                AND cs_today.work_date = CURRENT_DATE
                AND cs_today.status = 'confirmed'
                AND cs_today.start_time <= CURRENT_TIME
                AND cs_today.end_time >= CURRENT_TIME
            WHERE c.store_id = %s
            AND c.is_active = TRUE
            ORDER BY
                sort_priority,
                cs_today.start_time,
                c.furigana
        """, (store_id,))
        
        casts = cur.fetchall()
        
        # 各キャストの週間スケジュールを取得
        result = {}
        for cast in casts:
            cast_id = cast['cast_id']
            result[cast_id] = {
                'cast_name': cast['cast_name'],
                'furigana': cast['furigana'],
                'schedules': {}
            }
            
            # 週間のスケジュールを取得
            cur.execute("""
                SELECT
                    work_date,
                    start_time,
                    end_time,
                    status,
                    note
                FROM cast_schedules
                WHERE cast_id = %s
                AND work_date >= %s
                AND work_date < %s
            """, (cast_id, start_date, (current_date + timedelta(days=7)).strftime('%Y-%m-%d')))
            
            schedules = cur.fetchall()
            for schedule in schedules:
                date_str = schedule['work_date'].strftime('%Y-%m-%d')
                result[cast_id]['schedules'][date_str] = {
                    'start_time': schedule['start_time'].strftime('%H:%M') if schedule['start_time'] else None,
                    'end_time': schedule['end_time'].strftime('%H:%M') if schedule['end_time'] else None,
                    'status': schedule['status'],
                    'note': schedule['note']
                }
        
        return result
        
    finally:
        cur.close()
        conn.close()

def get_schedule_by_cast_date(cast_id, work_date):
    """
    特定のキャストと日付の出勤情報を取得
    
    Args:
        cast_id: キャストID
        work_date: 出勤日（YYYY-MM-DD形式）
    
    Returns:
        dict: 出勤情報、存在しない場合はNone
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT
                schedule_id,
                start_time,
                end_time,
                status,
                note
            FROM cast_schedules
            WHERE cast_id = %s
            AND work_date = %s
        """, (cast_id, work_date))
        
        schedule = cur.fetchone()
        if schedule:
            return {
                'schedule_id': schedule['schedule_id'],
                'start_time': schedule['start_time'].strftime('%H:%M') if schedule['start_time'] else None,
                'end_time': schedule['end_time'].strftime('%H:%M') if schedule['end_time'] else None,
                'status': schedule['status'],
                'note': schedule['note']
            }
        return None
        
    finally:
        cur.close()
        conn.close()

def upsert_schedule(store_id, cast_id, work_date, start_time, end_time, status='confirmed', note=None):
    """
    出勤情報を登録・更新（UPSERT）
    
    Args:
        store_id: 店舗ID
        cast_id: キャストID
        work_date: 出勤日（YYYY-MM-DD形式）
        start_time: 開始時刻（HH:MM形式）、休みの場合はNone
        end_time: 終了時刻（HH:MM形式）、休みの場合はNone
        status: ステータス（confirmed/off/cancelled）
        note: メモ
    
    Returns:
        bool: 成功した場合True
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 休みの場合
        if status == 'off':
            cur.execute("""
                INSERT INTO cast_schedules 
                (store_id, cast_id, work_date, start_time, end_time, status, note, source)
                VALUES (%s, %s, %s, NULL, NULL, %s, %s, 'manual')
                ON CONFLICT (cast_id, work_date)
                DO UPDATE SET
                    start_time = NULL,
                    end_time = NULL,
                    status = EXCLUDED.status,
                    note = EXCLUDED.note,
                    updated_at = CURRENT_TIMESTAMP
            """, (store_id, cast_id, work_date, status, note))
        else:
            # 出勤の場合
            cur.execute("""
                INSERT INTO cast_schedules 
                (store_id, cast_id, work_date, start_time, end_time, status, note, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'manual')
                ON CONFLICT (cast_id, work_date)
                DO UPDATE SET
                    start_time = EXCLUDED.start_time,
                    end_time = EXCLUDED.end_time,
                    status = EXCLUDED.status,
                    note = EXCLUDED.note,
                    updated_at = CURRENT_TIMESTAMP
            """, (store_id, cast_id, work_date, start_time, end_time, status, note))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error in upsert_schedule: {e}")
        return False
        
    finally:
        cur.close()
        conn.close()

def delete_schedule(cast_id, work_date):
    """
    出勤情報を削除
    
    Args:
        cast_id: キャストID
        work_date: 出勤日（YYYY-MM-DD形式）
    
    Returns:
        bool: 成功した場合True
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DELETE FROM cast_schedules
            WHERE cast_id = %s
            AND work_date = %s
        """, (cast_id, work_date))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error in delete_schedule: {e}")
        return False
        
    finally:
        cur.close()
        conn.close()

def get_time_slots(start_hour=6, end_hour=5, interval_minutes=30):
    """
    時間スロットのリストを生成
    
    Args:
        start_hour: 開始時刻（時）
        end_hour: 終了時刻（時）※翌日の場合は0-23の範囲
        interval_minutes: 間隔（分）
    
    Returns:
        list: 時間スロットのリスト [('06:00', '06:00'), ('06:30', '06:30'), ...]
    """
    time_slots = []
    
    # 開始時刻から24:00まで
    current_hour = start_hour
    current_minute = 0
    
    while current_hour < 24:
        time_str = f"{current_hour:02d}:{current_minute:02d}"
        time_slots.append((time_str, time_str))
        
        current_minute += interval_minutes
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1
    
    # 翌日0:00から終了時刻まで
    if end_hour < start_hour:
        current_hour = 0
        current_minute = 0
        
        while current_hour < end_hour or (current_hour == end_hour and current_minute <= 30):
            time_str = f"{current_hour:02d}:{current_minute:02d}"
            time_slots.append((time_str, time_str))
            
            current_minute += interval_minutes
            if current_minute >= 60:
                current_minute = 0
                current_hour += 1
    
    return time_slots