# Project Conventions

- This is a skills repository. Files (commands, references, skills, etc.) belong in the project root, NOT in a `.claude` folder. Use `commands/`, `references/`, etc. at the top level.
- To install the toolkit, use `node install.js` with the appropriate flags:
  - `--global` installs to `~/.claude/` (all projects), `--local` installs to the current project's `.claude/`
  - `--link` uses symlinks instead of copies (so `git pull` auto-updates the installation)
  - If the user just says "install the toolkit" without specifying, ask whether they want global or local
