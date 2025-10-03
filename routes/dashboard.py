from flask import render_template, request, session, jsonify
from datetime import datetime, timedelta
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
        # 自動クリーンアップをチェック
        auto_cleanup_if_needed(db)
        
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
        cursor = db.execute("""
            SELECT content, is_visible 
            FROM announcements 
            WHERE store_name = %s AND announcement_date = %s
            LIMIT 1
        """, (session.get('store'), target_date))
        
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
            return jsonify({'success': False, 'error': 'year と month が必要です'})
        
        # 指定された月の日付範囲を取得
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # その月に予定があるすべての日付を取得
        cursor = db.execute("""
            SELECT DISTINCT DATE(created_date) as record_date
            FROM pickup_records 
            WHERE DATE(created_date) BETWEEN %s AND %s
            ORDER BY record_date
        """, (start_date, end_date))
        
        dates = [row['record_date'] for row in cursor.fetchall()]
        
        return jsonify({'success': True, 'dates': dates})
        
    except Exception as e:
        print(f"Error in get_record_dates: {e}")
        return jsonify({'success': False, 'error': f'日付取得エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()

def update_record(store):
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        field = data.get('field')
        value = data.get('value')
        
        success = update_pickup_record(db, record_id, field, value)
        
        return jsonify({'success': success})
    finally:
        if db:
            db.close()

def delete_record(store):
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        
        success = delete_pickup_record(db, record_id)
        
        return jsonify({'success': success})
    finally:
        if db:
            db.close()

def save_all(store):
    # 実際には特に何もしない（リアルタイム更新しているため）
    # ユーザーに保存完了の確認を与えるためのエンドポイント
    return jsonify({'success': True, 'message': '更新できました'})

def dashboard_data(store):
    """ダッシュボードの最新データを取得するAPI"""
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        # URLパラメータから日付を取得
        target_date = request.args.get('date')
        if target_date:
            try:
                current_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                current_date = datetime.now().date()
        else:
            current_date = datetime.now().date()
        
        # 最新データを取得
        pickup_records = get_pickup_records_by_date(db, current_date)
        staff_list = get_staff_list(db)
        casts = get_all_casts(db)
        hotels = get_all_hotels_with_details(db)
        
        # sqlite3.Rowオブジェクトを辞書に変換
        pickup_records_dict = []
        for record in pickup_records:
            record_dict = {
                'record_id': record.record_id,
                'type': record.type,
                'cast_id': record.cast_id,
                'hotel_id': record.hotel_id,
                'course_id': record.course_id,
                'staff_id': record.staff_id,
                'entry_time': record.entry_time,
                'exit_time': record.exit_time,
                'content': record.content,
                'is_entry': record.is_entry,
                'is_completed': record.is_completed,
                'memo': record.memo,
                'memo_expanded': record.memo_expanded,
                'nomination_type': record.nomination_type,
                'cast_name': record.cast_name,
                'hotel_name': record.hotel_name,
                'staff_name': record.staff_name,
                'staff_color': record.staff_color
            }
            pickup_records_dict.append(record_dict)
        
        staff_list_dict = []
        for staff in staff_list:
            staff_dict = {
                'login_id': staff.login_id,
                'name': staff.name,
                'color': staff.color
            }
            staff_list_dict.append(staff_dict)
        
        casts_dict = []
        for cast in casts:
            cast_dict = {
                'cast_id': cast.cast_id,
                'name': cast.name,
                'phone_number': cast.phone_number
            }
            casts_dict.append(cast_dict)
        
        hotels_dict = []
        for hotel in hotels:
            hotel_dict = {
                'hotel_id': hotel.hotel_id,
                'hotel_name': hotel.hotel_name,
                'category_id': hotel.category_id,
                'area_id': hotel.area_id,
                'category_name': hotel.category_name,
                'area_name': hotel.area_name
            }
            hotels_dict.append(hotel_dict)
        
        return jsonify({
            'success': True,
            'pickup_records': pickup_records_dict,
            'staff_list': staff_list_dict,
            'casts': casts_dict,
            'hotels': hotels_dict
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
        
        # レコード情報を取得
        cursor = db.execute("""
            SELECT p.record_id, p.is_entry, p.cast_id, p.exit_time
            FROM pickup_records p
            WHERE p.record_id = %s
        """, (record_id,))
        
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
        
        # お釣り登録状況をチェック
        cursor = db.execute("""
            SELECT COUNT(*) as count
            FROM money_records m
            WHERE m.cast_id = %s AND m.exit_time = %s AND m.created_date = date('now', 'localtime')
        """, (record['cast_id'], record['exit_time']))
        
        money_count = cursor.fetchone()['count']
        
        return jsonify({
            'success': True,
            'is_exit': True,
            'has_change': money_count > 0
        })
        
    except Exception as e:
        print(f"Error in check_change_status: {e}")
        return jsonify({'success': False, 'error': f'確認エラー: {str(e)}'})
    
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
        target_date = data.get('date')  # 日付を受け取る
        
        if field not in ['content', 'is_visible']:
            return jsonify({'success': False, 'error': '無効なフィールドです'})
        
        if not target_date:
            return jsonify({'success': False, 'error': '日付が指定されていません'})
        
        # その日のお知らせレコードが存在するかチェック
        cursor = db.execute("""
            SELECT COUNT(*) as count FROM announcements 
            WHERE store_name = %s AND announcement_date = %s
        """, (store, target_date))
        
        count = cursor.fetchone()['count']
        
        if count == 0:
            # レコードが存在しない場合は作成
            db.execute("""
                INSERT INTO announcements (store_name, announcement_date, content, is_visible) 
                VALUES (%s, %s, '', 0)
            """, (store, target_date))
        
        # フィールドを更新
        if field == 'content':
            db.execute("""
                UPDATE announcements 
                SET content = %s 
                WHERE store_name = %s AND announcement_date = %s
            """, (value, store, target_date))
        elif field == 'is_visible':
            db.execute("""
                UPDATE announcements 
                SET is_visible = %s 
                WHERE store_name = %s AND announcement_date = %s
            """, (1 if value else 0, store, target_date))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in update_announcement: {e}")
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
        
        # sqlite3.Rowオブジェクトを辞書に変換
        courses_dict = []
        for course in courses:
            course_dict = {
                'course_id': course['course_id'],
                'name': course['name'],
                'time': course['time']
            }
            courses_dict.append(course_dict)
        
        return jsonify({
            'success': True,
            'courses': courses_dict
        })
        
    except Exception as e:
        print(f"Error in get_course_data: {e}")
        return jsonify({'success': False, 'error': f'データ取得エラー: {str(e)}'})
    
    finally:
        if db:
            db.close()