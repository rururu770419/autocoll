#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
既存予約のend_datetimeを再計算して更新する

コース時間と延長時間から正しい終了時刻を計算します。
"""
from datetime import datetime, timedelta
from database.connection import get_db

def fix_end_datetime():
    """すべての予約のend_datetimeを再計算"""
    db = get_db()
    cursor = db.cursor()

    try:
        # すべての予約を取得（キャンセル・削除以外）
        cursor.execute("""
            SELECT
                reservation_id,
                reservation_datetime,
                course_time_minutes,
                extension_minutes,
                end_datetime,
                customer_name
            FROM reservations
            WHERE status NOT IN ('キャンセル', 'cancelled', 'deleted')
            ORDER BY reservation_id
        """)

        reservations = cursor.fetchall()
        print(f'対象予約数: {len(reservations)}件\n')

        updated_count = 0
        skipped_count = 0

        for row in reservations:
            reservation_id = row[0]
            reservation_datetime = row[1]
            course_time_minutes = row[2] or 0
            extension_minutes = row[3] or 0
            current_end_datetime = row[4]
            customer_name = row[5]

            # 合計時間を計算
            total_minutes = course_time_minutes + extension_minutes

            if total_minutes == 0:
                print(f'⚠️  予約ID {reservation_id} ({customer_name}): コース時間が0分のためスキップ')
                skipped_count += 1
                continue

            # 新しい終了時刻を計算
            if isinstance(reservation_datetime, str):
                reservation_dt = datetime.strptime(reservation_datetime, '%Y-%m-%d %H:%M:%S')
            else:
                reservation_dt = reservation_datetime
            new_end_datetime = reservation_dt + timedelta(minutes=total_minutes)

            # 現在の値と比較
            if current_end_datetime == new_end_datetime:
                print(f'✓ 予約ID {reservation_id} ({customer_name}): すでに正しい値です')
                continue

            print(f'🔧 予約ID {reservation_id} ({customer_name}):')
            print(f'   開始: {reservation_datetime}')
            print(f'   コース時間: {course_time_minutes}分')
            print(f'   延長時間: {extension_minutes}分')
            print(f'   合計: {total_minutes}分')
            print(f'   旧終了時刻: {current_end_datetime}')
            print(f'   新終了時刻: {new_end_datetime}')

            # 更新
            cursor.execute("""
                UPDATE reservations
                SET end_datetime = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE reservation_id = %s
            """, (new_end_datetime, reservation_id))

            updated_count += 1
            print(f'   ✅ 更新完了\n')

        # コミット
        db.commit()

        print('=' * 60)
        print(f'処理完了:')
        print(f'  更新: {updated_count}件')
        print(f'  スキップ: {skipped_count}件')
        print(f'  合計: {len(reservations)}件')
        print('=' * 60)

    except Exception as e:
        db.rollback()
        print(f'❌ エラー発生: {e}')
        raise

    finally:
        db.close()

if __name__ == '__main__':
    print('既存予約のend_datetime再計算スクリプト')
    print('=' * 60)

    response = input('\n予約データを更新しますか？ (yes/no): ')

    if response.lower() in ['yes', 'y']:
        fix_end_datetime()
    else:
        print('キャンセルされました')
