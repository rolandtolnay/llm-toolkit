import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "youtube.py"


def load_youtube_module():
    spec = importlib.util.spec_from_file_location("youtube_under_test", SCRIPT)
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


def sample_video(video_id="v1"):
    return {
        "video_id": video_id,
        "title": "Title",
        "channel": "Channel",
        "upload_date": "2026-05-01",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "view_count": 10,
        "like_count": 1,
        "duration": 60,
        "description_preview": "desc",
    }


def invoke_search(module, *args):
    return CliRunner().invoke(module.app, ["search", *args])


def fail_if_called(*args, **kwargs):
    raise AssertionError("unexpected call")


def test_transcript_command_returns_full_text(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_get(url, params, headers, timeout):
        assert module.YOUTUBE_TRANSCRIPT_PATH in url
        return FakeResponse({"transcript_only_text": "hello   world  transcript"})

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = CliRunner().invoke(module.app, ["transcript", "https://www.youtube.com/watch?v=abc12345"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["transcript"] == "hello world transcript"
    assert data["video_id"] == "abc12345"
    assert data["metadata"]["backend"] == "scrapecreators"


def test_transcript_command_falls_back_to_free_backend(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_get(url, params, headers, timeout):
        return FakeResponse({}, status_code=500)

    monkeypatch.setattr(module.requests, "get", fake_get)
    monkeypatch.setattr(module, "_fetch_transcript", lambda vid: ("free transcript text", None))

    result = CliRunner().invoke(module.app, ["transcript", "https://youtu.be/abc12345"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["transcript"] == "free transcript text"
    assert data["metadata"]["backend"] == "yt-dlp"
    assert any("scrapecreators" in w for w in data["metadata"]["warnings"])


def test_transcript_command_total_failure_is_error(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_get(url, params, headers, timeout):
        return FakeResponse({}, status_code=500)

    monkeypatch.setattr(module.requests, "get", fake_get)
    monkeypatch.setattr(module, "_fetch_transcript", lambda vid: (None, "no captions"))

    result = CliRunner().invoke(module.app, ["transcript", "https://youtu.be/abc12345"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["error"]["code"] == "TRANSCRIPT_UNAVAILABLE"


def test_comments_command_normalizes_and_caps(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_get(url, params, headers, timeout):
        assert module.YOUTUBE_COMMENTS_PATH in url
        assert params["order"] == "top"
        return FakeResponse({
            "comments": [
                {
                    "content": f"comment {i}",
                    "author": {"name": f"user{i}", "isCreator": i == 0},
                    "engagement": {"likes": i, "replies": 0},
                    "publishedTime": "2026-01-01T00:00:00Z",
                }
                for i in range(5)
            ],
            "continuationToken": "tok",
        })

    monkeypatch.setattr(module.requests, "get", fake_get)

    result = CliRunner().invoke(
        module.app, ["comments", "https://www.youtube.com/watch?v=abc12345", "--limit", "2"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert len(data["comments"]) == 2
    assert data["comments"][0]["author"] == "user0"
    assert data["comments"][0]["is_creator"] is True
    assert data["metadata"]["continuation_token"] == "tok"


def test_comments_command_requires_api_key(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "")

    result = CliRunner().invoke(module.app, ["comments", "https://www.youtube.com/watch?v=abc12345"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["error"]["code"] == "MISSING_API_KEY"


def test_scrapecreators_search_normalizes_video_fields(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_get(url, params, headers, timeout):
        return FakeResponse(
            {
                "videos": [
                    {
                        "id": "abc123",
                        "title": "A video",
                        "channel": {"title": "A channel"},
                        "publishedTime": "2026-05-20T12:34:56Z",
                        "url": "https://youtu.be/abc123",
                        "viewCountInt": 1234,
                        "likeCountInt": 56,
                        "lengthSeconds": 321,
                        "description": "x" * 250,
                    }
                ]
            }
        )

    monkeypatch.setattr(module.requests, "get", fake_get)

    videos, cache_hit, credits, error = module._scrapecreators_search("query", 10, None)

    assert error is None
    assert cache_hit is False
    assert credits == 1
    assert videos == [
        {
            "video_id": "abc123",
            "title": "A video",
            "channel": "A channel",
            "upload_date": "2026-05-20",
            "url": "https://youtu.be/abc123",
            "view_count": 1234,
            "like_count": 56,
            "duration": 321,
            "description_preview": "x" * 200,
        }
    ]


def test_scrapecreators_search_sends_upload_date_and_caps(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    seen = {}

    def fake_get(url, params, headers, timeout):
        seen.update(params)
        return FakeResponse({"videos": [{"id": "v1"}, {"id": "v2"}, {"id": "v3"}]})

    monkeypatch.setattr(module.requests, "get", fake_get)

    videos, _, _, error = module._scrapecreators_search("query", 2, "this_month")

    assert error is None
    assert seen["uploadDate"] == "this_month"
    assert [video["video_id"] for video in videos] == ["v1", "v2"]


def test_scrapecreators_search_failure_counts_uncached_request(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module.requests, "get", lambda *args, **kwargs: FakeResponse({}, status_code=500))

    videos, cache_hit, credits, error = module._scrapecreators_search("query", 10, None)

    assert videos == []
    assert cache_hit is False
    assert credits == 1
    assert error is not None



def test_transcript_normalization_prefers_plain_text_and_collapses_whitespace(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(
        module.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"transcript_only_text": " hello\n\n  world\t "}),
    )

    text, cache_hit, credits, error = module._scrapecreators_fetch_transcript("https://youtu.be/v1")

    assert (text, cache_hit, credits, error) == ("hello world", False, 1, None)


def test_transcript_normalization_joins_segments(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(
        module.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"transcript": [{"text": "hello"}, {"text": "world"}]}),
    )

    text, _, _, error = module._scrapecreators_fetch_transcript("https://youtu.be/v1")

    assert error is None
    assert text == "hello world"


def test_empty_transcript_response_returns_none(monkeypatch):
    module = load_youtube_module()
    no_cache(monkeypatch, module)
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module.requests, "get", lambda *args, **kwargs: FakeResponse({"transcript": []}))

    text, cache_hit, credits, error = module._scrapecreators_fetch_transcript("https://youtu.be/v1")

    assert text is None
    assert cache_hit is False
    assert credits == 1
    assert error == "empty_transcript"


def test_missing_api_key_uses_free_fallback_for_search_and_transcript(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "")
    monkeypatch.setattr(module, "_has_ytdlp", lambda: True)
    monkeypatch.setattr(module, "_ytdlp_search", lambda query, max_videos, after: [sample_video()])
    monkeypatch.setattr(module, "_fetch_transcript", lambda video_id: ("fallback transcript", None))
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)

    result = invoke_search(module, "query", "--no-preprocess")

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["metadata"]["backend"] == "yt-dlp"
    assert data["videos"][0]["raw_transcript"] == "fallback transcript"


def test_scrapecreators_search_failure_uses_ytdlp(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module, "_scrapecreators_search", lambda *args: ([], False, 1, "api_error"))
    monkeypatch.setattr(module, "_has_ytdlp", lambda: True)
    monkeypatch.setattr(module, "_ytdlp_search", lambda query, max_videos, after: [sample_video()])
    monkeypatch.setattr(module, "_scrapecreators_fetch_transcript", lambda url: ("sc transcript", False, 1, None))
    monkeypatch.setattr(module, "_fetch_transcript", fail_if_called)
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)

    result = invoke_search(module, "query", "--no-preprocess")

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["metadata"]["backend"] == "mixed"
    assert data["videos"][0]["raw_transcript"] == "sc transcript"


def test_scrapecreators_transcript_failure_uses_free_fallback_and_reports_mixed(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module, "_scrapecreators_search", lambda *args: ([sample_video()], False, 1, None))
    monkeypatch.setattr(module, "_scrapecreators_fetch_transcript", lambda url: (None, False, 1, "api_error"))
    monkeypatch.setattr(module, "_fetch_transcript", lambda video_id: ("fallback transcript", None))
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)

    result = invoke_search(module, "query", "--no-preprocess")

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["metadata"]["backend"] == "mixed"
    assert data["metadata"]["cache_hit"] is False
    assert data["videos"][0]["raw_transcript"] == "fallback transcript"


def test_transcript_word_does_not_trigger_ip_block(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "_fetch_transcript_api", lambda video_id: (None, "transcript unavailable"))
    monkeypatch.setattr(module, "_fetch_transcript_ytdlp", lambda video_id: (None, "no transcript file"))

    text, reason = module._fetch_transcript("v1")

    assert text is None
    assert reason is not None
    assert not reason.startswith("ip_blocked")


def test_zero_transcripts_after_both_attempts_returns_failure(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module, "_scrapecreators_search", lambda *args: ([sample_video()], False, 1, None))
    monkeypatch.setattr(module, "_scrapecreators_fetch_transcript", lambda url: (None, False, 1, "empty_transcript"))
    monkeypatch.setattr(module, "_fetch_transcript", lambda video_id: (None, "no_english_transcript"))
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)

    result = invoke_search(module, "query", "--no-preprocess")

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["metadata"]["transcripts_fetched"] == 0
    assert data["videos"][0]["transcript_available"] is False


def test_after_rejects_exact_dates_before_backend_work(monkeypatch):
    module = load_youtube_module()
    called = False

    def fail_if_called(*args):
        nonlocal called
        called = True
        return [], False, 0, None

    monkeypatch.setattr(module, "_scrapecreators_search", fail_if_called)

    result = invoke_search(module, "query", "--after", "2026-01-01")

    assert result.exit_code != 0
    assert called is False
    assert "this_month" in result.stderr


def test_after_accepts_coarse_filter(monkeypatch):
    module = load_youtube_module()
    seen = {}
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")

    def fake_search(query, max_videos, after):
        seen["after"] = after
        return [], False, 1, None

    monkeypatch.setattr(module, "_scrapecreators_search", fake_search)
    monkeypatch.setattr(module, "_log_call", lambda *args, **kwargs: None)

    result = invoke_search(module, "query", "--after", "this_month")

    assert result.exit_code == 0
    assert seen["after"] == "this_month"


def test_scrapecreators_search_uses_cache_without_request(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    cached = [sample_video("cached")]
    monkeypatch.setattr(module, "_cache_get", lambda *args: cached)
    monkeypatch.setattr(module.requests, "get", fail_if_called)

    videos, cache_hit, credits, error = module._scrapecreators_search("query", 10, "this_week")

    assert error is None
    assert cache_hit is True
    assert credits == 0
    assert videos == cached


def test_scrapecreators_transcript_uses_cache_without_request(monkeypatch):
    module = load_youtube_module()
    monkeypatch.setattr(module, "SCRAPECREATORS_API_KEY", "key")
    monkeypatch.setattr(module, "_cache_get", lambda *args: "cached transcript")
    monkeypatch.setattr(module.requests, "get", fail_if_called)

    text, cache_hit, credits, error = module._scrapecreators_fetch_transcript("https://youtu.be/v1")

    assert error is None
    assert cache_hit is True
    assert credits == 0
    assert text == "cached transcript"
