from flask import render_template, request, redirect, url_for
from flask import Blueprint
from database.connection import get_db, get_display_name
from database.discount_db import (
    get_all_discounts, get_discount_by_id, find_discount_by_name,
    register_discount, update_discount, delete_discount_permanently, is_discount_used
)
discount_bp = Blueprint('discount', __name__, url_prefix='/discount')

def discount_management(store):
    """割引マスタ一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    discounts = get_all_discounts(db)
    
    # 成功・エラーメッセージの取得
    success_msg = request.args.get('success')
    error_msg = request.args.get('error')
    
    return render_template(
        'discount_management.html',
        store=store,
        display_name=display_name,
        discounts=discounts,
        success=success_msg,
        error=error_msg
    )

def register_discount_page(store):
    """割引マスタ登録ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    
    if request.method == "POST":
        discount_data = {
            'name': request.form.get("name"),
            'discount_type': request.form.get("discount_type", "fixed"),
            'value': float(request.form.get("value", 0)),
            'is_active': request.form.get("is_active") == "on",
            'store_id': 1  # 必要に応じて動的に設定
        }
        
        # バリデーション
        if not discount_data['name']:
            return render_template(
                "discount_registration.html",
                store=store,
                display_name=display_name,
                error="割引名は必須です。"
            )
        
        if discount_data['value'] <= 0:
            return render_template(
                "discount_registration.html",
                store=store,
                display_name=display_name,
                error="割引値は0より大きい値を入力してください。"
            )
        
        # パーセント割引の場合は100以下
        if discount_data['discount_type'] == 'percent' and discount_data['value'] > 100:
            return render_template(
                "discount_registration.html",
                store=store,
                display_name=display_name,
                error="パーセント割引は100%以下で入力してください。"
            )
        
        # 重複チェック
        existing_discount = find_discount_by_name(db, discount_data['name'])
        if existing_discount:
            return render_template(
                "discount_registration.html",
                store=store,
                display_name=display_name,
                error="既に登録されている割引名です。"
            )
        
        # 登録実行
        result = register_discount(db, discount_data)
        
        if result:  # discount_idが返ってくるので、0以外ならTrue
            return redirect(url_for('main_routes.discount_management', store=store, success="割引を登録しました。"))
        else:
            return render_template(
                "discount_registration.html",
                store=store,
                display_name=display_name,
                error="登録に失敗しました。"
            )
    
    # GETリクエストの場合
    return render_template(
        "discount_registration.html",
        store=store,
        display_name=display_name
    )

def edit_discount_page(store, discount_id):
    """割引マスタ編集ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    discount = get_discount_by_id(db, discount_id)
    
    if discount is None:
        return redirect(url_for('main_routes.discount_management', store=store, error="割引が見つかりません。"))
    
    if request.method == "POST":
        discount_data = {
            'name': request.form.get("name"),
            'discount_type': request.form.get("discount_type", "fixed"),
            'value': float(request.form.get("value", 0)),
            'is_active': request.form.get("is_active") == "1"  # ラジオボタンの値を判定
        }
        
        # バリデーション
        if not discount_data['name']:
            return render_template(
                "discount_edit.html",
                store=store,
                discount=discount,
                display_name=display_name,
                error="割引名は必須です。"
            )
        
        if discount_data['value'] <= 0:
            return render_template(
                "discount_edit.html",
                store=store,
                discount=discount,
                display_name=display_name,
                error="割引値は0より大きい値を入力してください。"
            )
        
        # パーセント割引の場合は100以下
        if discount_data['discount_type'] == 'percent' and discount_data['value'] > 100:
            return render_template(
                "discount_edit.html",
                store=store,
                discount=discount,
                display_name=display_name,
                error="パーセント割引は100%以下で入力してください。"
            )
        
        # 名前の重複チェック（編集中の割引自身は除く）
        existing_discount = find_discount_by_name(db, discount_data['name'])
        if existing_discount and existing_discount.discount_id != discount_id:
            return render_template(
                "discount_edit.html",
                store=store,
                discount=discount,
                display_name=display_name,
                error="この割引名は既に使用されています。"
            )
        
        # 更新実行
        success = update_discount(db, discount_id, discount_data)
        
        if success:
            return redirect(url_for('main_routes.discount_management', store=store, success="割引情報を更新しました。"))
        else:
            return render_template(
                "discount_edit.html",
                store=store,
                discount=discount,
                display_name=display_name,
                error="更新に失敗しました。"
            )
    
    return render_template(
        "discount_edit.html",
        store=store,
        discount=discount,
        display_name=display_name
    )

def delete_discount_route(store, discount_id):
    """割引マスタ削除（使用されていない場合のみ完全削除）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    
    # 予約で使用されているかチェック
    if is_discount_used(db, discount_id):
        return redirect(url_for('main_routes.discount_management', store=store, 
                               error="この割引は予約で使用されているため削除できません。無効化してください。"))
    
    # 完全削除を実行
    success = delete_discount_permanently(db, discount_id)
    
    if success:
        return redirect(url_for('main_routes.discount_management', store=store, success="割引を削除しました。"))
    else:
        return redirect(url_for('main_routes.discount_management', store=store, error="削除に失敗しました。"))