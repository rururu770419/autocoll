import os

# LINE Bot API設定
LINE_CHANNEL_ACCESS_TOKEN = "xB1EThS05kjozecebFAVcVv/Uruz62gMFvoVhOQSN9GrekSFoK8K3UekXvl1dhaGAixXqlSrTORU/pqQUgaKyr558OA3yagQ1eiVCI1oDozGXUbIshWtRCnketmv1Utxjn2qGOMxQ6jWPe1CAp6gwwdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "fce9b0b02f4d62f68b6d936cfbe06684"

# PostgreSQL接続設定
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pickup_system',
    'user': 'postgres',
    'password': 'diary8475ftkb'
}

# 通知設定
DEFAULT_NOTIFICATION_MINUTES = 10