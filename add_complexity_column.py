import sqlite3

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

cur.execute("ALTER TABLE changed_files ADD COLUMN complexity_score REAL")

conn.commit()
conn.close()

print("complexity_score column add ho gaya!")