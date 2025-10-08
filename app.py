import sys
import os

# UTF-8を強制（Windows対応）
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from flask import Flask, request
from routes.main import main_routes
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['JSON_AS_ASCII'] = False

# 日付フィルターを追加
@app.template_filter('date_prev')
def date_prev_filter(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    prev_date = date_obj - timedelta(days=1)
    return prev_date.strftime('%Y-%m-%d')

@app.template_filter('date_next')
def date_next_filter(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    next_date = date_obj + timedelta(days=1)
    return next_date.strftime('%Y-%m-%d')

# JSONパースフィルター
@app.template_filter('parse_json')
def parse_json_filter(value):
    """JSON文字列をPythonオブジェクトに変換"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@app.route('/<store>/test', methods=['GET'])
def test_route(store):
    return f"Test route working for store: {store}"

# Blueprintの登録
app.register_blueprint(main_routes)

# 設定管理ルートの登録
from routes.settings import register_settings_routes
register_settings_routes(app)

# シフト管理ルートの登録
from routes.shift_management import register_shift_management_routes
register_shift_management_routes(app)

# NG項目管理ルートの登録
from routes.ng_routes import ng_bp
app.register_blueprint(ng_bp)
print("✅ NG項目管理APIを登録しました")

# スケジュール取り込みルートの登録
from routes.schedule_import import schedule_import_bp
app.register_blueprint(schedule_import_bp)
print("✅ スケジュール取り込みAPIを登録しました")

# ===== Twilio音声通話エンドポイント =====
@app.route('/twilio/voice', methods=['GET', 'POST'])
def twilio_voice():
    """
    Twilioからのコールバック用エンドポイント
    キャストへの自動音声メッセージを返す
    """
    from twilio.twiml.voice_response import VoiceResponse
    
    cast_name = request.args.get('cast_name', 'キャスト')
    exit_time = request.args.get('exit_time', '時刻')
    
    response = VoiceResponse()
    
    # 日本語音声メッセージ
    message = f"{cast_name}さん、退室時刻は{exit_time}です。準備をお願いします。"
    
    response.say(
        message,
        language='ja-JP',
        voice='woman'
    )
    
    return str(response), 200, {'Content-Type': 'text/xml'}


# ===== スケジューラー管理エンドポイント（店舗コード対応） =====
@app.route('/<store>/admin/scheduler/status', methods=['GET'])
def scheduler_status(store):
    """スケジューラーの状態を確認（管理者用）"""
    from scheduler import get_scheduler_status
    
    status = get_scheduler_status()
    
    return {
        'store': store,
        'running': status['running'],
        'jobs': status['jobs'],
        'timestamp': datetime.now().isoformat()
    }


@app.route('/<store>/admin/scheduler/restart', methods=['POST'])
def scheduler_restart(store):
    """スケジューラーを再起動（管理者用）"""
    from scheduler import stop_scheduler, start_scheduler
    
    try:
        stop_scheduler()
        start_scheduler()
        return {'success': True, 'message': 'スケジューラーを再起動しました', 'store': store}
    except Exception as e:
        return {'success': False, 'error': str(e), 'store': store}, 500


if __name__ == '__main__':
    print("=" * 50)
    print("ピックアップシステム起動中...")
    print("=" * 50)
    
    # スケジューラーを起動
    from scheduler import start_scheduler
    start_scheduler()
    
    try:
        print("\n🚀 Flaskアプリケーション起動")
        print("   URL: http://0.0.0.0:5001")
        print("   Ctrl+C で停止\n")
        
        # debug=False でスケジューラーの二重起動を防ぐ
        app.run(host='0.0.0.0', port=5001, debug=False)
        
    except (KeyboardInterrupt, SystemExit):
        print("\n\n終了シグナル受信...")
        from scheduler import stop_scheduler
        stop_scheduler()
        print("✅ アプリケーション終了")