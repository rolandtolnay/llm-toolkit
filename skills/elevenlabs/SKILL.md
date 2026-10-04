---
name: elevenlabs
description: Generate speech with ElevenLabs, prepare scripts for it, or add narration to a video. Use for voiceovers, voice selection, and ElevenLabs access or usage checks.
---

# ElevenLabs

Produce narration the user can accept on first listen, from their script or source material, using the official `elevenlabs` CLI. For video requests, deliver a new narrated video with the original preserved. Synthesis is hosted: submitted text leaves the machine.

## Access and defaults

Read `~/.config/elevenlabs/defaults.json` for the user's voice, model, language and audio format. Explicit request choices override these defaults; don't substitute a different voice or model to bypass an access failure. Missing setup: read `~/.agents/skills/elevenlabs/references/setup.md`.

Credentials live in `~/.config/elevenlabs/credentials.env`. Load them into the CLI process without reading or printing the file. Shell state doesn't carry between tool calls, so define `EL` in each command that uses it:

```bash
EL=(env -u ELEVENLABS_API_KEY uv run --no-project --env-file "$HOME/.config/elevenlabs/credentials.env" -- elevenlabs)
"${EL[@]}" user subscription get --query '{tier:tier,status:status,used:character_count,limit:character_limit}'
"${EL[@]}" voices get --voice-id "$VOICE_ID" --query '{id:voice_id,name:name,category:category,fine_tuning:fine_tuning.state,sharing:sharing.status}'
```

Set `VOICE_ID` from the nonsecret defaults. Account/voice metadata checks are useful when access is unknown or has changed; they do not prove synthesis permission, model compatibility or commercial rights. Free accounts cannot use community Voice Library voices through the API. Report that restriction rather than upgrading the account or silently choosing another voice.

The key must reach only the ElevenLabs API over verified TLS: keep it out of chat, command arguments, logs, repository files and CLI debug output, and never combine it with `--base-url` or a dry run.

## Authorization and cost

A request to generate narration authorizes the necessary synthesis within the stated scope; a setup, browse, estimate or planning request does not. Use one take by default. Ask when a missing script decision, batch size, existing-audio treatment or paid expansion would materially change the result. Don't buy credits, change subscriptions or clone voices without a request for that action.

Count submitted characters, including planned retakes, and check available usage before a substantial batch. Credit balances are not universally character allowances: model and voice rates vary. Use current account pricing for monetary estimates, not hardcoded rates. Free-generated audio is noncommercial; upgrading later does not retroactively license it. When the output is for commercial use, establish paid-plan eligibility before generation.

## Writing for speech

On V4 the submitted text is the performance direction. There are no Style or Speed controls and no SSML, so wording, punctuation and audio tags set pace, emphasis and emotion. Turn the script into a speech-ready version before generating:

- Write for the ear: short sentences and paragraph breaks give natural rhythm. About 150–180 words per minute is a planning estimate for fitting a duration; the generated audio is the measurement.
- Write anything with more than one plausible reading in its intended spoken form: numbers, dates, times, currencies, units, symbols, URLs, abbreviations and version strings (`v2.1` → "version two point one").
- Create pauses with ellipses, dashes and paragraph breaks; V4 ignores `<break>` tags. Capitalize a word only for deliberate stress.
- Direct delivery with bracketed audio tags placed before the segment they shape, such as `[warm, measured]` or `[short pause]`. Describe the voice quality explicitly, because V4 can render an ambiguous tag as a sound effect. Keep narration tags vocal, match them to the voice's character, and add them where delivery should change rather than on every line. Emotion written as prose ("she said sadly") is spoken aloud; express it as a tag instead.
- For a name or term the model may mispronounce, write its IPA between slashes inside double quotes, such as `"/ˌkuːbərˈnɛtiːz/"`, with stress marks, or respell it phonetically.

The user's script is authoritative: add direction, spoken forms and pronunciation hints without changing its words or meaning, and mention substitutions a listener would notice. When writing from source material, ground concrete claims in it. For tag vocabulary, normalization patterns, pronunciation dictionaries and a worked example, read `~/.agents/skills/elevenlabs/references/v4-delivery.md`.

## Generation

Use the selected voice and explicit model. V4 accepts two voice settings: Stability (lower is more expressive and varied, higher more consistent) and Similarity (closer adherence to the reference voice, at some cost to naturalness). Keep the voice's stored settings unless a take calls for a change. Discover less-common parameters with the installed command's `--help` or `--schema` rather than guessing.

Write `request.json` with `text`, `model_id`, `language_code` and any changed `voice_settings` using a JSON serializer, which escapes the quotes, tags and IPA in the script and keeps narration text out of shell interpolation. The CLI rejects mixing `--json` with body-field flags; keep voice and output format as flags:

```bash
"${EL[@]}" text-to-speech convert \
  --voice-id "$VOICE_ID" --output-format "$OUTPUT_FORMAT" \
  --json - --no-retry --output narration.mp3 < request.json
```

V4 accepts up to 10,000 characters per request. Scene-sized clips make revisions cheaper, but a short continuous narration need not be fragmented. When splitting, break at paragraph boundaries and pass the neighbouring text as `previous_text`/`next_text` so delivery flows across clips.

Choose an unused output path before submitting. Preserve accepted audio and a small nonsecret record of the script, voice/model, settings, generation date and any returned request ID. Seeds don't guarantee identical regeneration. On an ambiguous timeout, check generation history if permitted before repeating a billed request. Stop on authorization or quota errors and report the actionable blocker.

For captions or precise synchronization, `text-to-speech convert_with_timestamps` accepts the same request parameters and returns JSON with `audio_base64`, `alignment` and `normalized_alignment`. Save the JSON to a file, decode its audio locally and group timing into readable caption cues whose text reads as the written script, without audio tags or spelled-out forms. Don't dump base64 into the conversation. Use forced alignment for an already-edited recording only when timing is requested.

## Video and completion

Use `ffprobe` to inspect streams and durations. Fit narration to the requested scene timing; don't silently crop speech or shorten the video. Preserve or duck existing ambience/music when that intent is clear; ask about competing dialogue or replacement when it isn't. Use FFmpeg to produce a separate output, copying the video stream when compatible and encoding the mixed audio as needed. A generic `-shortest` can truncate either track: choose padding, placement and duration deliberately.

Done means the requested files exist, decode successfully, have the intended streams and duration, and preserve the source. Check the final result with `ffprobe` and an FFmpeg decode; assess audible pronunciation/mix when playback or an audio-capable tool is available. Don't claim listening verification from metadata alone. Report output paths, any spoken-form or pronunciation choices the user should listen for, and any material validation gap, then stop; further takes are not automatic.

For capabilities beyond narration, consult the [official API index](https://elevenlabs.io/docs/llms.txt) and the matching CLI command help. Keep the work scoped to the request rather than provisioning agents or a media pipeline.
