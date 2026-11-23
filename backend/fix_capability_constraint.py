#!/usr/bin/env python
"""Fix SQLite CHECK constraint for capability_status_records to allow 'loan_view'."""
import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Disable foreign keys temporarily
cursor.execute('PRAGMA foreign_keys=OFF')

# Enable schema writing
cursor.execute('PRAGMA writable_schema=1')

# Update the table definition
cursor.execute("""
UPDATE sqlite_master 
SET sql = REPLACE(
    sql, 
    "capability_name IN ('accounts_overview','saved_payees','payments','payment_status')", 
    "capability_name IN ('accounts_overview','saved_payees','payments','payment_status','loan_view')"
) 
WHERE name='capability_status_records' AND type='table'
""")

# Disable schema writing
cursor.execute('PRAGMA writable_schema=0')

# Re-enable foreign keys
cursor.execute('PRAGMA foreign_keys=ON')

# Verify integrity
result = cursor.execute('PRAGMA integrity_check').fetchone()
print(f"Integrity check: {result[0]}")

conn.commit()
conn.close()

print("✅ Successfully updated capability_status_records constraint to allow 'loan_view'")
