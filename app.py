import sys
import os

# UTF-8を強制（Windows対応）
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from flask import Flask
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

# ★★★ ここを追加 ★★★
# 設定管理ルートの登録
from routes.settings import register_settings_routes
register_settings_routes(app)

# シフト管理ルートの登録
from routes.shift_management import register_shift_management_routes
register_shift_management_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)