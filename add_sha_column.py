import sqlite3

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

cur.execute("ALTER TABLE pull_requests ADD COLUMN merge_commit_sha TEXT")

conn.commit()
conn.close()

print("merge_commit_sha column add ho gaya!")