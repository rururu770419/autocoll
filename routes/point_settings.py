# -*- coding: utf-8 -*-
"""
ポイント設定ページのルート
"""
from flask import render_template, request, redirect, url_for, session, jsonify
from database.connection import get_store_id
from database.point_settings_db import (
    get_store_point_settings,
    save_store_point_settings,
    get_course_percentage_rules,
    save_course_percentage_rules,
    get_course_point_rules,
    save_course_point_rules,
    get_courses_for_point_settings,
    get_member_types_for_point_settings,
    # ポイント操作理由関連
    get_point_reasons,
    add_point_reason,
    update_point_reason,
    delete_point_reason,
    move_point_reason_up,
    move_point_reason_down
)
from database.db_access import get_display_name


def point_settings_view(store):
    """ポイント設定ページの表示（GET）"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))

    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        # 基本設定を取得
        settings = get_store_point_settings(store_id)

        # コース一覧を取得
        courses = get_courses_for_point_settings(store_id)

        # 会員種別一覧を取得
        member_types = get_member_types_for_point_settings(store_id)

        # パーセンテージルールを取得
        percentage_rules = get_course_percentage_rules(store_id)

        # 固定ポイントルールを取得
        point_rules = get_course_point_rules(store_id)

        # ポイント操作理由一覧を取得
        point_reasons = get_point_reasons(store_id)

        # パーセンテージルールを辞書化（course_id + member_type をキーに）
        percentage_dict = {}
        for rule in percentage_rules:
            key = f"{rule['course_id']}_{rule['member_type']}"
            percentage_dict[key] = rule['percentage_rate']

        # 固定ポイントルールを辞書化
        point_dict = {}
        for rule in point_rules:
            key = f"{rule['course_id']}_{rule['member_type']}"
            point_dict[key] = rule['point_amount']

        success = request.args.get('success')
        error = request.args.get('error')

        return render_template(
            'point_settings.html',
            store=store,
            display_name=display_name,
            settings=settings,
            courses=courses,
            member_types=member_types,
            percentage_dict=percentage_dict,
            point_dict=point_dict,
            point_reasons=point_reasons,
            success=success,
            error=error
        )

    except Exception as e:
        print(f"ポイント設定ページ表示エラー: {e}")
        import traceback
        traceback.print_exc()
        return render_template(
            'point_settings.html',
            store=store,
            display_name=display_name,
            settings={
                'point_method': 'percentage',
                'default_percentage': 5,
                'new_customer_default_points': 0,  # 機能削除により常に0
                'is_active': True
            },
            courses=[],
            member_types=[],
            percentage_dict={},
            point_dict={},
            point_reasons=[],
            error="設定の読み込みに失敗しました"
        )


def point_settings_save(store):
    """ポイント設定の保存（POST）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'データが送信されていません'}), 400

        save_type = data.get('save_type')

        # 基本設定の保存
        if save_type == 'basic':
            settings_data = {
                'point_method': data.get('point_method', 'percentage'),
                'default_percentage': int(data.get('default_percentage', 5)),
                'new_customer_default_points': 0,  # 機能削除により常に0を設定
                'is_active': data.get('is_active', True)
            }

            success = save_store_point_settings(store_id, settings_data)

            if success:
                return jsonify({'success': True, 'message': '基本設定を保存しました'})
            else:
                return jsonify({'success': False, 'message': '保存に失敗しました'}), 500

        # パーセンテージルールの保存
        elif save_type == 'percentage':
            rules = data.get('rules', [])
            success = save_course_percentage_rules(store_id, rules)

            if success:
                return jsonify({'success': True, 'message': 'パーセンテージ設定を保存しました'})
            else:
                return jsonify({'success': False, 'message': '保存に失敗しました'}), 500

        # 固定ポイントルールの保存
        elif save_type == 'course_based':
            rules = data.get('rules', [])
            success = save_course_point_rules(store_id, rules)

            if success:
                return jsonify({'success': True, 'message': '固定ポイント設定を保存しました'})
            else:
                return jsonify({'success': False, 'message': '保存に失敗しました'}), 500

        else:
            return jsonify({'success': False, 'message': '不正な保存タイプです'}), 400

    except Exception as e:
        print(f"ポイント設定保存エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'エラーが発生しました: {str(e)}'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ポイント操作理由管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def add_point_reason_endpoint(store):
    """ポイント操作理由追加API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        data = request.get_json()
        reason_name = data.get('reason_name', '').strip()

        if not reason_name:
            return jsonify({'success': False, 'message': '理由名を入力してください'}), 400

        success = add_point_reason(store_id, reason_name)

        if success:
            return jsonify({'success': True, 'message': '理由を登録しました'})
        else:
            return jsonify({'success': False, 'message': '登録に失敗しました'}), 500

    except Exception as e:
        print(f"理由追加エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def update_point_reason_endpoint(store, reason_id):
    """ポイント操作理由更新API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        data = request.get_json()
        reason_name = data.get('reason_name', '').strip()
        is_active = data.get('is_active', True)

        if not reason_name:
            return jsonify({'success': False, 'message': '理由名を入力してください'}), 400

        success = update_point_reason(store_id, reason_id, reason_name, is_active)

        if success:
            return jsonify({'success': True, 'message': '理由を更新しました'})
        else:
            return jsonify({'success': False, 'message': '更新に失敗しました'}), 500

    except Exception as e:
        print(f"理由更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def delete_point_reason_endpoint(store, reason_id):
    """ポイント操作理由削除API"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        success = delete_point_reason(store_id, reason_id)

        if success:
            return jsonify({'success': True, 'message': '理由を削除しました'})
        else:
            return jsonify({'success': False, 'message': '削除に失敗しました'}), 500

    except Exception as e:
        print(f"理由削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def move_point_reason_up_endpoint(store, reason_id):
    """ポイント操作理由の並び順を上げる"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        success = move_point_reason_up(store_id, reason_id)

        if success:
            return redirect(url_for('main_routes.point_settings', store=store, success='並び順を変更しました'))
        else:
            return redirect(url_for('main_routes.point_settings', store=store, error='並び順の変更に失敗しました'))

    except Exception as e:
        print(f"理由並び順変更エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.point_settings', store=store, error=str(e)))


def move_point_reason_down_endpoint(store, reason_id):
    """ポイント操作理由の並び順を下げる"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        success = move_point_reason_down(store_id, reason_id)

        if success:
            return redirect(url_for('main_routes.point_settings', store=store, success='並び順を変更しました'))
        else:
            return redirect(url_for('main_routes.point_settings', store=store, error='並び順の変更に失敗しました'))

    except Exception as e:
        print(f"理由並び順変更エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.point_settings', store=store, error=str(e)))


def get_point_reasons_api(store):
    """ポイント操作理由一覧取得API（JavaScript用）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        reasons = get_point_reasons(store_id)

        # 有効な理由のみをフィルタ
        active_reasons = [r for r in reasons if r['is_active']]

        return jsonify({'success': True, 'reasons': active_reasons})

    except Exception as e:
        print(f"理由一覧取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def calculate_reservation_points_api(store):
    """予約時のポイント計算API（JavaScript用）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        data = request.get_json()
        course_id = data.get('course_id')
        member_type = data.get('member_type')
        course_price = data.get('course_price')

        if not course_id or not member_type:
            return jsonify({'success': False, 'points': 0})

        # ポイント設定を取得
        settings = get_store_point_settings(store_id)
        point_method = settings.get('point_method', 'percentage')

        calculated_points = 0

        if point_method == 'percentage':
            # パーセンテージルールを取得
            percentage_rules = get_course_percentage_rules(store_id)

            # 該当するルールを探す
            for rule in percentage_rules:
                if rule['course_id'] == int(course_id) and rule['member_type'] == member_type:
                    percentage_rate = rule['percentage_rate']
                    calculated_points = int(course_price * percentage_rate / 100)
                    break

        elif point_method == 'course_based':
            # 固定ポイントルールを取得
            point_rules = get_course_point_rules(store_id)

            # 該当するルールを探す
            for rule in point_rules:
                if rule['course_id'] == int(course_id) and rule['member_type'] == member_type:
                    calculated_points = rule['point_amount']
                    break

        return jsonify({'success': True, 'points': calculated_points})

    except Exception as e:
        print(f"ポイント計算エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'points': 0}), 500


def get_member_types_api(store):
    """会員種別一覧取得API（JavaScript用）"""
    if 'store' not in session:
        return jsonify({'success': False, 'message': '未ログイン'}), 401

    try:
        store_code = session['store']
        store_id = get_store_id(store_code)

        member_types = get_member_types_for_point_settings(store_id)

        return jsonify({'success': True, 'member_types': member_types})

    except Exception as e:
        print(f"会員種別一覧取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
