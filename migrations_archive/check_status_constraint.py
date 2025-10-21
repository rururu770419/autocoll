import sys
sys.path.append(r'C:\Users\Admin\autocoll\multi_store_app')

from database.connection import get_db

try:
    db = get_db()
    cursor = db.cursor()

    # CHECK制約を確認
    cursor.execute("""
        SELECT
            con.conname AS constraint_name,
            pg_get_constraintdef(con.oid) AS constraint_definition
        FROM pg_constraint con
        INNER JOIN pg_class rel ON rel.oid = con.conrelid
        INNER JOIN pg_namespace nsp ON nsp.oid = connamespace
        WHERE nsp.nspname = 'public'
        AND rel.relname = 'reservations'
        AND con.contype = 'c'
    """)

    constraints = cursor.fetchall()

    print("=" * 80)
    print("reservationsテーブルのCHECK制約")
    print("=" * 80)

    if constraints:
        for constraint in constraints:
            print(f"\n制約名: {constraint['constraint_name']}")
            print(f"定義: {constraint['constraint_definition']}")
    else:
        print("CHECK制約は見つかりませんでした")

    db.close()

except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
