from flask import render_template, request, redirect, url_for
from database.db_access import (
    get_display_name, get_all_categories, get_all_areas,
    get_all_hotels_with_details, register_category as db_register_category,
    register_area as db_register_area, register_hotel as db_register_hotel,
    find_category_by_name, find_area_by_name, find_hotel_by_name_category_area,
    find_hotel_by_id, update_category, update_area, update_hotel,
    delete_category_by_id, delete_area_by_id, delete_hotel_by_id,
    move_hotel_up, move_hotel_down, get_db
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
    
    # デバッグ出力を追加
    print(f"Debug - Hotel data: {hotel}")
    if hotel:
        print(f"Debug - travel_time_minutes: {getattr(hotel, 'travel_time_minutes', 'No attribute')}")
        print(f"Debug - Hotel attributes: {dir(hotel)}")
    
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