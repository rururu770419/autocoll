# -*- coding: utf-8 -*-
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# 外部キー制約の確認
cursor.execute("""
    SELECT
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'reservations'
      AND kcu.column_name = 'extension_id';
""")

print("Extension foreign key constraint:")
for row in cursor.fetchall():
    print(row)

# extensionsテーブルの確認
cursor.execute("SELECT COUNT(*) FROM extensions;")
print(f"\nExtensions table count: {cursor.fetchone()[0]}")

# extension_timesテーブルの確認
try:
    cursor.execute("SELECT COUNT(*) FROM extension_times;")
    print(f"Extension_times table count: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Extension_times table error: {e}")

# extensionsテーブルのデータ確認
cursor.execute("SELECT extension_id, extension_name FROM extensions ORDER BY extension_id;")
print("\nExtensions table data:")
for row in cursor.fetchall():
    print(row)

conn.close()
