# -*- coding: utf-8 -*-
"""
ポイント設定関連のデータベース操作
"""
from database.connection import get_db


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 店舗ポイント基本設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_store_point_settings(store_id):
    """店舗のポイント基本設定を取得"""
    db = get_db()
    try:
        result = db.execute("""
            SELECT
                point_method,
                default_percentage,
                new_customer_default_points,
                is_active
            FROM store_point_settings
            WHERE store_id = %s
        """, (store_id,)).fetchone()

        if result:
            return dict(result)
        else:
            # デフォルト値を返す
            return {
                'point_method': 'percentage',  # デフォルトはパーセンテージ方式
                'default_percentage': 5,
                'new_customer_default_points': 0,
                'is_active': True
            }
    finally:
        db.close()


def save_store_point_settings(store_id, data):
    """店舗のポイント基本設定を保存"""
    db = get_db()
    try:
        # 既存データの確認
        existing = db.execute("""
            SELECT store_id FROM store_point_settings
            WHERE store_id = %s
        """, (store_id,)).fetchone()

        if existing:
            # UPDATE
            db.execute("""
                UPDATE store_point_settings
                SET
                    point_method = %s,
                    default_percentage = %s,
                    new_customer_default_points = %s,
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE store_id = %s
            """, (
                data.get('point_method', 'percentage'),
                data.get('default_percentage', 5),
                data.get('new_customer_default_points', 0),
                data.get('is_active', True),
                store_id
            ))
        else:
            # INSERT
            db.execute("""
                INSERT INTO store_point_settings (
                    store_id,
                    point_method,
                    default_percentage,
                    new_customer_default_points,
                    is_active
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                store_id,
                data.get('point_method', 'percentage'),
                data.get('default_percentage', 5),
                data.get('new_customer_default_points', 0),
                data.get('is_active', True)
            ))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving store point settings: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# コース×会員種別 パーセンテージルール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_course_percentage_rules(store_id):
    """コース×会員種別のパーセンテージルールを取得"""
    db = get_db()
    try:
        results = db.execute("""
            SELECT
                course_id,
                member_type,
                percentage_rate
            FROM course_percentage_rules
            WHERE store_id = %s
        """, (store_id,)).fetchall()

        return [dict(row) for row in results]
    finally:
        db.close()


def save_course_percentage_rules(store_id, rules):
    """コース×会員種別のパーセンテージルールを保存

    Args:
        store_id: 店舗ID
        rules: [{'course_id': 1, 'member_type': '一般会員', 'percentage_rate': 5}, ...]
    """
    db = get_db()
    try:
        # 既存データを削除
        db.execute("""
            DELETE FROM course_percentage_rules
            WHERE store_id = %s
        """, (store_id,))

        # 新しいデータを挿入
        for rule in rules:
            if rule.get('percentage_rate') is not None and rule.get('percentage_rate') != '':
                db.execute("""
                    INSERT INTO course_percentage_rules (
                        store_id,
                        course_id,
                        member_type,
                        percentage_rate
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    store_id,
                    rule['course_id'],
                    rule['member_type'],
                    int(rule['percentage_rate'])
                ))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving course percentage rules: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# コース×会員種別 固定ポイントルール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_course_point_rules(store_id):
    """コース×会員種別の固定ポイントルールを取得"""
    db = get_db()
    try:
        results = db.execute("""
            SELECT
                course_id,
                member_type,
                point_amount
            FROM course_point_rules
            WHERE store_id = %s
        """, (store_id,)).fetchall()

        return [dict(row) for row in results]
    finally:
        db.close()


def save_course_point_rules(store_id, rules):
    """コース×会員種別の固定ポイントルールを保存

    Args:
        store_id: 店舗ID
        rules: [{'course_id': 1, 'member_type': '一般会員', 'point_amount': 100}, ...]
    """
    db = get_db()
    try:
        # 既存データを削除
        db.execute("""
            DELETE FROM course_point_rules
            WHERE store_id = %s
        """, (store_id,))

        # 新しいデータを挿入
        for rule in rules:
            if rule.get('point_amount') is not None and rule.get('point_amount') != '':
                db.execute("""
                    INSERT INTO course_point_rules (
                        store_id,
                        course_id,
                        member_type,
                        point_amount
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    store_id,
                    rule['course_id'],
                    rule['member_type'],
                    int(rule['point_amount'])
                ))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving course point rules: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# マスタデータ取得（コース・会員種別）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_courses_for_point_settings(store_id):
    """ポイント設定用のコース一覧を取得"""
    db = get_db()
    try:
        results = db.execute("""
            SELECT
                c.course_id,
                c.name as course_name,
                cc.category_name
            FROM courses c
            LEFT JOIN course_categories cc ON c.category_id = cc.category_id
            WHERE c.store_id = %s AND c.is_active = true
            ORDER BY cc.category_name, c.sort_order
        """, (store_id,)).fetchall()

        return [dict(row) for row in results]
    finally:
        db.close()


def get_member_types_for_point_settings(store_id):
    """ポイント設定用の会員種別一覧を取得"""
    db = get_db()
    try:
        results = db.execute("""
            SELECT DISTINCT
                option_value as member_type,
                display_order
            FROM customer_field_options
            WHERE store_id = %s
              AND field_key = 'member_type'
              AND is_hidden = false
            ORDER BY display_order
        """, (store_id,)).fetchall()

        return [row['member_type'] for row in results]
    finally:
        db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ポイント操作理由マスタ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_point_reasons(store_id):
    """ポイント操作理由一覧を取得"""
    db = get_db()
    try:
        results = db.execute("""
            SELECT
                reason_id,
                reason_name,
                display_order,
                is_active,
                created_at,
                updated_at
            FROM point_operation_reasons
            WHERE store_id = %s
            ORDER BY display_order
        """, (store_id,)).fetchall()

        return [dict(row) for row in results]
    finally:
        db.close()


def add_point_reason(store_id, reason_name):
    """ポイント操作理由を追加"""
    db = get_db()
    try:
        # 最大の display_order を取得
        max_order_result = db.execute("""
            SELECT COALESCE(MAX(display_order), -1) as max_order
            FROM point_operation_reasons
            WHERE store_id = %s
        """, (store_id,)).fetchone()

        next_order = max_order_result['max_order'] + 1

        # 新規追加
        db.execute("""
            INSERT INTO point_operation_reasons (
                store_id,
                reason_name,
                display_order,
                is_active
            ) VALUES (%s, %s, %s, %s)
        """, (store_id, reason_name, next_order, True))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding point reason: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def update_point_reason(store_id, reason_id, reason_name, is_active):
    """ポイント操作理由を更新"""
    db = get_db()
    try:
        db.execute("""
            UPDATE point_operation_reasons
            SET
                reason_name = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND reason_id = %s
        """, (reason_name, is_active, store_id, reason_id))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating point reason: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def delete_point_reason(store_id, reason_id):
    """ポイント操作理由を削除"""
    db = get_db()
    try:
        # 削除対象の display_order を取得
        target = db.execute("""
            SELECT display_order
            FROM point_operation_reasons
            WHERE store_id = %s AND reason_id = %s
        """, (store_id, reason_id)).fetchone()

        if not target:
            return False

        target_order = target['display_order']

        # 削除
        db.execute("""
            DELETE FROM point_operation_reasons
            WHERE store_id = %s AND reason_id = %s
        """, (store_id, reason_id))

        # 後続の項目の display_order を詰める
        db.execute("""
            UPDATE point_operation_reasons
            SET display_order = display_order - 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND display_order > %s
        """, (store_id, target_order))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting point reason: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def move_point_reason_up(store_id, reason_id):
    """ポイント操作理由の並び順を上げる"""
    db = get_db()
    try:
        # 現在の項目を取得
        current = db.execute("""
            SELECT display_order
            FROM point_operation_reasons
            WHERE store_id = %s AND reason_id = %s
        """, (store_id, reason_id)).fetchone()

        if not current or current['display_order'] == 0:
            return False  # 既に一番上

        current_order = current['display_order']

        # 1つ上の項目を取得
        prev = db.execute("""
            SELECT reason_id
            FROM point_operation_reasons
            WHERE store_id = %s AND display_order = %s
        """, (store_id, current_order - 1)).fetchone()

        if not prev:
            return False

        # 順序を入れ替え
        db.execute("""
            UPDATE point_operation_reasons
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND reason_id = %s
        """, (current_order, store_id, prev['reason_id']))

        db.execute("""
            UPDATE point_operation_reasons
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND reason_id = %s
        """, (current_order - 1, store_id, reason_id))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error moving point reason up: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def move_point_reason_down(store_id, reason_id):
    """ポイント操作理由の並び順を下げる"""
    db = get_db()
    try:
        # 現在の項目を取得
        current = db.execute("""
            SELECT display_order
            FROM point_operation_reasons
            WHERE store_id = %s AND reason_id = %s
        """, (store_id, reason_id)).fetchone()

        if not current:
            return False

        current_order = current['display_order']

        # 最大の display_order を取得
        max_order_result = db.execute("""
            SELECT MAX(display_order) as max_order
            FROM point_operation_reasons
            WHERE store_id = %s
        """, (store_id,)).fetchone()

        if current_order >= max_order_result['max_order']:
            return False  # 既に一番下

        # 1つ下の項目を取得
        next_item = db.execute("""
            SELECT reason_id
            FROM point_operation_reasons
            WHERE store_id = %s AND display_order = %s
        """, (store_id, current_order + 1)).fetchone()

        if not next_item:
            return False

        # 順序を入れ替え
        db.execute("""
            UPDATE point_operation_reasons
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND reason_id = %s
        """, (current_order, store_id, next_item['reason_id']))

        db.execute("""
            UPDATE point_operation_reasons
            SET display_order = %s, updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND reason_id = %s
        """, (current_order + 1, store_id, reason_id))

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error moving point reason down: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
