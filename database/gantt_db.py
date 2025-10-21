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
    """
    cursor = db.cursor()

    try:
        # 1. 出勤しているキャストを取得
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

        working_casts = cursor.fetchall()

        # 2. 予約があるキャストを取得（出勤していないキャストも含む）
        cursor.execute(
            """
            SELECT DISTINCT
                c.cast_id,
                c.name AS cast_name
            FROM reservations r
            JOIN casts c ON r.cast_id = c.cast_id
            WHERE r.store_id = %s
              AND r.business_date = %s
              AND r.status NOT IN ('cancelled', 'deleted')
              AND c.is_active = TRUE
            """,
            (store_id, target_date)
        )

        reserved_casts = cursor.fetchall()

        # 3. マージ処理
        all_casts = {}

        # 出勤キャストを追加
        for cast in working_casts:
            all_casts[cast[0]] = {
                'cast_id': cast[0],
                'cast_name': cast[1],
                'start_time': str(cast[2]) if cast[2] else None,
                'end_time': str(cast[3]) if cast[3] else None,
                'is_working': True,
                'reservations': []
            }

        # 予約があるが出勤していないキャストを追加
        for cast in reserved_casts:
            if cast[0] not in all_casts:
                all_casts[cast[0]] = {
                    'cast_id': cast[0],
                    'cast_name': cast[1],
                    'start_time': None,
                    'end_time': None,
                    'is_working': False,
                    'reservations': []
                }

        # 4. 予約データを各キャストに紐付け
        for cast_id in all_casts.keys():
            reservations = get_cast_reservations(db, cast_id, target_date)
            all_casts[cast_id]['reservations'] = reservations

        # 5. リストに変換（出勤キャスト優先でソート）
        casts = sorted(
            all_casts.values(),
            key=lambda x: (not x['is_working'], x['start_time'] if x['start_time'] else '99:99', x['cast_name'])
        )

        return {
            'date': target_date,
            'casts': casts
        }

    finally:
        cursor.close()


def get_cast_reservations(db: psycopg.Connection, cast_id: int, target_date: str) -> List[Dict[str, Any]]:
    """
    キャストの予約一覧を取得

    Args:
        db: データベース接続
        cast_id: キャストID
        target_date: 対象日（YYYY-MM-DD形式）

    Returns:
        list: 予約データのリスト
    """
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT
                r.reservation_id,
                r.customer_name,
                r.reservation_datetime,
                r.end_datetime,
                r.hotel_name,
                r.room_number,
                a.travel_time_minutes
            FROM reservations r
            LEFT JOIN hotels h ON r.hotel_id = h.hotel_id
            LEFT JOIN areas a ON h.area_id = a.area_id
            WHERE r.cast_id = %s
                AND r.business_date = %s
                AND r.status NOT IN ('cancelled', 'deleted')
            ORDER BY r.reservation_datetime
            """,
            (cast_id, target_date)
        )

        rows = cursor.fetchall()

        reservations = []
        for row in rows:
            reservation_data = {
                'reservation_id': row[0],
                'customer_name': row[1],
                'start_time': row[2].strftime('%H:%M') if row[2] else None,
                'end_time': row[3].strftime('%H:%M') if row[3] else None,
                'hotel_name': row[4],
                'room_number': row[5],
                'travel_time_minutes': row[6] if row[6] else 0
            }
            reservations.append(reservation_data)

        return reservations

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
            display_hour = hour if hour < 24 else hour - 24
            time_value = f"{hour:02d}:{minute:02d}"
            time_label = f"{display_hour}:{minute:02d}"
            
            time_slots.append({
                'value': time_value,
                'label': time_label
            })
            
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
        dict: スケジュール設定
    """
    cursor = db.cursor()
    
    try:
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stores' 
            AND column_name IN ('schedule_start_time', 'schedule_end_time', 'schedule_time_unit')
            """
        )
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if not existing_columns:
            return {
                'start_time': '06:00',
                'end_time': '05:30',
                'time_unit': 30
            }
        
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
            return {
                'start_time': '06:00',
                'end_time': '05:30',
                'time_unit': 30
            }
    
    except Exception as e:
        return {
            'start_time': '06:00',
            'end_time': '05:30',
            'time_unit': 30
        }
    
    finally:
        cursor.close()


def update_reservation_room_number(db: psycopg.Connection, reservation_id: int, room_number: Optional[str]) -> bool:
    """
    予約の部屋番号を更新
    
    Args:
        db: データベース接続
        reservation_id: 予約ID
        room_number: 部屋番号（Noneの場合は空にする）
    
    Returns:
        bool: 更新成功したらTrue
    """
    cursor = db.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE reservations
            SET room_number = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE reservation_id = %s
            """,
            (room_number, reservation_id)
        )
        
        success = cursor.rowcount > 0
        db.commit()
        
        return success
    
    except Exception as e:
        db.rollback()
        raise e
    
    finally:
        cursor.close()