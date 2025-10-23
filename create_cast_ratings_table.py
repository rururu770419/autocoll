# -*- coding: utf-8 -*-
"""キャスト顧客評価テーブルを作成するスクリプト"""

from database.connection import get_connection

def create_cast_customer_ratings_table():
    """cast_customer_ratingsテーブルを作成"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # テーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cast_customer_ratings (
                rating_id SERIAL PRIMARY KEY,
                cast_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                rating_value TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cast_id, customer_id, item_id, store_id)
            )
        """)

        # インデックス作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cast_customer_ratings_cast_customer
            ON cast_customer_ratings(cast_id, customer_id, store_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cast_customer_ratings_customer
            ON cast_customer_ratings(customer_id, store_id)
        """)

        conn.commit()
        print("✅ cast_customer_ratingsテーブルの作成が完了しました")

    except Exception as e:
        print(f"❌ エラー: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_cast_customer_ratings_table()
