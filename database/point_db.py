# -*- coding: utf-8 -*-
"""
ポイント管理用のデータベース操作関数
"""
import os
import sys

# Windows環境でUTF-8を強制
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

from database.connection import get_connection, get_store_id
from datetime import datetime


def add_point_transaction(store_code, customer_id, point_change, transaction_type, reason=None):
    """
    ポイント取引を追加する

    Args:
        store_code: 店舗コード
        customer_id: 顧客ID
        point_change: ポイント変動（+5、-3など）
        transaction_type: 'add' または 'consume'
        reason: 理由（任意）

    Returns:
        bool: 成功したらTrue
    """
    try:
        store_id = get_store_id(store_code)
        db = get_connection()
        cursor = db.cursor()

        # 現在のポイントを取得
        cursor.execute(
            "SELECT current_points FROM customers WHERE customer_id = %s AND store_id = %s",
            (customer_id, store_id)
        )
        result = cursor.fetchone()

        if not result:
            db.close()
            return False

        current_points = result[0] or 0

        # 新しいポイント残高を計算
        balance_after = current_points + point_change

        # 残高がマイナスにならないかチェック
        if balance_after < 0:
            db.close()
            return False

        # ポイント履歴に追加
        cursor.execute(
            """
            INSERT INTO point_history
            (store_id, customer_id, point_change, balance_after, transaction_type, reason, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (store_id, customer_id, point_change, balance_after, transaction_type, reason)
        )

        # 顧客テーブルのcurrent_pointsを更新
        cursor.execute(
            "UPDATE customers SET current_points = %s, updated_at = CURRENT_TIMESTAMP WHERE customer_id = %s AND store_id = %s",
            (balance_after, customer_id, store_id)
        )

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"ポイント取引追加エラー: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
            db.close()
        return False


def get_point_history(store_code, customer_id):
    """
    顧客のポイント履歴を取得

    Args:
        store_code: 店舗コード
        customer_id: 顧客ID

    Returns:
        list: ポイント履歴のリスト
    """
    try:
        store_id = get_store_id(store_code)
        db = get_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                ph.id,
                ph.customer_id,
                ph.point_change,
                ph.balance_after,
                ph.transaction_type,
                ph.reason,
                ph.created_at
            FROM point_history ph
            WHERE ph.customer_id = %s AND ph.store_id = %s
            ORDER BY ph.created_at DESC
            """,
            (customer_id, store_id)
        )

        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'customer_id': row[1],
                'point_change': row[2],
                'balance_after': row[3],
                'transaction_type': row[4],
                'reason': row[5],
                'created_at': row[6]
            })

        db.close()
        return history

    except Exception as e:
        print(f"ポイント履歴取得エラー: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.close()
        return []


def get_customer_current_points(store_code, customer_id):
    """
    顧客の現在のポイントを取得

    Args:
        store_code: 店舗コード
        customer_id: 顧客ID

    Returns:
        int: 現在のポイント
    """
    try:
        store_id = get_store_id(store_code)
        db = get_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT current_points FROM customers WHERE customer_id = %s AND store_id = %s",
            (customer_id, store_id)
        )

        result = cursor.fetchone()
        db.close()

        if result:
            return result[0] or 0
        return 0

    except Exception as e:
        print(f"ポイント取得エラー: {e}")
        if db:
            db.close()
        return 0
