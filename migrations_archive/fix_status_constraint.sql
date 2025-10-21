-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- reservations_status_check制約を削除または修正
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- まず現在の制約を確認
SELECT
    con.conname AS constraint_name,
    pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
INNER JOIN pg_class rel ON rel.oid = con.conrelid
INNER JOIN pg_namespace nsp ON nsp.oid = connamespace
WHERE nsp.nspname = 'public'
AND rel.relname = 'reservations'
AND con.contype = 'c';

-- 既存の制約を削除
ALTER TABLE reservations DROP CONSTRAINT IF EXISTS reservations_status_check;

-- 新しい制約を追加（日本語の値を許可）
ALTER TABLE reservations ADD CONSTRAINT reservations_status_check
    CHECK (status IN ('成約', 'キャンセル', '仮予約', '確定', '完了'));
