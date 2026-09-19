import json

import pytest
from typer.testing import CliRunner

from test_linear import load_linear_module


VIEW_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def issue_page(number=1, *, more=False):
    return {
        "nodes": [{
            "identifier": f"ENG-{number}", "title": f"Issue {number}",
            "state": {"name": "Todo"}, "priority": 2, "estimate": 3,
            "labels": {"nodes": [{"name": "backend"}]},
        }],
        "pageInfo": {"hasNextPage": more, "endCursor": f"cursor-{number}"},
    }


@pytest.fixture
def api(monkeypatch):
    module = load_linear_module()
    monkeypatch.setenv("LINEAR_API_KEY", "test")
    monkeypatch.delenv("LINEAR_TEAM", raising=False)
    monkeypatch.setattr(module, "find_config_file", lambda: None)
    calls = []

    def install(respond):
        def post(self, url, *, headers, json):
            calls.append(json)
            return module.httpx.Response(200, json=respond(json["query"], json.get("variables", {})))
        monkeypatch.setattr(module.httpx.Client, "post", post)

    return module, calls, install


def test_list_continues_with_same_filters_and_reports_final_page(api):
    module, calls, install = api

    def respond(query, variables):
        assert "issues(filter: $filter, first: $first, after: $after)" in query
        assert "pageInfo { hasNextPage endCursor }" in query
        return {"data": {"issues": issue_page(2) if variables["after"] else issue_page(more=True)}}

    install(respond)
    args = ["list", "--priority", "high", "--state", "todo", "--estimate", "none", "--limit", "1"]
    first = CliRunner().invoke(module.app, args)
    assert first.exit_code == 0, first.stdout
    first_data = json.loads(first.stdout)
    assert "metadata" not in first_data  # Completeness is present even in concise output.
    assert first_data["result"]["pageInfo"]["hasNextPage"] is True
    cursor = first_data["result"]["pageInfo"]["endCursor"]

    second = CliRunner().invoke(module.app, args + ["--after", cursor, "-V"])
    assert second.exit_code == 0, second.stdout
    second_data = json.loads(second.stdout)
    assert second_data["result"]["pageInfo"]["hasNextPage"] is False
    assert second_data["metadata"]["count"] == second_data["metadata"]["limit"] == 1
    assert [first_data["result"]["issues"][0]["identifier"], second_data["result"]["issues"][0]["identifier"]] == ["ENG-1", "ENG-2"]
    assert first_data["result"]["issues"][0]["priority"] == "High"
    assert first_data["result"]["issues"][0]["labels"] == ["backend"]
    assert len(calls) == 2  # No automatic all-page traversal.
    assert calls[0]["variables"]["filter"] == calls[1]["variables"]["filter"] == {
        "priority": {"eq": 2}, "state": {"type": {"eq": "unstarted"}}, "estimate": {"null": True},
    }
    assert calls[1]["variables"]["after"] == "cursor-1"


@pytest.mark.parametrize("page_info,exit_code", [
    ({"hasNextPage": False, "endCursor": None}, 0),
    ({"hasNextPage": True, "endCursor": None}, 1),
    ({}, 1),
])
def test_empty_page_is_distinct_from_missing_completeness_evidence(api, page_info, exit_code):
    module, calls, install = api
    install(lambda q, v: {"data": {"issues": {"nodes": [], "pageInfo": page_info}}})
    result = CliRunner().invoke(module.app, ["list"])
    assert result.exit_code == exit_code, result.stdout
    data = json.loads(result.stdout)
    if exit_code:
        assert data["error"]["code"] == "INVALID_RESPONSE"
    else:
        assert data["result"] == {"issues": [], "pageInfo": page_info}
    assert len(calls) == 1


@pytest.mark.parametrize("flags,expected", [
    (["--name", "Wedding queue"], {"name": "Wedding queue"}),
    (["--private", "-d", "", "--filter-json", "{}"], {"shared": False, "description": "", "filterData": {}}),
])
def test_update_view_preserves_identity_and_unspecified_fields(api, flags, expected):
    module, calls, install = api
    stored = {
        "id": VIEW_ID, "name": "Wedding", "modelName": "Issue", "shared": True,
        "description": "Current description", "color": "#123456", "icon": "Target",
        "filterData": {"state": {"type": {"eq": "unstarted"}}}, "team": {"id": "team-id"},
    }
    original = stored.copy()

    def respond(query, variables):
        if "mutation CustomViewUpdate" in query:
            assert variables["id"] == VIEW_ID
            assert variables["input"] == expected
            stored.update(variables["input"])
            return {"data": {"customViewUpdate": {"success": True, "customView": stored}}}
        assert "query CustomView(" in query
        assert variables == {"id": VIEW_ID}
        return {"data": {"customView": stored}}

    install(respond)
    result = CliRunner().invoke(module.app, ["update-view", VIEW_ID] + flags)
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["result"]["id"] == VIEW_ID
    assert stored == {**original, **expected}
    assert len(calls) == 2


def test_duplicate_exact_view_names_refuse_mutation(api):
    module, calls, install = api

    def respond(query, variables):
        assert "customViews(first: 2, filter: {name: {eqIgnoreCase: $name}})" in query
        assert variables == {"name": "Wedding"}
        return {"data": {"customViews": {
            "nodes": [{"id": VIEW_ID, "name": "Wedding"}, {"id": "other-id", "name": "Wedding"}],
            "pageInfo": {"hasNextPage": False},
        }}}

    install(respond)
    result = CliRunner().invoke(module.app, ["update-view", "Wedding", "--name", "Renamed"])
    assert result.exit_code == 1, result.stdout
    data = json.loads(result.stdout)
    assert data["error"]["code"] == "INVALID_INPUT"
    assert VIEW_ID in str(data["error"]["suggestions"])
    assert len(calls) == 1


@pytest.mark.parametrize("args", [
    ["update-view", VIEW_ID],
    ["update-view", VIEW_ID, "--filter-json", "[]"],
    ["update-view", VIEW_ID, "--filter-json", "{"],
    ["update-view", VIEW_ID, "-d", "x" * 256],
    ["create-view", "Wedding", "-d", "x" * 256],
    ["create-view", "Wedding", "--filter-json", "null"],
])
def test_invalid_view_input_is_rejected_before_requests(api, args):
    module, calls, install = api
    install(lambda q, v: pytest.fail("Invalid input must not reach the API"))
    result = CliRunner().invoke(module.app, args)
    assert result.exit_code == 1, result.stdout
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_INPUT"
    assert not calls


def test_saved_view_preview_uses_native_membership_and_cursor(api):
    module, calls, install = api
    view = {"id": VIEW_ID, "name": "Wedding", "modelName": "Issue"}

    def respond(query, variables):
        if "query CustomViewsByName" in query:
            return {"data": {"customViews": {"nodes": [view], "pageInfo": {"hasNextPage": False}}}}
        assert "customView(id: $id)" in query
        assert "issues(first: $first, after: $after)" in query
        assert "filter" not in variables  # Do not reconstruct or weaken the saved filter/team scope.
        assert variables["id"] == VIEW_ID
        page = issue_page(2) if variables["after"] else issue_page(more=True)
        return {"data": {"customView": {**view, "issues": page}}}

    install(respond)
    args = ["view-issues", "Wedding", "--limit", "1"]
    first = CliRunner().invoke(module.app, args)
    assert first.exit_code == 0, first.stdout
    data = json.loads(first.stdout)["result"]
    assert data["view"] == {"id": VIEW_ID, "name": "Wedding"}
    assert data["issues"][0]["identifier"] == "ENG-1"
    second = CliRunner().invoke(module.app, args + ["--after", data["pageInfo"]["endCursor"]])
    assert second.exit_code == 0, second.stdout
    data = json.loads(second.stdout)["result"]
    assert data["issues"][0]["identifier"] == "ENG-2"
    assert data["pageInfo"]["hasNextPage"] is False
    assert len(calls) == 4


def test_non_issue_view_is_an_error_not_an_empty_issue_list(api):
    module, calls, install = api
    view = {"id": VIEW_ID, "name": "Projects", "modelName": "Project"}
    install(lambda q, v: {"data": {"customView": {
        **view, "issues": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}},
    }}})
    result = CliRunner().invoke(module.app, ["view-issues", VIEW_ID])
    assert result.exit_code == 1, result.stdout
    data = json.loads(result.stdout)
    assert data["error"]["code"] == "INVALID_INPUT"
    assert "result" not in data


@pytest.mark.parametrize("command", ["view-issues", "update-view"])
def test_view_api_failure_is_reported_without_retry_or_fallback(api, command):
    module, calls, install = api

    def respond(query, variables):
        if "query CustomView(" in query:
            return {"data": {"customView": {"id": VIEW_ID, "name": "Wedding", "modelName": "Issue"}}}
        return {"errors": [{"message": "Unsupported filter field", "extensions": {"userPresentableMessage": "Use labels, not label"}}]}

    install(respond)
    args = [command, VIEW_ID]
    if command == "update-view":
        args += ["--filter-json", '{"label":{"name":{"eq":"Bug"}}}']
    result = CliRunner().invoke(module.app, args)
    assert result.exit_code == 1, result.stdout
    data = json.loads(result.stdout)
    assert data["error"]["code"] == "API_ERROR"
    assert data["error"]["suggestions"] == ["Use labels, not label"]
    assert "result" not in data
    assert len(calls) == 2
