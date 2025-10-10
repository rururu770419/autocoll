# routes/line_webhook.py
from flask import Blueprint, request, abort, current_app
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from database.db_connection import get_db_connection

line_webhook_bp = Blueprint('line_webhook', __name__)

def get_line_credentials():
    """
    store_settingsからLINE認証情報を取得
    """
    conn = get_db_connection()
    if not conn:
        return None, None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT setting_key, setting_value 
            FROM store_settings 
            WHERE setting_key IN ('line_channel_access_token', 'line_channel_secret')
        """)
        
        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = row[1]
        
        cursor.close()
        conn.close()
        
        access_token = settings.get('line_channel_access_token', '')
        channel_secret = settings.get('line_channel_secret', '')
        
        return access_token, channel_secret
    except Exception as e:
        current_app.logger.error(f"LINE認証情報取得エラー: {e}")
        if conn:
            conn.close()
        return None, None


@line_webhook_bp.route('/line/webhook', methods=['POST'])
def webhook():
    """
    LINE Webhook エンドポイント
    LINEプラットフォームからのメッセージを受信
    """
    # 署名を取得
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        abort(400, 'Missing X-Line-Signature header')
    
    # リクエストボディを取得
    body = request.get_data(as_text=True)
    current_app.logger.info(f"Request body: {body}")
    
    # LINE認証情報を取得
    access_token, channel_secret = get_line_credentials()
    
    if not access_token or not channel_secret:
        current_app.logger.error("LINE認証情報が設定されていません")
        abort(500, 'LINE credentials not configured')
    
    # LINE Bot API とハンドラーを初期化
    line_bot_api = LineBotApi(access_token)
    handler = WebhookHandler(channel_secret)
    
    # 署名を検証してイベントを処理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        current_app.logger.error("Invalid signature")
        abort(400, 'Invalid signature')
    except LineBotApiError as e:
        current_app.logger.error(f"LINE Bot API error: {e}")
        abort(500, 'LINE Bot API error')
    
    # メッセージイベントのハンドラーを定義
    @handler.add(MessageEvent, message=TextMessage)
    def handle_text_message(event):
        """
        テキストメッセージを処理
        """
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        current_app.logger.info(f"Received message: '{text}' from user: {user_id}")
        
        # 「ID確認」コマンドに対応
        if text in ['ID確認', 'id確認', 'ID', 'id', 'ユーザーID', 'ユーザーid']:
            reply_message = f"あなたのLINE User IDは:\n\n{user_id}\n\nこのIDをコピーして、スタッフ編集画面の「LINE User ID」欄に貼り付けてください。"
            
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_message)
                )
                current_app.logger.info(f"Sent User ID to {user_id}")
            except LineBotApiError as e:
                current_app.logger.error(f"Failed to send message: {e}")
        else:
            # その他のメッセージには簡単な返信
            reply_message = "「ID確認」と送信すると、あなたのLINE User IDを確認できます。"
            
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_message)
                )
            except LineBotApiError as e:
                current_app.logger.error(f"Failed to send message: {e}")
    
    return 'OK', 200


@line_webhook_bp.route('/line/test', methods=['GET'])
def test_endpoint():
    """
    Webhook設定のテスト用エンドポイント
    """
    access_token, channel_secret = get_line_credentials()
    
    if access_token and channel_secret:
        return {
            'status': 'ok',
            'message': 'LINE credentials are configured',
            'access_token_length': len(access_token),
            'channel_secret_length': len(channel_secret)
        }, 200
    else:
        return {
            'status': 'error',
            'message': 'LINE credentials not found'
        }, 500