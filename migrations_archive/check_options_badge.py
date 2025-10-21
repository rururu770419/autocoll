#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
optionsテーブルのbadge_nameカラムを確認
"""

from database.connection import get_db

db = get_db()
cursor = db.cursor()

# Check if badge_name column exists in options table
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'options'
    ORDER BY ordinal_position
""")

print('=== optionsテーブルのカラム ===')
for row in cursor.fetchall():
    print(f"  {row['column_name']}: {row['data_type']}")

# Check actual data
print('\n=== 登録されているオプションデータ ===')
cursor.execute('SELECT option_id, name, badge_name, price FROM options LIMIT 5')
for row in cursor.fetchall():
    badge = row.get('badge_name') if row.get('badge_name') else 'NULL'
    print(f"  ID: {row['option_id']}, 名前: {row['name']}, バッジ: {badge}, 金額: {row['price']}")

db.close()
