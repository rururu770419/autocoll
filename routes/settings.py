from flask import render_template, request, jsonify, session, flash, redirect, url_for
from functools import wraps
from database.settings_db import (
    get_all_settings,
    get_setting,
    update_setting,
    bulk_update_settings,
    get_twilio_config
)
from database.parking_db import (
    get_all_parking_lots,
    get_parking_lot,
    create_parking_lot,
    update_parking_lot,
    delete_parking_lot,
    get_parking_enabled
)
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# 管理者権限チェック用デコレーター
def admin_required(f):
    """管理者のみアクセス可能"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ログインチェック（user_name または user_id の存在確認）
        if 'user_name' not in session:  # ← これに変更
            store = kwargs.get('store')
            return redirect(f'/{store}/login')
        
        return f(*args, **kwargs)
    return decorated_function


def register_settings_routes(app):
    """設定管理のルートを登録"""
    
    @app.route('/<store>/settings')
    @admin_required
    def settings(store):
        
        try:
            # 全設定を取得
            settings_data = get_all_settings()
            
            return render_template(
                'settings.html',
                store=store,
                store_info=settings_data['store_info'],
                notification=settings_data['notification'],
                auto_call=settings_data['auto_call']
            )
            
        except Exception as e:
            print(f"Error in settings route: {e}")
            flash('設定の読み込みに失敗しました', 'error')
            return redirect(url_for('main_routes.store_home', store=store))
    
    
    @app.route('/<store>/settings/save', methods=['POST'])
    @admin_required
    def save_settings(store):
        """設定を保存"""
        try:
            # POSTデータを取得
            settings_dict = {}
            
            # フォームから送られてきた全データを取得
            for key in request.form:
                settings_dict[key] = request.form[key]
            
            # チェックボックスの処理（チェックOFFの場合はPOSTデータに含まれない）
            checkbox_keys = ['auto_call_enabled', 'line_notify_enabled', 'parking_enabled']
            for checkbox_key in checkbox_keys:
                if checkbox_key not in settings_dict:
                    settings_dict[checkbox_key] = 'false'
            
            # 更新者を記録
            updated_by = session.get('user', {}).get('login_id', 'unknown')
            
            # 一括更新
            success_count, error_count = bulk_update_settings(settings_dict, updated_by)
            
            if error_count > 0:
                return jsonify({
                    'success': False,
                    'message': f'一部の設定の保存に失敗しました（成功: {success_count}件、失敗: {error_count}件）'
                }), 500
            
            return jsonify({
                'success': True,
                'message': '設定を保存しました'
            })
            
        except Exception as e:
            print(f"Error in save_settings: {e}")
            return jsonify({
                'success': False,
                'message': '設定の保存に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/test_call', methods=['POST'])
    @admin_required
    def test_call(store):
        """テスト発信"""
        try:
            # テスト用電話番号を取得
            data = request.get_json()
            test_phone = data.get('phone_number')
            
            if not test_phone:
                return jsonify({
                    'success': False,
                    'message': '電話番号を入力してください'
                }), 400
            
            # 電話番号のフォーマットチェック（簡易）
            test_phone = test_phone.replace('-', '').replace(' ', '')
            if not test_phone.startswith('+'):
                # 日本の番号の場合、+81に変換
                if test_phone.startswith('0'):
                    test_phone = '+81' + test_phone[1:]
                else:
                    return jsonify({
                        'success': False,
                        'message': '電話番号の形式が正しくありません'
                    }), 400
            
            # Twilio設定を取得
            twilio_config = get_twilio_config()
            
            if not twilio_config['account_sid'] or not twilio_config['auth_token']:
                return jsonify({
                    'success': False,
                    'message': 'Twilio設定が完了していません'
                }), 400
            
            # Twilioクライアント作成
            client = Client(
                twilio_config['account_sid'],
                twilio_config['auth_token']
            )
            
            # メッセージテンプレートを取得
            message_template = get_setting('call_message_template') or 'これはテスト通話です。'
            message = message_template.replace('{name}', 'テスト')
            
            # 通話時間を取得
            timeout_seconds = int(get_setting('call_timeout_seconds') or '15')
            
            # テスト発信
            call = client.calls.create(
                to=test_phone,
                from_=twilio_config['phone_number'],
                twiml=f'<Response><Say language="ja-JP">{message}</Say></Response>',
                timeout=timeout_seconds
            )
            
            return jsonify({
                'success': True,
                'message': f'テスト発信しました（通話ID: {call.sid}）',
                'call_sid': call.sid
            })
            
        except Exception as e:
            print(f"Error in test_call: {e}")
            return jsonify({
                'success': False,
                'message': f'発信に失敗しました: {str(e)}'
            }), 500
    
    
    @app.route('/<store>/settings/get/<key>')
    @admin_required
    def get_setting_value(store, key):
        """特定の設定値を取得（AJAX用）"""
        try:
            value = get_setting(key)
            return jsonify({
                'success': True,
                'value': value
            })
        except Exception as e:
            print(f"Error in get_setting_value: {e}")
            return jsonify({
                'success': False,
                'message': '設定の取得に失敗しました'
            }), 500
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 駐車場管理エンドポイント
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/settings/parking')
    @admin_required
    def parking_settings(store):
        """駐車場設定ページ"""
        try:
            parking_lots = get_all_parking_lots()
            parking_enabled = get_parking_enabled()
            
            return jsonify({
                'success': True,
                'parking_lots': parking_lots,
                'parking_enabled': parking_enabled
            })
            
        except Exception as e:
            print(f"Error in parking_settings: {e}")
            return jsonify({
                'success': False,
                'message': '駐車場情報の取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/parking/create', methods=['POST'])
    @admin_required
    def create_parking(store):
        """駐車場を新規作成"""
        try:
            data = request.get_json()
            parking_name = data.get('parking_name')
            
            if not parking_name:
                return jsonify({
                    'success': False,
                    'message': '駐車場名を入力してください'
                }), 400
            
            # 表示順序を取得（最後に追加）
            existing_lots = get_all_parking_lots()
            display_order = len(existing_lots)
            
            parking_id = create_parking_lot(parking_name, display_order)
            
            if parking_id:
                return jsonify({
                    'success': True,
                    'message': '駐車場を追加しました',
                    'parking_id': parking_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '駐車場の追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_parking: {e}")
            return jsonify({
                'success': False,
                'message': '駐車場の追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/parking/<int:parking_id>', methods=['PUT'])
    @admin_required
    def update_parking(store, parking_id):
        """駐車場を更新"""
        try:
            data = request.get_json()
            parking_name = data.get('parking_name')
            
            if not parking_name:
                return jsonify({
                    'success': False,
                    'message': '駐車場名を入力してください'
                }), 400
            
            success = update_parking_lot(parking_id, parking_name=parking_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '駐車場を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '駐車場の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_parking: {e}")
            return jsonify({
                'success': False,
                'message': '駐車場の更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/parking/<int:parking_id>', methods=['DELETE'])
    @admin_required
    def delete_parking(store, parking_id):
        """駐車場を削除"""
        try:
            success = delete_parking_lot(parking_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '駐車場を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '駐車場の削除に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_parking: {e}")
            return jsonify({
                'success': False,
                'message': '駐車場の削除に失敗しました'
            }), 500

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # シフト種別管理エンドポイント
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/settings/shift_types')
    @admin_required
    def get_shift_types(store):
        """シフト種別一覧を取得"""
        try:
            from database.shift_db import get_all_shift_types
            
            shift_types = get_all_shift_types()
            
            return jsonify({
                'success': True,
                'shift_types': shift_types
            })
            
        except Exception as e:
            print(f"Error in get_shift_types: {e}")
            return jsonify({
                'success': False,
                'message': 'シフト種別の取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/shift_types/create', methods=['POST'])
    @admin_required
    def create_shift_type(store):
        """シフト種別を新規作成"""
        try:
            from database.shift_db import create_shift_type as db_create_shift_type, get_all_shift_types
            
            data = request.get_json()
            shift_name = data.get('shift_name')
            is_work_day = data.get('is_work_day', True)
            color = data.get('color', '#3498db')
            
            if not shift_name:
                return jsonify({
                    'success': False,
                    'message': 'シフト名を入力してください'
                }), 400
            
  
            
            shift_type_id = db_create_shift_type(
                shift_name=shift_name,
                is_work_day=is_work_day,
                color=color,
     
            )
            
            if shift_type_id:
                return jsonify({
                    'success': True,
                    'message': 'シフト種別を追加しました',
                    'shift_type_id': shift_type_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'シフト種別の追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_shift_type: {e}")
            return jsonify({
                'success': False,
                'message': 'シフト種別の追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/shift_types/<int:shift_type_id>', methods=['PUT'])
    @admin_required
    def update_shift_type(store, shift_type_id):
        """シフト種別を更新"""
        try:
            from database.shift_db import update_shift_type as db_update_shift_type
            
            data = request.get_json()
            shift_name = data.get('shift_name')
            is_work_day = data.get('is_work_day')
            color = data.get('color')
            
            if not shift_name:
                return jsonify({
                    'success': False,
                    'message': 'シフト名を入力してください'
                }), 400
            
            success = db_update_shift_type(
                shift_type_id=shift_type_id,
                shift_name=shift_name,
                is_work_day=is_work_day,
                color=color
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'シフト種別を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'シフト種別の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_shift_type: {e}")
            return jsonify({
                'success': False,
                'message': 'シフト種別の更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/shift_types/<int:shift_type_id>', methods=['DELETE'])
    @admin_required
    def delete_shift_type(store, shift_type_id):
        """シフト種別を削除"""
        try:
            from database.shift_db import delete_shift_type as db_delete_shift_type
            
            success = db_delete_shift_type(shift_type_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'シフト種別を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'シフト種別の削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_shift_type: {e}")
            return jsonify({
                'success': False,
                'message': 'シフト種別の削除に失敗しました'
            }), 500
    
    
    @app.route('/<store>/settings/shift_types/move', methods=['POST'])
    @admin_required
    def move_shift_type(store):
        """シフト種別の表示順を変更"""
        try:
            from database.shift_db import update_shift_type_order
            
            data = request.get_json()
            shift_type_id = data.get('shift_type_id')
            new_order = data.get('new_order')
            
            if shift_type_id is None or new_order is None:
                return jsonify({
                    'success': False,
                    'message': 'パラメータが不足しています'
                }), 400
            
            success = update_shift_type_order(shift_type_id, new_order)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '表示順を変更しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '表示順の変更に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in move_shift_type: {e}")
            return jsonify({
                'success': False,
                'message': '表示順の変更に失敗しました'
            }), 500