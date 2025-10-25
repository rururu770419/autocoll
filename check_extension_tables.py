# -*- coding: utf-8 -*-
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# extensionsテーブルの全データ確認
cursor.execute("SELECT * FROM extensions ORDER BY extension_id;")
columns = [desc[0] for desc in cursor.description]
print("Extensions table:")
print(columns)
for row in cursor.fetchall():
    print(row)

print("\n" + "="*50 + "\n")

# extension_timesテーブルの全データ確認
cursor.execute("SELECT * FROM extension_times ORDER BY extension_id;")
columns = [desc[0] for desc in cursor.description]
print("Extension_times table:")
print(columns)
for row in cursor.fetchall():
    print(row)

conn.close()
