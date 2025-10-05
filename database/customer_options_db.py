# -*- coding: utf-8 -*-
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """データベース接続を取得"""
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname='pickup_system',
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'diary8475ftkb')
    )
    return conn


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# カテゴリ管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_all_categories(store_code):
    """全カテゴリを取得"""
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT id, field_key, field_label, display_order, is_deletable
                FROM customer_field_categories
                WHERE store_code = %s
                ORDER BY display_order
            """, (store_code,))
            return cursor.fetchall()
    finally:
        conn.close()


def update_category_label(store_code, field_key, new_label):
    """カテゴリ名を更新"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE customer_field_categories
                SET field_label = %s, updated_at = CURRENT_TIMESTAMP
                WHERE store_code = %s AND field_key = %s
            """, (new_label, store_code, field_key))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating category label: {e}")
        return False
    finally:
        conn.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 選択肢管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_field_options(store_code, field_key):
    """指定カテゴリの選択肢を取得"""
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT id, option_value, display_color, display_order, is_hidden
                FROM customer_field_options
                WHERE store_code = %s AND field_key = %s
                ORDER BY display_order
            """, (store_code, field_key))
            return cursor.fetchall()
    finally:
        conn.close()


def get_all_field_options(store_code):
    """全カテゴリの選択肢を取得（顧客編集画面用）"""
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT field_key, option_value, display_color, is_hidden
                FROM customer_field_options
                WHERE store_code = %s
                ORDER BY field_key, display_order
            """, (store_code,))
            
            # カテゴリ別に整理
            options = {}
            for row in cursor.fetchall():
                field_key = row['field_key']
                if field_key not in options:
                    options[field_key] = []
                options[field_key].append({
                    'value': row['option_value'],
                    'color': row['display_color'],
                    'is_hidden': row['is_hidden']
                })
            
            return options
    finally:
        conn.close()


def add_field_option(store_code, field_key, option_value, display_color='#f0f0f0'):
    """選択肢を追加"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 最大のdisplay_orderを取得
            cursor.execute("""
                SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
                FROM customer_field_options
                WHERE store_code = %s AND field_key = %s
            """, (store_code, field_key))
            next_order = cursor.fetchone()[0]
            
            # 新規追加
            cursor.execute("""
                INSERT INTO customer_field_options 
                (store_code, field_key, option_value, display_color, display_order)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (store_code, field_key, option_value, display_color, next_order))
            
            option_id = cursor.fetchone()[0]
            conn.commit()
            return option_id
    except Exception as e:
        conn.rollback()
        print(f"Error adding field option: {e}")
        return None
    finally:
        conn.close()


def update_field_option(option_id, option_value=None, display_color=None):
    """選択肢を更新"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if option_value is not None:
                updates.append("option_value = %s")
                params.append(option_value)
            
            if display_color is not None:
                updates.append("display_color = %s")
                params.append(display_color)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(option_id)
            
            cursor.execute(f"""
                UPDATE customer_field_options
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating field option: {e}")
        return False
    finally:
        conn.close()


def toggle_field_option_visibility(option_id, is_hidden):
    """選択肢の表示/非表示を切り替え"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE customer_field_options
                SET is_hidden = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (is_hidden, option_id))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error toggling visibility: {e}")
        return False
    finally:
        conn.close()


def delete_field_option(store_code, option_id):
    """選択肢を削除（使用中チェック付き）"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 使用中かチェック
            cursor.execute("""
                SELECT field_key, option_value
                FROM customer_field_options
                WHERE id = %s AND store_code = %s
            """, (option_id, store_code))
            
            option = cursor.fetchone()
            if not option:
                return {'success': False, 'message': '選択肢が見つかりません'}
            
            field_key, option_value = option
            
            # 対応するカラム名を取得
            column_map = {
                'member_type': 'member_type',
                'status': 'status',
                'web_member': 'web_member',
                'recruitment_source': 'recruitment_source'
            }
            
            column_name = column_map.get(field_key)
            if not column_name:
                return {'success': False, 'message': '不正なフィールドキーです'}
            
            # 使用中の顧客がいるかチェック
            cursor.execute(f"""
                SELECT COUNT(*) FROM customers
                WHERE {column_name} = %s
            """, (option_value,))
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                return {
                    'success': False, 
                    'message': f'この項目は{count}件の顧客データで使用中のため削除できません。非表示にしてください。'
                }
            
            # 削除実行
            cursor.execute("""
                DELETE FROM customer_field_options
                WHERE id = %s
            """, (option_id,))
            
            conn.commit()
            return {'success': True, 'message': '選択肢を削除しました'}
            
    except Exception as e:
        conn.rollback()
        print(f"Error deleting field option: {e}")
        return {'success': False, 'message': f'エラーが発生しました: {str(e)}'}
    finally:
        conn.close()


def move_field_option(store_code, option_id, direction):
    """
    選択肢の表示順序を変更
    
    Args:
        store_code: 店舗コード
        option_id: 移動する選択肢のID
        direction: 'up' or 'down'
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 現在の選択肢を取得
            cursor.execute("""
                SELECT field_key, display_order
                FROM customer_field_options
                WHERE id = %s AND store_code = %s
            """, (option_id, store_code))
            
            current = cursor.fetchone()
            if not current:
                return {'success': False, 'message': '選択肢が見つかりません'}
            
            field_key, current_order = current
            
            # 入れ替え対象を取得
            if direction == 'up':
                # 1つ上の項目（display_orderが小さい）
                cursor.execute("""
                    SELECT id, display_order
                    FROM customer_field_options
                    WHERE store_code = %s AND field_key = %s 
                      AND display_order < %s
                    ORDER BY display_order DESC
                    LIMIT 1
                """, (store_code, field_key, current_order))
            else:  # down
                # 1つ下の項目（display_orderが大きい）
                cursor.execute("""
                    SELECT id, display_order
                    FROM customer_field_options
                    WHERE store_code = %s AND field_key = %s 
                      AND display_order > %s
                    ORDER BY display_order ASC
                    LIMIT 1
                """, (store_code, field_key, current_order))
            
            target = cursor.fetchone()
            if not target:
                # 移動できない（先頭or末尾）
                return {'success': True, 'message': 'これ以上移動できません'}
            
            target_id, target_order = target
            
            # 順序を入れ替え
            cursor.execute("""
                UPDATE customer_field_options
                SET display_order = %s
                WHERE id = %s
            """, (target_order, option_id))
            
            cursor.execute("""
                UPDATE customer_field_options
                SET display_order = %s
                WHERE id = %s
            """, (current_order, target_id))
            
            conn.commit()
            return {'success': True, 'message': '順序を変更しました'}
            
    except Exception as e:
        conn.rollback()
        print(f"Error moving field option: {e}")
        return {'success': False, 'message': f'エラーが発生しました: {str(e)}'}
    finally:
        conn.close()