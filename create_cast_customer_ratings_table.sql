-- キャストの顧客評価テーブル
CREATE TABLE IF NOT EXISTS cast_customer_ratings (
    rating_id SERIAL PRIMARY KEY,
    cast_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    rating_value TEXT NOT NULL,
    store_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cast_id, customer_id, item_id, store_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_cast_customer_ratings_cast_customer
ON cast_customer_ratings(cast_id, customer_id, store_id);

CREATE INDEX IF NOT EXISTS idx_cast_customer_ratings_customer
ON cast_customer_ratings(customer_id, store_id);
