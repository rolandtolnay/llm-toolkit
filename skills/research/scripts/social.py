#!/usr/bin/env python3
# /// script
# dependencies = [
#     "requests",
#     "typer",
#     "diskcache",
# ]
# ///
"""
Social CLI - Search Reddit and short-form video (TikTok/Instagram) for research.

Uses ScrapeCreators API for all backends. Reddit threads are ranked by upvotes
and optionally condensed via `claude -p`. Short-form results are interleaved
TikTok + Instagram with transcript/caption extraction.

Usage:
    uv run social.py reddit "<query>" [--question Q] [--subreddit S] [--no-cache]
    uv run social.py shortform "<query>" [--no-cache]
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
import typer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REDDIT_API_BASE = "https://api.scrapecreators.com/v1/reddit"
TIKTOK_API_BASE = "https://api.scrapecreators.com/v1/tiktok"
INSTAGRAM_API_BASE = "https://api.scrapecreators.com/v2/instagram"

REDDIT_MAX_THREADS = 5
REDDIT_TOP_COMMENTS = 10
REDDIT_COMMENT_EXCERPT = 300
REDDIT_CONDENSE_THRESHOLD = 2500  # words

SHORTFORM_MAX_PER_PLATFORM = 3
SHORTFORM_CAPTION_MAX_WORDS = 500
SHORTFORM_MIN_CAPTION_WORDS = 30  # filter noise

RELEVANCE_THRESHOLD = 0.25  # Minimum relevance score to keep a result

CACHE_DIR = Path.home() / ".cache" / "research"
CACHE_TTL_REDDIT = 2 * 3600  # 2h
CACHE_TTL_SHORTFORM = 4 * 3600  # 4h

LOG_DIR = Path.home() / ".cache" / "research" / "logs"
LOG_RETENTION_DAYS = 30

CLAUDE_CONDENSE_TIMEOUT = 60  # seconds
API_TIMEOUT = 30  # seconds per API call

CONDENSE_PROMPT_TEMPLATE = """\
Analyze these Reddit threads about: {question}

THREADS:
{threads_text}

Extract and organize the community's perspective:
- Consensus views (what most people agree on)
- Contrarian/minority opinions worth noting
- Specific tools, products, or resources mentioned by name
- Notable quotes that capture key sentiments (attribute to username)

Format as a concise bulleted list. Lead with the strongest consensus."""


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

_ENV_FILE_PATHS = [
    Path.home() / ".claude" / "research" / ".env",
    Path.cwd() / ".claude" / "research.env",
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

SCRAPECREATORS_API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


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
    tool: str,
    query: str,
    *,
    success: bool = True,
    duration_ms: int | None = None,
    error: str | None = None,
    cache_hit: bool = False,
    **extra: Any,
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
            "tool": tool,
            "query": query,
            "backend": "scrapecreators",
            "cache_hit": cache_hit,
            "success": success,
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        entry["cost_usd"] = 0.0
        entry["credits"] = 0
        entry.update(extra)
        if error:
            entry["error"] = error
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _emit(data: dict) -> None:
    """Write JSON to stdout."""
    typer.echo(json.dumps(data, ensure_ascii=False))


def _emit_error(command: str, code: str, message: str, suggestions: list[str] | None = None) -> None:
    """Emit a structured error and exit."""
    data: dict[str, Any] = {
        "success": False,
        "command": command,
        "error": {"code": code, "message": message},
    }
    if suggestions:
        data["error"]["suggestions"] = suggestions
    _emit(data)
    raise typer.Exit(code=1)


def _log_stderr(msg: str) -> None:
    """Log a message to stderr."""
    sys.stderr.write(f"[Social] {msg}\n")
    sys.stderr.flush()


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _get_cache():
    """Get or create diskcache instance."""
    import diskcache

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return diskcache.Cache(str(CACHE_DIR))


def _cache_key(command: str, *parts: Any) -> str:
    """Build a cache key from command + all relevant parts."""
    import hashlib

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
    return f"social:{command}:{h}"


def _cache_get(command: str, *parts: Any) -> Any | None:
    """Return cached value or None."""
    cache = _get_cache()
    return cache.get(_cache_key(command, *parts))


def _cache_set(command: str, *parts: Any, value: Any, ttl: int) -> None:
    """Store value in cache with given TTL."""
    cache = _get_cache()
    cache.set(_cache_key(command, *parts), value, expire=ttl)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _sc_headers() -> dict[str, str]:
    """Return ScrapeCreators auth headers."""
    return {
        "x-api-key": SCRAPECREATORS_API_KEY,
        "Accept": "application/json",
        "User-Agent": "research-skill/1.0 (Assistant Skill)",
    }


def _check_api_key(command: str) -> None:
    """Fail fast if SCRAPECREATORS_API_KEY is not set."""
    if not SCRAPECREATORS_API_KEY:
        _emit_error(
            command,
            "MISSING_API_KEY",
            "SCRAPECREATORS_API_KEY not set",
            [
                "Add SCRAPECREATORS_API_KEY=... to ~/.claude/research/.env",
                "Or set it in your shell environment",
                "Get a key at https://scrapecreators.com",
            ],
        )


# ---------------------------------------------------------------------------
# Relevance scoring (ported from last30days/lib/relevance.py)
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset({
    'the', 'a', 'an', 'to', 'for', 'how', 'is', 'in', 'of', 'on',
    'and', 'with', 'from', 'by', 'at', 'this', 'that', 'it', 'my',
    'your', 'i', 'me', 'we', 'you', 'what', 'are', 'do', 'can',
    'its', 'be', 'or', 'not', 'no', 'so', 'if', 'but', 'about',
    'all', 'just', 'get', 'has', 'have', 'was', 'will',
})

_SYNONYMS = {
    'js': {'javascript'}, 'javascript': {'js'},
    'ts': {'typescript'}, 'typescript': {'ts'},
    'ai': {'artificial', 'intelligence'},
    'ml': {'machine', 'learning'},
    'react': {'reactjs'}, 'reactjs': {'react'},
    'vue': {'vuejs'}, 'vuejs': {'vue'},
    'svelte': {'sveltejs'}, 'sveltejs': {'svelte'},
}

# Generic query words that shouldn't carry relevance on their own
_LOW_SIGNAL = frozenset({
    'advice', 'best', 'compare', 'comparison', 'explain', 'guide',
    'how', 'latest', 'news', 'opinion', 'opinions', 'review', 'reviews',
    'thoughts', 'tip', 'tips', 'tutorial', 'tutorials', 'update',
    'updates', 'use', 'using', 'versus', 'vs', 'worth',
})


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, remove stopwords, expand synonyms."""
    words = re.sub(r'[^\w\s]', ' ', text.lower()).split()
    tokens = {w for w in words if w not in _STOPWORDS and len(w) > 1}
    expanded = set(tokens)
    for t in tokens:
        if t in _SYNONYMS:
            expanded.update(_SYNONYMS[t])
    return expanded


def _relevance_score(query: str, text: str, hashtags: list[str] | None = None) -> float:
    """Compute query-centric relevance score between 0.0 and 1.0."""
    q_tokens = _tokenize(query)
    combined = f"{text} {' '.join(hashtags)}" if hashtags else text
    t_tokens = _tokenize(combined)

    # Split concatenated hashtags (e.g., "claudecode" -> matches "claude")
    if hashtags:
        for tag in hashtags:
            tag_lower = tag.lower()
            for qt in q_tokens:
                if qt in tag_lower and qt != tag_lower:
                    t_tokens.add(qt)

    if not q_tokens:
        return 0.5

    overlap = q_tokens & t_tokens
    if not overlap:
        return 0.0

    informative = {t for t in q_tokens if t not in _LOW_SIGNAL} or q_tokens

    coverage = len(overlap) / len(q_tokens)
    info_overlap = len(informative & t_tokens) / len(informative)
    precision = len(overlap) / (min(len(t_tokens), len(q_tokens) + 4) or 1)

    # Exact phrase bonus
    norm_q = ' '.join(re.sub(r'[^\w\s]', ' ', query.lower()).split())
    norm_t = ' '.join(re.sub(r'[^\w\s]', ' ', combined.lower()).split())
    phrase_bonus = 0.0
    if norm_q and norm_q in norm_t:
        phrase_bonus = 0.12 if len(norm_q.split()) > 1 else 0.16

    base = 0.55 * (coverage ** 1.35) + 0.25 * info_overlap + 0.20 * precision

    # Cap score if only generic words matched
    if informative and not (informative & t_tokens):
        return round(min(0.24, base), 2)

    return round(min(1.0, base + phrase_bonus), 2)


# ---------------------------------------------------------------------------
# Reddit backend
# ---------------------------------------------------------------------------


def _parse_date(created_utc: Any) -> str | None:
    """Convert Unix timestamp to YYYY-MM-DD."""
    if not created_utc:
        return None
    try:
        dt = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return None


def _reddit_global_search(query: str) -> list[dict]:
    """Search Reddit globally via ScrapeCreators."""
    try:
        resp = requests.get(
            f"{REDDIT_API_BASE}/search",
            params={"query": query, "sort": "relevance", "timeframe": "month"},
            headers=_sc_headers(),
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("posts", data.get("data", []))
    except Exception as e:
        _log_stderr(f"Reddit global search failed: {e}")
        return []


def _reddit_subreddit_search(subreddit: str, query: str) -> list[dict]:
    """Search within a specific subreddit via ScrapeCreators."""
    try:
        resp = requests.get(
            f"{REDDIT_API_BASE}/subreddit/search",
            params={
                "subreddit": subreddit,
                "query": query,
                "sort": "relevance",
                "timeframe": "month",
            },
            headers=_sc_headers(),
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("posts", data.get("data", []))
    except Exception as e:
        _log_stderr(f"Subreddit search failed for r/{subreddit}: {e}")
        return []


def _reddit_normalize_post(post: dict) -> dict:
    """Extract normalized fields from a raw Reddit post."""
    permalink = post.get("permalink", "")
    if permalink and not permalink.startswith("http"):
        url = f"https://www.reddit.com{permalink}"
    else:
        url = permalink or post.get("url", "")

    selftext = post.get("selftext", "") or ""
    if len(selftext) > 500:
        # Truncate at word boundary
        truncated = selftext[:500]
        last_space = truncated.rfind(" ")
        if last_space > 400:
            truncated = truncated[:last_space]
        selftext = truncated + "..."

    # Subreddit can be a string or a dict with a "name" key
    sub = post.get("subreddit", post.get("subreddit_name_prefixed", ""))
    if isinstance(sub, dict):
        sub = sub.get("name", sub.get("display_name", str(sub)))

    return {
        "title": post.get("title", ""),
        "url": url,
        "subreddit": sub,
        "date": _parse_date(post.get("created_utc", post.get("created"))),
        "score": post.get("score", 0) or 0,
        "num_comments": post.get("num_comments", 0) or 0,
        "selftext": selftext,
        "id": post.get("id", post.get("name", "")),
    }


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate text at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    return truncated + "..."


def _reddit_fetch_comments(post_url: str) -> list[dict]:
    """Fetch and normalize top comments for a Reddit post."""
    try:
        resp = requests.get(
            f"{REDDIT_API_BASE}/post/comments",
            params={"url": post_url},
            headers=_sc_headers(),
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_comments = data.get("comments", data.get("data", []))
    except Exception as e:
        _log_stderr(f"Comment fetch failed for {post_url}: {e}")
        return []

    # Filter out deleted/removed/AutoModerator
    filtered = []
    for c in raw_comments:
        author = c.get("author", "") or ""
        body = c.get("body", "") or ""
        if author.lower() in ("[deleted]", "[removed]", "automoderator"):
            continue
        if body.strip().lower() in ("[deleted]", "[removed]"):
            continue
        filtered.append(c)

    # Sort by score, take top N
    filtered.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
    top = filtered[:REDDIT_TOP_COMMENTS]

    results = []
    for c in top:
        body = c.get("body", "") or ""
        excerpt = _truncate_at_word(body, REDDIT_COMMENT_EXCERPT)

        # Check for replies — attach highest-scored reply
        top_reply = None
        replies = c.get("replies", None)
        if replies and isinstance(replies, list):
            valid_replies = [
                r for r in replies
                if isinstance(r, dict)
                and (r.get("author", "") or "").lower() not in ("[deleted]", "[removed]", "automoderator")
                and (r.get("body", "") or "").strip().lower() not in ("[deleted]", "[removed]")
            ]
            if valid_replies:
                best = max(valid_replies, key=lambda r: r.get("score", 0) or 0)
                top_reply = {
                    "author": best.get("author", ""),
                    "score": best.get("score", 0) or 0,
                    "excerpt": _truncate_at_word(best.get("body", ""), REDDIT_COMMENT_EXCERPT),
                }

        results.append({
            "author": c.get("author", ""),
            "score": c.get("score", 0) or 0,
            "excerpt": excerpt,
            "top_reply": top_reply,
        })

    return results


def _reddit_condense(threads: list[dict], question: str) -> str | None:
    """Condense Reddit threads via claude -p if content exceeds threshold.

    Returns condensed string or None if below threshold or on failure.
    """
    # Serialize threads to text and check word count
    parts = []
    for t in threads:
        parts.append(f"## {t['title']} (r/{t['subreddit']}, score: {t['score']})")
        if t.get("selftext"):
            parts.append(t["selftext"])
        for c in t.get("comments", []):
            parts.append(f"  - u/{c['author']} (score {c['score']}): {c['excerpt']}")
            if c.get("top_reply"):
                r = c["top_reply"]
                parts.append(f"    └ u/{r['author']} (score {r['score']}): {r['excerpt']}")
        parts.append("")

    threads_text = "\n".join(parts)
    word_count = len(threads_text.split())

    if word_count <= REDDIT_CONDENSE_THRESHOLD:
        return None

    _log_stderr(f"Condensing {word_count} words of Reddit content via claude -p")

    prompt = CONDENSE_PROMPT_TEMPLATE.format(
        question=question,
        threads_text=threads_text,
    )

    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        "sonnet",
        "--output-format",
        "text",
        "--no-session-persistence",
    ]

    preexec = os.setsid if hasattr(os, "setsid") else None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec,
        )
        try:
            stdout, stderr = proc.communicate(timeout=CLAUDE_CONDENSE_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            proc.wait(timeout=5)
            _log_stderr("Reddit condensing timed out")
            return None
    except FileNotFoundError:
        _log_stderr("claude command not found for condensing")
        return None

    if proc.returncode != 0:
        detail = (stderr or "").strip()[:200]
        _log_stderr(f"Reddit condensing failed: {detail}")
        return None

    return stdout.strip() if stdout and stdout.strip() else None


# ---------------------------------------------------------------------------
# Shortform backend (TikTok + Instagram)
# ---------------------------------------------------------------------------


def _clean_webvtt(text: str) -> str:
    """Strip WebVTT timestamps and headers from transcript text."""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if re.match(r"^\d{2}:\d{2}", line):
            continue
        if "-->" in line:
            continue
        cleaned.append(line)
    return " ".join(cleaned)


def _truncate_words(text: str, max_words: int) -> str:
    """Truncate text to max_words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def _tiktok_search(query: str) -> list[dict]:
    """Search TikTok via ScrapeCreators."""
    try:
        resp = requests.get(
            f"{TIKTOK_API_BASE}/search/keyword",
            params={"query": query, "sort_by": "relevance"},
            headers=_sc_headers(),
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        # Items are nested under aweme_info
        raw_entries = data.get("search_item_list") or data.get("data") or []
        items = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                continue
            info = entry.get("aweme_info", entry)

            video_id = str(info.get("aweme_id", info.get("id", "")))
            desc = info.get("desc", "") or ""
            author_info = info.get("author", {}) or {}
            author = author_info.get("nickname", author_info.get("unique_id", ""))
            stats = info.get("statistics", {}) or {}

            items.append({
                "platform": "tiktok",
                "video_id": video_id,
                "text": desc,
                "url": f"https://www.tiktok.com/@{author_info.get('unique_id', '')}/video/{video_id}",
                "author": author,
                "views": stats.get("play_count", 0) or 0,
                "likes": stats.get("digg_count", stats.get("like_count", 0)) or 0,
                "duration": info.get("duration", 0) or 0,
            })

        return items
    except Exception as e:
        _log_stderr(f"TikTok search failed: {e}")
        return []


def _tiktok_fetch_transcript(url: str) -> str | None:
    """Fetch transcript for a TikTok video."""
    try:
        resp = requests.get(
            f"{TIKTOK_API_BASE}/video/transcript",
            params={"url": url},
            headers=_sc_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        transcript = data.get("transcript")
        if not transcript:
            return None
        if isinstance(transcript, list):
            transcript = " ".join(str(s) for s in transcript)
        transcript = _clean_webvtt(transcript)
        if transcript:
            return _truncate_words(transcript, SHORTFORM_CAPTION_MAX_WORDS)
        return None
    except Exception as e:
        _log_stderr(f"TikTok transcript failed for {url}: {e}")
        return None


def _instagram_search(query: str) -> list[dict]:
    """Search Instagram Reels via ScrapeCreators."""
    try:
        resp = requests.get(
            f"{INSTAGRAM_API_BASE}/reels/search",
            params={"query": query},
            headers=_sc_headers(),
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_entries = data.get("reels") or data.get("items") or data.get("data") or []
        items = []
        for raw in raw_entries:
            if not isinstance(raw, dict):
                continue

            video_id = str(raw.get("id", raw.get("pk", "")))

            # Caption text — can be a string or dict
            caption_obj = raw.get("caption", "")
            if isinstance(caption_obj, dict):
                text = caption_obj.get("text", "")
            elif isinstance(caption_obj, str):
                text = caption_obj
            else:
                text = raw.get("desc", raw.get("text", ""))

            author_info = raw.get("user", raw.get("owner", {})) or {}
            author = author_info.get("username", author_info.get("full_name", ""))

            items.append({
                "platform": "instagram",
                "video_id": video_id,
                "text": text,
                "url": f"https://www.instagram.com/reel/{video_id}/",
                "author": author,
                "views": raw.get("play_count", raw.get("view_count", 0)) or 0,
                "likes": raw.get("like_count", 0) or 0,
                "duration": raw.get("video_duration", 0) or 0,
            })

        return items
    except Exception as e:
        _log_stderr(f"Instagram search failed: {e}")
        return []


def _instagram_fetch_transcript(url: str) -> str | None:
    """Fetch transcript for an Instagram Reel."""
    try:
        resp = requests.get(
            f"{INSTAGRAM_API_BASE}/media/transcript",
            params={"url": url},
            headers=_sc_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        transcripts = data.get("transcripts") or []
        if transcripts and isinstance(transcripts, list):
            transcript_text = " ".join(
                t.get("text", "") for t in transcripts
                if isinstance(t, dict) and t.get("text")
            )
            if transcript_text:
                return _truncate_words(transcript_text, SHORTFORM_CAPTION_MAX_WORDS)
        return None
    except Exception as e:
        _log_stderr(f"Instagram transcript failed for {url}: {e}")
        return None


def _interleave(tiktok_items: list[dict], instagram_items: list[dict], per_platform: int = 3) -> list[dict]:
    """Interleave top items from each platform: TT1/IG1/TT2/IG2/..."""
    tt = tiktok_items[:per_platform]
    ig = instagram_items[:per_platform]
    result = []
    for i in range(max(len(tt), len(ig))):
        if i < len(tt):
            result.append(tt[i])
        if i < len(ig):
            result.append(ig[i])
    return result


# ---------------------------------------------------------------------------
# Typer CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="social",
    help="Social search (Reddit + short-form video) for research",
    add_completion=False,
)


@app.callback()
def _callback() -> None:
    """Social search (Reddit + short-form video) for research."""


@app.command()
def reddit(
    query: str = typer.Argument(..., help="Reddit search query"),
    question: Optional[str] = typer.Option(
        None, "--question", "-q", help="Research question for condensing"
    ),
    subreddit: Optional[str] = typer.Option(
        None, "--subreddit", "-s", help="Limit search to specific subreddit"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache"
    ),
) -> None:
    """Search Reddit threads and fetch top comments."""
    _check_api_key("reddit")
    t0 = time.monotonic()

    # Check cache
    cache_parts = ("reddit", query, subreddit or "")
    if not no_cache:
        cached = _cache_get(*cache_parts)
        if cached is not None:
            duration_ms = int((time.monotonic() - t0) * 1000)
            _log_call("reddit", query, duration_ms=duration_ms, cache_hit=True)
            cached["metadata"]["cache_hit"] = True
            _emit(cached)
            return

    # Search
    if subreddit:
        raw_posts = _reddit_subreddit_search(subreddit, query)
    else:
        raw_posts = _reddit_global_search(query)

    # Normalize, deduplicate, score relevance, filter, rank
    seen_ids: set[str] = set()
    posts = []
    for raw in raw_posts:
        normalized = _reddit_normalize_post(raw)
        post_id = normalized["id"]
        if post_id and post_id in seen_ids:
            continue
        if post_id:
            seen_ids.add(post_id)
        # Score relevance against title + selftext
        rel = _relevance_score(query, f"{normalized['title']} {normalized['selftext']}")
        normalized["_relevance"] = rel
        posts.append(normalized)

    threads_found = len(posts)

    # Filter irrelevant results (only for global search where noise is high)
    if not subreddit:
        relevant = [p for p in posts if p["_relevance"] >= RELEVANCE_THRESHOLD]
        if relevant:
            posts = relevant

    # Sort by blended score: relevance + normalized engagement
    max_score = max((p["score"] for p in posts), default=1) or 1
    posts.sort(
        key=lambda p: p["_relevance"] * 0.5 + (p["score"] / max_score) * 0.5,
        reverse=True,
    )
    posts = posts[:REDDIT_MAX_THREADS]

    # Fetch comments for each thread
    for post in posts:
        post["comments"] = _reddit_fetch_comments(post["url"])
        # Remove internal fields
        post.pop("id", None)
        post.pop("_relevance", None)

    # Condense if question provided and enough content
    condensed = None
    did_condense = False
    if question:
        condensed = _reddit_condense(posts, question)
        if condensed:
            did_condense = True

    duration_ms = int((time.monotonic() - t0) * 1000)

    result = {
        "success": True,
        "command": "reddit",
        "query": query,
        "question": question,
        "threads": posts,
        "condensed": condensed,
        "metadata": {
            "backend": "scrapecreators",
            "threads_found": threads_found,
            "threads_returned": len(posts),
            "condensed": did_condense,
            "cache_hit": False,
        },
    }

    # Cache and log
    _cache_set(*cache_parts, value=result, ttl=CACHE_TTL_REDDIT)
    _log_call(
        "reddit",
        query,
        duration_ms=duration_ms,
        threads_found=threads_found,
        threads_returned=len(posts),
        condensed=did_condense,
    )

    _emit(result)


@app.command()
def shortform(
    query: str = typer.Argument(..., help="Search query for short-form video"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache"
    ),
) -> None:
    """Search TikTok + Instagram Reels with transcript extraction."""
    _check_api_key("shortform")
    t0 = time.monotonic()

    # Check cache
    cache_parts = ("shortform", query)
    if not no_cache:
        cached = _cache_get(*cache_parts)
        if cached is not None:
            duration_ms = int((time.monotonic() - t0) * 1000)
            _log_call("shortform", query, duration_ms=duration_ms, cache_hit=True)
            cached["metadata"]["cache_hit"] = True
            _emit(cached)
            return

    # Search TikTok + Instagram in parallel
    tiktok_results: list[dict] = []
    instagram_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        tt_future = executor.submit(_tiktok_search, query)
        ig_future = executor.submit(_instagram_search, query)

        try:
            tiktok_results = tt_future.result(timeout=API_TIMEOUT + 5)
        except Exception as e:
            _log_stderr(f"TikTok search error: {e}")

        try:
            instagram_results = ig_future.result(timeout=API_TIMEOUT + 5)
        except Exception as e:
            _log_stderr(f"Instagram search error: {e}")

    tiktok_found = len(tiktok_results)
    instagram_found = len(instagram_results)

    # Score relevance and rank by blended relevance + engagement
    import math
    for item in tiktok_results + instagram_results:
        hashtags = re.findall(r'#(\w+)', item.get("text", ""))
        item["_relevance"] = _relevance_score(query, item.get("text", ""), hashtags)
        item["_eng"] = math.log1p(item.get("views", 0))

    def _shortform_rank(items: list[dict]) -> list[dict]:
        max_eng = max((i["_eng"] for i in items), default=1) or 1
        return sorted(
            items,
            key=lambda i: i["_relevance"] * 0.6 + (i["_eng"] / max_eng) * 0.4,
            reverse=True,
        )

    tiktok_results = _shortform_rank(tiktok_results)
    instagram_results = _shortform_rank(instagram_results)

    # Widen pool for transcript fetch, then trim after caption filtering
    fetch_pool = SHORTFORM_MAX_PER_PLATFORM + 2  # fetch 5 per platform
    items = _interleave(tiktok_results, instagram_results, fetch_pool)

    # Fetch transcripts/captions sequentially
    captions_fetched = 0
    for item in items:
        if item["platform"] == "tiktok":
            caption = _tiktok_fetch_transcript(item["url"])
        else:
            caption = _instagram_fetch_transcript(item["url"])

        if caption:
            item["caption"] = caption
            captions_fetched += 1
        else:
            # Fall back to description text
            item["caption"] = _truncate_words(item.get("text", ""), SHORTFORM_CAPTION_MAX_WORDS)

    # Filter out items with caption < 30 words (noise), trim to final count
    filtered = []
    for item in items:
        if len((item.get("caption", "") or "").split()) >= SHORTFORM_MIN_CAPTION_WORDS:
            item.pop("_relevance", None)
            item.pop("_eng", None)
            filtered.append(item)
    # Interleaved order preserves per-platform balance, just trim total
    items = filtered[:SHORTFORM_MAX_PER_PLATFORM * 2]

    duration_ms = int((time.monotonic() - t0) * 1000)

    result = {
        "success": True,
        "command": "shortform",
        "query": query,
        "items": items,
        "metadata": {
            "backend": "scrapecreators",
            "tiktok_found": tiktok_found,
            "instagram_found": instagram_found,
            "items_returned": len(items),
            "captions_fetched": captions_fetched,
            "cache_hit": False,
        },
    }

    # Cache and log
    _cache_set(*cache_parts, value=result, ttl=CACHE_TTL_SHORTFORM)
    _log_call(
        "shortform",
        query,
        duration_ms=duration_ms,
        tiktok_found=tiktok_found,
        instagram_found=instagram_found,
        items_returned=len(items),
        captions_fetched=captions_fetched,
    )

    _emit(result)


if __name__ == "__main__":
    app()
