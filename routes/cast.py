import re
import os
import json
from datetime import datetime
from flask import Blueprint
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for
from database.connection import get_db, get_display_name, get_store_id
from datetime import datetime, date
from database.cast_db import (
    register_cast as db_register_cast,
    get_all_casts, find_cast_by_name, find_cast_by_phone_number, find_cast_by_id,
    get_all_casts_with_details, update_cast, delete_cast as db_delete_cast,
    get_cast_with_age,
    get_all_hotels, get_all_courses, get_all_options, get_all_areas,
    get_all_ng_areas, get_all_ng_age_patterns,
    get_cast_ng_hotels, get_cast_ng_courses, get_cast_ng_options, get_cast_ng_areas,
    get_cast_ng_custom_areas, get_cast_ng_age_patterns,
    update_cast_ng_items,
    update_cast_ng_custom_areas, update_cast_ng_age_patterns
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
    """キャスト新規登録ページ（フル機能版 + コースカテゴリ対応）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    store_id = get_store_id(store)
    
    db = get_db()
    
    # コースカテゴリ一覧を取得
    cursor = db.cursor()
    cursor.execute("""
        SELECT category_id, category_name
        FROM course_categories
        WHERE store_id = %s
        AND is_active = TRUE
        ORDER BY category_id
    """, (store_id,))
    course_categories = cursor.fetchall()

    if request.method == "POST":
        name = request.form.get("name")
        phone_number = request.form.get("phone_number")
        email = request.form.get("email")
        birth_date = request.form.get("birth_date") or None
        join_date = request.form.get("join_date") or None
        status = request.form.get("status", '在籍')
        recruitment_source = request.form.get("recruitment_source")
        transportation_fee = int(request.form.get("transportation_fee", 0))
        work_type = request.form.get("work_type", "")
        comments = request.form.get("comments")
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")
        notification_minutes_before = int(request.form.get("notification_minutes_before", 15))
        auto_call_enabled = request.form.get("auto_call_enabled", "true") == "true"
        
        # 住所の結合
        prefecture = request.form.get("prefecture", "")
        city = request.form.get("city", "")
        address_detail = request.form.get("address_detail", "")
        full_address = " ".join(filter(None, [prefecture, city, address_detail]))
        
        # 対応コースカテゴリの取得
        course_category_id = request.form.get("course_category_id")
        
        # バリデーションチェック（名前のみ必須）
        if not name:
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                course_categories=course_categories,
                error="キャスト名を入力してください。"
            )

        # 電話番号のバリデーション（入力がある場合のみチェック）
        if phone_number and not re.fullmatch(r'\d{11}', phone_number):
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                course_categories=course_categories,
                error="電話番号は半角数字11桁で入力してください。"
            )

        # 名前の重複チェック
        existing_cast_by_name = find_cast_by_name(db, name)
        if existing_cast_by_name:
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                course_categories=course_categories,
                error="既に登録されているキャスト名です。"
            )

        # 電話番号が入力されている場合のみ重複チェック
        if phone_number and phone_number.strip():
            existing_cast_by_phone = find_cast_by_phone_number(db, phone_number)
            if existing_cast_by_phone:
                return render_template(
                    "cast_registration.html",
                    store=store,
                    display_name=display_name,
                    course_categories=course_categories,
                    error="既に登録されている電話番号です。"
                )
        
        # ログインIDの重複チェック（入力されている場合）
        if login_id:
            from database.cast_db import find_cast_by_login_id
            existing_cast_by_login = find_cast_by_login_id(db, login_id)
            if existing_cast_by_login:
                return render_template(
                    "cast_registration.html",
                    store=store,
                    display_name=display_name,
                    course_categories=course_categories,
                    error=f"このログインID '{login_id}' は既に使用されています。"
                )

        # 基本登録（名前と電話番号のみ）
        cast_id = db_register_cast(db, name, phone_number)
        
        if not cast_id:
            return render_template(
                "cast_registration.html",
                store=store,
                display_name=display_name,
                course_categories=course_categories,
                error="登録に失敗しました。"
            )
        
        # 追加情報を更新
        cast_data = {
            'email': email,
            'birth_date': birth_date,
            'address': full_address,
            'join_date': join_date,
            'status': status,
            'recruitment_source': recruitment_source,
            'transportation_fee': transportation_fee,
            'work_type': work_type,
            'comments': comments,
            'login_id': login_id if login_id else None,
            'notification_minutes_before': notification_minutes_before,
            'auto_call_enabled': auto_call_enabled,
            'available_course_categories': [int(course_category_id)] if course_category_id else [],
            'id_document_paths': [],
            'contract_document_paths': []
        }
        
        # パスワードが入力されている場合のみ設定
        if password:
            cast_data['password'] = password
        
        # ファイルアップロード処理
        id_docs = []
        contract_docs = []
        
        # 身分証画像
        id_document_files = request.files.getlist('id_documents')
        for file in id_document_files:
            if file and file.filename:
                saved_path = save_cast_file(file, cast_id, 'id_document')
                if saved_path:
                    id_docs.append(saved_path)
        
        # 契約書等画像
        contract_document_files = request.files.getlist('contract_documents')
        for file in contract_document_files:
            if file and file.filename:
                saved_path = save_cast_file(file, cast_id, 'contract_document')
                if saved_path:
                    contract_docs.append(saved_path)
        
        cast_data['id_document_paths'] = id_docs
        cast_data['contract_document_paths'] = contract_docs
        
        # 詳細情報を更新
        update_cast(db, cast_id, cast_data)
        
        # ✅ 登録成功後は一覧画面にリダイレクト（これはOK）
        return redirect(url_for('main_routes.cast_management', store=store))
        
    # GETリクエストの場合、登録フォームを表示
    success_msg = request.args.get('success')
    error_msg = request.args.get('error')
    
    return render_template(
        "cast_registration.html",
        store=store,
        display_name=display_name,
        course_categories=course_categories,
        success=success_msg,
        error=error_msg
    )

def edit_cast(store, cast_id):
    """キャスト編集ページ（hotel_management統一版 - flash削除済み）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    store_id = get_store_id(store)

    db = get_db()
    # 年齢計算込みのキャスト情報を取得
    cast = get_cast_with_age(db, cast_id)

    if cast is None:
        return redirect(url_for('main_routes.cast_management', store=store))

    # 住所を都道府県・市区町村・詳細に分割
    address = cast.get('address', '')
    prefecture = ''
    city = ''
    address_detail = ''

    if address:
        # 都道府県リスト
        prefectures = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
                      '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
                      '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
                      '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
                      '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
                      '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
                      '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']

        for pref in prefectures:
            if address.startswith(pref):
                prefecture = pref
                rest = address[len(pref):].strip()

                # 市区町村と詳細住所を分割（最初の空白まで）
                parts = rest.split(' ', 1)
                if len(parts) > 0:
                    city = parts[0]
                if len(parts) > 1:
                    address_detail = parts[1]
                break

    # castにprefecture、city、address_detailを追加
    cast['prefecture'] = prefecture
    cast['city'] = city
    cast['address_detail'] = address_detail

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
        
        # オートコール設定の取得
        notification_minutes_before = request.form.get("notification_minutes_before", "15")
        auto_call_enabled = request.form.get("auto_call_enabled", "true")
        
        # Boolean変換
        auto_call_enabled_bool = (auto_call_enabled == "true")
        
        # 働き方区分の取得
        work_type = request.form.get("work_type", "")
        
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
            'work_type': work_type,
            'comments': request.form.get("comments"),
            'login_id': new_login_id,
            'notification_minutes_before': int(notification_minutes_before),
            'auto_call_enabled': auto_call_enabled_bool,
        }
        
        # 対応コースカテゴリの処理（category_idで保存）
        course_category_id = request.form.get("course_category_id")
        if course_category_id:
            cast_data['available_course_categories'] = [int(course_category_id)]
        else:
            cast_data['available_course_categories'] = []
        
        # パスワードが入力されている場合のみ更新
        password = request.form.get("password")
        if password:
            cast_data['password'] = password
        
        # コースカテゴリ一覧を取得（エラー時の再表示用）
        cursor = db.cursor()
        cursor.execute("""
            SELECT category_id, category_name
            FROM course_categories
            WHERE store_id = %s
            AND is_active = TRUE
            ORDER BY category_id
        """, (store_id,))
        course_categories = cursor.fetchall()
        
        # バリデーション
        if not cast_data['name']:
            return render_template(
                "cast_edit.html",
                store=store,
                cast=cast,
                display_name=display_name,
                course_categories=course_categories,
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
                course_categories=course_categories,
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
                    course_categories=course_categories,
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
                    course_categories=course_categories,
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
                        course_categories=course_categories,
                        error="ファイルサイズは5MB以下にしてください。"
                    )
                
                # 最大2枚まで
                if len(existing_id_docs) >= 2:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        course_categories=course_categories,
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
                        course_categories=course_categories,
                        error="ファイルサイズは5MB以下にしてください。"
                    )
                
                # 最大5枚まで
                if len(existing_contract_docs) >= 5:
                    return render_template(
                        "cast_edit.html",
                        store=store,
                        cast=cast,
                        display_name=display_name,
                        course_categories=course_categories,
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
        
        print(f"✅ キャスト更新{'成功' if success else '失敗'}: cast_id {cast_id}")
        
        # NG設定の更新処理
        try:
            # NGホテルの保存
            ng_hotels = request.form.getlist('ng_hotels')
            ng_hotels = [int(h) for h in ng_hotels if h]
            
            # NGコースの保存
            ng_courses = request.form.getlist('ng_courses')
            ng_courses = [int(c) for c in ng_courses if c]
            
            # NGオプションの保存
            ng_options = request.form.getlist('ng_options')
            ng_options = [int(o) for o in ng_options if o]
            
            # NGエリア（カスタム）の保存
            ng_custom_areas = request.form.getlist('ng_custom_areas')
            ng_custom_areas = [int(a) for a in ng_custom_areas if a]
            
            # 年齢NGの保存
            ng_age_patterns = request.form.getlist('ng_age_patterns')
            ng_age_patterns = [int(p) for p in ng_age_patterns if p]
            
            # データベース更新
            update_cast_ng_items(db, cast_id, 'hotels', ng_hotels)
            update_cast_ng_items(db, cast_id, 'courses', ng_courses)
            update_cast_ng_items(db, cast_id, 'options', ng_options)
            update_cast_ng_custom_areas(db, cast_id, ng_custom_areas)
            update_cast_ng_age_patterns(db, cast_id, ng_age_patterns)
            
        except Exception as e:
            print(f"❌ NG設定更新エラー: {e}")
            success = False
        
        # ✅ 更新後、最新のキャスト情報を取得して再表示（flash削除、redirect削除）
        cast = get_cast_with_age(db, cast_id)

        # 住所を都道府県・市区町村・詳細に分割
        address = cast.get('address', '')
        prefecture = ''
        city = ''
        address_detail = ''

        if address:
            # 都道府県リスト
            prefectures_list = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
                          '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
                          '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
                          '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
                          '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
                          '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
                          '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']

            for pref in prefectures_list:
                if address.startswith(pref):
                    prefecture = pref
                    rest = address[len(pref):].strip()

                    # 市区町村と詳細住所を分割（最初の空白まで）
                    parts = rest.split(' ', 1)
                    if len(parts) > 0:
                        city = parts[0]
                    if len(parts) > 1:
                        address_detail = parts[1]
                    break

        # castにprefecture、city、address_detailを追加
        cast['prefecture'] = prefecture
        cast['city'] = city
        cast['address_detail'] = address_detail

        # コースカテゴリ一覧を取得
        cursor = db.cursor()
        cursor.execute("""
            SELECT category_id, category_name
            FROM course_categories
            WHERE store_id = %s
            AND is_active = TRUE
            ORDER BY category_id
        """, (store_id,))
        course_categories = cursor.fetchall()
        
        # NG設定タブ用のデータを取得
        all_hotels = get_all_hotels(db, store_id)
        all_courses = get_all_courses(db, store_id)
        all_options = get_all_options(db, store_id)
        all_ng_areas = get_all_ng_areas(db)
        all_ng_age_patterns = get_all_ng_age_patterns(db)
        
        # キャストのNG設定を取得
        ng_hotels = get_cast_ng_hotels(db, cast_id)
        ng_courses = get_cast_ng_courses(db, cast_id)
        ng_options = get_cast_ng_options(db, cast_id)
        ng_custom_areas = get_cast_ng_custom_areas(db, cast_id)
        ng_age_patterns = get_cast_ng_age_patterns(db, cast_id)
        
        # NGのIDリストを作成
        ng_hotel_ids = [h['hotel_id'] for h in ng_hotels]
        ng_course_ids = [c['course_id'] for c in ng_courses]
        ng_option_ids = [o['option_id'] for o in ng_options]
        ng_custom_area_ids = [a['ng_area_id'] for a in ng_custom_areas]
        ng_age_pattern_ids = [p['ng_age_id'] for p in ng_age_patterns]
        
        # ✅ flash()とredirect()を使わず、successまたはerrorメッセージを渡して再レンダリング
        return render_template(
            "cast_edit.html",
            store=store,
            cast=cast,
            display_name=display_name,
            today=date.today(),
            course_categories=course_categories,
            all_hotels=all_hotels,
            all_courses=all_courses,
            all_options=all_options,
            all_ng_areas=all_ng_areas,
            all_ng_age_patterns=all_ng_age_patterns,
            ng_hotel_ids=ng_hotel_ids,
            ng_course_ids=ng_course_ids,
            ng_option_ids=ng_option_ids,
            ng_custom_area_ids=ng_custom_area_ids,
            ng_age_pattern_ids=ng_age_pattern_ids,
            success="更新できました。" if success else None,
            error="更新に失敗しました。" if not success else None
        )

    # GETリクエスト：編集画面を表示
    
    # コースカテゴリ一覧を取得
    cursor = db.cursor()
    cursor.execute("""
        SELECT category_id, category_name
        FROM course_categories
        WHERE store_id = %s
        AND is_active = TRUE
        ORDER BY category_id
    """, (store_id,))
    course_categories = cursor.fetchall()
    
    # NG設定タブ用のデータを取得
    all_hotels = get_all_hotels(db, store_id)
    all_courses = get_all_courses(db, store_id)
    all_options = get_all_options(db, store_id)
    all_ng_areas = get_all_ng_areas(db)
    all_ng_age_patterns = get_all_ng_age_patterns(db)
    
    # キャストのNG設定を取得
    ng_hotels = get_cast_ng_hotels(db, cast_id)
    ng_courses = get_cast_ng_courses(db, cast_id)
    ng_options = get_cast_ng_options(db, cast_id)
    ng_custom_areas = get_cast_ng_custom_areas(db, cast_id)
    ng_age_patterns = get_cast_ng_age_patterns(db, cast_id)
    
    # NGのIDリストを作成
    ng_hotel_ids = [h['hotel_id'] for h in ng_hotels]
    ng_course_ids = [c['course_id'] for c in ng_courses]
    ng_option_ids = [o['option_id'] for o in ng_options]
    ng_custom_area_ids = [a['ng_area_id'] for a in ng_custom_areas]
    ng_age_pattern_ids = [p['ng_age_id'] for p in ng_age_patterns]

    return render_template(
        "cast_edit.html",
        store=store,
        cast=cast,
        display_name=display_name,
        today=date.today(),
        course_categories=course_categories,
        all_hotels=all_hotels,
        all_courses=all_courses,
        all_options=all_options,
        all_ng_areas=all_ng_areas,
        all_ng_age_patterns=all_ng_age_patterns,
        ng_hotel_ids=ng_hotel_ids,
        ng_course_ids=ng_course_ids,
        ng_option_ids=ng_option_ids,
        ng_custom_area_ids=ng_custom_area_ids,
        ng_age_pattern_ids=ng_age_pattern_ids
    )


def save_cast_ng_settings(store, cast_id):
    """キャストNG設定の保存処理（NGエリア・年齢NG対応）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    db = get_db()
    cast = get_cast_with_age(db, cast_id)
    
    if cast is None:
        return redirect(url_for('main_routes.cast_management', store=store))

    if request.method == "POST":
        try:
            # NGホテルの保存
            ng_hotels = request.form.getlist('ng_hotels')
            ng_hotels = [int(h) for h in ng_hotels if h]
            
            # NGコースの保存
            ng_courses = request.form.getlist('ng_courses')
            ng_courses = [int(c) for c in ng_courses if c]
            
            # NGオプションの保存
            ng_options = request.form.getlist('ng_options')
            ng_options = [int(o) for o in ng_options if o]
            
            # NGエリア（カスタム）の保存
            ng_custom_areas = request.form.getlist('ng_custom_areas')
            ng_custom_areas = [int(a) for a in ng_custom_areas if a]
            
            # 年齢NGの保存
            ng_age_patterns = request.form.getlist('ng_age_patterns')
            ng_age_patterns = [int(p) for p in ng_age_patterns if p]
            
            # データベース更新
            update_cast_ng_items(db, cast_id, 'hotels', ng_hotels)
            update_cast_ng_items(db, cast_id, 'courses', ng_courses)
            update_cast_ng_items(db, cast_id, 'options', ng_options)
            update_cast_ng_custom_areas(db, cast_id, ng_custom_areas)
            update_cast_ng_age_patterns(db, cast_id, ng_age_patterns)
            
            # ✅ 保存後は編集画面にリダイレクト（これはOK - 別ページへの遷移）
            return redirect(url_for('main_routes.edit_cast', store=store, cast_id=cast_id))
            
        except Exception as e:
            print(f"NG設定保存エラー: {e}")
            import traceback
            traceback.print_exc()
            return redirect(url_for('main_routes.edit_cast', store=store, cast_id=cast_id))
    
    return redirect(url_for('main_routes.edit_cast', store=store, cast_id=cast_id))


def delete_cast(store, cast_id):
    """キャスト削除（論理削除）"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db()
    
    # 論理削除を実行
    success = db_delete_cast(db, cast_id)
    
    # ✅ 削除後は一覧画面にリダイレクト（これはOK - 別ページへの遷移）
    return redirect(url_for('main_routes.cast_management', store=store))