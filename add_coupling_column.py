import sqlite3

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

cur.execute("ALTER TABLE changed_files ADD COLUMN coupling_score INTEGER")

conn.commit()
conn.close()

print("coupling_score column add ho gaya!")