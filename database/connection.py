import psycopg
from psycopg.rows import dict_row
from flask import g

# PostgreSQL接続設定を読み込み
from config import DATABASE_CONFIG

DB_PATHS = {
    "nagano": {"display_name": "Diary長野"},
    "isesaki": {"display_name": "Diary伊勢崎"},
    "globalwork": {"display_name": "グローバルワーク"},
}

class PostgreSQLConnectionWrapper:
    """
    PostgreSQL接続をSQLiteライクに使用するためのラッパークラス
    """
    def __init__(self, conn):
        self.conn = conn
        self.row_factory = None
        self.conn.autocommit = True
    
    def execute(self, query, params=()):
        """SQLiteライクなexecute()メソッド"""
        try:
            if 'rowid' in query.lower():
                query = query.replace('rowid', 'id').replace('ROWID', 'id')
                print(f"SQLite互換性: rowidをidに置き換えました")
            
            cursor = self.conn.cursor(row_factory=dict_row)
            cursor.execute(query, params)
            return cursor
        except Exception as e:
            print(f"SQL実行エラー: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            try:
                self.conn.rollback()
            except:
                pass
            raise
    
    def cursor(self):
        """通常のcursor()メソッド（dict_row対応）"""
        return self.conn.cursor(row_factory=dict_row)
    
    def commit(self):
        """commit()メソッド"""
        if not self.conn.autocommit:
            return self.conn.commit()
    
    def rollback(self):
        """rollback()メソッド"""
        if not self.conn.autocommit:
            return self.conn.rollback()
    
    def close(self):
        """close()メソッド"""
        return self.conn.close()

def get_db(store=None):
    """
    PostgreSQLデータベース接続を取得
    """
    try:
        conn = psycopg.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            dbname=DATABASE_CONFIG['database'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password']
        )
        
        return PostgreSQLConnectionWrapper(conn)
    except psycopg.Error as e:
        print(f"PostgreSQL接続エラー: {e}")
        return None

def get_connection():
    """
    標準的なPostgreSQL接続を取得（psycopg2互換用）
    customer_options_db.pyなどから使用される
    """
    try:
        conn = psycopg.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            dbname=DATABASE_CONFIG['database'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password']
        )
        return conn
    except psycopg.Error as e:
        print(f"PostgreSQL接続エラー: {e}")
        raise

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_display_name(store):
    return DB_PATHS.get(store, {}).get("display_name", store)

# ============================================
# 🆕 店舗ID取得関数
# ============================================

def get_store_id(store_code):
    """
    店舗コード（URL）から store_id を取得
    
    Args:
        store_code (str): 店舗コード ('nagano', 'isesaki', 'globalwork')
    
    Returns:
        int: store_id
    
    新店舗追加時は store_map に追加してください
    例：'ikebukuro': 4,
    """
    store_map = {
        'nagano': 1,
        'isesaki': 2,
        'globalwork': 3,
        # 新店舗追加時はここに追加
        # 例: 'ikebukuro': 4,
    }
    return store_map.get(store_code, 1)  # デフォルトは1（長野店）