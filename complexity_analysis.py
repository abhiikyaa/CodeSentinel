import git
import sqlite3
from radon.complexity import cc_visit

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

# Dono repos ke liye alag GitPython objects
repos = {
    "psf/requests": git.Repo("repos/requests"),
    "pallets/flask": git.Repo("repos/flask")
}

# changed_files table se saari files uthao, jinke saath unke PR ka repo_name aur sha bhi chahiye
cur.execute("""
    SELECT cf.id, cf.pr_id, cf.filename, pr.repo_name, pr.merge_commit_sha
    FROM changed_files cf
    JOIN pull_requests pr ON cf.pr_id = pr.pr_id
    WHERE pr.merge_commit_sha IS NOT NULL AND pr.merge_commit_sha != ''
""")
all_files = cur.fetchall()

print(f"Total {len(all_files)} files process karni hain...")

count = 0
skipped = 0

for file_id, pr_id, filename, repo_name, sha in all_files:
    try:
        repo = repos[repo_name]
        commit = repo.commit(sha)

        # File ka content nikalo us commit pe
        file_content = commit.tree[filename].data_stream.read().decode("utf-8")

        # Sirf .py files pe Radon chalega (baaki file types skip)
        if not filename.endswith(".py"):
            skipped += 1
            continue

        complexity_results = cc_visit(file_content)

        if complexity_results:
            total_complexity = sum(item.complexity for item in complexity_results)
            avg_complexity = total_complexity / len(complexity_results)
        else:
            avg_complexity = 0

        # Database mein is file ki row update karo
        cur.execute("""
            UPDATE changed_files
            SET complexity_score = ?
            WHERE id = ?
        """, (avg_complexity, file_id))

        count += 1
        if count % 100 == 0:
            print(f"Progress: {count} files done, {skipped} skipped")
            conn.commit()

    except Exception as e:
        skipped += 1
        continue

conn.commit()
conn.close()
print(f"Complete! {count} files processed, {skipped} skipped.")