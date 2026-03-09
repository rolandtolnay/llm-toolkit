---
name: create-toolkit-installer
description: >
  Generate install.js for Claude Code toolkit repos with manifest tracking,
  symlink/copy modes, and uninstall support. Use when creating a new distributable
  collection of commands, skills, agents, or references.
---

<essential_principles>

- **Symlink-first, local-first.** Default mode is symlinks into `./.claude/` of the current project. `--copy` and `--global` are opt-in overrides. This means `git pull` in the toolkit repo auto-updates all installations.
- **Skills get directory-level symlinks.** Each skill directory becomes one symlink in link mode (not per-file). Everything else (commands, agents, references) uses individual file symlinks.
- **Unmanaged target paths are conflicts.** Pre-existing files, directories, or symlinks at install destinations must be treated as conflicts, even on a fresh install. Never silently replace user-owned `.claude/` content in non-interactive mode.
- **INSTALLABLE_DIRS drives everything.** A single array constant at the top of the script controls file collection, migration scanning, install counts, orphan protection, and summary output. Adding or removing a directory is a one-line change.
- **Manifest per toolkit.** Each toolkit stores its manifest in `<target>/<toolkit-name>/.manifest.json`. Multiple toolkits coexist at the same target without collision.

</essential_principles>

<process>

## Step 1: Detect project structure

Scan the current project root for installable content directories:
- `agents/` — subagent configurations
- `commands/` — slash commands
- `skills/` — auto-activating skills
- `references/` — reference documents

Only include directories that exist and contain files. These become the `INSTALLABLE_DIRS` array.

If the project has files that need remapping (e.g., a file at root that should install into `references/`), note this — but prefer moving the source file into the correct directory rather than adding special-case mappings. The template assumes source structure mirrors install structure.

## Step 2: Gather configuration

Determine from project context or ask the user:

1. **Toolkit name** — kebab-case identifier for the manifest directory (e.g., `flutter-llm-toolkit`). Usually matches the repo name.
2. **Repo URL** — GitHub clone URL for help text examples.
3. **Clone directory name** — what users name the local clone (e.g., `my-toolkit`). Usually matches the repo name.
4. **Description** — one-line description for help text (e.g., `Flutter/Dart skills and commands for Claude Code`).
5. **Legacy name** — if this toolkit was renamed from something else, the old name enables manifest migration. Otherwise `null`.

## Step 3: Generate install.js

Read `references/install-script-reference.md` for the complete template and gotchas.

1. Copy the template from the "Complete Template" section
2. Set the 6 configuration constants at the top:
   - `TOOLKIT_NAME` — from step 2
   - `TOOLKIT_DESCRIPTION` — from step 2
   - `REPO_URL` — from step 2
   - `REPO_CLONE_NAME` — from step 2
   - `INSTALLABLE_DIRS` — from step 1
   - `LEGACY_MANIFEST_DIR_NAME` — from step 2 (or `null`)
3. No other changes needed — the rest of the script adapts via these constants

Write `install.js` at the project root. Run `chmod +x install.js` to make it executable.

## Step 4: Verify installer behavior

Run smoke tests in a disposable project directory before considering the installer done:

1. **Install + uninstall in link mode** — confirm skills uninstall by removing only the skill symlink root, not files inside the source repo.
2. **Broken legacy symlink migration** — create a stale symlink under an installable directory and confirm install still succeeds.
3. **Unmanaged target collision** — create a pre-existing `.claude/...` file or symlink and confirm non-interactive install stops unless the user runs interactively or passes `--force`.

## Step 5: Generate documentation

### README Quick Start section

Adapt this template (replace `REPO_URL`, `REPO_CLONE_NAME` with actual values):

```markdown
## Quick start

Requires Node.js 16.7+ and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Clone once, install anywhere:**

\```bash
git clone REPO_URL ~/toolkits/REPO_CLONE_NAME
\```

**Install into a project** (default — symlinks into `./.claude/`):

\```bash
cd your-project
~/toolkits/REPO_CLONE_NAME/install.js
\```

**Install globally** (available in all projects):

\```bash
~/toolkits/REPO_CLONE_NAME/install.js --global
\```

**Copy mode** (for team sharing via git):

\```bash
cd your-project
~/toolkits/REPO_CLONE_NAME/install.js --copy
\```

**Uninstall:**

\```bash
cd your-project
~/toolkits/REPO_CLONE_NAME/install.js --uninstall
\```

Symlinks are the default — a `git pull` in the toolkit repo updates all installations automatically. Use `--copy` when you need to commit the files into your project. Not supported on Windows (use `--copy`).
```

### CLAUDE.md install snippet

Add to the project's CLAUDE.md under conventions:

```markdown
- To install the toolkit, run `install.js` from the target project directory (or use `--global` for `~/.claude/`):
  - Default: symlinks into `./.claude/` of the current project (auto-updates with `git pull`)
  - `--global` installs to `~/.claude/` (all projects)
  - `--copy` copies files instead of symlinking (for team sharing via git)
  - `--uninstall` removes all toolkit files from the target scope
```

</process>

<reference_index>

Supporting files in `references/`:
- `install-script-reference.md` — complete install.js template, configuration constants table, architecture overview, and 14 gotchas from production use. Read before generating the script.

</reference_index>

<success_criteria>

- [ ] Template used verbatim from reference — no manual modifications to universal logic
- [ ] install.js uses INSTALLABLE_DIRS constant to drive all directory-dependent behavior (no hardcoded directory lists elsewhere)
- [ ] `chmod +x install.js` run after writing the file
- [ ] install.js smoke-tested for link-mode install/uninstall, broken legacy symlink migration, and unmanaged target collisions
- [ ] CLAUDE.md snippet generated with install instructions
- [ ] README Quick Start section generated with correct repo URL and clone name
- [ ] Configuration constants at top match the detected project structure and user-provided values

</success_criteria>
