#!/usr/bin/env python3
# /// script
# dependencies = [
#     "youtube-transcript-api",
#     "typer",
#     "requests",
#     "diskcache",
# ]
# ///
"""
YouTube CLI - Search YouTube and extract transcripts for research.

Uses ScrapeCreators as the primary backend when SCRAPECREATORS_API_KEY is
configured, with yt-dlp/youtube-transcript-api as the free fallback backend.
Long transcripts are pre-processed via `claude -p` for directed extraction.

Usage:
    uv run youtube.py search "<query>" [--question Q] [--max-videos N] [--after this_month] [--no-preprocess] [--no-select]
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple, Optional

import requests
import typer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DIR = Path.home() / ".cache" / "research"
CACHE_TTL_YOUTUBE_SEARCH = 24 * 3600
CACHE_TTL_YOUTUBE_TRANSCRIPT = 30 * 24 * 3600

LOG_DIR = Path.home() / ".cache" / "research" / "logs"
LOG_RETENTION_DAYS = 30

SCRAPECREATORS_BASE_URL = "https://api.scrapecreators.com"
YOUTUBE_SEARCH_PATH = "/v1/youtube/search"
YOUTUBE_TRANSCRIPT_PATH = "/v1/youtube/video/transcript"
SC_API_TIMEOUT = 30
UPLOAD_DATE_FILTERS = {"today", "this_week", "this_month", "this_year"}

WORD_THRESHOLD = 1500  # Transcripts above this get pre-processed
MAX_PREPROCESS_WORKERS = 3  # Max concurrent claude --bare -p calls
YTDLP_SEARCH_TIMEOUT = 120  # seconds
CLAUDE_PREPROCESS_TIMEOUT = 60  # seconds per transcript
SELECTION_TIMEOUT = 60  # seconds

SELECTION_PROMPT_TEMPLATE = """\
You are selecting YouTube videos for a research investigation.

RESEARCH QUESTION: {question}

VIDEOS:
{video_list}

Select which videos to transcribe for research. Return ONLY valid JSON:
{{"selected": [{{"video_id": "...", "reason": "..."}}]}}

Selection criteria:
- Relevance: title/description must address the research question
- Unique value: each selected video should likely contain different information
- Source quality: prefer practitioners and established channels over clickbait
- Skip off-topic videos regardless of view count
- For narrow topics, selecting 1-2 videos is fine
- For broad topics with multiple angles, select up to 4"""

PREPROCESS_PROMPT_TEMPLATE = """\
Extract the key findings relevant to this research question from the YouTube \
video transcript provided on stdin.

RESEARCH QUESTION: {question}

VIDEO: "{title}" by {channel}

INSTRUCTIONS:
- Focus only on information relevant to the research question
- Extract specific facts, recommendations, techniques, or opinions stated by the speaker
- Include any tools, libraries, versions, or URLs mentioned
- Preserve the speaker's exact phrasing for notable claims (quote briefly)
- Omit filler, intros, outros, sponsor segments, and off-topic tangents
- If the transcript contains nothing relevant, respond with: "No relevant content found."

Format as a concise bulleted list (8-15 bullets max). Lead with the most important finding."""


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

_ENV_FILE_PATHS = [
    Path.home() / ".claude" / "research" / ".env",
    Path.cwd() / ".claude" / "research.env",
]


def _load_env_files() -> list[Path]:
    """Load skill-specific env files into os.environ. Later files override."""
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
# Logging (matches research.py pattern)
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
    query: str,
    *,
    success: bool = True,
    duration_ms: int | None = None,
    error: str | None = None,
    backend: str = "yt-dlp",
    cache_hit: bool = False,
    credits: int = 0,
    videos_searched: int = 0,
    videos_selected: int = 0,
    transcripts_fetched: int = 0,
    transcripts_preprocessed: int = 0,
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
            "tool": "youtube",
            "query": query,
            "backend": backend,
            "cache_hit": cache_hit,
            "success": success,
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        entry["cost_usd"] = 0.0
        entry["credits"] = credits
        entry["videos_searched"] = videos_searched
        entry["videos_selected"] = videos_selected
        entry["transcripts_fetched"] = transcripts_fetched
        entry["transcripts_preprocessed"] = transcripts_preprocessed
        if error:
            entry["error"] = error
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Logging must never break the main flow


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _emit(data: dict) -> None:
    """Write JSON to stdout."""
    typer.echo(json.dumps(data, ensure_ascii=False))


def _emit_error(code: str, message: str, suggestions: list[str] | None = None) -> None:
    """Emit a structured error and exit."""
    data: dict[str, Any] = {
        "success": False,
        "command": "search",
        "error": {"code": code, "message": message},
    }
    if suggestions:
        data["error"]["suggestions"] = suggestions
    _emit(data)
    raise typer.Exit(code=1)


def _log_stderr(msg: str) -> None:
    """Log a message to stderr."""
    sys.stderr.write(f"[YouTube] {msg}\n")
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
    """Build a YouTube cache key from command + relevant parts."""
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
    return f"youtube:{command}:{h}"


def _cache_get(command: str, *parts: Any) -> Any | None:
    """Return cached value or None."""
    cache = _get_cache()
    return cache.get(_cache_key(command, *parts))


def _cache_set(command: str, *parts: Any, value: Any, ttl: int) -> None:
    """Store value in cache with given TTL."""
    cache = _get_cache()
    cache.set(_cache_key(command, *parts), value, expire=ttl)


# ---------------------------------------------------------------------------
# ScrapeCreators adapters
# ---------------------------------------------------------------------------


def _sc_headers() -> dict[str, str]:
    """Return ScrapeCreators auth headers."""
    return {
        "x-api-key": SCRAPECREATORS_API_KEY,
        "Accept": "application/json",
        "User-Agent": "research-skill/1.0 (Assistant Skill)",
    }


def _extract_result_items(data: Any) -> list[dict]:
    """Extract result objects from known ScrapeCreators response shapes."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("videos", "results", "items", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _parse_iso_date(value: Any) -> str | None:
    """Parse ISO-ish date/datetime values to YYYY-MM-DD."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def _description_text(video: dict[str, Any]) -> str:
    """Return the best description-like text from a ScrapeCreators video."""
    for key in ("description", "descriptionSnippet", "shortDescription", "snippet"):
        value = video.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = []
            for part in value:
                if isinstance(part, dict):
                    parts.append(str(part.get("text") or part.get("simpleText") or ""))
                else:
                    parts.append(str(part))
            text = " ".join(parts)
            if text.strip():
                return text
        if isinstance(value, dict):
            text = value.get("text") or value.get("simpleText")
            if isinstance(text, str):
                return text
    return ""


def _to_int(value: Any) -> int | None:
    """Return an int for numeric ScrapeCreators fields when possible."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_sc_video(video: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize a ScrapeCreators search item to the existing YouTube shape."""
    video_id = video.get("id") or video.get("videoId")
    if not video_id:
        return None

    channel = video.get("channel") or {}
    if isinstance(channel, dict):
        channel_title = channel.get("title") or channel.get("name") or ""
    else:
        channel_title = str(channel) if channel else ""

    upload_date = _parse_iso_date(video.get("publishedTime")) or _parse_iso_date(video.get("publishDate"))
    url = video.get("url") or f"https://www.youtube.com/watch?v={video_id}"
    description = _description_text(video)

    return {
        "video_id": video_id,
        "title": video.get("title", "") or "",
        "channel": channel_title,
        "upload_date": upload_date,
        "url": url,
        "view_count": _to_int(video.get("viewCountInt")) or _to_int(video.get("view_count")) or 0,
        "like_count": _to_int(video.get("likeCountInt")) or _to_int(video.get("like_count")) or 0,
        "duration": _to_int(video.get("lengthSeconds")) or _to_int(video.get("duration")),
        "description_preview": description[:200],
    }


def _scrapecreators_search(query: str, max_videos: int, upload_date: str | None) -> tuple[list[dict], bool, int, str | None]:
    """Return (videos, cache_hit, credits_used, error_reason)."""
    if not SCRAPECREATORS_API_KEY:
        return [], False, 0, "missing_api_key"
    if upload_date is not None and upload_date not in UPLOAD_DATE_FILTERS:
        return [], False, 0, "invalid_upload_date"

    cached = _cache_get("search", query, max_videos, upload_date)
    if cached is not None:
        return cached, True, 0, None

    params = {
        "query": query,
        "type": "videos",
        "sortBy": "relevance",
        "includeExtras": "true",
    }
    if upload_date:
        params["uploadDate"] = upload_date

    try:
        resp = requests.get(
            f"{SCRAPECREATORS_BASE_URL}{YOUTUBE_SEARCH_PATH}",
            params=params,
            headers=_sc_headers(),
            timeout=SC_API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return [], False, 1, f"api_error: {exc}"

    videos: list[dict] = []
    for item in _extract_result_items(data):
        normalized = _normalize_sc_video(item)
        if normalized is not None:
            videos.append(normalized)
        if len(videos) >= max_videos:
            break

    _cache_set("search", query, max_videos, upload_date, value=videos, ttl=CACHE_TTL_YOUTUBE_SEARCH)
    return videos, False, 1, None


def _normalize_sc_transcript(data: Any) -> str | None:
    """Normalize ScrapeCreators transcript response to plain text."""
    text: str | None = None
    if isinstance(data, dict):
        direct = data.get("transcript_only_text")
        if isinstance(direct, str) and direct.strip():
            text = direct
        else:
            segments = data.get("transcript") or data.get("segments") or []
            if isinstance(segments, list):
                parts = [str(seg.get("text", "")) for seg in segments if isinstance(seg, dict)]
                text = " ".join(part for part in parts if part.strip())
    elif isinstance(data, list):
        parts = [str(seg.get("text", "")) for seg in data if isinstance(seg, dict)]
        text = " ".join(part for part in parts if part.strip())

    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _scrapecreators_fetch_transcript(video_url: str) -> tuple[str | None, bool, int, str | None]:
    """Return (plain_text, cache_hit, credits_used, error_reason)."""
    if not SCRAPECREATORS_API_KEY:
        return None, False, 0, "missing_api_key"

    cached = _cache_get("transcript", video_url, "en")
    if cached is not None:
        return cached, True, 0, None

    try:
        resp = requests.get(
            f"{SCRAPECREATORS_BASE_URL}{YOUTUBE_TRANSCRIPT_PATH}",
            params={"url": video_url, "language": "en"},
            headers=_sc_headers(),
            timeout=SC_API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return None, False, 1, f"api_error: {exc}"

    text = _normalize_sc_transcript(data)
    if not text:
        return None, False, 1, "empty_transcript"

    _cache_set("transcript", video_url, "en", value=text, ttl=CACHE_TTL_YOUTUBE_TRANSCRIPT)
    return text, False, 1, None


# ---------------------------------------------------------------------------
# yt-dlp search
# ---------------------------------------------------------------------------


def _has_ytdlp() -> bool:
    """Return whether yt-dlp is installed."""
    return bool(shutil.which("yt-dlp"))


def _coarse_upload_date_cutoff(upload_date: str | None) -> str | None:
    """Convert a coarse upload-date filter to a YYYY-MM-DD fallback cutoff."""
    if not upload_date:
        return None
    from datetime import timedelta

    today = datetime.now(timezone.utc).date()
    days = {
        "today": 0,
        "this_week": 7,
        "this_month": 31,
        "this_year": 366,
    }.get(upload_date)
    if days is None:
        return None
    return (today - timedelta(days=days)).isoformat()


def _ytdlp_search(query: str, max_videos: int, after: str | None) -> list[dict]:
    """Search YouTube via yt-dlp. Returns list of video metadata dicts."""
    cmd = [
        "yt-dlp",
        "--ignore-config",
        "--no-cookies-from-browser",
        f"ytsearch{max_videos}:{query}",
        "--dump-json",
        "--no-warnings",
        "--no-download",
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
            stdout, stderr = proc.communicate(timeout=YTDLP_SEARCH_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            proc.wait(timeout=5)
            _log_stderr("Search timed out (120s)")
            return []
    except FileNotFoundError:
        return []

    if not (stdout or "").strip():
        return []

    items = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            video = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = video.get("id", "")
        upload_date = video.get("upload_date", "")  # YYYYMMDD

        date_str = None
        if upload_date and len(upload_date) == 8:
            date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

        description = video.get("description", "") or ""
        items.append(
            {
                "video_id": video_id,
                "title": video.get("title", ""),
                "channel": video.get("channel", video.get("uploader", "")),
                "upload_date": date_str,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "view_count": video.get("view_count") or 0,
                "like_count": video.get("like_count") or 0,
                "duration": video.get("duration"),
                "description_preview": description[:200],
            }
        )

    # Soft date filter for the Free Fallback Backend.
    cutoff = _coarse_upload_date_cutoff(after)
    if cutoff:
        recent = [i for i in items if i["upload_date"] and i["upload_date"] >= cutoff]
        if len(recent) >= 2:
            items = recent

    # Sort by views descending
    items.sort(key=lambda x: x["view_count"], reverse=True)
    return items


# ---------------------------------------------------------------------------
# Transcript fetching (youtube-transcript-api with yt-dlp fallback)
# ---------------------------------------------------------------------------

YTDLP_SUBTITLE_TIMEOUT = 60  # seconds


def _fetch_transcript_api(video_id: str) -> tuple[str | None, str | None]:
    """Fetch transcript via youtube-transcript-api. Returns (text, error)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.formatters import TextFormatter

        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                pass

        if transcript is None:
            return None, "no english transcript found in available tracks"

        formatter = TextFormatter()
        return formatter.format_transcript(transcript.fetch()), None
    except Exception as exc:
        return None, str(exc)


def _fetch_transcript_ytdlp(video_id: str) -> tuple[str | None, str | None]:
    """Fetch transcript via yt-dlp subtitle download. Returns (text, error)."""
    if not shutil.which("yt-dlp"):
        return None, "yt-dlp not installed"

    tmpdir = tempfile.mkdtemp()
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = [
            "yt-dlp",
            "--ignore-config",
            "--no-cookies-from-browser",
            "--skip-download",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "json3",
            "--no-warnings",
            "-o", os.path.join(tmpdir, "sub"),
            url,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=YTDLP_SUBTITLE_TIMEOUT,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            return None, stderr if stderr else "unknown yt-dlp error"

        sub_files = list(Path(tmpdir).glob("*.json3"))
        if not sub_files:
            return None, "yt-dlp succeeded but no subtitle files written"

        manual = [f for f in sub_files if ".auto." not in f.name]
        chosen = manual[0] if manual else sub_files[0]

        with open(chosen) as f:
            data = json.load(f)

        segments = []
        for event in data.get("events", []):
            segs = event.get("segs", [])
            text = "".join(s.get("utf8", "") for s in segs).strip()
            if text and text != "\n":
                segments.append(text)

        text = " ".join(segments)
        text = re.sub(r"\s+", " ", text).strip()
        return (text, None) if text else (None, "subtitle file contained no text")
    except subprocess.TimeoutExpired:
        return None, "yt-dlp subtitle download timed out"
    except Exception as e:
        return None, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _fetch_transcript(video_id: str) -> tuple[str | None, str | None]:
    """Fetch transcript, trying youtube-transcript-api first then yt-dlp subtitle download.

    Returns (text, error_reason). error_reason is None on success.
    """
    errors: list[str] = []

    text, err = _fetch_transcript_api(video_id)
    if text:
        return text, None
    if err:
        errors.append(f"api: {err}")

    _log_stderr(f"API transcript failed for {video_id}, trying yt-dlp subtitle download...")
    text, err = _fetch_transcript_ytdlp(video_id)
    if text:
        return text, None
    if err:
        errors.append(f"yt-dlp: {err}")

    combined = "; ".join(errors)
    err_lower = combined.lower()
    ip_block_markers = (
        "ip blocked",
        "ip address blocked",
        "blocked by youtube",
        "youtube blocked",
        "too many requests",
        "rate limit",
        "429",
    )
    if any(marker in err_lower for marker in ip_block_markers):
        reason = f"ip_blocked ({combined})"
    elif "disabled" in err_lower:
        reason = f"transcripts_disabled ({combined})"
    elif "no english transcript" in err_lower and "no subtitle" in err_lower:
        reason = f"no_english_transcript ({combined})"
    else:
        reason = f"fetch_error ({combined})"

    _log_stderr(f"Transcript fetch failed for {video_id}: {combined}")
    return None, reason


class TranscriptFetchResult(NamedTuple):
    transcripts: dict[str, str | None]
    errors: list[str]
    backend: str
    credits: int
    cache_hit: bool


def _fetch_transcripts_with_fallback(selected_videos: list[dict]) -> TranscriptFetchResult:
    """Fetch selected transcripts through ScrapeCreators, then free fallback."""
    results: dict[str, str | None] = {}
    errors: list[str] = []
    successful_backends: set[str] = set()
    credits_used = 0
    sc_attempted = False
    sc_all_successes_cached = True

    for video in selected_videos:
        vid = video["video_id"]
        url = video.get("url") or f"https://www.youtube.com/watch?v={vid}"
        sc_error: str | None = None

        if SCRAPECREATORS_API_KEY and url:
            sc_attempted = True
            text, cache_hit, credits, reason = _scrapecreators_fetch_transcript(url)
            credits_used += credits
            if text:
                results[vid] = text
                successful_backends.add("scrapecreators")
                sc_all_successes_cached = sc_all_successes_cached and cache_hit
                continue
            sc_error = reason
            if not cache_hit:
                sc_all_successes_cached = False

        text, reason = _fetch_transcript(vid)
        results[vid] = text
        if text:
            successful_backends.add("yt-dlp")
            continue

        detail = reason or "unknown transcript failure"
        if sc_error and sc_error != "missing_api_key":
            detail = f"{detail}; scrapecreators: {sc_error}"
        errors.append(f"{vid}: {detail}")

    if len(successful_backends) > 1:
        backend_used = "mixed"
    elif successful_backends:
        backend_used = next(iter(successful_backends))
    else:
        backend_used = "scrapecreators" if sc_attempted else "yt-dlp"

    cache_hit = sc_attempted and credits_used == 0 and sc_all_successes_cached
    return TranscriptFetchResult(results, errors, backend_used, credits_used, cache_hit)


# ---------------------------------------------------------------------------
# Intelligent video selection (claude -p)
# ---------------------------------------------------------------------------


def _parse_json_response(text: str) -> dict | None:
    """Parse JSON from claude -p output, stripping code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _format_count(n: int) -> str:
    """Format a number as human-readable (e.g. 45000 -> '45K')."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _format_duration(seconds: int | None) -> str:
    """Format seconds as MM:SS or H:MM:SS."""
    if seconds is None:
        return "?"
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _select_videos(
    videos: list[dict], question: str
) -> tuple[list[str], dict[str, str], str | None]:
    """Use claude -p to select which videos to transcribe.

    Returns (selected_ids, reasons_map, warning). Warning is None on success,
    or a specific failure reason when fallback was used.
    """
    video_lines = []
    for i, v in enumerate(videos, 1):
        desc = v.get("description_preview", "")[:120]
        line = (
            f'{i}. video_id={v["video_id"]} | '
            f'"{v["title"]}" | {v.get("channel", "Unknown")} | '
            f'{_format_count(v["view_count"])} views | '
            f'{_format_count(v.get("like_count", 0))} likes | '
            f'{_format_duration(v.get("duration"))} | '
            f'"{desc}"'
        )
        video_lines.append(line)

    prompt = SELECTION_PROMPT_TEMPLATE.format(
        question=question,
        video_list="\n".join(video_lines),
    )

    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "text",
        "--no-session-persistence",
    ]

    valid_ids = {v["video_id"] for v in videos}

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
            stdout, stderr = proc.communicate(timeout=SELECTION_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            proc.wait(timeout=5)
            _log_stderr("LLM selection timed out")
            return _selection_fallback(videos, "LLM selection timed out")
    except FileNotFoundError:
        _log_stderr("claude command not found for selection")
        return _selection_fallback(videos, "claude command not found")

    if proc.returncode != 0:
        detail = (stderr or "").strip()[:200]
        _log_stderr(f"claude selection failed: {detail}")
        return _selection_fallback(videos, f"claude selection failed: {detail}")

    parsed = _parse_json_response(stdout or "")
    if not parsed or "selected" not in parsed:
        _log_stderr("Failed to parse selection response")
        return _selection_fallback(videos, "Failed to parse LLM selection JSON")

    selected = parsed["selected"]
    if not isinstance(selected, list) or not selected:
        _log_stderr("Empty selection from LLM")
        return _selection_fallback(videos, "LLM returned empty selection")

    # Validate all video_ids exist in input
    ids = []
    reasons = {}
    for item in selected:
        vid = item.get("video_id", "")
        if vid in valid_ids and vid not in reasons:
            ids.append(vid)
            reasons[vid] = item.get("reason", "")

    if not ids:
        _log_stderr("No valid video_ids in selection response")
        return _selection_fallback(videos, "No valid video_ids in LLM selection")

    return ids, reasons, None


def _selection_fallback(
    videos: list[dict], reason: str
) -> tuple[list[str], dict[str, str], str]:
    """Fallback: top 3 videos by view count."""
    top = videos[:3]  # Already sorted by views
    return [v["video_id"] for v in top], {}, reason


# ---------------------------------------------------------------------------
# Transcript pre-processing (claude --bare -p)
# ---------------------------------------------------------------------------


def _preprocess_transcript(
    transcript: str,
    question: str,
    title: str,
    channel: str,
) -> str | None:
    """Run claude -p to extract findings from a long transcript."""
    prompt = PREPROCESS_PROMPT_TEMPLATE.format(
        question=question,
        title=title,
        channel=channel,
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
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec,
        )
        try:
            stdout, stderr = proc.communicate(
                input=transcript, timeout=CLAUDE_PREPROCESS_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            proc.wait(timeout=5)
            _log_stderr(f"claude preprocessing timed out for '{title}'")
            return None
    except FileNotFoundError:
        _log_stderr("claude command not found")
        return None

    if proc.returncode != 0:
        _log_stderr(
            f"claude preprocessing failed for '{title}': {(stderr or '')[:200]}"
        )
        return None

    return stdout.strip() if stdout and stdout.strip() else None


def _preprocess_transcripts_parallel(
    videos: list[dict],
    question: str,
) -> int:
    """Pre-process long transcripts via claude -p in parallel.

    Modifies video dicts in-place. Returns count of preprocessed transcripts.
    """
    to_preprocess: list[dict] = []
    for video in videos:
        transcript = video.pop("_transcript", None)
        if transcript is None:
            video["transcript_available"] = False
            continue

        text = transcript.strip()
        if not text:
            video["transcript_available"] = False
            continue

        video["transcript_available"] = True
        word_count = len(text.split())
        video["word_count"] = word_count

        if word_count >= WORD_THRESHOLD and question:
            video["_transcript_text"] = text
            to_preprocess.append(video)
        else:
            video["raw_transcript"] = text
            video["preprocessed"] = False

    if not to_preprocess:
        return 0

    preprocessed_count = 0
    with ThreadPoolExecutor(max_workers=MAX_PREPROCESS_WORKERS) as executor:
        future_to_video = {}
        for video in to_preprocess:
            future = executor.submit(
                _preprocess_transcript,
                video["_transcript_text"],
                question,
                video["title"],
                video.get("channel", "Unknown"),
            )
            future_to_video[future] = video

        for future in as_completed(future_to_video):
            video = future_to_video[future]
            raw_text = video.pop("_transcript_text")
            try:
                extraction = future.result()
                if extraction:
                    video["extraction"] = extraction
                    video["preprocessed"] = True
                    preprocessed_count += 1
                else:
                    # Fallback: truncated raw transcript
                    words = raw_text.split()
                    video["raw_transcript"] = " ".join(words[:WORD_THRESHOLD]) + "..."
                    video["preprocessed"] = False
            except Exception:
                words = raw_text.split()
                video["raw_transcript"] = " ".join(words[:WORD_THRESHOLD]) + "..."
                video["preprocessed"] = False

    return preprocessed_count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _combined_backend(search_backend: str, transcript_backend: str | None = None) -> str:
    """Combine search/transcript backend names for run metadata."""
    if transcript_backend is None:
        return search_backend
    backend_parts = {search_backend, transcript_backend}
    if "mixed" in backend_parts or len(backend_parts) > 1:
        return "mixed"
    return search_backend


def _run_cache_hit(
    *,
    search_backend: str,
    search_cache_hit: bool,
    transcript_result: TranscriptFetchResult | None,
    credits_used: int,
) -> bool:
    """Return true when every paid ScrapeCreators call in this run hit cache."""
    if credits_used != 0:
        return False

    used_scrapecreators = search_backend == "scrapecreators" or (
        transcript_result is not None
        and transcript_result.backend in {"scrapecreators", "mixed"}
    )
    if not used_scrapecreators:
        return False

    if search_backend == "scrapecreators" and not search_cache_hit:
        return False

    if (
        transcript_result is not None
        and transcript_result.backend in {"scrapecreators", "mixed"}
        and not transcript_result.cache_hit
    ):
        return False

    return True


app = typer.Typer(
    name="youtube",
    help="YouTube search and transcript extraction for research",
    add_completion=False,
)


@app.callback()
def _callback() -> None:
    """YouTube search and transcript extraction for research."""


@app.command()
def search(
    query: str = typer.Argument(..., help="YouTube search query"),
    question: Optional[str] = typer.Option(
        None, "--question", "-q", help="Research sub-question for directed extraction"
    ),
    max_videos: int = typer.Option(
        10, "--max-videos", "-v", help="Max videos to search"
    ),
    after: Optional[str] = typer.Option(
        None,
        "--after",
        help="Upload-date filter: today, this_week, this_month, this_year",
    ),
    no_preprocess: bool = typer.Option(
        False, "--no-preprocess", help="Skip claude extraction, return raw transcripts"
    ),
    no_select: bool = typer.Option(
        False, "--no-select", help="Skip LLM selection, use top videos by views"
    ),
) -> None:
    """Search YouTube, fetch transcripts, and optionally pre-process via claude."""
    if after is not None and after not in UPLOAD_DATE_FILTERS:
        allowed = ", ".join(sorted(UPLOAD_DATE_FILTERS))
        raise typer.BadParameter(f"--after must be one of: {allowed}")

    t0 = time.monotonic()
    warnings: list[str] = []
    credits_used = 0
    search_cache_hit = False

    # Search: Primary Backend first, then Free Fallback Backend when primary is unavailable/fails.
    videos, search_cache_hit, search_credits, sc_search_error = _scrapecreators_search(
        query, max_videos, after
    )
    credits_used += search_credits

    if sc_search_error is None:
        search_backend = "scrapecreators"
    else:
        if not _has_ytdlp():
            if sc_search_error == "missing_api_key":
                _emit_error(
                    "NO_SEARCH_BACKEND",
                    "SCRAPECREATORS_API_KEY is not configured and yt-dlp was not found in PATH",
                    [
                        "Set SCRAPECREATORS_API_KEY in ~/.claude/research/.env",
                        "Or install yt-dlp with: brew install yt-dlp",
                    ],
                )
            _emit_error(
                "NO_SEARCH_BACKEND",
                f"ScrapeCreators YouTube search failed ({sc_search_error}) and yt-dlp was not found in PATH",
                [
                    "Check SCRAPECREATORS_API_KEY and network access",
                    "Or install yt-dlp with: brew install yt-dlp",
                ],
            )
        videos = _ytdlp_search(query, max_videos, after)
        search_backend = "yt-dlp"

    if not videos:
        backend = _combined_backend(search_backend)
        duration_ms = int((time.monotonic() - t0) * 1000)
        run_cache_hit = _run_cache_hit(
            search_backend=search_backend,
            search_cache_hit=search_cache_hit,
            transcript_result=None,
            credits_used=credits_used,
        )
        _log_call(
            query,
            duration_ms=duration_ms,
            backend=backend,
            cache_hit=run_cache_hit,
            credits=credits_used,
            videos_searched=0,
        )
        _emit(
            {
                "success": True,
                "command": "search",
                "query": query,
                "question": question,
                "videos": [],
                "metadata": {
                    "backend": backend,
                    "videos_searched": 0,
                    "videos_selected": 0,
                    "transcripts_fetched": 0,
                    "transcripts_preprocessed": 0,
                    "selection_method": "all",
                    "warnings": [],
                    "cache_hit": run_cache_hit,
                },
            }
        )
        return

    # Select which videos to transcribe
    selection_reasons: dict[str, str] = {}
    if question and not no_select and len(videos) > 3:
        selected_ids, selection_reasons, selection_warning = _select_videos(
            videos, question
        )
        if selection_warning:
            selection_method = "top_by_views"
            warnings.append(selection_warning)
        else:
            selection_method = "llm"
    elif len(videos) <= 3:
        selected_ids = [v["video_id"] for v in videos]
        selection_method = "all"
    else:
        # no question or --no-select: top 3 by views
        selected_ids = [v["video_id"] for v in videos[:3]]
        selection_method = "top_by_views"

    selected_set = set(selected_ids)

    # Mark selection on all videos
    for video in videos:
        vid = video["video_id"]
        video["selected"] = vid in selected_set
        if vid in selection_reasons:
            video["selection_reason"] = selection_reasons[vid]

    selected_videos = [v for v in videos if v["selected"]]

    # Fetch transcripts only for selected videos, with ScrapeCreators first per video.
    transcript_result = _fetch_transcripts_with_fallback(selected_videos)
    transcripts = transcript_result.transcripts
    credits_used += transcript_result.credits
    if transcript_result.errors:
        for te in transcript_result.errors:
            warnings.append(f"transcript_fetch_failed: {te}")

    # Detect likely IP block: all selected videos failed through the Free Fallback Backend.
    all_failed = selected_ids and all(
        transcripts.get(vid) is None for vid in selected_ids
    )
    ip_block_suspected = all_failed and any("ip_blocked" in e for e in transcript_result.errors)

    if all_failed and not ip_block_suspected:
        # All failed but not clearly IP-blocked — still suspicious.
        if len(selected_ids) >= 2:
            warnings.append(
                f"all_transcripts_failed: 0/{len(selected_ids)} transcripts fetched — "
                "possible IP block by YouTube (try a VPN)"
            )

    if ip_block_suspected:
        warnings.append(
            "youtube_ip_block: YouTube appears to be blocking transcript requests "
            "from this IP. All transcript fetches failed. Use a VPN to confirm."
        )

    # Attach transcripts to video dicts (internal field)
    for video in videos:
        vid = video["video_id"]
        if vid in transcripts:
            video["_transcript"] = transcripts[vid]
        elif video["selected"]:
            video["transcript_available"] = False

    # Pre-process or pass raw (only for selected videos)
    preprocessed_count = 0
    unselected_videos = [v for v in videos if not v["selected"]]

    if not no_preprocess and question:
        preprocessed_count = _preprocess_transcripts_parallel(
            selected_videos, question
        )
    else:
        # No preprocessing — attach raw transcripts
        for video in selected_videos:
            transcript = video.pop("_transcript", None)
            if transcript and transcript.strip():
                video["transcript_available"] = True
                video["word_count"] = len(transcript.split())
                words = transcript.split()
                if len(words) > 2000:
                    video["raw_transcript"] = " ".join(words[:2000]) + "..."
                else:
                    video["raw_transcript"] = transcript
                video["preprocessed"] = False
            elif "transcript_available" not in video:
                video["transcript_available"] = False

    # Clean up unselected videos (no transcript data)
    for video in unselected_videos:
        video.pop("_transcript", None)
        video["transcript_available"] = False

    transcripts_fetched = sum(
        1 for v in videos if v.get("transcript_available", False)
    )

    # Determine overall success: false when we selected videos but got zero transcripts.
    overall_success = True
    error_msg: str | None = None
    if selected_ids and transcripts_fetched == 0:
        overall_success = False
        if ip_block_suspected:
            error_msg = "YouTube is blocking transcript requests from this IP"
        else:
            error_msg = (
                f"0/{len(selected_ids)} transcripts fetched — "
                "possible IP block or transcripts unavailable"
            )

    backend = _combined_backend(
        search_backend,
        transcript_result.backend if selected_ids else None,
    )
    run_cache_hit = _run_cache_hit(
        search_backend=search_backend,
        search_cache_hit=search_cache_hit,
        transcript_result=transcript_result if selected_ids else None,
        credits_used=credits_used,
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    _log_call(
        query,
        success=overall_success,
        error=error_msg,
        duration_ms=duration_ms,
        backend=backend,
        cache_hit=run_cache_hit,
        credits=credits_used,
        videos_searched=len(videos),
        videos_selected=len(selected_ids),
        transcripts_fetched=transcripts_fetched,
        transcripts_preprocessed=preprocessed_count,
    )

    _emit(
        {
            "success": overall_success,
            "command": "search",
            "query": query,
            "question": question,
            "videos": videos,
            "metadata": {
                "backend": backend,
                "videos_searched": len(videos),
                "videos_selected": len(selected_ids),
                "transcripts_fetched": transcripts_fetched,
                "transcripts_preprocessed": preprocessed_count,
                "selection_method": selection_method,
                "warnings": warnings,
                "cache_hit": run_cache_hit,
            },
        }
    )
    if error_msg:
        _log_stderr(f"⚠ {error_msg}")


if __name__ == "__main__":
    app()
