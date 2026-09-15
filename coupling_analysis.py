import ast
import os
import sqlite3
import networkx as nx

def get_imports(file_path):
    """Ek Python file ke andar ke saare imports nikalta hai"""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports

# # Test — ek known file pe try karo
# test_imports = get_imports("repos/requests/src/requests/models.py")
# print(test_imports)

def get_all_py_files(repo_path):
    """Poore repo mein saari .py files dhoondta hai"""
    py_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                py_files.append(full_path)
    return py_files


def build_dependency_graph(repo_path):
    """Poore repo ka dependency graph banata hai"""
    py_files = get_all_py_files(repo_path)

    # Module-name se file-path ka mapping banao (jaise 'cookies' -> 'repos/requests/src/requests/cookies.py')
    module_to_file = {}
    for path in py_files:
        module_name = os.path.splitext(os.path.basename(path))[0]  # sirf filename, bina .py ke
        module_to_file[module_name] = path

    graph = nx.DiGraph()

    for path in py_files:
        graph.add_node(path)   # har file ek node hai

        imports = get_imports(path)
        for imp in imports:
            # Import ka last part lo (jaise 'requests.cookies' se 'cookies')
            imp_short = imp.split(".")[-1]

            # Agar ye import kisi internal file se match karta hai, edge banao
            if imp_short in module_to_file:
                target_file = module_to_file[imp_short]
                if target_file != path:   # khud ko import na kare
                    graph.add_edge(path, target_file)

    return graph

# ---- Ab dono repos ke graphs banate hain ----
graphs = {
    "psf/requests": build_dependency_graph(os.path.join("repos", "requests")),
    "pallets/flask": build_dependency_graph(os.path.join("repos", "flask"))
}

conn = sqlite3.connect("codesentinel.db")
cur = conn.cursor()

# changed_files table se saari files uthao, unke repo_name ke saath
cur.execute("""
    SELECT cf.id, cf.filename, pr.repo_name
    FROM changed_files cf
    JOIN pull_requests pr ON cf.pr_id = pr.pr_id
""")
all_files = cur.fetchall()

print(f"Total {len(all_files)} files process karni hain...")

count = 0
skipped = 0

for file_id, filename, repo_name in all_files:
    try:
        graph = graphs[repo_name]

        # filename database mein forward-slash se hai (GitHub se aaya), use OS path mein convert karo
        repo_folder = "requests" if repo_name == "psf/requests" else "flask"
        # GitHub ka filename repo ke andar ka relative path hota hai, jaise 'src/requests/models.py'
        possible_path = os.path.join("repos", repo_folder, *filename.split("/"))

        if possible_path in graph.nodes:
            coupling_score = graph.in_degree(possible_path)
        else:
            coupling_score = None   # file graph mein nahi mili (ho sakta hai delete ho gayi ho baad mein, ya non-.py file)

        cur.execute("""
            UPDATE changed_files
            SET coupling_score = ?
            WHERE id = ?
        """, (coupling_score, file_id))

        count += 1
        if count % 200 == 0:
            print(f"Progress: {count}/{len(all_files)} done, {skipped} not found")
            conn.commit()

    except Exception as e:
        skipped += 1
        continue

conn.commit()
conn.close()
print(f"Complete! {count} files processed, {skipped} errors.")