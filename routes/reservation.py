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

    # TODO: 来店回数や最終来店情報を取得する機能は、
    # 予約データを保存する新しいテーブル（reservations）を作成後に実装予定
    # 現在は固定値/ダミーデータを使用

    # 顧客データに追加情報を含める
    customer_data = {
        'customer_id': customer['customer_id'],
        'customer_number': f"{customer['customer_id']:06d}",  # customer_idから生成
        'name': customer['name'],
        'phone': customer['phone'],
        'current_points': customer['current_points'] or 0,
        'member_type': customer['member_type'] or '通常会員',
        'visit_count': 0,  # TODO: 予約履歴から取得
        'last_visit_datetime': None,  # TODO: 予約履歴から取得
        'last_cast_name': '未設定',  # TODO: 予約履歴から取得
        'last_hotel_name': '未設定'  # TODO: 予約履歴から取得
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
            reservation_method_id=reservation_method_id
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

    if not customer:
        db.close()
        return "顧客が見つかりません。", 404

    # 顧客データに追加情報を含める
    customer_data = {
        'customer_id': customer['customer_id'],
        'customer_number': f"{customer['customer_id']:06d}",
        'name': customer['name'],
        'phone': customer['phone'],
        'current_points': customer['current_points'] or 0,
        'visit_count': 0,
        'last_visit_datetime': None,
        'last_cast_name': '未設定',
        'last_hotel_name': '未設定'
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