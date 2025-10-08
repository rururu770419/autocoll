from flask import render_template, request, session, jsonify
from datetime import datetime, timedelta
from database.db_connection import get_db_connection
from database.db_access import (
    get_display_name, get_db, get_pickup_records_by_date, get_staff_list,
    get_all_casts, get_all_hotels_with_details, update_pickup_record,
    delete_pickup_record, auto_cleanup_if_needed, get_all_courses
)

def store_home(store):
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404
    
    try:
        # URLパラメータから日付を取得（なければ今日）
        target_date = request.args.get('date')
        if target_date:
            try:
                current_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                current_date = datetime.now().date()
        else:
            current_date = datetime.now().date()
        
        # 日付表示用のフォーマット
        current_date_display = format_date_display(current_date)
        
        # 送迎記録とその他のデータを取得
        pickup_records = get_pickup_records_by_date(db, current_date)
        
        # 各レコードに通知情報を追加
        cursor = db.cursor()
        for record in pickup_records:
            if record['type'] == 'pickup' and not record['is_entry'] and record.get('exit_time'):
                # キャストの通知設定とオートコール状態を取得
                cast_id = record.get('cast_id')
                if cast_id:
                    cursor.execute(
                        """
                        SELECT notification_minutes_before 
                        FROM casts 
                        WHERE cast_id = %s
                        """,
                        (cast_id,)
                    )
                    cast_result = cursor.fetchone()
                    
                    if cast_result and cast_result['notification_minutes_before']:
                        # 通知予定時刻を計算
                        notification_time = record['exit_time'] - timedelta(minutes=cast_result['notification_minutes_before'])
                        record['call_scheduled_time'] = notification_time.strftime('%H:%M')
                    else:
                        record['call_scheduled_time'] = '-'
                else:
                    record['call_scheduled_time'] = '-'
                
                # データベースからオートコール状態フラグを取得
                record_id = record.get('record_id')
                
                cursor.execute(
                    """
                    SELECT cast_auto_call_sent, cast_auto_call_disabled
                    FROM pickup_records
                    WHERE record_id = %s
                    """,
                    (record_id,)
                )
                call_flags = cursor.fetchone()
                
                # フラグをrecordに追加
                if call_flags:
                    record['cast_auto_call_sent'] = call_flags['cast_auto_call_sent'] or False
                    record['cast_auto_call_disabled'] = call_flags['cast_auto_call_disabled'] or False
                else:
                    record['cast_auto_call_sent'] = False
                    record['cast_auto_call_disabled'] = False
                
                # 通知状態を設定
                if record['cast_auto_call_disabled']:
                    record['call_status'] = 'disabled'
                elif record['cast_auto_call_sent']:
                    record['call_status'] = 'success'
                else:
                    record['call_status'] = 'pending'
            else:
                record['call_scheduled_time'] = '-'
                record['call_status'] = None
                record['cast_auto_call_sent'] = False
                record['cast_auto_call_disabled'] = False
        
        staff_list = get_staff_list(db)
        casts = get_all_casts(db)
        hotels = get_all_hotels_with_details(db)
        
        # その日のお知らせ情報を取得（修正済み）
        announcement = get_announcement(db, current_date)
        
        success_msg = request.args.get('success')
        error_msg = request.args.get('error')
        
        return render_template(
            "dashboard.html",
            store=store,
            display_name=display_name,
            user_name=session.get('user_name', 'ゲスト'),
            user_role=session.get('user_role', 'なし'),
            pickup_records=pickup_records,
            staff_list=staff_list,
            casts=casts,
            hotels=hotels,
            announcement=announcement,
            current_date=current_date.strftime('%Y-%m-%d'),
            current_date_display=current_date_display,
            success=success_msg,
            error=error_msg
        )
    finally:
        if db:
            db.close()

def format_date_display(date):
    """日付を表示用フォーマットに変換"""
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    month = date.month
    day = date.day
    weekday = weekdays[date.weekday()]
    
    return f"{month}月{day}日（{weekday}）"

def get_announcement(db, target_date):
    """指定日のお知らせ情報を取得"""
    try:
        # PostgreSQL形式に修正
        cursor = db.cursor()
        cursor.execute(
            "SELECT content, is_visible FROM announcements WHERE store_name = %s AND announcement_date = %s LIMIT 1",
            (session.get('store'), target_date)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                'content': row['content'],
                'is_visible': bool(row['is_visible'])
            }
        else:
            return {'content': '', 'is_visible': False}
    except Exception as e:
        print(f"Error in get_announcement: {e}")
        return {'content': '', 'is_visible': False}

def get_record_dates(store):
    """指定された年月の予定がある日付リストを取得"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        year = data.get('year')
        month = data.get('month')
        
        if not year or not month:
            return jsonify({'success': False, 'error': 'yearとmonthが必要です'})
        
        # その月の最初の日と最後の日
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # PostgreSQL形式に修正
        cursor = db.cursor()
        cursor.execute(
            "SELECT DISTINCT DATE(entry_time) as record_date FROM pickup_records WHERE DATE(entry_time) BETWEEN %s AND %s",
            (first_day, last_day)
        )
        
        dates = [row['record_date'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'dates': dates
        })
        
    except Exception as e:
        print(f"Error in get_record_dates: {e}")
        return jsonify({'success': False, 'error': f'データ取得エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def update_record(store):
    """レコード更新エンドポイント"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        field = data.get('field')
        value = data.get('value')
        
        if not record_id or not field:
            return jsonify({'success': False, 'error': 'record_idとfieldが必要です'})
        
        # フィールド名をデータベースカラム名にマッピング
        field_mapping = {
            'entry_time': 'entry_time',
            'exit_time': 'exit_time',
            'cast_id': 'cast_id',
            'hotel_id': 'hotel_id',
            'content': 'content',
            'staff_id': 'staff_id',
            'is_completed': 'is_completed',
            'memo': 'memo',
            'memo_expanded': 'memo_expanded'
        }
        
        db_field = field_mapping.get(field)
        if not db_field:
            return jsonify({'success': False, 'error': f'不正なフィールド: {field}'})
        
        # is_completedとmemo_expandedはbooleanとして処理
        if field in ['is_completed', 'memo_expanded']:
            value = True if value else False
        
        # レコードを更新
        update_pickup_record(db, record_id, db_field, value)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in update_record: {e}")
        return jsonify({'success': False, 'error': f'更新エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def delete_record(store):
    """レコード削除エンドポイント"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        
        if not record_id:
            return jsonify({'success': False, 'error': 'record_idが必要です'})
        
        delete_pickup_record(db, record_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in delete_record: {e}")
        return jsonify({'success': False, 'error': f'削除エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def save_all(store):
    """全変更を保存"""
    return jsonify({'success': True, 'message': '保存は個別に処理されます'})

def dashboard_data(store):
    """ダッシュボードデータ取得API"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        target_date = request.args.get('date', datetime.now().date())
        pickup_records = get_pickup_records_by_date(db, target_date)
        
        return jsonify({
            'success': True,
            'records': [dict(record) for record in pickup_records]
        })
        
    except Exception as e:
        print(f"Error in dashboard_data: {e}")
        return jsonify({'success': False, 'error': f'データ取得エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def check_change_status(store):
    """退室レコードのお釣り登録状況を確認するAPI"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        
        if not record_id:
            return jsonify({'success': False, 'error': 'record_idが必要です'})
        
        # デバッグ用
        print(f"DEBUG check_change_status: record_id = {record_id}, type = {type(record_id)}")
        
        # PostgreSQL形式に修正（%sプレースホルダー）
        cursor = db.cursor()
        cursor.execute(
            "SELECT p.record_id, p.is_entry, p.cast_id, p.exit_time FROM pickup_records p WHERE p.record_id = %s",
            (record_id,)
        )
        
        record = cursor.fetchone()
        if not record:
            return jsonify({'success': False, 'error': 'レコードが見つかりません'})
        
        # 入室レコードの場合はお釣り確認不要
        if record['is_entry']:
            return jsonify({
                'success': True, 
                'is_exit': False,
                'has_change': False
            })
        
        # cast_idまたはexit_timeがNULLの場合はお釣り未登録として扱う
        if not record['cast_id'] or not record['exit_time']:
            return jsonify({
                'success': True,
                'is_exit': True,
                'has_change': False
            })
        
        # お釣り登録状況をチェック（PostgreSQL形式）
        # money_recordsテーブルにmoney_typeカラムがないため、record_idで判定
        cursor.execute(
            "SELECT COUNT(*) as count FROM money_records WHERE record_id = %s AND cast_id = %s",
            (record_id, record['cast_id'])
        )
        
        money_result = cursor.fetchone()
        money_count = money_result['count'] if money_result else 0
        
        print(f"DEBUG: record_id={record_id}, cast_id={record['cast_id']}, money_count={money_count}")
        
        return jsonify({
            'success': True,
            'is_exit': True,
            'has_change': money_count > 0
        })
        
    except Exception as e:
        print(f"Error in check_change_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'確認エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def check_change_registration(store):
    """お釣り登録済みかチェックするAPI"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        cast_id = data.get('cast_id')
        exit_time = data.get('exit_time')
        
        if not cast_id or not exit_time:
            return jsonify({'success': False, 'error': 'cast_idとexit_timeが必要です'})
        
        # 今日の日付
        today = datetime.now().date()
        
        # デバッグ用
        print(f"DEBUG check_change_registration: cast_id={cast_id}, exit_time={exit_time}, today={today}")
        
        # PostgreSQL形式に修正
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM money_records WHERE cast_id = %s AND exit_time = %s AND created_date = %s",
            (cast_id, exit_time, today)
        )
        
        money_result = cursor.fetchone()
        money_count = money_result['count'] if money_result else 0
        
        print(f"DEBUG: money_count = {money_count}")
        
        return jsonify({
            'success': True,
            'already_registered': money_count > 0
        })
        
    except Exception as e:
        print(f"Error in check_change_registration: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'チェックエラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def update_announcement_endpoint(store):
    """お知らせ更新エンドポイント"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        date = data.get('date')
        
        if not field or date is None:
            return jsonify({'success': False, 'error': 'fieldとdateが必要です'})
        
        # PostgreSQL形式に修正
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM announcements WHERE store_name = %s AND announcement_date = %s",
            (store, date)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 更新
            if field == 'content':
                cursor.execute(
                    "UPDATE announcements SET content = %s WHERE store_name = %s AND announcement_date = %s",
                    (value, store, date)
                )
            elif field == 'is_visible':
                cursor.execute(
                    "UPDATE announcements SET is_visible = %s WHERE store_name = %s AND announcement_date = %s",
                    (True if value else False, store, date)
                )
        else:
            # 新規作成
            if field == 'content':
                cursor.execute(
                    "INSERT INTO announcements (store_name, announcement_date, content, is_visible) VALUES (%s, %s, %s, FALSE)",
                    (store, date, value)
                )
            elif field == 'is_visible':
                cursor.execute(
                    "INSERT INTO announcements (store_name, announcement_date, content, is_visible) VALUES (%s, %s, '', %s)",
                    (store, date, True if value else False)
                )
        
        db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in update_announcement_endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'更新エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def get_course_data(store):
    """コース情報を取得するAPI"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        courses = get_all_courses(db)
        
        # デバッグ用: 最初のコースのキーを確認
        if courses:
            print(f"DEBUG get_course_data: First course keys = {list(courses[0].keys())}")
            print(f"DEBUG get_course_data: First course data = {dict(courses[0])}")
        
        # psycopg.Rowオブジェクトを辞書に変換
        courses_dict = []
        for course in courses:
            # 正確なカラム名: time_minutes
            time_value = course.get('time_minutes', 60)
            
            course_dict = {
                'course_id': course['course_id'],
                'name': course['name'],
                'time': time_value,
                'price': course.get('price', 0)
            }
            courses_dict.append(course_dict)
        
        print(f"DEBUG: Returning {len(courses_dict)} courses")
        
        return jsonify({
            'success': True,
            'courses': courses_dict
        })
        
    except Exception as e:
        print(f"Error in get_course_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'データ取得エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()