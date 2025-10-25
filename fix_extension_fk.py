# -*- coding: utf-8 -*-
"""
外部キー制約を修正: extension_times -> extensions
"""
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

try:
    print("外部キー制約を削除中...")
    # 既存の外部キー制約を削除
    cursor.execute("""
        ALTER TABLE reservations
        DROP CONSTRAINT IF EXISTS reservations_extension_id_fkey;
    """)
    conn.commit()
    print("OK: 古い外部キー制約を削除しました")

    print("\n新しい外部キー制約を追加中...")
    # 正しいテーブル（extensions）への外部キー制約を追加
    cursor.execute("""
        ALTER TABLE reservations
        ADD CONSTRAINT reservations_extension_id_fkey
        FOREIGN KEY (extension_id)
        REFERENCES extensions(extension_id);
    """)
    conn.commit()
    print("OK: 新しい外部キー制約を追加しました（extensions テーブル参照）")

    # 確認
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

    result = cursor.fetchone()
    if result:
        print(f"\n確認: 外部キー制約が正しく設定されました")
        print(f"  制約名: {result[0]}")
        print(f"  参照テーブル: {result[3]}")
    else:
        print("\n警告: 外部キー制約が見つかりません")

except Exception as e:
    conn.rollback()
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n完了!")
