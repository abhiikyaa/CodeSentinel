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

# Database se saare PR numbers aur unke repo names nikalo
cur.execute("SELECT pr_id, repo_name FROM pull_requests")
all_prs = cur.fetchall()   # ye list of (pr_id, repo_name) tuples degi

print(f"Total {len(all_prs)} PRs ka SHA fetch karna hai...")

count = 0
for pr_id, repo_name in all_prs:
    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_id)

        # Merge commit SHA nikalo aur database update karo
        cur.execute("""
            UPDATE pull_requests
            SET merge_commit_sha = ?
            WHERE pr_id = ? AND repo_name = ?
        """, (pr.merge_commit_sha, pr_id, repo_name))

        count += 1
        if count % 50 == 0:
            print(f"Progress: {count}/{len(all_prs)} done")
            conn.commit()

    except Exception as e:
        print(f"Error on PR #{pr_id}: {e}")
        print("60 seconds wait kar raha hoon...")
        time.sleep(60)
        continue

conn.commit()
conn.close()
print("Saare SHA values update ho gaye!")