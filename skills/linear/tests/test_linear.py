import importlib.util
import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "linear.py"


def load_linear_module():
    spec = importlib.util.spec_from_file_location("linear_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before exec: @dataclass annotation resolution (with
    # `from __future__ import annotations`) looks the module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TEAMS = [
    {"id": "team-eng-uuid", "key": "ENG", "name": "Engineering"},
    {"id": "team-ops-uuid", "key": "OPS", "name": "Operations"},
]


def parent_issue(team=None):
    """A canned parent issue for get_issue (QUERY_ISSUE), carrying its team."""
    return {
        "id": "issue-uuid",
        "identifier": "ABC-123",
        "title": "Parent title",
        "url": "https://linear.app/x/issue/ABC-123",
        "state": {"name": "Todo"},
        "team": team or {"id": "team-eng-uuid", "key": "ENG", "name": "Engineering"},
        "labels": {"nodes": []},
        "project": None,
    }


def route(query, variables, *, teams, calls):
    """Shared canned-response router keyed by the GraphQL query text."""
    calls.append((query, variables))
    if "issueCreate" in query:
        title = (variables or {}).get("input", {}).get("title", "")
        return {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "sub-uuid",
                    "identifier": "ABC-124",
                    "title": title,
                    "url": "https://linear.app/x/issue/ABC-124",
                    "state": {"name": "Todo"},
                },
            }
        }
    if "issueUpdate" in query:
        return {
            "issueUpdate": {
                "success": True,
                "issue": {
                    "identifier": "ABC-123",
                    "title": "Parent title",
                    "url": "https://linear.app/x/issue/ABC-123",
                    "state": {"name": "Todo"},
                    "labels": {"nodes": []},
                },
            }
        }
    if "issue(id: $id)" in query:
        return {"issue": parent_issue()}
    if "teams {" in query:
        return {"teams": {"nodes": teams, "pageInfo": {"hasNextPage": False}}}
    raise AssertionError(f"unexpected query: {query[:60]!r}")


def make_client(module, teams=TEAMS):
    """Build a LinearClient whose _request is a canned router; records calls."""
    client = module.LinearClient(api_key="test")
    calls = []
    client._request = lambda query, variables=None: route(
        query, variables, teams=teams, calls=calls
    )
    client.calls = calls
    return client


def install_cli_request(monkeypatch, module, teams=TEAMS):
    """Patch LinearClient._request at the class level for CLI-driven tests."""
    calls = []

    def fake_request(self, query, variables=None):
        return route(query, variables, teams=teams, calls=calls)

    monkeypatch.setattr(module.LinearClient, "_request", fake_request)
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    return calls


# ---------------------------------------------------------------------------
# find_team_by_ref
# ---------------------------------------------------------------------------


def test_find_team_by_ref_matches_key_case_insensitively():
    module = load_linear_module()
    client = make_client(module)
    assert client.find_team_by_ref("eng")["id"] == "team-eng-uuid"


def test_find_team_by_ref_matches_uuid():
    module = load_linear_module()
    client = make_client(module)
    assert client.find_team_by_ref("team-ops-uuid")["key"] == "OPS"


def test_find_team_by_ref_matches_partial_name():
    module = load_linear_module()
    client = make_client(module)
    assert client.find_team_by_ref("ngineer")["id"] == "team-eng-uuid"


def test_find_team_by_ref_miss_raises_team_not_found():
    module = load_linear_module()
    client = make_client(module)
    with pytest.raises(module.LinearError) as exc:
        client.find_team_by_ref("nope")
    assert exc.value.code == module.ErrorCode.TEAM_NOT_FOUND


# ---------------------------------------------------------------------------
# resolve_config precedence
# ---------------------------------------------------------------------------


def test_resolve_config_flag_beats_env_and_file(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_TEAM", "OPS")
    monkeypatch.setattr(
        module, "_load_config_optional", lambda *a, **k: module.LinearConfig(team_id="team-ops-uuid")
    )
    client = make_client(module)

    config = module.resolve_config(client, "ENG")

    assert config.team_id == "team-eng-uuid"


def test_resolve_config_env_beats_file(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_TEAM", "OPS")
    monkeypatch.setattr(
        module, "_load_config_optional", lambda *a, **k: module.LinearConfig(team_id="team-file-uuid")
    )
    client = make_client(module)

    config = module.resolve_config(client, None)

    assert config.team_id == "team-ops-uuid"


def test_resolve_config_file_beats_autodetect_without_team_query(monkeypatch):
    module = load_linear_module()
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    monkeypatch.setattr(
        module, "_load_config_optional", lambda *a, **k: module.LinearConfig(team_id="team-file-uuid")
    )
    client = make_client(module)

    config = module.resolve_config(client, None)

    assert config.team_id == "team-file-uuid"
    # No flag/env ref and a file present → never queries the teams list.
    assert all("teams {" not in q for q, _ in client.calls)


def test_resolve_config_single_team_autodetect(monkeypatch):
    module = load_linear_module()
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    monkeypatch.setattr(module, "_load_config_optional", lambda *a, **k: None)
    client = make_client(module, teams=[TEAMS[0]])

    config = module.resolve_config(client, None)

    assert config.team_id == "team-eng-uuid"


def test_resolve_config_multi_team_no_selection_raises_missing_config(monkeypatch):
    module = load_linear_module()
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    monkeypatch.setattr(module, "_load_config_optional", lambda *a, **k: None)
    client = make_client(module)

    with pytest.raises(module.LinearError) as exc:
        module.resolve_config(client, None)

    assert exc.value.code == module.ErrorCode.MISSING_CONFIG
    # Available team keys are surfaced to the user.
    assert any("ENG" in s and "OPS" in s for s in exc.value.suggestions)


# ---------------------------------------------------------------------------
# config-merge rule
# ---------------------------------------------------------------------------


def test_resolve_config_drops_project_id_when_team_overridden(monkeypatch):
    module = load_linear_module()
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    file_config = module.LinearConfig(
        team_id="team-ops-uuid",
        project_id="proj-ops-uuid",
        default_priority=1,
        default_labels=["mobile"],
    )
    monkeypatch.setattr(module, "_load_config_optional", lambda *a, **k: file_config)
    client = make_client(module)

    # Override to a *different* team via flag.
    config = module.resolve_config(client, "ENG")

    assert config.team_id == "team-eng-uuid"
    assert config.project_id is None  # team-scoped UUID dropped
    assert config.default_priority == 1  # other defaults kept
    assert config.default_labels == ["mobile"]


def test_resolve_config_keeps_file_when_team_matches(monkeypatch):
    module = load_linear_module()
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    file_config = module.LinearConfig(
        team_id="team-eng-uuid",
        project_id="proj-eng-uuid",
        default_priority=2,
        default_labels=["backend"],
    )
    monkeypatch.setattr(module, "_load_config_optional", lambda *a, **k: file_config)
    client = make_client(module)

    # Flag names the same team the file already points at.
    config = module.resolve_config(client, "ENG")

    assert config is file_config
    assert config.project_id == "proj-eng-uuid"


# ---------------------------------------------------------------------------
# CLI: update / break need no config and no team lookup
# ---------------------------------------------------------------------------


def test_update_priority_needs_no_config_and_issues_no_team_query(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)

    result = CliRunner().invoke(module.app, ["update", "ABC-123", "-p", "2"])

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["result"]["identifier"] == "ABC-123"
    # The common path makes exactly one call (the update mutation) — no get_issue,
    # no teams query.
    assert len(calls) == 1
    assert "issueUpdate" in calls[0][0]


def test_break_derives_team_from_parent_without_config(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)

    result = CliRunner().invoke(
        module.app,
        ["break", "ABC-123", "--issues", '[{"title": "sub a"}, {"title": "sub b"}]'],
    )

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert len(data["result"]["created"]) == 2

    # No teams query was needed; the parent issue supplied the team.
    assert all("teams {" not in q for q, _ in calls)
    # Every sub-issue was created in the parent's team.
    create_calls = [v for q, v in calls if "issueCreate" in q]
    assert len(create_calls) == 2
    assert all(v["input"]["teamId"] == "team-eng-uuid" for v in create_calls)
