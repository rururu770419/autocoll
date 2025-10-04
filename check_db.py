import sys
sys.path.append(r'C:\Users\Admin\autocoll\multi_store_app')

from database.connection import get_db
import traceback

try:
    db = get_db()
    if db is None:
        print("エラー: データベース接続に失敗しました")
        sys.exit(1)
    
    cursor = db.cursor()
    
    print("=" * 60)
    print("PostgreSQLバージョン確認")
    print("=" * 60)
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    # dict形式で返ってくる可能性があるため、両方に対応
    if isinstance(version, dict):
        print(f"PostgreSQL Version: {version.get('version', version)}")
    else:
        print(f"PostgreSQL Version: {version[0] if version else 'Unknown'}")
    print()
    
    print("=" * 60)
    print("coursesテーブルの構造")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'courses'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    if columns:
        print(f"カラム数: {len(columns)}")
        for col in columns:
            col_name = col['column_name'] if isinstance(col, dict) else col[0]
            data_type = col['data_type'] if isinstance(col, dict) else col[1]
            is_null = col['is_nullable'] if isinstance(col, dict) else col[2]
            default = col['column_default'] if isinstance(col, dict) else col[3]
            print(f"  {col_name:20} {data_type:15} NULL: {is_null:3} Default: {default}")
    else:
        print("  テーブルが見つかりません")
    print()
    
    print("=" * 60)
    print("coursesテーブルのサンプルデータ（最初の3件）")
    print("=" * 60)
    cursor.execute("SELECT * FROM courses LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        # 最初の行のキーを取得
        if isinstance(rows[0], dict):
            keys = list(rows[0].keys())
        else:
            # タプルの場合、カラム情報を取得
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'courses'
                ORDER BY ordinal_position
            """)
            col_info = cursor.fetchall()
            keys = [c['column_name'] if isinstance(c, dict) else c[0] for c in col_info]
        
        print(f"カラム名: {keys}")
        print()
        for i, row in enumerate(rows, 1):
            print(f"レコード {i}:")
            if isinstance(row, dict):
                for key in row.keys():
                    print(f"  {key}: {row[key]}")
            else:
                for idx, key in enumerate(keys):
                    print(f"  {key}: {row[idx] if idx < len(row) else 'N/A'}")
            print()
    else:
        print("  データがありません")
    print()
    
    print("=" * 60)
    print("money_recordsテーブルの構造")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'money_records'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    if columns:
        print(f"カラム数: {len(columns)}")
        for col in columns:
            col_name = col['column_name'] if isinstance(col, dict) else col[0]
            data_type = col['data_type'] if isinstance(col, dict) else col[1]
            is_null = col['is_nullable'] if isinstance(col, dict) else col[2]
            default = col['column_default'] if isinstance(col, dict) else col[3]
            print(f"  {col_name:20} {data_type:15} NULL: {is_null:3} Default: {default}")
    else:
        print("  テーブルが見つかりません")
    print()
    
    print("✅ データベース構造の確認が完了しました")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    traceback.print_exc()