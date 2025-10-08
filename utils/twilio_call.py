# -*- coding: utf-8 -*-
"""
Twilioオートコール機能
キャストに自動電話をかける
"""
import os
import psycopg
from psycopg.rows import dict_row
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

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


def get_twilio_settings():
    """
    データベースからTwilio設定を取得
    
    Returns:
        dict: Twilio設定
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT setting_key, setting_value
            FROM store_settings
            WHERE setting_key IN (
                'twilio_account_sid',
                'twilio_auth_token',
                'twilio_phone_number',
                'call_timeout_seconds',
                'auto_call_enabled'
            )
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        settings = {}
        for row in rows:
            settings[row['setting_key']] = row['setting_value']
        
        # 🔍 デバッグ出力
        print(f"🔍 DEBUG: Retrieved settings = {settings}")
        print(f"🔍 DEBUG: auto_call_enabled = '{settings.get('auto_call_enabled')}'")
        print(f"🔍 DEBUG: Comparison result = {settings.get('auto_call_enabled') == 'true'}")
        
        return settings
        
    except Exception as e:
        print(f"❌ 設定取得エラー: {e}")
        return {}


def format_phone_number(phone):
    """
    電話番号を国際形式（+81形式）に変換
    
    Args:
        phone (str): 電話番号（例: '08091729180', '090-9172-9180', '+819091729180'）
    
    Returns:
        str: 国際形式の電話番号（例: '+819091729180'）
    """
    if not phone:
        return phone
    
    # ハイフンとスペースを除去
    clean = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    
    # 既に+81形式なら返す
    if clean.startswith('+81'):
        return clean
    
    # 0から始まる場合は+81に変換
    if clean.startswith('0'):
        return '+81' + clean[1:]
    
    # それ以外はそのまま返す
    return clean


def make_auto_call(to_phone_number, cast_name, exit_time_str):
    """
    キャストに自動電話をかける
    
    Args:
        to_phone_number (str): 発信先電話番号（例: '08091729180' or '+819091729180'）
        cast_name (str): キャスト名
        exit_time_str (str): 退室時刻（例: '18:30'）
    
    Returns:
        dict: {
            'success': bool,
            'call_sid': str or None,
            'error': str or None
        }
    """
    try:
        # データベースから設定を取得
        settings = get_twilio_settings()
        
        # オートコールが無効なら終了
        if settings.get('auto_call_enabled') != 'true':
            return {
                'success': False,
                'call_sid': None,
                'error': 'オートコールが無効になっています'
            }
        
        # Twilio認証情報
        account_sid = settings.get('twilio_account_sid')
        auth_token = settings.get('twilio_auth_token')
        phone_number = settings.get('twilio_phone_number')
        timeout_seconds = int(settings.get('call_timeout_seconds', 20))
        
        if not all([account_sid, auth_token, phone_number]):
            return {
                'success': False,
                'call_sid': None,
                'error': 'Twilio認証情報が設定されていません'
            }
        
        # 🔧 電話番号を国際形式に変換
        formatted_phone = format_phone_number(to_phone_number)
        
        # Twilioクライアント
        client = Client(account_sid, auth_token)
        
        # TwiML URL（音声メッセージ）
        twiml_url = os.getenv('TWIML_URL', 'http://twimlets.com/holdmusic?Bucket=com.twilio.music.classical')
        
        print(f"Making auto call to {cast_name} ({formatted_phone})...")
        print(f"Exit time: {exit_time_str}, Timeout: {timeout_seconds}秒")
        
        # 電話をかける
        call = client.calls.create(
            to=formatted_phone,  # 🔧 変換後の番号を使用
            from_=phone_number,
            url=twiml_url,
            timeout=timeout_seconds,
            status_callback_event=['completed'],
            status_callback_method='POST'
        )
        
        print(f"Call SID: {call.sid}")
        
        return {
            'success': True,
            'call_sid': call.sid,
            'error': None
        }
        
    except Exception as e:
        print(f"Error making call: {e}")
        return {
            'success': False,
            'call_sid': None,
            'error': str(e)
        }


def get_call_status(call_sid):
    """
    通話ステータスを取得
    
    Args:
        call_sid (str): Twilio Call SID
    
    Returns:
        dict: {
            'status': str,  # queued, ringing, in-progress, completed, failed, busy, no-answer
            'duration': int or None,
            'error': str or None
        }
    """
    try:
        settings = get_twilio_settings()
        account_sid = settings.get('twilio_account_sid')
        auth_token = settings.get('twilio_auth_token')
        
        if not all([account_sid, auth_token]):
            return {
                'status': 'error',
                'duration': None,
                'error': 'Twilio認証情報が設定されていません'
            }
        
        client = Client(account_sid, auth_token)
        call = client.calls(call_sid).fetch()
        
        return {
            'status': call.status,
            'duration': call.duration,
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'duration': None,
            'error': str(e)
        }


# テスト用
if __name__ == '__main__':
    # テスト実行
    result = make_auto_call(
        to_phone_number='+819012345678',  # テスト用電話番号
        cast_name='テストキャスト',
        exit_time_str='18:30'
    )
    
    print(f"\nResult: {result}")