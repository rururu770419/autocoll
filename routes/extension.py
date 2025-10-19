from flask import render_template, request, redirect, url_for, jsonify
from database.connection import get_db, get_store_id, get_display_name
from database.extension_db import (
    get_all_extensions, get_extension_by_id, register_extension,
    update_extension, delete_extension_permanently, move_extension_order
)

# ========================================
# API: 延長一覧取得
# ========================================
def get_extensions_api(store):
    """延長一覧をJSON形式で返す（予約登録画面用）"""
    try:
        store_id = get_store_id(store)
        db = get_db()
        extensions = get_all_extensions(db, store_id=store_id)
        db.close()
        # extension_id, extension_name, fee(extension_fee), extension_minutes を含むデータを返す
        return jsonify([{
            'extension_id': ext['extension_id'],
            'extension_name': ext['extension_name'],
            'fee': ext['extension_fee'] if ext.get('extension_fee') else 0,
            'extension_minutes': ext.get('extension_minutes', 0)
        } for ext in extensions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extension_management(store):
    """延長管理ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        store_id = get_store_id(store)
        db = get_db()
        extensions_data = get_all_extensions(db, store_id=store_id)
        success = request.args.get('success')
        error = request.args.get('error')

        return render_template(
            'extension.html',
            extensions=extensions_data,
            store=store,
            display_name=display_name,
            success=success,
            error=error
        )
    except Exception as e:
        print(f"延長管理ページエラー: {e}")
        import traceback
        traceback.print_exc()
        return render_template(
            'extension.html',
            extensions=[],
            store=store,
            display_name=display_name,
            error=f"延長一覧の取得に失敗しました: {str(e)}"
        )

def register_extension_route(store):
    """延長登録処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        extension_name = request.form.get('extension_name', '').strip()
        extension_fee = request.form.get('extension_fee', '').strip()
        back_amount = request.form.get('back_amount', '').strip()
        extension_minutes = request.form.get('extension_minutes', '').strip()
        is_active = True if request.form.get('is_active') == 'on' else False

        # バリデーション
        if not extension_name:
            return redirect(url_for('main_routes.extension_management', store=store, error="延長名を入力してください"))

        if not extension_fee or not extension_fee.isdigit() or int(extension_fee) < 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しい金額を入力してください"))

        if not back_amount or not back_amount.isdigit() or int(back_amount) < 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しいバック金額を入力してください"))

        if not extension_minutes or not extension_minutes.isdigit() or int(extension_minutes) <= 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しい時間を入力してください"))

        extension_fee_int = int(extension_fee)
        back_amount_int = int(back_amount)
        extension_minutes_int = int(extension_minutes)

        if back_amount_int > extension_fee_int:
            return redirect(url_for('main_routes.extension_management', store=store, error="バック金額は金額以下で入力してください"))

        # 店舗IDを動的取得
        store_id = get_store_id(store)

        # 延長登録
        db = get_db()
        extension_data = {
            'extension_name': extension_name,
            'extension_fee': extension_fee_int,
            'back_amount': back_amount_int,
            'extension_minutes': extension_minutes_int,
            'is_active': is_active,
            'store_id': store_id
        }

        result = register_extension(db, extension_data)
        print(f"register_extension結果: {result}")  # デバッグ用

        if result:
            return redirect(url_for('main_routes.extension_management', store=store, success="延長を登録しました"))
        else:
            # 既存の延長名かチェック
            from database.extension_db import find_extension_by_name
            existing = find_extension_by_name(db, extension_name, store_id)
            if existing:
                return redirect(url_for('main_routes.extension_management', store=store, error=f"延長名「{extension_name}」は既に登録されています"))
            else:
                return redirect(url_for('main_routes.extension_management', store=store, error="延長の登録に失敗しました"))

    except Exception as e:
        print(f"延長登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.extension_management', store=store, error=f"延長の登録中にエラーが発生しました: {str(e)}"))

def update_extension_route(store, extension_id):
    """延長更新処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        extension_name = request.form.get('extension_name', '').strip()
        extension_fee = request.form.get('extension_fee', '').strip()
        back_amount = request.form.get('back_amount', '').strip()
        extension_minutes = request.form.get('extension_minutes', '').strip()
        is_active_str = request.form.get('is_active', 'true')
        is_active = True if is_active_str == 'true' else False

        # バリデーション
        if not extension_name:
            return redirect(url_for('main_routes.extension_management', store=store, error="延長名を入力してください"))

        if not extension_fee or not extension_fee.isdigit() or int(extension_fee) < 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しい金額を入力してください"))

        if not back_amount or not back_amount.isdigit() or int(back_amount) < 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しいバック金額を入力してください"))

        if not extension_minutes or not extension_minutes.isdigit() or int(extension_minutes) <= 0:
            return redirect(url_for('main_routes.extension_management', store=store, error="正しい時間を入力してください"))

        extension_fee_int = int(extension_fee)
        back_amount_int = int(back_amount)
        extension_minutes_int = int(extension_minutes)

        if back_amount_int > extension_fee_int:
            return redirect(url_for('main_routes.extension_management', store=store, error="バック金額は金額以下で入力してください"))

        # 延長更新
        db = get_db()
        extension_data = {
            'extension_name': extension_name,
            'extension_fee': extension_fee_int,
            'back_amount': back_amount_int,
            'extension_minutes': extension_minutes_int,
            'is_active': is_active
        }

        if update_extension(db, extension_id, extension_data):
            return redirect(url_for('main_routes.extension_management', store=store, success="延長情報を更新しました"))
        else:
            return redirect(url_for('main_routes.extension_management', store=store, error="延長情報の更新に失敗しました"))

    except Exception as e:
        print(f"延長更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.extension_management', store=store, error="延長情報の更新中にエラーが発生しました"))

def delete_extension_route(store, extension_id):
    """延長削除処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        db = get_db()
        if delete_extension_permanently(db, extension_id):
            return redirect(url_for('main_routes.extension_management', store=store, success="延長を削除しました"))
        else:
            return redirect(url_for('main_routes.extension_management', store=store, error="延長の削除に失敗しました"))
    except Exception as e:
        print(f"延長削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.extension_management', store=store, error="延長の削除中にエラーが発生しました"))

def move_extension_up_route(store, extension_id):
    """延長並び順上移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        db = get_db()
        if move_extension_order(db, extension_id, 'up'):
            return redirect(url_for('main_routes.extension_management', store=store, success="並び順を変更しました"))
        else:
            # 既に最上位の場合はエラーを表示せずにリダイレクト
            return redirect(url_for('main_routes.extension_management', store=store))
    except Exception as e:
        print(f"並び順上移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.extension_management', store=store, error="並び順の変更中にエラーが発生しました"))

def move_extension_down_route(store, extension_id):
    """延長並び順下移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        db = get_db()
        if move_extension_order(db, extension_id, 'down'):
            return redirect(url_for('main_routes.extension_management', store=store, success="並び順を変更しました"))
        else:
            # 既に最下位の場合はエラーを表示せずにリダイレクト
            return redirect(url_for('main_routes.extension_management', store=store))
    except Exception as e:
        print(f"並び順下移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.extension_management', store=store, error="並び順の変更中にエラーが発生しました"))
