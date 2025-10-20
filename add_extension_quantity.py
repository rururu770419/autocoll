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
    print("reservationsテーブルにextension_quantityカラムを追加")
    print("=" * 60)

    # extension_quantityカラムを追加
    cursor.execute("""
        ALTER TABLE reservations
        ADD COLUMN IF NOT EXISTS extension_quantity INTEGER DEFAULT 0
    """)

    db.commit()
    print("✓ extension_quantityカラムを追加しました")
    print()

    # 確認
    print("=" * 60)
    print("reservationsテーブルの延長関連カラム確認")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'reservations' AND column_name LIKE '%extension%'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    if columns:
        for col in columns:
            col_name = col['column_name'] if isinstance(col, dict) else col[0]
            data_type = col['data_type'] if isinstance(col, dict) else col[1]
            default = col['column_default'] if isinstance(col, dict) else col[2]
            print(f"  {col_name:25} {data_type:15} Default: {default}")
    else:
        print("  延長関連のカラムが見つかりません")
    print()

    print("✅ 処理が完了しました")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    traceback.print_exc()
finally:
    if db:
        db.close()
