# -*- coding: utf-8 -*-
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

from database.connection import get_db
import psycopg
from psycopg.rows import dict_row
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

# ==== ユーザー関連の関数 ====
def find_user_by_login_id(db, login_id, store_id=None):
    """ログインIDでユーザーを検索する"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT * FROM users WHERE login_id = %s AND store_id = %s", (login_id, store_id))
    else:
        cursor.execute("SELECT * FROM users WHERE login_id = %s", (login_id,))
    user = cursor.fetchone()
    return user if user else None

def find_user_by_name(db, name, store_id=None):
    """名前でユーザーを検索する"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT * FROM users WHERE name = %s AND store_id = %s", (name, store_id))
    else:
        cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
    user = cursor.fetchone()
    return user if user else None

def get_all_users(db, store_id=None):
    """データベースから全てのユーザー情報を取得します。"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT name, login_id, role, color FROM users WHERE is_active = true AND store_id = %s ORDER BY name", (store_id,))
    else:
        cursor.execute("SELECT name, login_id, role, color FROM users WHERE is_active = true ORDER BY name")
    users = cursor.fetchall()
    return users

def register_user(db, name, login_id, password, role, color, store_id):
    """新しいユーザーをデータベースに登録する"""
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, login_id, password, role, color, store_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, login_id, password, role, color, store_id)
        )
        db.commit()
        return True
    except psycopg.IntegrityError:
        raise
    except Exception as e:
        print(f"ユーザー登録エラー: {e}")
        return False

def get_staff_list(db, store_id=None):
    """スタッフ一覧を取得（ダッシュボード用）"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT login_id, name, color FROM users WHERE is_active = true AND store_id = %s ORDER BY name", (store_id,))
    else:
        cursor.execute("SELECT login_id, name, color FROM users WHERE is_active = true ORDER BY name")
    staff = cursor.fetchall()
    return staff

def update_user(db, user_id, name, login_id, role, color, is_active=True):
    """ユーザー情報を更新"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE users 
            SET name = %s, login_id = %s, role = %s, color = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (name, login_id, role, color, is_active, user_id))
        db.commit()
        print(f"ユーザー更新成功: user_id {user_id}")
        return True
    except Exception as e:
        print(f"ユーザー更新エラー: {e}")
        return False

def delete_user(db, user_id):
    """ユーザーを論理削除"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE users 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        """, (user_id,))
        db.commit()
        print(f"ユーザー削除成功: user_id {user_id}")
        return True
    except Exception as e:
        print(f"ユーザー削除エラー: {e}")
        return False

def find_user_by_id(db, user_id, store_id=None):
    """IDでユーザーを検索"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("SELECT * FROM users WHERE user_id = %s AND store_id = %s", (user_id, store_id))
    else:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    return user if user else None

def verify_user_password(db, login_id, password):
    """ユーザーのパスワード認証（平文比較）"""
    user = find_user_by_login_id(db, login_id)
    if not user:
        return False
    
    if user['password'] == password:
        return user
    
    return False

def get_active_users(db, store_id=None):
    """アクティブなユーザー一覧を取得"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("""
            SELECT user_id, name, login_id, role, color, created_at, updated_at
            FROM users
            WHERE is_active = true AND store_id = %s
            ORDER BY name
        """, (store_id,))
    else:
        cursor.execute("""
            SELECT user_id, name, login_id, role, color, created_at, updated_at
            FROM users
            WHERE is_active = true
            ORDER BY name
        """)
    return cursor.fetchall()

def get_users_by_role(db, role, store_id=None):
    """役割別ユーザー一覧を取得"""
    cursor = db.cursor()
    if store_id:
        cursor.execute("""
            SELECT user_id, name, login_id, role, color
            FROM users
            WHERE role = %s AND is_active = true AND store_id = %s
            ORDER BY name
        """, (role, store_id))
    else:
        cursor.execute("""
            SELECT user_id, name, login_id, role, color
            FROM users
            WHERE role = %s AND is_active = true
            ORDER BY name
        """, (role,))
    return cursor.fetchall()

def update_user_password(db, user_id, new_password):
    """ユーザーパスワードを更新"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE users 
            SET password = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        """, (new_password, user_id))
        db.commit()
        print(f"パスワード更新成功: user_id {user_id}")
        return True
    except Exception as e:
        print(f"パスワード更新エラー: {e}")
        return False

def get_user_roles():
    """ユーザー役割の選択肢を取得"""
    return [
        'admin',
        'manager', 
        'staff',
        'viewer'
    ]