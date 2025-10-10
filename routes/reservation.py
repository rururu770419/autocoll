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
    reorder_cancellation_reasons
)

# 🔍 デバッグ：関数のシグネチャを確認
import inspect
print("=" * 60)
print("🔍 DEBUG: 関数シグネチャ確認")
print("get_all_reservation_methods:", inspect.signature(get_all_reservation_methods))
print("get_all_cancellation_reasons:", inspect.signature(get_all_cancellation_reasons))
print("=" * 60)

reservation_bp = Blueprint('reservation', __name__)

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
    cursor.execute("""
        SELECT customer_id, name, phone, current_points
        FROM customers
        WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        return "顧客が見つかりません。", 404
    
    return f"""
    <h1>新規予約登録ページ（開発中）</h1>
    <p>店舗: {display_name}</p>
    <p>顧客ID: {customer_id}</p>
    <p>顧客名: {customer['name']}</p>
    <p><a href="{url_for('main_routes.customer_edit_view', store=store, customer_id=customer_id)}">← 顧客編集に戻る</a></p>
    <p style="color: gray;">※予約フォームは現在作成中です</p>
    """

@reservation_bp.route('/<store>/reservation/save', methods=['POST'])
def save_reservation(store):
    """予約保存（Ajax用）"""
    return jsonify({'success': False, 'error': '未実装'})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定画面：予約方法管理API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@reservation_bp.route('/<store>/settings/reservation_methods', methods=['GET'])
def get_reservation_methods(store):
    """予約方法一覧を取得"""
    print("\n" + "=" * 60)
    print("🔍 DEBUG: get_reservation_methods 呼び出し")
    print(f"🔍 store = {store}")
    try:
        store_id = get_store_id(store)
        print(f"🔍 store_id = {store_id}")
        print(f"🔍 get_all_reservation_methods を呼び出します...")
        print(f"🔍 引数: store_id={store_id}")
        methods = get_all_reservation_methods(store_id)
        print(f"✅ 成功！取得した件数: {len(methods)}")
        print("=" * 60 + "\n")
        return jsonify(methods), 200
    except Exception as e:
        print(f"❌ Error in get_reservation_methods: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60 + "\n")
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
    print("\n" + "=" * 60)
    print("🔍 DEBUG: get_cancellation_reasons 呼び出し")
    print(f"🔍 store = {store}")
    try:
        store_id = get_store_id(store)
        print(f"🔍 store_id = {store_id}")
        print(f"🔍 get_all_cancellation_reasons を呼び出します...")
        print(f"🔍 引数: store_id={store_id}")
        reasons = get_all_cancellation_reasons(store_id)
        print(f"✅ 成功！取得した件数: {len(reasons)}")
        print("=" * 60 + "\n")
        return jsonify(reasons), 200
    except Exception as e:
        print(f"❌ Error in get_cancellation_reasons: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60 + "\n")
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