from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import sys
import os

# database モジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import schedule_db
from database.db_access import get_display_name
from database.connection import get_db, get_store_id  # ← get_store_id を追加

schedule_bp = Blueprint('schedule', __name__)

def register_schedule_routes(app):
    """出勤管理ルートを登録"""
    app.register_blueprint(schedule_bp)

@schedule_bp.route('/<store>/schedule', methods=['GET'])
def cast_schedule(store):
    """出勤表ページを表示（フィルタ＋ページネーション対応）"""
    
    # 店舗情報を取得
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    # ✅ store_id を動的取得
    store_id = get_store_id(store)
    
    # クエリパラメータから開始日を取得（デフォルトは今日）
    date_param = request.args.get('date')
    if date_param:
        start_date = datetime.strptime(date_param, '%Y-%m-%d')
    else:
        # 今日を開始日とする
        start_date = datetime.now()
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    # フィルタパラメータを取得
    active_only = request.args.get('active_only', 'true') == 'true'
    course_category_id = request.args.get('course_category', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # ✅ コースカテゴリ一覧を取得（動的 store_id 使用）
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT category_id, category_name
        FROM course_categories
        WHERE store_id = %s
        AND is_active = TRUE
        ORDER BY category_id
    """, (store_id,))
    course_categories = cursor.fetchall()
    
    # フィルタ対応の週間スケジュールを取得
    schedule_data = schedule_db.get_weekly_schedules_filtered(
        store_id=store_id,
        start_date=start_date_str,
        active_only=active_only,
        course_category_id=course_category_id,
        page=page,
        per_page=per_page
    )
    
    schedules = schedule_data['schedules']
    total_pages = schedule_data['total_pages']
    current_page = schedule_data['current_page']
    total_casts = schedule_data['total_casts']
    
    # 日付リストを生成
    dates = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        dates.append({
            'date': date.strftime('%Y-%m-%d'),
            'display': date.strftime('%m/%d'),
            'weekday': ['(月)', '(火)', '(水)', '(木)', '(金)', '(土)', '(日)'][date.weekday()]
        })
    
    # 前の7日・次の7日のリンク用
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
        current_date=datetime.now().strftime('%Y-%m-%d'),
        # フィルタ用の追加データ
        course_categories=course_categories,
        active_only=active_only,
        selected_course_category=course_category_id,
        current_page=current_page,
        total_pages=total_pages,
        total_casts=total_casts
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
    
    # ✅ store_id を動的取得
    store_id = get_store_id(store)
    
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