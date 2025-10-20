#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reservationsテーブルにdiscount_badge_nameカラムを追加
"""

from database.connection import get_db

db = get_db()
cursor = db.cursor()

try:
    # discount_badge_nameカラムを追加
    cursor.execute("""
        ALTER TABLE reservations
        ADD COLUMN IF NOT EXISTS discount_badge_name VARCHAR(4)
    """)

    db.commit()
    print("✓ discount_badge_nameカラムを追加しました")

    # 確認
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'reservations' AND column_name LIKE '%discount%'
        ORDER BY ordinal_position
    """)

    print("\n=== reservationsテーブルの割引関連カラム ===")
    for row in cursor.fetchall():
        length = f"({row['character_maximum_length']})" if row['character_maximum_length'] else ""
        print(f"  {row['column_name']}: {row['data_type']}{length}")

except Exception as e:
    print(f"エラー: {e}")
    db.rollback()
finally:
    db.close()
