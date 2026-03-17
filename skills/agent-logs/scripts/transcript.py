#!/usr/bin/env python3
"""Extract a clean debug transcript from a Claude Code subagent JSONL file.

Default output is LLM-optimized (flat, no truncation, no decoration).

Usage:
  transcript.py <path-to-jsonl>                # LLM format to stdout
  transcript.py <path-to-jsonl> -o debug.md    # LLM format to file
  transcript.py <path-to-jsonl> --human         # human-readable markdown
  transcript.py <path-to-jsonl> --minified      # compact summary (one line per step)
  transcript.py <path-to-jsonl> --no-results    # tool calls only, skip results
  transcript.py <path-to-jsonl> --thinking 0    # hide assistant thinking text
"""

import argparse
import json
import re
import signal
import sys

LINE_NUM_RE = re.compile(r"^ {0,5}\d+→", re.MULTILINE)
SYSTEM_REMINDER_RE = re.compile(
    r"<system-reminder>.*?</system-reminder>", re.DOTALL
)


# ---------------------------------------------------------------------------
# LLM format (default)
# ---------------------------------------------------------------------------

def format_llm(input_path, max_thinking=-1, show_results=True):
    lines = _read_jsonl(input_path)

    out = []
    out.append(f"source: {input_path}")
    out.append(f"jsonl_lines: {len(lines)}")
    out.append("")

    prompt = _extract_initial_prompt(lines)
    if prompt:
        out.append("PROMPT")
        out.append(prompt)
        out.append("")

    final_response = _extract_final_response(lines)

    step = 0
    tool_id_to_name = {}

    for line in lines:
        obj = _parse(line)
        if not obj:
            continue

        typ = obj.get("type")
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")

        if typ not in ("user", "assistant"):
            continue

        if role == "assistant":
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")

                if btype == "text" and max_thinking != 0:
                    text = block.get("text", "").strip()
                    if text:
                        # Skip if this is the final response (emitted separately)
                        if text == final_response:
                            continue
                        step += 1
                        out.append(f"[{step}] THINKING")
                        if 0 < max_thinking < len(text):
                            out.append(text[:max_thinking] + "...")
                        else:
                            out.append(text)
                        out.append("")

                elif btype == "tool_use":
                    step += 1
                    name = block.get("name", "?")
                    inp = block.get("input", {})
                    tid = block.get("id", "")
                    tool_id_to_name[tid] = name

                    out.append(f"[{step}] CALL {name}")
                    _format_tool_llm(out, name, inp)
                    out.append("")

        elif role == "user" and show_results:
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    tid = block.get("tool_use_id", "")
                    tool_name = tool_id_to_name.get(tid, "?")
                    is_error = block.get("is_error", False)
                    result_text = _extract_result_text(block.get("content", ""))
                    result_text = LINE_NUM_RE.sub("", result_text)

                    tag = f"RESULT {tool_name}"
                    if is_error:
                        tag += " ERROR"
                    out.append(tag)
                    out.append(result_text if result_text else "(empty)")
                    out.append("")

    if final_response:
        out.append("RESPONSE")
        out.append(final_response)
        out.append("")

    return "\n".join(out)


def _format_tool_llm(out, name, inp):
    if name == "Bash":
        desc = inp.get("description", "")
        if desc:
            out.append(f"  desc: {desc}")
        out.append(f"  $ {inp.get('command', '')}")

    elif name == "Read":
        out.append(f"  file: {inp.get('file_path', '')}")
        if inp.get("offset"):
            out.append(f"  offset: {inp.get('offset')}  limit: {inp.get('limit', 'full')}")

    elif name == "Write":
        fp = inp.get("file_path", "")
        content_w = inp.get("content", "")
        out.append(f"  file: {fp}")
        out.append(f"  content ({len(content_w)} chars):")
        out.append(content_w)

    elif name == "Edit":
        out.append(f"  file: {inp.get('file_path', '')}")
        out.append(f"  old: {inp.get('old_string', '')}")
        out.append(f"  new: {inp.get('new_string', '')}")

    elif name == "Glob":
        out.append(f"  pattern: {inp.get('pattern', '')}")
        if inp.get("path"):
            out.append(f"  path: {inp.get('path')}")

    elif name == "Grep":
        out.append(f"  pattern: {inp.get('pattern', '')}")
        for key in ("glob", "path", "output_mode", "type"):
            if inp.get(key):
                out.append(f"  {key}: {inp.get(key)}")

    elif name == "Skill":
        out.append(f"  skill: {inp.get('skill', '')}")
        if inp.get("args"):
            out.append(f"  args: {inp.get('args', '')}")

    elif name == "Agent":
        out.append(f"  desc: {inp.get('description', '')}")
        if inp.get("subagent_type"):
            out.append(f"  type: {inp.get('subagent_type')}")
        if inp.get("prompt"):
            out.append(f"  prompt: {inp.get('prompt', '')}")

    else:
        out.append(f"  {json.dumps(inp)}")


# ---------------------------------------------------------------------------
# Human format (--human)
# ---------------------------------------------------------------------------

def format_human(input_path, max_result=1000, max_thinking=600, show_results=True):
    lines = _read_jsonl(input_path)

    out = []
    out.append("# Agent Debug Transcript")
    out.append(f"**Source:** `{input_path}`")
    out.append(f"**Lines in source:** {len(lines)}")
    out.append("")

    prompt = _extract_initial_prompt(lines)
    if prompt:
        out.append("## Prompt")
        out.append("")
        out.append(prompt)
        out.append("")
        out.append("---")
        out.append("")

    final_response = _extract_final_response(lines)

    step = 0
    tool_id_to_name = {}

    for line in lines:
        obj = _parse(line)
        if not obj:
            continue

        typ = obj.get("type")
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")

        if typ not in ("user", "assistant"):
            continue

        if role == "assistant":
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")

                if btype == "text" and max_thinking != 0:
                    text = block.get("text", "").strip()
                    if text:
                        if text == final_response:
                            continue
                        step += 1
                        out.append(f"## [{step}] Assistant")
                        out.append("")
                        if 0 < max_thinking < len(text):
                            out.append(text[:max_thinking] + "...")
                        else:
                            out.append(text)
                        out.append("")

                elif btype == "tool_use":
                    step += 1
                    name = block.get("name", "?")
                    inp = block.get("input", {})
                    tid = block.get("id", "")
                    tool_id_to_name[tid] = name

                    out.append(f"## [{step}] Tool Call: {name}")
                    out.append("")
                    _format_tool_human(out, name, inp)
                    out.append("")

        elif role == "user" and show_results:
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    tid = block.get("tool_use_id", "")
                    tool_name = tool_id_to_name.get(tid, "?")
                    is_error = block.get("is_error", False)
                    result_text = _extract_result_text(block.get("content", ""))

                    error_tag = " **ERROR**" if is_error else ""
                    out.append(f"### Result ({tool_name}){error_tag}")

                    if max_result > 0 and len(result_text) > max_result:
                        out.append("```")
                        out.append(
                            result_text[:max_result]
                            + f"\n... ({len(result_text)} chars total)"
                        )
                        out.append("```")
                    elif result_text:
                        out.append("```")
                        out.append(result_text)
                        out.append("```")
                    else:
                        out.append("*(empty)*")
                    out.append("")

    # Mark the final response distinctly
    final = _extract_final_response(lines)
    if final:
        out.append("## Response")
        out.append("")
        out.append(final)
        out.append("")

    return "\n".join(out)


def _format_tool_human(out, name, inp):
    if name == "Bash":
        desc = inp.get("description", "")
        if desc:
            out.append(f"**Description:** {desc}")
        out.append("```bash")
        out.append(inp.get("command", ""))
        out.append("```")

    elif name == "Read":
        out.append(f"**File:** `{inp.get('file_path', '')}`")
        if inp.get("offset"):
            out.append(
                f"**Offset:** {inp.get('offset')}  **Limit:** {inp.get('limit', 'full')}"
            )

    elif name == "Write":
        fp = inp.get("file_path", "")
        content_w = inp.get("content", "")
        out.append(f"**File:** `{fp}`")
        out.append(f"**Content length:** {len(content_w)} chars")
        if content_w:
            preview = content_w[:400] + ("..." if len(content_w) > 400 else "")
            out.append("```")
            out.append(preview)
            out.append("```")

    elif name == "Edit":
        out.append(f"**File:** `{inp.get('file_path', '')}`")
        old = inp.get("old_string", "")
        new = inp.get("new_string", "")
        out.append(
            f"**old_string** ({len(old)} chars): `{old[:120]}{'...' if len(old) > 120 else ''}`"
        )
        out.append(
            f"**new_string** ({len(new)} chars): `{new[:120]}{'...' if len(new) > 120 else ''}`"
        )

    elif name == "Glob":
        out.append(f"**Pattern:** `{inp.get('pattern', '')}`")
        if inp.get("path"):
            out.append(f"**Path:** `{inp.get('path')}`")

    elif name == "Grep":
        out.append(f"**Pattern:** `{inp.get('pattern', '')}`")
        for key, label in [("glob", "Glob"), ("path", "Path"), ("output_mode", "Mode")]:
            if inp.get(key):
                out.append(f"**{label}:** `{inp.get(key)}`")

    elif name == "Skill":
        out.append(f"**Skill:** `{inp.get('skill', '')}`")
        if inp.get("args"):
            out.append(f"**Args:** `{inp.get('args', '')}`")

    elif name == "Agent":
        out.append(f"**Description:** {inp.get('description', '')}")
        if inp.get("subagent_type"):
            out.append(f"**Type:** `{inp.get('subagent_type')}`")
        prompt = inp.get("prompt", "")
        if prompt:
            preview = prompt[:300] + ("..." if len(prompt) > 300 else "")
            out.append(f"**Prompt:** {preview}")

    else:
        dumped = json.dumps(inp)
        out.append(f"**Input:** {dumped[:300]}{'...' if len(dumped) > 300 else ''}")


# ---------------------------------------------------------------------------
# Minified format (--minified)
# ---------------------------------------------------------------------------

# Tools where the call line already contains the key info (file path),
# so the result line is noise when collapsed to one line.
_SKIP_RESULT_TOOLS = {"Read", "Write", "Edit", "Glob"}


def format_minified(input_path, show_results=True):
    lines = _read_jsonl(input_path)

    # First pass: collect tool counts and error count for header summary
    tool_counts = {}
    error_count = 0
    tool_id_to_name_pre = {}
    for line in lines:
        obj = _parse(line)
        if not obj:
            continue
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if role == "assistant" and block.get("type") == "tool_use":
                name = block.get("name", "?")
                tool_counts[name] = tool_counts.get(name, 0) + 1
                tool_id_to_name_pre[block.get("id", "")] = name
            if role == "user" and block.get("type") == "tool_result":
                if block.get("is_error", False):
                    error_count += 1

    out = []
    out.append(f"# Minified Transcript — {input_path}")

    prompt = _extract_initial_prompt(lines)
    if prompt:
        out.append("")
        out.append("PROMPT")
        out.append(prompt)
        out.append("")

    # Tool usage summary
    tool_summary = ", ".join(f"{n} x{c}" for n, c in tool_counts.items())
    out.append(f"# Tools: {tool_summary}")
    if error_count > 0:
        out.append(f"# Errors: {error_count}")
    out.append("")

    # Second pass: build the transcript
    step = 0
    tool_id_to_name = {}
    pending_calls = {}  # tid -> (step, name, summary)

    for line in lines:
        obj = _parse(line)
        if not obj:
            continue

        typ = obj.get("type")
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")

        if typ not in ("user", "assistant"):
            continue

        if role == "assistant":
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    step += 1
                    name = block.get("name", "?")
                    inp = block.get("input", {})
                    tid = block.get("id", "")
                    tool_id_to_name[tid] = name
                    summary = _minified_call_summary(name, inp)
                    pending_calls[tid] = (step, name, summary)

                    if not show_results:
                        out.append(f"{step}. {name}: {summary}")
                        out.append("")

        elif role == "user" and show_results:
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    tid = block.get("tool_use_id", "")
                    is_error = block.get("is_error", False)
                    result_text = _extract_result_text(block.get("content", ""))

                    if tid in pending_calls:
                        s, name, summary = pending_calls.pop(tid)
                    else:
                        s = "?"
                        name = tool_id_to_name.get(tid, "?")
                        summary = ""

                    out.append(f"{s}. {name}: {summary}")

                    if is_error:
                        error_oneliner = _minified_result(result_text, max_chars=120)
                        out.append(f"   [ERROR] {error_oneliner}")
                    elif name not in _SKIP_RESULT_TOOLS:
                        result_oneliner = _minified_result(result_text, max_chars=120)
                        out.append(f"   -> {result_oneliner}")

                    out.append("")

    # Flush any calls that never got a result
    for tid, (s, name, summary) in pending_calls.items():
        out.append(f"{s}. {name}: {summary}")
        out.append(f"   -> (no result)")
        out.append("")

    out.append(f"# Total steps: {step}")

    # Include the final response in full
    final = _extract_final_response(lines)
    if final:
        out.append("")
        out.append("RESPONSE")
        out.append(final)
        out.append("")

    return "\n".join(out)


def _minified_call_summary(name, inp):
    if name == "Bash":
        cmd = inp.get("command", "")
        return cmd[:100] + ("..." if len(cmd) > 100 else "")
    elif name == "Read":
        fp = inp.get("file_path", "")
        extra = ""
        if inp.get("offset"):
            extra = f" [L{inp['offset']}]"
        return fp + extra
    elif name == "Write":
        fp = inp.get("file_path", "")
        sz = len(inp.get("content", ""))
        return f"{fp} ({sz} chars)"
    elif name == "Edit":
        fp = inp.get("file_path", "")
        old = inp.get("old_string", "")
        return f"{fp} (replace {len(old)} chars)"
    elif name == "Glob":
        return inp.get("pattern", "")
    elif name == "Grep":
        pat = inp.get("pattern", "")
        g = inp.get("glob", "")
        return f"/{pat}/ {g}".strip()
    elif name == "Skill":
        return inp.get("skill", "")
    elif name == "Agent":
        return inp.get("description", "")
    else:
        dumped = json.dumps(inp)
        return dumped[:80] + ("..." if len(dumped) > 80 else "")


def _minified_result(text, max_chars=120):
    if not text:
        return "(empty)"
    # Collapse to single line
    oneliner = " ".join(text.split())
    if len(oneliner) > max_chars:
        return oneliner[:max_chars] + "..."
    return oneliner


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path):
    with open(path) as f:
        return f.readlines()


def _parse(line):
    try:
        return json.loads(line)
    except Exception:
        return None


def _extract_initial_prompt(lines):
    """Extract the first user text message, which is the prompt sent to the subagent."""
    for line in lines:
        obj = _parse(line)
        if not obj:
            continue
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                if texts:
                    return "\n".join(texts)
            elif isinstance(content, str) and content.strip():
                return content.strip()
            # First user message found but empty — stop looking
            return None
    return None


def _extract_final_response(lines):
    """Extract the last assistant text block, which is the agent's final response/output."""
    last_text = None
    for line in lines:
        obj = _parse(line)
        if not obj:
            continue
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        last_text = text
    return last_text


def _extract_result_text(result_content):
    if isinstance(result_content, list):
        texts = []
        for rb in result_content:
            if isinstance(rb, dict) and rb.get("type") == "text":
                texts.append(rb.get("text", ""))
        result_text = "\n".join(texts)
    elif isinstance(result_content, str):
        result_text = result_content
    else:
        result_text = str(result_content)

    result_text = SYSTEM_REMINDER_RE.sub("", result_text).strip()
    return result_text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Extract clean debug transcript from Claude Code subagent JSONL"
    )
    parser.add_argument("jsonl", help="Path to subagent JSONL file")
    parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--human",
        action="store_true",
        help="Human-readable markdown format (default is LLM-optimized)",
    )
    fmt_group.add_argument(
        "--minified",
        action="store_true",
        help="Compact summary: one line per tool call + one-line result",
    )
    parser.add_argument(
        "--thinking",
        type=int,
        default=None,
        help="Max chars for thinking (-1=unlimited, 0=hide). Default: unlimited for LLM, 600 for --human",
    )
    parser.add_argument(
        "--no-results",
        action="store_true",
        help="Show tool calls only, skip results",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Max chars for tool results (0=unlimited). Only applies to --human. Default: 1000",
    )

    args = parser.parse_args()

    if args.minified:
        transcript = format_minified(
            args.jsonl,
            show_results=not args.no_results,
        )
    elif args.human:
        max_thinking = args.thinking if args.thinking is not None else 600
        max_result = args.max if args.max is not None else 1000
        transcript = format_human(
            args.jsonl,
            max_result=max_result,
            max_thinking=max_thinking,
            show_results=not args.no_results,
        )
    else:
        max_thinking = args.thinking if args.thinking is not None else -1
        transcript = format_llm(
            args.jsonl,
            max_thinking=max_thinking,
            show_results=not args.no_results,
        )

    if args.output:
        with open(args.output, "w") as f:
            f.write(transcript)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(transcript)


if __name__ == "__main__":
    main()
