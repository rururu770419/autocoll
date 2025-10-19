# -*- coding: utf-8 -*-
"""
LINE Messaging API通知処理
スタッフへの退室時刻リマインダー通知
店舗へのオートコール結果通知
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from database.connection import get_db

load_dotenv()

def send_line_message(line_user_id, message_text):
    """
    LINE Messaging APIでメッセージを送信
    
    Args:
        line_user_id (str): LINE User ID
        message_text (str): 送信メッセージ
    
    Returns:
        dict: 送信結果 {'success': bool, 'error': str}
    """
    try:
        # Channel Access Tokenをデータベースから取得
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT setting_value 
            FROM store_settings 
            WHERE setting_key = 'line_channel_access_token'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result or not result['setting_value']:
            return {
                'success': False,
                'error': 'LINE Channel Access Tokenが設定されていません'
            }
        
        access_token = result['setting_value']
        
        # LINE Messaging API エンドポイント
        url = 'https://api.line.me/v2/bot/message/push'
        
        # リクエストヘッダー
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # リクエストボディ
        payload = {
            'to': line_user_id,
            'messages': [
                {
                    'type': 'text',
                    'text': message_text
                }
            ]
        }
        
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ LINE通知送信成功: {line_user_id}")
            return {
                'success': True,
                'error': None
            }
        else:
            error_msg = f"LINE API エラー: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
    except Exception as e:
        error_msg = f"LINE通知エラー: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }


def send_pickup_reminder_to_staff(staff_name, cast_name, exit_time_str, hotel_name, line_user_id=None):
    """
    スタッフにピックアップリマインダーを送信（テンプレート使用）

    Args:
        staff_name (str): スタッフ名
        cast_name (str): キャスト名
        exit_time_str (str): 退室時刻
        hotel_name (str): ホテル名
        line_user_id (str, optional): LINE User ID (指定されない場合はDBから取得)

    Returns:
        dict: 送信結果
    """
    try:
        # LINE IDが指定されていない場合は取得（後方互換性のため）
        if not line_user_id:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT line_id
                FROM users
                WHERE name = %s AND line_id IS NOT NULL
                LIMIT 1
            """, (staff_name,))

            result = cursor.fetchone()

            if not result or not result['line_id']:
                cursor.close()
                return {
                    'success': False,
                    'error': f'スタッフ {staff_name} のLINE IDが登録されていません'
                }

            line_user_id = result['line_id']
            cursor.close()
        
        # 🔧 メッセージテンプレートを取得
        cursor.execute("""
            SELECT setting_value 
            FROM store_settings 
            WHERE setting_key = 'line_message_template'
            LIMIT 1
        """)
        
        template_result = cursor.fetchone()
        cursor.close()
        
        # テンプレートがあれば使用、なければデフォルト
        if template_result and template_result['setting_value']:
            message_template = template_result['setting_value']
        else:
            message_template = """【ピックアップリマインダー】

キャスト: {name}さん
退室時刻: {time}
ホテル: {hotel}

まもなく退室時刻です。
ピックアップの準備をお願いします。"""
        
        # 🔧 変数を置き換え
        message = message_template.replace('{name}', cast_name)
        message = message.replace('{time}', exit_time_str)
        message = message.replace('{hotel}', hotel_name or '未設定')
        
        # LINE送信
        return send_line_message(line_user_id, message)
        
    except Exception as e:
        error_msg = f"スタッフ通知エラー: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }


def send_autocall_result_to_store(cast_name, exit_time_str, call_success, error_message=None):
    """
    店舗にオートコール実行結果を通知
    
    Args:
        cast_name (str): キャスト名
        exit_time_str (str): 退室時刻
        call_success (bool): オートコール成功/失敗
        error_message (str, optional): エラーメッセージ
    
    Returns:
        dict: 送信結果
    """
    try:
        # 店舗用LINE IDとテンプレートを取得
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT setting_key, setting_value 
            FROM store_settings 
            WHERE setting_key IN ('store_line_id', 'store_line_message_template')
        """)
        
        settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
        cursor.close()
        
        # 店舗LINE IDが設定されていない場合はスキップ
        store_line_id = settings.get('store_line_id')
        if not store_line_id:
            print("📝 店舗用LINE IDが未設定のため、通知をスキップしました")
            return {
                'success': True,  # エラーではないのでTrue
                'error': None,
                'skipped': True
            }
        
        # テンプレート取得
        message_template = settings.get('store_line_message_template')
        if not message_template:
            # デフォルトテンプレート
            message_template = """【オートコール{result}】
{name}さんへの発信{result_text}
退室予定: {time}
発信時刻: {call_time}"""
        
        # 変数を準備
        current_time = datetime.now().strftime('%H:%M')
        
        if call_success:
            result = "完了"
            result_text = "完了"
            result_emoji = "✅"
        else:
            result = "失敗"
            result_text = "失敗"
            result_emoji = "❌"
        
        # 変数を置き換え
        message = message_template.replace('{result}', result)
        message = message.replace('{result_text}', result_text)
        message = message.replace('{name}', cast_name)
        message = message.replace('{time}', exit_time_str)
        message = message.replace('{call_time}', current_time)
        
        # エラーメッセージがあれば追加
        if error_message:
            message += f"\n\nエラー詳細: {error_message}"
        
        # 結果の絵文字を先頭に追加
        message = f"{result_emoji} {message}"
        
        # LINE送信
        return send_line_message(store_line_id, message)
        
    except Exception as e:
        error_msg = f"店舗通知エラー: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }


def send_line_flex_message(line_user_id, flex_message):
    """
    LINE Flex Messageを送信（リッチなメッセージ）
    
    Args:
        line_user_id (str): LINE User ID
        flex_message (dict): Flex MessageのJSON
    
    Returns:
        dict: 送信結果
    """
    try:
        # Channel Access Tokenをデータベースから取得
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT setting_value 
            FROM store_settings 
            WHERE setting_key = 'line_channel_access_token'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result or not result['setting_value']:
            return {
                'success': False,
                'error': 'LINE Channel Access Tokenが設定されていません'
            }
        
        access_token = result['setting_value']
        
        # LINE Messaging API エンドポイント
        url = 'https://api.line.me/v2/bot/message/push'
        
        # リクエストヘッダー
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # リクエストボディ
        payload = {
            'to': line_user_id,
            'messages': [flex_message]
        }
        
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ LINE Flex Message送信成功: {line_user_id}")
            return {
                'success': True,
                'error': None
            }
        else:
            error_msg = f"LINE API エラー: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
    except Exception as e:
        error_msg = f"LINE Flex Message送信エラー: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }


def create_pickup_flex_message(cast_name, exit_time_str, hotel_name, hotel_address):
    """
    ピックアップリマインダー用のFlex Messageを作成
    
    Args:
        cast_name (str): キャスト名
        exit_time_str (str): 退室時刻
        hotel_name (str): ホテル名
        hotel_address (str): ホテル住所
    
    Returns:
        dict: Flex Message JSON
    """
    return {
        "type": "flex",
        "altText": f"【ピックアップ】{cast_name}さん {exit_time_str}退室",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🚗 ピックアップリマインダー",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff"
                    }
                ],
                "backgroundColor": "#FF6B6B"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "キャスト",
                                "size": "sm",
                                "color": "#999999",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": f"{cast_name}さん",
                                "size": "md",
                                "weight": "bold",
                                "margin": "md"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "退室時刻",
                                "size": "sm",
                                "color": "#999999",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": exit_time_str,
                                "size": "md",
                                "weight": "bold",
                                "color": "#FF6B6B",
                                "margin": "md"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": hotel_name,
                                "size": "md",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": hotel_address,
                                "size": "xs",
                                "color": "#999999",
                                "wrap": True
                            }
                        ],
                        "margin": "lg"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "⏰ まもなく退室時刻です",
                        "size": "sm",
                        "color": "#999999",
                        "align": "center"
                    }
                ]
            }
        }
    }


# テスト用関数
if __name__ == '__main__':
    print("=== LINE通知テスト ===")
    
    # シンプルなテキストメッセージ
    test_line_id = 'takeru770515'  # テスト用LINE User IDに置き換え
    test_message = "これはテスト通知です。"
    
    result = send_line_message(test_line_id, test_message)
    
    if result['success']:
        print("通知送信成功！")
    else:
        print(f"通知送信失敗: {result['error']}")