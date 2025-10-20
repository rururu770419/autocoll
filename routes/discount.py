from flask import render_template, request, jsonify, session, redirect
from functools import wraps
from database.connection import get_db, get_display_name, get_store_id
from database.discount_db import (
    get_all_discounts, get_discount_by_id, find_discount_by_name,
    register_discount, update_discount, delete_discount_permanently,
    is_discount_used, move_discount_order
)

def admin_required(f):
    """管理者権限チェック"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


def discount_management(store):
    """割引マスタ一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    db = get_db()
    discounts = get_all_discounts(db)
    success = request.args.get('success')
    error = request.args.get('error')

    return render_template(
        'discount_management.html',
        store=store,
        display_name=display_name,
        discounts=discounts,
        success=success,
        error=error
    )


def get_discounts_api(store):
    """割引一覧取得API"""
    try:
        db = get_db()
        discounts = get_all_discounts(db)
        
        return jsonify({
            'success': True,
            'discounts': [dict(d) for d in discounts]
        })
    except Exception as e:
        print(f"割引一覧取得エラー: {e}")
        return jsonify({'success': False, 'message': '割引の取得に失敗しました'}), 500


def get_discount_api(store, discount_id):
    """割引詳細取得API"""
    try:
        db = get_db()
        discount = get_discount_by_id(db, discount_id)
        
        if discount:
            return jsonify({
                'success': True,
                'discount': dict(discount)
            })
        else:
            return jsonify({'success': False, 'message': '割引が見つかりません'}), 404
    except Exception as e:
        print(f"割引取得エラー: {e}")
        return jsonify({'success': False, 'message': '割引の取得に失敗しました'}), 500


def register_discount_api(store):
    """割引登録API"""
    try:
        data = request.get_json()
        db = get_db()
        
        # バリデーション
        if not data.get('name'):
            return jsonify({'success': False, 'message': '割引名は必須です'}), 400
        
        if not data.get('value') or float(data.get('value', 0)) <= 0:
            return jsonify({'success': False, 'message': '割引値は0より大きい値を入力してください'}), 400
        
        # パーセント割引の場合は100以下
        if data.get('discount_type') == 'percent' and float(data.get('value', 0)) > 100:
            return jsonify({'success': False, 'message': 'パーセント割引は100%以下で入力してください'}), 400
        
        # 重複チェック
        existing = find_discount_by_name(db, data['name'])
        if existing:
            return jsonify({'success': False, 'message': '既に登録されている割引名です'}), 400
        
        # 登録実行
        discount_data = {
            'name': data['name'],
            'badge_name': data.get('badge_name'),
            'discount_type': data.get('discount_type', 'fixed'),
            'value': float(data['value']),
            'is_active': data.get('is_active', True),
            'store_id': 1
        }
        
        result = register_discount(db, discount_data)
        
        if result:
            return jsonify({'success': True, 'message': '割引を登録しました'})
        else:
            return jsonify({'success': False, 'message': '登録に失敗しました'}), 500
            
    except Exception as e:
        print(f"割引登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '登録に失敗しました'}), 500


def update_discount_api(store, discount_id):
    """割引更新API"""
    try:
        data = request.get_json()
        db = get_db()
        
        # 存在チェック
        discount = get_discount_by_id(db, discount_id)
        if not discount:
            return jsonify({'success': False, 'message': '割引が見つかりません'}), 404
        
        # バリデーション
        if not data.get('name'):
            return jsonify({'success': False, 'message': '割引名は必須です'}), 400
        
        if not data.get('value') or float(data.get('value', 0)) <= 0:
            return jsonify({'success': False, 'message': '割引値は0より大きい値を入力してください'}), 400
        
        # パーセント割引の場合は100以下
        if data.get('discount_type') == 'percent' and float(data.get('value', 0)) > 100:
            return jsonify({'success': False, 'message': 'パーセント割引は100%以下で入力してください'}), 400
        
        # 名前の重複チェック（自分自身は除く）
        existing = find_discount_by_name(db, data['name'])
        if existing and existing['discount_id'] != discount_id:
            return jsonify({'success': False, 'message': 'この割引名は既に使用されています'}), 400
        
        # 更新実行
        discount_data = {
            'name': data['name'],
            'badge_name': data.get('badge_name'),
            'discount_type': data.get('discount_type', 'fixed'),
            'value': float(data['value']),
            'is_active': data.get('is_active', True)
        }
        
        success = update_discount(db, discount_id, discount_data)
        
        if success:
            return jsonify({'success': True, 'message': '割引を更新しました'})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
            
    except Exception as e:
        print(f"割引更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '更新に失敗しました'}), 500


def delete_discount_api(store, discount_id):
    """割引削除API"""
    try:
        db = get_db()
        store_id = get_store_id(store)

        # 使用チェック
        if is_discount_used(db, discount_id, store_id):
            return jsonify({
                'success': False,
                'message': 'この割引は予約で使用されているため削除できません。無効化してください。'
            }), 400

        # 完全削除実行
        success = delete_discount_permanently(db, discount_id, store_id)
        
        if success:
            return jsonify({'success': True, 'message': '割引を削除しました'})
        else:
            return jsonify({'success': False, 'message': '削除に失敗しました'}), 500
            
    except Exception as e:
        print(f"割引削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '削除に失敗しました'}), 500


def move_discount_api(store, discount_id):
    """並び順変更API"""
    try:
        data = request.get_json()
        direction = data.get('direction')
        
        if direction not in ['up', 'down']:
            return jsonify({'success': False, 'message': '不正な移動方向です'}), 400
        
        db = get_db()
        success = move_discount_order(db, discount_id, direction)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'これ以上移動できません'}), 400
            
    except Exception as e:
        print(f"並び順変更エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '移動に失敗しました'}), 500