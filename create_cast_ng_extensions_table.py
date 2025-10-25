# -*- coding: utf-8 -*-
"""
キャストNG延長テーブルの作成
"""
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

try:
    print("Creating cast_ng_extensions table...")

    # cast_ng_extensionsテーブルを作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cast_ng_extensions (
            id SERIAL PRIMARY KEY,
            cast_id INTEGER NOT NULL,
            extension_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            store_id INTEGER NOT NULL,
            UNIQUE(cast_id, extension_id),
            FOREIGN KEY (cast_id) REFERENCES casts(cast_id) ON DELETE CASCADE,
            FOREIGN KEY (extension_id) REFERENCES extensions(extension_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    print("OK: cast_ng_extensions table created successfully")

    # 確認
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'cast_ng_extensions'
        ORDER BY ordinal_position;
    """)

    print("\nTable structure:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\nComplete!")
