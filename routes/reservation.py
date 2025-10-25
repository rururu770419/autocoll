# -*- coding: utf-8 -*-
"""
予約管理用Blueprint
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import sys
import os

# database モジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db_access import get_display_name
from database.connection import get_db, get_store_id

# 予約データベース関数をインポート
from database.reservation_db import (
    get_all_reservation_methods,
    add_reservation_method,
    update_reservation_method,
    delete_reservation_method,
    reorder_reservation_methods,
    get_all_cancellation_reasons,
    add_cancellation_reason,
    update_cancellation_reason,
    delete_cancellation_reason,
    reorder_cancellation_reasons,
    create_reservation,
    get_reservations_by_date,
    get_reservation_by_id,
    update_reservation,
    cancel_reservation
)

reservation_bp = Blueprint('reservation', __name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 予約一覧ページ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/reservations', methods=['GET'])
def reservations_list(store):
    """予約一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    # 日付パラメータを取得（指定がなければ今日）
    target_date = request.args.get('date')
    if not target_date:
        from datetime import date
        target_date = date.today().strftime('%Y-%m-%d')

    return render_template(
        'reservation_list.html',
        store=store,
        display_name=display_name,
        target_date=target_date
    )


@reservation_bp.route('/<store>/reservations/api', methods=['GET'])
def get_reservations_api(store):
    """指定日付の予約一覧を取得するAPI"""
    try:
        store_id = get_store_id(store)
        target_date = request.args.get('date')

        if not target_date:
            from datetime import date
            target_date = date.today().strftime('%Y-%m-%d')

        reservations = get_reservations_by_date(store_id, target_date)

        # datetime型をISO形式文字列に変換
        for reservation in reservations:
            for key, value in reservation.items():
                if isinstance(value, datetime):
                    reservation[key] = value.isoformat()

        # お釣り機能の設定を取得
        from database.settings_db import get_change_feature_setting
        use_change_feature = get_change_feature_setting(store_id)

        return jsonify({
            'success': True,
            'data': reservations,
            'date': target_date,
            'use_change_feature': use_change_feature
        })

    except Exception as e:
        print(f"Error in get_reservations_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'予約一覧の取得に失敗しました: {str(e)}'
        }), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 顧客予約登録ページ（既存機能）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/reservation/new', methods=['GET'])
def new_reservation(store):
    """新規予約登録ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    customer_id = request.args.get('customer_id', type=int)
    if not customer_id:
        return "顧客IDが指定されていません。", 400

    store_id = get_store_id(store)

    db = get_db()
    cursor = db.cursor()

    # 顧客情報を取得
    cursor.execute("""
        SELECT
            customer_id,
            name,
            phone,
            current_points,
            member_type
        FROM customers
        WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()

    if not customer:
        db.close()
        return "顧客が見つかりません。", 404

    # 来店回数を取得（成約済みの予約のみカウント）
    cursor.execute("""
        SELECT COUNT(*) as visit_count
        FROM reservations
        WHERE customer_id = %s
        AND store_id = %s
        AND status = '成約'
    """, (customer_id, store_id))
    visit_count_result = cursor.fetchone()
    visit_count = visit_count_result['visit_count'] if visit_count_result else 0

    # 最終来店情報を取得
    cursor.execute("""
        SELECT
            r.reservation_datetime,
            c.name as cast_name,
            h.name as hotel_name
        FROM reservations r
        LEFT JOIN casts c ON r.cast_id = c.cast_id AND r.store_id = c.store_id
        LEFT JOIN hotels h ON r.hotel_id = h.hotel_id AND r.store_id = h.store_id
        WHERE r.customer_id = %s
        AND r.store_id = %s
        AND r.status = '成約'
        ORDER BY r.reservation_datetime DESC
        LIMIT 1
    """, (customer_id, store_id))
    last_visit = cursor.fetchone()

    # 顧客データに追加情報を含める
    customer_data = {
        'customer_id': customer['customer_id'],
        'customer_number': f"{customer['customer_id']:06d}",  # customer_idから生成
        'name': customer['name'],
        'phone': customer['phone'],
        'current_points': customer['current_points'] or 0,
        'member_type': customer['member_type'] or '通常会員',
        'visit_count': visit_count,
        'last_visit_datetime': last_visit['reservation_datetime'] if last_visit else None,
        'last_cast_name': last_visit['cast_name'] if last_visit and last_visit['cast_name'] else '未設定',
        'last_hotel_name': last_visit['hotel_name'] if last_visit and last_visit['hotel_name'] else '未設定'
    }

    db.close()

    # reservation.html をレンダリング
    return render_template(
        'reservation.html',
        store=store,
        display_name=display_name,
        customer=customer_data
    )

@reservation_bp.route('/<store>/reservation/save', methods=['POST'])
def save_reservation(store):
    """予約保存（Ajax用）"""
    return jsonify({'success': False, 'error': '未実装'})


@reservation_bp.route('/<store>/reservations/register', methods=['POST'])
def register_reservation(store):
    """予約登録（Ajax用）"""
    try:
        store_id = get_store_id(store)

        # デバッグ: 送信されたフォームデータを全て表示
        print("=== 予約登録フォームデータ ===")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        print("===========================")

        # FormDataから全てのデータを取得
        customer_id = request.form.get('customer_id', type=int)
        contract_type = request.form.get('contract_type', 'contract')
        reservation_date = request.form.get('reservation_date')
        reservation_time = request.form.get('reservation_time')

        # 必須項目のバリデーション
        if not customer_id:
            return jsonify({'success': False, 'message': '顧客IDが指定されていません'}), 400

        if not reservation_date or not reservation_time:
            return jsonify({'success': False, 'message': '予約日時を入力してください'}), 400

        # reservation_datetimeを作成
        reservation_datetime = f"{reservation_date} {reservation_time}"

        # business_dateは予約日と同じ（深夜営業の考慮は後で実装）
        business_date = reservation_date

        # その他のフィールド
        cast_id = request.form.get('cast_id', type=int) or None
        staff_id = request.form.get('staff_id', type=int) or None
        reservation_method_id = request.form.get('reservation_method', type=int) or None
        nomination_type_id = request.form.get('nomination_type', type=int) or None
        course_id = request.form.get('course_id', type=int) or None
        extension_id = request.form.get('extension', type=int) or None
        extension_quantity = request.form.get('extension_quantity', type=int, default=0)
        meeting_place_id = request.form.get('meeting_place', type=int) or None
        transportation_fee = request.form.get('transportation_fee', type=int, default=0)
        hotel_id = request.form.get('hotel_id', type=int) or None
        room_number = request.form.get('room_number') or None
        payment_method = request.form.get('payment_method') or None

        pt_add = request.form.get('pt_add', type=int, default=0)
        comment = request.form.get('comment') or None
        cancellation_reason_id = request.form.get('cancellation_reason', type=int) or None
        adjustment_amount = request.form.get('adjustment_amount', type=int, default=0)

        # オプション（複数選択可）
        option_ids = request.form.getlist('options[]', type=int)

        # area_idの取得（交通費から逆引きする場合もあるが、今回は未使用）
        area_id = None

        # discount_idsの取得（チェックボックスから複数選択対応）
        discount_ids = request.form.getlist('discounts[]', type=int)

        # 予約を作成
        reservation_id = create_reservation(
            store_id=store_id,
            customer_id=customer_id,
            contract_type=contract_type,
            reservation_datetime=reservation_datetime,
            business_date=business_date,
            cast_id=cast_id,
            staff_id=staff_id,
            course_id=course_id,
            nomination_type_id=nomination_type_id,
            extension_id=extension_id,
            extension_quantity=extension_quantity,
            meeting_place_id=meeting_place_id,
            hotel_id=hotel_id,
            room_number=room_number,
            area_id=area_id,
            transportation_fee=transportation_fee,
            payment_method=payment_method,
            option_ids=option_ids,
            discount_ids=discount_ids,
            points_to_grant=pt_add,
            customer_comment=comment,
            staff_memo=None,
            cancellation_reason_id=cancellation_reason_id,
            reservation_method_id=reservation_method_id,
            adjustment_amount=adjustment_amount
        )

        if reservation_id:
            return jsonify({
                'success': True,
                'message': '予約を登録しました',
                'reservation_id': reservation_id
            })
        else:
            return jsonify({
                'success': False,
                'message': '予約登録に失敗しました'
            }), 500

    except Exception as e:
        print(f"Error in register_reservation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定画面：予約方法管理API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/settings/reservation_methods', methods=['GET'])
def get_reservation_methods(store):
    """予約方法一覧を取得"""
    try:
        store_id = get_store_id(store)
        methods = get_all_reservation_methods(store_id)
        return jsonify(methods), 200
    except Exception as e:
        print(f"Error in get_reservation_methods: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/reservation_methods', methods=['POST'])
def add_method(store):
    """予約方法を追加"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()
        method_name = data.get('method_name')
        is_active = data.get('is_active', True)
        
        if not method_name:
            return jsonify({'error': '予約方法名を入力してください'}), 400
        
        method_id = add_reservation_method(store_id, method_name, is_active)
        return jsonify({'id': method_id, 'message': '予約方法を追加しました'}), 201
    except Exception as e:
        print(f"Error adding reservation method: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/reservation_methods/<int:method_id>', methods=['PUT'])
def update_method(store, method_id):
    """予約方法を更新"""
    try:
        data = request.get_json()
        method_name = data.get('method_name')
        is_active = data.get('is_active', True)
        
        if not method_name:
            return jsonify({'error': '予約方法名を入力してください'}), 400
        
        success = update_reservation_method(method_id, method_name, is_active)
        
        if success:
            return jsonify({'message': '予約方法を更新しました'}), 200
        else:
            return jsonify({'error': '更新に失敗しました'}), 404
    except Exception as e:
        print(f"Error updating reservation method: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/reservation_methods/<int:method_id>', methods=['DELETE'])
def delete_method(store, method_id):
    """予約方法を削除"""
    try:
        success = delete_reservation_method(method_id)
        
        if success:
            return jsonify({'message': '予約方法を削除しました'}), 200
        else:
            return jsonify({'error': '削除に失敗しました'}), 404
    except Exception as e:
        print(f"Error deleting reservation method: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/reservation_methods/reorder', methods=['POST'])
def reorder_methods(store):
    """予約方法の表示順序を更新"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()
        method_ids = data.get('method_ids', [])
        
        success = reorder_reservation_methods(store_id, method_ids)
        
        if success:
            return jsonify({'message': '表示順序を更新しました'}), 200
        else:
            return jsonify({'error': '更新に失敗しました'}), 500
    except Exception as e:
        print(f"Error reordering methods: {e}")
        return jsonify({'error': str(e)}), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定画面：キャンセル理由管理API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/settings/cancellation_reasons', methods=['GET'])
def get_cancellation_reasons(store):
    """キャンセル理由一覧を取得"""
    try:
        store_id = get_store_id(store)
        reasons = get_all_cancellation_reasons(store_id)
        return jsonify(reasons), 200
    except Exception as e:
        print(f"Error in get_cancellation_reasons: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/cancellation_reasons', methods=['POST'])
def add_reason(store):
    """キャンセル理由を追加"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()
        reason_text = data.get('reason_text')
        is_active = data.get('is_active', True)
        
        if not reason_text:
            return jsonify({'error': 'キャンセル理由を入力してください'}), 400
        
        reason_id = add_cancellation_reason(store_id, reason_text, is_active)
        return jsonify({'id': reason_id, 'message': 'キャンセル理由を追加しました'}), 201
    except Exception as e:
        print(f"Error adding cancellation reason: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/cancellation_reasons/<int:reason_id>', methods=['PUT'])
def update_reason(store, reason_id):
    """キャンセル理由を更新"""
    try:
        data = request.get_json()
        reason_text = data.get('reason_text')
        is_active = data.get('is_active', True)
        
        if not reason_text:
            return jsonify({'error': 'キャンセル理由を入力してください'}), 400
        
        success = update_cancellation_reason(reason_id, reason_text, is_active)
        
        if success:
            return jsonify({'message': 'キャンセル理由を更新しました'}), 200
        else:
            return jsonify({'error': '更新に失敗しました'}), 404
    except Exception as e:
        print(f"Error updating cancellation reason: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/cancellation_reasons/<int:reason_id>', methods=['DELETE'])
def delete_reason(store, reason_id):
    """キャンセル理由を削除"""
    try:
        success = delete_cancellation_reason(reason_id)
        
        if success:
            return jsonify({'message': 'キャンセル理由を削除しました'}), 200
        else:
            return jsonify({'error': '削除に失敗しました'}), 404
    except Exception as e:
        print(f"Error deleting cancellation reason: {e}")
        return jsonify({'error': str(e)}), 500

@reservation_bp.route('/<store>/settings/cancellation_reasons/reorder', methods=['POST'])
def reorder_reasons(store):
    """キャンセル理由の表示順序を更新"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()
        reason_ids = data.get('reason_ids', [])

        success = reorder_cancellation_reasons(store_id, reason_ids)

        if success:
            return jsonify({'message': '表示順序を更新しました'}), 200
        else:
            return jsonify({'error': '更新に失敗しました'}), 500
    except Exception as e:
        print(f"Error reordering reasons: {e}")
        return jsonify({'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 予約編集ページ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/reservation/edit', methods=['GET'])
def edit_reservation(store):
    """予約編集ページ"""
    import json
    from datetime import date
    from decimal import Decimal

    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    reservation_id = request.args.get('reservation_id', type=int)
    if not reservation_id:
        return "予約IDが指定されていません。", 400

    # 予約情報を取得
    reservation = get_reservation_by_id(reservation_id)
    if not reservation:
        return "予約が見つかりません。", 404

    customer_id = reservation.get('customer_id')
    store_id = get_store_id(store)

    print(f"=== 予約編集ページ: reservation_id={reservation_id}, customer_id={customer_id}, store_id={store_id} ===")

    db = get_db()
    cursor = db.cursor()

    # 顧客情報を取得
    cursor.execute("""
        SELECT
            customer_id,
            name,
            phone,
            current_points
        FROM customers
        WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()

    print(f"=== 顧客情報取得: {customer} ===")

    if not customer:
        db.close()
        return "顧客が見つかりません。", 404

    # 来店回数を取得（成約済みの予約のみカウント）
    cursor.execute("""
        SELECT COUNT(*) as visit_count
        FROM reservations
        WHERE customer_id = %s
        AND store_id = %s
        AND status = '成約'
    """, (customer_id, store_id))
    visit_count_result = cursor.fetchone()
    visit_count = visit_count_result['visit_count'] if visit_count_result else 0

    print(f"=== 顧客ID {customer_id} の来店回数: {visit_count} ===")

    # 最終来店情報を取得（現在編集中の予約を除く）
    cursor.execute("""
        SELECT
            r.reservation_datetime,
            c.name as cast_name,
            h.name as hotel_name
        FROM reservations r
        LEFT JOIN casts c ON r.cast_id = c.cast_id AND r.store_id = c.store_id
        LEFT JOIN hotels h ON r.hotel_id = h.hotel_id AND r.store_id = h.store_id
        WHERE r.customer_id = %s
        AND r.store_id = %s
        AND r.status = '成約'
        AND r.reservation_id != %s
        ORDER BY r.reservation_datetime DESC
        LIMIT 1
    """, (customer_id, store_id, reservation_id))
    last_visit = cursor.fetchone()

    print(f"=== 最終来店情報: {last_visit} ===")

    # 顧客データに追加情報を含める
    customer_data = {
        'customer_id': customer['customer_id'],
        'customer_number': f"{customer['customer_id']:06d}",
        'name': customer['name'],
        'phone': customer['phone'],
        'current_points': customer['current_points'] or 0,
        'visit_count': visit_count,
        'last_visit_datetime': last_visit['reservation_datetime'] if last_visit else None,
        'last_cast_name': last_visit['cast_name'] if last_visit and last_visit['cast_name'] else '未設定',
        'last_hotel_name': last_visit['hotel_name'] if last_visit and last_visit['hotel_name'] else '未設定'
    }

    db.close()

    # お釣り機能の設定を取得
    from database.settings_db import get_change_feature_setting
    use_change_feature = get_change_feature_setting(store_id)

    # datetime型、date型、Decimal型をJSON serializable に変換
    for key, value in reservation.items():
        if isinstance(value, datetime):
            reservation[key] = value.isoformat()
        elif isinstance(value, date):
            reservation[key] = value.isoformat()
        elif isinstance(value, Decimal):
            reservation[key] = float(value)

    # 予約データをJSON形式に変換
    reservation_json = json.dumps(reservation)

    # reservation_edit.html をレンダリング
    return render_template(
        'reservation_edit.html',
        store=store,
        display_name=display_name,
        customer=customer_data,
        reservation=reservation,
        reservation_json=reservation_json,
        use_change_feature=use_change_feature
    )


@reservation_bp.route('/<store>/reservation/update', methods=['POST'])
def update_reservation_route(store):
    """予約更新（Ajax用）"""
    try:
        reservation_id = request.form.get('reservation_id', type=int)
        if not reservation_id:
            return jsonify({'success': False, 'message': '予約IDが指定されていません'}), 400

        # 予約を更新
        success = update_reservation(reservation_id, request.form)

        if success:
            return jsonify({
                'success': True,
                'message': '予約を更新しました',
                'reservation_id': reservation_id
            })
        else:
            return jsonify({
                'success': False,
                'message': '予約更新に失敗しました'
            }), 500

    except Exception as e:
        print(f"Error in update_reservation_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500


@reservation_bp.route('/<store>/reservation/cancel', methods=['POST'])
def cancel_reservation_route(store):
    """予約キャンセル（Ajax用）"""
    try:
        data = request.get_json()
        reservation_id = data.get('reservation_id', type=int)
        cancellation_reason_id = data.get('cancellation_reason_id', type=int)

        if not reservation_id:
            return jsonify({'success': False, 'message': '予約IDが指定されていません'}), 400

        # 予約をキャンセル
        success = cancel_reservation(reservation_id, cancellation_reason_id)

        if success:
            return jsonify({
                'success': True,
                'message': '予約をキャンセルしました'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'キャンセルに失敗しました'
            }), 500

    except Exception as e:
        print(f"Error in cancel_reservation_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500


@reservation_bp.route('/<store>/reservation/delete', methods=['POST'])
def delete_reservation_route(store):
    """予約削除（Ajax用）"""
    try:
        data = request.get_json()
        reservation_id = data.get('reservation_id')

        if not reservation_id:
            return jsonify({'success': False, 'message': '予約IDが指定されていません'}), 400

        # 予約を削除（データベース関数をインポート）
        from database.reservation_db import delete_reservation_completely
        success = delete_reservation_completely(reservation_id)

        if success:
            return jsonify({
                'success': True,
                'message': '予約を削除しました'
            })
        else:
            return jsonify({
                'success': False,
                'message': '削除に失敗しました'
            }), 500

    except Exception as e:
        print(f"Error in delete_reservation_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500


@reservation_bp.route('/<store>/reservation/customer_rating/<int:customer_id>', methods=['GET'])
def get_customer_rating(store, customer_id):
    """顧客評価を取得するAPI"""
    try:
        from database.rating_db import get_all_rating_items

        db = get_db()
        store_id = get_store_id(store)

        # 評価項目を取得（アクティブな項目のみ）
        all_rating_items = get_all_rating_items(db)
        active_rating_items = [item for item in all_rating_items if item.get('is_active')]

        # 評価件数を取得（この顧客を評価したキャストの数）
        cursor = db.execute("""
            SELECT COUNT(DISTINCT cast_id) as rating_count
            FROM cast_customer_ratings
            WHERE customer_id = %s AND store_id = %s
        """, (customer_id, store_id))
        rating_count_result = cursor.fetchone()
        rating_count = rating_count_result['rating_count'] if rating_count_result else 0

        # 皆の評価を集計（全キャストの評価）
        # ラジオボタン/セレクト項目の集計
        cursor = db.execute("""
            SELECT r.item_id, r.rating_value, COUNT(*) as count
            FROM cast_customer_ratings r
            JOIN rating_items ri ON r.item_id = ri.item_id
            WHERE r.customer_id = %s
            AND r.store_id = %s
            AND ri.item_type IN ('radio', 'select')
            GROUP BY r.item_id, r.rating_value
        """, (customer_id, store_id))
        rating_counts = cursor.fetchall()

        # 辞書形式に変換（item_id -> {option_value -> count}）
        everyone_ratings_dict = {}
        for row in rating_counts:
            item_id = str(row['item_id'])
            rating_value = row['rating_value']
            count = row['count']

            if item_id not in everyone_ratings_dict:
                everyone_ratings_dict[item_id] = {}

            everyone_ratings_dict[item_id][rating_value] = count

        # 評価項目ごとの集計データを作成
        import json
        everyone_ratings = {}
        for item in active_rating_items:
            item_id = str(item['item_id'])
            item_type = item['item_type']

            # ラジオボタン、セレクトの場合のみ集計
            if item_type not in ['radio', 'select']:
                continue

            # 選択肢を取得（JSON形式かカンマ区切りか判定）
            options_raw = item.get('options', '')
            options_list = []

            if options_raw:
                try:
                    # JSON形式の場合
                    options_parsed = json.loads(options_raw)
                    if isinstance(options_parsed, list):
                        for opt in options_parsed:
                            if isinstance(opt, dict):
                                options_list.append(opt.get('value', ''))
                            else:
                                options_list.append(str(opt))
                    else:
                        options_list = [str(options_parsed)]
                except (json.JSONDecodeError, TypeError):
                    # JSON形式でない場合はカンマ区切り
                    options_list = [opt.strip() for opt in options_raw.split(',') if opt.strip()]

            item_counts = []
            for option_value in options_list:
                if not option_value:
                    continue

                count = everyone_ratings_dict.get(item_id, {}).get(option_value, 0)
                item_counts.append({
                    'value': option_value,
                    'count': count
                })

            everyone_ratings[item_id] = item_counts

        # テキストエリア（備考欄）の評価を取得（新しい順）
        cursor = db.execute("""
            SELECT r.rating_value, c.name as cast_name, r.created_at
            FROM cast_customer_ratings r
            JOIN rating_items ri ON r.item_id = ri.item_id
            JOIN casts c ON r.cast_id = c.cast_id
            WHERE r.customer_id = %s
            AND r.store_id = %s
            AND ri.item_type = 'textarea'
            AND r.rating_value != ''
            ORDER BY r.created_at DESC
        """, (customer_id, store_id))
        everyone_comments = cursor.fetchall()

        # datetime型を文字列に変換
        comments_list = []
        for comment in everyone_comments:
            comments_list.append({
                'rating_value': comment['rating_value'],
                'cast_name': comment['cast_name'],
                'created_at': comment['created_at'].strftime('%Y/%m/%d') if comment.get('created_at') else ''
            })

        # 評価項目を辞書形式に変換
        rating_items_list = []
        for item in active_rating_items:
            rating_items_list.append({
                'item_id': item['item_id'],
                'item_name': item['item_name'],
                'item_type': item['item_type']
            })

        db.close()

        return jsonify({
            'success': True,
            'rating_count': rating_count,
            'rating_items': rating_items_list,
            'everyone_ratings': everyone_ratings,
            'everyone_comments': comments_list
        })

    except Exception as e:
        print(f"Error in get_customer_rating: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500