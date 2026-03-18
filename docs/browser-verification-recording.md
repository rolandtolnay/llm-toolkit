# Browser Verification Recording Techniques

Reference for recording visual evidence when an AI agent verifies its own front-end work in a browser. Covers video recording, tracing, screenshot sequences, and practical skill patterns.

## Context

Claude Code "verification skills" drive a browser to test UI that was just built. Recording what was tested lets a human review the results after the fact. This document covers all viable approaches, their tradeoffs, and how to combine them into practical skills.

---

## Approach 1: Playwright Native Video Recording

Playwright records video directly from the browser compositor. Works fully headless — no display server or Xvfb needed.

### Configuration

**Per-context (standalone script):**

```js
const { chromium } = require("playwright");

const browser = await chromium.launch();
const context = await browser.newContext({
  recordVideo: {
    dir: "./videos/",
    size: { width: 1280, height: 720 },
  },
});

const page = await context.newPage();
// ... perform verification steps ...

await context.close(); // IMPORTANT: finalizes the video file
const videoPath = await page.video().path();
```

**Via test config (`playwright.config.ts`):**

```ts
export default defineConfig({
  use: {
    video: "retain-on-failure", // only saves when assertions fail
    // other options: 'on', 'off', 'on-first-retry'
  },
});
```

### Output

- Format: `.webm` (VP8/VP9) — always `.webm`, no native MP4 output
- Convert for Safari compatibility: `ffmpeg -i session.webm -c:v libx264 session.mp4`
- File is only fully written after `context.close()` — do not read before closing

### Tradeoffs

| Pros | Cons |
|------|------|
| Works fully headless, no Xvfb | Output is `.webm` only — needs ffmpeg for MP4 |
| Self-contained (just Node.js) | Requires a Node.js wrapper script |
| `retain-on-failure` controls disk usage | ~10-15% performance overhead |
| Captures animations and transitions | Video lifecycle must be managed manually in standalone scripts |

### Best when

The verification task involves animations, transitions, or loading states that screenshots would miss. Best default when the project already uses Playwright.

---

## Approach 2: Playwright Tracing

Traces capture far more than video: action timeline, DOM snapshots before/after each action, full network log (request + response headers and bodies), console output, and source locations. Packaged as a `.zip` archive.

### Usage

```js
const context = await browser.newContext();
await context.tracing.start({
  screenshots: true, // screenshot at every action
  snapshots: true, // DOM snapshot before/after each action
  sources: true, // source code locations
});

const page = await context.newPage();
// ... verification steps ...

await context.tracing.stop({ path: "trace.zip" });
```

### Viewing

```bash
# Local (no upload, no privacy concerns):
npx playwright show-trace trace.zip

# Online (uploads to Microsoft servers — avoid for proprietary code):
# Open https://trace.playwright.dev/ and upload the zip
```

### What traces capture that video cannot

- **DOM state**: Inspect the actual HTML/CSS at any step — see if an element exists, has the right text, correct classes
- **Network requests**: Full request/response headers and bodies — verify API calls succeeded
- **Console errors**: See if the UI produced JavaScript errors during verification
- **Timing**: Precise duration of each action

### Tradeoffs

| Pros | Cons |
|------|------|
| Richer than video — DOM inspection at every step | Not "visual" in the traditional sense — requires trace viewer |
| Captures network and console (invisible to video) | Non-technical reviewers may struggle with the viewer |
| Smaller file size than video | Online viewer uploads to third-party servers |
| No performance concerns about codecs | |

### Best when

Verifying that network requests succeed, no console errors occur, or DOM state is correct. Especially useful for form submissions, API integrations, and state management verification. **Combine with video** for the most complete evidence.

---

## Approach 3: Screenshot Sequence with Assertion Log

Take a screenshot at each verification step, pair it with a structured assertion result, then assemble into a reviewable artifact.

### Capture Pattern

```bash
#!/bin/bash
OUTDIR="./verification-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTDIR"

# At each step:
# 1. Take screenshot
agent-browser screenshot "$OUTDIR/step-001-load-page.png"
# 2. Log assertion
echo '{"step":1,"action":"load signup page","selector":"#signup-form","expected":"visible","passed":true}' >> "$OUTDIR/assertions.jsonl"

# Next step:
agent-browser type @email "test@example.com"
agent-browser click @submit
agent-browser screenshot "$OUTDIR/step-002-after-submit.png"
echo '{"step":2,"action":"submit form","expected":"redirect to /dashboard","passed":true}' >> "$OUTDIR/assertions.jsonl"
```

### Assembly Options

**MP4 from screenshot sequence (ffmpeg):**

```bash
# Requires: brew install ffmpeg
# Images must be numbered sequentially: step-001.png, step-002.png, ...
ffmpeg -framerate 2 -i "$OUTDIR/step-%03d.png" -c:v libx264 -pix_fmt yuv420p "$OUTDIR/filmstrip.mp4"
```

**Animated GIF (ImageMagick):**

```bash
# Requires: brew install imagemagick
convert -delay 100 -loop 0 "$OUTDIR/step-*.png" "$OUTDIR/filmstrip.gif"
# Note: GIF is limited to 256 colors — degrades quality for rich UIs
```

**HTML filmstrip (no dependencies):**

```bash
cat > "$OUTDIR/report.html" << 'HTMLEOF'
<!DOCTYPE html>
<html><head><style>
  body { font-family: system-ui; max-width: 900px; margin: 0 auto; padding: 20px; }
  .step { margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
  .step img { width: 100%; display: block; }
  .step .info { padding: 12px; background: #f8f8f8; }
  .pass { color: #16a34a; } .fail { color: #dc2626; font-weight: bold; }
</style></head><body>
<h1>Verification Report</h1>
<div id="steps"></div>
<script>
fetch('assertions.jsonl').then(r => r.text()).then(text => {
  const steps = text.trim().split('\n').map(JSON.parse);
  document.getElementById('steps').innerHTML = steps.map(s => `
    <div class="step">
      <img src="step-${String(s.step).padStart(3,'0')}-${s.action.replace(/\s+/g,'-')}.png"
           onerror="this.style.display='none'">
      <div class="info">
        <span class="${s.passed ? 'pass' : 'fail'}">${s.passed ? 'PASS' : 'FAIL'}</span>
        Step ${s.step}: ${s.action} — expected: ${s.expected}
      </div>
    </div>
  `).join('');
});
</script></body></html>
HTMLEOF
```

### Tradeoffs

| Pros | Cons |
|------|------|
| Assertions coupled to screenshots — most debuggable | No temporal continuity (animations invisible) |
| HTML report requires zero dependencies | Requires building a small report generator |
| GIF/MP4 can embed in PR comments or Slack | GIF color depth limited to 256 colors |
| Works reliably in any headless environment | |

### Best when

Step-by-step correctness matters more than smooth playback. Excellent for form flows, multi-page workflows, and any case where assertions should be documented alongside visual evidence.

---

## Approach 4: CDP Screencast (Direct Protocol)

Using Chrome DevTools Protocol directly for maximum control over video encoding.

### Usage with Puppeteer

```js
const puppeteer = require("puppeteer");

const browser = await puppeteer.launch();
const page = await browser.newPage();

// Native Puppeteer API (v22+):
const recorder = await page.screencast({ path: "recording.webm" });
// ... verification steps ...
await recorder.stop();
```

### Manual CDP approach

```js
const client = await page.createCDPSession();
const frames = [];

client.on("Page.screencastFrame", async ({ data, sessionId }) => {
  frames.push(Buffer.from(data, "base64"));
  await client.send("Page.screencastFrameAck", { sessionId });
});

await client.send("Page.startScreencast", {
  format: "jpeg",
  quality: 80,
  maxWidth: 1280,
  maxHeight: 720,
  everyNthFrame: 1,
});

// ... verification steps ...

await client.send("Page.stopScreencast");
// Pipe frames to ffmpeg for encoding
```

### Tradeoffs

| Pros | Cons |
|------|------|
| Maximum control over codec, bitrate, format | Significantly more complex to implement |
| Adaptive frame rate (only changed frames) | Frame acknowledgment logic required |
| Can pipe directly to ffmpeg (no intermediate files) | CDP API can change between Chrome versions |
| Native MP4 output via ffmpeg | May require non-headless mode |

### Best when

You need fine-grained control over video encoding, native MP4 output without a conversion step, or direct streaming to cloud storage during recording. Generally overkill for verification skills.

---

## Approach 5: `agent-browser` Record Commands

The `agent-browser` CLI tool provides shell-level recording commands. No Node.js scaffolding required.

### Usage

```bash
# Start recording
agent-browser record start "./session.webm"

# ... perform verification steps ...
agent-browser goto "http://localhost:3000"
agent-browser click @submit
agent-browser screenshot "./step-01.png"

# Stop recording (finalizes file)
agent-browser record stop
```

### Critical: Always use a trap

```bash
trap 'agent-browser record stop 2>/dev/null' EXIT
```

Recording must be stopped even on script failure — the `.webm` is only finalized on stop.

### Supplementary commands

```bash
# Annotated screenshot (adds element highlights):
agent-browser screenshot --annotate "./annotated.png"

# Visual regression diff:
agent-browser diff screenshot --baseline before.png
```

### Tradeoffs

| Pros | Cons |
|------|------|
| Shell-only — no TypeScript compilation | No DOM/network capture (video only) |
| Already installed, battle-tested | Assertions must be added separately |
| Works headed and headless | `.webm` output only |
| Combines with `screenshot --annotate` | |

### Best when

Quick verification scripts where visual confirmation is sufficient. The simplest path for pure shell skills.

---

## Approach 6: Terminal Recording (asciinema)

Records terminal I/O as a `.cast` file. Captures what the agent "saw" (text output of browser commands, assertion results) rather than what the browser rendered.

### Usage

```bash
# Requires: brew install asciinema
asciinema rec verification.cast --command "./verify.sh"

# Replay:
asciinema play verification.cast

# Plain text dump:
asciinema cat verification.cast
```

### Tradeoffs

| Pros | Cons |
|------|------|
| Captures the agent's perspective | Does not capture visual rendering |
| Very small file size | Layout bugs invisible |
| No display server needed | Less compelling for non-technical reviewers |

### Best when

Supplementary artifact alongside screenshots. Good for capturing the full assertion log as a narrative.

---

## Comparison Matrix

| Aspect | Playwright Video | Playwright Trace | Screenshot Sequence | CDP Screencast | agent-browser record | asciinema |
|--------|-----------------|-----------------|--------------------|----|-----|-----|
| Complexity | M | S-M | S-M | L | S | S |
| Visual continuity | Good | None (stills) | Poor (stills) | Good | Good | None |
| DOM inspection | No | Excellent | No | No | No | No |
| Network/console | No | Yes | No | No | No | Partial |
| Headless support | Excellent | Excellent | Excellent | Mixed | Good | Excellent |
| Output format | `.webm` | `.zip` | `.png`/`.mp4`/`.gif` | `.mp4` | `.webm` | `.cast` |
| Human reviewability | Medium | High (technical) | High | Medium | Medium | Medium |
| Setup needed | Node.js | Node.js | Optional ffmpeg | Node.js + ffmpeg | Already installed | brew install |
| Assertion coupling | Programmatic | Programmatic | Excellent | Manual | Manual | Excellent |

---

## Recommended Combinations

### Tier 1: Quick Verification (shell-only)

**agent-browser record + annotated screenshots + JSON assertion log**

No npm dependencies. Produces a video, per-step screenshots, and a machine-readable pass/fail log.

```bash
#!/bin/bash
set -euo pipefail
OUTDIR="./verification-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTDIR"
PASS=true

trap 'agent-browser record stop 2>/dev/null; [ "$PASS" = true ] && echo "PASS" || echo "FAIL"' EXIT

agent-browser record start "$OUTDIR/session.webm"

# Step 1
agent-browser goto "http://localhost:3000/signup"
agent-browser screenshot "$OUTDIR/step-001-signup.png"
echo '{"step":1,"action":"load signup page","passed":true}' >> "$OUTDIR/assertions.jsonl"

# Step 2
agent-browser type @email "test@example.com"
agent-browser type @password "Test1234!"
agent-browser click @submit
agent-browser screenshot "$OUTDIR/step-002-submitted.png"

# Assert redirect
CURRENT_URL=$(agent-browser eval "window.location.pathname")
if [ "$CURRENT_URL" = "/dashboard" ]; then
  echo '{"step":2,"action":"submit redirects to dashboard","passed":true}' >> "$OUTDIR/assertions.jsonl"
else
  echo '{"step":2,"action":"submit redirects to dashboard","passed":false,"actual":"'"$CURRENT_URL"'"}' >> "$OUTDIR/assertions.jsonl"
  PASS=false
fi

agent-browser record stop
```

### Tier 2: Deep Verification (Node.js)

**Playwright video + trace + programmatic assertions**

For complex flows where you need DOM inspection and network verification alongside video.

```js
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const OUTDIR = `./verification-${new Date().toISOString().replace(/[:.]/g, "-")}`;
fs.mkdirSync(OUTDIR, { recursive: true });

const assertions = [];
function assert(step, action, condition, details = {}) {
  assertions.push({ step, action, passed: condition, ...details });
  if (!condition) console.error(`FAIL: Step ${step} — ${action}`);
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    recordVideo: { dir: OUTDIR, size: { width: 1280, height: 720 } },
  });
  await context.tracing.start({ screenshots: true, snapshots: true });

  const page = await context.newPage();

  // Step 1: Load page
  await page.goto("http://localhost:3000/signup");
  await page.screenshot({ path: path.join(OUTDIR, "step-001-signup.png") });
  assert(1, "signup page loads", await page.isVisible("#signup-form"));

  // Step 2: Fill and submit
  await page.fill('[name="email"]', "test@example.com");
  await page.fill('[name="password"]', "Test1234!");
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard");
  await page.screenshot({ path: path.join(OUTDIR, "step-002-dashboard.png") });
  assert(2, "redirects to dashboard", page.url().includes("/dashboard"));

  // Step 3: Verify no console errors
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  assert(3, "no console errors", consoleErrors.length === 0, {
    errors: consoleErrors,
  });

  // Finalize
  await context.tracing.stop({ path: path.join(OUTDIR, "trace.zip") });
  await context.close();
  await browser.close();

  fs.writeFileSync(
    path.join(OUTDIR, "assertions.json"),
    JSON.stringify(assertions, null, 2)
  );

  const allPassed = assertions.every((a) => a.passed);
  console.log(`\nResult: ${allPassed ? "PASS" : "FAIL"}`);
  console.log(`Artifacts: ${OUTDIR}/`);
  console.log(`  - session video: *.webm`);
  console.log(`  - trace: trace.zip (view with: npx playwright show-trace ${OUTDIR}/trace.zip)`);
  console.log(`  - screenshots: step-*.png`);
  console.log(`  - assertions: assertions.json`);
  process.exit(allPassed ? 0 : 1);
})();
```

### Tier 3: Maximum Evidence

**All of the above + HTML filmstrip report**

Add an HTML report generator that reads `assertions.jsonl` and renders screenshots with pass/fail badges. Useful when verification results need to be shared with non-technical stakeholders or embedded in PR descriptions.

---

## Skill Integration Patterns

### Directory structure for a verification skill

```
skills/
  verify-signup/
    SKILL.md           # Skill definition
    verify.sh           # Shell-based verification (Tier 1)
    verify.js           # Node.js verification (Tier 2)
    report-generator.sh # Assembles HTML filmstrip from artifacts
```

### SKILL.md trigger pattern

```markdown
## When to use
After modifying signup flow components, auth forms, or onboarding pages.
Run automatically after completing work on files matching `src/auth/**` or `src/signup/**`.

## Artifacts produced
- `verification-*/session.webm` — full session video
- `verification-*/trace.zip` — Playwright trace (view with `npx playwright show-trace`)
- `verification-*/step-*.png` — screenshots at each checkpoint
- `verification-*/assertions.jsonl` — structured pass/fail log
```

### Exit code convention

- `exit 0` — all assertions passed
- `exit 1` — one or more assertions failed (artifacts still produced for review)

### Hooking into Claude Code workflows

A PostToolUse hook can trigger verification after code is written:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "python3 check-if-verification-needed.py \"$TOOL_INPUT_FILE_PATH\""
      }
    ]
  }
}
```

The hook script checks if the written file matches verification-worthy paths and prompts Claude to run the verification skill.

---

## Gotchas

- **`context.close()` finalizes video** — do not attempt to read the video file path before closing the context
- **`agent-browser` refs invalidate on navigation** — always re-snapshot after `goto`, link clicks, or form submissions
- **`.webm` not playable in Safari** — convert with `ffmpeg -i session.webm -c:v libx264 session.mp4`
- **Playwright trace viewer online upload** — `trace.playwright.dev` sends data to Microsoft servers; use `npx playwright show-trace` locally for proprietary code
- **macOS `screencapture -v`** — records the actual screen, does not work on headless processes; use Playwright or `agent-browser` recording instead
- **`asciinema` inside Claude Code** — cannot be initiated from within an already-running session in most configurations; requires wrapping the parent process
- **CDP `Page.startScreencast`** — frame acknowledgment is required; if acks back up, the browser throttles frame emission
- **Puppeteer screencast** — may require non-headless mode depending on configuration
