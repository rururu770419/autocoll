import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    PostgreSQLデータベースへの接続を取得
    
    Returns:
        connection: psycopg 接続オブジェクト
    """
    # 環境変数またはデフォルト値を使用
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # 接続を作成
    conn = psycopg.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,  # ← database → dbname に変更
        user=db_user,
        password=db_password
    )
    
    return conn