from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, jsonify
from database.db_access import (
    get_display_name, get_db, get_all_casts, get_all_users,
    register_money_record, get_money_records_by_date, delete_money_record_by_id,
    cleanup_old_money_records
)

def money_management(store):
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404

    try:
        # 古いデータを自動削除
        cleanup_old_money_records(db)

        # 日付の処理
        selected_date = request.args.get('date')
        if not selected_date:
            selected_date = datetime.now().strftime('%Y-%m-%d')

        if request.method == "POST":
            cast_id = request.form.get("cast_id")
            exit_time = request.form.get("exit_time")
            received_amount = request.form.get("received_amount")
            change_amount = request.form.get("change_amount")
            payment_method = request.form.get("payment_method")
            staff_id = request.form.get("staff_id")

            if not all([cast_id, exit_time, received_amount, change_amount, payment_method, staff_id]):
                casts = get_all_casts(db)
                staff = get_all_users(db)
                records = get_money_records_by_date(db, selected_date)
                cast_totals = {}
                current_staff_id = session.get('login_id', '')
                return render_template(
                    "money_management.html",
                    store=store, display_name=display_name,
                    casts=casts, staff=staff, records=records,
                    cast_totals=cast_totals, selected_date=selected_date,
                    current_staff_id=current_staff_id,
                    error="全ての項目を入力してください。"
                )

            try:
                received_amount = int(received_amount)
                change_amount = int(change_amount)
                cast_id = int(cast_id)
            except ValueError:
                casts = get_all_casts(db)
                staff = get_all_users(db)
                records = get_money_records_by_date(db, selected_date)
                cast_totals = {}
                current_staff_id = session.get('login_id', '')
                return render_template(
                    "money_management.html",
                    store=store, display_name=display_name,
                    casts=casts, staff=staff, records=records,
                    cast_totals=cast_totals, selected_date=selected_date,
                    current_staff_id=current_staff_id,
                    error="金額は数値で入力してください。"
                )

            success = register_money_record(
                db, cast_id, exit_time, received_amount, 
                change_amount, payment_method, staff_id
            )

            if success:
                return redirect(url_for('main_routes.money_management', store=store, date=selected_date, success="記録を追加しました。"))
            else:
                casts = get_all_casts(db)
                staff = get_all_users(db)
                records = get_money_records_by_date(db, selected_date)
                cast_totals = create_cast_totals(records)
                current_staff_id = session.get('login_id', '')
                return render_template(
                    "money_management.html",
                    store=store, display_name=display_name,
                    casts=casts, staff=staff, records=records,
                    cast_totals=cast_totals, selected_date=selected_date,
                    current_staff_id=current_staff_id,
                    error="登録中にエラーが発生しました。"
                )

        # GETリクエストの場合
        casts = get_all_casts(db)
        staff = get_all_users(db)
        records = get_money_records_by_date(db, selected_date)
        
        # キャスト別集計を作成
        cast_totals = create_cast_totals(records)

        current_staff_id = session.get('login_id', '')
        success_msg = request.args.get('success')
        error_msg = request.args.get('error')

        return render_template(
            "money_management.html",
            store=store, display_name=display_name,
            casts=casts, staff=staff, records=records,
            cast_totals=cast_totals, selected_date=selected_date, 
            current_staff_id=current_staff_id,
            success=success_msg, error=error_msg
        )
    
    finally:
        # データベース接続を確実に閉じる
        if db:
            db.close()

def create_cast_totals(records):
    """キャスト別集計を作成する関数"""
    cast_totals = {}
    for record in records:
        try:
            # recordがsqlite3.Rowかdictかを判定してアクセス
            if hasattr(record, 'cast_name'):
                cast_name = record.cast_name
                received_amount = record.received_amount
                change_amount = record.change_amount
            else:
                cast_name = record['cast_name']
                received_amount = record['received_amount']
                change_amount = record['change_amount']
            
            if cast_name not in cast_totals:
                cast_totals[cast_name] = {
                    'received_total': 0,
                    'change_total': 0,
                    'sales_total': 0
                }
            cast_totals[cast_name]['received_total'] += received_amount
            cast_totals[cast_name]['change_total'] += change_amount
            cast_totals[cast_name]['sales_total'] += (received_amount - change_amount)
        except Exception as e:
            print(f"Error processing record: {e}")
            print(f"Record type: {type(record)}")
            print(f"Record content: {record}")
            continue
    
    return cast_totals

def delete_money_record(store, record_id):
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404
    
    try:
        selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        success = delete_money_record_by_id(db, record_id)
        
        if success:
            return redirect(url_for('main_routes.money_management', store=store, date=selected_date, success="記録を削除しました。"))
        else:
            return redirect(url_for('main_routes.money_management', store=store, date=selected_date, error="削除中にエラーが発生しました。"))
    finally:
        # データベース接続を確実に閉じる
        if db:
            db.close()

def register_change(store):
    """ダッシュボードからのお釣り登録API"""
    if request.method != 'POST':
        return jsonify({'success': False, 'error': 'POSTメソッドが必要です'})
    
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        # JSONデータを取得
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'JSONデータが無効です'})
        
        # 必要なフィールドを取得
        cast_id = data.get('cast_id')
        exit_time = data.get('exit_time')
        received_amount = data.get('received_amount')
        change_amount = data.get('change_amount')
        payment_method = data.get('payment_method')
        staff_id = data.get('staff_id')
        
        # バリデーション
        if not all([cast_id, exit_time, received_amount, change_amount, payment_method, staff_id]):
            return jsonify({'success': False, 'error': '必要な項目が不足しています'})
        
        try:
            cast_id = int(cast_id)
            received_amount = int(received_amount)
            change_amount = int(change_amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '数値が無効です'})
        
        # 金銭記録を登録
        success = register_money_record(
            db, cast_id, exit_time, received_amount, 
            change_amount, payment_method, staff_id
        )
        
        if success:
            return jsonify({'success': True, 'message': 'お釣り登録が完了しました'})
        else:
            return jsonify({'success': False, 'error': '登録中にエラーが発生しました'})
            
    except Exception as e:
        print(f"Error in register_change: {e}")
        return jsonify({'success': False, 'error': f'サーバーエラー: {str(e)}'})
    
    finally:
        # データベース接続を確実に閉じる
        if db:
            db.close()

def check_change_registration(store):
    """お釣り登録済みかどうかをチェックするAPI"""
    if request.method != 'POST':
        return jsonify({'success': False, 'error': 'POSTメソッドが必要です'})
    
    db = get_db(store)
    if db is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'JSONデータが無効です'})
        
        cast_id = data.get('cast_id')
        exit_time = data.get('exit_time')
        
        if not cast_id or not exit_time:
            return jsonify({'success': False, 'error': 'キャストIDと退室時間が必要です'})
        
        # 同じキャストの同じ退室時間で今日のお釣り記録があるかチェック
        cursor = db.execute("""
            SELECT COUNT(*) as count
            FROM money_records 
            WHERE cast_id = ? AND exit_time = ? AND created_date = date('now', 'localtime')
        """, (cast_id, exit_time))
        
        result = cursor.fetchone()
        already_registered = result['count'] > 0
        
        return jsonify({
            'success': True,
            'already_registered': already_registered
        })
        
    except Exception as e:
        print(f"Error in check_change_registration: {e}")
        return jsonify({'success': False, 'error': f'チェックエラー: {str(e)}'})
    
    finally:
        if db:
            db.close()