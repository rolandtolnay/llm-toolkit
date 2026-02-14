#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx",
#     "typer",
# ]
# ///
"""
Linear CLI - Standalone skill for Linear issue management.

A single-file PEP 723 script that provides a CLI interface to Linear's GraphQL API.
Designed to work from any project directory, using project-specific .linear.json config.

Usage:
    uv run linear.py <command> [options]

Commands:
    create          Create a new issue
    update          Update an existing issue
    done            Mark an issue as completed
    state           Change an issue's state
    break           Break down an issue into sub-issues
    relate          Create a relation between issues
    comment         Post a comment on an issue
    attach          Attach a file to an issue
    document        Create a document linked to an issue
    attach-commit   Attach the latest git commit to an issue
    get             Fetch issue details
    list            List issues with filters
    members         List active workspace members
    states          List workflow states
    projects        List projects
    create-project  Create a new project
    update-project  Update an existing project
    delete-project  Delete a project by name
    labels          List labels
    create-label    Create a new label
    delete-label    Delete a label by name
"""

from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
import typer


# =============================================================================
# Errors
# =============================================================================


class ErrorCode(str, Enum):
    """Error codes for CLI responses."""

    MISSING_API_KEY = "MISSING_API_KEY"
    MISSING_CONFIG = "MISSING_CONFIG"
    INVALID_CONFIG = "INVALID_CONFIG"
    ISSUE_NOT_FOUND = "ISSUE_NOT_FOUND"
    STATE_NOT_FOUND = "STATE_NOT_FOUND"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    API_ERROR = "API_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    INVALID_INPUT = "INVALID_INPUT"
    LABEL_NOT_FOUND = "LABEL_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UPLOAD_FAILED = "UPLOAD_FAILED"


class LinearError(Exception):
    """Base exception for Linear CLI errors."""

    def __init__(self, code: ErrorCode, message: str, suggestions: list[str] | None = None):
        self.code = code
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


# =============================================================================
# Output Formatting
# =============================================================================


def format_success(
    command: str,
    result: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format successful response."""
    response: dict[str, Any] = {
        "success": True,
        "command": command,
        "result": result,
    }
    if _verbose and metadata:
        response["metadata"] = metadata
    return response


def format_error(command: str, error: LinearError) -> dict[str, Any]:
    """Format error response."""
    error_dict: dict[str, Any] = {
        "code": error.code.value,
        "message": error.message,
    }
    if error.suggestions:
        error_dict["suggestions"] = error.suggestions

    return {
        "success": False,
        "command": command,
        "error": error_dict,
    }


def output_json(data: dict[str, Any]) -> str:
    """Convert data to JSON string (always pretty-printed)."""
    return json.dumps(data, indent=2, ensure_ascii=False)


# =============================================================================
# Configuration
# =============================================================================

LINEAR_API_URL = "https://api.linear.app/graphql"


@dataclass
class LinearConfig:
    """Linear project configuration from .linear.json."""

    team_id: str
    project_id: str | None = None
    default_priority: int = 3
    default_labels: list[str] | None = None

    def __post_init__(self) -> None:
        if self.default_labels is None:
            self.default_labels = []


def get_api_key() -> str:
    """Get LINEAR_API_KEY from environment."""
    api_key = os.environ.get("LINEAR_API_KEY", "")
    if not api_key:
        raise LinearError(
            code=ErrorCode.MISSING_API_KEY,
            message="LINEAR_API_KEY environment variable not set",
            suggestions=[
                "Set LINEAR_API_KEY in project .claude/settings.local.json env section",
                "Or set in your shell: export LINEAR_API_KEY='lin_api_...'",
                "Get your API key from Linear Settings > API > Personal API keys",
            ],
        )
    return api_key


def find_config_file() -> Path | None:
    """Find .linear.json by searching upward from current directory."""
    current = Path.cwd()

    while current != current.parent:
        config_path = current / ".linear.json"
        if config_path.exists():
            return config_path
        current = current.parent

    # Check root
    root_config = current / ".linear.json"
    if root_config.exists():
        return root_config

    return None


# =============================================================================
# Priority and State Parsing Helpers
# =============================================================================

PRIORITY_NAMES = {
    "none": 0,
    "urgent": 1,
    "high": 2,
    "normal": 3,
    "low": 4,
}

STATE_TYPE_ALIASES = {
    "backlog": "backlog",
    "todo": "unstarted",
    "unstarted": "unstarted",
    "started": "started",
    "in_progress": "started",
    "done": "completed",
    "completed": "completed",
    "canceled": "canceled",
    "cancelled": "canceled",
}


def parse_priority(value: str) -> int:
    """Parse priority from number or name.

    Args:
        value: Priority as number string (0-4) or name (none/urgent/high/normal/low)

    Returns:
        Priority integer (0-4)

    Raises:
        LinearError: If value is invalid
    """
    # Try as number first
    if value.isdigit():
        num = int(value)
        if 0 <= num <= 4:
            return num
        raise LinearError(
            code=ErrorCode.INVALID_INPUT,
            message=f"Priority must be 0-4, got {num}",
            suggestions=["0=None, 1=Urgent, 2=High, 3=Normal, 4=Low"],
        )

    # Try as name
    name_lower = value.lower()
    if name_lower in PRIORITY_NAMES:
        return PRIORITY_NAMES[name_lower]

    available = ", ".join(PRIORITY_NAMES.keys())
    raise LinearError(
        code=ErrorCode.INVALID_INPUT,
        message=f"Unknown priority '{value}'",
        suggestions=[f"Use 0-4 or: {available}"],
    )


def load_config(config_path: Path | None = None) -> LinearConfig:
    """Load configuration from .linear.json.

    Searches upward from current directory if no path specified.
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        raise LinearError(
            code=ErrorCode.MISSING_CONFIG,
            message=".linear.json not found in project",
            suggestions=[
                "Create .linear.json in your project root",
                'Required fields: {"teamId": "uuid"}',
                'Optional: {"projectId": "uuid"} for default project assignment',
                "Find IDs from Linear URLs or use `linear.py states` to discover team",
            ],
        )

    try:
        with open(config_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise LinearError(
            code=ErrorCode.INVALID_CONFIG,
            message=f"Invalid JSON in .linear.json: {e}",
            suggestions=["Check .linear.json for syntax errors"],
        )

    if "teamId" not in data:
        raise LinearError(
            code=ErrorCode.INVALID_CONFIG,
            message="teamId is required in .linear.json",
            suggestions=['Add "teamId": "your-team-uuid" to .linear.json'],
        )

    return LinearConfig(
        team_id=data["teamId"],
        project_id=data.get("projectId"),
        default_priority=data.get("defaultPriority", 3),
        default_labels=data.get("defaultLabels", []),
    )


# =============================================================================
# GraphQL Queries & Mutations
# =============================================================================

QUERY_ISSUE = """
query Issue($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    estimate
    url
    state {
      id
      name
      type
    }
    assignee {
      id
      name
      email
    }
    parent {
      identifier
      title
    }
    children {
      nodes {
        identifier
        title
        priority
        estimate
        state {
          name
        }
      }
    }
    project {
      id
      name
    }
    labels {
      nodes {
        id
        name
      }
    }
    team {
      id
      key
      name
    }
    relations {
      nodes {
        id
        type
        relatedIssue {
          identifier
          title
        }
      }
    }
    inverseRelations {
      nodes {
        id
        type
        issue {
          identifier
          title
        }
      }
    }
    attachments {
      nodes {
        url
        title
      }
    }
    comments {
      nodes {
        id
      }
    }
  }
}
"""

QUERY_ISSUE_WITH_COMMENTS = """
query Issue($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    estimate
    url
    state {
      id
      name
      type
    }
    assignee {
      id
      name
      email
    }
    parent {
      identifier
      title
    }
    children {
      nodes {
        identifier
        title
        priority
        estimate
        state {
          name
        }
      }
    }
    project {
      id
      name
    }
    labels {
      nodes {
        id
        name
      }
    }
    team {
      id
      key
      name
    }
    relations {
      nodes {
        id
        type
        relatedIssue {
          identifier
          title
        }
      }
    }
    inverseRelations {
      nodes {
        id
        type
        issue {
          identifier
          title
        }
      }
    }
    attachments {
      nodes {
        url
        title
      }
    }
    comments(first: 50) {
      nodes {
        id
        body
        createdAt
        user {
          name
        }
      }
    }
  }
}
"""

QUERY_WORKFLOW_STATES = """
query {
  workflowStates {
    nodes {
      id
      name
      type
      position
      team {
        id
        key
        name
      }
    }
  }
}
"""

QUERY_TEAM_STATES = """
query TeamWorkflowStates($teamId: String!) {
  team(id: $teamId) {
    id
    name
    key
    states {
      nodes {
        id
        name
        type
        position
      }
    }
  }
}
"""

QUERY_PROJECTS = """
query {
  projects {
    nodes {
      id
      name
      state
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
  }
}
"""

QUERY_TEAM_PROJECTS = """
query TeamProjects($teamId: String!) {
  team(id: $teamId) {
    id
    name
    key
    projects {
      nodes {
        id
        name
        state
      }
    }
  }
}
"""

QUERY_VIEWER = """
query {
  viewer {
    id
    name
    email
  }
}
"""

QUERY_ISSUES = """
query Issues($filter: IssueFilter, $first: Int) {
  issues(filter: $filter, first: $first) {
    nodes {
      id
      identifier
      title
      priority
      estimate
      state { id name type }
      assignee { id name email }
      creator { id name email }
      project { id name }
      labels { nodes { id name } }
      team { id key name }
    }
  }
}
"""

QUERY_USERS = """
query {
  users {
    nodes {
      id
      name
      displayName
      email
      active
    }
  }
}
"""

MUTATION_CREATE_ISSUE = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
      url
      state {
        name
      }
    }
  }
}
"""

MUTATION_UPDATE_ISSUE = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
      id
      identifier
      title
      url
      state {
        id
        name
      }
      labels {
        nodes {
          id
          name
        }
      }
      project {
        id
        name
      }
    }
  }
}
"""

MUTATION_CREATE_RELATION = """
mutation CreateRelation($input: IssueRelationCreateInput!) {
  issueRelationCreate(input: $input) {
    success
    issueRelation {
      id
      type
    }
  }
}
"""

QUERY_ISSUE_RELATIONS = """
query IssueRelations($id: String!) {
  issue(id: $id) {
    id
    identifier
    relations {
      nodes {
        id
        type
        relatedIssue {
          id
          identifier
        }
      }
    }
    inverseRelations {
      nodes {
        id
        type
        issue {
          id
          identifier
        }
      }
    }
  }
}
"""

MUTATION_DELETE_RELATION = """
mutation DeleteRelation($id: String!) {
  issueRelationDelete(id: $id) {
    success
  }
}
"""

MUTATION_FILE_UPLOAD = """
mutation FileUpload($contentType: String!, $filename: String!, $size: Int!) {
  fileUpload(contentType: $contentType, filename: $filename, size: $size) {
    success
    uploadFile {
      uploadUrl
      assetUrl
      headers {
        key
        value
      }
    }
  }
}
"""

MUTATION_CREATE_DOCUMENT = """
mutation DocumentCreate($input: DocumentCreateInput!) {
  documentCreate(input: $input) {
    success
    document {
      id
      title
      url
      slugId
      content
      issue {
        identifier
      }
      project {
        name
      }
    }
  }
}
"""

MUTATION_CREATE_COMMENT = """
mutation CommentCreate($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment {
      id
      body
      url
      issue {
        identifier
        title
      }
    }
  }
}
"""

MUTATION_CREATE_ATTACHMENT = """
mutation AttachmentCreate($input: AttachmentCreateInput!) {
  attachmentCreate(input: $input) {
    success
    attachment {
      id
      title
      url
    }
  }
}
"""

MUTATION_CREATE_PROJECT = """
mutation ProjectCreate($input: ProjectCreateInput!) {
  projectCreate(input: $input) {
    success
    project {
      id
      name
      description
      state
      color
      icon
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
  }
}
"""

MUTATION_DELETE_PROJECT = """
mutation ProjectDelete($id: String!) {
  projectDelete(id: $id) {
    success
  }
}
"""

MUTATION_UPDATE_PROJECT = """
mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project {
      id
      name
      description
      state
      color
      icon
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
  }
}
"""

QUERY_LABELS = """
query {
  issueLabels {
    nodes {
      id
      name
      color
      description
      isGroup
      parent { id name }
      team { id key name }
    }
  }
}
"""

QUERY_TEAM_LABELS = """
query TeamLabels($teamId: String!) {
  team(id: $teamId) {
    id
    name
    key
    labels {
      nodes {
        id
        name
        color
        description
        isGroup
        parent { id name }
      }
    }
  }
}
"""

MUTATION_CREATE_LABEL = """
mutation LabelCreate($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) {
    success
    issueLabel {
      id
      name
      color
      description
      team { id key name }
    }
  }
}
"""

MUTATION_DELETE_LABEL = """
mutation LabelDelete($id: String!) {
  issueLabelDelete(id: $id) {
    success
  }
}
"""

MUTATION_UPDATE_LABEL = """
mutation LabelUpdate($id: String!, $input: IssueLabelUpdateInput!) {
  issueLabelUpdate(id: $id, input: $input) {
    success
    issueLabel {
      id
      name
      color
      description
      team { id key name }
    }
  }
}
"""


# =============================================================================
# Linear API Client
# =============================================================================


class LinearClient:
    """Client for Linear GraphQL API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key()
        self.client = httpx.Client(timeout=30.0)

    def _request(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GraphQL request to Linear."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
        }

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = self.client.post(LINEAR_API_URL, headers=headers, json=payload)
        except httpx.NetworkError as e:
            raise LinearError(
                code=ErrorCode.NETWORK_ERROR,
                message=f"Network error: {e}",
                suggestions=["Check your internet connection"],
            )

        if response.status_code == 429:
            raise LinearError(
                code=ErrorCode.RATE_LIMITED,
                message="Rate limited by Linear API",
                suggestions=["Wait a moment and retry"],
            )

        try:
            data = response.json()
        except ValueError:
            if response.status_code != 200:
                raise LinearError(
                    code=ErrorCode.API_ERROR,
                    message=f"API error: HTTP {response.status_code} (no response body)",
                )
            raise LinearError(
                code=ErrorCode.INVALID_RESPONSE,
                message="Invalid JSON response from Linear",
            )

        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown error")
            if "Authentication" in error_msg:
                raise LinearError(
                    code=ErrorCode.MISSING_API_KEY,
                    message="Authentication failed",
                    suggestions=[
                        "Check LINEAR_API_KEY is valid",
                        "Get a new key from Linear Settings > API",
                    ],
                )
            if "not found" in error_msg.lower():
                raise LinearError(
                    code=ErrorCode.ISSUE_NOT_FOUND,
                    message=error_msg,
                    suggestions=["Check the issue identifier is correct"],
                )
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message=error_msg,
            )

        return data.get("data", {})

    def get_issue(self, issue_id: str, include_comments: bool = False) -> dict[str, Any]:
        """Fetch issue details by ID or identifier.

        Args:
            issue_id: Issue ID or identifier (e.g., ABC-123)
            include_comments: If True, include full comment content. If False, only count.

        Returns:
            Issue dict with comment data based on include_comments flag.
        """
        query = QUERY_ISSUE_WITH_COMMENTS if include_comments else QUERY_ISSUE
        data = self._request(query, {"id": issue_id})
        issue = data.get("issue")
        if not issue:
            raise LinearError(
                code=ErrorCode.ISSUE_NOT_FOUND,
                message=f"Issue {issue_id} not found",
                suggestions=["Check the issue identifier is correct"],
            )
        return issue

    def get_workflow_states(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """Get workflow states, optionally filtered by team."""
        if team_id:
            data = self._request(QUERY_TEAM_STATES, {"teamId": team_id})
            team = data.get("team", {})
            states = team.get("states", {}).get("nodes", [])
            # Add team info to each state
            team_info = {"id": team.get("id"), "key": team.get("key"), "name": team.get("name")}
            return [{"team": team_info, **state} for state in states]
        else:
            data = self._request(QUERY_WORKFLOW_STATES)
            return data.get("workflowStates", {}).get("nodes", [])

    def get_projects(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """Get projects, optionally filtered by team."""
        if team_id:
            data = self._request(QUERY_TEAM_PROJECTS, {"teamId": team_id})
            team = data.get("team", {})
            projects = team.get("projects", {}).get("nodes", [])
            # Add team info to each project
            team_info = {"id": team.get("id"), "key": team.get("key"), "name": team.get("name")}
            return [{"team": team_info, **project} for project in projects]
        else:
            data = self._request(QUERY_PROJECTS)
            projects = data.get("projects", {}).get("nodes", [])
            # Normalize: flatten first team from teams.nodes into "team" key
            # to match the shape returned by the team-filtered path
            result = []
            for project in projects:
                team_nodes = project.get("teams", {}).get("nodes", [])
                team_info = team_nodes[0] if team_nodes else {}
                result.append({"team": team_info, **project})
            return result

    def find_project_by_name(self, project_name: str, team_id: str | None = None) -> dict[str, Any]:
        """Find a project by name, optionally within a specific team."""
        projects = self.get_projects(team_id)
        project_name_lower = project_name.lower()

        # Exact match first
        for project in projects:
            if project["name"].lower() == project_name_lower:
                return project

        # Partial match
        for project in projects:
            if project_name_lower in project["name"].lower():
                return project

        available = ", ".join(sorted(set(p["name"] for p in projects)))
        raise LinearError(
            code=ErrorCode.PROJECT_NOT_FOUND,
            message=f"Project '{project_name}' not found",
            suggestions=[f"Available projects: {available}"],
        )

    def get_labels(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """Get labels, optionally filtered by team."""
        if team_id:
            data = self._request(QUERY_TEAM_LABELS, {"teamId": team_id})
            team = data.get("team", {})
            labels = team.get("labels", {}).get("nodes", [])
            team_info = {"id": team.get("id"), "key": team.get("key"), "name": team.get("name")}
            return [{"team": team_info, **label} for label in labels]
        else:
            data = self._request(QUERY_LABELS)
            return data.get("issueLabels", {}).get("nodes", [])

    def find_label_by_name(self, label_name: str, team_id: str | None = None) -> dict[str, Any]:
        """Find a label by name, optionally within a specific team."""
        labels = self.get_labels(team_id)
        label_name_lower = label_name.lower()

        # Exact match first
        for label in labels:
            if label["name"].lower() == label_name_lower:
                return label

        # Partial match
        for label in labels:
            if label_name_lower in label["name"].lower():
                return label

        available = ", ".join(sorted(set(l["name"] for l in labels)))
        raise LinearError(
            code=ErrorCode.LABEL_NOT_FOUND,
            message=f"Label '{label_name}' not found",
            suggestions=[f"Available labels: {available}"],
        )

    def resolve_label_names(self, label_names: list[str], team_id: str | None = None) -> list[str]:
        """Resolve a list of label names to label IDs."""
        return [self.find_label_by_name(name, team_id)["id"] for name in label_names]

    def create_label(
        self,
        name: str,
        team_id: str,
        color: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new label.

        Args:
            name: Label name
            team_id: Team ID to scope the label to
            color: Hex color (e.g. #4CAF50)
            description: Label description
        """
        input_data: dict[str, Any] = {
            "name": name,
            "teamId": team_id,
        }

        if color:
            input_data["color"] = color
        if description:
            input_data["description"] = description

        data = self._request(MUTATION_CREATE_LABEL, {"input": input_data})
        result = data.get("issueLabelCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create label",
            )

        return result.get("issueLabel", {})

    def delete_label(self, label_id: str) -> bool:
        """Delete a label by its ID.

        Args:
            label_id: UUID of the label to delete

        Returns:
            True if successful
        """
        data = self._request(MUTATION_DELETE_LABEL, {"id": label_id})
        result = data.get("issueLabelDelete", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to delete label",
            )

        return True

    def update_label(
        self,
        label_id: str,
        name: str | None = None,
        color: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing label.

        Args:
            label_id: UUID of the label to update
            name: New label name
            color: Hex color (e.g. #FF6B35)
            description: New description
        """
        input_data: dict[str, Any] = {}

        if name is not None:
            input_data["name"] = name
        if color is not None:
            input_data["color"] = color
        if description is not None:
            input_data["description"] = description

        if not input_data:
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message="No fields to update",
                suggestions=["Provide at least one field to update"],
            )

        data = self._request(MUTATION_UPDATE_LABEL, {"id": label_id, "input": input_data})
        result = data.get("issueLabelUpdate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to update label",
            )

        return result.get("issueLabel", {})

    def create_project(
        self,
        name: str,
        team_ids: list[str],
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: Project name
            team_ids: List of team IDs to associate with the project
            description: Project description
            color: Hex color (e.g. #FF6B35)
            icon: Icon identifier
            state: Initial state (planned, started, paused, completed, canceled)
            start_date: Start date (YYYY-MM-DD)
            target_date: Target date (YYYY-MM-DD)
        """
        input_data: dict[str, Any] = {
            "name": name,
            "teamIds": team_ids,
        }

        if description:
            input_data["description"] = description
        if color:
            input_data["color"] = color
        if icon:
            input_data["icon"] = icon
        if state:
            input_data["state"] = state
        if start_date:
            input_data["startDate"] = start_date
        if target_date:
            input_data["targetDate"] = target_date

        data = self._request(MUTATION_CREATE_PROJECT, {"input": input_data})
        result = data.get("projectCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create project",
            )

        return result.get("project", {})

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by its ID.

        Args:
            project_id: UUID of the project to delete

        Returns:
            True if successful
        """
        data = self._request(MUTATION_DELETE_PROJECT, {"id": project_id})
        result = data.get("projectDelete", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to delete project",
            )

        return True

    def update_project(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing project.

        Args:
            project_id: UUID of the project to update
            name: New project name
            description: New description
            color: Hex color (e.g. #FF6B35)
            icon: Icon identifier
            state: State (planned, started, paused, completed, canceled)
            start_date: Start date (YYYY-MM-DD)
            target_date: Target date (YYYY-MM-DD)
        """
        input_data: dict[str, Any] = {}

        if name is not None:
            input_data["name"] = name
        if description is not None:
            input_data["description"] = description
        if color is not None:
            input_data["color"] = color
        if icon is not None:
            input_data["icon"] = icon
        if state is not None:
            input_data["state"] = state
        if start_date is not None:
            input_data["startDate"] = start_date
        if target_date is not None:
            input_data["targetDate"] = target_date

        if not input_data:
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message="No fields to update",
                suggestions=["Provide at least one field to update"],
            )

        data = self._request(MUTATION_UPDATE_PROJECT, {"id": project_id, "input": input_data})
        result = data.get("projectUpdate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to update project",
            )

        return result.get("project", {})

    def get_viewer(self) -> dict[str, Any]:
        """Get current authenticated user."""
        data = self._request(QUERY_VIEWER)
        return data.get("viewer", {})

    def get_users(self) -> list[dict[str, Any]]:
        """Get all users in workspace."""
        data = self._request(QUERY_USERS)
        return data.get("users", {}).get("nodes", [])

    def find_user(self, identifier: str) -> dict[str, Any] | None:
        """Find active user by email (exact), name (partial), or displayName (partial).

        Args:
            identifier: Email address, name, or display name to search for

        Returns:
            User dict or None if not found
        """
        users = [u for u in self.get_users() if u.get("active", False)]
        identifier_lower = identifier.lower()

        # Try exact email match first
        for user in users:
            if user.get("email", "").lower() == identifier_lower:
                return user

        # Try partial name match
        for user in users:
            if identifier_lower in user.get("name", "").lower():
                return user

        # Try partial displayName match
        for user in users:
            if identifier_lower in user.get("displayName", "").lower():
                return user

        return None

    def list_issues(
        self,
        team_id: str | None = None,
        assignee_id: str | None = None,
        creator_id: str | None = None,
        priority: int | None = None,
        project_id: str | None = None,
        state_id: str | None = None,
        state_type: str | None = None,
        estimate: int | None = None,
        no_estimate: bool = False,
        label_ids: list[str] | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """List issues with optional filters.

        All filters combine with AND logic.

        Args:
            team_id: Filter by team
            assignee_id: Filter by assignee user ID
            creator_id: Filter by creator user ID
            priority: Filter by priority (0-4)
            project_id: Filter by project ID
            state_id: Filter by specific state ID
            state_type: Filter by state type (backlog/unstarted/started/completed/canceled)
            estimate: Filter by specific estimate value
            no_estimate: Filter for issues with null estimate
            label_ids: Filter by label IDs (AND logic for multiple)
            limit: Maximum number of results (default 25)

        Returns:
            List of issue dicts
        """
        filter_obj: dict[str, Any] = {}

        if team_id:
            filter_obj["team"] = {"id": {"eq": team_id}}
        if assignee_id:
            filter_obj["assignee"] = {"id": {"eq": assignee_id}}
        if creator_id:
            filter_obj["creator"] = {"id": {"eq": creator_id}}
        if priority is not None:
            filter_obj["priority"] = {"eq": priority}
        if project_id:
            filter_obj["project"] = {"id": {"eq": project_id}}
        if state_id:
            filter_obj["state"] = {"id": {"eq": state_id}}
        elif state_type:
            filter_obj["state"] = {"type": {"eq": state_type}}
        if no_estimate:
            filter_obj["estimate"] = {"null": True}
        elif estimate is not None:
            filter_obj["estimate"] = {"eq": estimate}

        if label_ids:
            if len(label_ids) == 1:
                filter_obj["labels"] = {"id": {"eq": label_ids[0]}}
            else:
                # Multiple labels with AND logic: wrap in "and" filter
                label_filters = [{"labels": {"id": {"eq": lid}}} for lid in label_ids]
                if filter_obj:
                    filter_obj = {"and": [filter_obj] + label_filters}
                else:
                    filter_obj = {"and": label_filters}

        variables: dict[str, Any] = {"first": limit}
        if filter_obj:
            variables["filter"] = filter_obj

        data = self._request(QUERY_ISSUES, variables)
        return data.get("issues", {}).get("nodes", [])

    def create_issue(
        self,
        config: LinearConfig,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        estimate: int | None = None,
        parent_id: str | None = None,
        state_id: str | None = None,
        label_ids: list[str] | None = None,
        project_id: str | None = None,
        no_project: bool = False,
        assignee_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new issue.

        Args:
            config: Linear configuration
            title: Issue title
            description: Issue description (markdown)
            priority: Priority (0-4)
            estimate: Estimate value
            parent_id: Parent issue ID for sub-issues
            state_id: Initial state ID
            label_ids: Label IDs to apply
            project_id: Explicit project ID (overrides config default)
            no_project: If True, don't assign to any project (ignores config default)
            assignee_id: User ID to assign the issue to
        """
        input_data: dict[str, Any] = {
            "teamId": config.team_id,
            "title": title,
        }

        if description:
            input_data["description"] = description

        # Project logic: explicit > config default, unless no_project
        if not no_project:
            if project_id:
                input_data["projectId"] = project_id
            elif config.project_id:
                input_data["projectId"] = config.project_id

        if priority is not None:
            input_data["priority"] = priority
        else:
            input_data["priority"] = config.default_priority
        if estimate is not None:
            input_data["estimate"] = estimate
        if parent_id:
            input_data["parentId"] = parent_id
        if state_id:
            input_data["stateId"] = state_id
        if label_ids:
            input_data["labelIds"] = label_ids
        if assignee_id:
            input_data["assigneeId"] = assignee_id

        data = self._request(MUTATION_CREATE_ISSUE, {"input": input_data})
        result = data.get("issueCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create issue",
            )

        return result.get("issue", {})

    def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        estimate: int | None = None,
        parent_id: str | None = None,
        label_ids: list[str] | None = None,
        removed_label_ids: list[str] | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing issue."""
        input_data: dict[str, Any] = {}

        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if state_id is not None:
            input_data["stateId"] = state_id
        if estimate is not None:
            input_data["estimate"] = estimate
        if parent_id is not None:
            input_data["parentId"] = parent_id
        if removed_label_ids:
            input_data["removedLabelIds"] = removed_label_ids
        if label_ids:
            input_data["labelIds"] = label_ids
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id or None
        if project_id is not None:
            input_data["projectId"] = project_id or None

        if not input_data:
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message="No fields to update",
                suggestions=["Provide at least one field to update"],
            )

        data = self._request(MUTATION_UPDATE_ISSUE, {"id": issue_id, "input": input_data})
        result = data.get("issueUpdate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to update issue",
            )

        return result.get("issue", {})

    def find_state_by_name(self, team_id: str, state_name: str) -> dict[str, Any]:
        """Find a workflow state by name within a team."""
        states = self.get_workflow_states(team_id)
        state_name_lower = state_name.lower()

        # Exact match first
        for state in states:
            if state["name"].lower() == state_name_lower:
                return state

        # Partial match
        for state in states:
            if state_name_lower in state["name"].lower():
                return state

        # Type-based match (e.g., "done" matches completed type)
        type_mapping = {
            "done": "completed",
            "complete": "completed",
            "finished": "completed",
            "todo": "unstarted",
            "backlog": "backlog",
            "in progress": "started",
            "started": "started",
            "cancelled": "canceled",
            "canceled": "canceled",
        }
        if state_name_lower in type_mapping:
            target_type = type_mapping[state_name_lower]
            for state in states:
                if state.get("type") == target_type:
                    return state

        available = ", ".join(sorted(set(s["name"] for s in states)))
        raise LinearError(
            code=ErrorCode.STATE_NOT_FOUND,
            message=f"State '{state_name}' not found",
            suggestions=[f"Available states: {available}"],
        )

    def mark_done(self, issue_id: str) -> dict[str, Any]:
        """Mark an issue as completed."""
        # First get the issue to find its team
        issue = self.get_issue(issue_id)
        team_id = issue.get("team", {}).get("id")

        if not team_id:
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Could not determine team for issue",
            )

        # Find the completed state
        done_state = self.find_state_by_name(team_id, "done")
        return self.update_issue(issue_id, state_id=done_state["id"])

    def change_state(self, issue_id: str, state_name: str) -> dict[str, Any]:
        """Change an issue's state by name."""
        # First get the issue to find its team
        issue = self.get_issue(issue_id)
        team_id = issue.get("team", {}).get("id")

        if not team_id:
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Could not determine team for issue",
            )

        # Find the target state
        target_state = self.find_state_by_name(team_id, state_name)
        return self.update_issue(issue_id, state_id=target_state["id"])

    def create_sub_issues(
        self,
        config: LinearConfig,
        parent_id: str,
        issues: list[dict[str, Any]],
        project_id: str | None = None,
        no_project: bool = False,
        label_ids: list[str] | None = None,
        no_labels: bool = False,
    ) -> list[dict[str, Any]]:
        """Create multiple sub-issues under a parent."""
        # Get parent issue to extract its UUID and project
        parent = self.get_issue(parent_id)
        parent_uuid = parent.get("id")

        # Inherit parent's project if not explicitly specified
        if not no_project and not project_id:
            parent_project = parent.get("project")
            if parent_project:
                project_id = parent_project.get("id")

        # Inherit parent's labels if not explicitly specified
        if not no_labels and not label_ids:
            parent_labels = parent.get("labels", {}).get("nodes", [])
            if parent_labels:
                label_ids = [l["id"] for l in parent_labels]

        created = []
        for issue_data in issues:
            issue = self.create_issue(
                config=config,
                title=issue_data.get("title", ""),
                description=issue_data.get("description"),
                priority=issue_data.get("priority"),
                estimate=issue_data.get("estimate"),
                parent_id=parent_uuid,
                project_id=project_id,
                no_project=no_project,
                label_ids=label_ids,
            )
            created.append(issue)

        return created

    def create_relation(
        self,
        issue_id: str,
        related_issue_id: str,
        relation_type: str,
    ) -> dict[str, Any]:
        """Create a relation between two issues.

        Args:
            issue_id: Source issue identifier (e.g., ABC-123) — resolved to UUID
            related_issue_id: Target issue identifier — resolved to UUID
            relation_type: Relation type: blocks, relates_to, or duplicates

        Returns:
            Created relation dict
        """
        # Resolve identifiers to UUIDs
        source = self.get_issue(issue_id)
        target = self.get_issue(related_issue_id)

        source_uuid = source.get("id")
        target_uuid = target.get("id")

        if not source_uuid or not target_uuid:
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Could not resolve issue UUIDs",
            )

        input_data = {
            "issueId": source_uuid,
            "relatedIssueId": target_uuid,
            "type": relation_type,
        }

        data = self._request(MUTATION_CREATE_RELATION, {"input": input_data})
        result = data.get("issueRelationCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create relation",
            )

        return result.get("issueRelation", {})

    def find_relation(self, issue_id: str, target_id: str) -> dict[str, Any] | None:
        """Find a relation between two issues.

        Searches both forward relations and inverse relations on the source issue.

        Args:
            issue_id: Source issue identifier (e.g., ABC-123)
            target_id: Target issue identifier (e.g., ABC-456)

        Returns:
            Relation dict with id and type, or None if not found
        """
        data = self._request(QUERY_ISSUE_RELATIONS, {"id": issue_id})
        issue = data.get("issue")
        if not issue:
            raise LinearError(
                code=ErrorCode.ISSUE_NOT_FOUND,
                message=f"Issue {issue_id} not found",
                suggestions=["Check the issue identifier is correct"],
            )

        target_upper = target_id.upper()

        # Check forward relations
        for rel in issue.get("relations", {}).get("nodes", []):
            related = rel.get("relatedIssue", {})
            if related.get("identifier", "").upper() == target_upper:
                return rel

        # Check inverse relations
        for rel in issue.get("inverseRelations", {}).get("nodes", []):
            source = rel.get("issue", {})
            if source.get("identifier", "").upper() == target_upper:
                return rel

        return None

    def delete_relation(self, relation_id: str) -> bool:
        """Delete a relation by its ID.

        Args:
            relation_id: UUID of the relation to delete

        Returns:
            True if successful
        """
        data = self._request(MUTATION_DELETE_RELATION, {"id": relation_id})
        result = data.get("issueRelationDelete", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to delete relation",
            )

        return True

    def upload_file(self, file_path: str) -> str:
        """Upload a file to Linear and return its asset URL.

        Args:
            file_path: Path to local file

        Returns:
            Asset URL of the uploaded file
        """
        path = Path(file_path)
        if not path.exists():
            raise LinearError(
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"File not found: {file_path}",
                suggestions=["Check the file path is correct"],
            )

        content = path.read_bytes()
        size = len(content)
        filename = path.name

        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        # Request pre-signed upload URL
        data = self._request(
            MUTATION_FILE_UPLOAD,
            {"contentType": content_type, "filename": filename, "size": size},
        )
        result = data.get("fileUpload", {})
        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.UPLOAD_FAILED,
                message="Failed to get upload URL from Linear",
            )

        upload_file = result.get("uploadFile", {})
        upload_url = upload_file.get("uploadUrl")
        asset_url = upload_file.get("assetUrl")

        # Build headers from response
        headers: dict[str, str] = {}
        for header in upload_file.get("headers", []):
            headers[header["key"]] = header["value"]
        headers["Content-Type"] = content_type
        headers["Cache-Control"] = "public, max-age=31536000"

        # PUT file content to upload URL
        try:
            response = self.client.put(upload_url, content=content, headers=headers)
        except httpx.NetworkError as e:
            raise LinearError(
                code=ErrorCode.UPLOAD_FAILED,
                message=f"Upload failed: {e}",
                suggestions=["Check your internet connection and retry"],
            )

        if response.status_code not in (200, 201):
            raise LinearError(
                code=ErrorCode.UPLOAD_FAILED,
                message=f"Upload failed: HTTP {response.status_code}",
                suggestions=["Retry the upload"],
            )

        return asset_url

    def create_attachment(
        self,
        issue_id: str,
        url: str,
        title: str,
        subtitle: str | None = None,
    ) -> dict[str, Any]:
        """Create an attachment on an issue.

        Args:
            issue_id: Issue identifier (e.g., ABC-123) — resolved to UUID
            url: URL of the attachment (typically from upload_file)
            title: Display title for the attachment
            subtitle: Optional subtitle/description

        Returns:
            Attachment dict with id, title, url
        """
        issue = self.get_issue(issue_id)
        issue_uuid = issue.get("id")
        if not issue_uuid:
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Could not resolve issue UUID",
            )

        input_data: dict[str, Any] = {
            "issueId": issue_uuid,
            "url": url,
            "title": title,
        }
        if subtitle:
            input_data["subtitle"] = subtitle

        data = self._request(MUTATION_CREATE_ATTACHMENT, {"input": input_data})
        result = data.get("attachmentCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create attachment",
            )

        return result.get("attachment", {})

    def create_document(
        self,
        issue_id: str,
        title: str,
        content: str | None = None,
        project_id: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        """Create a document linked to an issue.

        Creates a native Linear document viewable inline on the issue.

        Args:
            issue_id: Issue identifier (e.g., ABC-123)
            title: Document title
            content: Document content in markdown format
            project_id: Optional project ID to also link to a project
            icon: Optional document icon
            color: Optional icon color

        Returns:
            Document dict with id, title, url, slugId
        """
        input_data: dict[str, Any] = {
            "issueId": issue_id,
            "title": title,
        }
        if content is not None:
            input_data["content"] = content
        if project_id:
            input_data["projectId"] = project_id
        if icon:
            input_data["icon"] = icon
        if color:
            input_data["color"] = color

        data = self._request(MUTATION_CREATE_DOCUMENT, {"input": input_data})
        result = data.get("documentCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create document",
            )

        return result.get("document", {})

    def create_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        """Post a comment on an issue.

        Args:
            issue_id: Issue identifier (e.g., ABC-123)
            body: Comment body in markdown format

        Returns:
            Comment dict with id, body, url
        """
        issue = self.get_issue(issue_id)
        actual_id = issue.get("id")
        if not actual_id:
            raise LinearError(
                code=ErrorCode.ISSUE_NOT_FOUND,
                message=f"Issue {issue_id} not found",
                suggestions=["Check the issue identifier"],
            )

        data = self._request(
            MUTATION_CREATE_COMMENT, {"input": {"issueId": actual_id, "body": body}}
        )
        result = data.get("commentCreate", {})

        if not result.get("success"):
            raise LinearError(
                code=ErrorCode.API_ERROR,
                message="Failed to create comment",
            )

        return result.get("comment", {})


# =============================================================================
# CLI Commands
# =============================================================================

__version__ = "1.0.0"

app = typer.Typer(
    name="linear",
    help="Linear CLI - create, update, and manage Linear issues",
    add_completion=False,
)

_verbose = False


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"linear {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Linear CLI - create, update, and manage Linear issues."""


@app.command()
def create(
    title: str = typer.Argument(..., help="Issue title"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Issue description (markdown)",
    ),
    priority: Optional[int] = typer.Option(
        None,
        "--priority",
        "-p",
        help="Priority: 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low",
    ),
    estimate: Optional[int] = typer.Option(
        None,
        "--estimate",
        "-e",
        help="Estimate (team-specific scale)",
    ),
    parent: Optional[str] = typer.Option(
        None,
        "--parent",
        help="Parent issue ID for sub-issues",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Project name (resolved to ID) - overrides config default",
    ),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Don't assign to any project (ignores config default)",
    ),
    label: Optional[list[str]] = typer.Option(
        None,
        "--label",
        help="Label name (repeatable, resolved to ID)",
    ),
    assignee: Optional[str] = typer.Option(
        None,
        "--assignee",
        help="Assignee name or email (resolved to user ID)",
    ),
) -> None:
    """Create a new issue.

    Examples:
        linear.py create "Fix login bug"
        linear.py create "Add OAuth" -d "Support Google and GitHub OAuth"
        linear.py create "Auth subtask" --parent ABC-123
        linear.py create "Mobile bug" --project "Mobile App"
        linear.py create "Backlog item" --no-project
        linear.py create "Mobile bug" --label mobile
        linear.py create "Fix login" --assignee "Roland"
    """
    command = "create"

    try:
        config = load_config()
        client = LinearClient()

        # Resolve project name to ID if provided
        project_id = None
        if project:
            project_info = client.find_project_by_name(project, config.team_id)
            project_id = project_info["id"]

        # Resolve label names to IDs
        label_ids = None
        if label:
            label_ids = client.resolve_label_names(label, config.team_id)
        elif config.default_labels:
            label_ids = client.resolve_label_names(config.default_labels, config.team_id)

        # Resolve assignee name/email to ID
        assignee_id = None
        if assignee:
            user = client.find_user(assignee)
            if not user:
                raise LinearError(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"User '{assignee}' not found",
                    suggestions=["Try email address or a different name", "Use `members` command to list users"],
                )
            assignee_id = user.get("id")

        issue = client.create_issue(
            config=config,
            title=title,
            description=description,
            priority=priority,
            estimate=estimate,
            parent_id=parent,
            project_id=project_id,
            no_project=no_project,
            label_ids=label_ids,
            assignee_id=assignee_id,
        )

        metadata = {
            "teamId": config.team_id,
        }
        if project_id:
            metadata["projectId"] = project_id
        elif config.project_id and not no_project:
            metadata["projectId"] = config.project_id

        result_data: dict[str, Any] = {
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "url": issue.get("url"),
            "state": issue.get("state", {}).get("name"),
        }
        label_nodes = issue.get("labels", {}).get("nodes", [])
        if label_nodes:
            result_data["labels"] = [l["name"] for l in label_nodes]

        response = format_success(
            command=command,
            result=result_data,
            metadata=metadata,
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def update(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="New title",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="New description",
    ),
    priority: Optional[int] = typer.Option(
        None,
        "--priority",
        "-p",
        help="New priority: 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low",
    ),
    estimate: Optional[int] = typer.Option(
        None,
        "--estimate",
        "-e",
        help="New estimate (T-shirt: XS=1, S=2, M=3, L=5, XL=8)",
    ),
    parent: Optional[str] = typer.Option(
        None,
        "--parent",
        help="Parent issue ID for reparenting (e.g., ABC-123)",
    ),
    label: Optional[list[str]] = typer.Option(
        None,
        "--label",
        help="Label name (repeatable) — replaces all existing labels",
    ),
    no_labels: bool = typer.Option(
        False,
        "--no-labels",
        help="Remove all labels from the issue",
    ),
    assignee: Optional[str] = typer.Option(
        None,
        "--assignee",
        help="Assignee name or email (resolved to user ID)",
    ),
    no_assignee: bool = typer.Option(
        False,
        "--no-assignee",
        help="Remove assignee from the issue",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Project name (resolved to ID)",
    ),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Remove from project",
    ),
) -> None:
    """Update an existing issue.

    Examples:
        linear.py update ABC-123 -t "New title"
        linear.py update ABC-123 -d "Updated description"
        linear.py update ABC-123 -p 2
        linear.py update ABC-123 -e 3
        linear.py update ABC-123 --parent ABC-456
        linear.py update ABC-123 --label mobile --label backend
        linear.py update ABC-123 --no-labels
        linear.py update ABC-123 --assignee "Roland"
        linear.py update ABC-123 --no-assignee
        linear.py update ABC-123 --project "My Project"
        linear.py update ABC-123 --no-project
    """
    command = "update"

    try:
        client = LinearClient()
        config = load_config()

        # Resolve parent identifier to UUID if provided
        parent_id = None
        if parent:
            parent_issue = client.get_issue(parent)
            parent_id = parent_issue.get("id")

        # Handle label updates
        label_ids = None
        removed_label_ids = None
        if no_labels or label:
            # Fetch current issue to get existing labels
            current_issue = client.get_issue(issue_id)
            current_labels = current_issue.get("labels", {}).get("nodes", [])
            current_label_ids = [l["id"] for l in current_labels]

            if no_labels:
                removed_label_ids = current_label_ids
            elif label:
                label_ids = client.resolve_label_names(label, config.team_id)
                # Remove labels not in the new set
                new_set = set(label_ids)
                removed_label_ids = [lid for lid in current_label_ids if lid not in new_set]

        # Resolve assignee
        assignee_id = None
        if no_assignee:
            assignee_id = ""  # Empty string signals unassign to update_issue
        elif assignee:
            user = client.find_user(assignee)
            if not user:
                raise LinearError(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"User '{assignee}' not found",
                    suggestions=["Try email address or a different name", "Use `members` command to list users"],
                )
            assignee_id = user.get("id")

        # Resolve project
        project_id = None
        if no_project:
            project_id = ""  # Empty string signals removal to update_issue
        elif project:
            found = client.find_project_by_name(project, config.team_id)
            project_id = found["id"]

        issue = client.update_issue(
            issue_id=issue_id,
            title=title,
            description=description,
            priority=priority,
            estimate=estimate,
            parent_id=parent_id,
            label_ids=label_ids,
            removed_label_ids=removed_label_ids,
            assignee_id=assignee_id,
            project_id=project_id,
        )

        result_data: dict[str, Any] = {
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "url": issue.get("url"),
            "state": issue.get("state", {}).get("name"),
        }
        label_nodes = issue.get("labels", {}).get("nodes", [])
        if label_nodes:
            result_data["labels"] = [l["name"] for l in label_nodes]
        project_node = issue.get("project")
        if project_node:
            result_data["project"] = project_node.get("name")

        response = format_success(
            command=command,
            result=result_data,
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def done(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
) -> None:
    """Mark an issue as completed.

    Examples:
        linear.py done ABC-123
    """
    command = "done"

    try:
        client = LinearClient()
        issue = client.mark_done(issue_id)

        response = format_success(
            command=command,
            result={
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "url": issue.get("url"),
                "state": issue.get("state", {}).get("name"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def state(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    state_name: str = typer.Argument(..., help="Target state name"),
) -> None:
    """Change an issue's state.

    Examples:
        linear.py state ABC-123 "In Progress"
        linear.py state ABC-123 "Done"
        linear.py state ABC-123 "Backlog"
    """
    command = "state"

    try:
        client = LinearClient()
        issue = client.change_state(issue_id, state_name)

        response = format_success(
            command=command,
            result={
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "url": issue.get("url"),
                "state": issue.get("state", {}).get("name"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("break")
def break_issue(
    issue_id: str = typer.Argument(..., help="Parent issue ID (e.g., ABC-123)"),
    issues: str = typer.Option(
        ...,
        "--issues",
        "-i",
        help='JSON array of sub-issues: [{"title": "...", "description": "...", "priority": N, "estimate": N}]',
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Project name for sub-issues (default: inherit from parent)",
    ),
    no_project: bool = typer.Option(
        False,
        "--no-project",
        help="Don't assign sub-issues to any project",
    ),
    label: Optional[list[str]] = typer.Option(
        None,
        "--label",
        help="Label name for sub-issues (repeatable) — overrides parent inheritance",
    ),
    no_labels: bool = typer.Option(
        False,
        "--no-labels",
        help="Don't inherit parent's labels",
    ),
) -> None:
    """Break down an issue into sub-issues.

    The --issues parameter must be a JSON array of objects with at minimum a "title" field.
    Optional fields: description, priority, estimate.

    By default, sub-issues inherit the parent's project and labels. Use --project/--label
    to override or --no-project/--no-labels to create without.

    Examples:
        linear.py break ABC-123 --issues '[{"title": "Design"}, {"title": "Implement"}, {"title": "Test"}]'
        linear.py break ABC-123 --issues '[{"title": "Task"}]' --project "Backend"
        linear.py break ABC-123 --issues '[{"title": "Task"}]' --label mobile
    """
    command = "break"

    try:
        config = load_config()
        client = LinearClient()

        # Parse JSON issues
        try:
            issues_data = json.loads(issues)
        except json.JSONDecodeError as e:
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid JSON for --issues: {e}",
                suggestions=["Ensure --issues is valid JSON array"],
            )

        if not isinstance(issues_data, list):
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message="--issues must be a JSON array",
                suggestions=['Use format: [{"title": "..."}, {"title": "..."}]'],
            )

        # Resolve project name to ID if provided
        project_id = None
        if project:
            project_info = client.find_project_by_name(project, config.team_id)
            project_id = project_info["id"]

        # Resolve label names to IDs if provided
        label_ids = None
        if label:
            label_ids = client.resolve_label_names(label, config.team_id)

        created = client.create_sub_issues(
            config, issue_id, issues_data,
            project_id=project_id, no_project=no_project,
            label_ids=label_ids, no_labels=no_labels,
        )

        formatted_created = []
        for i in created:
            entry: dict[str, Any] = {
                "identifier": i.get("identifier"),
                "title": i.get("title"),
                "url": i.get("url"),
            }
            sub_labels = i.get("labels", {}).get("nodes", [])
            if sub_labels:
                entry["labels"] = [l["name"] for l in sub_labels]
            formatted_created.append(entry)

        response = format_success(
            command=command,
            result={
                "parent": issue_id,
                "created": formatted_created,
            },
            metadata={
                "count": len(created),
                "teamId": config.team_id,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


RELATION_TYPES = {
    "blocks": "blocks",
    "blocked-by": "blocks",  # Flips source/target
    "relates-to": "related",
    "duplicates": "duplicate",
}


@app.command()
def relate(
    issue_id: str = typer.Argument(..., help="Source issue ID (e.g., ABC-123)"),
    relation: str = typer.Argument(
        ...,
        help="Relation type: blocks, blocked-by, relates-to, duplicates",
    ),
    target_id: str = typer.Argument(..., help="Target issue ID (e.g., ABC-456)"),
) -> None:
    """Create a relation between two issues.

    Supported relation types:
        blocks      — Source blocks target (target can't start until source is done)
        blocked-by  — Source is blocked by target (same as target blocks source)
        relates-to  — Issues are related (bidirectional)
        duplicates  — Source is a duplicate of target

    Examples:
        linear.py relate MIN-41 blocks MIN-42        # MIN-42 can't start until MIN-41 is done
        linear.py relate MIN-42 blocked-by MIN-41    # Same as above
        linear.py relate MIN-42 relates-to MIN-43    # Related issues
    """
    command = "relate"

    try:
        client = LinearClient()

        relation_lower = relation.lower()
        if relation_lower not in RELATION_TYPES:
            available = ", ".join(RELATION_TYPES.keys())
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message=f"Unknown relation type '{relation}'",
                suggestions=[f"Available types: {available}"],
            )

        api_type = RELATION_TYPES[relation_lower]

        # For "blocked-by", flip source and target
        if relation_lower == "blocked-by":
            source, target = target_id, issue_id
        else:
            source, target = issue_id, target_id

        result = client.create_relation(source, target, api_type)

        response = format_success(
            command=command,
            result={
                "source": issue_id,
                "relation": relation_lower,
                "target": target_id,
                "relationId": result.get("id"),
                "apiType": result.get("type"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def unrelate(
    issue_id: str = typer.Argument(..., help="First issue ID (e.g., ABC-123)"),
    target_id: str = typer.Argument(..., help="Second issue ID (e.g., ABC-456)"),
) -> None:
    """Remove a relation between two issues.

    Finds and deletes any relation between the two issues, regardless of direction.

    Examples:
        linear.py unrelate MIN-54 MIN-52
    """
    command = "unrelate"

    try:
        client = LinearClient()

        relation = client.find_relation(issue_id, target_id)
        if not relation:
            raise LinearError(
                code=ErrorCode.ISSUE_NOT_FOUND,
                message=f"No relation found between {issue_id} and {target_id}",
            )

        relation_id = relation.get("id")
        client.delete_relation(relation_id)

        response = format_success(
            command=command,
            result={
                "source": issue_id,
                "target": target_id,
                "deletedRelationId": relation_id,
                "relationType": relation.get("type"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def get(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    comments: bool = typer.Option(
        False,
        "--comments",
        "-c",
        help="Include full comment content",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Include all fields in response",
    ),
) -> None:
    """Fetch issue details.

    By default, shows comment count only. Use --comments to include full comment content.

    Examples:
        linear.py get ABC-123
        linear.py get ABC-123 --comments
    """
    command = "get"
    global _verbose
    _verbose = verbose

    try:
        client = LinearClient()
        issue = client.get_issue(issue_id, include_comments=comments)

        # Format children if present
        children = issue.get("children", {}).get("nodes", [])
        children_data = [
            {
                "identifier": c.get("identifier"),
                "title": c.get("title"),
                "priority": c.get("priority"),
                "estimate": c.get("estimate"),
                "state": c.get("state", {}).get("name"),
            }
            for c in children
        ]

        if _verbose:
            # Full output — all fields
            result: dict[str, Any] = {
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "description": issue.get("description"),
                "priority": issue.get("priority"),
                "estimate": issue.get("estimate"),
                "url": issue.get("url"),
                "state": {
                    "id": issue.get("state", {}).get("id"),
                    "name": issue.get("state", {}).get("name"),
                    "type": issue.get("state", {}).get("type"),
                },
                "team": {
                    "id": issue.get("team", {}).get("id"),
                    "key": issue.get("team", {}).get("key"),
                    "name": issue.get("team", {}).get("name"),
                },
            }
            assignee_data = issue.get("assignee")
            if assignee_data:
                result["assignee"] = {
                    "id": assignee_data.get("id"),
                    "name": assignee_data.get("name"),
                    "email": assignee_data.get("email"),
                }
            project = issue.get("project")
            if project:
                result["project"] = {
                    "id": project.get("id"),
                    "name": project.get("name"),
                }
            label_nodes = issue.get("labels", {}).get("nodes", [])
            if label_nodes:
                result["labels"] = [{"id": l["id"], "name": l["name"]} for l in label_nodes]
        else:
            # Concise output — only what Claude needs
            result = {
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "description": issue.get("description"),
                "priority": issue.get("priority"),
                "estimate": issue.get("estimate"),
                "state": issue.get("state", {}).get("name"),
            }
            assignee_data = issue.get("assignee")
            if assignee_data:
                result["assignee"] = assignee_data.get("name")
            project = issue.get("project")
            if project:
                result["project"] = project.get("name")
            label_nodes = issue.get("labels", {}).get("nodes", [])
            if label_nodes:
                result["labels"] = [l["name"] for l in label_nodes]

        # Add parent if exists
        parent = issue.get("parent")
        if parent:
            result["parent"] = {
                "identifier": parent.get("identifier"),
                "title": parent.get("title"),
            }

        # Add children if any
        if children_data:
            result["children"] = children_data

        # Add relations (verbose only)
        if _verbose:
            relations_data = []
            for rel in issue.get("relations", {}).get("nodes", []):
                related = rel.get("relatedIssue", {})
                relations_data.append({
                    "type": rel.get("type"),
                    "issue": related.get("identifier"),
                    "title": related.get("title"),
                })
            for rel in issue.get("inverseRelations", {}).get("nodes", []):
                rel_type = rel.get("type")
                # Invert the direction for display
                if rel_type == "blocks":
                    rel_type = "blocked-by"
                elif rel_type == "blocked-by":
                    rel_type = "blocks"
                related = rel.get("issue", {})
                relations_data.append({
                    "type": rel_type,
                    "issue": related.get("identifier"),
                    "title": related.get("title"),
                })
            if relations_data:
                result["relations"] = relations_data

            # Extract commit SHAs from attachments
            attachments = issue.get("attachments", {}).get("nodes", [])
            commits = []
            for att in attachments:
                url = att.get("url", "")
                if "/commit/" in url:
                    sha = url.rsplit("/commit/", 1)[-1]
                    commits.append(sha)
                elif url.startswith("commit://"):
                    commits.append(url.removeprefix("commit://"))
            if commits:
                result["commits"] = commits

        # Add comment data
        comments_nodes = issue.get("comments", {}).get("nodes", [])
        result["commentCount"] = len(comments_nodes)

        if comments:
            # Include full comment content
            result["comments"] = [
                {
                    "author": c.get("user", {}).get("name"),
                    "date": c.get("createdAt"),
                    "body": c.get("body"),
                }
                for c in comments_nodes
            ]

        response = format_success(command=command, result=result)
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def states(
    team_id: Optional[str] = typer.Option(
        None,
        "--team",
        "-t",
        help="Filter by team ID (optional)",
    ),
) -> None:
    """List workflow states.

    Without --team, returns all states across all teams.
    With --team, returns states for that specific team.

    Examples:
        linear.py states
        linear.py states --team abc123-team-uuid
    """
    command = "states"

    try:
        client = LinearClient()
        states_list = client.get_workflow_states(team_id)

        # Group by team for cleaner output
        teams: dict[str, dict] = {}
        for state in states_list:
            team = state.get("team", {})
            team_key = team.get("key", "unknown")
            if team_key not in teams:
                teams[team_key] = {
                    "id": team.get("id"),
                    "key": team_key,
                    "name": team.get("name"),
                    "states": [],
                }
            teams[team_key]["states"].append(
                {
                    "id": state.get("id"),
                    "name": state.get("name"),
                    "type": state.get("type"),
                    "position": state.get("position"),
                }
            )

        # Sort states by position within each team
        for team_data in teams.values():
            team_data["states"].sort(key=lambda s: s.get("position", 0))

        response = format_success(
            command=command,
            result={"teams": list(teams.values())},
            metadata={"totalStates": len(states_list)},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def projects(
    team_id: Optional[str] = typer.Option(
        None,
        "--team",
        "-t",
        help="Filter by team ID (optional)",
    ),
) -> None:
    """List projects.

    Without --team, returns all projects across all teams.
    With --team, returns projects for that specific team.

    Examples:
        linear.py projects
        linear.py projects --team abc123-team-uuid
    """
    command = "projects"

    try:
        client = LinearClient()
        projects_list = client.get_projects(team_id)

        # Group by team for cleaner output
        teams: dict[str, dict] = {}
        for project in projects_list:
            team = project.get("team", {})
            team_key = team.get("key", "unknown")
            if team_key not in teams:
                teams[team_key] = {
                    "id": team.get("id"),
                    "key": team_key,
                    "name": team.get("name"),
                    "projects": [],
                }
            teams[team_key]["projects"].append(
                {
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "state": project.get("state"),
                }
            )

        # Sort projects by name within each team
        for team_data in teams.values():
            team_data["projects"].sort(key=lambda p: p.get("name", "").lower())

        response = format_success(
            command=command,
            result={"teams": list(teams.values())},
            metadata={"totalProjects": len(projects_list)},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("create-project")
def create_project(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Project description",
    ),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Hex color (e.g. #FF6B35)",
    ),
    icon: Optional[str] = typer.Option(
        None,
        "--icon",
        help="Icon identifier",
    ),
    state: Optional[str] = typer.Option(
        None,
        "--state",
        help="Initial state (planned, started, paused, completed, canceled)",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date (YYYY-MM-DD)",
    ),
    target_date: Optional[str] = typer.Option(
        None,
        "--target-date",
        help="Target date (YYYY-MM-DD)",
    ),
) -> None:
    """Create a new project.

    Examples:
        linear.py create-project "Mobile App Redesign"
        linear.py create-project "Q1 Goals" -d "Quarterly objectives"
        linear.py create-project "Bug Bash" --state started --color "#FF6B35"
    """
    command = "create-project"

    try:
        config = load_config()
        client = LinearClient()

        project = client.create_project(
            name=name,
            team_ids=[config.team_id],
            description=description,
            color=color,
            icon=icon,
            state=state,
            start_date=start_date,
            target_date=target_date,
        )

        teams = [
            {"id": t.get("id"), "key": t.get("key"), "name": t.get("name")}
            for t in project.get("teams", {}).get("nodes", [])
        ]

        response = format_success(
            command=command,
            result={
                "id": project.get("id"),
                "name": project.get("name"),
                "state": project.get("state"),
                "teams": teams,
            },
            metadata={"teamId": config.team_id},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("delete-project")
def delete_project(
    name: str = typer.Argument(..., help="Project name to delete"),
) -> None:
    """Delete a project by name.

    Finds the project by name within the configured team and deletes it.

    Examples:
        linear.py delete-project "CLI Test Project"
    """
    command = "delete-project"

    try:
        config = load_config()
        client = LinearClient()

        project = client.find_project_by_name(name, config.team_id)
        client.delete_project(project["id"])

        response = format_success(
            command=command,
            result={
                "id": project.get("id"),
                "name": project.get("name"),
                "deleted": True,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("update-project")
def update_project(
    name: str = typer.Argument(..., help="Current project name (used to find it)"),
    new_name: Optional[str] = typer.Option(
        None,
        "--name",
        help="New project name",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="New description",
    ),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Hex color (e.g. #FF6B35)",
    ),
    icon: Optional[str] = typer.Option(
        None,
        "--icon",
        help="Icon identifier",
    ),
    state: Optional[str] = typer.Option(
        None,
        "--state",
        help="State: planned, started, paused, completed, canceled",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date (YYYY-MM-DD)",
    ),
    target_date: Optional[str] = typer.Option(
        None,
        "--target-date",
        help="Target date (YYYY-MM-DD)",
    ),
) -> None:
    """Update a project by name.

    Finds the project by name within the configured team and updates it.

    Examples:
        linear.py update-project "My Project" --name "Renamed Project"
        linear.py update-project "My Project" --state paused -d "Updated desc"
        linear.py update-project "My Project" --start-date 2025-01-01 --target-date 2025-06-30
    """
    command = "update-project"

    try:
        config = load_config()
        client = LinearClient()

        project = client.find_project_by_name(name, config.team_id)

        updated = client.update_project(
            project_id=project["id"],
            name=new_name,
            description=description,
            color=color,
            icon=icon,
            state=state,
            start_date=start_date,
            target_date=target_date,
        )

        teams = [
            {"id": t.get("id"), "key": t.get("key"), "name": t.get("name")}
            for t in updated.get("teams", {}).get("nodes", [])
        ]

        response = format_success(
            command=command,
            result={
                "id": updated.get("id"),
                "name": updated.get("name"),
                "state": updated.get("state"),
                "teams": teams,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def labels(
    team_id: Optional[str] = typer.Option(
        None,
        "--team",
        "-t",
        help="Filter by team ID (optional)",
    ),
) -> None:
    """List labels.

    Without --team, returns all labels across all teams.
    With --team, returns labels for that specific team.

    Examples:
        linear.py labels
        linear.py labels --team abc123-team-uuid
    """
    command = "labels"

    try:
        client = LinearClient()
        labels_list = client.get_labels(team_id)

        # Group by team for cleaner output
        teams: dict[str, dict] = {}
        for label in labels_list:
            team = label.get("team") or {}
            team_key = team.get("key", "workspace")
            if team_key not in teams:
                teams[team_key] = {
                    "id": team.get("id"),
                    "key": team_key,
                    "name": team.get("name"),
                    "labels": [],
                }
            teams[team_key]["labels"].append(
                {
                    "id": label.get("id"),
                    "name": label.get("name"),
                    "color": label.get("color"),
                    "description": label.get("description"),
                }
            )

        # Sort labels by name within each team
        for team_data in teams.values():
            team_data["labels"].sort(key=lambda l: l.get("name", "").lower())

        response = format_success(
            command=command,
            result={"teams": list(teams.values())},
            metadata={"totalLabels": len(labels_list)},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("create-label")
def create_label_cmd(
    name: str = typer.Argument(..., help="Label name"),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Hex color (e.g. #4CAF50)",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Label description",
    ),
) -> None:
    """Create a new label.

    Examples:
        linear.py create-label "mobile"
        linear.py create-label "mobile" --color "#4CAF50"
        linear.py create-label "backend" --color "#2196F3" -d "Backend services"
    """
    command = "create-label"

    try:
        config = load_config()
        client = LinearClient()

        label = client.create_label(
            name=name,
            team_id=config.team_id,
            color=color,
            description=description,
        )

        team = label.get("team", {})
        response = format_success(
            command=command,
            result={
                "id": label.get("id"),
                "name": label.get("name"),
                "color": label.get("color"),
                "team": {
                    "id": team.get("id"),
                    "key": team.get("key"),
                    "name": team.get("name"),
                },
            },
            metadata={"teamId": config.team_id},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("delete-label")
def delete_label_cmd(
    name: str = typer.Argument(..., help="Label name to delete"),
) -> None:
    """Delete a label by name.

    Finds the label by name within the configured team and deletes it.

    Examples:
        linear.py delete-label "mobile"
    """
    command = "delete-label"

    try:
        config = load_config()
        client = LinearClient()

        label = client.find_label_by_name(name, config.team_id)
        client.delete_label(label["id"])

        response = format_success(
            command=command,
            result={
                "id": label.get("id"),
                "name": label.get("name"),
                "deleted": True,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("update-label")
def update_label(
    name: str = typer.Argument(..., help="Current label name (used to find it)"),
    new_name: Optional[str] = typer.Option(
        None,
        "--name",
        help="New label name",
    ),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Hex color (e.g. #FF6B35)",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="New description",
    ),
) -> None:
    """Update a label by name.

    Finds the label by name within the configured team and updates it.
    Preserves all issue associations (unlike delete + recreate).

    Examples:
        linear.py update-label "old-name" --name "new-name"
        linear.py update-label "mobile" --color "#FF6B35" -d "Updated description"
    """
    command = "update-label"

    try:
        config = load_config()
        client = LinearClient()

        label = client.find_label_by_name(name, config.team_id)

        updated = client.update_label(
            label_id=label["id"],
            name=new_name,
            color=color,
            description=description,
        )

        team = updated.get("team") or {}

        response = format_success(
            command=command,
            result={
                "id": updated.get("id"),
                "name": updated.get("name"),
                "color": updated.get("color"),
                "description": updated.get("description"),
                "team": {"id": team.get("id"), "key": team.get("key"), "name": team.get("name")} if team else None,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def members() -> None:
    """List active workspace members.

    Shows name, email, and displayName for each active user.

    Examples:
        linear.py members
    """
    command = "members"

    try:
        client = LinearClient()
        users = client.get_users()

        active_users = [
            {
                "name": u.get("name"),
                "email": u.get("email"),
                "displayName": u.get("displayName"),
            }
            for u in users
            if u.get("active", False)
        ]

        response = format_success(
            command=command,
            result={"members": active_users},
            metadata={"count": len(active_users)},
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("list")
def list_cmd(
    mine: bool = typer.Option(
        False,
        "--mine",
        "-m",
        help="Issues assigned to me",
    ),
    assignee: Optional[str] = typer.Option(
        None,
        "--assignee",
        "-a",
        help="Filter by assignee (email or name)",
    ),
    creator: Optional[str] = typer.Option(
        None,
        "--creator",
        "-c",
        help="Filter by creator (email or name)",
    ),
    priority: Optional[str] = typer.Option(
        None,
        "--priority",
        "-p",
        help="Filter by priority (0-4 or none/urgent/high/normal/low)",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Filter by project name",
    ),
    state: Optional[str] = typer.Option(
        None,
        "--state",
        "-s",
        help="Filter by state name or type (backlog/todo/started/done/canceled)",
    ),
    limit: int = typer.Option(
        25,
        "--limit",
        "-l",
        help="Max results (default 25)",
    ),
    team: Optional[str] = typer.Option(
        None,
        "--team",
        "-t",
        help="Filter by team (uses config team if not specified)",
    ),
    estimate: Optional[str] = typer.Option(
        None,
        "--estimate",
        "-e",
        help="Filter by estimate (number or 'none' for unestimated)",
    ),
    label: Optional[list[str]] = typer.Option(
        None,
        "--label",
        help="Filter by label name (repeatable, AND logic)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Include all fields and metadata in response",
    ),
) -> None:
    """List issues with optional filters.

    All filters combine with AND logic.

    Examples:
        linear.py list                          # All issues (up to 25)
        linear.py list --mine                   # Assigned to me
        linear.py list --priority 0             # No priority set
        linear.py list --priority none          # Same as above
        linear.py list --state done             # Completed issues
        linear.py list --mine --state started   # My in-progress issues
        linear.py list --project "Backend"      # Issues in Backend project
        linear.py list --estimate none          # Unestimated issues
        linear.py list --estimate 3             # Issues with estimate=3
        linear.py list --label mobile           # Issues with mobile label
    """
    command = "list"
    global _verbose
    _verbose = verbose

    try:
        client = LinearClient()

        # Determine team ID
        team_id = team
        if not team_id:
            try:
                config = load_config()
                team_id = config.team_id
            except LinearError:
                # No config, proceed without team filter
                pass

        # Handle --mine flag
        assignee_id = None
        if mine:
            viewer = client.get_viewer()
            assignee_id = viewer.get("id")
            if not assignee_id:
                raise LinearError(
                    code=ErrorCode.API_ERROR,
                    message="Could not determine current user",
                )
        elif assignee:
            user = client.find_user(assignee)
            if not user:
                raise LinearError(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"User '{assignee}' not found",
                    suggestions=["Try email address or a different name"],
                )
            assignee_id = user.get("id")

        # Handle creator filter
        creator_id = None
        if creator:
            user = client.find_user(creator)
            if not user:
                raise LinearError(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"User '{creator}' not found",
                    suggestions=["Try email address or a different name"],
                )
            creator_id = user.get("id")

        # Handle priority filter
        priority_val = None
        if priority is not None:
            priority_val = parse_priority(priority)

        # Handle estimate filter
        estimate_val = None
        no_estimate = False
        if estimate is not None:
            if estimate.lower() == "none":
                no_estimate = True
            else:
                try:
                    estimate_val = int(estimate)
                except ValueError:
                    raise LinearError(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Invalid estimate '{estimate}'",
                        suggestions=["Use a number or 'none' for unestimated issues"],
                    )

        # Handle project filter
        project_id = None
        if project:
            project_info = client.find_project_by_name(project, team_id)
            project_id = project_info.get("id")

        # Handle state filter
        state_id = None
        state_type = None
        if state:
            state_lower = state.lower().replace(" ", "_")
            # Check if it's a type alias
            if state_lower in STATE_TYPE_ALIASES:
                state_type = STATE_TYPE_ALIASES[state_lower]
            elif team_id:
                # Try to find by name
                try:
                    state_info = client.find_state_by_name(team_id, state)
                    state_id = state_info.get("id")
                except LinearError:
                    raise LinearError(
                        code=ErrorCode.STATE_NOT_FOUND,
                        message=f"State '{state}' not found",
                        suggestions=[
                            "Use state name (e.g., 'In Progress') or type shortcut",
                            "Type shortcuts: backlog, todo, started, done, canceled",
                        ],
                    )
            else:
                raise LinearError(
                    code=ErrorCode.STATE_NOT_FOUND,
                    message=f"Cannot resolve state '{state}' without team context",
                    suggestions=[
                        "Use type shortcuts: backlog, todo, started, done, canceled",
                        "Or specify --team or create .linear.json",
                    ],
                )

        # Handle label filter
        label_ids = None
        if label:
            label_ids = client.resolve_label_names(label, team_id)

        # Fetch issues
        issues = client.list_issues(
            team_id=team_id,
            assignee_id=assignee_id,
            creator_id=creator_id,
            priority=priority_val,
            project_id=project_id,
            state_id=state_id,
            state_type=state_type,
            estimate=estimate_val,
            no_estimate=no_estimate,
            label_ids=label_ids,
            limit=limit,
        )

        # Format output
        priority_labels = {0: "None", 1: "Urgent", 2: "High", 3: "Normal", 4: "Low"}
        formatted_issues = []
        for issue in issues:
            formatted = {
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "state": issue.get("state", {}).get("name"),
                "priority": priority_labels.get(issue.get("priority", 0), "Unknown"),
                "estimate": issue.get("estimate"),
            }
            assignee_data = issue.get("assignee")
            if assignee_data:
                formatted["assignee"] = assignee_data.get("name")
            label_nodes = issue.get("labels", {}).get("nodes", [])
            if label_nodes:
                formatted["labels"] = [l["name"] for l in label_nodes]
            formatted_issues.append(formatted)

        # Build metadata
        metadata: dict[str, Any] = {"count": len(issues), "limit": limit}
        filters_applied = []
        if mine:
            filters_applied.append("mine")
        if assignee:
            filters_applied.append(f"assignee={assignee}")
        if creator:
            filters_applied.append(f"creator={creator}")
        if priority is not None:
            filters_applied.append(f"priority={priority}")
        if project:
            filters_applied.append(f"project={project}")
        if state:
            filters_applied.append(f"state={state}")
        if estimate is not None:
            filters_applied.append(f"estimate={estimate}")
        if label:
            filters_applied.append(f"label={','.join(label)}")
        if team_id:
            filters_applied.append(f"team={team_id[:8]}...")
        if filters_applied:
            metadata["filters"] = filters_applied

        response = format_success(
            command=command,
            result={"issues": formatted_issues},
            metadata=metadata,
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def attach(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    file_path: str = typer.Argument(..., help="Path to local file"),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Display title (default: filename)",
    ),
    subtitle: Optional[str] = typer.Option(
        None,
        "--subtitle",
        "-s",
        help="Subtitle text",
    ),
) -> None:
    """Attach a file to an issue.

    Uploads the file to Linear's storage and creates an attachment link on the issue.

    Examples:
        linear.py attach ABC-123 screenshot.png
        linear.py attach ABC-123 report.pdf -t "Test Report"
        linear.py attach ABC-123 design.fig -t "Design Spec" -s "Final version"
    """
    command = "attach"

    try:
        client = LinearClient()

        # Default title to filename
        display_title = title or Path(file_path).name

        # Upload file and create attachment
        asset_url = client.upload_file(file_path)
        attachment = client.create_attachment(
            issue_id=issue_id,
            url=asset_url,
            title=display_title,
            subtitle=subtitle,
        )

        response = format_success(
            command=command,
            result={
                "identifier": issue_id,
                "title": attachment.get("title"),
                "attachmentUrl": attachment.get("url"),
                "assetUrl": asset_url,
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def document(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    title: str = typer.Argument(..., help="Document title"),
    content: Optional[str] = typer.Option(
        None,
        "--content",
        "-c",
        help="Document content in markdown",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="Read content from a markdown file",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Also link to a project by name",
    ),
) -> None:
    """Create a document linked to an issue.

    Creates a native Linear document viewable inline on the issue.
    Content can be provided inline with --content or read from a file with --file.

    Examples:
        linear.py document ABC-123 "Design Notes" -c "## Overview\\nKey decisions..."
        linear.py document ABC-123 "Tech Spec" -f spec.md
        linear.py document ABC-123 "Requirements" -c "# Requirements" --project "Backend"
    """
    command = "document"

    try:
        client = LinearClient()

        # Resolve content from file if provided
        doc_content = content
        if file:
            file_path = Path(file)
            if not file_path.exists():
                raise LinearError(
                    code=ErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file}",
                    suggestions=["Check the file path is correct"],
                )
            doc_content = file_path.read_text(encoding="utf-8")

        # Resolve project name to ID if provided
        project_id = None
        if project:
            try:
                config = load_config()
                team_id = config.team_id
            except LinearError:
                team_id = None
            project_info = client.find_project_by_name(project, team_id)
            project_id = project_info["id"]

        doc = client.create_document(
            issue_id=issue_id,
            title=title,
            content=doc_content,
            project_id=project_id,
        )

        result: dict[str, Any] = {
            "identifier": issue_id,
            "documentId": doc.get("id"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "slugId": doc.get("slugId"),
        }

        issue_ref = doc.get("issue")
        if issue_ref:
            result["issue"] = issue_ref.get("identifier")

        project_ref = doc.get("project")
        if project_ref:
            result["project"] = project_ref.get("name")

        response = format_success(command=command, result=result)
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command("attach-commit")
def attach_commit(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    commit: str = typer.Argument(
        default=None, help="Commit SHA to attach (defaults to HEAD)"
    ),
) -> None:
    """Attach a git commit to an issue.

    Reads the commit (hash, message, author) and creates an
    attachment on the issue linking to the commit on GitHub/GitLab.

    Examples:
        linear.py attach-commit ABC-123
        linear.py attach-commit ABC-123 a1b2c3d
    """
    command = "attach-commit"

    try:
        # Get git commit info
        ref = commit or "HEAD"
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", ref], text=True
            ).strip()
            commit_msg = subprocess.check_output(
                ["git", "log", "-1", "--format=%s", commit_hash], text=True
            ).strip()
            commit_author = subprocess.check_output(
                ["git", "log", "-1", "--format=%an", commit_hash], text=True
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise LinearError(
                code=ErrorCode.INVALID_INPUT,
                message="Could not read git commit info",
                suggestions=["Ensure you are in a git repository with at least one commit"],
            )

        # Construct commit URL from remote
        commit_url = f"commit://{commit_hash[:12]}"
        try:
            remote_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"], text=True
            ).strip()
            # SSH: git@github.com:org/repo.git -> https://github.com/org/repo
            # HTTPS: https://github.com/org/repo.git -> https://github.com/org/repo
            if remote_url.startswith("git@"):
                # git@github.com:org/repo.git
                host_path = remote_url.split("@", 1)[1]
                host, path = host_path.split(":", 1)
                path = path.removesuffix(".git")
                commit_url = f"https://{host}/{path}/commit/{commit_hash}"
            elif remote_url.startswith("https://") or remote_url.startswith("http://"):
                base = remote_url.removesuffix(".git")
                commit_url = f"{base}/commit/{commit_hash}"
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            # No remote or parse error — use local fallback URL
            pass

        short_hash = commit_hash[:8]
        title = f"{short_hash}: {commit_msg}"
        subtitle = f"by {commit_author}"

        client = LinearClient()
        attachment = client.create_attachment(
            issue_id=issue_id,
            url=commit_url,
            title=title,
            subtitle=subtitle,
        )

        response = format_success(
            command=command,
            result={
                "identifier": issue_id,
                "commitHash": commit_hash,
                "commitMessage": commit_msg,
                "commitUrl": commit_url,
                "attachmentId": attachment.get("id"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


@app.command()
def comment(
    issue_id: str = typer.Argument(..., help="Issue ID (e.g., ABC-123)"),
    body: str = typer.Argument(..., help="Comment body (markdown supported)"),
) -> None:
    """Post a comment on an issue.

    Examples:
        linear.py comment ABC-123 "Fixed in commit abc123"
        linear.py comment ABC-123 "## Resolution\\nAddressed by PR #42"
    """
    command = "comment"

    try:
        client = LinearClient()
        result = client.create_comment(issue_id, body)

        response = format_success(
            command=command,
            result={
                "identifier": result.get("issue", {}).get("identifier", issue_id),
                "title": result.get("issue", {}).get("title"),
                "commentId": result.get("id"),
                "url": result.get("url"),
            },
        )
        typer.echo(output_json(response))

    except LinearError as e:
        error_response = format_error(command, e)
        typer.echo(output_json(error_response))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
