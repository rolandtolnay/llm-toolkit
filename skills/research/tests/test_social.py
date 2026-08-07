import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "social.py"


def load_social_module():
    spec = importlib.util.spec_from_file_location("social_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.data


def no_cache(monkeypatch, module):
    monkeypatch.setattr(module, "_cache_get", lambda *args: None)
    monkeypatch.setattr(module, "_cache_set", lambda *args, **kwargs: None)


def setup_module_for_cli(monkeypatch, module):
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)


def sample_post(post_id="p1", title="Best pedestal fan", score=42):
    return {
        "id": post_id,
        "title": title,
        "permalink": f"/r/fans/comments/{post_id}/x/",
        "subreddit": "fans",
        "created_utc": 1750000000,
        "score": score,
        "num_comments": 5,
        "selftext": "Looking for a quiet pedestal fan recommendation",
    }


def invoke(module, *args):
    return CliRunner().invoke(module.app, list(args))


def test_reddit_defaults_to_all_timeframe_and_relevance_sort(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)
    monkeypatch.setattr(module, "_discover_subreddits", lambda *a: [])

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        if url.endswith("/search"):
            captured.update(params)
            return FakeResponse({"posts": [sample_post()], "credits_charged": 1})
        if url.endswith("/post/comments"):
            return FakeResponse({"comments": [], "credits_charged": 1})
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "reddit", "pedestal fan")
    assert result.exit_code == 0, result.output
    assert captured["timeframe"] == "all"
    assert captured["sort"] == "relevance"

    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["metadata"]["timeframe"] == "all"
    assert data["metadata"]["credits_used"] >= 2  # search + comment fetch


def test_reddit_passes_explicit_timeframe_and_sort(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)
    monkeypatch.setattr(module, "_discover_subreddits", lambda *a: [])

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        if url.endswith("/search"):
            captured.update(params)
            return FakeResponse({"posts": [sample_post()], "credits_charged": 1})
        return FakeResponse({"comments": [], "credits_charged": 1})

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "reddit", "pedestal fan", "--timeframe", "month", "--sort", "top")
    assert result.exit_code == 0, result.output
    assert captured["timeframe"] == "month"
    assert captured["sort"] == "top"


def test_reddit_rejects_invalid_timeframe(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)

    result = invoke(module, "reddit", "q", "--timeframe", "fortnight")
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_ARGUMENT"


def test_reddit_provider_failure_is_an_error_not_empty_success(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse({}, status_code=500)

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "reddit", "pedestal fan")
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["error"]["code"] == "PROVIDER_ERROR"


def test_reddit_cache_key_includes_question_and_timeframe(monkeypatch):
    module = load_social_module()
    key_a = module._cache_key("reddit", "q", "", "all", "relevance", "7", "why buy")
    key_b = module._cache_key("reddit", "q", "", "all", "relevance", "7", "")
    key_c = module._cache_key("reddit", "q", "", "month", "relevance", "7", "why buy")
    assert key_a != key_b
    assert key_a != key_c


def test_thread_flattens_nested_replies_with_depth(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)

    def fake_get(url, params=None, headers=None, timeout=None):
        assert url.endswith("/post/comments")
        return FakeResponse({
            "post": sample_post(),
            "comments": [
                {
                    "author": "alice",
                    "body": "Top level answer with plenty of detail",
                    "score": 10,
                    "created_utc": 1750000000,
                    "replies": {
                        "items": [
                            {
                                "author": "bob",
                                "body": "A nested reply that adds a counterpoint",
                                "score": 4,
                            }
                        ],
                        "more": {"has_more": False},
                    },
                },
                {"author": "[deleted]", "body": "[removed]", "score": 1},
                {"author": "carol", "body": "Another top-level perspective worth keeping", "score": 2},
            ],
            "more": {"has_more": True, "cursor": "abc123"},
            "credits_charged": 1,
        })

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "thread", "https://www.reddit.com/r/fans/comments/p1/x/")
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)

    authors = [(c["author"], c["depth"]) for c in data["comments"]]
    assert authors == [("alice", 0), ("bob", 1), ("carol", 0)]
    assert data["post"]["selftext"] == "Looking for a quiet pedestal fan recommendation"
    assert data["metadata"]["has_more"] is True
    assert data["metadata"]["next_cursor"] == "abc123"


def test_thread_respects_max_comments(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse({
            "post": sample_post(),
            "comments": [
                {"author": f"user{i}", "body": f"Comment number {i} with enough substance", "score": i}
                for i in range(10)
            ],
            "credits_charged": 1,
        })

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "thread", "https://www.reddit.com/r/fans/comments/p1/x/", "--max-comments", "3")
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert len(data["comments"]) == 3


def test_thread_provider_failure_is_error(monkeypatch):
    module = load_social_module()
    setup_module_for_cli(monkeypatch, module)

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse({}, status_code=502)

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = invoke(module, "thread", "https://www.reddit.com/r/fans/comments/p1/x/")
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["error"]["code"] == "PROVIDER_ERROR"
