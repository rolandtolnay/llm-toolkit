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
        "labels": {"nodes": [{"id": "label-parent-uuid", "name": "parent-label"}]},
        "project": {"id": "proj-parent-uuid", "name": "Parent Project"},
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
    for operation in ("commentCreate", "commentUpdate"):
        if operation in query:
            return {operation: {
                "success": True,
                "comment": {
                    "id": "comment-uuid",
                    "url": "https://linear.app/x/issue/ABC-123#comment",
                    "issue": {"identifier": "ABC-123", "title": "Parent title"},
                },
            }}
    if "issue(id: $id)" in query:
        return {"issue": parent_issue()}
    if "teams {" in query:
        return {"teams": {"nodes": teams, "pageInfo": {"hasNextPage": False}}}
    if "labels" in query and "team(id: $teamId)" in query:
        team_id = (variables or {}).get("teamId")
        team = next(t for t in teams if t["id"] == team_id)
        return {
            "team": {
                **team,
                "labels": {
                    "nodes": [{"id": f"label-{team['key'].lower()}-uuid", "name": "backend"}],
                    "pageInfo": {"hasNextPage": False},
                },
            }
        }
    if "cycles(" in query:
        return {
            "team": {
                "cycles": {
                    "nodes": [
                        {
                            "id": "cycle-active-uuid",
                            "number": 12,
                            "name": "Active Cycle",
                            "startsAt": "2026-06-01",
                            "endsAt": "2026-06-14",
                            "completedAt": None,
                            "progress": 0.5,
                            "isActive": True,
                            "isNext": False,
                            "isPast": False,
                            "isFuture": False,
                            "issues": {"pageInfo": {"hasNextPage": False}, "nodes": []},
                        }
                    ]
                }
            }
        }
    if "issues(filter:" in query:
        return {
            "issues": {
                "pageInfo": {"hasNextPage": False, "endCursor": "issue-uuid"},
                "nodes": [
                    {
                        "id": "issue-uuid",
                        "identifier": "ABC-123",
                        "title": "Parent title",
                        "priority": 3,
                        "estimate": None,
                        "state": {"id": "state-uuid", "name": "Todo", "type": "unstarted"},
                        "assignee": None,
                        "creator": None,
                        "project": None,
                        "projectMilestone": None,
                        "cycle": {"id": "cycle-active-uuid", "number": 12, "name": "Active Cycle"},
                        "labels": {"nodes": []},
                        "team": {"id": "team-ops-uuid", "key": "OPS", "name": "Operations"},
                    }
                ]
            }
        }
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


def test_resolve_config_accepts_defaults_only_file_with_flag(monkeypatch, tmp_path):
    module = load_linear_module()
    config_path = tmp_path / ".linear.json"
    config_path.write_text(
        json.dumps({"defaultPriority": 1, "defaultLabels": ["backend"]})
    )
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    monkeypatch.setattr(module, "find_config_file", lambda: config_path)
    client = make_client(module)

    config = module.resolve_config(client, "ENG")

    assert config.team_id == "team-eng-uuid"
    assert config.project_id is None
    assert config.default_priority == 1
    assert config.default_labels == ["backend"]


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


def test_update_label_uses_linear_team_env_for_name_resolution(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)
    monkeypatch.setenv("LINEAR_TEAM", "OPS")

    result = CliRunner().invoke(module.app, ["update", "ABC-123", "--label", "backend"])

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True

    label_queries = [(q, v) for q, v in calls if "labels" in q and "team(id: $teamId)" in q]
    assert len(label_queries) == 1
    assert label_queries[0][1]["teamId"] == "team-ops-uuid"

    update_input = next(v["input"] for q, v in calls if "issueUpdate" in q)
    assert update_input["labelIds"] == ["label-ops-uuid"]
    assert "removedLabelIds" not in update_input


def test_update_clears_labels_without_fetching_current_issue(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)

    result = CliRunner().invoke(module.app, ["update", "ABC-123", "--no-labels"])

    assert result.exit_code == 0, result.stdout
    assert len(calls) == 1
    assert calls[0][1]["input"] == {"labelIds": []}


def test_list_cycle_uses_linear_team_env_for_cycle_resolution(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)
    monkeypatch.setenv("LINEAR_TEAM", "OPS")

    result = CliRunner().invoke(module.app, ["list", "--cycle", "active", "--verbose"])

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["metadata"]["count"] == 1

    cycle_call = next(v for q, v in calls if "cycles(" in q)
    assert cycle_call["teamId"] == "team-ops-uuid"

    issues_call = next(v for q, v in calls if "issues(filter:" in q)
    assert issues_call["filter"]["team"]["id"]["eq"] == "team-ops-uuid"
    assert issues_call["filter"]["cycle"]["id"]["eq"] == "cycle-active-uuid"


def test_create_parent_derives_team_uuid_project_and_labels_without_config(monkeypatch):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)

    result = CliRunner().invoke(module.app, ["create", "sub task", "--parent", "ABC-123"])

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True

    create_input = next(v["input"] for q, v in calls if "issueCreate" in q)
    assert create_input["teamId"] == "team-eng-uuid"
    assert create_input["parentId"] == "issue-uuid"
    assert create_input["projectId"] == "proj-parent-uuid"
    assert create_input["labelIds"] == ["label-parent-uuid"]
    assert all("teams {" not in q for q, _ in calls)


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


# ---------------------------------------------------------------------------
# CLI: update-comment edits in place and surfaces API failures
# ---------------------------------------------------------------------------


def test_update_comment_replaces_body_in_place(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    comment_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    body = '## Revised decision\n\nKeep **café** and "quoted text".\n'
    calls = []

    def fake_post(self, url, *, headers, json):
        calls.append(json)
        assert url == module.LINEAR_API_URL
        assert headers["Authorization"] == "test"
        assert "commentUpdate(id: $id, input: $input)" in json["query"]
        assert "commentCreate" not in json["query"]
        assert "commentDelete" not in json["query"]
        assert json["variables"] == {"id": comment_id, "input": {"body": body}}
        return module.httpx.Response(200, json={
            "data": {"commentUpdate": {
                "success": True,
                "comment": {
                    "id": comment_id,
                    "body": body,
                    "url": "https://linear.app/x/issue/ABC-123#comment",
                    "issue": {"identifier": "ABC-123", "title": "Parent title"},
                },
            }},
        })

    monkeypatch.setattr(module.httpx.Client, "post", fake_post)

    result = CliRunner().invoke(module.app, ["update-comment", comment_id, body])

    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["command"] == "update-comment"
    assert data["result"]["commentId"] == comment_id
    assert data["result"]["identifier"] == "ABC-123"
    assert data["result"]["url"] == "https://linear.app/x/issue/ABC-123#comment"
    assert len(calls) == 1  # No lookup, deletion, or replacement comment creation.


def test_get_comments_exposes_uuid_for_update_and_delete(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    comment = {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "body": "Handoff",
        "createdAt": "2026-09-25T10:05:01.364Z",
        "user": {"name": "Roland"},
    }
    issue = {
        **parent_issue(),
        "comments": {"pageInfo": {"hasNextPage": False}, "nodes": [comment]},
    }
    monkeypatch.setattr(module.LinearClient, "_request", lambda self, query, variables=None: {"issue": issue})

    result = CliRunner().invoke(module.app, ["get", "ABC-123", "--comments"])

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["result"]["comments"][0]["id"] == comment["id"]


@pytest.mark.parametrize("response", [
    {"data": {"commentUpdate": {"success": False}}},
    {"errors": [{"message": "You do not have permission to edit this comment"}]},
])
def test_update_comment_api_failure_returns_json_and_nonzero_exit(monkeypatch, response):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    monkeypatch.setattr(
        module.httpx.Client, "post",
        lambda *args, **kwargs: module.httpx.Response(200, json=response),
    )

    result = CliRunner().invoke(module.app, ["update-comment", "comment-uuid", "New body"])

    assert result.exit_code == 1, result.stdout
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["command"] == "update-comment"
    assert data["error"]["code"] == "API_ERROR"
    assert "result" not in data


def test_update_comment_requires_body_without_making_request(monkeypatch):
    module = load_linear_module()

    def unexpected_post(*args, **kwargs):
        pytest.fail("Missing body must not trigger an API request")

    monkeypatch.setenv("LINEAR_API_KEY", "test")
    monkeypatch.setattr(module.httpx.Client, "post", unexpected_post)

    result = CliRunner().invoke(module.app, ["update-comment", "comment-uuid"])

    assert result.exit_code == 2


@pytest.mark.parametrize("args,flag,operation,field", [
    (["create", "New ticket", "--parent", "ABC-123"], "--description-file", "issueCreate", "description"),
    (["update", "ABC-123"], "--description-file", "issueUpdate", "description"),
    (["comment", "ABC-123"], "--body-file", "commentCreate", "body"),
    (["update-comment", "comment-uuid"], "--body-file", "commentUpdate", "body"),
])
def test_markdown_file_reaches_mutation_unchanged(monkeypatch, tmp_path, args, flag, operation, field):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)
    # Include Linear's link serialization, literal shell syntax, Unicode and CRLF.
    text = '## Café\r\n\r\n- [ ] Keep `$HOME` and "quotes".\r\n[doc](<https://example.com/a_(b)>)\r\n\r\n'
    source = tmp_path / "body with spaces.md"
    source.write_bytes(text.encode("utf-8"))

    result = CliRunner().invoke(module.app, args + [flag, str(source)])

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["success"] is True
    mutations = [v["input"] for q, v in calls if operation in q]
    assert len(mutations) == 1
    assert mutations[0][field] == text


def test_empty_description_file_explicitly_clears_description(monkeypatch, tmp_path):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)
    source = tmp_path / "empty.md"
    source.write_bytes(b"")

    result = CliRunner().invoke(module.app, ["update", "ABC-123", "--description-file", str(source)])

    assert result.exit_code == 0, result.stdout
    assert calls[0][1]["input"] == {"description": ""}


@pytest.mark.parametrize("case,code", [
    ("both", "INVALID_INPUT"), ("missing", "FILE_NOT_FOUND"), ("invalid-utf8", "INVALID_INPUT"),
])
def test_invalid_text_source_fails_before_any_request(monkeypatch, tmp_path, case, code):
    module = load_linear_module()
    calls = install_cli_request(monkeypatch, module)
    source = tmp_path / "body.md"
    args = ["update", "ABC-123", "--description-file", str(source)]
    if case == "both":
        source.write_text("file text", encoding="utf-8")
        args += ["-d", "inline text"]
    elif case == "invalid-utf8":
        source.write_bytes(b"\xff")

    result = CliRunner().invoke(module.app, args)

    assert result.exit_code == 1, result.stdout
    assert json.loads(result.stdout)["error"]["code"] == code
    assert calls == []


def test_graphql_validation_diagnostics_exclude_values_and_targets(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    response = {"errors": [{
        "message": "Argument Validation Error",
        "extensions": {
            "userPresentableMessage": "Choose one label update mode",
            "exception": {"validationErrors": [{
                "property": "input",
                "target": {"description": "private ticket contents"},
                "children": [{
                    "property": "labelIds", "value": "private field value",
                    "constraints": {"exclusive": "Cannot combine labelIds and removedLabelIds"},
                }],
            }]},
        },
    }, {"message": "Additional validation failure"}]}
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return module.httpx.Response(400, json=response)

    monkeypatch.setattr(module.httpx.Client, "post", fake_post)

    result = CliRunner().invoke(module.app, ["update", "ABC-123", "-p", "2"])

    assert result.exit_code == 1, result.stdout
    error = json.loads(result.stdout)["error"]
    assert error["code"] == "API_ERROR"
    assert "Argument Validation Error" in error["message"]
    assert "Additional validation failure" in error["message"]
    assert "Choose one label update mode" in error["suggestions"]
    assert "input.labelIds: Cannot combine labelIds and removedLabelIds" in error["suggestions"]
    assert "private" not in result.stdout
    assert len(calls) == 1  # Surface the failure; never retry mutations automatically.
