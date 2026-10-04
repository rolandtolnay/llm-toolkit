# Local setup

This skill uses the official ElevenLabs CLI plus `uv` for explicit env-file loading. FFmpeg/ffprobe are needed only for video assembly and audio validation. No MCP server, SDK wrapper or background service is required.

## Tools and installation

On macOS, with permission to install missing packages:

```bash
brew install elevenlabs/tap/elevenlabs
# Only if missing and video work is needed:
brew install ffmpeg
```

Verify `elevenlabs --version`, `uv --version`, `ffmpeg -version` and `ffprobe -version`. The command examples were checked against ElevenLabs CLI 1.4.0; use installed `--help`/`--schema` if a later release changes a name. In this release the timing operation is `convert_with_timestamps`, with underscores.

Install the whole skill directory into the requested harness locations. Source lives in the toolkit; personal defaults and credentials do not. A Pi session needs `/reload` to discover a newly installed skill; restart Claude Code if it does not yet appear.

## Personal configuration

Use `~/.config/elevenlabs/` with directory mode `700`. Create `defaults.json` there, substituting the user's selected voice:

```json
{
  "voice_id": "SELECTED_VOICE_ID",
  "model_id": "eleven_v4",
  "language_code": "en",
  "output_format": "mp3_44100_128"
}
```

These are ordinary nonsecret settings and may be read by the agent. Keep the selected voice out of shared skill source so another installation does not inherit someone else's narrator.

The user creates a restricted key in [ElevenLabs API-key settings](https://elevenlabs.io/app/settings/api-keys), enabling Text to Speech, Voices Read and User Read as needed. Apply a small key quota and leave automatic paid top-ups off. Key scope labels can change; diagnose a denied endpoint without granting unrelated permissions.

The user enters the key privately into an owner-only (`600`) file at `~/.config/elevenlabs/credentials.env`:

```dotenv
ELEVENLABS_API_KEY=your_actual_key
```

Do not ask for the key in chat or put its literal value in a terminal command. A private editor is sufficient; don't echo or read the populated file through agent tools. This file is plaintext, not an encrypted secret store or a sandbox against processes running as the user. Do not put unrelated variables in it.

The command prefix in `SKILL.md` uses `env -u ELEVENLABS_API_KEY` so a stale globally exported key cannot override the selected env file, and `uv run --no-project --env-file ...` so execution does not depend on a consumer project's Python environment. No shell profile changes are needed.

## Verification without synthesis

This check loads the credential but prints only whether a nonempty value is present. It never sends a request:

```bash
env -u ELEVENLABS_API_KEY uv run --no-project \
  --env-file "$HOME/.config/elevenlabs/credentials.env" -- python -c \
  'import os,sys; ok=bool(os.environ.get("ELEVENLABS_API_KEY")); print("Key configured" if ok else "Key missing"); sys.exit(0 if ok else 1)'
```

If missing, stop authenticated checks and give the user the file path to populate. If configured, use the account and selected-voice metadata commands in `SKILL.md`; `models list` can inspect advertised model capabilities. Keep output to the necessary fields. An inaccessible selected voice is not proof the key is invalid, and a visible voice is not proof synthesis will succeed. Authentication and discovery can be verified without audio generation; an end-to-end test requires a later generation request.

Don't use `say` as an access test: it generates audio. For offline command validation, use `--schema` or a dry run with a fake key in an isolated environment, never the user's key. CLI `--debug` prints HTTP requests and responses.

## Account constraints

- [Free-tier Voice Library restriction](https://elevenlabs.io/docs/overview/capabilities/voices): community voices require a paid plan for API synthesis. Inspect the selected voice's category; don't assume that website preview access grants API access.
- [Commercial use](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform): Free output is noncommercial; paid-period output remains usable under its license after cancellation. Check terms for special services rather than extending narration rights to everything.
- [Pricing](https://elevenlabs.io/pricing/api): API rates, Creative credits, voice multipliers and promotions may differ. Verify the account's meter before promising a dollar estimate. Key quotas are separate from subscription allowance.
- [Data use](https://elevenlabs.io/privacy-policy): opt out of model improvement before sensitive submissions. Training opt-out is not zero retention; don't promise private/offline synthesis or send an Enterprise-only logging flag as a privacy workaround.
- [V4](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4): voice compatibility and fine-tuning rollout can vary. V4 Turbo has a documented dialogue WebSocket path; don't assume it is interchangeable with V4 in ordinary file-generation commands.

For CLI installation/authentication changes use the [official CLI repository](https://github.com/elevenlabs/cli). The [API quickstart](https://elevenlabs.io/docs/quickstart) and [timestamp contract](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps) are the primary request/response references.
