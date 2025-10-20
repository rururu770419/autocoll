from database.connection import get_db

db = get_db()
cursor = db.cursor()
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'customer_field_options'
    ORDER BY ordinal_position
""")
print("customer_field_options table structure:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row['column_name']:20} {row['data_type']:20} Nullable: {row['is_nullable']:3} Default: {row['column_default']}")
db.close()
