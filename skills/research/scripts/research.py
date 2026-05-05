#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx",
#     "typer",
#     "diskcache",
#     "firecrawl-py",
#     "PyYAML",
# ]
# ///
"""
Research CLI - Unified web research tool for Claude Code.

A single-file PEP 723 script that wraps Perplexity API, Context7 API, and Firecrawl SDK
into a consistent CLI interface for web research from any project directory.

Usage:
    uv run research.py <command> [options]

Commands:
    ask       Synthesized answer via Perplexity sonar-pro
    search    Raw web search results via Perplexity Search API
    reason    Deep reasoning via Perplexity sonar-reasoning-pro
    docs      Library documentation via Context7
    map       Discover URLs on a site via Firecrawl
    scrape    Extract page content as markdown via Firecrawl
    credits   Check Firecrawl credit balance
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
import typer
import yaml

# ---------------------------------------------------------------------------
# Env file loading
# ---------------------------------------------------------------------------

_ENV_FILE_PATHS = [
    Path.home() / ".claude" / "research" / ".env",  # global skill config
    Path.cwd() / ".claude" / "research.env",         # project-level override
]


def _load_env_files() -> list[Path]:
    """Load skill-specific env files into os.environ. Later files take priority."""
    loaded: list[Path] = []
    for p in _ENV_FILE_PATHS:
        if p.is_file():
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, sep, value = line.partition("=")
                if key and sep:
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    os.environ[key.strip()] = value
            loaded.append(p)
    return loaded


_LOADED_ENV_FILES = _load_env_files()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
CONTEXT7_API_KEY = os.environ.get("CONTEXT7_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
SCRAPECREATORS_API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "")

PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
CONTEXT7_BASE_URL = "https://context7.com/api/v2"

CACHE_DIR = Path.home() / ".cache" / "research"

# TTLs in seconds
CACHE_TTL = {
    "ask": 6 * 3600,       # 6h
    "search": 2 * 3600,    # 2h
    "reason": 6 * 3600,    # 6h
    "docs": 24 * 3600,     # 24h
    "map": 24 * 3600,      # 24h
    "scrape": 12 * 3600,   # 12h
}

# Timeouts in seconds
TIMEOUTS = {
    "ask": 60.0,
    "search": 30.0,
    "reason": 90.0,
    "docs": 60.0,
    "map": 30.0,
    "scrape": 30.0,
}

DEFAULT_MAX_TOKENS = 5000

LOG_DIR = Path.home() / ".cache" / "research" / "logs"

DEFAULT_RESEARCH_DIR = Path.home() / "Documents" / "Research"
RESEARCH_DIR = Path(os.environ.get("RESEARCH_DIR", str(DEFAULT_RESEARCH_DIR))).expanduser()

STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "are",
    "were", "been", "has", "have", "had", "do", "does", "did", "not",
    "this", "that", "what", "how", "which", "who", "when", "where", "why",
})

FILE_FIELD_WEIGHTS = {
    "tags": 0.30,
    "title": 0.25,
    "sub_question": 0.20,
    "query": 0.20,
    "index_bullet": 0.15,
    "run_title": 0.10,
}

COMPOUND_BONUS = 0.08
MAX_COMPOUND_BONUS = 0.16
SYNTHESIS_SCORE_FACTOR = 0.75
DEFAULT_PRIOR_MIN_SCORE = 0.15
MAX_PRIOR_SOURCES = 5

# Approximate per-call cost in USD (0 = free or credit-based)
COST_USD = {
    "ask": 0.02,
    "search": 0.005,
    "reason": 0.02,
    "docs": 0.0,
    "map": 0.0,
    "scrape": 0.0,
}

# Firecrawl credits consumed per call
CREDIT_COST = {
    "map": 1,
    "scrape": 1,
}


# ---------------------------------------------------------------------------
# Call logging
# ---------------------------------------------------------------------------

LOG_RETENTION_DAYS = 30


def _cleanup_old_logs() -> None:
    """Delete log files older than LOG_RETENTION_DAYS. Silent on failure."""
    try:
        today = datetime.now(timezone.utc).date()
        for f in LOG_DIR.iterdir():
            if not f.name.endswith(".jsonl"):
                continue
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d").date()
                if (today - file_date).days > LOG_RETENTION_DAYS:
                    f.unlink()
            except ValueError:
                continue
    except Exception:
        pass


def _log_call(
    command: str,
    query: str,
    *,
    backend: str,
    model: str | None = None,
    cache_hit: bool = False,
    success: bool = True,
    duration_ms: int | None = None,
    usage: dict | None = None,
    error: str | None = None,
) -> None:
    """Append a call record to the daily JSONL log. Never raises."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        if not log_file.exists():
            _cleanup_old_logs()
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
            "type": "cli",
            "tool": command,
            "query": query,
            "backend": backend,
        }
        if model:
            entry["model"] = model
        entry["cache_hit"] = cache_hit
        entry["success"] = success
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if usage:
            entry["usage"] = usage
        entry["cost_usd"] = COST_USD.get(command, 0.0) if not cache_hit else 0.0
        entry["credits"] = CREDIT_COST.get(command, 0) if not cache_hit else 0
        if error:
            entry["error"] = error
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Logging must never break the main flow


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

ASK_SYSTEM_PROMPT = (
    "You are a research assistant. Return a synthesized answer with inline citations.\n\n"
    "FORMAT:\n"
    "- Lead with the direct answer\n"
    "- Support with key findings as bullet points\n"
    "- Every factual claim must cite its source URL inline\n"
    "- Include code examples when relevant\n"
    "- Flag caveats or edge cases\n"
)

REASON_SYSTEM_PROMPT = (
    "You are a technical research assistant. Think step-by-step to analyze the query, "
    "search for authoritative sources, and synthesize actionable findings.\n\n"
    "RESEARCH APPROACH:\n"
    "1. Identify the core technical question\n"
    "2. Search for current best practices from official docs and trusted sources\n"
    "3. Verify claims across multiple sources when possible\n"
    "4. Synthesize into practical guidance\n\n"
    "OUTPUT FORMAT:\n"
    "- Lead with the recommended approach or answer\n"
    "- Support with 8-12 key findings as bullet points\n"
    "- Each finding cites its source inline [Source]\n"
    "- Include code examples when relevant\n"
    "- Flag any caveats or edge cases\n"
    "- End with clear next steps if applicable\n"
)

# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class ErrorCode(str, Enum):
    MISSING_API_KEY = "MISSING_API_KEY"
    API_ERROR = "API_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    LIBRARY_NOT_FOUND = "LIBRARY_NOT_FOUND"
    FILESYSTEM_ERROR = "FILESYSTEM_ERROR"


class ResearchError(Exception):
    def __init__(self, code: ErrorCode, message: str, suggestions: list[str] | None = None):
        self.code = code
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def output_success(command: str, query: str, metadata: dict, **fields: Any) -> dict:
    """Build success response envelope."""
    response: dict[str, Any] = {
        "success": True,
        "command": command,
        "query": query,
    }
    response.update(fields)
    response["metadata"] = metadata
    return response


def output_error(command: str, error: ResearchError) -> dict:
    """Build error response envelope."""
    err: dict[str, Any] = {"code": error.code.value, "message": error.message}
    if error.suggestions:
        err["suggestions"] = error.suggestions
    return {"success": False, "command": command, "error": err}


def emit(data: dict) -> None:
    """Print JSON to stdout."""
    typer.echo(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _get_cache():
    """Get or create diskcache instance."""
    import diskcache

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return diskcache.Cache(str(CACHE_DIR))


def _cache_key(command: str, *parts: Any) -> str:
    """Build a cache key from command + all relevant parts."""
    normalized = []
    for p in parts:
        if p is None:
            normalized.append("")
        elif isinstance(p, list):
            normalized.append("|".join(sorted(str(x) for x in p)))
        else:
            normalized.append(str(p))
    raw = ":".join([command] + normalized)
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{command}:{h}"


def cache_get(command: str, *parts: str) -> Any | None:
    """Return cached value or None."""
    cache = _get_cache()
    return cache.get(_cache_key(command, *parts))


def cache_set(command: str, *parts: str, value: Any) -> None:
    """Store value in cache with command-appropriate TTL."""
    cache = _get_cache()
    ttl = CACHE_TTL.get(command, 6 * 3600)
    cache.set(_cache_key(command, *parts), value, expire=ttl)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _extract_error_body(response: httpx.Response) -> str:
    """Extract human-readable error from an HTTP error response."""
    try:
        data = response.json()
        if isinstance(data.get("error"), dict):
            return data["error"].get("message", str(data["error"]))
        return data.get("message", data.get("error", response.text[:200]))
    except Exception:
        return response.text[:200]


def _handle_http_error(e: httpx.HTTPStatusError, service: str) -> ResearchError:
    """Convert HTTP status errors to ResearchError."""
    body = _extract_error_body(e.response)
    if e.response.status_code == 401:
        return ResearchError(
            ErrorCode.MISSING_API_KEY,
            f"Invalid {service} API key — {body}",
            suggestions=[f"Check your {service} API key"],
        )
    if e.response.status_code == 429:
        return ResearchError(
            ErrorCode.RATE_LIMITED,
            f"{service} rate limited — {body}",
            suggestions=["Wait a moment and retry"],
        )
    return ResearchError(
        ErrorCode.API_ERROR,
        f"{service} API error ({e.response.status_code}): {body}",
    )


def _safe_json(resp: httpx.Response, service: str) -> Any:
    """Parse JSON response, raising ResearchError on decode failure."""
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise ResearchError(
            ErrorCode.API_ERROR,
            f"{service} returned invalid JSON: {e}",
        )


# ---------------------------------------------------------------------------
# Token estimation (for Context7 truncation)
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return int(len(text.split()) * 1.3)


def truncate_results(results: list[dict], max_tokens: int) -> tuple[list[dict], int]:
    """Truncate Context7 results to fit within token budget."""
    truncated = []
    tokens_used = 0
    overhead = 50

    for result in results:
        content = result.get("content", "")
        result_tokens = estimate_tokens(content)
        total = result_tokens + overhead

        if tokens_used + total <= max_tokens:
            truncated.append({**result, "tokens": result_tokens})
            tokens_used += total
        else:
            remaining = max_tokens - tokens_used - overhead
            if remaining > 100:
                words = content.split()
                word_count = int(remaining / 1.3)
                if word_count > 0:
                    truncated_content = " ".join(words[:word_count]) + "..."
                    t = estimate_tokens(truncated_content)
                    truncated.append({**result, "content": truncated_content, "tokens": t, "truncated": True})
                    tokens_used += t + overhead
            break

    return truncated, tokens_used


# ---------------------------------------------------------------------------
# Strip <think> tags from reasoning models
# ---------------------------------------------------------------------------


def strip_think_tags(content: str) -> str:
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


# ---------------------------------------------------------------------------
# Prior research helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase, split, strip non-alnum, filter stop words."""
    text = text.lower().replace("-", " ")
    tokens = []
    for word in text.split():
        cleaned = re.sub(r"[^a-z0-9]", "", word)
        if cleaned and cleaned not in STOP_WORDS:
            tokens.append(cleaned)
            if len(cleaned) > 3 and cleaned.endswith("s") and not cleaned.endswith("ss"):
                tokens.append(cleaned[:-1])
    return tokens


def _read_frontmatter(path: Path) -> str:
    """Read only the YAML frontmatter block from a markdown file."""
    lines = []
    in_frontmatter = False
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip("\n")
                if not in_frontmatter:
                    if stripped == "---":
                        in_frontmatter = True
                    continue
                if stripped == "---":
                    break
                lines.append(stripped)
    except (OSError, UnicodeDecodeError):
        return ""
    return "\n".join(lines)


def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter into a dictionary. Returns {} on malformed YAML."""
    if not text.strip():
        return {}
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _as_list(value: Any) -> list:
    """Normalize scalar/list frontmatter values into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_list(value: Any) -> list[str]:
    """Normalize a scalar/list frontmatter value into non-empty strings."""
    return [str(item).strip() for item in _as_list(value) if str(item).strip()]


def _parse_index_entries(index_text: str) -> dict[str, dict]:
    """Parse INDEX.md into run metadata keyed by run_id."""
    entries: dict[str, dict] = {}
    current: dict[str, Any] | None = None

    for line in index_text.splitlines():
        if line.startswith("### "):
            if current and current.get("run_id"):
                entries[current["run_id"]] = current
            title_line = line[4:].strip()
            parts = title_line.rsplit(" — ", 1)
            title = parts[0].strip()
            date = parts[1].strip() if len(parts) > 1 else ""
            current = {"title": title, "date": date, "tags": [], "bullets": "", "run_id": "", "file_bullets": {}}
        elif current is not None:
            if line.startswith("**Tags:**"):
                tag_text = line[len("**Tags:**"):].strip()
                current["tags"] = [t.strip() for t in tag_text.split(",") if t.strip()]
            elif line.startswith("- ["):
                link_match = re.search(r"\]\(([^)]+)\)", line)
                bullet_text = re.sub(r"^- \[[^\]]*\]\([^)]+\)\s*—?\s*", "", line).strip()
                if link_match:
                    rel_path = link_match.group(1).strip()
                    parts = Path(rel_path).parts
                    if parts and not current.get("run_id"):
                        current["run_id"] = parts[0]
                    if rel_path:
                        current["file_bullets"][rel_path] = bullet_text
                current["bullets"] += " " + bullet_text

    if current and current.get("run_id"):
        entries[current["run_id"]] = current
    return entries


def _load_index_metadata(research_dir: Path) -> dict[str, dict]:
    """Load optional INDEX.md metadata for run/file enrichment."""
    index_path = research_dir / "INDEX.md"
    if not index_path.is_file():
        return {}
    try:
        return _parse_index_entries(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def _parse_since(since: str | None) -> datetime | None:
    """Parse duration string like 6m, 1y, 30d into cutoff datetime."""
    if not since:
        return None
    match = re.match(r"^(\d+)([dmy])$", since.strip().lower())
    if not match:
        raise ResearchError(
            ErrorCode.FILESYSTEM_ERROR,
            f"Invalid --since format: '{since}'. Use Nd, Nm, or Ny (e.g. 30d, 6m, 1y).",
        )
    amount = int(match.group(1))
    unit = match.group(2)
    now = datetime.now(timezone.utc)
    if unit == "d":
        days = amount
    elif unit == "m":
        days = amount * 30
    else:
        days = amount * 365
    from datetime import timedelta
    return now - timedelta(days=days)


def _resolve_research_dir(research_dir: Path | None = None) -> Path:
    """Resolve the effective research directory for prior-search commands."""
    if research_dir:
        return research_dir.expanduser()
    return RESEARCH_DIR


def _iter_research_markdown_files(research_dir: Path) -> list[Path]:
    """Return persisted research markdown files, excluding the global index and archives."""
    if not research_dir.is_dir():
        return []
    files: list[Path] = []
    for md_file in research_dir.glob("**/*.md"):
        rel_parts = md_file.relative_to(research_dir).parts
        if md_file.name == "INDEX.md":
            continue
        if any(part.startswith("_") for part in rel_parts):
            continue
        files.append(md_file)
    return sorted(files)


def _frontmatter_date(value: Any, fallback: str = "") -> str:
    """Normalize a frontmatter date value to YYYY-MM-DD when possible."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = str(value or fallback or "").strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else text


def _date_from_run_id(run_id: str) -> str:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", run_id or "")
    return match.group(1) if match else ""


def _date_passes_cutoff(date_text: str, cutoff: datetime | None) -> bool:
    if not cutoff or not date_text:
        return True
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc) >= cutoff
    except ValueError:
        return True


def _index_bullet_for_file(index_entry: dict, research_dir: Path, md_file: Path) -> str:
    rel_path = md_file.relative_to(research_dir).as_posix()
    return (index_entry.get("file_bullets") or {}).get(rel_path, "")


def _cap_sources(sources: Any, limit: int = MAX_PRIOR_SOURCES) -> list[dict[str, str]]:
    """Return up to N source entries, prioritizing primary sources."""
    normalized: list[dict[str, str]] = []
    for source in _as_list(sources):
        if isinstance(source, dict):
            url = str(source.get("url", "")).strip()
            role = str(source.get("role", "")).strip()
        else:
            url = str(source).strip()
            role = ""
        if url:
            item = {"url": url}
            if role:
                item["role"] = role
            normalized.append(item)

    role_rank = {"primary": 0, "secondary": 1, "tertiary": 2}
    normalized.sort(key=lambda s: role_rank.get(s.get("role", ""), 3))
    return normalized[:limit]


def _collect_prior_files(research_dir: Path, index_by_run: dict[str, dict], cutoff: datetime | None) -> list[dict[str, Any]]:
    """Collect file-level prior research records from markdown frontmatter."""
    records: list[dict[str, Any]] = []
    synthesis_titles: dict[str, str] = {}
    synthesis_paths: dict[str, str] = {}

    markdown_files = _iter_research_markdown_files(research_dir)
    frontmatters: dict[Path, dict] = {}
    for md_file in markdown_files:
        fm = _parse_frontmatter(_read_frontmatter(md_file))
        if not fm:
            continue
        frontmatters[md_file] = fm
        run_id = str(fm.get("run_id") or md_file.parent.name)
        role = str(fm.get("role") or ("synthesis" if md_file.name == "00-synthesis.md" else "angle"))
        if role == "synthesis":
            synthesis_titles[run_id] = str(fm.get("title") or "")
            synthesis_paths[run_id] = str(md_file)

    for md_file, fm in frontmatters.items():
        run_id = str(fm.get("run_id") or md_file.parent.name)
        index_entry = index_by_run.get(run_id, {})
        role = str(fm.get("role") or ("synthesis" if md_file.name == "00-synthesis.md" else "angle"))
        date_text = _frontmatter_date(fm.get("date"), index_entry.get("date") or _date_from_run_id(run_id))
        if not _date_passes_cutoff(date_text, cutoff):
            continue

        run_title = synthesis_titles.get(run_id) or index_entry.get("title") or run_id
        tags = _string_list(fm.get("tags") or index_entry.get("tags"))
        index_bullet = _index_bullet_for_file(index_entry, research_dir, md_file) if index_entry else ""

        record: dict[str, Any] = {
            "file": str(md_file),
            "title": str(fm.get("title") or md_file.stem),
            "role": role,
            "run_id": run_id,
            "run_title": run_title,
            "date": date_text,
            "sub_question": str(fm.get("sub_question") or ""),
            "query": str(fm.get("query") or ""),
            "tags": tags,
            "confidence": str(fm.get("confidence") or ""),
            "sources": _cap_sources(fm.get("sources")),
            "index_bullet": index_bullet,
            "run_synthesis": synthesis_paths.get(run_id, ""),
        }
        records.append(record)

    return records


def _score_prior_file(query_tokens_set: set[str], record: dict[str, Any]) -> dict:
    """Score one prior research file against query tokens, normalized to 0-1."""
    if not query_tokens_set:
        return {"score": 0.0, "matched_on": []}

    num_query_tokens = len(query_tokens_set)
    raw_score = 0.0
    max_score = 0.0
    matched_on: list[str] = []

    field_sources = {
        "tags": " ".join(record.get("tags", [])),
        "title": record.get("title", ""),
        "sub_question": record.get("sub_question", ""),
        "query": record.get("query", ""),
        "index_bullet": record.get("index_bullet", ""),
        "run_title": record.get("run_title", ""),
    }

    for field_name, field_text in field_sources.items():
        if not field_text:
            continue
        weight = FILE_FIELD_WEIGHTS.get(field_name, 0.1)
        max_score += weight
        field_tokens = set(_tokenize(str(field_text)))
        matched = query_tokens_set & field_tokens
        if not matched:
            continue
        raw_score += (len(matched) / num_query_tokens) * weight
        if field_name == "tags":
            for tag in record.get("tags", []):
                if matched & set(_tokenize(tag)):
                    matched_on.append(f"tags:{tag}")
        else:
            matched_on.append(f"{field_name}:{','.join(sorted(matched))}")

    compound_bonus_total = 0.0
    for tag in record.get("tags", []):
        tag_tokens = set(_tokenize(tag))
        if len(tag_tokens) >= 2 and tag_tokens.issubset(query_tokens_set):
            compound_bonus_total += COMPOUND_BONUS
            if f"tags:{tag}" not in matched_on:
                matched_on.append(f"compound:{tag}")
    compound_bonus_total = min(compound_bonus_total, MAX_COMPOUND_BONUS)
    raw_score += compound_bonus_total
    max_score += MAX_COMPOUND_BONUS

    if max_score <= 0:
        return {"score": 0.0, "matched_on": matched_on}

    normalized = min(raw_score / max_score, 1.0)
    if record.get("role") == "synthesis":
        normalized *= SYNTHESIS_SCORE_FACTOR

    return {"score": round(normalized, 4), "matched_on": matched_on}


# ---------------------------------------------------------------------------
# Perplexity backends
# ---------------------------------------------------------------------------


def _check_perplexity_key() -> None:
    if not PERPLEXITY_API_KEY:
        raise ResearchError(
            ErrorCode.MISSING_API_KEY,
            "PERPLEXITY_API_KEY not set",
            suggestions=["Export PERPLEXITY_API_KEY in your environment", "Get a key at https://docs.perplexity.ai/"],
        )


_VALID_RECENCY = {"hour", "day", "week", "month", "year"}


def _validate_recency(recency: str | None) -> None:
    if recency and recency not in _VALID_RECENCY:
        raise ResearchError(
            ErrorCode.API_ERROR,
            f"Invalid --recency value: '{recency}'. Must be one of: {', '.join(sorted(_VALID_RECENCY))}. "
            "These are preset windows (e.g., 'month' = last 30 days). "
            "For custom date ranges use --after YYYY-MM-DD and/or --before YYYY-MM-DD instead.",
        )


def _perplexity_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}


def perplexity_ask(
    query: str,
    *,
    domains: list[str] | None = None,
    recency: str | None = None,
    context: str = "high",
    after: str | None = None,
    before: str | None = None,
) -> dict:
    """Perplexity sonar-pro chat completion."""
    _check_perplexity_key()
    _validate_recency(recency)

    payload: dict[str, Any] = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": ASK_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "web_search_options": {"search_context_size": context},
    }
    if domains:
        payload["search_domain_filter"] = domains
    if recency:
        payload["search_recency_filter"] = recency
    if after:
        payload["search_after_date_filter"] = after
    if before:
        payload["search_before_date_filter"] = before

    try:
        with httpx.Client(timeout=TIMEOUTS["ask"]) as client:
            resp = client.post(f"{PERPLEXITY_BASE_URL}/chat/completions", headers=_perplexity_headers(), json=payload)
            resp.raise_for_status()
            data = _safe_json(resp, "Perplexity")
    except httpx.HTTPStatusError as e:
        raise _handle_http_error(e, "Perplexity")
    except httpx.RequestError as e:
        raise ResearchError(ErrorCode.NETWORK_ERROR, f"Network error connecting to Perplexity: {e}")

    # Extract answer and citations
    answer = ""
    choices = data.get("choices", [])
    if choices:
        answer = choices[0].get("message", {}).get("content", "")
    citations = data.get("citations", [])

    return {"answer": answer, "citations": citations, "model": "sonar-pro", "usage": data.get("usage", {})}


def perplexity_search(
    query: str,
    *,
    domains: list[str] | None = None,
    recency: str | None = None,
    limit: int = 10,
) -> dict:
    """Perplexity Search API — raw search results."""
    _check_perplexity_key()
    _validate_recency(recency)

    payload: dict[str, Any] = {"query": query}
    if domains:
        payload["search_domain_filter"] = domains
    if recency:
        payload["search_recency_filter"] = recency
    if limit != 10:
        payload["max_results"] = limit

    try:
        with httpx.Client(timeout=TIMEOUTS["search"]) as client:
            resp = client.post(f"{PERPLEXITY_BASE_URL}/search", headers=_perplexity_headers(), json=payload)
            resp.raise_for_status()
            data = _safe_json(resp, "Perplexity")
    except httpx.HTTPStatusError as e:
        raise _handle_http_error(e, "Perplexity")
    except httpx.RequestError as e:
        raise ResearchError(ErrorCode.NETWORK_ERROR, f"Network error connecting to Perplexity: {e}")

    # Normalize results
    results = []
    for item in data.get("results", []):
        results.append({
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "snippet": item.get("snippet", item.get("content", "")),
        })

    return {"results": results}


def perplexity_reason(
    query: str,
    *,
    domains: list[str] | None = None,
    recency: str | None = None,
    context: str = "high",
    effort: str = "high",
) -> dict:
    """Perplexity sonar-reasoning-pro chat completion."""
    _check_perplexity_key()
    _validate_recency(recency)

    payload: dict[str, Any] = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {"role": "system", "content": REASON_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "web_search_options": {"search_context_size": context},
        "reasoning_effort": effort,
    }
    if domains:
        payload["search_domain_filter"] = domains
    if recency:
        payload["search_recency_filter"] = recency

    try:
        with httpx.Client(timeout=TIMEOUTS["reason"]) as client:
            resp = client.post(f"{PERPLEXITY_BASE_URL}/chat/completions", headers=_perplexity_headers(), json=payload)
            resp.raise_for_status()
            data = _safe_json(resp, "Perplexity")
    except httpx.HTTPStatusError as e:
        raise _handle_http_error(e, "Perplexity")
    except httpx.RequestError as e:
        raise ResearchError(ErrorCode.NETWORK_ERROR, f"Network error connecting to Perplexity: {e}")

    # Extract and clean answer
    answer = ""
    choices = data.get("choices", [])
    if choices:
        raw = choices[0].get("message", {}).get("content", "")
        answer = strip_think_tags(raw)
    citations = data.get("citations", [])

    return {"answer": answer, "citations": citations, "model": "sonar-reasoning-pro", "usage": data.get("usage", {})}


# ---------------------------------------------------------------------------
# Context7 backend
# ---------------------------------------------------------------------------


def _check_context7_key() -> None:
    if not CONTEXT7_API_KEY:
        raise ResearchError(
            ErrorCode.MISSING_API_KEY,
            "CONTEXT7_API_KEY not set",
            suggestions=["Export CONTEXT7_API_KEY in your environment", "Get a key at https://context7.com/dashboard"],
        )


def _context7_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {CONTEXT7_API_KEY}"}


def context7_docs(library: str, query: str, *, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """Query library documentation via Context7."""
    _check_context7_key()

    # Step 1: Resolve library name to ID
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{CONTEXT7_BASE_URL}/libs/search",
                headers=_context7_headers(),
                params={"query": library, "limit": 5},
            )
            resp.raise_for_status()
            search_data = _safe_json(resp, "Context7")
    except httpx.HTTPStatusError as e:
        raise _handle_http_error(e, "Context7")
    except httpx.RequestError as e:
        raise ResearchError(ErrorCode.NETWORK_ERROR, f"Network error connecting to Context7: {e}")

    libraries = search_data.get("results", [])
    if not libraries:
        raise ResearchError(
            ErrorCode.LIBRARY_NOT_FOUND,
            f"Could not find library '{library}' in Context7",
            suggestions=["Try the exact package name from npm/pypi", "Check for common aliases (e.g., 'nextjs' for Next.js)"],
        )

    best = libraries[0]
    library_id = best.get("id", "")
    library_name = best.get("name", library)

    # Step 2: Query documentation
    try:
        with httpx.Client(timeout=TIMEOUTS["docs"]) as client:
            resp = client.get(
                f"{CONTEXT7_BASE_URL}/context",
                headers=_context7_headers(),
                params={"libraryId": library_id, "query": query},
            )
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                doc_data = _safe_json(resp, "Context7")
            else:
                doc_data = {"content": resp.text, "format": "markdown"}
    except httpx.HTTPStatusError as e:
        raise _handle_http_error(e, "Context7")
    except httpx.RequestError as e:
        raise ResearchError(ErrorCode.NETWORK_ERROR, f"Network error connecting to Context7: {e}")

    # Format results
    results = []
    for snippet in doc_data.get("codeSnippets", []):
        results.append({
            "title": snippet.get("title", "Code Example"),
            "content": snippet.get("code", ""),
            "source_url": snippet.get("url", ""),
            "type": "code",
        })
    for snippet in doc_data.get("infoSnippets", []):
        results.append({
            "title": snippet.get("title", "Documentation"),
            "content": snippet.get("content", ""),
            "source_url": snippet.get("url", ""),
            "type": "info",
        })
    if not results and "content" in doc_data:
        results.append({
            "title": "Documentation",
            "content": doc_data["content"],
            "source_url": doc_data.get("url", ""),
            "type": "info",
        })

    # Truncate to token budget
    truncated, tokens_used = truncate_results(results, max_tokens)

    return {
        "results": truncated,
        "library_id": library_id,
        "library_name": library_name,
        "total_available": len(results),
        "tokens_used": tokens_used,
    }


# ---------------------------------------------------------------------------
# Firecrawl backends
# ---------------------------------------------------------------------------


def _check_firecrawl_key() -> None:
    if not FIRECRAWL_API_KEY:
        raise ResearchError(
            ErrorCode.MISSING_API_KEY,
            "FIRECRAWL_API_KEY not set",
            suggestions=["Export FIRECRAWL_API_KEY in your environment", "Get a key at https://firecrawl.dev/"],
        )


def _get_firecrawl():
    """Get Firecrawl client instance."""
    from firecrawl import FirecrawlApp

    _check_firecrawl_key()
    return FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def firecrawl_map(url: str, *, search: str | None = None, limit: int = 100) -> dict:
    """Discover URLs on a site via Firecrawl map."""
    fc = _get_firecrawl()

    try:
        kwargs: dict[str, Any] = {}
        if search:
            kwargs["search"] = search
        if limit != 100:
            kwargs["limit"] = limit

        result = fc.map(url, **kwargs)

        # V2 SDK returns MapData with .links list of LinkResult(url, title, description)
        discovered = []
        for link in result.links[:limit]:
            discovered.append({"url": link.url or "", "title": link.title or ""})

        return {"discovered_urls": discovered}
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "Unauthorized" in err_str:
            raise ResearchError(ErrorCode.MISSING_API_KEY, f"Invalid Firecrawl API key — {err_str}")
        if "429" in err_str or "rate" in err_str.lower():
            raise ResearchError(ErrorCode.RATE_LIMITED, f"Firecrawl rate limited — {err_str}")
        raise ResearchError(ErrorCode.API_ERROR, f"Firecrawl map error: {err_str}")


def firecrawl_scrape(url: str) -> dict:
    """Scrape a URL and return markdown content via Firecrawl."""
    fc = _get_firecrawl()

    try:
        result = fc.scrape(url, formats=["markdown"])

        # V2 SDK returns Document with .markdown, .metadata.title, .metadata.source_url
        content = result.markdown or ""
        title = result.metadata.title if result.metadata else ""
        source_url = result.metadata.source_url if result.metadata else url

        return {"content": content, "url": source_url or url, "title": title or ""}
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "Unauthorized" in err_str:
            raise ResearchError(ErrorCode.MISSING_API_KEY, f"Invalid Firecrawl API key — {err_str}")
        if "429" in err_str or "rate" in err_str.lower():
            raise ResearchError(ErrorCode.RATE_LIMITED, f"Firecrawl rate limited — {err_str}")
        raise ResearchError(ErrorCode.API_ERROR, f"Firecrawl scrape error: {err_str}")


def firecrawl_credits() -> dict:
    """Check Firecrawl credit balance."""
    fc = _get_firecrawl()

    try:
        usage = fc.get_credit_usage()
        return {
            "remaining": usage.remaining_credits,
            "plan": usage.plan_credits,
        }
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "Unauthorized" in err_str:
            raise ResearchError(ErrorCode.MISSING_API_KEY, f"Invalid Firecrawl API key — {err_str}")
        raise ResearchError(ErrorCode.API_ERROR, f"Firecrawl credits error: {err_str}")


# ---------------------------------------------------------------------------
# Typer CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="research",
    help="Unified web research CLI — Perplexity, Context7, Firecrawl",
    add_completion=False,
)


def _validate_sites(sites: list[str] | None) -> list[str] | None:
    """Validate site filter values are actual domain names."""
    if not sites:
        return None
    for s in sites:
        if " " in s or "." not in s:
            raise ResearchError(
                ErrorCode.API_ERROR,
                f"Invalid --site value: '{s}'. Expected a domain name (e.g., stripe.com, pay.uk). "
                "This flag filters results to specific websites, not topics.",
            )
    return sites


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to answer"),
    site: Optional[list[str]] = typer.Option(None, "--site", "-s", help="Filter to specific sites (e.g., stripe.com)"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Preset window: hour, day, week, month, year"),
    context: str = typer.Option("high", "--context", "-c", help="Search context size: low, medium, high"),
    after: Optional[str] = typer.Option(None, "--after", help="Only results after date (YYYY-MM-DD)"),
    before: Optional[str] = typer.Option(None, "--before", help="Only results before date (YYYY-MM-DD)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Synthesized answer via Perplexity sonar-pro (~$0.02/query)."""
    cmd = "ask"
    cache_parts = [query, str(site), str(recency), context, str(after), str(before)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, query, backend="perplexity", model="sonar-pro", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = perplexity_ask(query, domains=_validate_sites(site), recency=recency, context=context, after=after, before=before)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": result["model"], "cache_hit": False, "usage": result.get("usage")},
            answer=result["answer"],
            citations=result["citations"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, query, backend="perplexity", model=result["model"], duration_ms=duration_ms, usage=result.get("usage"))
        emit(response)
    except ResearchError as e:
        _log_call(cmd, query, backend="perplexity", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    site: Optional[list[str]] = typer.Option(None, "--site", "-s", help="Filter to specific sites (e.g., stripe.com)"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Preset window: hour, day, week, month, year"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Raw web search results via Perplexity Search API (~$0.005/query)."""
    cmd = "search"
    cache_parts = [query, str(site), str(recency), str(limit)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, query, backend="perplexity", model="search", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = perplexity_search(query, domains=_validate_sites(site), recency=recency, limit=limit)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": "search", "cache_hit": False},
            results=result["results"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, query, backend="perplexity", model="search", duration_ms=duration_ms)
        emit(response)
    except ResearchError as e:
        _log_call(cmd, query, backend="perplexity", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def reason(
    query: str = typer.Argument(..., help="Complex question requiring reasoning"),
    site: Optional[list[str]] = typer.Option(None, "--site", "-s", help="Filter to specific sites (e.g., stripe.com)"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Preset window: hour, day, week, month, year"),
    context: str = typer.Option("high", "--context", "-c", help="Search context size: low, medium, high"),
    effort: str = typer.Option("high", "--effort", "-e", help="Reasoning effort: low, medium, high"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Deep reasoning via Perplexity sonar-reasoning-pro (~$0.02/query)."""
    cmd = "reason"
    cache_parts = [query, str(site), str(recency), context, effort]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, query, backend="perplexity", model="sonar-reasoning-pro", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = perplexity_reason(query, domains=_validate_sites(site), recency=recency, context=context, effort=effort)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": result["model"], "cache_hit": False, "usage": result.get("usage")},
            answer=result["answer"],
            citations=result["citations"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, query, backend="perplexity", model=result["model"], duration_ms=duration_ms, usage=result.get("usage"))
        emit(response)
    except ResearchError as e:
        _log_call(cmd, query, backend="perplexity", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def docs(
    library: str = typer.Argument(..., help="Library name (e.g., 'react', 'nextjs')"),
    query: str = typer.Argument(..., help="Documentation query"),
    max_tokens: int = typer.Option(DEFAULT_MAX_TOKENS, "--max-tokens", "-t", help="Max response tokens"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Library documentation via Context7 (free)."""
    cmd = "docs"
    cache_parts = [library, query, str(max_tokens)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, query, backend="context7", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = context7_docs(library, query, max_tokens=max_tokens)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            query,
            metadata={
                "backend": "context7",
                "library_id": result["library_id"],
                "library_name": result["library_name"],
                "total_available": result["total_available"],
                "returned": len(result["results"]),
                "tokens_used": result["tokens_used"],
                "max_tokens": max_tokens,
                "cache_hit": False,
            },
            results=result["results"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, query, backend="context7", duration_ms=duration_ms)
        emit(response)
    except ResearchError as e:
        _log_call(cmd, query, backend="context7", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command(name="map")
def map_cmd(
    url: str = typer.Argument(..., help="URL to map"),
    search_kw: Optional[str] = typer.Option(None, "--search", "-k", help="Filter discovered URLs by keyword"),
    limit: int = typer.Option(100, "--limit", "-l", help="Max URLs to return"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Discover URLs on a site via Firecrawl (1 credit)."""
    cmd = "map"
    cache_parts = [url, str(search_kw), str(limit)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, url, backend="firecrawl", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = firecrawl_map(url, search=search_kw, limit=limit)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            url,
            metadata={"backend": "firecrawl", "cache_hit": False},
            discovered_urls=result["discovered_urls"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, url, backend="firecrawl", duration_ms=duration_ms)
        emit(response)
    except ResearchError as e:
        _log_call(cmd, url, backend="firecrawl", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Extract page content as markdown via Firecrawl (1 credit)."""
    cmd = "scrape"
    cache_parts = [url]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            _log_call(cmd, url, backend="firecrawl", cache_hit=True)
            emit(cached)
            return

    try:
        t0 = time.monotonic()
        result = firecrawl_scrape(url)
        duration_ms = int((time.monotonic() - t0) * 1000)
        response = output_success(
            cmd,
            url,
            metadata={"backend": "firecrawl", "cache_hit": False},
            content=result["content"],
            url=result["url"],
            title=result["title"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        _log_call(cmd, url, backend="firecrawl", duration_ms=duration_ms)
        emit(response)
    except ResearchError as e:
        _log_call(cmd, url, backend="firecrawl", success=False, error=str(e))
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def credits() -> None:
    """Check Firecrawl credit balance."""
    cmd = "credits"
    try:
        result = firecrawl_credits()
        emit(output_success(
            cmd,
            "credit check",
            metadata={"backend": "firecrawl"},
            remaining=result["remaining"],
            plan=result["plan"],
        ))
    except ResearchError as e:
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def config() -> None:
    """Show resolved configuration (env files, API keys, settings)."""
    no_persist = os.environ.get("RESEARCH_NO_PERSIST", "0")
    env_files = []
    for p in _ENV_FILE_PATHS:
        status = "loaded" if p in _LOADED_ENV_FILES else "not found"
        env_files.append(f"{p} ({status})")
    emit({
        "success": True,
        "command": "config",
        "persistence": no_persist not in ("1", "true", "yes"),
        "keys": {
            "perplexity": bool(PERPLEXITY_API_KEY),
            "context7": bool(CONTEXT7_API_KEY),
            "firecrawl": bool(FIRECRAWL_API_KEY),
            "scrapecreators": bool(SCRAPECREATORS_API_KEY),
        },
        "env_files": env_files,
        "research_dir": str(RESEARCH_DIR),
    })


# ---------------------------------------------------------------------------
# Audit command
# ---------------------------------------------------------------------------


def _load_log_entries(days: int) -> list[dict]:
    """Read JSONL log entries for the last N days."""
    entries = []
    if not LOG_DIR.is_dir():
        return entries
    today = datetime.now(timezone.utc).date()
    for i in range(days):
        from datetime import timedelta

        d = today - timedelta(days=i)
        log_file = LOG_DIR / f"{d.isoformat()}.jsonl"
        if log_file.is_file():
            for line in log_file.read_text().splitlines():
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return entries


@app.command()
def audit(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Filter by session ID"),
    detail: bool = typer.Option(False, "--detail", help="Include individual call records"),
) -> None:
    """Analyze research API usage and costs from logs.

    Full reference: ~/.claude/skills/research/references/audit-reference.md
    """
    entries = _load_log_entries(days)
    if session:
        entries = [e for e in entries if e.get("session_id") == session]

    if not entries:
        emit({
            "success": True,
            "command": "audit",
            "message": f"No log entries found for the last {days} day(s).",
            "log_dir": str(LOG_DIR),
        })
        return

    # Compute period bounds from actual data
    timestamps = [e.get("timestamp", "") for e in entries]
    date_from = min(timestamps)[:10] if timestamps else ""
    date_to = max(timestamps)[:10] if timestamps else ""

    total = len(entries)
    sessions = set(e.get("session_id", "") for e in entries if e.get("session_id"))
    cache_hits = sum(1 for e in entries if e.get("cache_hit"))
    failures = sum(1 for e in entries if not e.get("success", True))
    total_cost = sum(e.get("cost_usd", 0.0) for e in entries)
    total_credits = sum(e.get("credits", 0) for e in entries)
    total_duration = sum(e.get("duration_ms", 0) for e in entries)

    # Breakdown by tool
    by_tool: dict[str, dict[str, Any]] = {}
    for e in entries:
        tool = e.get("tool", "unknown")
        if tool not in by_tool:
            by_tool[tool] = {"count": 0, "cost_usd": 0.0, "credits": 0, "cache_hits": 0, "failures": 0, "duration_ms": 0}
        by_tool[tool]["count"] += 1
        by_tool[tool]["cost_usd"] += e.get("cost_usd", 0.0)
        by_tool[tool]["credits"] += e.get("credits", 0)
        if e.get("cache_hit"):
            by_tool[tool]["cache_hits"] += 1
        if not e.get("success", True):
            by_tool[tool]["failures"] += 1
        by_tool[tool]["duration_ms"] += e.get("duration_ms", 0)

    for tool, stats in by_tool.items():
        stats["pct"] = round(stats["count"] / total * 100, 1)

    # Breakdown by backend
    by_backend: dict[str, dict[str, Any]] = {}
    for e in entries:
        backend = e.get("backend", "unknown")
        if backend not in by_backend:
            by_backend[backend] = {"count": 0, "cost_usd": 0.0, "credits": 0}
        by_backend[backend]["count"] += 1
        by_backend[backend]["cost_usd"] += e.get("cost_usd", 0.0)
        by_backend[backend]["credits"] += e.get("credits", 0)

    for backend, stats in by_backend.items():
        stats["pct"] = round(stats["count"] / total * 100, 1)

    # Breakdown by type (builtin vs cli)
    by_type: dict[str, int] = {}
    for e in entries:
        t = e.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    # Per-session summary
    per_session: dict[str, dict[str, Any]] = {}
    for e in entries:
        sid = e.get("session_id", "(no session)")
        if sid not in per_session:
            per_session[sid] = {"calls": 0, "cost_usd": 0.0, "credits": 0, "tools_used": set()}
        per_session[sid]["calls"] += 1
        per_session[sid]["cost_usd"] += e.get("cost_usd", 0.0)
        per_session[sid]["credits"] += e.get("credits", 0)
        per_session[sid]["tools_used"].add(e.get("tool", ""))

    # Convert sets to lists for JSON serialization
    sessions_summary = []
    for sid, stats in per_session.items():
        sessions_summary.append({
            "session_id": sid,
            "calls": stats["calls"],
            "cost_usd": round(stats["cost_usd"], 4),
            "credits": stats["credits"],
            "tools_used": sorted(stats["tools_used"]),
        })
    sessions_summary.sort(key=lambda s: s["calls"], reverse=True)

    result: dict[str, Any] = {
        "success": True,
        "command": "audit",
        "period": {"from": date_from, "to": date_to, "days": days},
        "summary": {
            "total_calls": total,
            "unique_sessions": len(sessions),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / total, 3) if total else 0,
            "failures": failures,
            "total_cost_usd": round(total_cost, 4),
            "total_credits": total_credits,
            "total_duration_ms": total_duration,
        },
        "by_tool": dict(sorted(by_tool.items(), key=lambda x: x[1]["count"], reverse=True)),
        "by_backend": dict(sorted(by_backend.items(), key=lambda x: x[1]["count"], reverse=True)),
        "by_type": by_type,
        "sessions": sessions_summary,
    }

    if detail:
        result["calls"] = entries

    emit(result)


# ---------------------------------------------------------------------------
# Prior research search
# ---------------------------------------------------------------------------


@app.command()
def prior(
    query: str = typer.Argument(..., help="Free-text query to match against prior research"),
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Date filter: 6m, 1y, 30d"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    min_score: float = typer.Option(DEFAULT_PRIOR_MIN_SCORE, "--min-score", help="Minimum normalized relevance score (0-1)"),
    research_dir: Optional[Path] = typer.Option(None, "--research-dir", help="Override research directory", hidden=True),
) -> None:
    """Search prior research files by relevance. Local only (free)."""
    t0 = time.time()

    try:
        cutoff = _parse_since(since)
        if min_score < 0 or min_score > 1:
            raise ResearchError(
                ErrorCode.FILESYSTEM_ERROR,
                f"Invalid --min-score: {min_score}. Use a value between 0 and 1.",
            )
    except ResearchError as e:
        emit(output_error("prior", e))
        raise typer.Exit(1)

    effective_research_dir = _resolve_research_dir(research_dir)
    if not effective_research_dir.is_dir():
        duration_ms = int((time.time() - t0) * 1000)
        _log_call("prior", query, backend="local", duration_ms=duration_ms)
        emit(output_success(
            "prior", query,
            metadata={
                "backend": "local",
                "duration_ms": duration_ms,
                "search_unit": "file",
                "research_dir": str(effective_research_dir),
                "total_files_indexed": 0,
                "min_score": min_score,
            },
            results=[],
        ))
        return

    index_by_run = _load_index_metadata(effective_research_dir)
    query_tokens_set = set(_tokenize(query))
    prior_files = _collect_prior_files(effective_research_dir, index_by_run, cutoff)

    results: list[dict[str, Any]] = []
    for record in prior_files:
        score_result = _score_prior_file(query_tokens_set, record)
        if score_result["score"] <= 0 or score_result["score"] < min_score:
            continue
        result = dict(record)
        result["score"] = score_result["score"]
        result["matched_on"] = score_result["matched_on"]
        results.append(result)

    results.sort(key=lambda r: (r["score"], 1 if r.get("role") == "angle" else 0, r.get("date", "")), reverse=True)
    results = results[:limit]

    duration_ms = int((time.time() - t0) * 1000)
    _log_call("prior", query, backend="local", duration_ms=duration_ms)
    emit(output_success(
        "prior", query,
        metadata={
            "backend": "local",
            "duration_ms": duration_ms,
            "search_unit": "file",
            "research_dir": str(effective_research_dir),
            "total_files_indexed": len(prior_files),
            "total_runs_indexed": len({r.get("run_id") for r in prior_files}),
            "min_score": min_score,
        },
        results=results,
    ))


if __name__ == "__main__":
    app()
