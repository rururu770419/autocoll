import sys
sys.path.append(r'C:\Users\Admin\autocoll\multi_store_app')

from database.connection import get_db

try:
    db = get_db()
    cursor = db.cursor()

    print("=" * 80)
    print("reservations_status_check制約の修正")
    print("=" * 80)

    # 既存の制約を確認
    print("\n1. 現在の制約を確認中...")
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
    if constraints:
        for constraint in constraints:
            print(f"   制約名: {constraint['constraint_name']}")
            print(f"   定義: {constraint['constraint_definition']}")
    else:
        print("   CHECK制約は見つかりませんでした")

    # 既存の制約を削除
    print("\n2. reservations_status_check制約を削除中...")
    cursor.execute("ALTER TABLE reservations DROP CONSTRAINT IF EXISTS reservations_status_check")
    db.commit()
    print("   ✅ 制約を削除しました")

    # 新しい制約を追加（日本語の値を許可）
    print("\n3. 新しい制約を追加中...")
    cursor.execute("""
        ALTER TABLE reservations ADD CONSTRAINT reservations_status_check
            CHECK (status IN ('成約', 'キャンセル', '仮予約', '確定', '完了'))
    """)
    db.commit()
    print("   ✅ 新しい制約を追加しました")
    print("   許可される値: '成約', 'キャンセル', '仮予約', '確定', '完了'")

    # 確認
    print("\n4. 修正後の制約を確認中...")
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
    if constraints:
        for constraint in constraints:
            print(f"   制約名: {constraint['constraint_name']}")
            print(f"   定義: {constraint['constraint_definition']}")

    print("\n" + "=" * 80)
    print("✅ 制約の修正が完了しました")
    print("=" * 80)

    db.close()

except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    if 'db' in locals():
        db.rollback()
        db.close()
