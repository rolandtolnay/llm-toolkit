# Project Conventions

- This is a skills repository. Files (commands, references, skills, etc.) belong in the project root, NOT in a `.claude` folder. Use `commands/`, `references/`, etc. at the top level.
- To install the toolkit, follow the install prompt in the README's Quickstart — there is no installer script. If the user just says "install the toolkit" without specifying, default to project scope with symlinks.
- Source files reference their own scripts and references through `~/.agents/skills/<skill>/...` — a harness-neutral stand-in for "wherever this skill is installed". Keep authored files on this convention (never a personal folder path); installations adapt it to the user's harness(es) however fits their system. Exception: hook `command:` lines in Claude frontmatter use `~/.claude/...` because Claude Code executes them.
- Test commands should include transient `uv` dependencies when the repo does not declare them. For research-skill tests, use commands like `uv run --with pytest --with typer --with requests pytest skills/research/tests/test_youtube.py` rather than bare `uv run pytest ...`, because `pytest` is not available as a bare executable in this repo's uv environment.
- Skills with `disable-model-invocation: true` also need `agents/openai.yaml` setting `policy.allow_implicit_invocation: false` so Codex preserves the explicit-only behavior.
