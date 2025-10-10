# -*- coding: utf-8 -*-
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

from database.connection import get_db
import psycopg
from psycopg.rows import dict_row
import json
from datetime import datetime
import hashlib
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

def get_db_connection(store_code):
    """データベース接続を取得"""
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname='pickup_system',  # 固定
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'diary8475ftkb')
    )
    return conn

# ==== 基本キャスト関数 ====
def get_all_casts(db):
    """データベースから全てのキャスト情報を取得します。"""
    cursor = db.cursor()
    cursor.execute("SELECT cast_id, name, phone_number FROM casts WHERE status = '在籍' ORDER BY name")
    casts = cursor.fetchall()
    return casts

def register_cast(db, name, phone_number):
    """新しいキャストをデータベースに登録する関数"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COALESCE(MAX(cast_id), 0) + 1 as next_id FROM casts")
        result = cursor.fetchone()
        new_cast_id = result['next_id']
        
        cursor.execute(
            "INSERT INTO casts (cast_id, name, phone_number) VALUES (%s, %s, %s)",
            (new_cast_id, name, phone_number)
        )
        db.commit()
        return True
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"キャスト登録エラー: {e}")
        return False

def find_cast_by_id(db, cast_id):
    """IDでキャストを検索する関数。"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM casts WHERE cast_id = %s", (cast_id,))
    cast = cursor.fetchone()
    return cast if cast else None

def find_cast_by_name(db, name):
    """名前でキャストを検索する関数。"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM casts WHERE name = %s AND is_active = TRUE", (name,))
    cast = cursor.fetchone()
    return cast if cast else None

def find_cast_by_phone_number(db, phone_number):
    """電話番号でキャストを検索する関数。"""
    # 電話番号がNULLまたは空文字の場合は検索しない
    if not phone_number or not phone_number.strip():
        return None
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM casts WHERE phone_number = %s", (phone_number,))
    cast = cursor.fetchone()
    return cast if cast else None

# ==== 拡張キャスト管理関数 ====
def get_all_casts_with_details(db):
    """年齢計算込みのキャスト詳細情報を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            cast_id,
            name,
            phone_number,
            email,
            birth_date,
            CASE 
                WHEN birth_date IS NOT NULL 
                THEN EXTRACT(YEAR FROM age(birth_date))::INTEGER 
                ELSE NULL 
            END AS age,
            address,
            join_date,
            status,
            recruitment_source,
            transportation_fee,
            available_course_categories,
            work_type,
            comments,
            login_id,
            password_plain,
            last_login,
            profile_image_path,
            is_active,
            created_at,
            updated_at,
            notification_minutes_before,
            auto_call_enabled
        FROM casts 
        WHERE is_active = TRUE
        ORDER BY name
    """)
    return cursor.fetchall()

def register_cast_extended(db, cast_data):
    """拡張フィールド対応のキャスト登録"""
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT COALESCE(MAX(cast_id), 0) + 1 as next_id FROM casts")
        result = cursor.fetchone()
        new_cast_id = result['next_id']
        
        # 平文パスワードとハッシュの両方を保存
        password_plain = cast_data.get('password', '')
        password_hash = None
        if password_plain:
            password_hash = hashlib.sha256(password_plain.encode()).hexdigest()
        
        course_categories_json = json.dumps(cast_data.get('available_course_categories', []), ensure_ascii=False)
        id_documents_json = json.dumps(cast_data.get('id_document_paths', []), ensure_ascii=False)
        contract_documents_json = json.dumps(cast_data.get('contract_document_paths', []), ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO casts (
                cast_id, name, phone_number, email, birth_date, address,
                join_date, status, recruitment_source, transportation_fee,
                available_course_categories, work_type, comments, login_id, 
                password_hash, password_plain,
                profile_image_path, id_document_paths, contract_document_paths,
                store_id, is_active, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, (
            new_cast_id,
            cast_data['name'],
            cast_data.get('phone_number'),
            cast_data.get('email'),
            cast_data.get('birth_date'),
            cast_data.get('address'),
            cast_data.get('join_date'),
            cast_data.get('status', '在籍'),
            cast_data.get('recruitment_source'),
            cast_data.get('transportation_fee', 0),
            course_categories_json,
            cast_data.get('work_type'),
            cast_data.get('comments'),
            cast_data.get('login_id'),
            password_hash,
            password_plain,
            cast_data.get('profile_image_path'),
            id_documents_json,
            contract_documents_json,
            cast_data.get('store_id', 1),
            True
        ))
        
        db.commit()
        print(f"拡張キャスト登録成功: {cast_data['name']} (ID: {new_cast_id})")
        return new_cast_id
        
    except psycopg.IntegrityError as e:
        print(f"整合性エラー: {e}")
        raise
    except Exception as e:
        print(f"拡張キャスト登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_cast(db, cast_id, cast_data):
    """キャスト情報を更新（平文パスワード対応）"""
    try:
        cursor = db.cursor()
        
        # 平文パスワードとハッシュの両方を処理
        password_plain = None
        password_hash = None
        if cast_data.get('password'):
            password_plain = cast_data['password']
            password_hash = hashlib.sha256(password_plain.encode()).hexdigest()
        
        course_categories_json = None
        if 'available_course_categories' in cast_data:
            course_categories_json = json.dumps(cast_data['available_course_categories'], ensure_ascii=False)
        
        id_documents_json = None
        if 'id_document_paths' in cast_data:
            id_documents_json = json.dumps(cast_data['id_document_paths'], ensure_ascii=False)
        
        contract_documents_json = None
        if 'contract_document_paths' in cast_data:
            contract_documents_json = json.dumps(cast_data['contract_document_paths'], ensure_ascii=False)
        
        update_fields = []
        params = []
        
        # 基本フィールド + オートコール設定フィールド + work_type
        for field in ['name', 'phone_number', 'email', 'birth_date', 'address', 
                     'join_date', 'status', 'recruitment_source', 'transportation_fee', 
                     'work_type', 'comments', 'login_id', 'profile_image_path', 
                     'notification_minutes_before', 'auto_call_enabled']:
            if field in cast_data:
                update_fields.append(f"{field} = %s")
                params.append(cast_data[field])
        
        if course_categories_json is not None:
            update_fields.append("available_course_categories = %s")
            params.append(course_categories_json)
        
        if id_documents_json is not None:
            update_fields.append("id_document_paths = %s")
            params.append(id_documents_json)
        
        if contract_documents_json is not None:
            update_fields.append("contract_document_paths = %s")
            params.append(contract_documents_json)
        
        # パスワードの更新（平文とハッシュ両方）
        if password_plain:
            update_fields.append("password_plain = %s")
            params.append(password_plain)
            update_fields.append("password_hash = %s")
            params.append(password_hash)
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(cast_id)
        
        if update_fields:
            query = f"UPDATE casts SET {', '.join(update_fields)} WHERE cast_id = %s"
            cursor.execute(query, params)
            db.commit()
            print(f"キャスト更新成功: cast_id {cast_id}")
            return True
        
        return False
        
    except Exception as e:
        print(f"キャスト更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_cast_by_login_id(db, login_id):
    """ログインIDでキャストを検索（マイページ認証用）"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            cast_id, name, login_id, password_hash, password_plain, status, last_login,
            is_active
        FROM casts 
        WHERE login_id = %s AND is_active = TRUE
    """, (login_id,))
    return cursor.fetchone()

def update_last_login(db, cast_id):
    """最終ログイン時刻を更新"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE casts 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE cast_id = %s
        """, (cast_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"最終ログイン更新エラー: {e}")
        return False

def verify_cast_password(db, login_id, password):
    """
    キャストの認証（平文パスワード対応）
    
    Args:
        db: データベース接続
        login_id: ログインID
        password: パスワード（平文）
    
    Returns:
        int: 認証成功時はcast_id、失敗時はNone
    """
    try:
        cast = find_cast_by_login_id(db, login_id)
        
        if not cast:
            print(f"❌ 認証失敗: キャストが見つかりません (login_id: {login_id})")
            return None
        
        # find_cast_by_login_idのSELECT順序:
        # cast_id, name, login_id, password_hash, password_plain, status, last_login, is_active
        # インデックス: 0, 1, 2, 3, 4, 5, 6, 7
        
        cast_id = cast[0]
        password_hash = cast[3]
        password_plain = cast[4]  # ★ここが重要！平文パスワード
        is_active = cast[7]
        
        # アクティブチェック
        if not is_active:
            print(f"❌ 認証失敗: キャストが無効です (cast_id: {cast_id})")
            return None
        
        # まず平文パスワードで認証
        if password_plain:
            if password_plain.strip() == password.strip():
                print(f"✅ 認証成功: cast_id {cast_id} (login_id: {login_id})")
                update_last_login(db, cast_id)
                return cast_id
            else:
                print(f"❌ 認証失敗: 平文パスワードが一致しません (login_id: {login_id})")
                return None
        
        # 平文がない場合はハッシュで認証
        if password_hash:
            hashed_input = hashlib.sha256(password.encode()).hexdigest()
            if hashed_input == password_hash:
                print(f"✅ 認証成功（ハッシュ）: cast_id {cast_id} (login_id: {login_id})")
                update_last_login(db, cast_id)
                return cast_id
            else:
                print(f"❌ 認証失敗: ハッシュパスワードが一致しません (login_id: {login_id})")
                return None
        
        print(f"❌ 認証失敗: パスワードが設定されていません (login_id: {login_id})")
        return None
            
    except Exception as e:
        print(f"❌ 認証エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_cast_with_age(db, cast_id):
    """年齢計算込みの特定キャスト詳細情報（平文パスワード含む）"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            cast_id,
            name,
            phone_number,
            email,
            birth_date,
            CASE 
                WHEN birth_date IS NOT NULL 
                THEN EXTRACT(YEAR FROM age(birth_date))::INTEGER 
                ELSE NULL 
            END AS age,
            address,
            join_date,
            status,
            recruitment_source,
            transportation_fee,
            available_course_categories,
            work_type,
            comments,
            login_id,
            password_plain,
            last_login,
            profile_image_path,
            id_document_paths,
            contract_document_paths,
            is_active,
            created_at,
            updated_at,
            notification_minutes_before,
            auto_call_enabled
        FROM casts 
        WHERE cast_id = %s
    """, (cast_id,))
    return cursor.fetchone()

def delete_cast(db, cast_id):
    """キャストを論理削除"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE casts 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE cast_id = %s
        """, (cast_id,))
        db.commit()
        print(f"キャスト削除成功: cast_id {cast_id}")
        return True
    except Exception as e:
        print(f"キャスト削除エラー: {e}")
        return False

# ==== マスターデータ取得関数 ====
def get_all_hotels(db):
    """全ホテル一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT hotel_id, name 
        FROM hotels 
        ORDER BY name
    """)
    return cursor.fetchall()

def get_all_courses(db):
    """全コース一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT course_id, name 
        FROM courses 
        ORDER BY name
    """)
    return cursor.fetchall()

def get_all_options(db):
    """全オプション一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT option_id, name 
        FROM options 
        ORDER BY name
    """)
    return cursor.fetchall()

def get_all_areas(db):
    """全エリア一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT area_id, name 
        FROM areas 
        ORDER BY name
    """)
    return cursor.fetchall()

def get_all_ng_areas(db):
    """全NGエリア一覧を取得（settingsで登録したもの）"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT ng_area_id, area_name 
        FROM ng_areas 
        WHERE is_active = TRUE
        ORDER BY display_order, area_name
    """)
    return cursor.fetchall()

def get_all_ng_age_patterns(db):
    """全年齢NGパターン一覧を取得（settingsで登録したもの）"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT ng_age_id, pattern_name, description 
        FROM ng_age_patterns 
        WHERE is_active = TRUE
        ORDER BY display_order, pattern_name
    """)
    return cursor.fetchall()

# ==== NG項目管理関数 ====
def get_cast_ng_hotels(db, cast_id):
    """キャストのNGホテル一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT h.hotel_id, h.name as hotel_name 
        FROM cast_ng_hotels ng
        JOIN hotels h ON ng.hotel_id = h.hotel_id
        WHERE ng.cast_id = %s
        ORDER BY h.name
    """, (cast_id,))
    return cursor.fetchall()

def get_cast_ng_courses(db, cast_id):
    """キャストのNGコース一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.course_id, c.name as course_name 
        FROM cast_ng_courses ng
        JOIN courses c ON ng.course_id = c.course_id
        WHERE ng.cast_id = %s
        ORDER BY c.name
    """, (cast_id,))
    return cursor.fetchall()

def get_cast_ng_options(db, cast_id):
    """キャストのNGオプション一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT o.option_id, o.name as option_name 
        FROM cast_ng_options ng
        JOIN options o ON ng.option_id = o.option_id
        WHERE ng.cast_id = %s
        ORDER BY o.name
    """, (cast_id,))
    return cursor.fetchall()

def get_cast_ng_areas(db, cast_id):
    """キャストのNGエリア一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT a.area_id, a.name as area_name 
        FROM cast_ng_areas ng
        JOIN areas a ON ng.area_id = a.area_id
        WHERE ng.cast_id = %s
        ORDER BY a.name
    """, (cast_id,))
    return cursor.fetchall()

def get_cast_ng_custom_areas(db, cast_id):
    """キャストのNGエリア（カスタム）一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT na.ng_area_id, na.area_name 
        FROM cast_ng_custom_areas cna
        JOIN ng_areas na ON cna.ng_area_id = na.ng_area_id
        WHERE cna.cast_id = %s AND na.is_active = TRUE
        ORDER BY na.area_name
    """, (cast_id,))
    return cursor.fetchall()

def get_cast_ng_age_patterns(db, cast_id):
    """キャストの年齢NGパターン一覧を取得"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT nap.ng_age_id, nap.pattern_name, nap.description 
        FROM cast_ng_age_patterns cnap
        JOIN ng_age_patterns nap ON cnap.ng_age_id = nap.ng_age_id
        WHERE cnap.cast_id = %s AND nap.is_active = TRUE
        ORDER BY nap.pattern_name
    """, (cast_id,))
    return cursor.fetchall()

def update_cast_ng_items(db, cast_id, ng_type, item_ids):
    """キャストのNG項目を一括更新"""
    try:
        cursor = db.cursor()
        
        table_map = {
            'hotels': ('cast_ng_hotels', 'hotel_id'),
            'courses': ('cast_ng_courses', 'course_id'),
            'options': ('cast_ng_options', 'option_id'),
            'areas': ('cast_ng_areas', 'area_id')
        }
        
        if ng_type not in table_map:
            raise ValueError(f"Invalid ng_type: {ng_type}")
        
        table_name, id_column = table_map[ng_type]
        
        cursor.execute(f"DELETE FROM {table_name} WHERE cast_id = %s", (cast_id,))
        
        if item_ids:
            values = [(cast_id, item_id) for item_id in item_ids]
            placeholders = ','.join(['(%s, %s)'] * len(values))
            flat_values = [val for pair in values for val in pair]
            
            cursor.execute(f"""
                INSERT INTO {table_name} (cast_id, {id_column}) 
                VALUES {placeholders}
            """, flat_values)
        
        db.commit()
        print(f"キャストNG{ng_type}更新成功: cast_id {cast_id}")
        return True
        
    except Exception as e:
        print(f"キャストNG項目更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_cast_ng_custom_areas(db, cast_id, ng_area_ids):
    """キャストのNGエリア（カスタム）を一括更新"""
    try:
        cursor = db.cursor()
        
        # 既存のNG設定を削除
        cursor.execute("DELETE FROM cast_ng_custom_areas WHERE cast_id = %s", (cast_id,))
        
        # 新しいNG設定を登録
        if ng_area_ids:
            values = [(cast_id, area_id) for area_id in ng_area_ids]
            placeholders = ','.join(['(%s, %s)'] * len(values))
            flat_values = [val for pair in values for val in pair]
            
            cursor.execute(f"""
                INSERT INTO cast_ng_custom_areas (cast_id, ng_area_id) 
                VALUES {placeholders}
            """, flat_values)
        
        db.commit()
        print(f"キャストNGエリア更新成功: cast_id {cast_id}")
        return True
        
    except Exception as e:
        print(f"キャストNGエリア更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_cast_ng_age_patterns(db, cast_id, ng_age_ids):
    """キャストの年齢NGパターンを一括更新"""
    try:
        cursor = db.cursor()
        
        # 既存のNG設定を削除
        cursor.execute("DELETE FROM cast_ng_age_patterns WHERE cast_id = %s", (cast_id,))
        
        # 新しいNG設定を登録
        if ng_age_ids:
            values = [(cast_id, age_id) for age_id in ng_age_ids]
            placeholders = ','.join(['(%s, %s)'] * len(values))
            flat_values = [val for pair in values for val in pair]
            
            cursor.execute(f"""
                INSERT INTO cast_ng_age_patterns (cast_id, ng_age_id) 
                VALUES {placeholders}
            """, flat_values)
        
        db.commit()
        print(f"キャスト年齢NG更新成功: cast_id {cast_id}")
        return True
        
    except Exception as e:
        print(f"キャスト年齢NG更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==== ユーティリティ関数 ====
def parse_json_field(field_value):
    """JSON文字列をPythonオブジェクトに変換"""
    if field_value is None:
        return []
    try:
        return json.loads(field_value)
    except (json.JSONDecodeError, TypeError):
        return []

def get_recruitment_sources():
    """募集媒体の選択肢を取得"""
    return [
        '求人サイト',
        '紹介',
        'SNS',
        '直接応募',
        'その他'
    ]

def get_status_options():
    """ステータスの選択肢を取得"""
    return [
        '在籍',
        '休職',
        '退職'
    ]