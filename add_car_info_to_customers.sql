-- customersテーブルにcar_infoカラムを追加するSQL
-- 実行方法: psql -U postgres -d pickup_system -f add_car_info_to_customers.sql

-- car_infoカラムを追加（車種・ナンバーなどを保存）
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS car_info VARCHAR(255) DEFAULT NULL;

-- street_addressとbuilding_nameカラムが存在しない場合は追加
-- (既存のaddress_detailカラムから移行する場合)
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS street_address VARCHAR(255) DEFAULT NULL;

ALTER TABLE customers
ADD COLUMN IF NOT EXISTS building_name VARCHAR(255) DEFAULT NULL;

-- 確認
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'customers'
AND column_name IN ('car_info', 'street_address', 'building_name')
ORDER BY column_name;
