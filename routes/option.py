from flask import render_template, request, redirect, url_for
from database.db_access import (
    get_all_options, get_option_by_id, add_option, update_option, 
    delete_option, move_option_up, move_option_down, get_display_name
)

def options(store):
    """オプション管理ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        options_data = get_all_options()
        success = request.args.get('success')
        error = request.args.get('error')
        
        return render_template(
            'options.html',
            options=options_data,
            store=store,
            display_name=display_name,
            success=success,
            error=error
        )
    except Exception as e:
        print(f"オプション管理ページエラー: {e}")
        return render_template(
            'options.html',
            options=[],
            store=store,
            display_name=display_name,
            error="オプション一覧の取得に失敗しました"
        )

def register_option(store):
    """オプション登録処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        cast_back_amount = request.form.get('cast_back_amount', '').strip()
        
        # バリデーション
        if not name:
            return redirect(url_for('main_routes.options', store=store, error="オプション名を入力してください"))
        
        if not price or not price.isdigit() or int(price) < 0:
            return redirect(url_for('main_routes.options', store=store, error="正しい金額を入力してください"))
        
        if not cast_back_amount or not cast_back_amount.isdigit() or int(cast_back_amount) < 0:
            return redirect(url_for('main_routes.options', store=store, error="正しいバック金額を入力してください"))
        
        price_int = int(price)
        cast_back_amount_int = int(cast_back_amount)
        
        if cast_back_amount_int > price_int:
            return redirect(url_for('main_routes.options', store=store, error="バック金額は金額以下で入力してください"))
        
        # 店舗IDを取得（今回は1固定）
        store_id = 1
        
        # オプション登録
        if add_option(name, price_int, cast_back_amount_int, store_id):
            return redirect(url_for('main_routes.options', store=store, success="オプションを登録しました"))
        else:
            return redirect(url_for('main_routes.options', store=store, error="オプションの登録に失敗しました"))
            
    except Exception as e:
        print(f"オプション登録エラー: {e}")
        return redirect(url_for('main_routes.options', store=store, error="オプションの登録中にエラーが発生しました"))

def edit_option(store, option_id):
    """オプション編集ページ"""
    print(f"DEBUG: edit_option called with store={store}, option_id={option_id}")
    
    display_name = get_display_name(store)
    if display_name is None:
        print("DEBUG: 店舗が見つかりません")
        return "店舗が見つかりません。", 404
    
    try:
        print(f"DEBUG: get_option_by_id({option_id}) を呼び出し中...")
        option_data = get_option_by_id(option_id)
        print(f"DEBUG: option_data = {option_data}")
        
        if not option_data:
            print("DEBUG: オプションが見つかりません")
            return redirect(url_for('main_routes.options', store=store, error="指定されたオプションが見つかりません"))
        
        success = request.args.get('success')
        error = request.args.get('error')
        
        print("DEBUG: edit_option.htmlをレンダリング中...")
        return render_template(
            'edit_option.html',
            option=option_data,
            store=store,
            display_name=display_name,
            success=success,
            error=error
        )
    except Exception as e:
        print(f"オプション編集ページエラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.options', store=store, error="オプション情報の取得に失敗しました"))

def update_option_route(store, option_id):
    """オプション更新処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        cast_back_amount = request.form.get('cast_back_amount', '').strip()
        is_active_str = request.form.get('is_active', 'true')
        is_active = True if is_active_str == 'true' else False
        
        # バリデーション
        if not name:
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="オプション名を入力してください"))
        
        if not price or not price.isdigit() or int(price) < 0:
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="正しい金額を入力してください"))
        
        if not cast_back_amount or not cast_back_amount.isdigit() or int(cast_back_amount) < 0:
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="正しいバック金額を入力してください"))
        
        price_int = int(price)
        cast_back_amount_int = int(cast_back_amount)
        
        if cast_back_amount_int > price_int:
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="バック金額は金額以下で入力してください"))
        
        # オプション更新
        if update_option(option_id, name, price_int, cast_back_amount_int, is_active):
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, success="オプション情報を更新しました"))
        else:
            return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="オプション情報の更新に失敗しました"))
            
    except Exception as e:
        print(f"オプション更新エラー: {e}")
        return redirect(url_for('main_routes.edit_option', store=store, option_id=option_id, error="オプション情報の更新中にエラーが発生しました"))

def delete_option_route(store, option_id):
    """オプション削除処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        if delete_option(option_id):
            return redirect(url_for('main_routes.options', store=store, success="オプションを削除しました"))
        else:
            return redirect(url_for('main_routes.options', store=store, error="オプションの削除に失敗しました"))
    except Exception as e:
        print(f"オプション削除エラー: {e}")
        return redirect(url_for('main_routes.options', store=store, error="オプションの削除中にエラーが発生しました"))

def move_option_up_route(store, option_id):
    """オプション並び順上移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        if move_option_up(option_id):
            return redirect(url_for('main_routes.options', store=store, success="並び順を変更しました"))
        else:
            return redirect(url_for('main_routes.options', store=store, error="並び順の変更に失敗しました"))
    except Exception as e:
        print(f"並び順上移動エラー: {e}")
        return redirect(url_for('main_routes.options', store=store, error="並び順の変更中にエラーが発生しました"))

def move_option_down_route(store, option_id):
    """オプション並び順下移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    try:
        if move_option_down(option_id):
            return redirect(url_for('main_routes.options', store=store, success="並び順を変更しました"))
        else:
            return redirect(url_for('main_routes.options', store=store, error="並び順の変更に失敗しました"))
    except Exception as e:
        print(f"並び順下移動エラー: {e}")
        return redirect(url_for('main_routes.options', store=store, error="並び順の変更中にエラーが発生しました"))