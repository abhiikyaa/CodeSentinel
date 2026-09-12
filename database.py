import sqlite3

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS pull_requests (
    pr_id INTEGER PRIMARY KEY,
    repo_name TEXT,
    title TEXT,
    author TEXT,
    created_at TEXT,
    merged_at TEXT,
    changed_files INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS changed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pr_id INTEGER,
    filename TEXT,
    patch TEXT,
    FOREIGN KEY (pr_id) REFERENCES pull_requests(pr_id)
)
""")

conn.commit()
conn.close()
print("Database aur tables ban gaye!")