# fix_blogpost_slug.py
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Get current schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs_blogpost';")
schema = cursor.fetchone()[0]

# 2. Modify schema: remove NOT NULL and UNIQUE from slug
new_schema = schema.replace("slug VARCHAR(255) NOT NULL UNIQUE", "slug VARCHAR(255)")

# 3. Recreate table
cursor.execute("ALTER TABLE jobs_blogpost RENAME TO jobs_blogpost_old;")
cursor.execute(new_schema)
cursor.execute("INSERT INTO jobs_blogpost SELECT * FROM jobs_blogpost_old;")
cursor.execute("DROP TABLE jobs_blogpost_old;")

conn.commit()
conn.close()

print("✅ jobs_blogpost.slug is now NULLable and non-unique!")