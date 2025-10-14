from flask import render_template, request, redirect, url_for, jsonify
from database.connection import get_display_name, get_db
from database.hotel_db import (
    get_all_categories,
    get_all_areas,
    get_all_hotels_with_details,
    register_category as db_register_category,
    register_area as db_register_area,
    register_hotel as db_register_hotel,
    find_category_by_name,
    find_area_by_name,
    find_hotel_by_name_category_area,
    find_hotel_by_id,
    update_category,
    update_area,
    update_hotel,
    delete_category_by_id,
    delete_area_by_id,
    delete_hotel_by_id,
    move_hotel_up,
    move_hotel_down,
    move_area_up,
    move_area_down
)

def register_hotel(store):
    """ホテル管理メイン画面（登録・一覧・カテゴリ・エリア管理）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    # データベース接続を取得
    db = get_db()
    if db is None:
        return "データベース接続エラー", 500

    # 共通で使用するデータを取得（並び順指定修正）
    categories = get_all_categories(db)
    areas = get_all_areas(db)
    # 重要：sort_order順で取得するよう変更
    hotels = get_all_hotels_with_details(db, sort_by='sort_order')

    if request.method == "POST":
        action = request.form.get("action")
        
        # カテゴリ追加処理
        if action == "add_category":
            name = request.form.get("name", "").strip()
            if not name:
                return redirect(url_for('main_routes.register_hotel', store=store, error="ホテル種別名を入力してください。"))
            
            existing_category = find_category_by_name(db, name)
            if existing_category:
                return redirect(url_for('main_routes.register_hotel', store=store, error="既に登録されているホテル種別です。"))
            
            try:
                if db_register_category(db, name):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="ホテル種別を追加しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="追加中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="追加中にエラーが発生しました。"))
        
        # カテゴリ編集処理
        elif action == "edit_category":
            category_id = request.form.get("category_id")
            name = request.form.get("name", "").strip()
            if not name:
                return redirect(url_for('main_routes.register_hotel', store=store, error="ホテル種別名を入力してください。"))
            
            try:
                category_id = int(category_id)
                if update_category(db, category_id, name):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="ホテル種別を更新しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="更新中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="更新中にエラーが発生しました。"))
        
        # カテゴリ削除処理
        elif action == "delete_category":
            category_id = request.form.get("category_id")
            try:
                category_id = int(category_id)
                if delete_category_by_id(db, category_id):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="ホテル種別を削除しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))
        
        # エリア追加処理（交通費・所要時間対応）
        elif action == "add_area":
            name = request.form.get("name", "").strip()
            transportation_fee_str = request.form.get("transportation_fee", "0").strip()
            travel_time_str = request.form.get("travel_time", "0").strip()
            
            if not name:
                return redirect(url_for('main_routes.register_hotel', store=store, error="エリア名を入力してください。"))
            
            try:
                transportation_fee = int(transportation_fee_str) if transportation_fee_str else 0
                travel_time = int(travel_time_str) if travel_time_str else 0
                
                if transportation_fee < 0:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="交通費は0以上で入力してください。"))
                if travel_time < 0:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="所要時間は0以上で入力してください。"))
            except ValueError:
                return redirect(url_for('main_routes.register_hotel', store=store, error="交通費・所要時間は数値で入力してください。"))
            
            existing_area = find_area_by_name(db, name)
            if existing_area:
                return redirect(url_for('main_routes.register_hotel', store=store, error="既に登録されているエリアです。"))
            
            try:
                # db_access.pyのregister_area関数を直接使用（travel_time_minutes対応版）
                if db_register_area(db, name, transportation_fee, travel_time):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="エリアを追加しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="追加中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="追加中にエラーが発生しました。"))
        
        # エリア編集処理（交通費・所要時間対応）
        elif action == "edit_area":
            area_id = request.form.get("area_id")
            name = request.form.get("name", "").strip()
            transportation_fee_str = request.form.get("transportation_fee", "0").strip()
            travel_time_str = request.form.get("travel_time", "0").strip()
            
            if not name:
                return redirect(url_for('main_routes.register_hotel', store=store, error="エリア名を入力してください。"))
            
            try:
                area_id = int(area_id)
                transportation_fee = int(transportation_fee_str) if transportation_fee_str else 0
                travel_time = int(travel_time_str) if travel_time_str else 0
                
                if transportation_fee < 0:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="交通費は0以上で入力してください。"))
                if travel_time < 0:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="所要時間は0以上で入力してください。"))
                
                # db_access.pyのupdate_area関数を直接使用（travel_time_minutes対応版）
                if update_area(db, area_id, name, transportation_fee, travel_time):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="エリアを更新しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="更新中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="更新中にエラーが発生しました。"))
        
        # エリア削除処理
        elif action == "delete_area":
            area_id = request.form.get("area_id")
            try:
                area_id = int(area_id)
                if delete_area_by_id(db, area_id):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="エリアを削除しました。"))
                else:
                    return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))
            except Exception as e:
                return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))
        
        # 通常のホテル登録処理（additional_time削除）
        elif action is None:
            name = request.form.get("name", "").strip()
            category_id = request.form.get("category_id", "").strip()
            area_id = request.form.get("area_id", "").strip()
            
            # バリデーションチェック
            error_msg = None
            if not name:
                error_msg = "ホテル名を入力してください。"
            elif not category_id:
                error_msg = "ホテル種別を選択してください。"
            elif not area_id:
                error_msg = "エリアを選択してください。"
            
            if error_msg:
                # エラー時も最新のホテル一覧を取得
                hotels = get_all_hotels_with_details(db, sort_by='sort_order')
                return render_template(
                    "hotel_management.html",
                    store=store, display_name=display_name,
                    categories=categories, areas=areas, hotels=hotels,
                    error=error_msg
                )

            # 数値変換チェック
            try:
                category_id = int(category_id)
                area_id = int(area_id)
                    
            except ValueError as e:
                # エラー時も最新のホテル一覧を取得
                hotels = get_all_hotels_with_details(db, sort_by='sort_order')
                return render_template(
                    "hotel_management.html",
                    store=store, display_name=display_name,
                    categories=categories, areas=areas, hotels=hotels,
                    error="数値変換エラーが発生しました。"
                )

            # 重複チェック
            existing_hotel = find_hotel_by_name_category_area(db, name, category_id, area_id)
            if existing_hotel:
                # エラー時も最新のホテル一覧を取得
                hotels = get_all_hotels_with_details(db, sort_by='sort_order')
                return render_template(
                    "hotel_management.html",
                    store=store, display_name=display_name,
                    categories=categories, areas=areas, hotels=hotels,
                    error="同じ名前・カテゴリ・エリアのホテルは既に登録されています。"
                )

            # ホテル登録（additional_timeを0で固定）
            try:
                if db_register_hotel(db, name, category_id, area_id, 0, 0):
                    return redirect(url_for('main_routes.register_hotel', store=store, success="ホテルを登録しました。"))
                else:
                    # エラー時も最新のホテル一覧を取得
                    hotels = get_all_hotels_with_details(db, sort_by='sort_order')
                    return render_template(
                        "hotel_management.html",
                        store=store, display_name=display_name,
                        categories=categories, areas=areas, hotels=hotels,
                        error="登録中にエラーが発生しました。"
                    )
            except Exception as e:
                # エラー時も最新のホテル一覧を取得
                hotels = get_all_hotels_with_details(db, sort_by='sort_order')
                return render_template(
                    "hotel_management.html",
                    store=store, display_name=display_name,
                    categories=categories, areas=areas, hotels=hotels,
                    error="登録中にエラーが発生しました。"
                )
        
    # GETリクエストの場合
    success_msg = request.args.get('success')
    error_msg = request.args.get('error')
    
    return render_template(
        "hotel_management.html",
        store=store, display_name=display_name,
        categories=categories, areas=areas, hotels=hotels,
        success=success_msg, error=error_msg
    )

def edit_hotel(store, hotel_id):
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    # データベース接続を取得
    db = get_db()
    if db is None:
        return "データベース接続エラー", 500

    # ホテル情報を取得（詳細情報含む）
    hotel = find_hotel_by_id(db, hotel_id)
    if hotel is None:
        return redirect(url_for('main_routes.register_hotel', store=store, error="ホテルが見つかりません。"))
    
    # カテゴリとエリア一覧を取得
    categories = get_all_categories(db)
    areas = get_all_areas(db)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id", "").strip()
        area_id = request.form.get("area_id", "").strip()
        is_active = request.form.get("is_active") == "on"
        
        # バリデーションチェック
        error_msg = None
        if not name:
            error_msg = "ホテル名を入力してください。"
        elif not category_id:
            error_msg = "ホテル種別を選択してください。"
        elif not area_id:
            error_msg = "エリアを選択してください。"
        
        if error_msg:
            return render_template(
                "hotel_edit.html",
                store=store, display_name=display_name,
                hotel=hotel, categories=categories, areas=areas,
                error=error_msg
            )

        # 数値変換チェック
        try:
            category_id = int(category_id)
            area_id = int(area_id)
                
        except ValueError as e:
            return render_template(
                "hotel_edit.html",
                store=store, display_name=display_name,
                hotel=hotel, categories=categories, areas=areas,
                error="数値変換エラーが発生しました。"
            )

        # 重複チェック（編集中のホテル自身は除く）
        existing_hotel = find_hotel_by_name_category_area(db, name, category_id, area_id)
        if existing_hotel and existing_hotel['hotel_id'] != hotel_id:
            return render_template(
                "hotel_edit.html",
                store=store, display_name=display_name,
                hotel=hotel, categories=categories, areas=areas,
                error="同じ名前・カテゴリ・エリアのホテルは既に登録されています。"
            )

        # ホテル更新（additional_timeを0で固定）
        try:
            if update_hotel(db, hotel_id, name, category_id, area_id, 0, 0, is_active):
                return redirect(url_for('main_routes.register_hotel', store=store, success="ホテル情報を更新しました。"))
            else:
                return render_template(
                    "hotel_edit.html",
                    store=store, display_name=display_name,
                    hotel=hotel, categories=categories, areas=areas,
                    error="更新中にエラーが発生しました。"
                )
        except Exception as e:
            return render_template(
                "hotel_edit.html",
                store=store, display_name=display_name,
                hotel=hotel, categories=categories, areas=areas,
                error="更新中にエラーが発生しました。"
            )

    # GETリクエストの場合、編集フォームを表示
    return render_template(
        "hotel_edit.html",
        store=store, display_name=display_name,
        hotel=hotel, categories=categories, areas=areas
    )


def delete_hotel(store, hotel_id):
    """ホテル削除"""
    try:
        db = get_db()
        if db is None:
            return redirect(url_for('main_routes.register_hotel', store=store, error="データベース接続エラー"))
        
        if delete_hotel_by_id(db, hotel_id):
            return redirect(url_for('main_routes.register_hotel', store=store, success="ホテルを削除しました。"))
        else:
            return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))
    except Exception as e:
        return redirect(url_for('main_routes.register_hotel', store=store, error="削除中にエラーが発生しました。"))

def move_hotel_up_route(store, hotel_id):
    """ホテル並び順上移動"""
    if move_hotel_up(hotel_id):
        return redirect(url_for('main_routes.register_hotel', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.register_hotel', store=store, error="並び順変更に失敗しました。"))

def move_hotel_down_route(store, hotel_id):
    """ホテル並び順下移動"""
    if move_hotel_down(hotel_id):
        return redirect(url_for('main_routes.register_hotel', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.register_hotel', store=store, error="並び順変更に失敗しました。"))

# 単独ページ用の関数（後方互換性）
def register_category(store):
    pass

def register_area(store):
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホテル管理API（新規追加）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホテル管理種別API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_hotel_types_api(store):
    """ホテル管理種別一覧取得API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        categories = get_all_categories(db)
        
        # 辞書形式に変換
        data = []
        for category in categories:
            data.append({
                "hotel_type_id": category['category_id'],
                "type_name": category['name']
            })
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def add_hotel_type_api(store):
    """ホテル管理種別追加API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        type_name = data.get('type_name', '').strip()
        
        if not type_name:
            return jsonify({"success": False, "message": "種別名を入力してください"}), 400
        
        # 重複チェック
        existing = find_category_by_name(db, type_name)
        if existing:
            return jsonify({"success": False, "message": "既に登録されている種別名です"}), 400
        
        # 登録
        result = db_register_category(db, type_name)
        
        if result:
            return jsonify({"success": True, "message": "ホテル管理種別を追加しました"})
        else:
            return jsonify({"success": False, "message": "追加に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def update_hotel_type_api(store, id):
    """ホテル管理種別更新API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        type_name = data.get('type_name', '').strip()
        
        if not type_name:
            return jsonify({"success": False, "message": "種別名を入力してください"}), 400
        
        # 更新
        result = update_category(db, id, type_name)
        
        if result:
            return jsonify({"success": True, "message": "ホテル管理種別を更新しました"})
        else:
            return jsonify({"success": False, "message": "更新に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def delete_hotel_type_api(store, id):
    """ホテル管理種別削除API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        # 削除
        if delete_category_by_id(db, id):
            return jsonify({"success": True, "message": "ホテル管理種別を削除しました"})
        else:
            return jsonify({"success": False, "message": "削除に失敗しました。この種別を使用しているホテルがある可能性があります"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エリア管理API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_areas_api(store):
    """エリア一覧取得API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        areas = get_all_areas(db)
        
        # 辞書形式に変換
        data = []
        for area in areas:
            data.append({
                "area_id": area['area_id'],
                "area_name": area['name'],
                "transportation_fee": area.get('transportation_fee', 0),
                "travel_time": area.get('travel_time_minutes', 0)
            })
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def add_area_api(store):
    """エリア追加API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        area_name = data.get('area_name', '').strip()
        transportation_fee = data.get('transportation_fee', 0)
        travel_time = data.get('travel_time', 0)
        
        if not area_name:
            return jsonify({"success": False, "message": "エリア名を入力してください"}), 400
        
        # 数値チェック
        try:
            transportation_fee = int(transportation_fee) if transportation_fee else 0
            travel_time = int(travel_time) if travel_time else 0
            
            if transportation_fee < 0 or travel_time < 0:
                return jsonify({"success": False, "message": "交通費と所要時間は0以上で入力してください"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "交通費と所要時間は数値で入力してください"}), 400
        
        # 重複チェック
        existing = find_area_by_name(db, area_name)
        if existing:
            return jsonify({"success": False, "message": "既に登録されているエリア名です"}), 400
        
        # 登録
        if db_register_area(db, area_name, transportation_fee, travel_time):
            return jsonify({"success": True, "message": "エリアを追加しました"})
        else:
            return jsonify({"success": False, "message": "追加に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def update_area_api(store, id):
    """エリア更新API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        
        area_name = data.get('area_name', '').strip()
        transportation_fee = data.get('transportation_fee', 0)
        travel_time = data.get('travel_time', 0)
        
        if not area_name:
            return jsonify({"success": False, "message": "エリア名を入力してください"}), 400
        
        # 数値チェック
        try:
            transportation_fee = int(transportation_fee) if transportation_fee else 0
            travel_time = int(travel_time) if travel_time else 0
            
            if transportation_fee < 0 or travel_time < 0:
                return jsonify({"success": False, "message": "交通費と所要時間は0以上で入力してください"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "交通費と所要時間は数値で入力してください"}), 400
        
        # 更新
        result = update_area(db, id, area_name, transportation_fee, travel_time)
        
        if result:
            return jsonify({"success": True, "message": "エリアを更新しました"})
        else:
            return jsonify({"success": False, "message": "更新に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def delete_area_api(store, id):
    """エリア削除API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        # 削除
        if delete_area_by_id(db, id):
            return jsonify({"success": True, "message": "エリアを削除しました"})
        else:
            return jsonify({"success": False, "message": "削除に失敗しました。このエリアを使用しているホテルがある可能性があります"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホテル管理API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_hotels_api(store):
    """ホテル一覧取得API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        hotels = get_all_hotels_with_details(db, sort_by='sort_order')
        
        # 辞書形式に変換
        data = []
        for hotel in hotels:
            data.append({
                "hotel_id": hotel['hotel_id'],
                "hotel_name": hotel['hotel_name'],
                "hotel_type_id": hotel.get('category_id'),
                "type_name": hotel.get('category_name', '-'),
                "area_id": hotel.get('area_id'),
                "area_name": hotel.get('area_name', '-'),
                "is_active": hotel.get('is_active', True)
            })
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def get_hotel_api(store, id):
    """ホテル詳細取得API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        hotel = find_hotel_by_id(db, id)
        
        if not hotel:
            return jsonify({"success": False, "message": "ホテルが見つかりません"}), 404
        
        data = {
            "hotel_id": hotel['hotel_id'],
            "hotel_name": hotel['hotel_name'],
            "hotel_type_id": hotel.get('category_id'),
            "area_id": hotel.get('area_id'),
            "is_active": hotel.get('is_active', True)
        }
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def add_hotel_api(store):
    """ホテル追加API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        hotel_name = (data.get('hotel_name') or '').strip()
        hotel_type_id = data.get('hotel_type_id')
        area_id = data.get('area_id')
        
        if not hotel_name:
            return jsonify({"success": False, "message": "ホテル名を入力してください"}), 400
        
        if not hotel_type_id:
            return jsonify({"success": False, "message": "種別を選択してください"}), 400
        
        if not area_id:
            return jsonify({"success": False, "message": "エリアを選択してください"}), 400
        
        # 重複チェック
        existing = find_hotel_by_name_category_area(db, hotel_name, hotel_type_id, area_id)
        if existing:
            return jsonify({"success": False, "message": "同じ名前・種別・エリアのホテルは既に登録されています"}), 400
        
        # 登録（additional_timeを0で固定）
        if db_register_hotel(db, hotel_name, hotel_type_id, area_id, 0, 0):
            return jsonify({"success": True, "message": "ホテルを登録しました"})
        else:
            return jsonify({"success": False, "message": "登録に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def update_hotel_api(store, id):
    """ホテル更新API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        data = request.get_json()
        
        hotel_name = (data.get('hotel_name') or '').strip()
        hotel_type_id = data.get('hotel_type_id')
        area_id = data.get('area_id')
        
        if not hotel_name:
            return jsonify({"success": False, "message": "ホテル名を入力してください"}), 400
        
        if not hotel_type_id:
            return jsonify({"success": False, "message": "種別を選択してください"}), 400
        
        if not area_id:
            return jsonify({"success": False, "message": "エリアを選択してください"}), 400
        
        # 重複チェック（自分自身は除く）
        existing = find_hotel_by_name_category_area(db, hotel_name, hotel_type_id, area_id)
        if existing and existing['hotel_id'] != id:
            return jsonify({"success": False, "message": "同じ名前・種別・エリアのホテルは既に登録されています"}), 400
        
        # 更新（additional_timeを0で固定、is_activeはTrueに固定）
        if update_hotel(db, id, hotel_name, hotel_type_id, area_id, 0, 0, True):
            return jsonify({"success": True, "message": "ホテル情報を更新しました"})
        else:
            return jsonify({"success": False, "message": "更新に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def delete_hotel_api(store, id):
    """ホテル削除API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        # 削除
        if delete_hotel_by_id(db, id):
            return jsonify({"success": True, "message": "ホテルを削除しました"})
        else:
            return jsonify({"success": False, "message": "削除に失敗しました"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 並び替えAPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def move_area_up_api(store, id):
    """エリア並び替え（上）API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        if move_area_up(db, id):
            return jsonify({"success": True, "message": "並び順を変更しました"})
        else:
            return jsonify({"success": False, "message": "並び替えに失敗しました"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def move_area_down_api(store, id):
    """エリア並び替え（下）API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        if move_area_down(db, id):
            return jsonify({"success": True, "message": "並び順を変更しました"})
        else:
            return jsonify({"success": False, "message": "並び替えに失敗しました"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def move_hotel_up_api(store, id):
    """ホテル並び替え（上）API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        # move_hotel_upは既にget_db()を内部で呼んでいるので、idのみ渡す
        if move_hotel_up(id):
            return jsonify({"success": True, "message": "並び順を変更しました"})
        else:
            return jsonify({"success": False, "message": "並び替えに失敗しました"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500

def move_hotel_down_api(store, id):
    """ホテル並び替え（下）API"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"success": False, "message": "データベース接続エラー"}), 500
        
        # move_hotel_downは既にget_db()を内部で呼んでいるので、idのみ渡す
        if move_hotel_down(id):
            return jsonify({"success": True, "message": "並び順を変更しました"})
        else:
            return jsonify({"success": False, "message": "並び替えに失敗しました"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"エラーが発生しました: {str(e)}"}), 500