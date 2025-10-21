#!/usr/bin/env python3
"""
usersテーブルにsort_orderカラムを追加するスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_db_connection

def add_sort_order_column():
    """usersテーブルにsort_orderカラムを追加"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        print("1. sort_orderカラムを追加中...")
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0
        """)

        print("2. 既存のスタッフにsort_orderを設定中（名前順）...")
        cursor.execute("""
            WITH ranked_users AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY name) as new_order
                FROM users
                WHERE is_active = true
            )
            UPDATE users
            SET sort_order = ranked_users.new_order
            FROM ranked_users
            WHERE users.id = ranked_users.id
        """)

        print("3. インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_sort_order ON users(sort_order)
        """)

        conn.commit()
        print("✅ 完了しました！")

        # 確認
        print("\n現在のスタッフ一覧（sort_order順）:")
        cursor.execute("""
            SELECT id, name, sort_order
            FROM users
            WHERE is_active = true
            ORDER BY sort_order
        """)

        for row in cursor.fetchall():
            print(f"  ID: {row[0]}, 名前: {row[1]}, sort_order: {row[2]}")

        cursor.close()

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

    return True

if __name__ == "__main__":
    success = add_sort_order_column()
    sys.exit(0 if success else 1)
