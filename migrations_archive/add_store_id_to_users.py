#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
usersテーブルにstore_idカラムを追加するスクリプト
"""

from database.connection import get_db

def add_store_id_to_users():
    """usersテーブルにstore_idカラムを追加"""
    db = get_db()
    cursor = db.cursor()

    try:
        print("1. store_idカラムを追加中...")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS store_id INTEGER
        """)
        print("   ✓ store_idカラムを追加しました")

        print("\n2. 既存データにstore_idを設定中...")
        cursor.execute("""
            UPDATE users SET store_id = 1 WHERE store_id IS NULL
        """)
        updated_count = cursor.rowcount
        print(f"   ✓ {updated_count}件のレコードにstore_id=1を設定しました")

        print("\n3. NOT NULL制約を追加中...")
        cursor.execute("""
            ALTER TABLE users ALTER COLUMN store_id SET NOT NULL
        """)
        print("   ✓ NOT NULL制約を追加しました")

        print("\n4. インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id)
        """)
        print("   ✓ インデックスを作成しました")

        db.commit()

        print("\n5. 確認：usersテーブルのデータ")
        cursor.execute("""
            SELECT id, login_id, name, role, store_id
            FROM users
            ORDER BY store_id, id
        """)
        results = cursor.fetchall()

        print("\n" + "="*80)
        print(f"{'ID':<5} {'ログインID':<20} {'名前':<20} {'役割':<15} {'店舗ID':<10}")
        print("="*80)
        for row in results:
            print(f"{row['id']:<5} {row['login_id']:<20} {row['name']:<20} {row['role']:<15} {row['store_id']:<10}")
        print("="*80)

        print("\n✅ usersテーブルへのstore_id追加が完了しました！")

    except Exception as e:
        db.rollback()
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    add_store_id_to_users()
