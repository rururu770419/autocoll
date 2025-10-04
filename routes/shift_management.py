from flask import render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database.shift_db import (
    get_all_shift_types,
    get_shifts_by_month,
    upsert_shift,
    get_working_staff_by_date,
    get_date_memos_by_month,
    upsert_date_memo
)


# 管理者権限チェック用デコレーター
def admin_required(f):
    """管理者のみアクセス可能"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        return f(*args, **kwargs)
    return decorated_function


def register_shift_management_routes(app):
    """シフト管理のルートを登録"""
    
    @app.route('/<store>/shift_management')
    @admin_required
    def shift_management(store):
        """シフト管理ページを表示"""
        try:
            return render_template('shift_management.html', store=store)
            
        except Exception as e:
            print(f"Error in shift_management: {e}")
            return redirect(url_for('main_routes.store_home', store=store))
    
    
    @app.route('/<store>/shift_management/get_shifts')
    @admin_required
    def get_shifts(store):
        """シフトデータを取得（月単位）"""
        try:
            # クエリパラメータから年月を取得
            year = request.args.get('year', type=int)
            month = request.args.get('month', type=int)
            
            if not year or not month:
                return jsonify({
                    'success': False,
                    'message': '年月を指定してください'
                }), 400
            
            # シフトデータを取得
            shifts_raw = get_shifts_by_month(year, month)
            
            # 日付・時間をISO形式に変換
            shifts = []
            for shift in shifts_raw:
                shift_dict = dict(shift)
                if 'shift_date' in shift_dict and shift_dict['shift_date']:
                    shift_dict['shift_date'] = shift_dict['shift_date'].isoformat()
                if 'start_time' in shift_dict and shift_dict['start_time']:
                    shift_dict['start_time'] = str(shift_dict['start_time'])
                if 'end_time' in shift_dict and shift_dict['end_time']:
                    shift_dict['end_time'] = str(shift_dict['end_time'])
                shifts.append(shift_dict)
            
            # スタッフ一覧を取得（database/user_db.pyから直接取得）
            from database.connection import get_db
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT login_id, name, role, is_active
                FROM users
                WHERE is_active = TRUE
                ORDER BY name
            """)
            all_users = cursor.fetchall()
            
            staff_list = [
                {
                    'staff_id': user['login_id'],
                    'staff_name': user['name'],
                    'user_role': user['role']
                }
                for user in all_users
            ]
            
            # シフト種別を取得
            shift_types = get_all_shift_types()
            
            # 日付別備考を取得
            date_memos_raw = get_date_memos_by_month(year, month)
            date_memos = {}
            for memo in date_memos_raw:
                date_key = memo['memo_date'].isoformat()
                date_memos[date_key] = memo['memo_text']
            
            return jsonify({
                'success': True,
                'shifts': shifts,
                'staff_list': staff_list,
                'shift_types': shift_types,
                'date_memos': date_memos
            })
            
        except Exception as e:
            print(f"Error in get_shifts: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'シフトデータの取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/shift_management/save_shift', methods=['POST'])
    @admin_required
    def save_shift(store):
        """シフトを保存（新規作成 or 更新）"""
        try:
            data = request.get_json()
            
            # デバッグ用: 受信データを出力
            print("=== 受信データ ===")
            print(f"data: {data}")
            
            staff_id = data.get('staff_id')
            shift_date = data.get('shift_date')
            shift_type_id = data.get('shift_type_id')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            memo = data.get('memo', '')
            parking_id = data.get('parking_id')
            
            print(f"staff_id: {staff_id}")
            print(f"shift_date: {shift_date}")
            print(f"shift_type_id: {shift_type_id}")
            print("==================")
            
            # バリデーション
            if not staff_id or staff_id == 0 or not shift_date or not shift_type_id:
                print(f"バリデーションエラー: staff_id={staff_id}, shift_date={shift_date}, shift_type_id={shift_type_id}")
                return jsonify({
                    'success': False,
                    'message': '必須項目を入力してください（スタッフを選択してください）'
                }), 400
            
            # 日付フォーマットの変換（YYYY-MM-DD）
            from datetime import datetime
            try:
                shift_date_obj = datetime.strptime(shift_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '日付形式が正しくありません'
                }), 400
            
            # upsert_shiftを使用（新規作成 or 更新を自動判定）
            success = upsert_shift(
                staff_id=staff_id,
                shift_date=shift_date_obj,
                shift_type_id=shift_type_id,
                start_time=start_time if start_time else None,
                end_time=end_time if end_time else None,
                parking_id=parking_id if parking_id else None,
                memo=memo
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'シフトを保存しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'シフトの保存に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in save_shift: {e}")
            return jsonify({
                'success': False,
                'message': 'シフトの保存に失敗しました'
            }), 500
    
    
    @app.route('/<store>/shift_management/delete_shift', methods=['POST'])
    @admin_required
    def delete_shift_route(store):
        """シフトを削除"""
        try:
            from database.shift_db import delete_shift
            
            data = request.get_json()
            staff_id = data.get('staff_id')
            shift_date = data.get('shift_date')
            
            if not staff_id or not shift_date:
                return jsonify({
                    'success': False,
                    'message': 'スタッフIDと日付が必要です'
                }), 400
            
            # 日付フォーマットの変換
            from datetime import datetime
            try:
                shift_date_obj = datetime.strptime(shift_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '日付形式が正しくありません'
                }), 400
            
            # delete_shiftは (staff_id, shift_date) を引数に取る
            success = delete_shift(staff_id, shift_date_obj)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'シフトを削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'シフトの削除に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_shift_route: {e}")
            return jsonify({
                'success': False,
                'message': 'シフトの削除に失敗しました'
            }), 500
    
    
    @app.route('/<store>/shift_management/get_working_staff')
    @admin_required
    def get_working_staff_route(store):
        """指定日の出勤スタッフを取得（駐車場割り当て用）"""
        try:
            # クエリパラメータから日付を取得
            target_date = request.args.get('date')
            
            if not target_date:
                return jsonify({
                    'success': False,
                    'message': '日付を指定してください'
                }), 400
            
            # 日付フォーマットの変換
            from datetime import datetime
            try:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '日付形式が正しくありません'
                }), 400
            
            # 出勤スタッフを取得
            working_staff_raw = get_working_staff_by_date(date_obj)
            
            # dictに変換
            working_staff = [dict(row) for row in working_staff_raw]
            
            return jsonify({
                'success': True,
                'working_staff': working_staff
            })
            
        except Exception as e:
            print(f"Error in get_working_staff_route: {e}")
            return jsonify({
                'success': False,
                'message': '出勤スタッフの取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/shift_management/save_date_memo', methods=['POST'])
    @admin_required
    def save_date_memo(store):
        """日付別備考を保存"""
        try:
            data = request.get_json()
            
            memo_date = data.get('date')
            memo_text = data.get('memo', '')
            
            if not memo_date:
                return jsonify({
                    'success': False,
                    'message': '日付が必要です'
                }), 400
            
            # 日付フォーマットの変換
            from datetime import datetime
            try:
                date_obj = datetime.strptime(memo_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '日付形式が正しくありません'
                }), 400
            
            # 備考を保存
            success = upsert_date_memo(date_obj, memo_text)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '備考を保存しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '備考の保存に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in save_date_memo: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '備考の保存に失敗しました'
            }), 500