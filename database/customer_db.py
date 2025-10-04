# -*- coding: utf-8 -*-
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

import psycopg
from psycopg.rows import dict_row
from datetime import datetime, date
from werkzeug.security import generate_password_hash
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

def create_customers_table(store_code):
    """顧客テーブル作成"""
    conn = get_db_connection(store_code)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            furigana VARCHAR(100),
            phone VARCHAR(20),
            birthday DATE,
            age INTEGER,
            postal_code VARCHAR(10),
            address TEXT,
            recruitment_source VARCHAR(50),
            mypage_id VARCHAR(50) UNIQUE,
            mypage_password_hash VARCHAR(255),
            current_points INTEGER DEFAULT 0,
            member_type VARCHAR(20) DEFAULT '通常会員',
            status VARCHAR(20) DEFAULT '普通',
            web_member VARCHAR(20) DEFAULT 'web会員',
            comment TEXT,
            nickname VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # インデックス作成
    cur.execute('CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_customers_mypage_id ON customers(mypage_id)')
    
    conn.commit()
    cur.close()
    conn.close()

def calculate_age(birthday):
    """年齢計算"""
    if not birthday:
        return None
    today = date.today()
    age = today.year - birthday.year
    if today.month < birthday.month or (today.month == birthday.month and today.day < birthday.day):
        age -= 1
    return age

def add_customer(store_code, customer_data):
    """顧客を追加する関数"""
    try:
        conn = get_db_connection(store_code)
        cur = conn.cursor()
        
        # 空文字列をNoneに変換（DATE型フィールド）
        birthday = customer_data.get('birth_date')
        if birthday == '':
            birthday = None
        
        # 住所は個別カラムで保存
        prefecture = customer_data.get('prefecture')
        city = customer_data.get('city')
        address_detail = customer_data.get('address_detail')
        
        # 年齢計算（birthdayがある場合）
        age = None
        if birthday:
            from datetime import date
            today = date.today()
            birth = date.fromisoformat(birthday) if isinstance(birthday, str) else birthday
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        
        cur.execute('''
            INSERT INTO customers (
                name, furigana, phone, 
                birthday, age, prefecture, city, address_detail,
                mypage_id, mypage_password_hash, status,
                web_member, comment, nickname, current_points, member_type,
                recruitment_source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        ''', (
            customer_data.get('name'),
            customer_data.get('furigana'),
            customer_data.get('phone_number') or customer_data.get('phone'),
            birthday,
            age,
            prefecture,
            city,
            address_detail,
            customer_data.get('login_id') or customer_data.get('mypage_id'),
            customer_data.get('password') or customer_data.get('mypage_password'),
            customer_data.get('status', '普通'),
            customer_data.get('web_member', 'web会員'),
            customer_data.get('comment'),
            customer_data.get('nickname'),
            customer_data.get('current_points', 0),
            customer_data.get('member_type', '通常会員'),
            customer_data.get('recruitment_source')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"顧客追加成功: {customer_data.get('name')}")
        return True
        
    except Exception as e:
        print(f"Error in add_customer: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_all_customers(store_code):
    """全顧客を取得"""
    try:
        conn = get_db_connection(store_code)
        cur = conn.cursor(row_factory=dict_row)
        
        cur.execute('''
            SELECT 
                customer_id, name, furigana, phone,
                birthday, age, prefecture, city, address_detail, recruitment_source,
                mypage_id, current_points, member_type, status,
                web_member, comment, nickname,
                created_at, updated_at
            FROM customers
            ORDER BY created_at DESC
        ''')
        
        customers = cur.fetchall()
        cur.close()
        conn.close()
        
        return customers
        
    except Exception as e:
        print(f"Error in get_all_customers: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_customer_by_id(store_code, customer_id):
    """顧客情報取得（ID指定）"""
    conn = get_db_connection(store_code)
    cur = conn.cursor(row_factory=dict_row)
    
    cur.execute('''
        SELECT 
            customer_id, name, furigana, phone,
            birthday, age, postal_code, prefecture, city, address_detail,
            recruitment_source, mypage_id,
            current_points, member_type, status,
            web_member, comment, nickname,
            created_at, updated_at
        FROM customers
        WHERE customer_id = %s
    ''', (customer_id,))
    
    customer = cur.fetchone()
    cur.close()
    conn.close()
    
    return customer

def update_customer(store_code, customer_id, customer_data):
    """顧客情報更新"""
    conn = get_db_connection(store_code)
    cur = conn.cursor()
    
    # 年齢自動計算
    age = None
    if customer_data.get('birthday'):
        age = calculate_age(customer_data['birthday'])
    
    # マイページパスワード更新（入力があった場合のみ）
    if customer_data.get('mypage_password'):
        mypage_password_hash = generate_password_hash(customer_data['mypage_password'])
        cur.execute('''
            UPDATE customers SET
                name = %s, furigana = %s, phone = %s,
                birthday = %s, age = %s, postal_code = %s, 
                prefecture = %s, city = %s, address_detail = %s,
                recruitment_source = %s, mypage_id = %s,
                mypage_password_hash = %s,
                current_points = %s, member_type = %s, status = %s,
                web_member = %s, comment = %s, nickname = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = %s
        ''', (
            customer_data['name'],
            customer_data.get('furigana'),
            customer_data.get('phone'),
            customer_data.get('birthday'),
            age,
            customer_data.get('postal_code'),
            customer_data.get('prefecture'),
            customer_data.get('city'),
            customer_data.get('address_detail'),
            customer_data.get('recruitment_source'),
            customer_data.get('mypage_id'),
            mypage_password_hash,
            customer_data.get('current_points', 0),
            customer_data.get('member_type', '通常会員'),
            customer_data.get('status', '普通'),
            customer_data.get('web_member', 'web会員'),
            customer_data.get('comment'),
            customer_data.get('nickname'),
            customer_id
        ))
    else:
        # パスワード更新なし
        cur.execute('''
            UPDATE customers SET
                name = %s, furigana = %s, phone = %s,
                birthday = %s, age = %s, postal_code = %s,
                prefecture = %s, city = %s, address_detail = %s,
                recruitment_source = %s, mypage_id = %s,
                current_points = %s, member_type = %s, status = %s,
                web_member = %s, comment = %s, nickname = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = %s
        ''', (
            customer_data['name'],
            customer_data.get('furigana'),
            customer_data.get('phone'),
            customer_data.get('birthday'),
            age,
            customer_data.get('postal_code'),
            customer_data.get('prefecture'),
            customer_data.get('city'),
            customer_data.get('address_detail'),
            customer_data.get('recruitment_source'),
            customer_data.get('mypage_id'),
            customer_data.get('current_points', 0),
            customer_data.get('member_type', '通常会員'),
            customer_data.get('status', '普通'),
            customer_data.get('web_member', 'web会員'),
            customer_data.get('comment'),
            customer_data.get('nickname'),
            customer_id
        ))
    
    conn.commit()
    cur.close()
    conn.close()

def delete_customer(store_code, customer_id):
    """顧客削除"""
    conn = get_db_connection(store_code)
    cur = conn.cursor()
    
    cur.execute('DELETE FROM customers WHERE customer_id = %s', (customer_id,))
    
    conn.commit()
    cur.close()
    conn.close()

def search_customers(store_code, keyword):
    """顧客を検索（電話番号またはフリガナ）"""
    conn = get_db_connection(store_code)
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            # 電話番号、フリガナ、名前のいずれかで部分一致検索
            sql = """
                SELECT 
                    customer_id,
                    name,
                    furigana,
                    phone,
                    birthday,
                    age,
                    prefecture,
                    city,
                    address_detail,
                    recruitment_source,
                    mypage_id,
                    current_points,
                    member_type,
                    status,
                    web_member,
                    comment,
                    nickname,
                    created_at,
                    updated_at
                FROM customers 
                WHERE phone LIKE %s 
                   OR furigana LIKE %s
                   OR name LIKE %s
                ORDER BY customer_id DESC
            """
            search_pattern = f"%{keyword}%"
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
    finally:
        conn.close()