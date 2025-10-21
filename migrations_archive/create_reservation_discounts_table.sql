-- reservation_discountsテーブルを作成（複数割引対応）

CREATE TABLE IF NOT EXISTS reservation_discounts (
    id SERIAL PRIMARY KEY,
    reservation_id INTEGER NOT NULL,
    discount_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (discount_id) REFERENCES discounts(discount_id) ON DELETE CASCADE
);

-- インデックスを作成
CREATE INDEX IF NOT EXISTS idx_reservation_discounts_reservation_id ON reservation_discounts(reservation_id);
CREATE INDEX IF NOT EXISTS idx_reservation_discounts_discount_id ON reservation_discounts(discount_id);
CREATE INDEX IF NOT EXISTS idx_reservation_discounts_store_id ON reservation_discounts(store_id);

-- 確認
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'reservation_discounts';
