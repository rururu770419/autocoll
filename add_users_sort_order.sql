-- usersテーブルにsort_orderカラムを追加

-- 1. sort_orderカラムを追加（まだない場合）
ALTER TABLE users
ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;

-- 2. 既存のスタッフにsort_orderを設定（名前順）
WITH ranked_users AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY name) as new_order
    FROM users
    WHERE is_active = true
)
UPDATE users
SET sort_order = ranked_users.new_order
FROM ranked_users
WHERE users.id = ranked_users.id;

-- 3. インデックスを作成（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_users_sort_order ON users(sort_order);

-- 確認
SELECT id, name, sort_order
FROM users
WHERE is_active = true
ORDER BY sort_order;
