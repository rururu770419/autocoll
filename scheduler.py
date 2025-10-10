# -*- coding: utf-8 -*-
"""
オートコール・LINE通知スケジューラー
5分ごとにpickup_recordsをチェックし、通知タイミングが来たら自動実行
"""
import os
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.twilio_call import make_auto_call
from utils.line_messaging import send_pickup_reminder_to_staff

load_dotenv()

# グローバルスケジューラー
scheduler = None

def get_db_connection():
    """データベース接続を取得"""
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname='pickup_system',
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'diary8475ftkb'),
        row_factory=dict_row
    )
    return conn


def check_and_send_notifications():
    """
    ピックアップレコードをチェックして通知を送信
    5分ごとに実行される
    """
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 通知チェック開始...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 現在時刻
        now = datetime.now()
        
        # ===== キャストへのオートコール =====
        cursor.execute("""
            SELECT 
                pr.record_id,
                pr.cast_id,
                pr.staff_id,
                pr.exit_time,
                pr.cast_auto_call_sent,
                c.name AS cast_name,
                c.phone_number AS cast_phone,
                c.notification_minutes_before AS cast_notification_minutes,
                c.auto_call_enabled,
                h.name AS hotel_name,
                h.address AS hotel_address
            FROM pickup_records pr
            JOIN casts c ON pr.cast_id = c.cast_id
            LEFT JOIN hotels h ON pr.hotel_id = h.hotel_id
            WHERE 
                pr.cast_auto_call_sent = FALSE
                AND c.auto_call_enabled = TRUE
                AND c.phone_number IS NOT NULL
                AND pr.exit_time IS NOT NULL
                AND (pr.exit_time - INTERVAL '1 minute' * c.notification_minutes_before) <= %s
                AND (pr.exit_time - INTERVAL '1 minute' * c.notification_minutes_before) > %s
        """, (now, now - timedelta(minutes=5)))
        
        cast_records = cursor.fetchall()
        
        for record in cast_records:
            print(f"  → キャストへのオートコール: {record['cast_name']}さん")
            
            # 退室時刻をフォーマット
            exit_time_str = record['exit_time'].strftime('%H:%M')
            
            # Twilio発信
            result = make_auto_call(
                to_phone_number=record['cast_phone'],
                cast_name=record['cast_name'],
                exit_time_str=exit_time_str
            )
            
            # 送信フラグを更新
            if result['success']:
                cursor.execute("""
                    UPDATE pickup_records 
                    SET cast_auto_call_sent = TRUE,
                        cast_auto_call_sent_at = CURRENT_TIMESTAMP
                    WHERE record_id = %s
                """, (record['record_id'],))
                conn.commit()
                print(f"    ✅ オートコール送信成功（Record ID: {record['record_id']}）")
            else:
                print(f"    ❌ オートコール送信失敗: {result['error']}")
        
        # ===== スタッフへのLINE通知 =====
        cursor.execute("""
            SELECT 
                pr.record_id,
                pr.cast_id,
                pr.staff_id,
                pr.exit_time,
                pr.staff_line_sent,
                c.name AS cast_name,
                u.name AS staff_name,
                u.line_id AS staff_line_id,
                u.notification_minutes_before AS staff_notification_minutes,
                h.name AS hotel_name,
                h.address AS hotel_address
            FROM pickup_records pr
            JOIN casts c ON pr.cast_id = c.cast_id
            JOIN users u ON pr.staff_id = u.login_id
            LEFT JOIN hotels h ON pr.hotel_id = h.hotel_id
            WHERE 
                pr.staff_line_sent = FALSE
                AND u.line_id IS NOT NULL
                AND u.line_id != ''
                AND pr.exit_time IS NOT NULL
                AND (pr.exit_time - INTERVAL '1 minute' * u.notification_minutes_before) <= %s
                AND (pr.exit_time - INTERVAL '1 minute' * u.notification_minutes_before) > %s
        """, (now, now - timedelta(minutes=5)))
        
        staff_records = cursor.fetchall()
        
        for record in staff_records:
            print(f"  → スタッフへのLINE通知: {record['staff_name']}さん (LINE ID: {record['staff_line_id']})")
            
            # 退室時刻をフォーマット
            exit_time_str = record['exit_time'].strftime('%H:%M')
            
            # LINE通知
            result = send_pickup_reminder_to_staff(
                staff_name=record['staff_name'],
                cast_name=record['cast_name'],
                exit_time_str=exit_time_str,
                hotel_name=record['hotel_name'] or '未設定'
            )
            
            # 送信フラグを更新
            if result['success']:
                cursor.execute("""
                    UPDATE pickup_records 
                    SET staff_line_sent = TRUE,
                        staff_line_sent_at = CURRENT_TIMESTAMP
                    WHERE record_id = %s
                """, (record['record_id'],))
                conn.commit()
                print(f"    ✅ LINE通知送信成功（Record ID: {record['record_id']}）")
            else:
                print(f"    ❌ LINE通知送信失敗: {result['error']}")
        
        cursor.close()
        conn.close()
        
        if not cast_records and not staff_records:
            print("  通知対象なし")
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 通知チェック完了\n")
        
    except Exception as e:
        print(f"❌ スケジューラーエラー: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """
    スケジューラーを開始
    5分ごとにcheck_and_send_notifications()を実行
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        print("⚠️ スケジューラーは既に起動しています")
        return
    
    scheduler = BackgroundScheduler(timezone='Asia/Tokyo')
    
    # 5分ごとに実行
    scheduler.add_job(
        func=check_and_send_notifications,
        trigger=IntervalTrigger(minutes=5),
        id='notification_check',
        name='通知チェック（5分ごと）',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ オートコール・LINE通知スケジューラー起動")
    print("   実行間隔: 5分ごと")
    print("   次回実行: " + scheduler.get_jobs()[0].next_run_time.strftime('%Y-%m-%d %H:%M:%S'))


def stop_scheduler():
    """スケジューラーを停止"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        print("⏸️ スケジューラーを停止しました")
    else:
        print("⚠️ スケジューラーは起動していません")


def get_scheduler_status():
    """スケジューラーの状態を取得"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
        })
    
    return {
        'running': scheduler.running,
        'jobs': jobs
    }


# 直接実行時のテスト
if __name__ == '__main__':
    print("=== スケジューラーテスト起動 ===")
    print("Ctrl+C で停止できます\n")
    
    start_scheduler()
    
    try:
        # スケジューラーを実行し続ける
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n終了シグナル受信")
        stop_scheduler()