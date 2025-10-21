# -*- coding: utf-8 -*-
"""
ポイント履歴表示ルート
"""
from flask import render_template, request, session, redirect, url_for
from database.point_db import get_point_history
from database.customer_db import get_customer_by_id


def point_history_view(store):
    """ポイント履歴表示ページ"""
    if 'store' not in session:
        return redirect(url_for('main_routes.index', store=store))

    customer_id = request.args.get('customer_id', type=int)

    if not customer_id:
        return "顧客IDが指定されていません", 400

    store_code = session['store']

    # 顧客情報を取得
    customer = get_customer_by_id(store_code, customer_id)
    if not customer:
        return "顧客が見つかりません", 404

    # ポイント履歴を取得
    history = get_point_history(store_code, customer_id)

    return render_template(
        'point_history.html',
        store=store,
        customer=customer,
        history=history
    )
