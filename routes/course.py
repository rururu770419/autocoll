from flask import render_template, request, redirect, url_for, jsonify
from database.db_access import (
    get_display_name, get_db,
    get_all_courses, get_course_by_id, add_course, update_course, delete_course as db_delete_course,
    move_course_up as db_move_course_up, move_course_down as db_move_course_down,
    get_all_course_categories, add_course_category, update_course_category, delete_course_category,
    move_course_category_up as db_move_category_up, move_course_category_down as db_move_category_down
)
from database.course_db import get_all_courses as get_courses_from_db

# ========================================
# API: コース一覧取得
# ========================================
def get_courses_api(store):
    """コース一覧をJSON形式で返す（予約登録画面用）"""
    try:
        db = get_db()
        courses = get_courses_from_db(db)
        db.close()

        # course_id, course_name(name), price, time_minutes, category_id を含むデータを返す
        return jsonify([{
            'course_id': course['course_id'],
            'course_name': course['name'],  # カラム名は 'name'
            'price': course['price'] if course.get('price') else 0,
            'duration_minutes': course.get('time_minutes', 0),  # カラム名は 'time_minutes'
            'category_id': course.get('category_id')
        } for course in courses])
    except Exception as e:
        print(f"コース一覧API取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ========================================
# コース管理
# ========================================

def course_registration(store):
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
                    return redirect(url_for('main_routes.course_registration', store=store, success="カテゴリを追加しました。"))
                else:
                    return redirect(url_for('main_routes.course_registration', store=store, error="カテゴリ追加に失敗しました。"))
        
        elif action == "edit_category":
            category_id = request.form.get("category_id")
            category_name = request.form.get("name", "").strip()
            if category_id and category_name:
                if update_course_category(category_id, category_name):
                    return redirect(url_for('main_routes.course_registration', store=store, success="カテゴリを更新しました。"))
                else:
                    return redirect(url_for('main_routes.course_registration', store=store, error="カテゴリ更新に失敗しました。"))
        
        elif action == "delete_category":
            category_id = request.form.get("category_id")
            if category_id:
                if delete_course_category(category_id):
                    return redirect(url_for('main_routes.course_registration', store=store, success="カテゴリを削除しました。"))
                else:
                    return redirect(url_for('main_routes.course_registration', store=store, error="カテゴリ削除に失敗しました。"))
        
        # コース登録
        else:
            course_name = request.form.get("course_name", "").strip()
            category_id = request.form.get("category_id")
            duration_minutes_str = request.form.get("duration_minutes", "").strip()
            price_str = request.form.get("price", "").strip()
            is_active = request.form.get("is_active") == "on"
            
            # バリデーションチェック
            error_msg = None
            if not course_name:
                error_msg = "コース名を入力してください。"
            elif not category_id:
                error_msg = "カテゴリを選択してください。"
            elif not duration_minutes_str:
                error_msg = "時間を入力してください。"
            elif not price_str:
                error_msg = "料金を入力してください。"
            
            if error_msg:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_registration.html",
                    store=store,
                    display_name=display_name,
                    courses=courses,
                    categories=categories,
                    error=error_msg
                )
            
            # 数値変換チェック
            try:
                duration_minutes = int(duration_minutes_str)
                price = int(price_str)
                
                if duration_minutes <= 0:
                    raise ValueError("時間は正の整数で入力してください。")
                if price < 0:
                    raise ValueError("料金は0以上で入力してください。")
                    
            except ValueError as e:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_registration.html",
                    store=store,
                    display_name=display_name,
                    courses=courses,
                    categories=categories,
                    error=str(e)
                )
            
            # コース登録
            if add_course(course_name, category_id, duration_minutes, price, 0, is_active, store_id=1):
                return redirect(url_for('main_routes.course_registration', store=store, success="コースを登録しました。"))
            else:
                courses = get_all_courses()
                categories = get_all_course_categories()
                return render_template(
                    "course_registration.html",
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
        "course_registration.html",
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
        return redirect(url_for('main_routes.course_registration', store=store, error="コースが見つかりません。"))

    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        category_id = request.form.get("category_id")
        duration_minutes_str = request.form.get("duration_minutes", "").strip()
        price_str = request.form.get("price", "").strip()
        is_active = request.form.get("is_active") == "on"
        
        # バリデーションチェック
        error_msg = None
        if not course_name:
            error_msg = "コース名を入力してください。"
        elif not category_id:
            error_msg = "カテゴリを選択してください。"
        elif not duration_minutes_str:
            error_msg = "時間を入力してください。"
        elif not price_str:
            error_msg = "料金を入力してください。"
        
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
            duration_minutes = int(duration_minutes_str)
            price = int(price_str)
            
            if duration_minutes <= 0:
                raise ValueError("時間は正の整数で入力してください。")
            if price < 0:
                raise ValueError("料金は0以上で入力してください。")
                
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
        if update_course(course_id, course_name, category_id, duration_minutes, price, 0, is_active):
            return redirect(url_for('main_routes.course_registration', store=store, success="コース情報を更新しました。"))
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
        return redirect(url_for('main_routes.course_registration', store=store, success="コースを削除しました。"))
    else:
        return redirect(url_for('main_routes.course_registration', store=store, error="コース削除に失敗しました。"))

def move_course_up(store, course_id):
    """コース並び順上移動"""
    if db_move_course_up(course_id):
        return redirect(url_for('main_routes.course_registration', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.course_registration', store=store, error="並び順変更に失敗しました。"))

def move_course_down(store, course_id):
    """コース並び順下移動"""
    if db_move_course_down(course_id):
        return redirect(url_for('main_routes.course_registration', store=store, success="並び順を変更しました。"))
    else:
        return redirect(url_for('main_routes.course_registration', store=store, error="並び順変更に失敗しました。"))


# ========================================
# コースカテゴリ管理
# ========================================

def course_category_management_view(store):
    """カテゴリ一覧画面（register_courseにリダイレクト）"""
    return redirect(url_for('main_routes.course_registration', store=store))

def course_category_registration_view(store):
    """カテゴリ登録画面（register_courseにリダイレクト）"""
    return redirect(url_for('main_routes.course_registration', store=store))

def course_category_edit_view(store):
    """カテゴリ編集画面（register_courseにリダイレクト）"""
    return redirect(url_for('main_routes.course_registration', store=store))

# ========================================
# カテゴリ管理API
# ========================================

def add_category_endpoint(store):
    """カテゴリを追加するAPI"""
    try:
        data = request.get_json()
        
        category_name = data.get('category_name')
        is_active = data.get('is_active', True)
        
        if not category_name:
            return jsonify({'success': False, 'error': 'カテゴリ名を入力してください'})
        
        # カテゴリを追加
        if add_course_category(category_name, is_active):
            return jsonify({'success': True, 'message': 'カテゴリを登録しました'})
        else:
            return jsonify({'success': False, 'error': 'カテゴリ追加に失敗しました'})
        
    except Exception as e:
        print(f"Error in add_category_endpoint: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})

def update_category_endpoint(store):
    """カテゴリを更新するAPI"""
    try:
        data = request.get_json()
        
        category_id = data.get('category_id')
        category_name = data.get('category_name')
        is_active = data.get('is_active', True)
        
        if not category_id or not category_name:
            return jsonify({'success': False, 'error': '必須項目が入力されていません'})
        
        # カテゴリを更新
        if update_course_category(category_id, category_name, is_active):
            return jsonify({'success': True, 'message': 'カテゴリを更新しました'})
        else:
            return jsonify({'success': False, 'error': 'カテゴリ更新に失敗しました'})
        
    except Exception as e:
        print(f"Error in update_category_endpoint: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})

def delete_category_endpoint(store):
    """カテゴリを削除するAPI"""
    try:
        data = request.get_json()
        category_id = data.get('category_id')
        
        if not category_id:
            return jsonify({'success': False, 'error': 'category_idが必要です'})
        
        # このカテゴリを使用しているコースがあるかチェック
        db = get_db()
        cursor = db.execute("""
            SELECT COUNT(*) as count
            FROM courses
            WHERE category_id = %s
        """, (category_id,))
        
        result = cursor.fetchone()
        count = result['count']
        db.close()
        
        if count > 0:
            return jsonify({'success': False, 'error': 'このカテゴリを使用しているコースがあるため削除できません'})
        
        # カテゴリを削除
        if delete_course_category(category_id):
            return jsonify({'success': True, 'message': 'カテゴリを削除しました'})
        else:
            return jsonify({'success': False, 'error': 'カテゴリ削除に失敗しました'})
        
    except Exception as e:
        print(f"Error in delete_category_endpoint: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})


def update_course_endpoint(store):
    """コースを更新するAPI"""
    try:
        data = request.get_json()
        
        course_id = data.get('course_id')
        course_name = data.get('course_name')
        category_id = data.get('category_id')
        price = data.get('price')
        duration_minutes = data.get('duration_minutes')
        is_active = data.get('is_active', True)
        
        # バリデーション
        if not course_id or not course_name or not category_id:
            return jsonify({'success': False, 'error': '必須項目が入力されていません'})
        
        if not isinstance(price, int) or price < 0:
            return jsonify({'success': False, 'error': '料金は0以上で入力してください'})
        
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            return jsonify({'success': False, 'error': '時間は正の整数で入力してください'})
        
        # コースを更新
        if update_course(course_id, course_name, category_id, duration_minutes, price, 0, is_active):
            return jsonify({'success': True, 'message': 'コース情報を更新しました'})
        else:
            return jsonify({'success': False, 'error': 'コース更新に失敗しました'})
        
    except Exception as e:
        print(f"Error in update_course_endpoint: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})

def move_category_up(store, category_id):
    """カテゴリを上に移動"""
    if db_move_category_up(category_id):
        return redirect(url_for('main_routes.course_registration', store=store, success='並び順を変更しました'))
    else:
        return redirect(url_for('main_routes.course_registration', store=store, error='並び順変更に失敗しました'))

def move_category_down(store, category_id):
    """カテゴリを下に移動"""
    if db_move_category_down(category_id):
        return redirect(url_for('main_routes.course_registration', store=store, success='並び順を変更しました'))
    else:
        return redirect(url_for('main_routes.course_registration', store=store, error='並び順変更に失敗しました'))