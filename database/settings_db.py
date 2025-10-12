import psycopg
from psycopg.rows import dict_row
from database.db_connection import get_db_connection

def get_all_settings():
    """
    全設定を取得してカテゴリごとに分類
    
    Returns:
        dict: {
            'store_info': [...],
            'notification': [...],
            'auto_call': [...]
        }
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT * FROM store_settings 
            ORDER BY category, display_order
        """)
        
        all_settings = cur.fetchall()
        
        # カテゴリごとに分類
        categorized = {
            'store_info': [],
            'notification': [],
            'auto_call': []
        }
        
        for setting in all_settings:
            category = setting['category']
            if category in categorized:
                categorized[category].append(dict(setting))
        
        return categorized
        
    except Exception as e:
        print(f"Error in get_all_settings: {e}")
        return {
            'store_info': [],
            'notification': [],
            'auto_call': []
        }
    finally:
        cur.close()
        conn.close()


def get_setting(key):
    """
    特定のキーの設定値を取得
    
    Args:
        key (str): 設定キー（例: 'store_name', 'twilio_account_sid'）
    
    Returns:
        str: 設定値、存在しない場合はNone
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT setting_value FROM store_settings 
            WHERE setting_key = %s
        """, (key,))
        
        result = cur.fetchone()
        return result['setting_value'] if result else None
        
    except Exception as e:
        print(f"Error in get_setting: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def get_settings_by_category(category):
    """
    カテゴリごとの設定を取得
    
    Args:
        category (str): 'store_info', 'notification', 'auto_call'
    
    Returns:
        list: 設定のリスト
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT * FROM store_settings 
            WHERE category = %s
            ORDER BY display_order
        """, (category,))
        
        return [dict(row) for row in cur.fetchall()]
        
    except Exception as e:
        print(f"Error in get_settings_by_category: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def update_setting(key, value, updated_by=None):
    """
    設定値を更新
    
    Args:
        key (str): 設定キー
        value (str): 新しい設定値
        updated_by (str, optional): 更新者のログインID
    
    Returns:
        bool: 成功時True、失敗時False
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # チェックボックスの場合、'on'を'true'に変換
        if value == 'on':
            value = 'true'
        elif value == 'off' or value == '':
            # チェックボックスがOFFの場合、POSTデータに含まれないため''の場合もある
            cur.execute("""
                SELECT setting_type FROM store_settings WHERE setting_key = %s
            """, (key,))
            result = cur.fetchone()
            if result and result[0] == 'checkbox':
                value = 'false'
        
        if updated_by:
            cur.execute("""
                UPDATE store_settings 
                SET setting_value = %s, 
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = %s
                WHERE setting_key = %s
            """, (value, updated_by, key))
        else:
            cur.execute("""
                UPDATE store_settings 
                SET setting_value = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = %s
            """, (value, key))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error in update_setting: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def bulk_update_settings(settings_dict, updated_by=None):
    """
    複数の設定を一括更新
    
    Args:
        settings_dict (dict): {key: value, ...}
        updated_by (str, optional): 更新者のログインID
    
    Returns:
        tuple: (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    for key, value in settings_dict.items():
        if update_setting(key, value, updated_by):
            success_count += 1
        else:
            error_count += 1
    
    return success_count, error_count


def get_twilio_config():
    """
    Twilio設定をまとめて取得（オートコール用）
    
    Returns:
        dict: {
            'account_sid': str,
            'auth_token': str,
            'phone_number': str,
            'enabled': bool
        }
    """
    return {
        'account_sid': get_setting('twilio_account_sid'),
        'auth_token': get_setting('twilio_auth_token'),
        'phone_number': get_setting('twilio_phone_number'),
        'enabled': get_setting('auto_call_enabled') == 'true'
    }


def get_line_config():
    """
    LINE Notify設定をまとめて取得（通知用）
    
    Returns:
        dict: {
            'token': str,
            'enabled': bool,
            'message_template': str
        }
    """
    return {
        'token': get_setting('line_notify_token'),
        'enabled': get_setting('line_notify_enabled') == 'true',
        'message_template': get_setting('line_message_template')
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# カード手数料管理関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_card_fee_rate(store_id=None):
    """
    カード手数料率を取得
    
    Args:
        store_id (int, optional): 店舗ID（将来の拡張用、現在は未使用）
    
    Returns:
        float: カード手数料率（デフォルト: 5.0）
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        cur.execute("""
            SELECT setting_value
            FROM store_settings
            WHERE setting_key = 'card_fee_rate'
            LIMIT 1
        """)
        
        result = cur.fetchone()
        
        if result and result['setting_value']:
            return float(result['setting_value'])
        else:
            return 5.0
            
    except Exception as e:
        print(f"Error in get_card_fee_rate: {e}")
        return 5.0
    finally:
        cur.close()
        conn.close()


def save_card_fee_rate(store_id, rate, updated_by=None):
    """
    カード手数料率を保存
    
    Args:
        store_id (int): 店舗ID（将来の拡張用、現在は未使用）
        rate (float): カード手数料率（0〜100）
        updated_by (str, optional): 更新者のログインID
        
    Returns:
        bool: 成功したらTrue
    """
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        # 既存レコードの存在確認
        cur.execute("""
            SELECT setting_id
            FROM store_settings
            WHERE setting_key = 'card_fee_rate'
            LIMIT 1
        """)
        existing = cur.fetchone()
        
        if existing:
            # 更新
            if updated_by:
                cur.execute("""
                    UPDATE store_settings
                    SET setting_value = %s,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = %s
                    WHERE setting_key = 'card_fee_rate'
                """, (str(rate), updated_by))
            else:
                cur.execute("""
                    UPDATE store_settings
                    SET setting_value = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = 'card_fee_rate'
                """, (str(rate),))
        else:
            # 新規作成
            cur.execute("""
                INSERT INTO store_settings (
                    setting_key,
                    setting_value,
                    setting_name,
                    category,
                    setting_type,
                    display_order,
                    created_at,
                    updated_at
                )
                VALUES (
                    'card_fee_rate',
                    %s,
                    'カード手数料率',
                    'payment',
                    'number',
                    100,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """, (str(rate),))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error in save_card_fee_rate: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()