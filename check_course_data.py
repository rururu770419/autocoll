#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""コースと予約データを確認"""
from database.connection import get_db

db = get_db()
cursor = db.cursor()

# コースマスタを確認
print('=== コースマスタ（store_id=1） ===')
cursor.execute('''
    SELECT course_id, name, time_minutes, price
    FROM courses
    WHERE store_id = 1
    ORDER BY course_id
    LIMIT 10
''')
for row in cursor.fetchall():
    print(f'ID:{row[0]}, 名前:{row[1]}, 時間:{row[2]}分, 料金:{row[3]}円')

print('\n=== 予約ID 22の詳細 ===')
cursor.execute('''
    SELECT
        reservation_id,
        customer_name,
        course_id,
        course_name,
        course_time_minutes,
        reservation_datetime,
        end_datetime,
        extension_id,
        extension_minutes
    FROM reservations
    WHERE reservation_id = 22
''')
row = cursor.fetchone()
if row:
    print(f'予約ID: {row[0]}')
    print(f'お客様: {row[1]}')
    print(f'コースID: {row[2]}')
    print(f'コース名: {row[3]}')
    print(f'コース時間: {row[4]}分')
    print(f'開始: {row[5]}')
    print(f'終了: {row[6]}')
    print(f'延長ID: {row[7]}')
    print(f'延長時間: {row[8]}分')

print('\n=== 予約ID 23の詳細 ===')
cursor.execute('''
    SELECT
        reservation_id,
        customer_name,
        course_id,
        course_name,
        course_time_minutes,
        reservation_datetime,
        end_datetime,
        extension_id,
        extension_minutes
    FROM reservations
    WHERE reservation_id = 23
''')
row = cursor.fetchone()
if row:
    print(f'予約ID: {row[0]}')
    print(f'お客様: {row[1]}')
    print(f'コースID: {row[2]}')
    print(f'コース名: {row[3]}')
    print(f'コース時間: {row[4]}分')
    print(f'開始: {row[5]}')
    print(f'終了: {row[6]}')
    print(f'延長ID: {row[7]}')
    print(f'延長時間: {row[8]}分')

db.close()
