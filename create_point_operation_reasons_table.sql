-- ポイント操作理由テーブルの作成
CREATE TABLE IF NOT EXISTS point_operation_reasons (
    reason_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    reason_name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_point_operation_reasons_store_id ON point_operation_reasons(store_id);
CREATE INDEX IF NOT EXISTS idx_point_operation_reasons_display_order ON point_operation_reasons(store_id, display_order);

-- コメント追加
COMMENT ON TABLE point_operation_reasons IS 'ポイント操作理由マスタ';
COMMENT ON COLUMN point_operation_reasons.reason_id IS '理由ID';
COMMENT ON COLUMN point_operation_reasons.store_id IS '店舗ID';
COMMENT ON COLUMN point_operation_reasons.reason_name IS '理由名';
COMMENT ON COLUMN point_operation_reasons.display_order IS '表示順';
COMMENT ON COLUMN point_operation_reasons.is_active IS '有効フラグ';
COMMENT ON COLUMN point_operation_reasons.created_at IS '作成日時';
COMMENT ON COLUMN point_operation_reasons.updated_at IS '更新日時';
