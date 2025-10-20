-- reservationsテーブルにdiscount_badge_nameカラムを追加

ALTER TABLE reservations
ADD COLUMN IF NOT EXISTS discount_badge_name VARCHAR(4);

-- 確認
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'reservations' AND column_name LIKE '%discount%'
ORDER BY ordinal_position;
