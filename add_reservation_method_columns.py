#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reservationsテーブルにreservation_method_idとreservation_method_nameカラムを追加
"""

from database.connection import get_db

def add_columns():
    db = get_db()
    cursor = db.cursor()

    try:
        # カラムを追加
        print("Adding reservation_method_id and reservation_method_name columns to reservations table...")

        cursor.execute("""
            ALTER TABLE reservations
            ADD COLUMN IF NOT EXISTS reservation_method_id INTEGER,
            ADD COLUMN IF NOT EXISTS reservation_method_name VARCHAR(255)
        """)

        db.commit()
        print("SUCCESS: Columns added successfully!")

        # 確認
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'reservations'
            AND column_name IN ('reservation_method_id', 'reservation_method_name')
            ORDER BY ordinal_position
        """)

        print("\nConfirmation:")
        for row in cursor.fetchall():
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    add_columns()
