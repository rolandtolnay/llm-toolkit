#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx",
#     "typer",
# ]
# ///
"""
EXA CLI - Semantic web search with inline content extraction.

Free tier: 1000 searches/month. Returns actual page text with results —
search + fetch in one call.

Usage:
    uv run exa.py search "<query>" [options]
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
import typer

# ---------------------------------------------------------------------------
# Env file loading
# ---------------------------------------------------------------------------

_ENV_FILE_PATHS = [
    Path.home() / ".claude" / "research" / ".env",
]


def _load_env_files() -> None:
    """Load env files into os.environ."""
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
                    os.environ.setdefault(key.strip(), value)


_load_env_files()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
EXA_BASE_URL = "https://api.exa.ai"
EXA_TIMEOUT = 30.0
USER_AGENT = "llm-toolkit-exa/1.0"

_RECENCY_DELTAS = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),
    "year": timedelta(days=365),
}

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ErrorCode(str, Enum):
    MISSING_API_KEY = "MISSING_API_KEY"
    API_ERROR = "API_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"


class ExaError(Exception):
    def __init__(
        self, code: ErrorCode, message: str, suggestions: list[str] | None = None
    ):
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


def output_error(command: str, error: ExaError) -> dict:
    """Build error response envelope."""
    err: dict[str, Any] = {"code": error.code.value, "message": error.message}
    if error.suggestions:
        err["suggestions"] = error.suggestions
    return {"success": False, "command": command, "error": err}


def emit(data: dict) -> None:
    """Print JSON to stdout."""
    typer.echo(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_api_key() -> None:
    if not EXA_API_KEY:
        raise ExaError(
            ErrorCode.MISSING_API_KEY,
            "EXA_API_KEY not set.",
            suggestions=[
                "Get a free key at https://exa.ai (1000 searches/month)",
                "Add EXA_API_KEY=... to ~/.claude/research/.env",
                "Or export EXA_API_KEY=... in your shell",
            ],
        )


def _recency_to_start_date(recency: str) -> str:
    """Convert recency shorthand to ISO 8601 start date."""
    delta = _RECENCY_DELTAS.get(recency)
    if not delta:
        valid = ", ".join(sorted(_RECENCY_DELTAS))
        raise ExaError(
            ErrorCode.API_ERROR,
            f"Invalid --recency value: '{recency}'. Must be one of: {valid}.",
        )
    dt = datetime.now(timezone.utc) - delta
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_sites(sites: list[str] | None) -> list[str] | None:
    if not sites:
        return None
    for s in sites:
        if " " in s or "." not in s:
            raise ExaError(
                ErrorCode.API_ERROR,
                f"Invalid --site value: '{s}'. Expected a domain (e.g., stripe.com).",
            )
    return sites


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


def exa_search(
    query: str,
    *,
    num_results: int = 10,
    max_characters: int = 1500,
    include_domains: list[str] | None = None,
    start_published_date: str | None = None,
) -> dict:
    """Semantic web search with inline content extraction via EXA."""
    _check_api_key()

    payload: dict[str, Any] = {
        "query": query,
        "type": "auto",
        "numResults": num_results,
        "contents": {"text": {"maxCharacters": max_characters}},
    }
    if include_domains:
        payload["includeDomains"] = include_domains
    if start_published_date:
        payload["startPublishedDate"] = start_published_date

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        with httpx.Client(timeout=EXA_TIMEOUT) as client:
            resp = client.post(
                f"{EXA_BASE_URL}/search", json=payload, headers=headers
            )

        if resp.status_code == 401:
            raise ExaError(
                ErrorCode.MISSING_API_KEY,
                "Invalid EXA API key.",
                suggestions=["Check EXA_API_KEY in ~/.claude/research/.env"],
            )
        if resp.status_code == 429:
            raise ExaError(
                ErrorCode.RATE_LIMITED,
                "EXA rate limit exceeded.",
                suggestions=["Free tier: 1000 searches/month", "Wait and retry"],
            )
        resp.raise_for_status()
        return resp.json()

    except ExaError:
        raise
    except httpx.TimeoutException:
        raise ExaError(ErrorCode.NETWORK_ERROR, "EXA request timed out.")
    except httpx.HTTPStatusError as e:
        raise ExaError(
            ErrorCode.API_ERROR,
            f"EXA API error: {e.response.status_code} {e.response.text[:200]}",
        )
    except httpx.HTTPError as e:
        raise ExaError(ErrorCode.NETWORK_ERROR, f"Network error: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="exa",
    help="Semantic web search with inline content — EXA API (free, 1000/mo)",
    add_completion=False,
)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    site: Optional[list[str]] = typer.Option(
        None, "--site", "-s", help="Restrict to domain (repeatable)"
    ),
    chars: int = typer.Option(
        1500, "--chars", "-c", help="Max characters of page text per result"
    ),
    recency: Optional[str] = typer.Option(
        None, "--recency", "-r", help="Preset window: hour, day, week, month, year"
    ),
) -> None:
    """Semantic web search with inline page content (free, 1000/month)."""
    cmd = "search"
    try:
        start_date = _recency_to_start_date(recency) if recency else None
        domains = _validate_sites(site)

        t0 = time.monotonic()
        raw = exa_search(
            query,
            num_results=limit,
            max_characters=chars,
            include_domains=domains,
            start_published_date=start_date,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "text": r.get("text", ""),
                "published_date": r.get("publishedDate"),
                "score": r.get("score"),
            }
            for r in raw.get("results", [])
        ]

        emit(
            output_success(
                cmd,
                query,
                metadata={
                    "backend": "exa",
                    "result_count": len(results),
                    "max_characters": chars,
                    "duration_ms": duration_ms,
                },
                results=results,
            )
        )

    except ExaError as e:
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
