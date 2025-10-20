#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ホテルAPIのデータ構造を確認
"""

from database.connection import get_db, get_store_id
import json

store_id = get_store_id('nagano')
db = get_db()
cursor = db.cursor()

print("=== ホテル一覧データ ===")
cursor.execute("""
    SELECT hotel_id, name, area_id, transportation_fee
    FROM hotels
    WHERE store_id = %s
    ORDER BY hotel_id
    LIMIT 5
""", (store_id,))

hotels = cursor.fetchall()
print(f"取得件数: {len(hotels)}件\n")

for hotel in hotels:
    print(f"hotel_id: {hotel['hotel_id']}")
    print(f"  name: {hotel['name']}")
    print(f"  area_id: {hotel['area_id']}")
    print(f"  transportation_fee: {hotel['transportation_fee']}")
    print()

db.close()
