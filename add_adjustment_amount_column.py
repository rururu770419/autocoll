# -*- coding: utf-8 -*-
"""
reservationsテーブルにadjustment_amountカラムを追加するマイグレーション
"""
from database.connection import get_db

def add_adjustment_amount_column():
    """reservationsテーブルにadjustment_amountカラムを追加"""
    db = get_db()

    try:
        # adjustment_amountカラムが既に存在するかチェック
        cursor = db.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'reservations'
            AND column_name = 'adjustment_amount'
        """)

        if cursor.fetchone():
            print("✅ adjustment_amountカラムは既に存在します")
            return

        # adjustment_amountカラムを追加
        print("adjustment_amountカラムを追加中...")
        db.execute("""
            ALTER TABLE reservations
            ADD COLUMN adjustment_amount INTEGER DEFAULT 0
        """)

        db.commit()
        print("✅ adjustment_amountカラムを追加しました")

    except Exception as e:
        db.rollback()
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    add_adjustment_amount_column()
