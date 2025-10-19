#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
customersテーブルにcar_infoカラムを追加するスクリプト
"""
import sys
sys.path.append(r'C:\Users\Admin\autocoll\multi_store_app')

from database.connection import get_db

def add_car_info_column():
    """customersテーブルにcar_infoカラムを追加"""
    db = get_db()
    cursor = db.cursor()

    try:
        # car_infoカラムを追加
        cursor.execute("""
            ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS car_info VARCHAR(255) DEFAULT NULL;
        """)
        db.commit()
        print("✓ car_infoカラムを追加しました")

    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_car_info_column()
