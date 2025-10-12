# -*- coding: utf-8 -*-
"""
ガントチャート表示用Blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from database.connection import get_connection, get_store_id
from database.gantt_db import get_gantt_data, get_time_slots, get_store_schedule_settings, update_reservation_room_number
from datetime import datetime, timedelta

gantt_bp = Blueprint('gantt', __name__)


@gantt_bp.route('/<store>/gantt')
def gantt_chart(store):
    """
    タイムスケジュール表示ページ
    """
    try:
        target_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        
        db = get_connection()
        
        try:
            store_id = get_store_id(store)
            
            schedule_settings = get_store_schedule_settings(db, store_id)
            
            gantt_data = get_gantt_data(db, store_id, target_date_str)
            
            start_time_parts = schedule_settings['start_time'].split(':')
            start_hour = int(start_time_parts[0])
            
            end_time_parts = schedule_settings['end_time'].split(':')
            end_hour = int(end_time_parts[0])
            end_minute = int(end_time_parts[1])
            
            if end_hour < start_hour:
                end_hour += 24
            
            time_slots = get_time_slots(
                start_hour=start_hour,
                end_hour=end_hour,
                interval_minutes=schedule_settings['time_unit']
            )
            
            prev_date = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
            next_date = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
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
        
        db = get_connection()
        
        try:
            store_id = get_store_id(store)
            gantt_data = get_gantt_data(db, store_id, target_date)
            
            return jsonify({
                'success': True,
                'data': gantt_data
            })
        
        finally:
            db.close()
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gantt_bp.route('/<store>/gantt/api/update_room_number', methods=['POST'])
def update_room_number(store):
    """
    予約の部屋番号を更新するAPI
    """
    try:
        data = request.get_json()
        reservation_id = data.get('reservation_id')
        room_number = data.get('room_number', '').strip()
        
        if not reservation_id:
            return jsonify({
                'success': False,
                'error': '予約IDが指定されていません'
            }), 400
        
        db = get_connection()
        
        try:
            store_id = get_store_id(store)
            
            success = update_reservation_room_number(
                db=db,
                reservation_id=reservation_id,
                room_number=room_number if room_number else None
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '部屋番号を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '更新に失敗しました'
                }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500