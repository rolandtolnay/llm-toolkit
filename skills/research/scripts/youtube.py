#!/usr/bin/env python3
# /// script
# dependencies = [
#     "youtube-transcript-api",
#     "typer",
# ]
# ///
"""
YouTube CLI - Search YouTube and extract transcripts for research.

Uses yt-dlp for search (no API key) and youtube-transcript-api for transcripts.
Long transcripts are pre-processed via `claude -p` for directed extraction.

Usage:
    uv run youtube.py search "<query>" [--question Q] [--max-videos N] [--max-transcripts N] [--after YYYY-MM-DD]
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import typer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = Path.home() / ".cache" / "research" / "logs"
LOG_RETENTION_DAYS = 30

WORD_THRESHOLD = 1500  # Transcripts above this get pre-processed
MAX_PREPROCESS_WORKERS = 3  # Max concurrent claude --bare -p calls
YTDLP_SEARCH_TIMEOUT = 120  # seconds
CLAUDE_PREPROCESS_TIMEOUT = 60  # seconds per transcript

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
    videos_searched: int = 0,
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
            "backend": "yt-dlp",
            "cache_hit": False,
            "success": success,
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        entry["cost_usd"] = 0.0
        entry["credits"] = 0
        entry["videos_searched"] = videos_searched
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
# yt-dlp search
# ---------------------------------------------------------------------------


def _check_ytdlp() -> None:
    """Fail fast if yt-dlp is not installed."""
    if not shutil.which("yt-dlp"):
        _emit_error(
            "MISSING_DEPENDENCY",
            "yt-dlp not found in PATH",
            ["Install with: brew install yt-dlp", "Or: pip install yt-dlp"],
        )


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

    # Soft date filter
    if after:
        recent = [i for i in items if i["upload_date"] and i["upload_date"] >= after]
        if len(recent) >= 2:
            items = recent

    # Sort by views descending
    items.sort(key=lambda x: x["view_count"], reverse=True)
    return items


# ---------------------------------------------------------------------------
# Transcript fetching (youtube-transcript-api)
# ---------------------------------------------------------------------------


def _fetch_transcript(video_id: str) -> str | None:
    """Fetch transcript for a single video. Returns text or None."""
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
            return None

        formatter = TextFormatter()
        return formatter.format_transcript(transcript.fetch())
    except Exception as exc:
        _log_stderr(f"Transcript fetch failed for {video_id}: {exc}")
        return None


def _fetch_transcripts(
    video_ids: list[str], max_transcripts: int
) -> dict[str, str | None]:
    """Fetch transcripts sequentially for up to max_transcripts videos."""
    results: dict[str, str | None] = {}
    for vid in video_ids[:max_transcripts]:
        results[vid] = _fetch_transcript(vid)
    return results


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
    max_videos: int = typer.Option(5, "--max-videos", "-v", help="Max videos to search"),
    max_transcripts: int = typer.Option(
        3, "--max-transcripts", "-t", help="Max transcripts to fetch"
    ),
    after: Optional[str] = typer.Option(
        None, "--after", help="Only videos after date (YYYY-MM-DD)"
    ),
    no_preprocess: bool = typer.Option(
        False, "--no-preprocess", help="Skip claude extraction, return raw transcripts"
    ),
) -> None:
    """Search YouTube, fetch transcripts, and optionally pre-process via claude."""
    _check_ytdlp()
    t0 = time.monotonic()

    # Search
    videos = _ytdlp_search(query, max_videos, after)
    if not videos:
        duration_ms = int((time.monotonic() - t0) * 1000)
        _log_call(query, duration_ms=duration_ms, videos_searched=0)
        _emit(
            {
                "success": True,
                "command": "search",
                "query": query,
                "question": question,
                "videos": [],
                "metadata": {
                    "backend": "yt-dlp",
                    "videos_searched": 0,
                    "transcripts_fetched": 0,
                    "transcripts_preprocessed": 0,
                    "cache_hit": False,
                },
            }
        )
        return

    # Fetch transcripts
    video_ids = [v["video_id"] for v in videos]
    transcripts = _fetch_transcripts(video_ids, max_transcripts)

    # Attach transcripts to video dicts (internal field)
    for video in videos:
        vid = video["video_id"]
        if vid in transcripts:
            video["_transcript"] = transcripts[vid]
        else:
            video["transcript_available"] = False

    # Pre-process or pass raw
    preprocessed_count = 0
    if not no_preprocess and question:
        preprocessed_count = _preprocess_transcripts_parallel(videos, question)
    else:
        # No preprocessing — attach raw transcripts
        for video in videos:
            transcript = video.pop("_transcript", None)
            if transcript and transcript.strip():
                video["transcript_available"] = True
                video["word_count"] = len(transcript.split())
                # Truncate very long transcripts in raw mode
                words = transcript.split()
                if len(words) > 2000:
                    video["raw_transcript"] = " ".join(words[:2000]) + "..."
                else:
                    video["raw_transcript"] = transcript
                video["preprocessed"] = False
            elif "transcript_available" not in video:
                video["transcript_available"] = False

    transcripts_fetched = sum(
        1 for v in videos if v.get("transcript_available", False)
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    _log_call(
        query,
        duration_ms=duration_ms,
        videos_searched=len(videos),
        transcripts_fetched=transcripts_fetched,
        transcripts_preprocessed=preprocessed_count,
    )

    _emit(
        {
            "success": True,
            "command": "search",
            "query": query,
            "question": question,
            "videos": videos,
            "metadata": {
                "backend": "yt-dlp",
                "videos_searched": len(videos),
                "transcripts_fetched": transcripts_fetched,
                "transcripts_preprocessed": preprocessed_count,
                "cache_hit": False,
            },
        }
    )


if __name__ == "__main__":
    app()
