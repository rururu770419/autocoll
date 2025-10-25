# -*- coding: utf-8 -*-
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# cast_ng_extensionsテーブルの存在確認
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'cast_ng_extensions'
    );
""")
exists = cursor.fetchone()[0]

if exists:
    print("cast_ng_extensions table exists")

    # テーブル構造を確認
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'cast_ng_extensions'
        ORDER BY ordinal_position;
    """)
    print("\nTable structure:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # データ件数確認
    cursor.execute("SELECT COUNT(*) FROM cast_ng_extensions;")
    count = cursor.fetchone()[0]
    print(f"\nRecord count: {count}")
else:
    print("cast_ng_extensions table does NOT exist - needs to be created")

conn.close()
