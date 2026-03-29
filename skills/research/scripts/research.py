#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx",
#     "typer",
#     "diskcache",
#     "firecrawl-py",
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
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
import typer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
CONTEXT7_API_KEY = os.environ.get("CONTEXT7_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

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
            f"Invalid --recency value: '{recency}'. Must be one of: {', '.join(sorted(_VALID_RECENCY))}",
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


def _parse_domains(domain: list[str] | None) -> list[str] | None:
    """Parse domain filter list."""
    if not domain:
        return None
    return domain


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to answer"),
    domain: Optional[list[str]] = typer.Option(None, "--domain", "-d", help="Filter to specific domains"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Recency filter: day, week, month, year"),
    context: str = typer.Option("high", "--context", "-c", help="Search context size: low, medium, high"),
    after: Optional[str] = typer.Option(None, "--after", help="Only results after date (YYYY-MM-DD)"),
    before: Optional[str] = typer.Option(None, "--before", help="Only results before date (YYYY-MM-DD)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Synthesized answer via Perplexity sonar-pro (~$0.02/query)."""
    cmd = "ask"
    cache_parts = [query, str(domain), str(recency), context, str(after), str(before)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            emit(cached)
            return

    try:
        result = perplexity_ask(query, domains=_parse_domains(domain), recency=recency, context=context, after=after, before=before)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": result["model"], "cache_hit": False},
            answer=result["answer"],
            citations=result["citations"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        emit(response)
    except ResearchError as e:
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    domain: Optional[list[str]] = typer.Option(None, "--domain", "-d", help="Filter to specific domains"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Recency filter: day, week, month, year"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Raw web search results via Perplexity Search API (~$0.005/query)."""
    cmd = "search"
    cache_parts = [query, str(domain), str(recency), str(limit)]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            emit(cached)
            return

    try:
        result = perplexity_search(query, domains=_parse_domains(domain), recency=recency, limit=limit)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": "search", "cache_hit": False},
            results=result["results"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        emit(response)
    except ResearchError as e:
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command()
def reason(
    query: str = typer.Argument(..., help="Complex question requiring reasoning"),
    domain: Optional[list[str]] = typer.Option(None, "--domain", "-d", help="Filter to specific domains"),
    recency: Optional[str] = typer.Option(None, "--recency", "-r", help="Recency filter: day, week, month, year"),
    context: str = typer.Option("high", "--context", "-c", help="Search context size: low, medium, high"),
    effort: str = typer.Option("high", "--effort", "-e", help="Reasoning effort: low, medium, high"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
) -> None:
    """Deep reasoning via Perplexity sonar-reasoning-pro (~$0.02/query)."""
    cmd = "reason"
    cache_parts = [query, str(domain), str(recency), context, effort]

    if not no_cache:
        cached = cache_get(cmd, *cache_parts)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            emit(cached)
            return

    try:
        result = perplexity_reason(query, domains=_parse_domains(domain), recency=recency, context=context, effort=effort)
        response = output_success(
            cmd,
            query,
            metadata={"backend": "perplexity", "model": result["model"], "cache_hit": False},
            answer=result["answer"],
            citations=result["citations"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        emit(response)
    except ResearchError as e:
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
            emit(cached)
            return

    try:
        result = context7_docs(library, query, max_tokens=max_tokens)
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
        emit(response)
    except ResearchError as e:
        emit(output_error(cmd, e))
        raise typer.Exit(code=1)


@app.command(name="map")
def map_cmd(
    url: str = typer.Argument(..., help="URL to map"),
    search_kw: Optional[str] = typer.Option(None, "--search", "-s", help="Filter discovered URLs by keyword"),
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
            emit(cached)
            return

    try:
        result = firecrawl_map(url, search=search_kw, limit=limit)
        response = output_success(
            cmd,
            url,
            metadata={"backend": "firecrawl", "cache_hit": False},
            discovered_urls=result["discovered_urls"],
        )
        if not no_cache:
            cache_set(cmd, *cache_parts, value=response)
        emit(response)
    except ResearchError as e:
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
            emit(cached)
            return

    try:
        result = firecrawl_scrape(url)
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
        emit(response)
    except ResearchError as e:
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


if __name__ == "__main__":
    app()
