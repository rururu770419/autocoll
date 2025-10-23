# -*- coding: utf-8 -*-
"""
キャスト報酬管理用データベース関数
"""

from database.connection import get_db


def get_reservation_options(reservation_id):
    """
    予約に紐づくオプション詳細を取得

    Args:
        reservation_id: 予約ID

    Returns:
        list: オプション詳細のリスト（名前とバック金額）
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT
                o.name as option_name,
                ro.cast_back_amount
            FROM reservation_options ro
            JOIN options o ON ro.option_id = o.option_id
            WHERE ro.reservation_id = %s
            ORDER BY ro.reservation_id
        """, (reservation_id,))

        return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] オプション取得エラー: {e}")
        return []


def get_daily_rewards(cast_id, store_id, business_date):
    """
    指定日のキャスト報酬詳細を取得

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        business_date: 営業日（YYYY-MM-DD形式）

    Returns:
        list: 予約ごとの報酬詳細のリスト
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT
                r.reservation_id,
                r.customer_name,
                r.reservation_datetime,
                r.end_datetime,
                r.course_name,
                r.course_time_minutes,
                COALESCE(nt.type_name, r.nomination_type_name) as nomination_type_name,
                r.change_amount,
                r.payment_method,

                -- 報酬計算
                COALESCE(c.cast_back_amount, 0) as course_back,
                COALESCE(nt.back_amount, 0) as nomination_back,

                -- 報酬合計
                COALESCE(c.cast_back_amount, 0) +
                COALESCE(nt.back_amount, 0) +
                COALESCE(
                    (SELECT SUM(ro.cast_back_amount)
                     FROM reservation_options ro
                     WHERE ro.reservation_id = r.reservation_id), 0
                ) as total_reward

            FROM reservations r
            LEFT JOIN courses c ON r.course_id = c.course_id
            LEFT JOIN nomination_types nt ON r.nomination_type_id = nt.nomination_type_id AND r.store_id = nt.store_id
            WHERE r.cast_id = %s
              AND r.store_id = %s
              AND r.business_date = %s
              AND r.status != 'cancelled'
            ORDER BY r.reservation_datetime
        """, (cast_id, store_id, business_date))

        results = cursor.fetchall()

        # 各予約にオプション詳細を追加
        for reward in results:
            reward['options'] = get_reservation_options(reward['reservation_id'])

        return results
    except Exception as e:
        print(f"[ERROR] 日別報酬取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_cast_transportation_fee(cast_id, store_id):
    """
    キャストの交通費を取得

    Args:
        cast_id: キャストID
        store_id: 店舗ID

    Returns:
        int: 交通費（デフォルト0）
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT transportation_fee
            FROM casts
            WHERE cast_id = %s
              AND store_id = %s
        """, (cast_id, store_id))

        result = cursor.fetchone()
        return result['transportation_fee'] if result and result['transportation_fee'] else 0
    except Exception as e:
        print(f"[ERROR] 交通費取得エラー: {e}")
        return 0


def get_total_change(cast_id, store_id, business_date):
    """
    指定日のお釣り合計を取得

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        business_date: 営業日（YYYY-MM-DD形式）

    Returns:
        int: お釣り合計（デフォルト0）
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT COALESCE(SUM(change_amount), 0) as total_change
            FROM reservations
            WHERE cast_id = %s
              AND store_id = %s
              AND business_date = %s
              AND status != 'cancelled'
        """, (cast_id, store_id, business_date))

        result = cursor.fetchone()
        return result['total_change'] if result else 0
    except Exception as e:
        print(f"[ERROR] お釣り合計取得エラー: {e}")
        return 0


def get_daily_adjustments(cast_id, store_id, business_date):
    """
    指定日の調整金データを取得

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        business_date: 営業日（YYYY-MM-DD形式）

    Returns:
        dict: 調整金データ（なければNone）
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT dormitory_fee, adjustment_amount, memo
            FROM cast_daily_adjustments
            WHERE cast_id = %s
              AND store_id = %s
              AND business_date = %s
        """, (cast_id, store_id, business_date))

        return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] 調整金データ取得エラー: {e}")
        return None


def save_daily_adjustments(cast_id, store_id, business_date, dormitory_fee, adjustment_amount, memo):
    """
    調整金データを保存（INSERT or UPDATE）

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        business_date: 営業日（YYYY-MM-DD形式）
        dormitory_fee: 寮費
        adjustment_amount: 調整金
        memo: メモ

    Returns:
        bool: 成功したらTrue
    """
    try:
        db = get_db()
        db.execute("""
            INSERT INTO cast_daily_adjustments (
                cast_id, store_id, business_date,
                dormitory_fee, adjustment_amount, memo,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (cast_id, store_id, business_date)
            DO UPDATE SET
                dormitory_fee = EXCLUDED.dormitory_fee,
                adjustment_amount = EXCLUDED.adjustment_amount,
                memo = EXCLUDED.memo,
                updated_at = CURRENT_TIMESTAMP
        """, (cast_id, store_id, business_date, dormitory_fee, adjustment_amount, memo))

        db.commit()
        return True
    except Exception as e:
        print(f"[ERROR] 調整金データ保存エラー: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False


def get_monthly_summary(cast_id, store_id, year, month):
    """
    月間サマリーを取得（出勤日数・接客件数・報酬合計）

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        year: 年
        month: 月

    Returns:
        dict: 月間サマリー
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT
                COUNT(DISTINCT r.business_date) as work_days,
                COUNT(r.reservation_id) as total_reservations,
                SUM(
                    COALESCE(c.cast_back_amount, 0) +
                    COALESCE(nt.back_amount, 0) +
                    COALESCE(
                        (SELECT SUM(ro.cast_back_amount)
                         FROM reservation_options ro
                         WHERE ro.reservation_id = r.reservation_id), 0
                    )
                ) as total_reward
            FROM reservations r
            LEFT JOIN courses c ON r.course_id = c.course_id
            LEFT JOIN nomination_types nt ON r.nomination_type_id = nt.nomination_type_id
            WHERE r.cast_id = %s
              AND r.store_id = %s
              AND EXTRACT(YEAR FROM r.business_date) = %s
              AND EXTRACT(MONTH FROM r.business_date) = %s
              AND r.status != 'cancelled'
        """, (cast_id, store_id, year, month))

        result = cursor.fetchone()
        if result:
            return {
                'work_days': result['work_days'] or 0,
                'total_reservations': result['total_reservations'] or 0,
                'total_reward': result['total_reward'] or 0
            }
        return {'work_days': 0, 'total_reservations': 0, 'total_reward': 0}
    except Exception as e:
        print(f"[ERROR] 月間サマリー取得エラー: {e}")
        return {'work_days': 0, 'total_reservations': 0, 'total_reward': 0}


def get_monthly_rewards(cast_id, store_id, year, month):
    """
    月間の日別報酬を取得（カレンダー用）

    Args:
        cast_id: キャストID
        store_id: 店舗ID
        year: 年
        month: 月

    Returns:
        dict: 日付をキーとした報酬額の辞書
    """
    try:
        db = get_db()
        cursor = db.execute("""
            SELECT
                r.business_date,
                SUM(
                    COALESCE(c.cast_back_amount, 0) +
                    COALESCE(nt.back_amount, 0) +
                    COALESCE(
                        (SELECT SUM(ro.cast_back_amount)
                         FROM reservation_options ro
                         WHERE ro.reservation_id = r.reservation_id), 0
                    )
                ) as daily_reward
            FROM reservations r
            LEFT JOIN courses c ON r.course_id = c.course_id
            LEFT JOIN nomination_types nt ON r.nomination_type_id = nt.nomination_type_id
            WHERE r.cast_id = %s
              AND r.store_id = %s
              AND EXTRACT(YEAR FROM r.business_date) = %s
              AND EXTRACT(MONTH FROM r.business_date) = %s
              AND r.status != 'cancelled'
            GROUP BY r.business_date
            ORDER BY r.business_date
        """, (cast_id, store_id, year, month))

        results = cursor.fetchall()

        # 日付をキーとした辞書に変換
        rewards = {}
        for row in results:
            # business_dateが日付型の場合、文字列に変換
            date_key = str(row['business_date'])
            rewards[date_key] = row['daily_reward']

        return rewards
    except Exception as e:
        print(f"[ERROR] 月間報酬取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return {}
