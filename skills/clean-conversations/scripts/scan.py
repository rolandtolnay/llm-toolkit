import json, os, sys, re

base = os.path.expanduser("~/.claude/projects")
if not os.path.isdir(base):
    print(json.dumps({"error": "No projects directory found"}))
    sys.exit(0)

LOCAL_CMD_RE = re.compile(r"<command-name>/(clear|exit|compact|resume|init|login|logout|status|config|help|model|cost|memory|doctor|bug|review|terminal-setup|listen|mcp|release-notes|permissions|approved-tools)</command-name>")
LOCAL_CMD_STDOUT_RE = re.compile(r"^<local-command-stdout>.*</local-command-stdout>$", re.DOTALL)

results = {}

for project_dir in sorted(os.listdir(base)):
    project_path = os.path.join(base, project_dir)
    if not os.path.isdir(project_path):
        continue

    jsonl_files = [f for f in os.listdir(project_path) if f.endswith(".jsonl")]
    if not jsonl_files:
        continue

    wasteful = []
    total = len(jsonl_files)

    for fname in jsonl_files:
        fpath = os.path.join(project_path, fname)
        has_real_content = False

        try:
            with open(fpath) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg_type = obj.get("type", "")

                    # Skip non-content types
                    if msg_type in ("file-history-snapshot", "progress", "summary", "system", "queue-operation", "custom-title"):
                        continue

                    # Assistant response = real content
                    if msg_type == "assistant":
                        has_real_content = True
                        break

                    # User messages need further classification
                    if msg_type == "user":
                        # Meta messages (system-injected) are not real
                        if obj.get("isMeta"):
                            continue

                        content = obj.get("message", {}).get("content", "")

                        # Array content (tool results) = real interaction
                        if isinstance(content, list):
                            has_real_content = True
                            break

                        # Local commands (/clear, /exit, etc.) are not real
                        if LOCAL_CMD_RE.search(content):
                            continue

                        # Local command stdout is not real
                        if LOCAL_CMD_STDOUT_RE.match(content):
                            continue

                        # Empty or whitespace-only content is not real
                        if not content.strip():
                            continue

                        # Anything else from user = real content
                        has_real_content = True
                        break

        except (IOError, OSError):
            continue

        if not has_real_content:
            session_id = fname.replace(".jsonl", "")
            wasteful.append(session_id)

    if wasteful:
        results[project_dir] = {
            "total": total,
            "wasteful": len(wasteful),
            "session_ids": wasteful
        }

print(json.dumps(results))
