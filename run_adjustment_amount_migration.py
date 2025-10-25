# -*- coding: utf-8 -*-
"""
reservationsテーブルにadjustment_amountカラムを追加するマイグレーション
Flask app contextで実行
"""
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    from database.connection import get_db

    def run_migration():
        """adjustment_amountカラムを追加"""
        with app.app_context():
            db = get_db()

            try:
                # カラムが既に存在するかチェック
                cursor = db.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'reservations'
                    AND column_name = 'adjustment_amount'
                """)

                if cursor.fetchone():
                    print("OK: adjustment_amount column already exists")
                    return True

                # adjustment_amountカラムを追加
                print("Adding adjustment_amount column...")
                db.execute("""
                    ALTER TABLE reservations
                    ADD COLUMN adjustment_amount INTEGER DEFAULT 0
                """)

                db.commit()
                print("SUCCESS: adjustment_amount column added")
                return True

            except Exception as e:
                db.rollback()
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                db.close()

    if __name__ == '__main__':
        success = run_migration()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    print("\nAlternative: Execute this SQL directly:")
    print("=" * 60)
    print("""
ALTER TABLE reservations
ADD COLUMN adjustment_amount INTEGER DEFAULT 0;
""")
    print("=" * 60)
    sys.exit(1)
