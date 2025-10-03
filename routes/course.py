from flask import render_template, request, redirect, url_for
from database.db_access import (
    get_display_name, 
    get_all_courses, get_course_by_id, add_course, update_course, delete_course as db_delete_course,
    move_course_up as db_move_course_up, move_course_down as db_move_course_down, get_all_course_categories, 
    add_course_category, update_course_category, delete_course_category
)

def register_course(store):
    """コース管理メイン画面（登録・一覧・カテゴリ管理）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    if request.method == "POST":
        action = request.form.get("action")
        
        # カテゴリ管理
        if action == "add_category":
            category_name = request.form.get("name", "").strip()
            if category_name:
                if add_course_category(category_name):
                    return redirect(url_for('main_routes.register_course', store=store, success="カテゴリを追加しました。"))
                else:
                    return redirect(url_for('main_routes.register_course', store=store, error="カテゴリ追加に失敗しました。"))
        
        elif action == "edit_category":
            category_id = request.form.get("category_id")
            category_name = request.form.get("name", "").strip()
            if category_id and category_name:
                if update_course_category(category_id, category_name):
                    return redirect(url_for('main_routes.register_course', store=store, success="カテゴリを更新しました。"))
                else:
                    return redirect(url_for('main_routes.register_course', store=store, error="カテゴリ更新に失敗しました。"))
        
        elif action == "delete_category":
            category_id = request.form.get("category_id")
            if category_id:
                if delete_course_category(category_id):
                    return redirect(url_for('main_routes.register_course', store=store, success="カテゴリを削除しました。"))
                else:
                    return redirect(url_for('main_routes.register_course', store=store, error="カテゴリ削除に失敗しました。"))
        
        # コース登録
        else:
            name = request.form.get("name", "").strip()
            category_id = request.form.get("category_id")
            time_minutes_str = request.form.get("time_minutes", "").strip()
            price_str = request.form.get("price", "").strip()
            cast_back_amount_str = request.form.get("cast_back_amount", "").strip()
            
            # バリデーションチェック
            error_msg = None
            if not name:
                error_msg = "コース名を入力してください。"
            elif not category_id:
                error_msg = "カテゴリを選択してください。"
            elif not time_minutes_str:
                error_msg = "時間を入力してください。"
            elif not price_str:
                error_msg = "料金を入力してください。"
            elif not cast_back_amount_str:
                error_msg = "バック金額を入力してください。"
            
            if error_msg:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_management.html",
                    store=store,
                    display_name=display_name,
                    courses=courses,
                    categories=categories,
                    error=error_msg
                )
            
            # 数値変換チェック
            try:
                time_minutes = int(time_minutes_str)
                price = int(price_str)
                cast_back_amount = int(cast_back_amount_str)
                
                if time_minutes <= 0:
                    raise ValueError("時間は正の整数で入力してください。")
                if price < 0:
                    raise ValueError("料金は0以上で入力してください。")
                if cast_back_amount < 0:
                    raise ValueError("バック金額は0以上で入力してください。")
                    
            except ValueError as e:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_management.html",
                    store=store,
                    display_name=display_name,
                    courses=courses,
                    categories=categories,
                    error=str(e)
                )
            
            # コース登録
            if add_course(name, category_id, time_minutes, price, cast_back_amount):
                return redirect(url_for('main_routes.register_course', store=store, success="コースを登録しました。"))
            else:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_management.html",
                    store=store,
                    display_name=display_name,
                    courses=courses,
                    categories=categories,
                    error="コース登録に失敗しました。"
                )
    
    # GETリクエストの場合、登録フォームとコース一覧を表示
    courses = get_all_courses()
    categories = get_all_course_categories()
    success_msg = request.args.get('success')
    error_msg = request.args.get('error')
    
    return render_template(
        "course_management.html",
        store=store,
        display_name=display_name,
        courses=courses,
        categories=categories,
        success=success_msg,
        error=error_msg
    )

def edit_course(store, course_id):
    """コース編集画面"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    course = get_course_by_id(course_id)
    if course is None:
        return redirect(url_for('main_routes.register_course', store=store, error="コースが見つかりません。"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        time_minutes_str = request.form.get("time_minutes", "").strip()
        price_str = request.form.get("price", "").strip()
        cast_back_amount_str = request.form.get("cast_back_amount", "").strip()
        is_active = request.form.get("is_active") == "on"
        
        # バリデーションチェック
        error_msg = None
        if not name:
            error_msg = "コース名を入力してください。"
        elif not category_id:
            error_msg = "カテゴリを選択してください。"
        elif not time_minutes_str:
            error_msg = "時間を入力してください。"
        elif not price_str:
            error_msg = "料金を入力してください。"
        elif not cast_back_amount_str:
            error_msg = "バック金額を入力してください。"
        
        if error_msg:
            categories = get_all_course_categories()
            return render_template(
                "course_edit.html",
                store=store,
                display_name=display_name,
                course=course,
                categories=categories,
                error=error_msg
            )
        
        # 数値変換チェック
        try:
            time_minutes = int(time_minutes_str)
            price = int(price_str)
            cast_back_amount = int(cast_back_amount_str)
            
            if time_minutes <= 0:
                raise ValueError("時間は正の整数で入力してください。")
            if price < 0:
                raise ValueError("料金は0以上で入力してください。")
            if cast_back_amount < 0:
                raise ValueError("バック金額は0以上で入力してください。")
                
        except ValueError as e:
            categories = get_all_course_categories()
            return render_template(
                "course_edit.html",
                store=store,
                display_name=display_name,
                course=course,
                categories=categories,
                error=str(e)
            )
        
        # コース更新
        if update_course(course_id, name, category_id, time_minutes, price, cast_back_amount, is_active):
            return redirect(url_for('main_routes.register_course', store=store, success="コース情報を更新しました。"))
        else:
            categories = get_all_course_categories()
            return render_template(
                "course_edit.html",
                store=store,
                display_name=display_name,
                course=course,
                categories=categories,
                error="コース更新に失敗しました。"
            )
    
    categories = get_all_course_categories()
    return render_template(
        "course_edit.html",
        store=store,
        display_name=display_name,
        course=course,
        categories=categories
    )

def delete_course(store, course_id):
    """コース削除"""
    if db_delete_course(course_id):
        return redirect(url_for('main_routes.register_course', store=store, success="コースを削除しました。"))
    else:
        return redirect(url_for('main_routes.register_course', store=store, error="コース削除に失敗しました。"))

def move_course_up(store, course_id):
    """コース並び順上移動"""
    if db_move_course_up(course_id):
        return redirect(url_for('main_routes.register_course', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.register_course', store=store, error="並び順変更に失敗しました。"))

def move_course_down(store, course_id):
    """コース並び順下移動"""
    if db_move_course_down(course_id):
        return redirect(url_for('main_routes.register_course', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.register_course', store=store, error="並び順変更に失敗しました。"))