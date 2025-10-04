import re
import os
import json
from datetime import datetime
from flask import Blueprint
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for
from database.connection import get_db, get_display_name
from database.cast_db import (
    register_cast as db_register_cast,
    get_all_casts, find_cast_by_name, find_cast_by_phone_number, find_cast_by_id,
    get_all_casts_with_details, update_cast, delete_cast as db_delete_cast,
    get_cast_with_age  # ← この行を追加
)


# ファイルアップロード設定
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

cast_bp = Blueprint('cast', __name__, url_prefix='/cast')

def allowed_file(filename):
    """ファイル拡張子のチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_cast_file(file, cast_id, file_type):
    """
    キャストのファイルを保存
    
    Args:
        file: アップロードファイルオブジェクト
        cast_id: キャストID
        file_type: ファイルタイプ ('id_document' or 'contract_document')
    
    Returns:
        str: 保存されたファイルの相対パス（static/からの相対パス）
    """
    if file and allowed_file(file.filename):
        # ファイル名を安全にする
        filename = secure_filename(file.filename)
        
        # タイムスタンプを追加してファイル名の重複を防ぐ
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{file_type}_{timestamp}{ext}"
        
        # 保存先ディレクトリを作成
        upload_dir = os.path.join('static', 'uploads', 'cast', str(cast_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # ファイルを保存
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # データベース保存用の相対パス（static/からの相対パス）
        relative_path = os.path.join('uploads', 'cast', str(cast_id), filename)
        return relative_path
    
    return None

def delete_cast_file(file_path):
    """
    キャストのファイルを削除
    
    Args:
        file_path: ファイルの相対パス（uploads/cast/{cast_id}/...）
    """
    try:
        full_path = os.path.join('static', file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"ファイル削除成功: {full_path}")
            return True
    except Exception as e:
        print(f"ファイル削除エラー: {e}")
    return False

def cast_management(store):
    """キャスト一覧ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    casts = get_all_casts_with_details(db)
    
    return render_template('cast_management.html', 
                         store=store, 
                         display_name=display_name, 
                         casts=casts)

def register_cast(store):
    """キャスト登録ページ（基本情報のみ）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name")
        phone_number = request.form.get("phone_number")
        
        # バリデーションチェック
        if not name or not phone_number:
            casts = get_all_casts(db)
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                casts=casts,
                error="全ての項目を入力してください。"
            )

        # 電話番号のバリデーション（半角数字11桁）
        if not re.fullmatch(r'\d{11}', phone_number):
            casts = get_all_casts(db)
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                casts=casts,
                error="電話番号は半角数字11桁で入力してください。"
            )

        # 重複チェック
        existing_cast_by_name = find_cast_by_name(db, name)
        if existing_cast_by_name:
            casts = get_all_casts(db)
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                casts=casts,
                error="既に登録されているキャスト名です。"
            )
            
        existing_cast_by_phone = find_cast_by_phone_number(db, phone_number)
        if existing_cast_by_phone:
            casts = get_all_casts(db)
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                casts=casts,
                error="既に登録されている電話番号です。"
            )

        # 全てのチェックを通過したら登録
        db_register_cast(db, name, phone_number)
        
        return redirect(url_for('main_routes.cast_management', store=store, success="キャストを登録しました。"))
        
    # GETリクエストの場合、登録フォームを表示
    success_msg = request.args.get('success')
    error_msg = request.args.get('error')
    
    return render_template(
        "cast_registration.html",
        store=store,
        display_name=display_name,
        success=success_msg,
        error=error_msg
    )

def edit_cast(store, cast_id):
    """キャスト編集ページ（詳細情報対応 + ファイルアップロード）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    db = get_db()
    # 年齢計算込みのキャスト情報を取得
    cast = get_cast_with_age(db, cast_id)
    
    if cast is None:
        return redirect(url_for('main_routes.cast_management', store=store, error="キャストが見つかりません。"))

    if request.method == "POST":
        # 基本情報の取得
        # 住所の結合処理
        prefecture = request.form.get("prefecture", "")
        city = request.form.get("city", "")
        address_detail = request.form.get("address_detail", "")
        full_address = " ".join(filter(None, [prefecture, city, address_detail]))
        
        # ログインIDの処理（空欄の場合は既存のIDを維持）
        new_login_id = request.form.get("login_id", "").strip()
        if not new_login_id:
            new_login_id = cast['login_id']  # 既存のIDを維持
        
        cast_data = {
            'name': request.form.get("name"),
            'phone_number': request.form.get("phone_number"),
            'email': request.form.get("email"),
            'birth_date': request.form.get("birth_date") or None,
            'address': full_address,
            'join_date': request.form.get("join_date") or None,
            'status': request.form.get("status", '在籍'),
            'recruitment_source': request.form.get("recruitment_source"),
            'transportation_fee': int(request.form.get("transportation_fee", 0)),
            'comments': request.form.get("comments"),
            'login_id': new_login_id,
        }
        
        # 対応コースの処理
        course_category = request.form.get("course_category")
        if course_category:
            cast_data['available_course_categories'] = [course_category]
        else:
            cast_data['available_course_categories'] = []
        
        # パスワードが入力されている場合のみ更新
        password = request.form.get("password")
        if password:
            cast_data['password'] = password
        
        # バリデーション
        if not cast_data['name']:
            return render_template(
                "cast_edit.html",
                store=store,
                cast=cast,
                display_name=display_name,
                error="キャスト名は必須です。"
            )
        
        # 名前の重複チェック（編集中のキャスト自身は除く）
        existing_cast_by_name = find_cast_by_name(db, cast_data['name'])
        if existing_cast_by_name and existing_cast_by_name['cast_id'] != cast_id:
            return render_template(
                "cast_edit.html",
                store=store,
                cast=cast,
                display_name=display_name,
                error="このキャスト名は既に使用されています。"
            )
        
        # 電話番号の重複チェック
        if cast_data['phone_number']:
            existing_cast_by_phone = find_cast_by_phone_number(db, cast_data['phone_number'])
            if existing_cast_by_phone and existing_cast_by_phone['cast_id'] != cast_id:
                return render_template(
                    "cast_edit.html",
                    store=store,
                    cast=cast,
                    display_name=display_name,
                    error="この電話番号は既に使用されています。"
                )
        
        # ログインIDの重複チェック（修正版）
        if cast_data.get('login_id'):
            from database.cast_db import find_cast_by_login_id
            existing_cast_by_login = find_cast_by_login_id(db, cast_data['login_id'])
            # 編集中のキャスト自身のログインIDは除外
            if existing_cast_by_login and existing_cast_by_login['cast_id'] != cast_id:
                return render_template(
                    "cast_edit.html",
                    store=store,
                    cast=cast,
                    display_name=display_name,
                    error=f"このログインID '{cast_data['login_id']}' は既に使用されています。"
                )

        # === ファイルアップロード処理 ===
        
        # 既存のファイルパスを取得
        existing_id_docs = json.loads(cast['id_document_paths']) if cast.get('id_document_paths') else []
        existing_contract_docs = json.loads(cast['contract_document_paths']) if cast.get('contract_document_paths') else []
        
        # 削除対象ファイルの処理
        deleted_id_docs = request.form.getlist('deleted_id_documents')
        deleted_contract_docs = request.form.getlist('deleted_contract_documents')
        
        # 削除対象ファイルを実際に削除
        for file_path in deleted_id_docs:
            delete_cast_file(file_path)
            if file_path in existing_id_docs:
                existing_id_docs.remove(file_path)
        
        for file_path in deleted_contract_docs:
            delete_cast_file(file_path)
            if file_path in existing_contract_docs:
                existing_contract_docs.remove(file_path)
        
        # 新規アップロードファイルの処理（身分証）
        id_document_files = request.files.getlist('id_documents')
        for file in id_document_files:
            if file and file.filename:
                # ファイルサイズチェック
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        error="ファイルサイズは5MB以下にしてください。"
                    )
                
                # 最大2枚まで
                if len(existing_id_docs) >= 2:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        error="身分証画像は最大2枚までです。"
                    )
                
                saved_path = save_cast_file(file, cast_id, 'id_document')
                if saved_path:
                    existing_id_docs.append(saved_path)
        
        # 新規アップロードファイルの処理（契約書等）
        contract_document_files = request.files.getlist('contract_documents')
        for file in contract_document_files:
            if file and file.filename:
                # ファイルサイズチェック
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        error="ファイルサイズは5MB以下にしてください。"
                    )
                
                # 最大5枚まで
                if len(existing_contract_docs) >= 5:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        error="契約書等画像は最大5枚までです。"
                    )
                
                saved_path = save_cast_file(file, cast_id, 'contract_document')
                if saved_path:
                    existing_contract_docs.append(saved_path)
        
        # ファイルパスをcast_dataに追加
        cast_data['id_document_paths'] = existing_id_docs
        cast_data['contract_document_paths'] = existing_contract_docs

        # データベースを更新
        success = update_cast(db, cast_id, cast_data)
        
        if success:
            return redirect(url_for('main_routes.cast_management', store=store, success="キャスト情報を更新しました。"))
        else:
            return render_template(
                "cast_edit.html",
                store=store,
                cast=cast,
                display_name=display_name,
                error="更新に失敗しました。"
            )

    return render_template(
        "cast_edit.html",
        store=store,
        cast=cast,
        display_name=display_name
    )

def delete_cast(store, cast_id):
    """キャスト削除（論理削除）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    
    # 論理削除を実行
    success = db_delete_cast(db, cast_id)
    
    if success:
        return redirect(url_for('main_routes.cast_management', store=store, success="キャストを削除しました。"))
    else:
        return redirect(url_for('main_routes.cast_management', store=store, error="削除に失敗しました。"))