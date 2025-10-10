from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import sys
import os

# database モジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import schedule_db
from database.db_access import get_display_name

schedule_bp = Blueprint('schedule', __name__)

def register_schedule_routes(app):
    """出勤管理ルートを登録"""
    app.register_blueprint(schedule_bp)

@schedule_bp.route('/<store>/schedule', methods=['GET'])
def cast_schedule(store):
    """出勤表ページを表示"""
    
    # 店舗情報を取得
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    # 店舗IDをストアコードから推定（既存パターンに合わせる）
    store_id = 1  # nagano=1, tokyo=2 など、必要に応じて調整
    
    # クエリパラメータから開始日を取得（デフォルトは今週の月曜日）
    date_param = request.args.get('date')
    if date_param:
        start_date = datetime.strptime(date_param, '%Y-%m-%d')
    else:
        # 今週の月曜日を取得
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    # 週間スケジュールを取得
    schedules = schedule_db.get_weekly_schedules(store_id, start_date_str)
    
    # 日付リストを生成
    dates = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        dates.append({
            'date': date.strftime('%Y-%m-%d'),
            'display': date.strftime('%m/%d'),
            'weekday': ['(月)', '(火)', '(水)', '(木)', '(金)', '(土)', '(日)'][date.weekday()]
        })
    
    # 前週・次週のリンク用
    prev_week = (start_date - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week = (start_date + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # 時間スロットを取得（06:00〜翌05:30）
    time_slots = schedule_db.get_time_slots(start_hour=6, end_hour=5, interval_minutes=30)
    
    return render_template(
        'cast_schedule.html',
        store=store,
        display_name=display_name,
        schedules=schedules,
        dates=dates,
        prev_week=prev_week,
        next_week=next_week,
        time_slots=time_slots,
        current_date=datetime.now().strftime('%Y-%m-%d')
    )

@schedule_bp.route('/<store>/schedule/get', methods=['GET'])
def get_schedule(store):
    """特定のキャストと日付の出勤情報を取得（Ajax用）"""
    
    cast_id = request.args.get('cast_id', type=int)
    work_date = request.args.get('work_date')
    
    if not cast_id or not work_date:
        return jsonify({'success': False, 'error': '必須パラメータが不足しています'})
    
    schedule = schedule_db.get_schedule_by_cast_date(cast_id, work_date)
    
    return jsonify({
        'success': True,
        'schedule': schedule
    })

@schedule_bp.route('/<store>/schedule/save', methods=['POST'])
def save_schedule(store):
    """出勤情報を保存（Ajax用）"""
    
    # 店舗IDを取得
    store_id = 1  # nagano=1, tokyo=2 など、必要に応じて調整
    
    data = request.get_json()
    cast_id = data.get('cast_id')
    work_date = data.get('work_date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    is_off = data.get('is_off', False)
    note = data.get('note', '')
    
    if not cast_id or not work_date:
        return jsonify({'success': False, 'error': '必須パラメータが不足しています'})
    
    # 休みで登録する場合
    if is_off:
        success = schedule_db.upsert_schedule(
            store_id=store_id,
            cast_id=cast_id,
            work_date=work_date,
            start_time=None,
            end_time=None,
            status='off',
            note=note
        )
    else:
        # 出勤登録の場合
        if not start_time or not end_time:
            return jsonify({'success': False, 'error': '開始時刻と終了時刻を選択してください'})
        
        success = schedule_db.upsert_schedule(
            store_id=store_id,
            cast_id=cast_id,
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            status='confirmed',
            note=note
        )
    
    if success:
        return jsonify({'success': True, 'message': '出勤情報を保存しました'})
    else:
        return jsonify({'success': False, 'error': '保存に失敗しました'})

@schedule_bp.route('/<store>/schedule/delete', methods=['POST'])
def delete_schedule(store):
    """出勤情報を削除（Ajax用）"""
    
    data = request.get_json()
    cast_id = data.get('cast_id')
    work_date = data.get('work_date')
    
    if not cast_id or not work_date:
        return jsonify({'success': False, 'error': '必須パラメータが不足しています'})
    
    success = schedule_db.delete_schedule(cast_id, work_date)
    
    if success:
        return jsonify({'success': True, 'message': '出勤情報を削除しました'})
    else:
        return jsonify({'success': False, 'error': '削除に失敗しました'})