-- 延長マスタテーブル作成スクリプト

CREATE TABLE IF NOT EXISTS extensions (
    extension_id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    extension_minutes INTEGER NOT NULL,
    extension_fee INTEGER NOT NULL,
    back_amount INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    store_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_extensions_store_id ON extensions(store_id);
CREATE INDEX IF NOT EXISTS idx_extensions_sort_order ON extensions(sort_order);

-- コメント
COMMENT ON TABLE extensions IS '延長マスタテーブル - 各店舗の延長時間オプションを管理';
COMMENT ON COLUMN extensions.extension_id IS '延長ID（主キー）';
COMMENT ON COLUMN extensions.extension_name IS '延長名（例：30分延長）';
COMMENT ON COLUMN extensions.extension_minutes IS '延長時間（分単位）';
COMMENT ON COLUMN extensions.extension_fee IS '延長料金（円）';
COMMENT ON COLUMN extensions.back_amount IS 'キャストへのバック金額（円）';
COMMENT ON COLUMN extensions.is_active IS '有効/無効フラグ';
COMMENT ON COLUMN extensions.store_id IS '店舗ID';
COMMENT ON COLUMN extensions.sort_order IS '並び順';
COMMENT ON COLUMN extensions.created_at IS '作成日時';
COMMENT ON COLUMN extensions.updated_at IS '更新日時';
