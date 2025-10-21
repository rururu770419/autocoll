#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reservationsテーブルにdiscount_nameカラムを追加
"""

from database.connection import get_db

db = get_db()
cursor = db.cursor()

try:
    print("Adding discount_name column to reservations table...")

    cursor.execute("""
        ALTER TABLE reservations
        ADD COLUMN IF NOT EXISTS discount_name VARCHAR(255)
    """)

    db.commit()
    print("SUCCESS: Column added successfully!")

    # 確認
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'reservations'
        AND column_name = 'discount_name'
    """)

    row = cursor.fetchone()
    if row:
        print(f"\nConfirmation: {row['column_name']} - {row['data_type']}")
    else:
        print("\nWarning: Column not found after adding")

except Exception as e:
    db.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
