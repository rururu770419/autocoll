-- 予約登録で使用する各テーブルのカラム名を確認

-- coursesテーブル
SELECT 'courses' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'courses'
ORDER BY ordinal_position;

-- castsテーブル
SELECT 'casts' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'casts'
ORDER BY ordinal_position;

-- nomination_typesテーブル
SELECT 'nomination_types' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'nomination_types'
ORDER BY ordinal_position;

-- extensionsテーブル
SELECT 'extensions' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'extensions'
ORDER BY ordinal_position;

-- meeting_placesテーブル
SELECT 'meeting_places' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'meeting_places'
ORDER BY ordinal_position;

-- hotelsテーブル
SELECT 'hotels' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'hotels'
ORDER BY ordinal_position;
