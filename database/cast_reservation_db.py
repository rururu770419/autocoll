# database/cast_reservation_db.py
"""
キャスト予約一覧用データベースアクセス関数
"""

def get_cast_reservations_by_date(db, cast_id, store_id, business_date):
    """
    指定日のキャスト予約一覧を取得（時刻順）

    Args:
        db: データベース接続
        cast_id: キャストID
        store_id: 店舗ID
        business_date: 営業日（YYYY-MM-DD形式）

    Returns:
        list: 予約一覧（辞書形式）
    """
    try:
        cursor = db.execute("""
            SELECT
                r.reservation_id,
                r.customer_id,
                r.reservation_datetime,
                r.end_datetime,
                r.status,
                r.customer_name,
                r.customer_phone,
                r.course_name,
                r.course_time_minutes,
                r.nomination_type_name,
                r.hotel_name,
                r.room_number,
                r.transportation_fee,
                r.total_amount,
                r.payment_method,
                r.amount_received,
                r.change_amount,
                STRING_AGG(o.name, ', ' ORDER BY o.name) as options_list
            FROM reservations r
            LEFT JOIN reservation_options ro ON r.reservation_id = ro.reservation_id
            LEFT JOIN options o ON ro.option_id = o.option_id AND ro.store_id = o.store_id
            WHERE r.store_id = %s
              AND r.cast_id = %s
              AND r.business_date = %s
            GROUP BY r.reservation_id, r.customer_id, r.reservation_datetime, r.end_datetime, r.status,
                     r.customer_name, r.customer_phone, r.course_name, r.course_time_minutes,
                     r.nomination_type_name, r.hotel_name, r.room_number, r.transportation_fee,
                     r.total_amount, r.payment_method, r.amount_received, r.change_amount
            ORDER BY r.reservation_datetime ASC
        """, (store_id, cast_id, business_date))

        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_cast_reservations_by_date: {e}")
        return []


def get_cast_monthly_reservation_counts(db, cast_id, store_id, year, month):
    """
    指定月のキャスト予約件数を日付別に集計

    Args:
        db: データベース接続
        cast_id: キャストID
        store_id: 店舗ID
        year: 年（例: 2025）
        month: 月（例: 3）

    Returns:
        dict: {日付文字列: 予約件数} の辞書
              例: {'2025-03-01': 3, '2025-03-02': 5}
    """
    try:
        # 指定月の初日を作成
        first_day = f"{year}-{month:02d}-01"

        cursor = db.execute("""
            SELECT
                business_date,
                COUNT(*) as reservation_count
            FROM reservations
            WHERE store_id = %s
              AND cast_id = %s
              AND DATE_TRUNC('month', business_date) = DATE_TRUNC('month', %s::date)
            GROUP BY business_date
            ORDER BY business_date ASC
        """, (store_id, cast_id, first_day))

        results = cursor.fetchall()

        # 辞書形式に変換（日付文字列 → 件数）
        counts = {}
        for row in results:
            # business_dateはdateオブジェクトなので文字列に変換
            date_str = row['business_date'].strftime('%Y-%m-%d')
            counts[date_str] = row['reservation_count']

        return counts

    except Exception as e:
        print(f"Error in get_cast_monthly_reservation_counts: {e}")
        return {}


def get_cast_reservation_detail(db, reservation_id, cast_id, store_id):
    """
    予約詳細を取得（キャスト本人の予約のみ）

    Args:
        db: データベース接続
        reservation_id: 予約ID
        cast_id: キャストID（セキュリティ：本人の予約のみ）
        store_id: 店舗ID

    Returns:
        dict: 予約詳細情報、見つからない場合はNone
    """
    try:
        cursor = db.execute("""
            SELECT
                r.reservation_id,
                r.customer_id,
                r.customer_name,
                r.customer_phone,
                r.cast_id,
                r.cast_name,
                r.business_date,
                r.reservation_datetime,
                r.end_datetime,
                r.status,
                r.course_name,
                r.course_time_minutes,
                r.extension_name,
                r.extension_minutes,
                r.nomination_type_name,
                r.hotel_name,
                r.room_number,
                r.meeting_place_name,
                r.transportation_fee,
                r.total_amount,
                r.payment_method,
                r.customer_comment,
                r.staff_memo,
                c.car_info as customer_car_info,
                STRING_AGG(o.name, ', ' ORDER BY o.name) as options_list
            FROM reservations r
            LEFT JOIN customers c ON r.customer_id = c.customer_id AND r.store_id = c.store_id
            LEFT JOIN reservation_options ro ON r.reservation_id = ro.reservation_id
            LEFT JOIN options o ON ro.option_id = o.option_id AND ro.store_id = o.store_id
            WHERE r.reservation_id = %s
              AND r.cast_id = %s
              AND r.store_id = %s
            GROUP BY r.reservation_id, r.customer_id, r.customer_name, r.customer_phone,
                     r.cast_id, r.cast_name, r.business_date, r.reservation_datetime,
                     r.end_datetime, r.status, r.course_name, r.course_time_minutes,
                     r.extension_name, r.extension_minutes, r.nomination_type_name,
                     r.hotel_name, r.room_number, r.meeting_place_name, r.transportation_fee,
                     r.total_amount, r.payment_method, r.customer_comment, r.staff_memo,
                     c.car_info
        """, (reservation_id, cast_id, store_id))

        return cursor.fetchone()

    except Exception as e:
        print(f"Error in get_cast_reservation_detail: {e}")
        return None


def get_customer_visit_count(db, customer_id, cast_id, store_id):
    """
    接客回数を計算（成約済みのみカウント）

    Args:
        db: データベース接続
        customer_id: 顧客ID
        cast_id: キャストID
        store_id: 店舗ID

    Returns:
        int: 接客回数（成約ステータスの予約数）
    """
    try:
        cursor = db.execute("""
            SELECT COUNT(*) as visit_count
            FROM reservations
            WHERE customer_id = %s
              AND cast_id = %s
              AND store_id = %s
              AND status = '成約'
        """, (customer_id, cast_id, store_id))

        result = cursor.fetchone()
        return result['visit_count'] if result else 0

    except Exception as e:
        print(f"Error in get_customer_visit_count: {e}")
        return 0


def update_reservation_amount_received(db, reservation_id, cast_id, store_id, amount_received):
    """
    お預かり金額を更新（キャスト本人の予約のみ）

    Args:
        db: データベース接続
        reservation_id: 予約ID
        cast_id: キャストID（セキュリティ：本人の予約のみ）
        store_id: 店舗ID
        amount_received: お預かり金額

    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        # 合計金額を取得
        cursor = db.execute("""
            SELECT total_amount
            FROM reservations
            WHERE reservation_id = %s
              AND cast_id = %s
              AND store_id = %s
        """, (reservation_id, cast_id, store_id))

        result = cursor.fetchone()

        if not result:
            print(f"Reservation not found or not authorized: {reservation_id}")
            return False

        total_amount = result['total_amount'] or 0
        change_amount = amount_received - total_amount

        # お預かり金額とお釣りを更新
        db.execute("""
            UPDATE reservations
            SET amount_received = %s,
                change_amount = %s
            WHERE reservation_id = %s
              AND cast_id = %s
              AND store_id = %s
        """, (amount_received, change_amount, reservation_id, cast_id, store_id))

        db.commit()
        return True

    except Exception as e:
        print(f"Error in update_reservation_amount_received: {e}")
        db.rollback()
        return False
