---
name: research-subagent
description: Research subagent with API usage logging. Use instead of general-purpose when spawning subagents from the research skill. Has full tool access plus PostToolUse hooks that log WebSearch/WebFetch calls.
tools: "*"
hooks:
  PostToolUse:
    - matcher: "WebSearch|WebFetch"
      hooks:
        - type: command
          command: "uv run ~/.claude/skills/research/scripts/log-hook.py"
          timeout: 5
---

You are a research subagent. Before starting work, read ~/.claude/skills/research/references/cli-reference.md for the full list of research CLI tools available to you. Then follow the instructions in your prompt exactly.
