# -*- coding: utf-8 -*-
"""
ガントチャート表示用Blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from database.db_connection import get_db_connection
from database.gantt_db import get_gantt_data, get_time_slots, get_store_schedule_settings
from datetime import datetime, timedelta

gantt_bp = Blueprint('gantt', __name__)


@gantt_bp.route('/<store>/gantt')
def gantt_chart(store):
    """
    タイムスケジュール表示ページ
    """
    try:
        # クエリパラメータから日付を取得（デフォルトは今日）
        target_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        
        # データベース接続
        db = get_db_connection()
        
        try:
            # 店舗IDは固定（1）※本来は店舗名から取得
            store_id = 1
            
            # 店舗のスケジュール設定を取得
            schedule_settings = get_store_schedule_settings(db, store_id)
            
            # ガントチャート用データを取得
            gantt_data = get_gantt_data(db, store_id, target_date_str)
            
            # 時間スロットを生成
            # 開始時刻と終了時刻をパース
            start_time_parts = schedule_settings['start_time'].split(':')
            start_hour = int(start_time_parts[0])
            
            end_time_parts = schedule_settings['end_time'].split(':')
            end_hour = int(end_time_parts[0])
            end_minute = int(end_time_parts[1])
            
            # 終了時刻が翌日の場合は24を加算
            if end_hour < start_hour:
                end_hour += 24
            
            time_slots = get_time_slots(
                start_hour=start_hour,
                end_hour=end_hour,
                interval_minutes=schedule_settings['time_unit']
            )
            
            # 前日・翌日の日付を計算
            prev_date = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
            next_date = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # 日付の表示形式
            date_display = target_date.strftime('%Y年%m月%d日（%a）')
            weekday_ja = ['月', '火', '水', '木', '金', '土', '日']
            weekday_index = target_date.weekday()
            date_display = target_date.strftime(f'%Y年%m月%d日（{weekday_ja[weekday_index]}）')
            
            return render_template(
                'gantt_chart.html',
                store=store,
                target_date=target_date_str,
                date_display=date_display,
                prev_date=prev_date,
                next_date=next_date,
                gantt_data=gantt_data,
                time_slots=time_slots,
                schedule_settings=schedule_settings
            )
        
        finally:
            db.close()
    
    except Exception as e:
        print(f"[ERROR] タイムスケジュール表示エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"エラーが発生しました: {str(e)}", 500


@gantt_bp.route('/<store>/gantt/api/data')
def gantt_api_data(store):
    """
    タイムスケジュールデータ取得API（AJAX用）
    """
    try:
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        db = get_db_connection()
        
        try:
            store_id = 1
            gantt_data = get_gantt_data(db, store_id, target_date)
            
            return jsonify({
                'success': True,
                'data': gantt_data
            })
        
        finally:
            db.close()
    
    except Exception as e:
        print(f"[ERROR] タイムスケジュールAPI エラー: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500