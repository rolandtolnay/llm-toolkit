---
name: agent-logs
description: Extract debug transcripts from subagents in the current conversation. Use when auditing subagent behavior, reviewing tool calls and errors, or creating logs for LLM-based prompt optimization.
disable-model-invocation: true
allowed-tools: [Bash, Read, Write, Glob, AskUserQuestion]
---

<objective>
Interactively extract formatted debug transcripts from selected subagents in the current conversation. The user picks which subagents to extract and what format for each. Output files go to `etc/audit/` in the project directory.
</objective>

<context>
- Conversation directory: !`echo $HOME/.claude/projects/$(pwd | tr '/' '-')`
- Parent JSONL: !`ls -t $HOME/.claude/projects/$(pwd | tr '/' '-')/*.jsonl 2>/dev/null | head -1`
- Subagent files: !`CONV_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-')"; SID=$(basename "$(ls -t "$CONV_DIR"/*.jsonl 2>/dev/null | head -1)" .jsonl); ls "$CONV_DIR/$SID/subagents/"*.jsonl 2>/dev/null || echo "NO_SUBAGENTS"`
- Transcript script: !`for p in "$HOME/.claude/skills/agent-logs/scripts/transcript.py" ".claude/skills/agent-logs/scripts/transcript.py"; do [ -f "$p" ] && echo "$p" && break; done`
- Project root: !`pwd`
</context>

<process>

## Step 1: Check for subagents

If "NO_SUBAGENTS" appears in context above, report "No subagents found in this conversation" and stop.

## Step 2: Set variables

From context:
- `PARENT_JSONL` = parent JSONL path
- `SESSION_ID` = basename without `.jsonl`
- `TRANSCRIPT_SCRIPT` = resolved transcript script path
- `OUTPUT_DIR` = `{project_root}/etc/audit`

## Step 3: Extract agent metadata from parent JSONL

Run this Python to build agentId-to-metadata mapping:

```python
python3 -c "
import json, re, sys
agent_calls, agent_id_map = {}, {}
for line in open(sys.argv[1]):
    try: obj = json.loads(line)
    except: continue
    msg = obj.get('message', {})
    content = msg.get('content', [])
    if not isinstance(content, list): continue
    for block in content:
        if not isinstance(block, dict): continue
        if msg.get('role') == 'assistant' and block.get('type') == 'tool_use' and block.get('name') == 'Agent':
            inp = block.get('input', {})
            agent_calls[block.get('id', '')] = {'description': inp.get('description', ''), 'type': inp.get('subagent_type', ''), 'prompt': inp.get('prompt', '')[:500]}
        if msg.get('role') == 'user' and block.get('type') == 'tool_result':
            rc = block.get('content', '')
            text = ' '.join(b.get('text','') for b in rc if isinstance(b,dict)) if isinstance(rc, list) else str(rc)
            m = re.search(r'agentId: (\S+)', text)
            if m: agent_id_map[m.group(1)] = block.get('tool_use_id', '')
result = {}
for aid, tuid in agent_id_map.items():
    if tuid in agent_calls: result[aid] = agent_calls[tuid]
print(json.dumps(result, indent=2))
" "$PARENT_JSONL"
```

Save output as `AGENT_META` JSON for later steps.

## Step 4: Build subagent summary list

For each subagent JSONL file found in context:

1. Extract agentId from filename: `basename <file> .jsonl | sed 's/^agent-//'`
2. Look up agentId in `AGENT_META` for description and type
3. Fallback if no match: read first user message from the subagent JSONL (second line, extract `message.content` first 200 chars) as description
4. Count JSONL lines as a rough size indicator

Build a numbered list like:
```
1. "explore codebase structure" (Explore) — 342 lines
2. "run test suite" (general-purpose) — 128 lines
```

## Step 5: Ask user which subagents to extract

Use `AskUserQuestion` with `selectionType: multi_select`. Each option: `"{description}" ({type}) — {line_count} lines`.

If the user selects none, report "No subagents selected" and stop.

## Step 6: Ask format per selected subagent

Use `AskUserQuestion` with `selectionType: single_select` for each selected subagent individually. Mention the agent description in the question. Options:

- **LLM-optimized** — Full detail, no truncation. Best for feeding to another LLM for analysis or prompt optimization.
- **Human-readable** — Formatted markdown with truncated results. Best for manual review of tool calls, responses, and reasoning.
- **Minified** — Compact one-liner per step. Quick overview of what happened and in what order.
- **Best judgment** — Let me pick the most useful format based on the agent's work.

**"Best judgment" heuristics:**
- Many tool calls (>20 steps) → minified (overview first)
- Errors in results → human (need to see error context)
- Research/explore agent types → llm (dense content best parsed by LLM)
- Short agents (<10 steps) → human (easy to read in full)
- Default fallback → human

To detect errors and step count for heuristics, scan the subagent JSONL for `"is_error": true` and count `"type": "tool_use"` blocks.

## Step 7: Generate transcripts

Create `mkdir -p $OUTPUT_DIR`. For each selected subagent, numbered sequentially (01, 02, ...):

**Script flags by format:**
- **LLM-optimized**: no extra flags (default)
- **Human-readable**: `--human --thinking 200 --max 500`
- **Minified**: `--minified`

Generate transcript:
```bash
python3 "$TRANSCRIPT_SCRIPT" <file> [flags]
```

Write `$OUTPUT_DIR/{NN}-{description-slug}.md`:
```
# Agent: {description}
**Type:** {type} | **ID:** {agentId} | **Format:** {format_name}

## Prompt
{prompt, first 500 chars}

---

{transcript output}
```

Sanitize description for filename: lowercase, spaces and special chars to hyphens, max 40 chars.

## Step 8: Report

List output files with sizes via `ls -lh $OUTPUT_DIR/`. Print the full output directory path.

</process>

<success_criteria>
- [ ] User selects which subagents to extract via multi-select
- [ ] User chooses format per subagent (or delegates to best judgment)
- [ ] One `.md` per selected subagent with metadata header + transcript in chosen format
- [ ] Agent description and type resolved from parent JSONL when available
- [ ] Files saved to `etc/audit/` in the project directory
- [ ] Files numbered `{NN}-{slug}.md` for scan order
</success_criteria>
