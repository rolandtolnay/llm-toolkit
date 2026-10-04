# Eleven v4 delivery

Distilled from the official [text-to-speech best practices](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices) and [Eleven v4](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4) pages; consult them when a technique here misfires. V4 follows tags and IPA well but not perfectly, and results vary by voice, so judge a delivery that matters on the generated audio.

## Spoken forms

The API's `apply_text_normalization` defaults to `auto`. Writing the spoken form removes the guesswork and settles choices the normalizer can't know, such as locale date order or a phone number read digit by digit.

| Written | Spoken |
|---|---|
| `$42.50`, `£1,001.32` | forty-two dollars and fifty cents, one thousand and one pounds and thirty-two pence |
| `555-555-5555` | five five five, five five five, five five five five |
| `2024-01-01`, `01/02/2023` | January first, twenty twenty-four; January second or the first of February, by the audience's locale |
| `14:30` | two thirty PM |
| `3.14`, `⅔`, `2nd` | three point one four, two-thirds, second |
| `100km`, `100%` | one hundred kilometers, one hundred percent |
| `Ctrl + Z` | control Z |
| `elevenlabs.io/docs` | eleven labs dot io slash docs |
| `Dr.`, `St.` | Doctor, Street (but Saint Patrick) |
| `XIV` | fourteen, or "the fourteenth" in a title |

Choose readings from context. Ask only when a wrong guess would be obvious to the audience, such as whether a product acronym is spelled out or said as a word.

## Pause, pace and emphasis

Ellipses add a pause and weight, dashes give a shorter break or an interruption, and paragraph breaks separate thoughts. `[short pause]` and `[long pause]` mark a deliberate beat. Capitals stress a word; frequent capitals make delivery sound shouted.

Pace comes from the voice and the writing: short sentences and ellipses slow delivery, dense clauses speed it up. To fit a fixed duration, edit the script. A small FFmpeg `atempo` adjustment is a fallback to mention to the user, not a silent fix.

## Audio tags

Place a tag immediately before the words it shapes, or after them for a reaction such as `[sighs]`. Square-bracketed text is direction and is not spoken, so never wrap the user's words in brackets or turn their existing prose into tags.

- **Delivery and emotion:** `[warm]`, `[curious]`, `[thoughtful]`, `[reassuring]`, `[excited]`, `[sarcastic]`, `[whispers]`. Descriptive compounds such as `[low, steady voice, restrained urgency]` or `[softly, with wonder]` are less ambiguous than single words.
- **Non-verbal:** `[sighs]`, `[exhales]`, `[laughs]`, `[chuckles]`, `[clears throat]`.
- **Sound effects and experiments:** `[applause]`, `[explosion]`, `[sings]` and `[strong X accent]` exist but are inconsistent across voices; use them when the user asks for that effect. Video sound effects belong in the mix rather than the voice track.
- **Not auditory:** stage directions such as `[standing]` or `[grinning]`, and `[music]`, don't direct the voice.

Tags land most reliably when the delivery is already in the voice's training data. A calm narrator won't shout convincingly, and a professional voice may not suit `[giggles]`. Explainer narration usually needs one register-setting tag per section and an occasional shift; dramatic reads and dialogue can carry more.

For multi-speaker scenes, give each speaker a distinct voice. `text-to-dialogue convert` takes `inputs` pairing each line with a voice ID and renders the exchange in one request; confirm the model it accepts with `--schema` and `models list` before relying on it.

## Pronunciation

**IPA:** V4 reads IPA wrapped in forward slashes inside double quotes, e.g. `The term "/ˌbaɪoʊˈkemɪstri/" refers to...`. Use standard symbols with primary (ˈ) and secondary (ˌ) stress marks, and wrap only the words that need control. The double quotes are part of the text, so let the JSON serializer escape them.

**Respelling:** when IPA misfires, try a phonetic spelling or emphasis through capitals and hyphens (`trapezIi`, `Cloffton` for "Claughton").

**Pronunciation dictionaries:** for names that recur across many generations, a dictionary applies replacements automatically through `pronunciation_dictionary_locators` (up to three per request). Use alias rules (`UN` → "United Nations"); phoneme rules target older models. Matching is case-sensitive and the first matching rule wins. Creating a dictionary is a separate API write, so do it when the user wants a reusable fix.

When a long narration depends on a pronunciation the user cares about, check that sentence in a short clip first: it costs less than regenerating the whole script.

## Worked example

Written script:

```text
Our Kubernetes add-on cuts deploy time by 40%. It's in v2.1 — read the docs at acme.dev/start.
```

Speech-ready text:

```text
[warm, conversational] Our "/ˌkuːbərˈnɛtiːz/" add-on cuts deploy time by forty percent.

It's in version two point one... read the docs at acme dot dev slash start.
```

The words and meaning are unchanged; the tag sets the register, the IPA fixes a commonly misread name, spoken forms replace the percentage, version and URL, and the paragraph break and ellipsis set the pauses.
