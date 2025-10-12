from flask import request, jsonify, session, redirect
from functools import wraps


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


def register_settings_management_routes(app):
    """設定管理系のルートを登録（顧客項目設定のみ）"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 顧客項目設定のエンドポイント
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app.route('/<store>/api/customer_fields')
    @admin_required
    def get_customer_fields(store):
        """顧客項目設定を取得"""
        try:
            from database.customer_db import get_customer_field_categories, get_customer_field_options_all
            
            categories = get_customer_field_categories()
            options = get_customer_field_options_all()
            
            return jsonify({
                'success': True,
                'data': {
                    'categories': categories,
                    'options': options
                }
            })
            
        except Exception as e:
            print(f"Error in get_customer_fields: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '顧客項目の取得に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/category', methods=['PUT'])
    @admin_required
    def update_customer_field_category(store):
        """カテゴリ名を更新"""
        try:
            from database.customer_db import update_customer_field_label
            
            data = request.get_json()
            field_key = data.get('field_key')
            field_label = data.get('field_label')
            
            if not field_key or not field_label:
                return jsonify({
                    'success': False,
                    'message': 'パラメータが不足しています'
                }), 400
            
            success = update_customer_field_label(field_key, field_label)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'カテゴリ名を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'カテゴリ名の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_customer_field_category: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'カテゴリ名の更新に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/option', methods=['POST'])
    @admin_required
    def add_customer_field_option(store):
        """選択肢を追加"""
        try:
            from database.customer_db import add_customer_field_option as db_add_option
            
            data = request.get_json()
            field_key = data.get('field_key')
            option_value = data.get('option_value')
            display_color = data.get('display_color', '#f0f0f0')
            
            if not field_key or not option_value:
                return jsonify({
                    'success': False,
                    'message': 'パラメータが不足しています'
                }), 400
            
            option_id = db_add_option(field_key, option_value, display_color)
            
            if option_id:
                return jsonify({
                    'success': True,
                    'message': '選択肢を追加しました',
                    'option_id': option_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '選択肢の追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in add_customer_field_option: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '選択肢の追加に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/option/<int:option_id>', methods=['PUT'])
    @admin_required
    def update_customer_field_option(store, option_id):
        """選択肢を更新"""
        try:
            from database.customer_db import update_customer_field_option as db_update_option
            
            data = request.get_json()
            option_value = data.get('option_value')
            display_color = data.get('display_color')
            
            if not option_value and not display_color:
                return jsonify({
                    'success': False,
                    'message': '更新する項目を指定してください'
                }), 400
            
            success = db_update_option(option_id, option_value, display_color)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '選択肢を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '選択肢の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_customer_field_option: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '選択肢の更新に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/option/<int:option_id>/visibility', methods=['PUT'])
    @admin_required
    def toggle_option_visibility(store, option_id):
        """選択肢の表示/非表示を切り替え"""
        try:
            from database.customer_db import toggle_customer_field_option_visibility
            
            data = request.get_json()
            is_hidden = data.get('is_hidden', False)
            
            success = toggle_customer_field_option_visibility(option_id, is_hidden)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '表示設定を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '表示設定の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in toggle_option_visibility: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '表示設定の更新に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/option/<int:option_id>/move', methods=['PUT'])
    @admin_required
    def move_customer_field_option(store, option_id):
        """選択肢の並び順を変更"""
        try:
            from database.customer_db import move_customer_field_option
            
            data = request.get_json()
            direction = data.get('direction')  # 'up' or 'down'
            
            if direction not in ['up', 'down']:
                return jsonify({
                    'success': False,
                    'message': '方向の指定が不正です'
                }), 400
            
            success = move_customer_field_option(option_id, direction)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '並び順を変更しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '並び順の変更に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in move_customer_field_option: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '並び順の変更に失敗しました'
            }), 500


    @app.route('/<store>/api/customer_fields/option/<int:option_id>', methods=['DELETE'])
    @admin_required
    def delete_customer_field_option(store, option_id):
        """選択肢を削除"""
        try:
            from database.customer_db import delete_customer_field_option as db_delete_option
            
            success = db_delete_option(option_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '選択肢を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '選択肢の削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_customer_field_option: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '選択肢の削除に失敗しました'
            }), 500