-- reservationsテーブルにadjustment_amountカラムを追加

-- カラムが既に存在するかチェック
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reservations'
        AND column_name = 'adjustment_amount'
    ) THEN
        ALTER TABLE reservations
        ADD COLUMN adjustment_amount INTEGER DEFAULT 0;

        RAISE NOTICE '✅ adjustment_amountカラムを追加しました';
    ELSE
        RAISE NOTICE 'ℹ️ adjustment_amountカラムは既に存在します';
    END IF;
END $$;
