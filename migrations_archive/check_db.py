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
    print("reservationsテーブルにdiscount_badge_nameカラムを追加")
    print("=" * 60)

    # discount_badge_nameカラムを追加
    cursor.execute("""
        ALTER TABLE reservations
        ADD COLUMN IF NOT EXISTS discount_badge_name VARCHAR(4)
    """)

    db.commit()
    print("✓ discount_badge_nameカラムを追加しました")
    print()

    print("=" * 60)
    print("reservation_discountsテーブルを作成（複数割引対応）")
    print("=" * 60)

    # reservation_discountsテーブルを作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservation_discounts (
            id SERIAL PRIMARY KEY,
            reservation_id INTEGER NOT NULL,
            discount_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
            FOREIGN KEY (discount_id) REFERENCES discounts(discount_id) ON DELETE CASCADE
        )
    """)

    # インデックスを作成
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservation_discounts_reservation_id ON reservation_discounts(reservation_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservation_discounts_discount_id ON reservation_discounts(discount_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservation_discounts_store_id ON reservation_discounts(store_id)
    """)

    db.commit()
    print("✓ reservation_discountsテーブルを作成しました")
    print()

    # 既存の予約データを reservation_discounts に移行
    print("=" * 60)
    print("既存の割引データを reservation_discounts に移行")
    print("=" * 60)

    # discount_id が NULL でない予約を取得（discount_amountも取得）
    cursor.execute("""
        SELECT reservation_id, discount_id, discount_amount, store_id
        FROM reservations
        WHERE discount_id IS NOT NULL
    """)

    existing_reservations = cursor.fetchall()
    migrated_count = 0
    skipped_count = 0

    for row in existing_reservations:
        res_id = row[0] if isinstance(row, tuple) else row['reservation_id']
        disc_id = row[1] if isinstance(row, tuple) else row['discount_id']
        disc_amount = row[2] if isinstance(row, tuple) else row['discount_amount']
        st_id = row[3] if isinstance(row, tuple) else row['store_id']

        # discount_amountがNULLの場合は0に設定
        if disc_amount is None:
            disc_amount = 0

        # 既に存在するかチェック
        cursor.execute("""
            SELECT COUNT(*) FROM reservation_discounts
            WHERE reservation_id = %s AND discount_id = %s AND store_id = %s
        """, (res_id, disc_id, st_id))

        count_result = cursor.fetchone()
        exists = (count_result[0] if isinstance(count_result, tuple) else count_result['count']) > 0

        if not exists:
            # reservation_discounts に挿入（applied_valueを含む）
            cursor.execute("""
                INSERT INTO reservation_discounts (reservation_id, discount_id, applied_value, store_id)
                VALUES (%s, %s, %s, %s)
            """, (res_id, disc_id, disc_amount, st_id))
            migrated_count += 1
        else:
            skipped_count += 1

    db.commit()
    print(f"✓ {migrated_count} 件の割引データを移行しました")
    if skipped_count > 0:
        print(f"  ({skipped_count} 件は既に存在していたためスキップしました)")
    print()

    # 確認
    print("=" * 60)
    print("reservationsテーブルの割引関連カラム確認")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'reservations' AND column_name LIKE '%discount%'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    if columns:
        for col in columns:
            col_name = col['column_name'] if isinstance(col, dict) else col[0]
            data_type = col['data_type'] if isinstance(col, dict) else col[1]
            max_length = col['character_maximum_length'] if isinstance(col, dict) else col[2]
            length_str = f"({max_length})" if max_length else ""
            print(f"  {col_name:25} {data_type}{length_str}")
    else:
        print("  割引関連のカラムが見つかりません")
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