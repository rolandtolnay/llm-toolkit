# Outstanding Research: Pi Migration

All questions resolved — see [research findings](../../Documents/Research/2026-04-26-pi-migration-outstanding/00-synthesis.md) for full details.

---

## 1. Prompt Engineering for Output Quality — RESOLVED

GPT 5.5 is actively harmed by process-heavy prompts. Pi's ~200-token default is a strength. Use AGENTS.md (append, not SYSTEM.md replace) with ~400 tokens covering: identity, outcome standards, tool use, git safety, presentation. Key behavioral differences documented. Template added to [onboarding.md](onboarding.md#gpt-55-agentsmd-template).

**Sources:** [OpenAI GPT-5.5 Prompt Guidance](https://developers.openai.com/api/docs/guides/prompt-guidance), [Codex CLI system prompt](https://github.com/openai/codex/blob/main/codex-rs/core/gpt-5.2-codex_prompt.md), [oh-my-pi system prompt](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/prompts/system/system-prompt.md)

---

## 2. Community Extensions: Trust & Coverage — RESOLVED

All four features have mature, actively-maintained community packages:

| Feature | Package | Stars | Weekly DLs | Last Release |
|---------|---------|-------|-----------|--------------|
| Subagents | `pi-subagents` (nicobailon) | 964 | 38K | Apr 26, 2026 |
| Plan Mode | `@plannotator/pi-extension` | — | 14K | Apr 24, 2026 |
| Ask User | `pi-ask-user` (edlsh) | 44 | — | Apr 7, 2026 |
| Web Search | `pi-web-access` (nicobailon) | 378 | 16K | Apr 4, 2026 |

Install commands and alternatives documented in [onboarding.md §8](onboarding.md#8-features-to-install).

---

## 3. Subagent Architecture (if building custom) — RESOLVED (moot)

Since §2 found install-ready packages, building custom is unnecessary. Architecture research preserved for reference: three patterns (SDK in-process, CLI process spawning, RPC subprocess), full protocol docs, concurrency limits. See [03-subagent-architecture.md](../../Documents/Research/2026-04-26-pi-migration-outstanding/03-subagent-architecture.md).

---

## 4. Pi-Native Capabilities Worth Adopting — RESOLVED

Daily drivers are extensions + model cycling + minimal prompt. Session branching, SYSTEM.md, mental models, and custom compaction are niche. Adoption order added to [onboarding.md §9](onboarding.md#9-pi-native-features-to-adopt).

---

## Deferred (answer through usage, not research)

These remain deferred — answer through hands-on use:

- **GPT 5.5 provider setup** — Pi's third-party provider docs cover this. Just try it.
- **Extension dev workflow** — Learn by building the first extension. Read `docs/development.md` when stuck.
- **Model performance across providers** — Empirical. Use it and see.
- **Custom provider config** — Covered in Pi docs. Only relevant if standard OpenAI provider doesn't work.
- **Session sharing** — Nice-to-have, not blocking.
