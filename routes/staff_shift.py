from flask import Blueprint, request, jsonify, session, redirect, render_template
from functools import wraps
from database.shift_db import (
    get_shifts_by_month,
    upsert_shift,
    delete_shift,
    get_all_shift_types,
    get_date_memos_by_month,
    upsert_date_memo
)
from database.connection import get_db, get_store_id
from datetime import datetime
import calendar


# Blueprint作成
staff_shift_bp = Blueprint('staff_shift', __name__)


def admin_required(f):
    """管理者権限チェック"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


@staff_shift_bp.route('/<store>/staff_shift')
@admin_required
def staff_shift_page(store):
    """スタッフシフトページを表示"""
    return render_template('staff_shift.html', store=store)


@staff_shift_bp.route('/<store>/staff_shift/data')
@admin_required
def get_staff_shift_data(store):
    """指定月のスタッフシフトデータを取得"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            today = datetime.now()
            year = today.year
            month = today.month

        store_id = get_store_id(store)

        # スタッフ一覧を取得（role='スタッフ' または 'ドライバー'）
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT login_id, name
            FROM users
            WHERE role IN ('スタッフ', 'ドライバー') AND store_id = %s
            ORDER BY COALESCE(sort_order, 0), name
        """, (store_id,))
        staff_list_raw = cursor.fetchall()
        
        # スタッフリストをJSON serializable形式に変換
        staff_list = []
        for staff in staff_list_raw:
            staff_dict = dict(staff)
            staff_list.append(staff_dict)

        # シフト種別を取得
        shift_types_raw = get_all_shift_types(store_id)

        # シフト種別をJSON serializable形式に変換
        shift_types = []
        for shift_type in shift_types_raw:
            shift_type_dict = dict(shift_type)
            shift_types.append(shift_type_dict)

        # 指定月のシフトを取得
        shifts = get_shifts_by_month(year, month, store_id)

        # 日付別備考を取得
        memos = get_date_memos_by_month(year, month, store_id)
        
        # その月の日数を取得
        _, days_in_month = calendar.monthrange(year, month)
        
        # シフトデータをJSON serializable形式に変換
        shifts_serializable = []
        for shift in shifts:
            shift_dict = dict(shift)
            # time型を文字列に変換
            if shift_dict.get('start_time'):
                shift_dict['start_time'] = str(shift_dict['start_time'])
            if shift_dict.get('end_time'):
                shift_dict['end_time'] = str(shift_dict['end_time'])
            # date型を文字列に変換
            if shift_dict.get('shift_date'):
                shift_dict['shift_date'] = str(shift_dict['shift_date'])
            shifts_serializable.append(shift_dict)
        
        # 備考データをJSON serializable形式に変換
        memos_serializable = []
        for memo in memos:
            memo_dict = dict(memo)
            # date型を文字列に変換
            if memo_dict.get('memo_date'):
                memo_dict['memo_date'] = str(memo_dict['memo_date'])
            memos_serializable.append(memo_dict)
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'staff_list': staff_list,
            'shift_types': shift_types,
            'shifts': shifts_serializable,
            'memos': memos_serializable
        })
        
    except Exception as e:
        print(f"Error in get_staff_shift_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'データの取得に失敗しました'
        }), 500


@staff_shift_bp.route('/<store>/staff_shift/save', methods=['POST'])
@admin_required
def save_staff_shift(store):
    """シフトを保存"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()

        staff_id = data.get('staff_id')
        shift_date = data.get('shift_date')
        shift_type_id = data.get('shift_type_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        memo = data.get('memo')

        if not staff_id or not shift_date:
            return jsonify({
                'success': False,
                'message': 'スタッフIDと日付は必須です'
            }), 400

        # シフト種別IDがNoneの場合はNULL、空文字の場合もNULL
        if shift_type_id == '' or shift_type_id == 'null':
            shift_type_id = None

        # 時間が空文字の場合はNULL
        if start_time == '':
            start_time = None
        if end_time == '':
            end_time = None

        success = upsert_shift(
            staff_id=staff_id,
            shift_date=shift_date,
            shift_type_id=shift_type_id,
            store_id=store_id,
            start_time=start_time,
            end_time=end_time,
            parking_id=None,  # 駐車場は今回使わない
            memo=memo
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'シフトを保存しました'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'シフトの保存に失敗しました'
            }), 500
            
    except Exception as e:
        print(f"Error in save_staff_shift: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'シフトの保存に失敗しました'
        }), 500


@staff_shift_bp.route('/<store>/staff_shift/delete', methods=['POST'])
@admin_required
def delete_staff_shift(store):
    """シフトを削除"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()

        staff_id = data.get('staff_id')
        shift_date = data.get('shift_date')

        if not staff_id or not shift_date:
            return jsonify({
                'success': False,
                'message': 'スタッフIDと日付は必須です'
            }), 400

        success = delete_shift(staff_id, shift_date, store_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'シフトを削除しました'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'シフトの削除に失敗しました'
            }), 500
            
    except Exception as e:
        print(f"Error in delete_staff_shift: {e}")
        return jsonify({
            'success': False,
            'message': 'シフトの削除に失敗しました'
        }), 500


@staff_shift_bp.route('/<store>/staff_shift/save_memo', methods=['POST'])
@admin_required
def save_date_memo(store):
    """日付別備考を保存"""
    try:
        store_id = get_store_id(store)
        data = request.get_json()

        memo_date = data.get('memo_date')
        memo_text = data.get('memo_text', '')

        if not memo_date:
            return jsonify({
                'success': False,
                'message': '日付は必須です'
            }), 400

        success = upsert_date_memo(memo_date, memo_text, store_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '備考を保存しました'
            })
        else:
            return jsonify({
                'success': False,
                'message': '備考の保存に失敗しました'
            }), 500
            
    except Exception as e:
        print(f"Error in save_date_memo: {e}")
        return jsonify({
            'success': False,
            'message': '備考の保存に失敗しました'
        }), 500