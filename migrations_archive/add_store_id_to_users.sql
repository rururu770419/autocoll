-- usersテーブルにstore_idカラムを追加

-- 1. store_idカラムを追加
ALTER TABLE users ADD COLUMN IF NOT EXISTS store_id INTEGER;

-- 2. 既存データにstore_idを設定（デフォルトでnagano店 = 1）
UPDATE users SET store_id = 1 WHERE store_id IS NULL;

-- 3. NOT NULL制約を追加
ALTER TABLE users ALTER COLUMN store_id SET NOT NULL;

-- 4. インデックスを作成
CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id);

-- 5. 確認
SELECT id, login_id, name, role, store_id FROM users ORDER BY store_id, id;
