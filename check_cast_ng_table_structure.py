# -*- coding: utf-8 -*-
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# cast_ng_optionsテーブルの構造を確認
print("cast_ng_options table structure:")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'cast_ng_options'
    ORDER BY ordinal_position;
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

# 制約も確認
print("\nConstraints:")
cursor.execute("""
    SELECT constraint_name, constraint_type
    FROM information_schema.table_constraints
    WHERE table_name = 'cast_ng_options';
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
