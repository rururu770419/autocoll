# -*- coding: utf-8 -*-
from flask import render_template, request, jsonify, session, redirect, url_for
from database.customer_db import (
    add_customer, get_all_customers, get_customer_by_id,
    update_customer, delete_customer, search_customers
)
from datetime import datetime

# ========================================
# 画面表示ルート
# ========================================

def customer_management_view(store):
    """顧客一覧画面"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))
    return render_template('customer_management.html', store=store)

def customer_registration_view(store):
    """顧客登録画面"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))
    return render_template('customer_registration.html', store=store)

def customer_edit_view(store, customer_id):
    """顧客編集画面"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))
    return render_template('customer_edit.html', store=store, customer_id=customer_id)

# ========================================
# APIエンドポイント
# ========================================

def api_get_customers_endpoint(store):
    """顧客一覧取得API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        customers = get_all_customers(store_code)
        
        print(f"API: 取得した顧客数: {len(customers)}")
        
        # dict_rowをそのままリストに
        customers_list = []
        for customer in customers:
            # dict_row を dict に安全に変換
            customer_dict = {
                'customer_id': customer['customer_id'],
                'name': customer['name'],
                'furigana': customer.get('furigana'),
                'phone': customer.get('phone'),
                'birthday': customer['birthday'].isoformat() if customer.get('birthday') else None,
                'age': customer.get('age'),
                'prefecture': customer.get('prefecture'),
                'city': customer.get('city'),
                'address_detail': customer.get('address_detail'),
                'recruitment_source': customer.get('recruitment_source'),
                'mypage_id': customer.get('mypage_id'),
                'current_points': customer.get('current_points', 0),
                'member_type': customer.get('member_type', '通常会員'),
                'status': customer.get('status', '普通'),
                'web_member': customer.get('web_member', 'web会員'),
                'comment': customer.get('comment'),
                'nickname': customer.get('nickname'),
                'created_at': customer['created_at'].isoformat() if customer.get('created_at') else None,
                'updated_at': customer['updated_at'].isoformat() if customer.get('updated_at') else None
            }
            customers_list.append(customer_dict)
        
        print(f"API: 変換後の顧客数: {len(customers_list)}")
        
        return jsonify({'success': True, 'customers': customers_list})
    except Exception as e:
        print(f"顧客一覧取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

def api_get_customer_endpoint(store, customer_id):
    """顧客情報取得API（ID指定）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        customer = get_customer_by_id(store_code, customer_id)
        
        if not customer:
            return jsonify({'success': False, 'message': '顧客が見つかりません'}), 404
        
        # dict_rowを通常のdictに変換
        customer_dict = dict(customer)

        # パスワードを追加（mypage_password_hashカラムをmypage_passwordとして返す）
        customer_dict['mypage_password'] = customer_dict.get('mypage_password_hash')
        
        # date型をJSON対応形式に変換
        if customer_dict.get('birthday'):
            customer_dict['birthday'] = customer_dict['birthday'].isoformat()
        if customer_dict.get('created_at'):
            customer_dict['created_at'] = customer_dict['created_at'].isoformat()
        if customer_dict.get('updated_at'):
            customer_dict['updated_at'] = customer_dict['updated_at'].isoformat()
        
        return jsonify({'success': True, 'customer': customer_dict})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def api_add_customer_endpoint(store):
    """顧客登録API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        data = request.get_json()
        
        # 必須項目チェック
        if not data.get('name'):
            return jsonify({'success': False, 'message': '名前は必須です'}), 400
        
        # 生年月日の変換
        if data.get('birthday'):
            try:
                data['birthday'] = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
            except:
                data['birthday'] = None
        
        # 数値型の変換
        if data.get('current_points'):
            data['current_points'] = int(data['current_points'])
        
        customer_id = add_customer(store_code, data)
        
        return jsonify({
            'success': True,
            'message': '顧客を登録しました',
            'customer_id': customer_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def api_update_customer_endpoint(store, customer_id):
    """顧客情報更新API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        data = request.get_json()

        
        # 必須項目チェック
        if not data.get('name'):
            return jsonify({'success': False, 'message': '名前は必須です'}), 400
        
        # 生年月日の変換
        if data.get('birthday'):
            try:
                data['birthday'] = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
            except:
                data['birthday'] = None
        
        # 数値型の変換
        if data.get('current_points'):
            data['current_points'] = int(data['current_points'])
        
        update_customer(store_code, customer_id, data)
        
        return jsonify({
            'success': True,
            'message': '顧客情報を更新しました'
        })
    except Exception as e:
        error_message = str(e)
        
        # エラーメッセージを分かりやすく変換
        if 'customers_mypage_id_key' in error_message:
            error_message = 'このマイページIDはすでに登録されています。'
        elif 'customers_phone_key' in error_message:
            error_message = 'この電話番号はすでに登録されています。'
        else:
            # それ以外のエラーはそのまま表示（開発時用）
            error_message = f'更新に失敗しました: {error_message}'
        
        return jsonify({'success': False, 'message': error_message}), 400

def api_delete_customer_endpoint(store, customer_id):
    """顧客削除API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        delete_customer(store_code, customer_id)
        
        return jsonify({
            'success': True,
            'message': '顧客を削除しました'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def api_search_customers_endpoint(store):
    """顧客検索API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401
    
    try:
        store_code = session['store']
        keyword = request.args.get('keyword', '')
        
        if not keyword:
            return jsonify({'success': False, 'message': '検索キーワードを入力してください'}), 400
        
        customers = search_customers(store_code, keyword)
        
        # dict_rowを通常のdictに変換してからJSON対応形式に
        customers_list = []
        for customer in customers:
            customer_dict = dict(customer)
            
            # date型をJSON対応形式に変換
            if customer_dict.get('birthday'):
                customer_dict['birthday'] = customer_dict['birthday'].isoformat()
            if customer_dict.get('created_at'):
                customer_dict['created_at'] = customer_dict['created_at'].isoformat()
            if customer_dict.get('updated_at'):
                customer_dict['updated_at'] = customer_dict['updated_at'].isoformat()
            
            customers_list.append(customer_dict)
        
        return jsonify({'success': True, 'customers': customers_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500