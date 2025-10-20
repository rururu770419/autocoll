#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
予約テーブルのホテル情報を確認
"""

from database.connection import get_db
import json

db = get_db()
cursor = db.cursor()

print("=== 最新の予約3件のホテル情報 ===")
cursor.execute("""
    SELECT reservation_id, hotel_id, hotel_name, room_number, customer_name
    FROM reservations
    ORDER BY reservation_id DESC
    LIMIT 3
""")

for row in cursor.fetchall():
    print(f"\n予約ID: {row['reservation_id']}")
    print(f"  顧客名: {row['customer_name']}")
    print(f"  ホテルID: {row['hotel_id']}")
    print(f"  ホテル名: {row['hotel_name']}")
    print(f"  部屋番号: {row['room_number']}")

db.close()
