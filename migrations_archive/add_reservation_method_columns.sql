-- reservationsテーブルにreservation_method_idとreservation_method_nameカラムを追加

ALTER TABLE reservations
ADD COLUMN IF NOT EXISTS reservation_method_id INTEGER,
ADD COLUMN IF NOT EXISTS reservation_method_name VARCHAR(255);

-- 外部キー制約を追加（オプション）
-- ALTER TABLE reservations
-- ADD CONSTRAINT fk_reservation_method
-- FOREIGN KEY (reservation_method_id)
-- REFERENCES reservation_methods(method_id);
