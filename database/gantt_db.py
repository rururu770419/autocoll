# -*- coding: utf-8 -*-
"""
タイムスケジュール用のデータベース操作関数
"""
import psycopg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def get_gantt_data(db: psycopg.Connection, store_id: int, target_date: str) -> Dict[str, Any]:
    """
    タイムスケジュール表示用のデータを取得
    
    Args:
        db: データベース接続
        store_id: 店舗ID
        target_date: 対象日（YYYY-MM-DD形式）
    
    Returns:
        dict: タイムスケジュール表示用データ
            {
                'date': '2025-10-10',
                'casts': [
                    {
                        'cast_id': 1,
                        'cast_name': '田中',
                        'start_time': '10:00',
                        'end_time': '18:00',
                        'reservations': [
                            {
                                'reservation_id': 1,
                                'start_time': '14:00',
                                'end_time': '16:00',
                                'customer_name': '山田太郎',
                                'hotel_name': 'ホテルABC',
                                'room_number': '101',
                                ...
                            }
                        ]
                    }
                ]
            }
    """
    cursor = db.cursor()
    
    try:
        # 出勤スケジュールを取得（予約データは後で追加）
        cursor.execute(
            """
            SELECT 
                c.cast_id,
                c.name AS cast_name,
                cs.start_time,
                cs.end_time
            FROM casts c
            INNER JOIN cast_schedules cs ON c.cast_id = cs.cast_id 
                AND cs.work_date = %s
                AND cs.status = 'confirmed'
            WHERE c.store_id = %s
                AND c.is_active = TRUE
                AND cs.start_time IS NOT NULL
            ORDER BY 
                cs.start_time,
                c.furigana
            """,
            (target_date, store_id)
        )
        
        rows = cursor.fetchall()
        
        # データを整形
        casts = []
        for row in rows:
            cast_data = {
                'cast_id': row[0],
                'cast_name': row[1],
                'start_time': str(row[2]) if row[2] else None,
                'end_time': str(row[3]) if row[3] else None,
                'reservations': []  # 予約は後で実装
            }
            casts.append(cast_data)
        
        return {
            'date': target_date,
            'casts': casts
        }
    
    finally:
        cursor.close()


def get_time_slots(start_hour: int = 6, end_hour: int = 29, interval_minutes: int = 30) -> List[Dict[str, str]]:
    """
    時間スロットのリストを生成
    
    Args:
        start_hour: 開始時刻（時）
        end_hour: 終了時刻（時）※25時以降も対応
        interval_minutes: 間隔（分）
    
    Returns:
        list: [{'value': '06:00', 'label': '6:00'}, ...]
    """
    time_slots = []
    
    for hour in range(start_hour, end_hour + 1):
        for minute in range(0, 60, interval_minutes):
            # 24時以降の表記を処理
            display_hour = hour if hour < 24 else hour - 24
            time_value = f"{hour:02d}:{minute:02d}"
            time_label = f"{display_hour}:{minute:02d}"
            
            time_slots.append({
                'value': time_value,
                'label': time_label
            })
            
            # 終了時刻に達したら終了
            if hour == end_hour and minute >= 30:
                break
    
    return time_slots


def get_store_schedule_settings(db: psycopg.Connection, store_id: int) -> Dict[str, Any]:
    """
    店舗のスケジュール設定を取得
    
    Args:
        db: データベース接続
        store_id: 店舗ID
    
    Returns:
        dict: {
            'start_time': '06:00',
            'end_time': '05:30',
            'time_unit': 30
        }
    """
    cursor = db.cursor()
    
    try:
        # まずカラムの存在を確認
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stores' 
            AND column_name IN ('schedule_start_time', 'schedule_end_time', 'schedule_time_unit')
            """
        )
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # カラムが存在しない場合はデフォルト値を返す
        if not existing_columns:
            return {
                'start_time': '06:00',
                'end_time': '05:30',
                'time_unit': 30
            }
        
        # カラムが存在する場合は取得
        cursor.execute(
            """
            SELECT 
                schedule_start_time,
                schedule_end_time,
                schedule_time_unit
            FROM stores
            WHERE store_id = %s
            """,
            (store_id,)
        )
        
        row = cursor.fetchone()
        
        if row:
            return {
                'start_time': str(row[0]) if row[0] else '06:00',
                'end_time': str(row[1]) if row[1] else '05:30',
                'time_unit': row[2] if row[2] else 30
            }
        else:
            # デフォルト値
            return {
                'start_time': '06:00',
                'end_time': '05:30',
                'time_unit': 30
            }
    
    except Exception as e:
        # エラー時もデフォルト値を返す
        print(f"[WARNING] スケジュール設定取得エラー（デフォルト値を使用）: {str(e)}")
        return {
            'start_time': '06:00',
            'end_time': '05:30',
            'time_unit': 30
        }
    
    finally:
        cursor.close()