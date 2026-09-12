from github import Github
from dotenv import load_dotenv
import os
import sqlite3
import time

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
g = Github(token)

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

repo = g.get_repo("pallets/flask")
print(f"Connected to: {repo.full_name}")

pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

count = 0
for pr in pulls:
    try:
        if pr.merged:
            if "bot" in pr.user.login.lower():
                continue

            print(f"Saving PR #{pr.number}: {pr.title}")

            cur.execute("""
                INSERT OR IGNORE INTO pull_requests
                (pr_id, repo_name, title, author, created_at, merged_at, changed_files)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pr.number,
                repo.full_name,
                pr.title,
                pr.user.login,
                str(pr.created_at),
                str(pr.merged_at),
                pr.changed_files
            ))

            files = pr.get_files()
            for f in files:
                cur.execute("""
                    INSERT INTO changed_files (pr_id, filename, patch)
                    VALUES (?, ?, ?)
                """, (pr.number, f.filename, f.patch))

            count += 1
            if count % 50 == 0:
                print(f"Progress: {count} PRs processed so far...")
                conn.commit()  # har 50 PRs pe save kar do, taaki agar beech mein ruke toh data na khoye

    except Exception as e:
        print(f"Rate limit ya error hit hua: {e}")
        print("60 seconds wait kar raha hoon...")
        time.sleep(60)
        continue
conn.commit()
conn.close()
print("Data database mein save ho gaya!")