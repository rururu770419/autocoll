# -*- coding: utf-8 -*-
# routes/settings_customer_api.py
# 顧客情報設定のAPIエンドポイント

from flask import jsonify, request, session
from database.customer_options_db import (
    get_all_categories, update_category_label,
    get_field_options, get_all_field_options,
    add_field_option, update_field_option,
    toggle_field_option_visibility, delete_field_option,
    move_field_option
)
from database.connection import get_store_id


def api_get_customer_fields(store):
    """顧客情報設定を取得"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        # カテゴリ一覧を取得
        categories = get_all_categories(store_id)

        # 各カテゴリの選択肢を取得
        options = {}
        for category in categories:
            field_key = category['field_key']
            options[field_key] = get_field_options(store_id, field_key)
        
        return jsonify({
            'success': True,
            'data': {
                'categories': [dict(c) for c in categories],
                'options': {k: [dict(o) for o in v] for k, v in options.items()}
            }
        })
    except Exception as e:
        print(f"Error getting customer fields: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def api_get_customer_field_options_for_edit(store):
    """顧客編集画面用：すべての選択肢を取得（非表示を除く）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        # カテゴリ一覧
        categories = get_all_categories(store_id)

        # すべての選択肢を取得
        all_options = get_all_field_options(store_id)
        
        # 非表示の選択肢を除外
        visible_options = {}
        for field_key, options in all_options.items():
            visible_options[field_key] = [
                opt for opt in options if not opt['is_hidden']
            ]
        
        return jsonify({
            'success': True,
            'categories': {c['field_key']: c['field_label'] for c in categories},
            'options': visible_options
        })
    except Exception as e:
        print(f"Error getting field options: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_update_category_label(store):
    """カテゴリ名を更新"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        data = request.get_json()

        field_key = data.get('field_key')
        field_label = data.get('field_label', '').strip()

        if not field_key or not field_label:
            return jsonify({'success': False, 'message': 'パラメータが不足しています'}), 400

        success = update_category_label(store_id, field_key, field_label)
        
        if success:
            return jsonify({'success': True, 'message': 'カテゴリ名を更新しました'})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
            
    except Exception as e:
        print(f"Error updating category label: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_add_field_option(store):
    """選択肢を追加"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        data = request.get_json()

        field_key = data.get('field_key')
        option_value = data.get('option_value', '').strip()
        display_color = data.get('display_color', '#f0f0f0')

        if not field_key or not option_value:
            return jsonify({'success': False, 'message': 'パラメータが不足しています'}), 400

        result = add_field_option(store_id, field_key, option_value, display_color, store_code)

        # 重複エラーの場合
        if isinstance(result, dict) and not result.get('success'):
            return jsonify(result), 400

        # 成功の場合
        if result:
            return jsonify({
                'success': True,
                'message': '選択肢を追加しました',
                'option_id': result
            })
        else:
            return jsonify({'success': False, 'message': '追加に失敗しました'}), 500

    except Exception as e:
        print(f"Error adding field option: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_update_field_option(store, option_id):
    """選択肢を更新"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        data = request.get_json()

        option_value = data.get('option_value')
        display_color = data.get('display_color')

        success = update_field_option(option_id, store_id, option_value, display_color)
        
        if success:
            return jsonify({'success': True, 'message': '選択肢を更新しました'})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
            
    except Exception as e:
        print(f"Error updating field option: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_toggle_field_option_visibility(store, option_id):
    """選択肢の表示/非表示を切り替え"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        data = request.get_json()
        is_hidden = data.get('is_hidden', False)

        success = toggle_field_option_visibility(option_id, is_hidden, store_id)
        
        if success:
            message = '非表示にしました' if is_hidden else '表示しました'
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500
            
    except Exception as e:
        print(f"Error toggling visibility: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_delete_field_option(store, option_id):
    """選択肢を削除"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        result = delete_field_option(store_id, option_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error deleting field option: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def api_move_field_option(store, option_id):
    """選択肢の並び順を変更"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)
        data = request.get_json()
        direction = data.get('direction')  # 'up' or 'down'

        if direction not in ['up', 'down']:
            return jsonify({'success': False, 'message': '不正なパラメータです'}), 400

        result = move_field_option(store_id, option_id, direction)
        
        return jsonify(result)
            
    except Exception as e:
        print(f"Error moving field option: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500