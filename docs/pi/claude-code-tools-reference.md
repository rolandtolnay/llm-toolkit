# Claude Code Built-in Tools & Subagents Reference

Complete reference of every built-in tool and subagent type that ships with Claude Code. Use this to replicate equivalent capabilities in Pi.

---

## Built-in Tools

All built-in tools are available in every Claude Code session. The "deferred" distinction below refers to context optimization — deferred tools have their schemas lazy-loaded via ToolSearch to keep the base prompt small, but they are not missing or disabled. MCP tools (from external servers) are the only truly optional tools.

### Core Tools

The foundational tools that are always fully loaded in the system prompt with complete schemas.

#### Read

Read file contents from the local filesystem. Supports text files, images (PNG, JPG — rendered visually as Claude is multimodal), PDFs (with page ranges for large files), and Jupyter notebooks (.ipynb with all cells and outputs).

- **Parameters:**
  - `file_path` (required): Absolute path to the file
  - `offset` (optional): Line number to start reading from (for large files)
  - `limit` (optional): Number of lines to read
  - `pages` (optional): Page range for PDFs (e.g. "1-5", max 20 pages per request)
- **Output format:** `cat -n` style with line numbers starting at 1
- **Constraints:** Can only read files, not directories. Max 2000 lines by default.

#### Edit

Performs exact string replacements in files. The primary tool for modifying existing code.

- **Parameters:**
  - `file_path` (required): Absolute path to file
  - `old_string` (required): The exact text to find and replace (must be unique in the file)
  - `new_string` (required): The replacement text
  - `replace_all` (optional, default false): Replace all occurrences instead of just one
- **Constraints:** Fails if `old_string` is not unique in the file unless `replace_all` is true. Must Read a file before editing it. Preserves exact indentation.

#### Write

Create new files or completely overwrite existing ones. Prefer Edit for modifications — use Write only for new files or complete rewrites.

- **Parameters:**
  - `file_path` (required): Absolute path (must be absolute)
  - `content` (required): Full file content
- **Constraints:** Must Read existing files before overwriting. Never creates documentation/README files unless explicitly requested.

#### Bash

Execute shell commands and return output. The working directory persists between calls but shell state does not.

- **Parameters:**
  - `command` (required): The shell command to execute
  - `description` (required): Short active-voice description of what the command does
  - `timeout` (optional): Timeout in milliseconds (max 600,000 = 10 minutes, default 120,000 = 2 minutes)
  - `run_in_background` (optional): Run the command in the background, get notified on completion
- **Behavior:** Shell environment is initialized from the user's profile (bash or zsh). File paths with spaces must be double-quoted. Independent commands can be run in parallel via multiple Bash calls. Use `&&` for sequential dependent commands.

#### Agent

Spawn a subagent with its own context window to handle a delegated task. Each subagent runs independently and returns a single result message.

- **Parameters:**
  - `prompt` (required): Self-contained task description (the agent has no prior conversation context)
  - `description` (required): Short 3-5 word summary of the task
  - `subagent_type` (optional): Which agent type to use (see Subagent Types below)
  - `model` (optional): Model override — "sonnet", "opus", or "haiku"
  - `isolation` (optional): Set to "worktree" to run in an isolated git worktree copy
  - `run_in_background` (optional): Run agent in background, get notified on completion
- **Key behaviors:**
  - Subagents have NO memory of the parent conversation — prompts must be fully self-contained
  - Multiple independent agents can be launched in parallel (single message, multiple Agent calls)
  - Use `SendMessage` with the agent's returned ID to continue a previously spawned agent
  - Worktree isolation auto-cleans if no changes are made

#### Skill

Invoke a registered skill (slash command) within the main conversation. Skills are user-configured extensions that provide specialized capabilities.

- **Parameters:**
  - `skill` (required): Exact name of the skill from the available-skills list
  - `args` (optional): Arguments for the skill
- **Constraints:** Only invoke skills listed in the available-skills system reminder. Never guess or invent skill names.

#### ToolSearch

Searches for and loads deferred tool schemas when MCP tool search is enabled. When an MCP server exposes many tools, only tool names are loaded into context initially. ToolSearch fetches the full JSON schema for a specific tool so it can actually be called.

- **Parameters:**
  - `query` (required): Query string — `"select:Read,Edit,Grep"` for exact names, or keyword search
  - `max_results` (optional, default 5): Maximum number of results
- **Query forms:**
  - `"select:ToolA,ToolB"` — fetch exact tools by name
  - `"notebook jupyter"` — keyword search
  - `"+slack send"` — require "slack" in name, rank by remaining terms
- **Note:** This is specifically for MCP tools that use the tool search optimization. Built-in tools don't need ToolSearch to be usable.

#### ScheduleWakeup

Schedule when to resume work in `/loop` dynamic mode (self-pacing iterations of a recurring task).

- **Parameters:**
  - `delaySeconds` (required): Seconds from now to wake up (clamped to 60–3600 by runtime)
  - `reason` (required): One short sentence explaining the delay (shown to user)
  - `prompt` (required): The /loop prompt to fire on wake-up (pass same prompt each turn to continue loop; use sentinel `<<autonomous-loop-dynamic>>` for autonomous loops)
- **Cache-aware timing:** Anthropic prompt cache has a 5-minute TTL. Sleep under 270s to stay in cache, or 1200s+ to amortize the miss. Avoid 300s (worst of both). Default idle tick: 1200–1800s.

---

### Schema-Deferred Tools

These tools are available in every session but their full JSON schemas are loaded on demand via ToolSearch — only tool names appear in the base prompt to save context space. Functionally identical to core tools once loaded.

#### Glob

Find files based on pattern matching (e.g. `src/**/*.tsx`, `*.config.js`). Returns matching file paths. No permission required.

- **Note:** The official docs do not publish parameter schemas for any tool. Based on usage: takes a glob pattern string and returns matching paths. Commonly used in plan mode for codebase exploration.

#### Grep

Search for patterns in file contents. Returns matching lines with file paths and line numbers. No permission required.

- **Note:** The official docs do not publish parameter schemas. Based on usage: takes a regex or string pattern and optional path scope. Used alongside Glob for codebase exploration.

#### EnterPlanMode

Transition into plan mode for designing an implementation approach before writing code. In plan mode, the agent explores the codebase using read-only tools, designs an approach, and presents it for user approval.

- **Parameters:** None
- **When to use:** Non-trivial implementation tasks, multiple valid approaches, architectural decisions, multi-file changes, unclear requirements. Skip for trivial single-line fixes.
- **Behavior:** Requires user consent to enter. While in plan mode, the agent uses Glob, Grep, Read, and AskUserQuestion to explore and clarify, then calls ExitPlanMode when ready.

#### ExitPlanMode

Present a completed plan for user approval and exit plan mode. The plan must already be written to the plan file.

- **Parameters:**
  - `allowedPrompts` (optional): Array of prompt-based permissions needed to implement the plan (e.g. `{tool: "Bash", prompt: "run tests"}`)
- **Constraints:** Only use when planning implementation steps (not research). Don't use AskUserQuestion to ask "is this plan okay" — that's what ExitPlanMode does.

#### EnterWorktree

Create an isolated git worktree and switch the session into it. The worktree lives in `.claude/worktrees/` with a new branch based on HEAD.

- **Parameters:**
  - `name` (optional): Name for the new worktree (auto-generated if omitted)
  - `path` (optional): Path to an existing worktree to enter instead of creating new (mutually exclusive with `name`)
- **Constraints:** Must be in a git repo. Must not already be in a worktree. Only use when "worktree" is explicitly mentioned by user or project instructions.

#### ExitWorktree

Leave a worktree session created by EnterWorktree.

- **Parameters:**
  - `action` (required): `"keep"` (leave on disk) or `"remove"` (delete worktree and branch)
  - `discard_changes` (optional, default false): Required true for `"remove"` when worktree has uncommitted changes
- **Behavior:** Restores original working directory. Clears CWD-dependent caches. Only operates on worktrees created by EnterWorktree in the current session.

#### AskUserQuestion

Present multiple-choice questions to gather requirements or clarify ambiguity during execution.

- **Parameters:**
  - `questions` (required): Array of 1–4 questions, each with:
    - `question`: The question text
    - `header`: Short label displayed as chip/tag (max 12 chars)
    - `options`: 2–4 choices, each with `label`, `description`, and optional `preview` (markdown rendered in monospace box for visual comparison)
    - `multiSelect`: Whether multiple options can be selected
  - `answers`: User answers collected by the permission component
  - `annotations`: Optional per-question annotations from user
- **Behavior:** Users always get an automatic "Other" option for custom text input. Preview mode switches to side-by-side layout.

#### TaskCreate

Create a structured task for tracking work in the current session.

- **Parameters:**
  - `subject` (required): Brief actionable title in imperative form
  - `description` (required): What needs to be done
  - `activeForm` (optional): Present continuous form shown in spinner when in_progress (e.g. "Running tests")
  - `metadata` (optional): Arbitrary key-value metadata
- **Behavior:** All tasks start as `pending`. Use for 3+ step tasks, complex work, or when user requests it. Skip for trivial single tasks.

#### TaskUpdate

Update a task's status, details, or dependencies.

- **Parameters:**
  - `taskId` (required): Task ID
  - `status`: `"pending"`, `"in_progress"`, `"completed"`, or `"deleted"`
  - `subject`, `description`, `activeForm`, `owner`: Update task details
  - `addBlocks`: Task IDs that cannot start until this one completes
  - `addBlockedBy`: Task IDs that must complete before this one starts
  - `metadata`: Merge metadata keys (set key to null to delete)
- **Workflow:** `pending` → `in_progress` → `completed`. Only mark completed when fully done.

#### TaskGet

Retrieve full details for a specific task by ID.

- **Parameters:** `taskId` (required)
- **Returns:** subject, description, status, blocks, blockedBy

#### TaskList

List all tasks with summary info (id, subject, status, owner, blockedBy).

- **Parameters:** None

#### TaskStop

Kill a running background task by ID.

- **Parameters:** `task_id` (required)

#### TaskOutput (Deprecated)

Retrieve output from a running or completed background task.

- **Parameters:**
  - `task_id` (required)
  - `block` (optional, default true): Wait for completion
  - `timeout` (optional, default 30000ms, max 600000ms)
- **Note:** Prefer using Read on the output file path instead.

#### PushNotification

Send a desktop notification (and mobile push if Remote Control is connected).

- **Parameters:**
  - `message` (required): Under 200 characters, one line, no markdown. Lead with actionable info.
  - `status` (required): Must be `"proactive"`
- **When to use:** Only when there's a real chance the user has walked away and something is worth coming back for. Don't notify for routine progress.

#### CronCreate

Schedule a recurring or one-shot prompt within the current session.

- **Parameters:**
  - `cron` (required): Standard 5-field cron expression in local timezone (`M H DoM Mon DoW`)
  - `prompt` (required): The prompt to enqueue at each fire time
  - `recurring` (optional, default true): false = fire once then auto-delete
  - `durable` (optional): true = persist to `.claude/scheduled_tasks.json` and survive restarts
- **Behavior:** Jobs only fire while REPL is idle. Recurring tasks auto-expire after 7 days. Small deterministic jitter is added. Returns a job ID for CronDelete.
- **Tip:** Avoid :00 and :30 minute marks to reduce API thundering-herd effects.

#### CronDelete

Cancel a cron job by ID.

- **Parameters:** `id` (required): Job ID from CronCreate

#### CronList

List all cron jobs in the current session.

- **Parameters:** None

#### WebSearch

Search the web and return results with links.

- **Parameters:**
  - `query` (required): Search query (min 2 chars)
  - `allowed_domains` (optional): Only include results from these domains
  - `blocked_domains` (optional): Exclude results from these domains
- **Constraints:** Only available in the US. Must include a "Sources:" section with URLs in responses.

#### WebFetch

Fetch a URL, convert HTML to markdown, and process it with a prompt using a small fast model.

- **Parameters:**
  - `url` (required): Fully-formed valid URL (HTTP auto-upgraded to HTTPS)
  - `prompt` (required): What information to extract from the page
- **Behavior:** Read-only. 15-minute cache. Reports redirects for manual follow-up. Will fail for authenticated/private URLs. For GitHub URLs, prefer `gh` CLI via Bash.

#### LSP

Language Server Protocol operations for code intelligence. Requires LSP servers to be configured for the file type.

- **Parameters:**
  - `operation` (required): One of: `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`
  - `filePath` (required): Path to the file
  - `line` (required): 1-based line number
  - `character` (required): 1-based character offset

#### Monitor

Start a background monitor that streams stdout lines from a long-running script as notifications.

- **Parameters:**
  - `command` (required): Shell command/script — each stdout line is an event, exit ends the watch
  - `description` (required): Short human-readable description (shown in notifications)
  - `timeout_ms` (required): Kill after this deadline (default 300,000ms, max 3,600,000ms). Ignored when persistent.
  - `persistent` (required): true = run for session lifetime (no timeout). Use for log tails, PR monitoring. Stop with TaskStop.
- **Key patterns:**
  - Use `grep --line-buffered` in pipes to avoid buffering delays
  - Poll intervals: 30s+ for remote APIs, 0.5–1s for local checks
  - Always cover failure signatures, not just success (e.g. `grep -E "SUCCESS|FAILED|Error|Traceback"`)
  - Lines within 200ms are batched into a single notification
- **When NOT to use:** For single "tell me when X is ready" notifications, use `Bash` with `run_in_background` instead.

#### NotebookEdit

Insert, replace, or delete cells in Jupyter notebooks.

- **Parameters:**
  - `notebook_path` (required): Absolute path to .ipynb file
  - `new_source` (required): New cell content
  - `cell_id` (optional): ID of cell to edit (for insert: new cell placed after this)
  - `cell_type` (optional): `"code"` or `"markdown"` (required for insert)
  - `edit_mode` (optional): `"replace"` (default), `"insert"`, or `"delete"`

#### RemoteTrigger

Call the claude.ai remote-trigger API. OAuth token is added automatically.

- **Parameters:**
  - `action` (required): `"list"`, `"get"`, `"create"`, `"update"`, or `"run"`
  - `trigger_id` (optional): Required for get, update, run
  - `body` (optional): Required for create/update, optional for run

#### SendMessage

Send a message to a previously spawned subagent (resume it with full context) or to an agent team teammate.

- **Usage:** Call with `to` set to the agent's ID or name to continue it. This resumes the agent with all prior context, unlike a fresh Agent call.

#### TeamCreate (Experimental)

Create an agent team with multiple teammates. Each teammate is a separate agent process.

#### TeamDelete (Experimental)

Disband an agent team and clean up all teammate processes.

#### TodoWrite

Manages the session task checklist. **Available in non-interactive mode and the Agent SDK; interactive sessions use TaskCreate, TaskGet, TaskList, and TaskUpdate instead.** No permission required.

- This is a separate tool from the Task\* family — same purpose (progress tracking) but different execution contexts. If building a headless/SDK agent, this is the one to use. If building an interactive CLI, use the Task\* tools.

#### PowerShell

Execute PowerShell commands natively. Permission required. Opt-in via `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` env var or in `settings.json`.

- **Availability:** Rolling out progressively on Windows. On Linux/macOS/WSL, requires PowerShell 7+ (`pwsh` on PATH).
- **Windows behavior:** Auto-detects `pwsh.exe` (PS 7+) with fallback to `powershell.exe` (PS 5.1). Bash tool remains registered alongside it.
- **Shell selection:** Three settings control where PowerShell is used:
  - `"defaultShell": "powershell"` in settings.json — routes interactive `!` commands through PowerShell
  - `"shell": "powershell"` on individual command hooks — runs that hook in PowerShell
  - `shell: powershell` in skill frontmatter — runs command blocks in PowerShell
- **Preview limitations:** Profiles not loaded. No sandboxing on Windows. Git Bash still required to start Claude Code on Windows.
- **Working directory:** Same cwd reset behavior as Bash (resets if `cd` leaves project directory).

---

## Built-in Subagent Types

These are the `subagent_type` values built into Claude Code. Each runs in its own context window with a specific subset of tools.

### general-purpose

The default agent type when no `subagent_type` is specified. Full tool access for complex, multi-step tasks requiring both exploration and code changes. Use for researching complex questions, searching for code, and executing multi-step tasks.

- **Tools available:** All tools
- **When to use:** Open-ended tasks spanning multiple files, tasks that need both reading and writing, anything that doesn't fit a more specialized type

### Explore

Fast, read-only agent optimized for codebase exploration. Cannot edit, write, or create files. Use when you need to quickly find files by patterns, search code for keywords, or answer questions about how the codebase works.

- **Tools available:** All tools except Agent, ExitPlanMode, Edit, Write, NotebookEdit
- **Thoroughness levels:** Specify in the prompt — "quick" for basic searches, "medium" for moderate exploration, "very thorough" for comprehensive multi-location analysis
- **When to use:** Finding files, searching for patterns, understanding architecture, answering questions about existing code. Especially valuable when exploration would take 3+ queries.

### Plan

Software architect agent for designing implementation plans. Read-only — it identifies critical files, considers architectural tradeoffs, and returns step-by-step plans without making changes.

- **Tools available:** All tools except Agent, ExitPlanMode, Edit, Write, NotebookEdit
- **When to use:** Planning implementation strategy for a task before coding begins

### claude-code-guide

Answers questions about Claude Code itself — features, hooks, slash commands, MCP servers, settings, IDE integrations, keyboard shortcuts, the Agent SDK, and the Claude API / Anthropic SDK.

- **Tools available:** Bash, Read, WebFetch, WebSearch
- **When to use:** "Can Claude Code do X?", "How do I configure Y?", "Does the API support Z?"

### statusline-setup

Configures the Claude Code status line setting. Automatically invoked by the `/statusline` command.

- **Tools available:** Read, Edit
- **When to use:** Invoked automatically, not typically called directly

---

## Key Architectural Patterns

These patterns are worth replicating in any coding agent:

1. **Tool deferral / lazy-loading:** All tools are available, but only ~10 core tools have full schemas in the base prompt. The rest are deferred — only their names appear until ToolSearch loads the schema on demand. This keeps the base context small. Only MCP tools are truly optional/external.

2. **Subagent isolation:** Each subagent gets its own context window with no memory of the parent conversation. Prompts must be fully self-contained. This protects the main context from being flooded by exploration results.

3. **Parallel execution:** Multiple independent Agent calls or Bash calls can be dispatched in a single turn, running concurrently.

4. **Worktree isolation:** Agents can work in isolated git worktrees to avoid interfering with the main working tree. Auto-cleaned if no changes are made.

5. **Background execution:** Both Bash (`run_in_background`) and Agent (`run_in_background`) support async execution with completion notifications.

6. **Plan-then-execute:** EnterPlanMode/ExitPlanMode enforces a structured flow where the agent explores and proposes before writing code, requiring explicit user approval.

7. **Permission model:** Tools are categorized by risk. Some always require user approval (Bash, Edit, Write, WebFetch, WebSearch, Monitor, NotebookEdit, Skill). The user can pre-allow specific patterns.

8. **Monitor pattern:** Long-running processes are observed via Monitor (streaming) or Bash with `run_in_background` (one-shot completion), not polling loops.

9. **Task tracking:** TaskCreate/TaskUpdate provides structured progress tracking visible to the user, with dependency chains (blocks/blockedBy) for ordered execution.

10. **Cron scheduling:** In-session recurring prompts via CronCreate allow periodic checks without leaving the session. Jobs auto-expire after 7 days.
