#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
discountsテーブルのカラム名を確認
"""

from database.connection import get_db

db = get_db()
cursor = db.cursor()

print("=== discountsテーブルのカラム一覧 ===")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'discounts'
    ORDER BY ordinal_position
""")

for row in cursor.fetchall():
    print(f"  {row['column_name']}: {row['data_type']}")

db.close()
