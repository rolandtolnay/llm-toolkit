# Claude Code Theme Reference

Color values extracted from the Claude Code v2.1.119 binary. Use this as a reference when building a Pi theme that matches Claude Code's visual style.

All values are `rgb(r,g,b)` format. Claude Code also supports `ansi:<colorName>` for ANSI-only themes.

## Active Theme: Default Dark

This is the default dark theme (no `/theme` override in settings). Values extracted from the compiled binary by matching `key:"rgb(r,g,b)"` patterns and identifying the dark theme by `text:rgb(255,255,255)` + warm Claude orange accent.

### Core UI

| Key | Value | Description |
|-----|-------|-------------|
| `text` | `rgb(255,255,255)` | Primary text color (white on dark) |
| `inverseText` | `rgb(0,0,0)` | Text on light/inverted backgrounds |
| `background` | `rgb(0,204,204)` | Accent background color (teal — used for highlights, not the terminal bg) |
| `inactive` | `rgb(153,153,153)` | Dimmed/disabled text, secondary labels |
| `subtle` | `rgb(80,80,80)` | Borders, separators, very low-emphasis elements |
| `promptBorder` | `rgb(136,136,136)` | Border around the user input area |
| `promptBorderShimmer` | `rgb(183,183,183)` | Animated shimmer on prompt border (active state) |
| `inactiveShimmer` | `rgb(193,193,193)` | Shimmer variant of inactive color |

### Agent Identity

| Key | Value | Description |
|-----|-------|-------------|
| `claude` | `rgb(215,119,87)` | Claude's signature color — used for the agent name label, logo, accents |
| `claudeShimmer` | `rgb(235,159,127)` | Shimmer/animation variant of the claude color |
| `briefLabelClaude` | `rgb(215,119,87)` | "Claude" label in brief/compact message view |
| `briefLabelYou` | `rgb(37,99,235)` | "You" label in brief/compact message view |
| `clawd_body` | `rgb(215,119,87)` | ASCII art cat mascot body color |
| `clawd_background` | `rgb(0,0,0)` | ASCII art cat mascot background |

### Functional Colors

| Key | Value | Description |
|-----|-------|-------------|
| `success` | `rgb(78,186,101)` | Success messages, completion indicators |
| `error` | `rgb(255,107,128)` | Error messages, failed operations |
| `warning` | `rgb(255,193,7)` | Warning messages, caution indicators |
| `warningShimmer` | `rgb(255,234,50)` | Shimmer variant for animated warnings |
| `suggestion` | `rgb(177,185,249)` | Suggested actions, hints, autocomplete |
| `remember` | `rgb(177,185,249)` | Memory/context persistence indicators |

### Mode Indicators

| Key | Value | Description |
|-----|-------|-------------|
| `permission` | `rgb(177,185,249)` | Permission request accent (lavender blue) |
| `permissionShimmer` | `rgb(207,215,255)` | Shimmer for permission prompts |
| `autoAccept` | `rgb(175,135,255)` | Auto-accept mode indicator (purple) |
| `planMode` | `rgb(72,150,140)` | Plan mode indicator (teal-green) |
| `fastMode` | `rgb(255,120,20)` | Fast mode indicator (orange) |
| `fastModeShimmer` | `rgb(255,165,70)` | Shimmer for fast mode |
| `merged` | `rgb(175,135,255)` | Merged/combined indicator (same purple as autoAccept) |
| `ide` | `rgb(71,130,200)` | IDE integration accent color |

### Message Backgrounds

| Key | Value | Description |
|-----|-------|-------------|
| `userMessageBackground` | `rgb(55,55,55)` | Background for user message blocks |
| `bashMessageBackgroundColor` | `rgb(65,60,65)` | Background for bash/command output blocks |
| `memoryBackgroundColor` | `rgb(55,65,70)` | Background for memory/context blocks |
| `bashBorder` | `rgb(253,93,177)` | Border around bash tool output (hot pink) |

### Diff Colors

| Key | Value | Description |
|-----|-------|-------------|
| `diffAdded` | `rgb(34,92,43)` | Background for added lines in diffs |
| `diffRemoved` | `rgb(122,41,54)` | Background for removed lines in diffs |
| `diffAddedDimmed` | `rgb(71,88,74)` | Dimmed variant of added-line background (context lines) |
| `diffRemovedDimmed` | `rgb(62,44,44)` | Dimmed variant of removed-line background (context lines) |
| `diffAddedWord` | `rgb(47,157,68)` | Inline word-level addition highlight |
| `diffRemovedWord` | `rgb(179,89,107)` | Inline word-level removal highlight |
| `diffAddedWordDimmed` | `rgb(50,160,80)` | Dimmed word-level addition |
| `diffRemovedWordDimmed` | `rgb(180,60,60)` | Dimmed word-level removal |

### Subagent Colors

Each subagent gets a distinct color from this palette. Used for status labels, borders, and spinners.

| Key | Value | Description |
|-----|-------|-------------|
| `red_FOR_SUBAGENTS_ONLY` | `rgb(220,38,38)` | Subagent color: red |
| `blue_FOR_SUBAGENTS_ONLY` | `rgb(37,99,235)` | Subagent color: blue |
| `green_FOR_SUBAGENTS_ONLY` | `rgb(22,163,74)` | Subagent color: green |
| `yellow_FOR_SUBAGENTS_ONLY` | `rgb(202,138,4)` | Subagent color: yellow |
| `purple_FOR_SUBAGENTS_ONLY` | `rgb(147,51,234)` | Subagent color: purple |
| `orange_FOR_SUBAGENTS_ONLY` | `rgb(234,88,12)` | Subagent color: orange |
| `pink_FOR_SUBAGENTS_ONLY` | `rgb(219,39,119)` | Subagent color: pink |
| `cyan_FOR_SUBAGENTS_ONLY` | `rgb(8,145,178)` | Subagent color: cyan |

### System Spinner

| Key | Value | Description |
|-----|-------|-------------|
| `claudeBlue_FOR_SYSTEM_SPINNER` | `rgb(87,105,247)` | Loading spinner primary color |
| `claudeBlueShimmer_FOR_SYSTEM_SPINNER` | `rgb(117,135,255)` | Loading spinner shimmer color |

### Rainbow (Progress Bars, Decorative)

Muted pastel palette used for progress indicators and decorative elements.

| Key | Value | Description |
|-----|-------|-------------|
| `rainbow_red` | `rgb(235,95,87)` | |
| `rainbow_red_shimmer` | `rgb(250,155,147)` | |
| `rainbow_orange` | `rgb(245,139,87)` | |
| `rainbow_orange_shimmer` | `rgb(255,185,137)` | |
| `rainbow_yellow` | `rgb(250,195,95)` | |
| `rainbow_yellow_shimmer` | `rgb(255,225,155)` | |
| `rainbow_green` | `rgb(145,200,130)` | |
| `rainbow_green_shimmer` | `rgb(185,230,180)` | |
| `rainbow_blue` | `rgb(130,170,220)` | |
| `rainbow_blue_shimmer` | `rgb(180,205,240)` | |
| `rainbow_indigo` | `rgb(155,130,200)` | |
| `rainbow_indigo_shimmer` | `rgb(195,180,230)` | |
| `rainbow_violet` | `rgb(200,130,180)` | |
| `rainbow_violet_shimmer` | `rgb(230,180,210)` | |

### Rate Limit Indicator

| Key | Value | Description |
|-----|-------|-------------|
| `rate_limit_fill` | `rgb(87,105,247)` | Filled portion of rate limit bar |
| `rate_limit_empty` | `rgb(39,47,111)` | Empty portion of rate limit bar |

### Miscellaneous

| Key | Value | Description |
|-----|-------|-------------|
| `professionalBlue` | `rgb(106,155,204)` | Generic blue accent for professional/business contexts |
| `chromeYellow` | `rgb(251,188,4)` | Chrome/browser integration accent |

---

## All 6 Embedded Themes

Extracted from binary in definition order. Theme identification is inferred from `text` color and value patterns.

### Theme 1 — Light (default)

| Key | Value |
|-----|-------|
| `autoAccept` | `rgb(135,0,255)` |
| `bashBorder` | `rgb(255,0,135)` |
| `claude` | `rgb(215,119,87)` |
| `claudeShimmer` | `rgb(245,149,117)` |
| `permission` | `rgb(87,105,247)` |
| `planMode` | `rgb(0,102,102)` |
| `ide` | `rgb(71,130,200)` |
| `promptBorder` | `rgb(153,153,153)` |
| `text` | `rgb(0,0,0)` |
| `inverseText` | `rgb(255,255,255)` |
| `inactive` | `rgb(102,102,102)` |
| `subtle` | `rgb(175,175,175)` |
| `suggestion` | `rgb(87,105,247)` |
| `remember` | `rgb(0,0,255)` |
| `background` | `rgb(0,153,153)` |
| `success` | `rgb(44,122,57)` |
| `error` | `rgb(171,43,63)` |
| `warning` | `rgb(150,108,30)` |
| `merged` | `rgb(135,0,255)` |
| `diffAdded` | `rgb(105,219,124)` |
| `diffRemoved` | `rgb(255,168,180)` |
| `clawd_body` | `rgb(215,119,87)` |
| `clawd_background` | `rgb(0,0,0)` |
| `userMessageBackground` | `rgb(240,240,240)` |
| `bashMessageBackgroundColor` | `rgb(250,245,250)` |
| `memoryBackgroundColor` | `rgb(230,245,250)` |
| `fastMode` | `rgb(255,106,0)` |

### Theme 2 — Light (ANSI only)

All values use `ansi:<colorName>` format. See binary extraction for full mapping.

### Theme 3 — Dark (ANSI only)

All values use `ansi:<colorName>` format with `Bright` variants. See binary extraction for full mapping.

### Theme 4 — Light (colorblind-friendly)

| Key | Value |
|-----|-------|
| `autoAccept` | `rgb(135,0,255)` |
| `bashBorder` | `rgb(0,102,204)` |
| `claude` | `rgb(255,153,51)` |
| `claudeShimmer` | `rgb(255,183,101)` |
| `permission` | `rgb(51,102,255)` |
| `planMode` | `rgb(51,102,102)` |
| `text` | `rgb(0,0,0)` |
| `inverseText` | `rgb(255,255,255)` |
| `inactive` | `rgb(102,102,102)` |
| `subtle` | `rgb(175,175,175)` |
| `suggestion` | `rgb(51,102,255)` |
| `remember` | `rgb(51,102,255)` |
| `background` | `rgb(0,153,153)` |
| `success` | `rgb(0,102,153)` |
| `error` | `rgb(204,0,0)` |
| `warning` | `rgb(255,153,0)` |
| `diffAdded` | `rgb(153,204,255)` |
| `diffRemoved` | `rgb(255,204,204)` |
| `userMessageBackground` | `rgb(220,220,220)` |
| `bashMessageBackgroundColor` | `rgb(250,245,250)` |
| `memoryBackgroundColor` | `rgb(230,245,250)` |

### Theme 5 — Dark (default) ← YOUR ACTIVE THEME

| Key | Value |
|-----|-------|
| `autoAccept` | `rgb(175,135,255)` |
| `bashBorder` | `rgb(253,93,177)` |
| `claude` | `rgb(215,119,87)` |
| `claudeShimmer` | `rgb(235,159,127)` |
| `permission` | `rgb(177,185,249)` |
| `planMode` | `rgb(72,150,140)` |
| `ide` | `rgb(71,130,200)` |
| `promptBorder` | `rgb(136,136,136)` |
| `text` | `rgb(255,255,255)` |
| `inverseText` | `rgb(0,0,0)` |
| `inactive` | `rgb(153,153,153)` |
| `subtle` | `rgb(80,80,80)` |
| `suggestion` | `rgb(177,185,249)` |
| `remember` | `rgb(177,185,249)` |
| `background` | `rgb(0,204,204)` |
| `success` | `rgb(78,186,101)` |
| `error` | `rgb(255,107,128)` |
| `warning` | `rgb(255,193,7)` |
| `merged` | `rgb(175,135,255)` |
| `diffAdded` | `rgb(34,92,43)` |
| `diffRemoved` | `rgb(122,41,54)` |
| `diffAddedDimmed` | `rgb(71,88,74)` |
| `diffRemovedDimmed` | `rgb(62,44,44)` |
| `diffAddedWord` | `rgb(47,157,68)` |
| `diffRemovedWord` | `rgb(179,89,107)` |
| `diffAddedWordDimmed` | `rgb(50,160,80)` |
| `diffRemovedWordDimmed` | `rgb(180,60,60)` |
| `clawd_body` | `rgb(215,119,87)` |
| `clawd_background` | `rgb(0,0,0)` |
| `userMessageBackground` | `rgb(55,55,55)` |
| `bashMessageBackgroundColor` | `rgb(65,60,65)` |
| `memoryBackgroundColor` | `rgb(55,65,70)` |
| `fastMode` | `rgb(255,120,20)` |
| `fastModeShimmer` | `rgb(255,165,70)` |

### Theme 6 — Dark (colorblind-friendly)

| Key | Value |
|-----|-------|
| `autoAccept` | `rgb(175,135,255)` |
| `bashBorder` | `rgb(51,153,255)` |
| `claude` | `rgb(255,153,51)` |
| `claudeShimmer` | `rgb(255,183,101)` |
| `permission` | `rgb(153,204,255)` |
| `planMode` | `rgb(102,153,153)` |
| `text` | `rgb(255,255,255)` |
| `inverseText` | `rgb(0,0,0)` |
| `inactive` | `rgb(153,153,153)` |
| `subtle` | `rgb(80,80,80)` |
| `suggestion` | `rgb(153,204,255)` |
| `remember` | `rgb(153,204,255)` |
| `background` | `rgb(0,204,204)` |
| `success` | `rgb(51,153,255)` |
| `error` | `rgb(255,102,102)` |
| `warning` | `rgb(255,204,0)` |
| `diffAdded` | `rgb(0,68,102)` |
| `diffRemoved` | `rgb(102,0,0)` |
| `userMessageBackground` | `rgb(55,55,55)` |
| `bashMessageBackgroundColor` | `rgb(65,60,65)` |
| `memoryBackgroundColor` | `rgb(55,65,70)` |
| `fastMode` | `rgb(255,120,20)` |

---

## Extraction Method

Values extracted from the compiled Mach-O binary at `~/.local/share/claude/versions/2.1.119` using:

```bash
strings <binary> | grep -oP '[a-zA-Z_]+:"rgb\(\d+,\d+,\d+\)"' | sort -u
```

Theme groupings identified by tracking `autoAccept` as the first key in each theme definition block. Dark vs light determined by `text` color (black = light, white = dark). Theme 5 confirmed as active by matching your settings (no `/theme` override = default dark).

## Next Step

Read Pi's theme documentation (`docs/themes.md` in pi-mono) to understand Pi's theme key schema, then build a mapping from these Claude Code keys to Pi's equivalents.
