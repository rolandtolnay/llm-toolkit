"""Unit tests for the Perplexity Agent API response parser and date conversion.

Run with:
    uv run --with pytest --with typer --with httpx --with pyyaml --with diskcache \
        pytest skills/research/tests/test_perplexity.py
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "research.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("research_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


research = _load_module()


def _agent_response(**overrides):
    base = {
        "status": "completed",
        "model": "openai/gpt-6-luna",
        "effort": "low@2026-10-24.0",
        "output": [
            {
                "type": "search_results",
                "queries": ["uv release"],
                "results": [
                    {"id": 1, "url": "https://pypi.org/project/uv/", "title": "uv", "snippet": "...", "date": "2026-10-27"},
                    {"id": 2, "url": "https://docs.astral.sh/uv/", "title": "uv docs", "snippet": "..."},
                ],
            },
            {
                "type": "search_results",
                "queries": ["uv changelog"],
                "results": [
                    {"id": 3, "url": "https://github.com/astral-sh/uv/releases", "title": "Releases", "snippet": "..."},
                    {"id": 1, "url": "https://pypi.org/project/uv/", "title": "uv", "snippet": "dup"},
                ],
            },
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "uv 0.13.6 is current[web:1][web:3].", "annotations": []}],
            },
        ],
        "usage": {
            "input_tokens": 5534,
            "output_tokens": 30,
            "cost": {"total_cost": 0.00151, "currency": "USD"},
            "tool_calls_details": {"search_web": {"invocation": 2, "cost_usd": 0.002}},
        },
    }
    base.update(overrides)
    return base


def test_parse_merges_search_results_across_steps_and_dedupes_ids():
    result = research.parse_agent_response(_agent_response())

    assert result["answer"] == "uv 0.13.6 is current[web:1][web:3]."
    assert [s["id"] for s in result["sources"]] == [1, 2, 3]
    assert result["sources"][0] == {"id": 1, "url": "https://pypi.org/project/uv/", "title": "uv", "date": "2026-10-27"}
    assert "date" not in result["sources"][1]
    assert result["effort"] == "low@2026-10-24.0"
    assert result["model"] == "openai/gpt-6-luna"
    assert result["cost_usd"] == pytest.approx(0.00151)
    assert result["usage"] == {"input_tokens": 5534, "output_tokens": 30, "searches": 2, "url_fetches": 0}
    assert "incomplete" not in result


def test_parse_sorts_sources_by_id_regardless_of_output_order():
    data = _agent_response()
    data["output"][0], data["output"][1] = data["output"][1], data["output"][0]
    result = research.parse_agent_response(data)
    assert [s["id"] for s in result["sources"]] == [1, 2, 3]


def test_parse_concatenates_multiple_message_items():
    data = _agent_response()
    data["output"].append(
        {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Second part."}]}
    )
    result = research.parse_agent_response(data)
    assert result["answer"] == "uv 0.13.6 is current[web:1][web:3].\n\nSecond part."


def test_parse_surfaces_incomplete_details_without_dropping_answer():
    data = _agent_response(status="incomplete", incomplete_details={"reason": "max_steps"})
    result = research.parse_agent_response(data)
    assert result["answer"].startswith("uv 0.13.6")
    assert result["incomplete"] == {"reason": "max_steps"}


def test_parse_raises_on_failed_run():
    data = _agent_response(status="failed", error={"type": "overloaded", "message": "upstream capacity"})
    with pytest.raises(research.ResearchError) as exc:
        research.parse_agent_response(data)
    assert exc.value.code == research.ErrorCode.API_ERROR
    assert "upstream capacity" in exc.value.message


def test_parse_tolerates_missing_usage_and_sources():
    result = research.parse_agent_response(
        {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "hi"}]}]}
    )
    assert result["answer"] == "hi"
    assert result["sources"] == []
    assert result["cost_usd"] is None
    assert result["usage"]["searches"] == 0


def test_to_api_date_converts_iso_to_us_format():
    assert research._to_api_date("2026-03-01", "--after") == "03/01/2026"
    assert research._to_api_date(None, "--after") is None


def test_to_api_date_rejects_other_formats():
    with pytest.raises(research.ResearchError) as exc:
        research._to_api_date("03/01/2026", "--before")
    assert "--before" in exc.value.message
    assert "YYYY-MM-DD" in exc.value.message


def test_search_filters_puts_dates_in_api_format():
    filters = research._search_filters(domains=["stripe.com"], recency="month", after="2026-01-15", before=None)
    assert filters == {
        "search_domain_filter": ["stripe.com"],
        "search_recency_filter": "month",
        "search_after_date_filter": "01/15/2026",
    }
