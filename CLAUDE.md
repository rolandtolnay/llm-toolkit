# Project Conventions

- This is a skills repository. Files (commands, references, skills, etc.) belong in the project root, NOT in a `.claude` folder. Use `commands/`, `references/`, etc. at the top level.
- To install the toolkit, run `install.js` from the target project directory (or use `--global` for `~/.claude/`):
  - Default: symlinks into `./.claude/` of the current project (auto-updates with `git pull`)
  - `--global` installs to `~/.claude/` (all projects)
  - `--copy` copies files instead of symlinking (for team sharing via git)
  - `--uninstall` removes all toolkit files from the target scope
  - If the user just says "install the toolkit" without specifying, default to local (current project)
