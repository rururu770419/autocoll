import sys
sys.path.append(r'C:\Users\Admin\autocoll\multi_store_app')

from database.connection import get_db

try:
    db = get_db()
    cursor = db.cursor()

    # 全テーブル一覧を取得
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()

    print("=" * 60)
    print("全テーブル一覧")
    print("=" * 60)
    for table in tables:
        table_name = table['table_name'] if isinstance(table, dict) else table[0]
        print(f"  - {table_name}")
    print()

    # reservationsテーブルの存在確認
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'reservations'
        )
    """)
    exists = cursor.fetchone()
    reservations_exists = exists['exists'] if isinstance(exists, dict) else exists[0]

    print("=" * 60)
    print("reservationsテーブルの存在確認")
    print("=" * 60)
    if reservations_exists:
        print("✅ reservationsテーブルは存在します")
        print()

        # テーブル構造を表示
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'reservations'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print(f"カラム数: {len(columns)}")
        for col in columns:
            col_name = col['column_name'] if isinstance(col, dict) else col[0]
            data_type = col['data_type'] if isinstance(col, dict) else col[1]
            is_null = col['is_nullable'] if isinstance(col, dict) else col[2]
            default = col['column_default'] if isinstance(col, dict) else col[3]
            print(f"  {col_name:30} {data_type:20} NULL: {is_null:3} Default: {default}")
    else:
        print("❌ reservationsテーブルは存在しません")
        print("   → テーブルを作成する必要があります")

    db.close()

except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
