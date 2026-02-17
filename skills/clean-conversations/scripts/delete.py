import json, os, sys, shutil

base = os.path.expanduser("~/.claude/projects")
report = json.loads("""$REPORT_JSON""")

deleted = 0
errors = []

for project_dir, info in report.items():
    project_path = os.path.join(base, project_dir)

    # Load sessions-index.json if present
    index_path = os.path.join(project_path, "sessions-index.json")
    index_data = None
    if os.path.isfile(index_path):
        try:
            with open(index_path) as f:
                index_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    for session_id in info["session_ids"]:
        # Delete JSONL file
        jsonl_path = os.path.join(project_path, session_id + ".jsonl")
        if os.path.isfile(jsonl_path):
            try:
                os.remove(jsonl_path)
                deleted += 1
            except OSError as e:
                errors.append(f"Failed to delete {jsonl_path}: {e}")

        # Delete companion directory
        companion = os.path.join(project_path, session_id)
        if os.path.isdir(companion):
            try:
                shutil.rmtree(companion)
            except OSError as e:
                errors.append(f"Failed to delete dir {companion}: {e}")

        # Remove from index
        if index_data and "entries" in index_data:
            index_data["entries"] = [
                e for e in index_data["entries"]
                if e.get("sessionId") != session_id
            ]

    # Write back cleaned index
    if index_data is not None:
        try:
            with open(index_path, "w") as f:
                json.dump(index_data, f, indent=2)
        except IOError as e:
            errors.append(f"Failed to write index {index_path}: {e}")

print(json.dumps({"deleted": deleted, "errors": errors}))
