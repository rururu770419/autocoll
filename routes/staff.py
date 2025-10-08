# staff_routes.py - PostgreSQL対応版（本番用）

import psycopg
from flask import render_template, request, redirect, url_for, flash, jsonify
from database.db_access import (
    get_display_name, get_db, register_user, get_all_users,
    find_user_by_name, find_user_by_login_id
)
from database.db_connection import get_db_connection


def get_line_bot_id():
    """
    store_settingsテーブルからLINE Bot IDを取得（全店舗共通）
    
    Returns:
        str: LINE Bot ID（例: @275gmabd）、取得できない場合はNone
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT setting_value 
            FROM store_settings 
            WHERE setting_key = 'line_bot_id'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            return result[0]
        return None
        
    except Exception as e:
        print(f"❌ LINE Bot ID取得エラー: {e}")
        return None


def register_staff(store):
    """スタッフ一覧表示"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    if request.method == "GET":
        db = get_db(store)
        
        if db is None:
            return render_template("staff_list.html", 
                                 store=store, 
                                 display_name=display_name, 
                                 users=[],
                                 success=None,
                                 error="データベース接続エラー")
        
        try:
            cursor = db.cursor()
            cursor.execute("""
                SELECT id, name, login_id, role, color, 
                       COALESCE(line_id, '') as line_id,
                       COALESCE(notification_minutes_before, 10) as notification_minutes_before,
                       COALESCE(line_notification_enabled, false) as line_notification_enabled,
                       password
                FROM users 
                WHERE is_active = true
                ORDER BY name
            """)
            users = cursor.fetchall()
                
        except Exception as e:
            users = []
        
        success_msg = request.args.get('success')
        error_msg = request.args.get('error')
        
        return render_template("staff_list.html", 
                             store=store, 
                             display_name=display_name, 
                             users=users,
                             success=success_msg,
                             error=error_msg)


def new_staff(store):
    """新規スタッフ登録ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    line_bot_id = get_line_bot_id()
    
    return render_template("staff_edit.html", 
                         store=store, 
                         display_name=display_name,
                         user=None,
                         mode='new',
                         line_bot_id=line_bot_id)


def edit_staff(store, user_id):
    """スタッフ編集ページ（IDベース）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
        
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404

    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, login_id, role, color, 
                   COALESCE(line_id, '') as line_id,
                   COALESCE(notification_minutes_before, 10) as notification_minutes_before,
                   COALESCE(line_notification_enabled, false) as line_notification_enabled,
                   password
            FROM users 
            WHERE id = %s AND is_active = true
        """, (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            return redirect(url_for('main_routes.register_staff', store=store, error="ユーザーが見つかりません。"))
            
    except Exception as e:
        return redirect(url_for('main_routes.register_staff', store=store, error=f"エラーが発生しました: {str(e)}"))

    line_bot_id = get_line_bot_id()

    return render_template("staff_edit.html",
                         store=store,
                         user=user,
                         display_name=display_name,
                         mode='edit',
                         line_bot_id=line_bot_id)


def save_staff(store):
    """スタッフ情報保存（新規・更新共通処理）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
        
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404

    user_id = request.form.get("user_id")
    name = request.form.get("name")
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    role = request.form.get("role")
    color = request.form.get("color", "#FFE5E5")
    line_id = request.form.get("line_id", "").strip()
    notification_minutes = int(request.form.get("notification_minutes_before", 10))
    notification_enabled = 'line_notification_enabled' in request.form

    if not all([name, login_id, password, role]):
        error_msg = "全ての必須項目を入力してください。"
        if user_id:
            return redirect(url_for('main_routes.edit_staff_by_id', store=store, user_id=user_id, error=error_msg))
        else:
            return redirect(url_for('main_routes.new_staff', store=store, error=error_msg))

    try:
        cursor = db.cursor()
        
        if user_id:
            cursor.execute(
                "SELECT id FROM users WHERE login_id = %s AND id != %s AND is_active = true", 
                (login_id, user_id)
            )
            existing_user = cursor.fetchone()
            
            if existing_user:
                return redirect(url_for('main_routes.edit_staff_by_id', store=store, user_id=user_id, error="このログインIDは既に使用されています。"))
            
            cursor.execute("""
                UPDATE users SET 
                    name = %s, login_id = %s, password = %s, role = %s, color = %s,
                    line_id = %s, notification_minutes_before = %s, line_notification_enabled = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (name, login_id, password, role, color, line_id, notification_minutes, notification_enabled, user_id))
            
            success_msg = f"{name}さんの情報を更新しました。"
            
        else:
            cursor.execute("SELECT id FROM users WHERE name = %s AND is_active = true", (name,))
            existing_user_by_name = cursor.fetchone()
            
            cursor.execute("SELECT id FROM users WHERE login_id = %s AND is_active = true", (login_id,))
            existing_user_by_login_id = cursor.fetchone()

            if existing_user_by_name:
                return redirect(url_for('main_routes.new_staff', store=store, error="既に登録されている名前です。"))
            if existing_user_by_login_id:
                return redirect(url_for('main_routes.new_staff', store=store, error="既に登録されているログインIDです。"))

            cursor.execute("""
                INSERT INTO users (name, login_id, password, role, color, line_id, notification_minutes_before, line_notification_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, login_id, password, role, color, line_id, notification_minutes, notification_enabled))
            
            success_msg = f"{name}さんを登録しました。"
        
        db.commit()
        return redirect(url_for('main_routes.register_staff', store=store, success=success_msg))
        
    except psycopg.IntegrityError:
        return redirect(url_for('main_routes.register_staff', store=store, error="登録中にエラーが発生しました。"))
    except Exception as e:
        return redirect(url_for('main_routes.register_staff', store=store, error=f"エラーが発生しました: {str(e)}"))


def delete_staff(store, user_id):
    """スタッフ削除（IDベース）"""
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404
    
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("UPDATE users SET is_active = false WHERE id = %s", (user_id,))
            db.commit()
            success_msg = f"{user['name']}さんを削除しました。"
        else:
            success_msg = "指定されたスタッフが見つかりませんでした。"

    except Exception as e:
        success_msg = "削除中にエラーが発生しました。"

    return redirect(url_for('main_routes.register_staff', store=store, success=success_msg))


def get_line_bot_info(store):
    """LINE Bot情報をJSONで返す"""
    return jsonify({
        'qr_url': '/static/images/line_qr.jpg',
        'instructions': [
            '1. 上記QRコードをスマホで読み取り、Botを友だち追加してください',
            '2. Botに「ID」とメッセージを送信してください',
            '3. 返ってきたUser ID（Uで始まる文字列）をコピーしてください',
            '4. 下記の「LINE User ID」欄に貼り付けて保存してください'
        ]
    })