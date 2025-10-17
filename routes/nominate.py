from flask import render_template, request, redirect, url_for
from database.connection import get_store_id, get_display_name
from database.nominate_db import (
    get_all_nomination_types, get_nomination_type_by_id, add_nomination_type,
    update_nomination_type, delete_nomination_type,
    move_nomination_type_up, move_nomination_type_down
)

def nominate_management(store):
    """指名管理ページ"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        store_id = get_store_id(store)
        nomination_types_data = get_all_nomination_types(store_id=store_id)
        success = request.args.get('success')
        error = request.args.get('error')

        return render_template(
            'nominate.html',
            nomination_types=nomination_types_data,
            store=store,
            display_name=display_name,
            success=success,
            error=error
        )
    except Exception as e:
        print(f"指名管理ページエラー: {e}")
        import traceback
        traceback.print_exc()
        return render_template(
            'nominate.html',
            nomination_types=[],
            store=store,
            display_name=display_name,
            error="指名種類一覧の取得に失敗しました"
        )

def register_nomination_type(store):
    """指名種類登録処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        type_name = request.form.get('type_name', '').strip()
        additional_fee = request.form.get('additional_fee', '').strip()
        back_amount = request.form.get('back_amount', '').strip()
        is_active = True if request.form.get('is_active') == 'on' else False

        # バリデーション
        if not type_name:
            return redirect(url_for('main_routes.nominate_management', store=store, error="種類名を入力してください"))

        if not additional_fee or not additional_fee.isdigit() or int(additional_fee) < 0:
            return redirect(url_for('main_routes.nominate_management', store=store, error="正しい金額を入力してください"))

        if not back_amount or not back_amount.isdigit() or int(back_amount) < 0:
            return redirect(url_for('main_routes.nominate_management', store=store, error="正しいバック金額を入力してください"))

        additional_fee_int = int(additional_fee)
        back_amount_int = int(back_amount)

        if back_amount_int > additional_fee_int:
            return redirect(url_for('main_routes.nominate_management', store=store, error="バック金額は金額以下で入力してください"))

        # 店舗IDを動的取得
        store_id = get_store_id(store)

        # 指名種類登録
        result = add_nomination_type(type_name, additional_fee_int, back_amount_int, store_id, is_active)

        if result:
            return redirect(url_for('main_routes.nominate_management', store=store, success="指名種類を登録しました"))
        else:
            return redirect(url_for('main_routes.nominate_management', store=store, error="指名種類の登録に失敗しました"))

    except Exception as e:
        print(f"指名種類登録エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.nominate_management', store=store, error=f"指名種類の登録中にエラーが発生しました: {str(e)}"))

def update_nomination_type_route(store, nomination_type_id):
    """指名種類更新処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        type_name = request.form.get('type_name', '').strip()
        additional_fee = request.form.get('additional_fee', '').strip()
        back_amount = request.form.get('back_amount', '').strip()
        is_active_str = request.form.get('is_active', 'true')
        is_active = True if is_active_str == 'true' else False

        # バリデーション
        if not type_name:
            return redirect(url_for('main_routes.nominate_management', store=store, error="種類名を入力してください"))

        if not additional_fee or not additional_fee.isdigit() or int(additional_fee) < 0:
            return redirect(url_for('main_routes.nominate_management', store=store, error="正しい金額を入力してください"))

        if not back_amount or not back_amount.isdigit() or int(back_amount) < 0:
            return redirect(url_for('main_routes.nominate_management', store=store, error="正しいバック金額を入力してください"))

        additional_fee_int = int(additional_fee)
        back_amount_int = int(back_amount)

        if back_amount_int > additional_fee_int:
            return redirect(url_for('main_routes.nominate_management', store=store, error="バック金額は金額以下で入力してください"))

        # 指名種類更新
        if update_nomination_type(nomination_type_id, type_name, additional_fee_int, back_amount_int, is_active):
            return redirect(url_for('main_routes.nominate_management', store=store, success="指名種類情報を更新しました"))
        else:
            return redirect(url_for('main_routes.nominate_management', store=store, error="指名種類情報の更新に失敗しました"))

    except Exception as e:
        print(f"指名種類更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.nominate_management', store=store, error="指名種類情報の更新中にエラーが発生しました"))

def delete_nomination_type_route(store, nomination_type_id):
    """指名種類削除処理"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        if delete_nomination_type(nomination_type_id):
            return redirect(url_for('main_routes.nominate_management', store=store, success="指名種類を削除しました"))
        else:
            return redirect(url_for('main_routes.nominate_management', store=store, error="指名種類の削除に失敗しました"))
    except Exception as e:
        print(f"指名種類削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.nominate_management', store=store, error="指名種類の削除中にエラーが発生しました"))

def move_nomination_type_up_route(store, nomination_type_id):
    """指名種類並び順上移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        if move_nomination_type_up(nomination_type_id):
            return redirect(url_for('main_routes.nominate_management', store=store, success="並び順を変更しました"))
        else:
            # 既に最上位の場合はエラーを表示せずにリダイレクト
            return redirect(url_for('main_routes.nominate_management', store=store))
    except Exception as e:
        print(f"並び順上移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.nominate_management', store=store, error="並び順の変更中にエラーが発生しました"))

def move_nomination_type_down_route(store, nomination_type_id):
    """指名種類並び順下移動"""
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404

    try:
        if move_nomination_type_down(nomination_type_id):
            return redirect(url_for('main_routes.nominate_management', store=store, success="並び順を変更しました"))
        else:
            # 既に最下位の場合はエラーを表示せずにリダイレクト
            return redirect(url_for('main_routes.nominate_management', store=store))
    except Exception as e:
        print(f"並び順下移動エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main_routes.nominate_management', store=store, error="並び順の変更中にエラーが発生しました"))
