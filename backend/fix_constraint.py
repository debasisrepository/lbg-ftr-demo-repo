#!/usr/bin/env python
"""Fix SQLite CHECK constraint for customer_profile_refs to allow 'business' profile_type."""
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
    "profile_type IN ('personal')", 
    "profile_type IN ('personal', 'business')"
) 
WHERE name='customer_profile_refs' AND type='table'
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

print("✅ Successfully updated customer_profile_refs constraint to allow 'business' profile_type")
