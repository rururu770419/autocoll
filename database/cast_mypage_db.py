# -*- coding: utf-8 -*-
"""
キャストマイページ用のデータベース操作関数（辞書形式対応版）
"""
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
import uuid


def get_cast_notices(db, store_id=1, limit=20):
    """
    キャスト向けお知らせ一覧を取得（ピン留め優先）
    
    Args:
        db: データベース接続
        store_id: 店舗ID（デフォルト=1）
        limit: 取得件数
    
    Returns:
        list: お知らせ一覧（辞書形式）
    """
    cursor = db.cursor(row_factory=dict_row)
    cursor.execute("""
        SELECT 
            notice_id,
            title,
            content,
            is_pinned,
            created_at,
            updated_at
        FROM cast_notices
        WHERE store_id = %s AND is_active = TRUE
        ORDER BY is_pinned DESC, created_at DESC
        LIMIT %s
    """, (store_id, limit))
    return cursor.fetchall()


def get_cast_notice_by_id(db, notice_id):
    """
    特定のお知らせ詳細を取得
    
    Args:
        db: データベース接続
        notice_id: お知らせID
    
    Returns:
        dict: お知らせ詳細
    """
    cursor = db.cursor(row_factory=dict_row)
    cursor.execute("""
        SELECT 
            notice_id,
            title,
            content,
            is_pinned,
            created_at,
            updated_at
        FROM cast_notices
        WHERE notice_id = %s AND is_active = TRUE
    """, (notice_id,))
    return cursor.fetchone()


def create_cast_notice(db, store_id, title, content, is_pinned=False):
    """
    お知らせを新規作成（管理者用）
    
    Args:
        db: データベース接続
        store_id: 店舗ID
        title: タイトル
        content: 本文（HTML）
        is_pinned: ピン留めフラグ
    
    Returns:
        int: 作成されたnotice_id
    """
    try:
        cursor = db.cursor(row_factory=dict_row)
        cursor.execute("""
            INSERT INTO cast_notices (store_id, title, content, is_pinned)
            VALUES (%s, %s, %s, %s)
            RETURNING notice_id
        """, (store_id, title, content, is_pinned))
        result = cursor.fetchone()
        db.commit()
        print(f"お知らせ作成成功: notice_id {result['notice_id']}")
        return result['notice_id']
    except Exception as e:
        print(f"お知らせ作成エラー: {e}")
        db.rollback()
        return None


def update_cast_notice(db, notice_id, title=None, content=None, is_pinned=None):
    """
    お知らせを更新（管理者用）
    
    Args:
        db: データベース接続
        notice_id: お知らせID
        title: タイトル（任意）
        content: 本文（任意）
        is_pinned: ピン留めフラグ（任意）
    
    Returns:
        bool: 成功/失敗
    """
    try:
        cursor = db.cursor()
        
        update_fields = []
        params = []
        
        if title is not None:
            update_fields.append("title = %s")
            params.append(title)
        
        if content is not None:
            update_fields.append("content = %s")
            params.append(content)
        
        if is_pinned is not None:
            update_fields.append("is_pinned = %s")
            params.append(is_pinned)
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(notice_id)
        
        query = f"UPDATE cast_notices SET {', '.join(update_fields)} WHERE notice_id = %s"
        cursor.execute(query, params)
        db.commit()
        print(f"お知らせ更新成功: notice_id {notice_id}")
        return True
        
    except Exception as e:
        print(f"お知らせ更新エラー: {e}")
        db.rollback()
        return False


def delete_cast_notice(db, notice_id):
    """
    お知らせを論理削除（管理者用）
    
    Args:
        db: データベース接続
        notice_id: お知らせID
    
    Returns:
        bool: 成功/失敗
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cast_notices
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE notice_id = %s
        """, (notice_id,))
        db.commit()
        print(f"お知らせ削除成功: notice_id {notice_id}")
        return True
    except Exception as e:
        print(f"お知らせ削除エラー: {e}")
        db.rollback()
        return False


# ==== ブログ下書き管理関数 ====

def get_cast_blog_drafts(db, cast_id, limit=50):
    """
    キャストのブログ下書き一覧を取得
    
    Args:
        db: データベース接続
        cast_id: キャストID
        limit: 取得件数（デフォルト=50）
    
    Returns:
        list: 下書き一覧（辞書形式）
    """
    cursor = db.cursor(row_factory=dict_row)
    cursor.execute("""
        SELECT 
            draft_id,
            title,
            content,
            image_paths,
            created_at,
            updated_at
        FROM cast_blog_drafts
        WHERE cast_id = %s AND is_active = TRUE
        ORDER BY updated_at DESC
        LIMIT %s
    """, (cast_id, limit))
    return cursor.fetchall()


def get_cast_blog_draft_by_id(db, draft_id, cast_id):
    """
    特定のブログ下書きを取得
    
    Args:
        db: データベース接続
        draft_id: 下書きID
        cast_id: キャストID（権限チェック用）
    
    Returns:
        dict: 下書き詳細
    """
    cursor = db.cursor(row_factory=dict_row)
    cursor.execute("""
        SELECT 
            draft_id,
            cast_id,
            title,
            content,
            image_paths,
            created_at,
            updated_at
        FROM cast_blog_drafts
        WHERE draft_id = %s AND cast_id = %s AND is_active = TRUE
    """, (draft_id, cast_id))
    return cursor.fetchone()


def create_cast_blog_draft(db, cast_id, title="", content="", image_paths=None):
    """
    ブログ下書きを新規作成
    
    Args:
        db: データベース接続
        cast_id: キャストID
        title: タイトル
        content: 本文
        image_paths: 画像パス（JSON配列）
    
    Returns:
        int: 作成されたdraft_id
    """
    try:
        import json
        cursor = db.cursor(row_factory=dict_row)
        
        image_paths_json = json.dumps(image_paths or [])
        
        cursor.execute("""
            INSERT INTO cast_blog_drafts (cast_id, title, content, image_paths)
            VALUES (%s, %s, %s, %s)
            RETURNING draft_id
        """, (cast_id, title, content, image_paths_json))
        
        result = cursor.fetchone()
        db.commit()
        print(f"ブログ下書き作成成功: draft_id {result['draft_id']}")
        return result['draft_id']
        
    except Exception as e:
        print(f"ブログ下書き作成エラー: {e}")
        db.rollback()
        return None


def update_cast_blog_draft(db, draft_id, cast_id, title=None, content=None, image_paths=None):
    """
    ブログ下書きを更新
    
    Args:
        db: データベース接続
        draft_id: 下書きID
        cast_id: キャストID（権限チェック用）
        title: タイトル（任意）
        content: 本文（任意）
        image_paths: 画像パス（任意）
    
    Returns:
        bool: 成功/失敗
    """
    try:
        import json
        cursor = db.cursor()
        
        update_fields = []
        params = []
        
        if title is not None:
            update_fields.append("title = %s")
            params.append(title)
        
        if content is not None:
            update_fields.append("content = %s")
            params.append(content)
        
        if image_paths is not None:
            update_fields.append("image_paths = %s")
            params.append(json.dumps(image_paths))
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([draft_id, cast_id])
        
        query = f"""
            UPDATE cast_blog_drafts 
            SET {', '.join(update_fields)} 
            WHERE draft_id = %s AND cast_id = %s
        """
        cursor.execute(query, params)
        db.commit()
        print(f"ブログ下書き更新成功: draft_id {draft_id}")
        return True
        
    except Exception as e:
        print(f"ブログ下書き更新エラー: {e}")
        db.rollback()
        return False


def delete_cast_blog_draft(db, draft_id, cast_id):
    """
    ブログ下書きを論理削除
    
    Args:
        db: データベース接続
        draft_id: 下書きID
        cast_id: キャストID（権限チェック用）
    
    Returns:
        bool: 成功/失敗
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cast_blog_drafts
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE draft_id = %s AND cast_id = %s
        """, (draft_id, cast_id))
        db.commit()
        print(f"ブログ下書き削除成功: draft_id {draft_id}")
        return True
    except Exception as e:
        print(f"ブログ下書き削除エラー: {e}")
        db.rollback()
        return False


# ==== セッション管理関数 ====

def create_cast_session(db, cast_id, ip_address=None, user_agent=None):
    """
    キャストセッションを作成
    
    Args:
        db: データベース接続
        cast_id: キャストID
        ip_address: IPアドレス
        user_agent: User-Agent
    
    Returns:
        str: session_id (UUID)
    """
    try:
        cursor = db.cursor()
        session_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO cast_sessions (session_id, cast_id, ip_address, user_agent)
            VALUES (%s, %s, %s, %s)
        """, (session_id, cast_id, ip_address, user_agent))
        db.commit()
        print(f"セッション作成成功: cast_id {cast_id}, session_id {session_id}")
        return session_id
    except Exception as e:
        print(f"セッション作成エラー: {e}")
        db.rollback()
        return None


def get_cast_session(db, session_id):
    """
    セッション情報を取得
    
    Args:
        db: データベース接続
        session_id: セッションID
    
    Returns:
        dict: セッション情報
    """
    cursor = db.cursor(row_factory=dict_row)
    cursor.execute("""
        SELECT 
            session_id,
            cast_id,
            login_at,
            last_activity,
            is_active
        FROM cast_sessions
        WHERE session_id = %s AND is_active = TRUE
    """, (session_id,))
    return cursor.fetchone()


def update_cast_session_activity(db, session_id):
    """
    セッションの最終アクティビティ時刻を更新
    
    Args:
        db: データベース接続
        session_id: セッションID
    
    Returns:
        bool: 成功/失敗
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cast_sessions
            SET last_activity = CURRENT_TIMESTAMP
            WHERE session_id = %s
        """, (session_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"セッション更新エラー: {e}")
        db.rollback()
        return False


def delete_cast_session(db, session_id):
    """
    セッションを無効化（ログアウト）
    
    Args:
        db: データベース接続
        session_id: セッションID
    
    Returns:
        bool: 成功/失敗
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cast_sessions
            SET is_active = FALSE
            WHERE session_id = %s
        """, (session_id,))
        db.commit()
        print(f"セッション無効化成功: session_id {session_id}")
        return True
    except Exception as e:
        print(f"セッション無効化エラー: {e}")
        db.rollback()
        return False


def cleanup_expired_sessions(db, hours=24):
    """
    期限切れセッションを削除（定期実行用）
    
    Args:
        db: データベース接続
        hours: 最終アクティビティから何時間で期限切れとするか
    
    Returns:
        int: 削除件数
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE cast_sessions
            SET is_active = FALSE
            WHERE last_activity < (CURRENT_TIMESTAMP - INTERVAL '%s hours')
            AND is_active = TRUE
            RETURNING session_id
        """, (hours,))
        deleted = cursor.fetchall()
        db.commit()
        print(f"期限切れセッション削除: {len(deleted)}件")
        return len(deleted)
    except Exception as e:
        print(f"セッションクリーンアップエラー: {e}")
        db.rollback()
        return 0