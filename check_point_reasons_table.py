#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ポイント操作理由テーブルの存在確認
"""
import sys
from database.connection import get_db

def check_table():
    """テーブルの存在を確認"""
    try:
        db = get_db()

        # テーブルの存在確認
        db.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'point_operation_reasons'
            )
        """)
        exists = db.fetchone()[0]

        if exists:
            print("✅ point_operation_reasonsテーブルは存在します")

            # テーブル構造を表示
            db.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'point_operation_reasons'
                ORDER BY ordinal_position
            """)
            columns = db.fetchall()

            print("\nテーブル構造:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        else:
            print("❌ point_operation_reasonsテーブルは存在しません")
            print("テーブルを作成する必要があります。")

        db.close()
        return exists

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_table()
