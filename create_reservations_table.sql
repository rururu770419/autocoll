-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 予約テーブル作成SQL
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 予約メインテーブル
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,

    -- 成約・キャンセル情報
    contract_type VARCHAR(20) NOT NULL DEFAULT 'contract', -- 'contract' or 'cancel'
    cancellation_reason_id INTEGER,

    -- 予約日時情報
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    reservation_datetime TIMESTAMP,  -- reservation_date + reservation_time の組み合わせ

    -- キャスト・スタッフ情報
    cast_id VARCHAR(50),
    staff_id INTEGER,

    -- 予約方法・指名情報
    reservation_method_id INTEGER,
    nomination_type_id INTEGER,

    -- コース・延長情報
    course_id INTEGER,
    extension_id INTEGER,

    -- 待ち合わせ・交通情報
    meeting_place_id INTEGER,
    transportation_fee INTEGER DEFAULT 0,

    -- ホテル情報
    hotel_id INTEGER,
    room_number VARCHAR(50),

    -- 支払い情報
    payment_method VARCHAR(20), -- 'cash' or 'card'
    total_amount INTEGER DEFAULT 0,

    -- ポイント情報
    pt_add INTEGER DEFAULT 0,
    pt_consume INTEGER DEFAULT 0,

    -- その他
    comment TEXT,

    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外部キー制約
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (staff_id) REFERENCES users(id)
);

-- 予約オプション中間テーブル（予約とオプションの多対多関係）
CREATE TABLE IF NOT EXISTS reservation_options (
    reservation_option_id SERIAL PRIMARY KEY,
    reservation_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES customer_options(option_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_reservations_store_id ON reservations(store_id);
CREATE INDEX IF NOT EXISTS idx_reservations_customer_id ON reservations(customer_id);
CREATE INDEX IF NOT EXISTS idx_reservations_reservation_date ON reservations(reservation_date);
CREATE INDEX IF NOT EXISTS idx_reservations_cast_id ON reservations(cast_id);
CREATE INDEX IF NOT EXISTS idx_reservation_options_reservation_id ON reservation_options(reservation_id);

-- コメント追加
COMMENT ON TABLE reservations IS '予約情報を管理するテーブル';
COMMENT ON TABLE reservation_options IS '予約とオプションの関連を管理する中間テーブル';
