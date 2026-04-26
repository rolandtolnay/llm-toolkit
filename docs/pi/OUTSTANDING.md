# Outstanding Questions: Pi Migration

Questions that couldn't be answered from the official documentation alone. These need web search, community research, or hands-on testing.

---

## High Priority (Blocks Getting Started)

### Q1: GPT 5.5 Provider Setup in Pi

**What we know:** Pi supports OpenAI as a provider via API key or ChatGPT Plus/Pro subscription. The `--model openai/gpt-5.5` flag should work.

**What we don't know:**
- Does GPT 5.5 work reliably with Pi's tool use system? Any model-specific quirks?
- Can you use a ChatGPT Plus/Pro subscription, or is an API key required?
- What thinking levels does GPT 5.5 support through Pi? Does it map to OpenAI's reasoning tokens?
- Are there any known issues with GPT 5.5 and Pi's 200-token system prompt? Does the model need more guidance than Claude?

**How to find out:** Web search for "pi coding agent gpt 5.5" and check Pi Discord. Also: hands-on testing.

---

### Q2: Reference Implementations of Subagent Extensions

**What we know:** The API surface for building subagents (RPC mode, tool registration, widget system) is fully documented. The video shows IndyDevDan's working subagent implementation.

**What we don't know:**
- Is IndyDevDan's subagent extension code available? The video mentioned "link in the description" for the codebase.
- Are there Pi packages on npm that provide subagent support? (`npm search keywords:pi-package`)
- What's the recommended approach for subprocess lifecycle management? (Process pool? Spawn per task? Cleanup on abort?)
- How do subagents handle cwd — do they inherit the parent's working directory?
- How do subagents interact with session persistence? Are their results saved?

**How to find out:** 
- Search npm for `pi-package` keyword packages
- Check Pi Discord #packages channel
- Search GitHub for `pi-coding-agent subagent extension`
- Check IndyDevDan's GitHub repos

---

### Q3: AGENTS.md Tuning for Non-Claude Models

**What we know:** Pi's system prompt is only 200 tokens. AGENTS.md is concatenated to provide project context.

**What we don't know:**
- GPT 5.5 may respond differently to instructions than Claude. Does the AGENTS.md need model-specific tuning?
- Are there best practices for writing AGENTS.md that works across multiple models?
- How does the 200-token base system prompt interact with a large AGENTS.md? Does it get truncated?
- Should the AGENTS.md include tool use instructions that Claude Code's 10K system prompt normally provides?

**How to find out:** Hands-on testing with GPT 5.5. Compare behavior with and without detailed AGENTS.md instructions.

---

## Medium Priority (Blocks Building Extensions)

### Q4: Extension Development Workflow

**What we know:** Extensions are TypeScript files loaded via jiti. `/reload` hot-reloads them.

**What we don't know:**
- How do you debug an extension? Is there a verbose/debug mode that shows extension errors?
- How do you access logs or console output from an extension?
- Does `--verbose` show extension-level information?
- What's the recommended development loop? Edit → `/reload` → test? Or restart?
- How do you handle extension errors gracefully? Does a crashing extension kill Pi?
- Are there extension examples beyond the README that show full working implementations?

**How to find out:**
- Check `docs/development.md` (we didn't read this one yet)
- Search Pi GitHub issues for "extension" + "debug"
- Check `examples/extensions/` directory in the Pi repo

---

### Q5: Pi Package Ecosystem — What Already Exists?

**What we know:** Pi packages are installable via `pi install npm:@foo/package` or `pi install git:github.com/user/repo`. There's a Discord channel for packages.

**What we don't know:**
- What packages exist that provide subagents, plan mode, or other CC-equivalent features?
- Is there a registry or curated list beyond npm search?
- How mature are third-party packages? Are any production-quality?
- What's the best practice: build your own extensions or install community packages?

**How to find out:**
- `npm search keywords:pi-package` 
- Check Pi Discord #packages channel
- Search GitHub for `pi-package`

---

### Q6: SDK-Based Subagents vs RPC Subagents

**What we know:** Two approaches exist — spawning `pi --mode rpc` subprocesses or using the TypeScript SDK (`createAgentSession`) in-process.

**What we don't know:**
- Which approach is recommended for what use case?
- What are the memory implications of in-process SDK subagents? (Each gets its own model context)
- Can SDK subagents share extensions with the parent?
- How does abort/cleanup work for each approach?
- Is there a limit to how many concurrent RPC subprocesses are practical?

**How to find out:** Hands-on testing and Pi Discord.

---

## Lower Priority (Nice to Have)

### Q7: Pi Performance with Different Models

**What we know:** Pi is model-agnostic. The video showed using Haiku, Flash, Sonnet.

**What we don't know:**
- How does Pi's minimal system prompt affect tool use accuracy across models?
- Are there models that struggle with Pi's tool calling format?
- Does the `thinkingBudgets` setting work with non-Anthropic models?
- What's the practical experience of using Pi daily with GPT 5.5 vs Claude?

**How to find out:** Community feedback on Discord, hands-on testing.

---

### Q8: Custom Provider Configuration for Non-Standard APIs

**What we know:** Custom providers can be added via `~/.pi/agent/models.json` or via `pi.registerProvider()` in extensions.

**What we don't know:**
- Full format of `models.json` for custom providers
- How to configure authentication for custom/self-hosted models
- Whether all OpenAI-compatible APIs work out of the box (e.g., local Ollama, vLLM)

**How to find out:** Check `docs/models.md` and `docs/custom-provider.md` (we haven't read these yet).

---

### Q9: Session Sharing and Collaboration

**What we know:** Sessions are JSONL files. `/export` creates HTML. `/share` creates a GitHub gist.

**What we don't know:**
- Can sessions be shared between team members? (Session portability)
- How do exported sessions handle sensitive content?
- Is there a way to import sessions from Claude Code?

**How to find out:** Testing and docs.

---

## Research Plan

| Question | Method | Priority |
|----------|--------|----------|
| Q1: GPT 5.5 setup | Web search + hands-on | High |
| Q2: Subagent reference code | GitHub/npm search | High |
| Q3: AGENTS.md for GPT 5.5 | Hands-on testing | High |
| Q4: Extension dev workflow | Read docs/development.md + testing | Medium |
| Q5: Package ecosystem | npm/Discord/GitHub search | Medium |
| Q6: SDK vs RPC subagents | Testing + Discord | Medium |
| Q7: Model performance | Community + testing | Low |
| Q8: Custom providers | Read unread docs | Low |
| Q9: Session sharing | Testing | Low |
