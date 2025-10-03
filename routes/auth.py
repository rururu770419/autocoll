from flask import render_template, request, session, redirect, url_for
from database.db_access import get_display_name, find_user_by_login_id, get_db

def index(store):
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    return render_template("login.html", store=store, display_name=display_name, error=request.args.get('error'))

def login(store):
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404

    login_id = request.form["login_id"]
    password = request.form["password"]

    user = find_user_by_login_id(db, login_id)
    if user is None:
        return redirect(url_for('main_routes.index', store=store, error="ログインIDが違います"))

    if user["password"] != password:
        return redirect(url_for('main_routes.index', store=store, error="パスワードが違います"))

    session.clear()
    session['logged_in'] = True
    session['login_id'] = user['login_id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    session['store'] = store

    return redirect(url_for('main_routes.store_home', store=store))

def logout(store):
    session.clear()
    return redirect(url_for('main_routes.index', store=store))