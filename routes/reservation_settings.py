from flask import render_template, request, jsonify, session, redirect
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


def get_store_id_from_code(store_code):
    """
    店舗コードから店舗IDを取得
    
    Args:
        store_code (str): 店舗コード（例: 'nagano', 'tokyo'）
    
    Returns:
        int: 店舗ID
    
    TODO: 将来的にはデータベースの stores テーブルから取得するように変更
    """
    # 暫定マッピング（必要に応じて追加・変更してください）
    store_mapping = {
        'nagano': 1,
        'tokyo': 2,
        'osaka': 3
    }
    return store_mapping.get(store_code, 1)  # デフォルトは1


def register_reservation_settings_routes(app):
    """予約設定のルートを登録"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # メインページ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings', endpoint='rs_main')
    @admin_required
    def reservation_settings(store):
        """予約設定ページを表示"""
        try:
            return render_template(
                'reservation_settings.html',
                store=store
            )
            
        except Exception as e:
            print(f"Error in reservation_settings route: {e}")
            import traceback
            traceback.print_exc()
            return redirect(f'/{store}/dashboard')
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # キャンセル理由管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings/cancellation_reasons', endpoint='rs_get_cancellation_reasons')
    @admin_required
    def get_cancellation_reasons(store):
        """キャンセル理由一覧を取得"""
        try:
            from database.reservation_db import get_all_cancellation_reasons
            
            store_id = get_store_id_from_code(store)
            reasons = get_all_cancellation_reasons(store_id)
            
            return jsonify({
                'success': True,
                'data': reasons
            })
            
        except Exception as e:
            print(f"Error in get_cancellation_reasons: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'キャンセル理由の取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/cancellation_reasons', methods=['POST'], endpoint='rs_create_cancellation_reason')
    @admin_required
    def create_cancellation_reason_route(store):
        """キャンセル理由を新規作成"""
        try:
            from database.reservation_db import add_cancellation_reason
            
            data = request.get_json()
            reason_name = data.get('reason_name')
            
            if not reason_name:
                return jsonify({
                    'success': False,
                    'message': 'キャンセル理由名を入力してください'
                }), 400
            
            store_id = get_store_id_from_code(store)
            reason_id = add_cancellation_reason(store_id, reason_name, True)
            
            if reason_id:
                return jsonify({
                    'success': True,
                    'message': 'キャンセル理由を追加しました',
                    'reason_id': reason_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'キャンセル理由の追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_cancellation_reason: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'キャンセル理由の追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/cancellation_reasons/<int:reason_id>', methods=['PUT'], endpoint='rs_update_cancellation_reason')
    @admin_required
    def update_cancellation_reason_route(store, reason_id):
        """キャンセル理由を更新"""
        try:
            from database.reservation_db import update_cancellation_reason
            
            data = request.get_json()
            reason_name = data.get('reason_name')
            
            if not reason_name:
                return jsonify({
                    'success': False,
                    'message': 'キャンセル理由名を入力してください'
                }), 400
            
            success = update_cancellation_reason(reason_id, reason_name=reason_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'キャンセル理由を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'キャンセル理由の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_cancellation_reason: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'キャンセル理由の更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/cancellation_reasons/<int:reason_id>', methods=['DELETE'], endpoint='rs_delete_cancellation_reason')
    @admin_required
    def delete_cancellation_reason_route(store, reason_id):
        """キャンセル理由を削除"""
        try:
            from database.reservation_db import delete_cancellation_reason
            
            success = delete_cancellation_reason(reason_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'キャンセル理由を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'キャンセル理由の削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_cancellation_reason: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'キャンセル理由の削除に失敗しました'
            }), 500
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 予約方法管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings/reservation_methods', endpoint='rs_get_reservation_methods')
    @admin_required
    def get_reservation_methods(store):
        """予約方法一覧を取得"""
        try:
            from database.reservation_db import get_all_reservation_methods
            
            store_id = get_store_id_from_code(store)
            methods = get_all_reservation_methods(store_id)
            
            return jsonify({
                'success': True,
                'data': methods
            })
            
        except Exception as e:
            print(f"Error in get_reservation_methods: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '予約方法の取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/reservation_methods', methods=['POST'], endpoint='rs_create_reservation_method')
    @admin_required
    def create_reservation_method_route(store):
        """予約方法を新規作成"""
        try:
            from database.reservation_db import add_reservation_method
            
            data = request.get_json()
            method_name = data.get('method_name')
            
            if not method_name:
                return jsonify({
                    'success': False,
                    'message': '予約方法名を入力してください'
                }), 400
            
            store_id = get_store_id_from_code(store)
            method_id = add_reservation_method(store_id, method_name, True)
            
            if method_id:
                return jsonify({
                    'success': True,
                    'message': '予約方法を追加しました',
                    'method_id': method_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '予約方法の追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_reservation_method: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '予約方法の追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/reservation_methods/<int:method_id>', methods=['PUT'], endpoint='rs_update_reservation_method')
    @admin_required
    def update_reservation_method_route(store, method_id):
        """予約方法を更新"""
        try:
            from database.reservation_db import update_reservation_method
            
            data = request.get_json()
            method_name = data.get('method_name')
            
            if not method_name:
                return jsonify({
                    'success': False,
                    'message': '予約方法名を入力してください'
                }), 400
            
            success = update_reservation_method(method_id, method_name, True)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '予約方法を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '予約方法の更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_reservation_method: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '予約方法の更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/reservation_methods/<int:method_id>', methods=['DELETE'], endpoint='rs_delete_reservation_method')
    @admin_required
    def delete_reservation_method_route(store, method_id):
        """予約方法を削除"""
        try:
            from database.reservation_db import delete_reservation_method
            
            success = delete_reservation_method(method_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '予約方法を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '予約方法の削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_reservation_method: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '予約方法の削除に失敗しました'
            }), 500
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # カード手数料
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings/card_fee_rate', methods=['GET'], endpoint='rs_get_card_fee_rate')
    @admin_required
    def get_card_fee_rate_api(store):
        """カード手数料率を取得"""
        try:
            from database.settings_db import get_card_fee_rate
            
            rate = get_card_fee_rate()
            
            return jsonify({
                'success': True,
                'rate': rate
            })
            
        except Exception as e:
            print(f"Error in get_card_fee_rate_api: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'カード手数料率の取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/card_fee_rate', methods=['POST'], endpoint='rs_save_card_fee_rate')
    @admin_required
    def save_card_fee_rate_api(store):
        """カード手数料率を保存"""
        try:
            from database.settings_db import save_card_fee_rate
            
            data = request.get_json()
            card_fee_rate = data.get('card_fee_rate')
            
            if card_fee_rate is None:
                return jsonify({
                    'success': False,
                    'message': 'カード手数料率を入力してください'
                }), 400
            
            # 数値チェック
            try:
                card_fee_rate = float(card_fee_rate)
                if card_fee_rate < 0 or card_fee_rate > 100:
                    return jsonify({
                        'success': False,
                        'message': 'カード手数料率は0〜100の範囲で入力してください'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'カード手数料率は数値で入力してください'
                }), 400
            
            updated_by = session.get('user_name', 'unknown')
            
            success = save_card_fee_rate(None, card_fee_rate, updated_by)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'カード手数料率を保存しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'カード手数料率の保存に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in save_card_fee_rate_api: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'カード手数料率の保存に失敗しました'
            }), 500
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NGエリア管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings/ng_areas', endpoint='rs_get_ng_areas')
    @admin_required
    def get_ng_areas(store):
        """NGエリア一覧を取得"""
        try:
            from database.cast_db import get_all_ng_areas_by_store, get_db_connection
            
            store_id = get_store_id_from_code(store)
            db = get_db_connection(store)
            areas = get_all_ng_areas_by_store(db, store_id)
            db.close()
            
            return jsonify({
                'success': True,
                'data': areas
            })
            
        except Exception as e:
            print(f"Error in get_ng_areas: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'NGエリアの取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_areas', methods=['POST'], endpoint='rs_create_ng_area')
    @admin_required
    def create_ng_area(store):
        """NGエリアを新規作成"""
        try:
            from database.cast_db import create_ng_area as db_create_ng_area, get_db_connection
            
            data = request.get_json()
            area_name = data.get('area_name')
            
            if not area_name:
                return jsonify({
                    'success': False,
                    'message': 'エリア名を入力してください'
                }), 400
            
            store_id = get_store_id_from_code(store)
            db = get_db_connection(store)
            area_id = db_create_ng_area(db, store_id, area_name)
            db.close()
            
            if area_id:
                return jsonify({
                    'success': True,
                    'message': 'NGエリアを追加しました',
                    'area_id': area_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'NGエリアの追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_ng_area: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'NGエリアの追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_areas/<int:area_id>', methods=['PUT'], endpoint='rs_update_ng_area')
    @admin_required
    def update_ng_area(store, area_id):
        """NGエリアを更新"""
        try:
            from database.cast_db import update_ng_area as db_update_ng_area, get_db_connection
            
            data = request.get_json()
            area_name = data.get('area_name')
            
            if not area_name:
                return jsonify({
                    'success': False,
                    'message': 'エリア名を入力してください'
                }), 400
            
            db = get_db_connection(store)
            success = db_update_ng_area(db, area_id, area_name)
            db.close()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'NGエリアを更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'NGエリアの更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_ng_area: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'NGエリアの更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_areas/<int:area_id>', methods=['DELETE'], endpoint='rs_delete_ng_area')
    @admin_required
    def delete_ng_area(store, area_id):
        """NGエリアを削除"""
        try:
            from database.cast_db import delete_ng_area as db_delete_ng_area, get_db_connection
            
            db = get_db_connection(store)
            success = db_delete_ng_area(db, area_id)
            db.close()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'NGエリアを削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'NGエリアの削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_ng_area: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': 'NGエリアの削除に失敗しました'
            }), 500
    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 年齢NG管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.route('/<store>/reservation-settings/ng_ages', endpoint='rs_get_ng_ages')
    @admin_required
    def get_ng_ages(store):
        """年齢NG一覧を取得"""
        try:
            from database.cast_db import get_all_ng_age_patterns_by_store, get_db_connection
            
            store_id = get_store_id_from_code(store)
            db = get_db_connection(store)
            patterns = get_all_ng_age_patterns_by_store(db, store_id)
            db.close()
            
            return jsonify({
                'success': True,
                'data': patterns
            })
            
        except Exception as e:
            print(f"Error in get_ng_ages: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '年齢NGの取得に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_ages', methods=['POST'], endpoint='rs_create_ng_age')
    @admin_required
    def create_ng_age(store):
        """年齢NGを新規作成"""
        try:
            from database.cast_db import create_ng_age_pattern, get_db_connection
            
            data = request.get_json()
            pattern_name = data.get('pattern_name')
            description = data.get('description', '')
            
            if not pattern_name:
                return jsonify({
                    'success': False,
                    'message': 'パターン名を入力してください'
                }), 400
            
            store_id = get_store_id_from_code(store)
            db = get_db_connection(store)
            age_id = create_ng_age_pattern(db, store_id, pattern_name, description)
            db.close()
            
            if age_id:
                return jsonify({
                    'success': True,
                    'message': '年齢NGを追加しました',
                    'age_id': age_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '年齢NGの追加に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in create_ng_age: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '年齢NGの追加に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_ages/<int:age_id>', methods=['PUT'], endpoint='rs_update_ng_age')
    @admin_required
    def update_ng_age(store, age_id):
        """年齢NGを更新"""
        try:
            from database.cast_db import update_ng_age_pattern, get_db_connection
            
            data = request.get_json()
            pattern_name = data.get('pattern_name')
            description = data.get('description', '')
            
            if not pattern_name:
                return jsonify({
                    'success': False,
                    'message': 'パターン名を入力してください'
                }), 400
            
            db = get_db_connection(store)
            success = update_ng_age_pattern(db, age_id, pattern_name, description)
            db.close()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '年齢NGを更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '年齢NGの更新に失敗しました'
                }), 500
                
        except Exception as e:
            print(f"Error in update_ng_age: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '年齢NGの更新に失敗しました'
            }), 500
    
    
    @app.route('/<store>/reservation-settings/ng_ages/<int:age_id>', methods=['DELETE'], endpoint='rs_delete_ng_age')
    @admin_required
    def delete_ng_age(store, age_id):
        """年齢NGを削除"""
        try:
            from database.cast_db import delete_ng_age_pattern, get_db_connection
            
            db = get_db_connection(store)
            success = delete_ng_age_pattern(db, age_id)
            db.close()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '年齢NGを削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '年齢NGの削除に失敗しました（使用中の可能性があります）'
                }), 500
                
        except Exception as e:
            print(f"Error in delete_ng_age: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '年齢NGの削除に失敗しました'
            }), 500


    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 待ち合わせ場所管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app.route('/<store>/reservation-settings/meeting_places', endpoint='rs_get_meeting_places')
    @admin_required
    def get_meeting_places(store):
        """待ち合わせ場所一覧を取得"""
        try:
            from database.meeting_places_db import get_all_meeting_places

            store_id = get_store_id_from_code(store)
            places = get_all_meeting_places(store_id)

            return jsonify({
                'success': True,
                'data': places
            })

        except Exception as e:
            print(f"Error in get_meeting_places: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '待ち合わせ場所の取得に失敗しました'
            }), 500


    @app.route('/<store>/reservation-settings/meeting_places', methods=['POST'], endpoint='rs_create_meeting_place')
    @admin_required
    def create_meeting_place_route(store):
        """待ち合わせ場所を新規作成"""
        try:
            from database.meeting_places_db import add_meeting_place

            data = request.get_json()
            place_name = data.get('place_name')

            if not place_name:
                return jsonify({
                    'success': False,
                    'message': '場所名を入力してください'
                }), 400

            store_id = get_store_id_from_code(store)
            place_id = add_meeting_place(store_id, place_name, True)

            if place_id:
                return jsonify({
                    'success': True,
                    'message': '待ち合わせ場所を追加しました',
                    'place_id': place_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '待ち合わせ場所の追加に失敗しました'
                }), 500

        except Exception as e:
            print(f"Error in create_meeting_place: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '待ち合わせ場所の追加に失敗しました'
            }), 500


    @app.route('/<store>/reservation-settings/meeting_places/<int:place_id>', methods=['PUT'], endpoint='rs_update_meeting_place')
    @admin_required
    def update_meeting_place_route(store, place_id):
        """待ち合わせ場所を更新"""
        try:
            from database.meeting_places_db import update_meeting_place

            data = request.get_json()
            place_name = data.get('place_name')

            if not place_name:
                return jsonify({
                    'success': False,
                    'message': '場所名を入力してください'
                }), 400

            success = update_meeting_place(place_id, place_name=place_name)

            if success:
                return jsonify({
                    'success': True,
                    'message': '待ち合わせ場所を更新しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '待ち合わせ場所の更新に失敗しました'
                }), 500

        except Exception as e:
            print(f"Error in update_meeting_place: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '待ち合わせ場所の更新に失敗しました'
            }), 500


    @app.route('/<store>/reservation-settings/meeting_places/<int:place_id>', methods=['DELETE'], endpoint='rs_delete_meeting_place')
    @admin_required
    def delete_meeting_place_route(store, place_id):
        """待ち合わせ場所を論理削除"""
        try:
            from database.meeting_places_db import delete_meeting_place

            success = delete_meeting_place(place_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': '待ち合わせ場所を削除しました'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '待ち合わせ場所の削除に失敗しました'
                }), 500

        except Exception as e:
            print(f"Error in delete_meeting_place: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': '待ち合わせ場所の削除に失敗しました'
            }), 500