# database/reservation_db.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.connection import get_connection

# =========================
# 予約方法の管理
# =========================

def get_all_reservation_methods(store_id: int) -> List[Dict]:
    """すべての予約方法を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT method_id, store_id, method_name, is_active, display_order, created_at, updated_at
        FROM reservation_methods
        WHERE store_id = %s
        ORDER BY display_order ASC
    """, (store_id,))
    
    columns = [desc[0] for desc in cursor.description]
    methods = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return methods

def add_reservation_method(store_id: int, method_name: str, is_active: bool = True) -> int:
    """予約方法を追加"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
        FROM reservation_methods
        WHERE store_id = %s
    """, (store_id,))
    
    result = cursor.fetchone()
    next_order = result[0] if result else 1
    
    cursor.execute("""
        INSERT INTO reservation_methods (store_id, method_name, is_active, display_order)
        VALUES (%s, %s, %s, %s)
        RETURNING method_id
    """, (store_id, method_name, is_active, next_order))
    
    method_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    return method_id

def update_reservation_method(method_id: int, method_name: str, is_active: bool) -> bool:
    """予約方法を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE reservation_methods
        SET method_name = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
        WHERE method_id = %s
    """, (method_name, is_active, method_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_reservation_method(method_id: int) -> bool:
    """予約方法を削除"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM reservation_methods WHERE method_id = %s", (method_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def reorder_reservation_methods(store_id: int, method_ids: List[int]) -> bool:
    """予約方法の表示順序を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for order, method_id in enumerate(method_ids, start=1):
            cursor.execute("""
                UPDATE reservation_methods
                SET display_order = %s, updated_at = CURRENT_TIMESTAMP
                WHERE method_id = %s AND store_id = %s
            """, (order, method_id, store_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error reordering methods: {e}")
        return False
    finally:
        conn.close()

# =========================
# キャンセル理由の管理
# =========================

def get_all_cancellation_reasons(store_id: int) -> List[Dict]:
    """すべてのキャンセル理由を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT reason_id, store_id, reason_name, is_active, display_order, created_at, updated_at
        FROM cancellation_reasons
        WHERE store_id = %s
        ORDER BY display_order ASC
    """, (store_id,))
    
    columns = [desc[0] for desc in cursor.description]
    reasons = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return reasons

def add_cancellation_reason(store_id: int, reason_text: str, is_active: bool = True) -> int:
    """キャンセル理由を追加"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
        FROM cancellation_reasons
        WHERE store_id = %s
    """, (store_id,))
    
    result = cursor.fetchone()
    next_order = result[0] if result else 1
    
    cursor.execute("""
        INSERT INTO cancellation_reasons (store_id, reason_name, is_active, display_order)
        VALUES (%s, %s, %s, %s)
        RETURNING reason_id
    """, (store_id, reason_text, is_active, next_order))
    
    reason_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    return reason_id

def update_cancellation_reason(reason_id: int, reason_name: str = None, is_active: bool = None) -> bool:
    """キャンセル理由を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 更新する項目を動的に構築
    updates = []
    params = []
    
    if reason_name is not None:
        updates.append("reason_name = %s")
        params.append(reason_name)
    
    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(reason_id)
    
    query = f"""
        UPDATE cancellation_reasons
        SET {', '.join(updates)}
        WHERE reason_id = %s
    """
    
    cursor.execute(query, params)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_cancellation_reason(reason_id: int) -> bool:
    """キャンセル理由を削除"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cancellation_reasons WHERE reason_id = %s", (reason_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def reorder_cancellation_reasons(store_id: int, reason_ids: List[int]) -> bool:
    """キャンセル理由の表示順序を更新"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for order, reason_id in enumerate(reason_ids, start=1):
            cursor.execute("""
                UPDATE cancellation_reasons
                SET display_order = %s, updated_at = CURRENT_TIMESTAMP
                WHERE reason_id = %s AND store_id = %s
            """, (order, reason_id, store_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error reordering reasons: {e}")
        return False
    finally:
        conn.close()

# =========================
# 予約の管理
# =========================

def create_reservation(
    store_id: int,
    customer_id: int,
    contract_type: str,
    reservation_datetime: str,
    business_date: str,
    cast_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    course_id: Optional[int] = None,
    nomination_type_id: Optional[int] = None,
    extension_id: Optional[int] = None,
    extension_quantity: int = 0,
    meeting_place_id: Optional[int] = None,
    hotel_id: Optional[int] = None,
    room_number: Optional[str] = None,
    area_id: Optional[int] = None,
    transportation_fee: int = 0,
    payment_method: Optional[str] = None,
    option_ids: List[int] = None,
    discount_ids: List[int] = None,
    points_to_grant: int = 0,
    customer_comment: Optional[str] = None,
    staff_memo: Optional[str] = None,
    cancellation_reason_id: Optional[int] = None,
    reservation_method_id: Optional[int] = None
) -> Optional[int]:
    """新規予約を作成（既存のreservationsテーブル構造に対応）"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 顧客情報を取得
        cursor.execute("""
            SELECT name, phone FROM customers WHERE customer_id = %s
        """, (customer_id,))
        customer = cursor.fetchone()
        customer_name = customer[0] if customer else None
        customer_phone = customer[1] if customer else None

        # キャスト情報を取得
        cast_name = None
        if cast_id:
            cursor.execute("""
                SELECT name FROM casts WHERE cast_id = %s AND store_id = %s
            """, (cast_id, store_id))
            cast_result = cursor.fetchone()
            cast_name = cast_result[0] if cast_result else None

        # スタッフ情報を取得
        staff_name = None
        if staff_id:
            cursor.execute("""
                SELECT name FROM users WHERE id = %s AND store_id = %s
            """, (staff_id, store_id))
            staff_result = cursor.fetchone()
            staff_name = staff_result[0] if staff_result else None

        # コース情報を取得
        course_name = None
        course_time_minutes = None
        course_price = 0
        if course_id:
            cursor.execute("""
                SELECT name, time_minutes, price
                FROM courses WHERE course_id = %s AND store_id = %s
            """, (course_id, store_id))
            course_result = cursor.fetchone()
            if course_result:
                course_name = course_result[0]
                course_time_minutes = course_result[1]
                course_price = course_result[2] or 0

        # 指名情報を取得
        nomination_type_name = None
        nomination_fee = 0
        if nomination_type_id:
            cursor.execute("""
                SELECT type_name, additional_fee
                FROM nomination_types WHERE nomination_type_id = %s AND store_id = %s
            """, (nomination_type_id, store_id))
            nomination_result = cursor.fetchone()
            if nomination_result:
                nomination_type_name = nomination_result[0]
                nomination_fee = nomination_result[1] or 0

        # 延長情報を取得（回数対応）
        extension_name = None
        extension_minutes = None
        extension_fee = 0
        if extension_id:
            cursor.execute("""
                SELECT extension_name, extension_minutes, extension_fee
                FROM extensions WHERE extension_id = %s AND store_id = %s
            """, (extension_id, store_id))
            extension_result = cursor.fetchone()
            if extension_result:
                extension_name = extension_result[0]
                extension_minutes = (extension_result[1] or 0) * extension_quantity
                extension_fee = (extension_result[2] or 0) * extension_quantity

        # 待ち合わせ場所情報を取得
        meeting_place_name = None
        if meeting_place_id:
            cursor.execute("""
                SELECT place_name FROM meeting_places
                WHERE place_id = %s AND store_id = %s
            """, (meeting_place_id, store_id))
            meeting_result = cursor.fetchone()
            meeting_place_name = meeting_result[0] if meeting_result else None

        # エリア情報を取得
        area_name = None
        if area_id:
            cursor.execute("""
                SELECT name FROM areas WHERE area_id = %s
            """, (area_id,))
            area_result = cursor.fetchone()
            area_name = area_result[0] if area_result else None

        # ホテル情報を取得
        hotel_name = None
        if hotel_id:
            cursor.execute("""
                SELECT name FROM hotels WHERE hotel_id = %s AND store_id = %s
            """, (hotel_id, store_id))
            hotel_result = cursor.fetchone()
            hotel_name = hotel_result[0] if hotel_result else None

        # 割引情報を取得（複数割引対応）
        discount_id = None  # 最初の割引ID（reservationsテーブル用）
        discount_type = None
        discount_name = None
        discount_badge_name = None
        discount_value = None
        discount_amount = 0
        discount_list = []  # 複数割引を保存

        if discount_ids and len(discount_ids) > 0:
            placeholders = ','.join(['%s'] * len(discount_ids))
            cursor.execute(f"""
                SELECT discount_id, discount_type, name, badge_name, value
                FROM discounts WHERE discount_id IN ({placeholders}) AND store_id = %s
                ORDER BY discount_id
            """, tuple(discount_ids) + (store_id,))
            discount_results = cursor.fetchall()

            # 最初の割引を代表として設定（reservationsテーブル用）
            if discount_results:
                first_discount = discount_results[0]
                discount_id = first_discount[0]  # 最初の割引ID
                discount_type = first_discount[1]
                discount_name = first_discount[2]
                discount_badge_name = first_discount[3]
                discount_value = first_discount[4]

            # すべての割引を保存
            for disc in discount_results:
                discount_list.append({
                    'discount_id': disc[0],
                    'discount_type': disc[1],
                    'value': disc[4]
                })

        # 予約方法情報を取得
        reservation_method_name = None
        if reservation_method_id:
            cursor.execute("""
                SELECT method_name FROM reservation_methods
                WHERE method_id = %s AND store_id = %s
            """, (reservation_method_id, store_id))
            method_result = cursor.fetchone()
            reservation_method_name = method_result[0] if method_result else None

        # オプション料金を計算
        options_total = 0
        if option_ids and len(option_ids) > 0:
            placeholders = ','.join(['%s'] * len(option_ids))
            cursor.execute(f"""
                SELECT COALESCE(SUM(price), 0)
                FROM options
                WHERE option_id IN ({placeholders}) AND store_id = %s
            """, tuple(option_ids) + (store_id,))
            options_total = cursor.fetchone()[0] or 0

        # 小計を計算
        subtotal = course_price + nomination_fee + extension_fee + transportation_fee + options_total

        # カード手数料を計算
        card_fee_rate = 0
        card_fee = 0
        if payment_method == 'card':
            # カード手数料率を取得（例: 3%）
            card_fee_rate = 0.03
            card_fee = int(subtotal * card_fee_rate)

        # 割引を適用（複数割引の合計）
        discount_amount = 0
        for disc in discount_list:
            if disc['discount_type'] == 'percentage' and disc['value']:
                discount_amount += int(subtotal * float(disc['value']) / 100)
            elif disc['discount_type'] == 'fixed' and disc['value']:
                discount_amount += int(disc['value'])

        # 合計金額を計算
        total_amount = subtotal + card_fee - discount_amount

        # 終了時刻を計算（コース時間 + 延長時間）
        end_datetime = None
        total_minutes = (course_time_minutes or 0) + (extension_minutes or 0)
        if total_minutes > 0:
            # reservation_datetimeを解析してtimedeltaで計算
            reservation_dt = datetime.strptime(reservation_datetime, '%Y-%m-%d %H:%M')
            end_dt = reservation_dt + timedelta(minutes=total_minutes)
            end_datetime = end_dt

        # ステータスを設定
        status = '成約' if contract_type == 'contract' else 'キャンセル'

        # 予約を挿入
        cursor.execute("""
            INSERT INTO reservations (
                store_id, customer_id, customer_name, customer_phone,
                cast_id, cast_name, business_date, reservation_datetime, end_datetime,
                status, cancellation_reason_id,
                course_id, course_name, course_time_minutes, course_price,
                nomination_type_id, nomination_type_name, nomination_fee,
                extension_id, extension_name, extension_minutes, extension_fee, extension_quantity,
                discount_id, discount_type, discount_name, discount_badge_name, discount_value, discount_amount,
                reservation_method_id, reservation_method_name,
                meeting_place_id, meeting_place_name,
                area_id, area_name,
                hotel_id, hotel_name, room_number,
                transportation_fee,
                payment_method, card_fee_rate, card_fee,
                options_total, subtotal, total_amount,
                staff_id, staff_name,
                points_to_grant, customer_comment, staff_memo
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            RETURNING reservation_id
        """, (
            store_id, customer_id, customer_name, customer_phone,
            cast_id, cast_name, business_date, reservation_datetime, end_datetime,
            status, cancellation_reason_id,
            course_id, course_name, course_time_minutes, course_price,
            nomination_type_id, nomination_type_name, nomination_fee,
            extension_id, extension_name, extension_minutes, extension_fee, extension_quantity,
            discount_id, discount_type, discount_name, discount_badge_name, discount_value, discount_amount,
            reservation_method_id, reservation_method_name,
            meeting_place_id, meeting_place_name,
            area_id, area_name,
            hotel_id, hotel_name, room_number,
            transportation_fee,
            payment_method, card_fee_rate, card_fee,
            options_total, subtotal, total_amount,
            staff_id, staff_name,
            points_to_grant, customer_comment, staff_memo
        ))

        reservation_id = cursor.fetchone()[0]

        # オプションを保存
        if option_ids and len(option_ids) > 0:
            for option_id in option_ids:
                # オプション情報を取得
                cursor.execute("""
                    SELECT price, cast_back_amount FROM options
                    WHERE option_id = %s AND store_id = %s
                """, (option_id, store_id))
                option = cursor.fetchone()

                if option:
                    calculated_price = option[0] or 0
                    cast_back_amount = option[1] or 0
                else:
                    calculated_price = 0
                    cast_back_amount = 0

                # INSERT時に必要なカラムを全て含める（store_id追加）
                cursor.execute("""
                    INSERT INTO reservation_options (
                        reservation_id,
                        option_id,
                        quantity,
                        calculated_price,
                        cast_back_amount,
                        store_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (reservation_id, option_id, 1, calculated_price, cast_back_amount, store_id))

        # 割引情報を保存（複数割引対応）
        for disc in discount_list:
            # 個別の割引額を計算
            individual_discount_amount = 0
            if disc['discount_type'] == 'percentage' and disc['value']:
                individual_discount_amount = int(subtotal * float(disc['value']) / 100)
            elif disc['discount_type'] == 'fixed' and disc['value']:
                individual_discount_amount = int(disc['value'])

            cursor.execute("""
                INSERT INTO reservation_discounts (
                    reservation_id,
                    discount_id,
                    applied_value,
                    store_id
                )
                VALUES (%s, %s, %s, %s)
            """, (reservation_id, disc['discount_id'], individual_discount_amount, store_id))

        # 顧客のポイントを更新
        if points_to_grant > 0:
            cursor.execute("""
                UPDATE customers
                SET current_points = COALESCE(current_points, 0) + %s
                WHERE customer_id = %s
            """, (points_to_grant, customer_id))

        conn.commit()
        return reservation_id

    except Exception as e:
        conn.rollback()
        print(f"Error creating reservation: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


def get_reservation_by_id(reservation_id: int) -> Optional[Dict]:
    """予約IDで予約情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM reservations
            WHERE reservation_id = %s
        """, (reservation_id,))

        result = cursor.fetchone()

        if result:
            columns = [desc[0] for desc in cursor.description]
            reservation = dict(zip(columns, result))

            # オプションを取得（store_idでフィルタ）
            cursor.execute("""
                SELECT ro.option_id
                FROM reservation_options ro
                WHERE ro.reservation_id = %s AND ro.store_id = %s
            """, (reservation_id, reservation['store_id']))

            options = cursor.fetchall()
            reservation['option_ids'] = [opt[0] for opt in options]

            # 割引を取得（複数割引対応）
            cursor.execute("""
                SELECT rd.discount_id
                FROM reservation_discounts rd
                WHERE rd.reservation_id = %s AND rd.store_id = %s
            """, (reservation_id, reservation['store_id']))

            discounts = cursor.fetchall()
            reservation['discount_ids'] = [disc[0] for disc in discounts]

            return reservation

        return None

    except Exception as e:
        print(f"Error getting reservation: {e}")
        return None
    finally:
        conn.close()


def get_reservations_by_date(store_id: int, target_date: str) -> List[Dict]:
    """指定日付の予約一覧を取得（予約時間の早い順）"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                reservation_id,
                store_id,
                customer_id,
                customer_name,
                customer_phone,
                cast_id,
                cast_name,
                business_date,
                reservation_datetime,
                end_datetime,
                status,
                course_id,
                course_name,
                course_time_minutes,
                course_price,
                nomination_type_id,
                nomination_type_name,
                nomination_fee,
                extension_id,
                extension_name,
                extension_minutes,
                extension_fee,
                extension_quantity,
                discount_id,
                discount_type,
                discount_name,
                discount_badge_name,
                discount_value,
                discount_amount,
                reservation_method_id,
                reservation_method_name,
                meeting_place_id,
                meeting_place_name,
                area_id,
                area_name,
                hotel_id,
                hotel_name,
                room_number,
                transportation_fee,
                payment_method,
                card_fee_rate,
                card_fee,
                options_total,
                subtotal,
                total_amount,
                staff_id,
                staff_name,
                points_to_grant,
                customer_comment,
                staff_memo,
                created_at,
                updated_at,
                cancellation_reason_id
            FROM reservations
            WHERE store_id = %s
            AND business_date = %s
            ORDER BY reservation_datetime ASC
        """, (store_id, target_date))

        columns = [desc[0] for desc in cursor.description]
        reservations = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # 各予約にオプション情報を追加（store_idでフィルタ）
        for reservation in reservations:
            cursor.execute("""
                SELECT ro.option_id, o.name, o.badge_name, o.price
                FROM reservation_options ro
                LEFT JOIN options o ON ro.option_id = o.option_id AND ro.store_id = o.store_id
                WHERE ro.reservation_id = %s AND ro.store_id = %s
            """, (reservation['reservation_id'], store_id))

            option_rows = cursor.fetchall()
            reservation['options'] = [
                {'option_id': row[0], 'name': row[1], 'badge_name': row[2], 'price': row[3]}
                for row in option_rows
            ]

            # 各予約に割引情報を追加（複数割引対応）
            cursor.execute("""
                SELECT rd.discount_id, d.name, d.badge_name
                FROM reservation_discounts rd
                LEFT JOIN discounts d ON rd.discount_id = d.discount_id AND rd.store_id = d.store_id
                WHERE rd.reservation_id = %s AND rd.store_id = %s
            """, (reservation['reservation_id'], store_id))

            discount_rows = cursor.fetchall()
            reservation['discounts'] = [
                {'discount_id': row[0], 'name': row[1], 'badge_name': row[2]}
                for row in discount_rows
            ]

        return reservations

    except Exception as e:
        print(f"Error getting reservations by date: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()


def update_reservation(reservation_id: int, data: Dict) -> bool:
    """予約を更新"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 既存の予約データを取得
        existing_reservation = get_reservation_by_id(reservation_id)
        if not existing_reservation:
            print(f"Reservation {reservation_id} not found")
            return False

        store_id = existing_reservation['store_id']
        customer_id = data.get('customer_id')
        contract_type = data.get('contract_type', 'contract')

        # 顧客情報を取得
        cursor.execute("""
            SELECT name, phone FROM customers
            WHERE customer_id = %s AND store_id = %s
        """, (customer_id, store_id))
        customer_result = cursor.fetchone()
        customer_name = customer_result[0] if customer_result else None
        customer_phone = customer_result[1] if customer_result else None

        # キャスト情報を取得
        cast_id = data.get('cast_id', type=int) or None
        cast_name = None
        if cast_id:
            cursor.execute("""
                SELECT name FROM casts WHERE cast_id = %s AND store_id = %s
            """, (cast_id, store_id))
            result = cursor.fetchone()
            cast_name = result[0] if result else None

        # コース情報を取得
        course_id = data.get('course_id', type=int) or None
        course_name = None
        course_time_minutes = None
        course_price = None
        if course_id:
            cursor.execute("""
                SELECT name, time_minutes, price FROM courses
                WHERE course_id = %s AND store_id = %s
            """, (course_id, store_id))
            result = cursor.fetchone()
            if result:
                course_name = result[0]
                course_time_minutes = result[1]
                course_price = result[2]

        # 指名種類情報を取得
        nomination_type_id = data.get('nomination_type', type=int) or None
        nomination_type_name = None
        nomination_fee = None
        if nomination_type_id:
            cursor.execute("""
                SELECT type_name, additional_fee FROM nomination_types
                WHERE nomination_type_id = %s AND store_id = %s
            """, (nomination_type_id, store_id))
            result = cursor.fetchone()
            if result:
                nomination_type_name = result[0]
                nomination_fee = result[1]

        # 延長情報を取得（回数対応）
        extension_id = data.get('extension', type=int) or None
        extension_quantity = data.get('extension_quantity', type=int) or 0
        extension_name = None
        extension_minutes = None
        extension_fee = None
        if extension_id:
            cursor.execute("""
                SELECT extension_name, extension_minutes, extension_fee FROM extensions
                WHERE extension_id = %s AND store_id = %s
            """, (extension_id, store_id))
            result = cursor.fetchone()
            if result:
                extension_name = result[0]
                extension_minutes = (result[1] or 0) * extension_quantity
                extension_fee = (result[2] or 0) * extension_quantity

        # 割引情報を取得（複数割引対応）
        discount_ids_raw = data.getlist('discounts[]') if hasattr(data, 'getlist') else []
        discount_ids = [int(d) for d in discount_ids_raw if d]
        discount_id = None  # 最初の割引ID（reservationsテーブル用）
        discount_type = None
        discount_name = None
        discount_badge_name = None
        discount_value = None
        discount_amount = 0
        discount_list = []  # 複数割引を保存

        if discount_ids and len(discount_ids) > 0:
            placeholders = ','.join(['%s'] * len(discount_ids))
            cursor.execute(f"""
                SELECT discount_id, discount_type, name, badge_name, value
                FROM discounts WHERE discount_id IN ({placeholders}) AND store_id = %s
                ORDER BY discount_id
            """, tuple(discount_ids) + (store_id,))
            discount_results = cursor.fetchall()

            # 最初の割引を代表として設定（reservationsテーブル用）
            if discount_results:
                first_discount = discount_results[0]
                discount_id = first_discount[0]  # 最初の割引ID
                discount_type = first_discount[1]
                discount_name = first_discount[2]
                discount_badge_name = first_discount[3]
                discount_value = first_discount[4]

            # すべての割引を保存
            for disc in discount_results:
                discount_list.append({
                    'discount_id': disc[0],
                    'discount_type': disc[1],
                    'value': disc[4]
                })

        # 予約方法情報を取得
        reservation_method_id = data.get('reservation_method', type=int) or None
        reservation_method_name = None
        if reservation_method_id:
            cursor.execute("""
                SELECT method_name FROM reservation_methods
                WHERE method_id = %s AND store_id = %s
            """, (reservation_method_id, store_id))
            method_result = cursor.fetchone()
            reservation_method_name = method_result[0] if method_result else None

        # 待ち合わせ場所情報を取得
        meeting_place_id = data.get('meeting_place', type=int) or None
        meeting_place_name = None
        if meeting_place_id:
            cursor.execute("""
                SELECT place_name FROM meeting_places
                WHERE place_id = %s AND store_id = %s
            """, (meeting_place_id, store_id))
            result = cursor.fetchone()
            if result:
                meeting_place_name = result[0]

        # エリア情報を取得
        area_id = data.get('area', type=int) or None
        area_name = None
        if area_id:
            cursor.execute("SELECT name FROM areas WHERE area_id = %s", (area_id,))
            area_result = cursor.fetchone()
            area_name = area_result[0] if area_result else None

        # ホテル情報を取得
        hotel_id = data.get('hotel_id', type=int) or None
        hotel_name = None
        if hotel_id:
            cursor.execute("SELECT name FROM hotels WHERE hotel_id = %s", (hotel_id,))
            result = cursor.fetchone()
            hotel_name = result[0] if result else None

        # その他の情報
        room_number = data.get('room_number') or None
        transportation_fee = data.get('transportation_fee', type=int) or 0
        payment_method = data.get('payment_method') or None
        cancellation_reason_id = data.get('cancellation_reason', type=int) or None

        # カード手数料を計算
        card_fee_rate = 0
        card_fee = 0
        if payment_method and payment_method.lower() == 'カード':
            cursor.execute("""
                SELECT card_fee_percentage FROM reservation_settings
                WHERE store_id = %s
            """, (store_id,))
            result = cursor.fetchone()
            if result and result[0]:
                card_fee_rate = result[0]

        # オプション情報を取得
        option_ids = data.getlist('options[]')
        options_total = 0
        if option_ids:
            placeholders = ','.join(['%s'] * len(option_ids))
            cursor.execute(f"SELECT COALESCE(SUM(price), 0) FROM options WHERE option_id IN ({placeholders})", tuple(option_ids))
            result = cursor.fetchone()
            options_total = result[0] if result and result[0] else 0

        # 料金計算
        subtotal = (course_price or 0) + (nomination_fee or 0) + (extension_fee or 0) + options_total + transportation_fee

        # 割引を適用（複数割引の合計）
        discount_amount = 0
        for disc in discount_list:
            if disc['discount_type'] == 'percentage' and disc['value']:
                discount_amount += int(subtotal * float(disc['value']) / 100)
            elif disc['discount_type'] == 'fixed' and disc['value']:
                discount_amount += int(disc['value'])

        total_amount = subtotal - discount_amount

        # カード手数料を適用
        if card_fee_rate > 0:
            card_fee = int(total_amount * (card_fee_rate / 100))
            total_amount += card_fee

        # スタッフ情報を取得
        staff_id = data.get('staff_id', type=int) or None
        staff_name = None
        if staff_id:
            cursor.execute("""
                SELECT name FROM users WHERE id = %s AND store_id = %s
            """, (staff_id, store_id))
            result = cursor.fetchone()
            staff_name = result[0] if result else None

        # ポイント
        points_to_grant = data.get('pt_add', type=int) or 0
        customer_comment = data.get('comment') or None
        staff_memo = None

        # 予約日時の組み立て
        reservation_date = data.get('reservation_date')
        reservation_time = data.get('reservation_time')
        reservation_datetime = f"{reservation_date} {reservation_time}"
        business_date = reservation_date

        # 終了時刻を計算（コース時間 + 延長時間）
        end_datetime = None
        total_minutes = (course_time_minutes or 0) + (extension_minutes or 0)
        if total_minutes > 0:
            # reservation_datetimeを解析してtimedeltaで計算
            reservation_dt = datetime.strptime(reservation_datetime, '%Y-%m-%d %H:%M')
            end_dt = reservation_dt + timedelta(minutes=total_minutes)
            end_datetime = end_dt

        # ステータスを設定
        status = '成約' if contract_type == 'contract' else 'キャンセル'

        # 予約を更新
        cursor.execute("""
            UPDATE reservations SET
                customer_id = %s, customer_name = %s, customer_phone = %s,
                cast_id = %s, cast_name = %s, business_date = %s, reservation_datetime = %s, end_datetime = %s,
                status = %s, cancellation_reason_id = %s,
                course_id = %s, course_name = %s, course_time_minutes = %s, course_price = %s,
                nomination_type_id = %s, nomination_type_name = %s, nomination_fee = %s,
                extension_id = %s, extension_name = %s, extension_minutes = %s, extension_fee = %s, extension_quantity = %s,
                discount_id = %s, discount_type = %s, discount_name = %s, discount_badge_name = %s, discount_value = %s, discount_amount = %s,
                reservation_method_id = %s, reservation_method_name = %s,
                meeting_place_id = %s, meeting_place_name = %s,
                area_id = %s, area_name = %s,
                hotel_id = %s, hotel_name = %s, room_number = %s,
                transportation_fee = %s,
                payment_method = %s, card_fee_rate = %s, card_fee = %s,
                options_total = %s, subtotal = %s, total_amount = %s,
                staff_id = %s, staff_name = %s,
                points_to_grant = %s, customer_comment = %s, staff_memo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE reservation_id = %s
        """, (
            customer_id, customer_name, customer_phone,
            cast_id, cast_name, business_date, reservation_datetime, end_datetime,
            status, cancellation_reason_id,
            course_id, course_name, course_time_minutes, course_price,
            nomination_type_id, nomination_type_name, nomination_fee,
            extension_id, extension_name, extension_minutes, extension_fee, extension_quantity,
            discount_id, discount_type, discount_name, discount_badge_name, discount_value, discount_amount,
            reservation_method_id, reservation_method_name,
            meeting_place_id, meeting_place_name,
            area_id, area_name,
            hotel_id, hotel_name, room_number,
            transportation_fee,
            payment_method, card_fee_rate, card_fee,
            options_total, subtotal, total_amount,
            staff_id, staff_name,
            points_to_grant, customer_comment, staff_memo,
            reservation_id
        ))

        # オプションを更新（既存を削除して再挿入、store_idでフィルタ）
        cursor.execute("DELETE FROM reservation_options WHERE reservation_id = %s AND store_id = %s", (reservation_id, store_id))

        # 割引を更新（既存を削除して再挿入、store_idでフィルタ）
        cursor.execute("DELETE FROM reservation_discounts WHERE reservation_id = %s AND store_id = %s", (reservation_id, store_id))

        if option_ids:
            for option_id in option_ids:
                # オプション情報を取得
                cursor.execute("""
                    SELECT price, cast_back_amount FROM options
                    WHERE option_id = %s AND store_id = %s
                """, (option_id, store_id))
                option = cursor.fetchone()

                if option:
                    calculated_price = option[0] or 0
                    cast_back_amount = option[1] or 0
                else:
                    calculated_price = 0
                    cast_back_amount = 0

                # INSERT時に必要なカラムを全て含める（store_id追加）
                cursor.execute("""
                    INSERT INTO reservation_options (
                        reservation_id,
                        option_id,
                        quantity,
                        calculated_price,
                        cast_back_amount,
                        store_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (reservation_id, option_id, 1, calculated_price, cast_back_amount, store_id))

        # 割引情報を保存（複数割引対応）
        for disc in discount_list:
            # 個別の割引額を計算
            individual_discount_amount = 0
            if disc['discount_type'] == 'percentage' and disc['value']:
                individual_discount_amount = int(subtotal * float(disc['value']) / 100)
            elif disc['discount_type'] == 'fixed' and disc['value']:
                individual_discount_amount = int(disc['value'])

            cursor.execute("""
                INSERT INTO reservation_discounts (
                    reservation_id,
                    discount_id,
                    applied_value,
                    store_id
                )
                VALUES (%s, %s, %s, %s)
            """, (reservation_id, disc['discount_id'], individual_discount_amount, store_id))

        # ポイント差分を計算して更新
        points_diff = points_to_grant - (existing_reservation.get('points_to_grant') or 0)
        if points_diff != 0:
            cursor.execute("""
                UPDATE customers
                SET current_points = COALESCE(current_points, 0) + %s
                WHERE customer_id = %s
            """, (points_diff, customer_id))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error updating reservation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def cancel_reservation(reservation_id: int, cancellation_reason_id: int = None) -> bool:
    """予約をキャンセル"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ステータスを「キャンセル」に変更
        cursor.execute("""
            UPDATE reservations
            SET status = 'キャンセル',
                cancellation_reason_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE reservation_id = %s
        """, (cancellation_reason_id, reservation_id))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error cancelling reservation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def delete_reservation_completely(reservation_id: int) -> bool:
    """予約を完全に削除"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 予約情報を取得（ポイント返却のため）
        existing_reservation = get_reservation_by_id(reservation_id)
        if not existing_reservation:
            print(f"Reservation {reservation_id} not found")
            return False

        customer_id = existing_reservation.get('customer_id')
        points_to_grant = existing_reservation.get('points_to_grant') or 0

        # オプションを削除（store_idでフィルタ）
        cursor.execute("""
            DELETE FROM reservation_options
            WHERE reservation_id = %s AND store_id = %s
        """, (reservation_id, existing_reservation['store_id']))

        # 予約を削除
        cursor.execute("""
            DELETE FROM reservations
            WHERE reservation_id = %s
        """, (reservation_id,))

        # 付与されたポイントを返却
        if points_to_grant > 0 and customer_id:
            cursor.execute("""
                UPDATE customers
                SET current_points = COALESCE(current_points, 0) - %s
                WHERE customer_id = %s
            """, (points_to_grant, customer_id))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error deleting reservation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()