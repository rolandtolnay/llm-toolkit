#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx",
#     "typer",
# ]
# ///
"""
Slack CLI - Standalone skill for Slack messaging and search.

A single-file PEP 723 script that provides a CLI interface to Slack's REST API.
Designed to work from any project directory using a SLACK_USER_TOKEN env var.

Usage:
    uv run slack.py <command> [options]

Commands:
    send            Send a message to a channel or person
    edit            Edit a sent message
    search          Search messages across the workspace
    history         Get recent messages from a channel
    read-thread     Read replies in a thread
    channels        List channels
    users           List workspace members
    delete          Delete a message
    react           Add a reaction to a message
    status          Set or clear your Slack status
    schedule        Schedule a message for later
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from enum import Enum
from typing import Any, Optional

import httpx
import typer


# =============================================================================
# Errors
# =============================================================================


class ErrorCode(str, Enum):
    """Error codes for CLI responses."""

    MISSING_TOKEN = "MISSING_TOKEN"
    AUTH_FAILED = "AUTH_FAILED"
    CHANNEL_NOT_FOUND = "CHANNEL_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"


# Map Slack error strings to our error codes
SLACK_ERROR_MAP: dict[str, ErrorCode] = {
    "not_authed": ErrorCode.AUTH_FAILED,
    "invalid_auth": ErrorCode.AUTH_FAILED,
    "token_revoked": ErrorCode.AUTH_FAILED,
    "token_expired": ErrorCode.AUTH_FAILED,
    "channel_not_found": ErrorCode.CHANNEL_NOT_FOUND,
    "user_not_found": ErrorCode.USER_NOT_FOUND,
    "message_not_found": ErrorCode.MESSAGE_NOT_FOUND,
    "cant_delete_message": ErrorCode.PERMISSION_DENIED,
    "cant_update_message": ErrorCode.PERMISSION_DENIED,
    "missing_scope": ErrorCode.PERMISSION_DENIED,
    "not_in_channel": ErrorCode.PERMISSION_DENIED,
    "time_in_past": ErrorCode.API_ERROR,
    "time_too_far": ErrorCode.API_ERROR,
    "invalid_time": ErrorCode.API_ERROR,
    "ratelimited": ErrorCode.RATE_LIMITED,
}


class SlackError(Exception):
    """Base exception for Slack CLI errors."""

    def __init__(self, code: ErrorCode, message: str, suggestions: list[str] | None = None):
        self.code = code
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


# =============================================================================
# Output Formatting
# =============================================================================


def format_success(command: str, result: dict[str, Any]) -> dict[str, Any]:
    """Format successful response."""
    return {
        "success": True,
        "command": command,
        "result": result,
    }


def format_error(command: str, error: SlackError) -> dict[str, Any]:
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


TOKEN_SETUP_SUGGESTIONS = [
    "Set SLACK_USER_TOKEN in project .claude/settings.local.json: {\"env\": {\"SLACK_USER_TOKEN\": \"xoxp-...\"}}",
    "Create a Slack app at https://api.slack.com/apps → 'From scratch'",
    "Add User Token Scopes: chat:write, search:read, channels:history, channels:read, users:read, users.profile:write, groups:history, groups:read, reactions:write, im:history",
    "Install to workspace and copy the xoxp-... token",
]


# =============================================================================
# Slack Client
# =============================================================================

SLACK_API_BASE = "https://slack.com/api"


class SlackClient:
    """Client for Slack REST API."""

    def __init__(self) -> None:
        self.token = os.environ.get("SLACK_USER_TOKEN", "")
        if not self.token:
            raise SlackError(
                code=ErrorCode.MISSING_TOKEN,
                message="SLACK_USER_TOKEN environment variable not set",
                suggestions=TOKEN_SETUP_SUGGESTIONS,
            )
        self._http = httpx.Client(
            base_url=SLACK_API_BASE,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30.0,
        )
        self._users_cache: list[dict[str, Any]] | None = None

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a REST call to Slack API and check for errors."""
        try:
            if method == "POST":
                resp = self._http.post(endpoint, json=json_body)
            else:
                resp = self._http.get(endpoint, params=params)

            resp.raise_for_status()
            data = resp.json()

        except httpx.TimeoutException:
            raise SlackError(
                code=ErrorCode.NETWORK_ERROR,
                message="Request to Slack API timed out",
                suggestions=["Check your network connection", "Try again in a moment"],
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After", "30")
                raise SlackError(
                    code=ErrorCode.RATE_LIMITED,
                    message=f"Rate limited by Slack API. Retry after {retry_after}s",
                    suggestions=[f"Wait {retry_after} seconds and try again"],
                )
            raise SlackError(
                code=ErrorCode.NETWORK_ERROR,
                message=f"HTTP {e.response.status_code} from Slack API",
            )
        except httpx.HTTPError:
            raise SlackError(
                code=ErrorCode.NETWORK_ERROR,
                message="Failed to connect to Slack API",
                suggestions=["Check your network connection"],
            )

        if not data.get("ok"):
            slack_error = data.get("error", "unknown_error")
            error_code = SLACK_ERROR_MAP.get(slack_error, ErrorCode.API_ERROR)
            suggestions: list[str] = []
            if error_code == ErrorCode.AUTH_FAILED:
                suggestions = TOKEN_SETUP_SUGGESTIONS
            elif error_code == ErrorCode.PERMISSION_DENIED:
                suggestions = [
                    f"Slack error: {slack_error}",
                    "Check that your token has the required scopes",
                    "You may need to reinstall the Slack app to add new scopes",
                ]
            raise SlackError(
                code=error_code,
                message=f"Slack API error: {slack_error}",
                suggestions=suggestions,
            )

        return data

    # -------------------------------------------------------------------------
    # User resolution
    # -------------------------------------------------------------------------

    def _fetch_users(self) -> list[dict[str, Any]]:
        """Fetch and cache all workspace members."""
        if self._users_cache is not None:
            return self._users_cache

        members: list[dict[str, Any]] = []
        cursor = None

        while True:
            params: dict[str, Any] = {"limit": 200}
            if cursor:
                params["cursor"] = cursor

            data = self._request("GET", "users.list", params=params)
            for m in data.get("members", []):
                if m.get("deleted") or m.get("is_bot") or m.get("id") == "USLACKBOT":
                    continue
                members.append(m)

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        self._users_cache = members
        return members

    def list_users(self, search: str | None = None) -> list[dict[str, Any]]:
        """List workspace members, optionally filtered by name."""
        members = self._fetch_users()
        if not search:
            return [
                {
                    "id": m["id"],
                    "real_name": m.get("real_name", ""),
                    "display_name": m.get("profile", {}).get("display_name", ""),
                }
                for m in members
            ]

        search_lower = search.lower()
        results = []
        for m in members:
            real_name = m.get("real_name", "").lower()
            display_name = m.get("profile", {}).get("display_name", "").lower()
            if search_lower in real_name or search_lower in display_name:
                results.append({
                    "id": m["id"],
                    "real_name": m.get("real_name", ""),
                    "display_name": m.get("profile", {}).get("display_name", ""),
                })
        return results

    def find_user(self, name: str) -> dict[str, Any]:
        """Find a single user by fuzzy name match."""
        matches = self.list_users(search=name)
        if not matches:
            raise SlackError(
                code=ErrorCode.USER_NOT_FOUND,
                message=f"No user found matching '{name}'",
                suggestions=["Use 'users' command to list all workspace members"],
            )
        if len(matches) == 1:
            return matches[0]

        # Try exact first-name match
        name_lower = name.lower()
        exact = [
            m for m in matches
            if m["real_name"].lower().split()[0] == name_lower
            or m["display_name"].lower() == name_lower
        ]
        if len(exact) == 1:
            return exact[0]

        # Multiple matches — return best guess (first) but include all in result
        raise SlackError(
            code=ErrorCode.USER_NOT_FOUND,
            message=f"Multiple users match '{name}': {', '.join(m['real_name'] for m in matches)}",
            suggestions=[f"Be more specific, or use a user ID directly"],
        )

    # -------------------------------------------------------------------------
    # Channel resolution
    # -------------------------------------------------------------------------

    def list_channels(self, search: str | None = None) -> list[dict[str, Any]]:
        """List channels, optionally filtered by name."""
        all_channels: list[dict[str, Any]] = []
        cursor = None

        while True:
            params: dict[str, Any] = {
                "types": "public_channel,private_channel",
                "limit": 200,
                "exclude_archived": "true",
            }
            if cursor:
                params["cursor"] = cursor

            data = self._request("GET", "conversations.list", params=params)
            all_channels.extend(data.get("channels", []))

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        results = []
        for c in all_channels:
            if search and search.lower() not in c.get("name", "").lower():
                continue
            results.append({
                "id": c["id"],
                "name": c.get("name", ""),
                "is_private": c.get("is_private", False),
                "num_members": c.get("num_members", 0),
            })

        return results

    def find_channel(self, name: str) -> dict[str, Any]:
        """Find a channel by name (with or without # prefix)."""
        name = name.lstrip("#")
        channels = self.list_channels(search=name)

        # Look for exact match first
        for c in channels:
            if c["name"] == name:
                return c

        if not channels:
            raise SlackError(
                code=ErrorCode.CHANNEL_NOT_FOUND,
                message=f"No channel found matching '{name}'",
                suggestions=["Use 'channels' command to list available channels"],
            )

        if len(channels) == 1:
            return channels[0]

        raise SlackError(
            code=ErrorCode.CHANNEL_NOT_FOUND,
            message=f"Multiple channels match '{name}': {', '.join(c['name'] for c in channels[:5])}",
            suggestions=["Be more specific, or use a channel ID directly"],
        )

    def open_dm(self, user_id: str) -> str:
        """Open a DM conversation and return the channel ID."""
        data = self._request("POST", "conversations.open", json_body={"users": user_id})
        channel = data.get("channel", {})
        return channel.get("id", "")

    def resolve_target(self, target: str) -> str:
        """Resolve a target string to a channel ID.

        - Channel ID (starts with C/G/D) → use directly
        - #name → find channel by name
        - Otherwise → find user by name, open DM
        """
        if target and target[0] in ("C", "G", "D") and len(target) > 8 and target[1:].isalnum():
            return target

        if target.startswith("#"):
            channel = self.find_channel(target)
            return channel["id"]

        # Assume it's a person's name
        user = self.find_user(target)
        return self.open_dm(user["id"])

    # -------------------------------------------------------------------------
    # User ID → name resolution for history output
    # -------------------------------------------------------------------------

    def _build_user_map(self) -> dict[str, str]:
        """Build a user_id → display_name map from cached users."""
        members = self._fetch_users()
        user_map: dict[str, str] = {}
        for m in members:
            display = m.get("profile", {}).get("display_name", "") or m.get("real_name", "")
            user_map[m["id"]] = display or m["id"]
        return user_map

    def _resolve_user_name(self, user_id: str, user_map: dict[str, str]) -> str:
        """Resolve a user ID to a name using the provided map."""
        return user_map.get(user_id, user_id)

    # -------------------------------------------------------------------------
    # API methods
    # -------------------------------------------------------------------------

    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """Send a message to a channel or thread."""
        body: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            body["thread_ts"] = thread_ts

        data = self._request("POST", "chat.postMessage", json_body=body)
        msg = data.get("message", {})
        return {
            "channel": data.get("channel", channel),
            "ts": msg.get("ts", ""),
            "text": msg.get("text", text),
        }

    def search_messages(self, query: str, count: int = 20) -> dict[str, Any]:
        """Search messages across the workspace."""
        data = self._request(
            "GET",
            "search.messages",
            params={
                "query": query,
                "sort": "timestamp",
                "sort_dir": "desc",
                "count": count,
            },
        )
        messages_data = data.get("messages", {})
        matches = messages_data.get("matches", [])
        total = messages_data.get("total", 0)

        results = []
        for m in matches:
            results.append({
                "channel": m.get("channel", {}).get("name", "?"),
                "user": m.get("username", "unknown"),
                "text": m.get("text", "")[:300],
                "ts": m.get("ts", ""),
                "permalink": m.get("permalink", ""),
            })

        return {"total": total, "messages": results}

    def get_history(self, channel: str, limit: int = 20) -> dict[str, Any]:
        """Get recent messages from a channel."""
        data = self._request(
            "GET",
            "conversations.history",
            params={"channel": channel, "limit": limit},
        )

        user_map = self._build_user_map()
        messages = []
        for m in data.get("messages", []):
            user_id = m.get("user", m.get("bot_id", "?"))
            messages.append({
                "user": self._resolve_user_name(user_id, user_map),
                "user_id": user_id,
                "text": m.get("text", "")[:500],
                "ts": m.get("ts", ""),
                "thread_reply_count": m.get("reply_count", 0),
            })

        return {"channel": channel, "messages": messages}

    def get_thread(self, channel: str, thread_ts: str) -> dict[str, Any]:
        """Get all replies in a thread."""
        data = self._request(
            "GET",
            "conversations.replies",
            params={"channel": channel, "ts": thread_ts},
        )

        user_map = self._build_user_map()
        messages = []
        for m in data.get("messages", []):
            user_id = m.get("user", m.get("bot_id", "?"))
            messages.append({
                "user": self._resolve_user_name(user_id, user_map),
                "user_id": user_id,
                "text": m.get("text", "")[:500],
                "ts": m.get("ts", ""),
            })

        return {"channel": channel, "thread_ts": thread_ts, "messages": messages}

    def delete_message(self, channel: str, ts: str) -> dict[str, Any]:
        """Delete a message."""
        self._request("POST", "chat.delete", json_body={"channel": channel, "ts": ts})
        return {"channel": channel, "ts": ts, "deleted": True}

    def add_reaction(self, channel: str, ts: str, emoji: str) -> dict[str, Any]:
        """Add a reaction emoji to a message."""
        # Strip colons if user included them (e.g. :thumbsup: → thumbsup)
        emoji = emoji.strip(":")
        self._request(
            "POST",
            "reactions.add",
            json_body={"channel": channel, "timestamp": ts, "name": emoji},
        )
        return {"channel": channel, "ts": ts, "emoji": emoji}

    def edit_message(self, channel: str, ts: str, text: str) -> dict[str, Any]:
        """Edit a message (only your own messages)."""
        data = self._request(
            "POST",
            "chat.update",
            json_body={"channel": channel, "ts": ts, "text": text},
        )
        msg = data.get("message", {})
        return {
            "channel": data.get("channel", channel),
            "ts": msg.get("ts", ts),
            "text": msg.get("text", text),
        }

    def set_status(
        self,
        text: str,
        emoji: str = "",
        expiration: int = 0,
    ) -> dict[str, Any]:
        """Set or clear the user's Slack status."""
        emoji = emoji.strip(":") if emoji else ""
        if emoji:
            emoji = f":{emoji}:"
        profile: dict[str, Any] = {
            "status_text": text,
            "status_emoji": emoji,
        }
        if expiration > 0:
            profile["status_expiration"] = expiration

        self._request(
            "POST",
            "users.profile.set",
            json_body={"profile": profile},
        )
        result: dict[str, Any] = {"status_text": text, "status_emoji": emoji}
        if expiration > 0:
            result["status_expiration"] = expiration
        return result

    def schedule_message(
        self,
        channel: str,
        text: str,
        post_at: int,
    ) -> dict[str, Any]:
        """Schedule a message for later delivery."""
        data = self._request(
            "POST",
            "chat.scheduleMessage",
            json_body={"channel": channel, "text": text, "post_at": post_at},
        )
        return {
            "channel": data.get("channel", channel),
            "scheduled_message_id": data.get("scheduled_message_id", ""),
            "post_at": data.get("post_at", post_at),
            "text": text,
        }


# =============================================================================
# CLI Commands
# =============================================================================

app = typer.Typer(
    name="slack",
    help="Slack CLI - send messages, search, and read channel history",
    add_completion=False,
)


def _run_command(command_name: str, func: Any) -> None:
    """Execute a command function with standard error handling."""
    try:
        result = func()
        typer.echo(output_json(format_success(command_name, result)))
    except SlackError as e:
        typer.echo(output_json(format_error(command_name, e)))
        raise typer.Exit(code=1)


@app.command()
def send(
    target: str = typer.Argument(..., help="Channel (#name or ID) or person's name"),
    message: str = typer.Argument(..., help="Message text to send"),
    thread: Optional[str] = typer.Option(
        None,
        "--thread",
        "-t",
        help="Thread timestamp to reply to",
    ),
) -> None:
    """Send a message to a channel or person."""
    def _send() -> dict[str, Any]:
        client = SlackClient()
        channel_id = client.resolve_target(target)
        return client.send_message(channel_id, message, thread_ts=thread)

    _run_command("send", _send)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (supports Slack search modifiers)"),
    count: int = typer.Option(20, "--count", "-c", help="Number of results (default 20)"),
) -> None:
    """Search messages across the workspace."""
    def _search() -> dict[str, Any]:
        client = SlackClient()
        return client.search_messages(query, count=count)

    _run_command("search", _search)


@app.command()
def history(
    channel: str = typer.Argument(..., help="Channel (#name or ID)"),
    count: int = typer.Option(20, "--count", "-c", help="Number of messages (default 20)"),
) -> None:
    """Get recent messages from a channel."""
    def _history() -> dict[str, Any]:
        client = SlackClient()
        if channel.startswith("#"):
            ch = client.find_channel(channel)
            channel_id = ch["id"]
        elif channel[0] in ("C", "G") and len(channel) > 8:
            channel_id = channel
        else:
            ch = client.find_channel(channel)
            channel_id = ch["id"]
        return client.get_history(channel_id, limit=count)

    _run_command("history", _history)


@app.command("read-thread")
def read_thread(
    channel: str = typer.Argument(..., help="Channel (#name or ID)"),
    thread_ts: str = typer.Argument(..., help="Thread timestamp"),
) -> None:
    """Read replies in a thread."""
    def _read_thread() -> dict[str, Any]:
        client = SlackClient()
        if channel.startswith("#"):
            ch = client.find_channel(channel)
            channel_id = ch["id"]
        elif channel[0] in ("C", "G") and len(channel) > 8:
            channel_id = channel
        else:
            ch = client.find_channel(channel)
            channel_id = ch["id"]
        return client.get_thread(channel_id, thread_ts)

    _run_command("read-thread", _read_thread)


@app.command()
def channels(
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Filter channels by name",
    ),
) -> None:
    """List channels in the workspace."""
    def _channels() -> dict[str, Any]:
        client = SlackClient()
        results = client.list_channels(search=search)
        return {"channels": results, "count": len(results)}

    _run_command("channels", _channels)


@app.command()
def users(
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Filter users by name",
    ),
) -> None:
    """List workspace members."""
    def _users() -> dict[str, Any]:
        client = SlackClient()
        results = client.list_users(search=search)
        return {"users": results, "count": len(results)}

    _run_command("users", _users)


@app.command()
def delete(
    channel: str = typer.Argument(..., help="Channel ID"),
    ts: str = typer.Argument(..., help="Message timestamp"),
) -> None:
    """Delete a message."""
    def _delete() -> dict[str, Any]:
        client = SlackClient()
        return client.delete_message(channel, ts)

    _run_command("delete", _delete)


@app.command()
def react(
    channel: str = typer.Argument(..., help="Channel ID"),
    ts: str = typer.Argument(..., help="Message timestamp"),
    emoji: str = typer.Argument(..., help="Emoji name (e.g. thumbsup, eyes)"),
) -> None:
    """Add a reaction to a message."""
    def _react() -> dict[str, Any]:
        client = SlackClient()
        return client.add_reaction(channel, ts, emoji)

    _run_command("react", _react)


@app.command()
def edit(
    channel: str = typer.Argument(..., help="Channel ID"),
    ts: str = typer.Argument(..., help="Message timestamp"),
    text: str = typer.Argument(..., help="New message text"),
) -> None:
    """Edit a sent message (only your own)."""
    def _edit() -> dict[str, Any]:
        client = SlackClient()
        return client.edit_message(channel, ts, text)

    _run_command("edit", _edit)


def _parse_duration(duration: str) -> int:
    """Parse a duration string like '2h', '30m', '1h30m' into seconds from now."""
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?"
    match = re.fullmatch(pattern, duration.strip())
    if not match or not any(match.groups()):
        raise SlackError(
            code=ErrorCode.API_ERROR,
            message=f"Invalid duration format: '{duration}'",
            suggestions=["Use format like '2h', '30m', or '1h30m'"],
        )
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return int(time.time()) + (hours * 3600) + (minutes * 60)


@app.command()
def status(
    text: str = typer.Argument("", help="Status text (empty to clear)"),
    emoji: str = typer.Option("", "--emoji", "-e", help="Status emoji (e.g. laptop, coffee)"),
    expires: str = typer.Option("", "--expires", "-x", help="Auto-clear after duration (e.g. 2h, 30m, 1h30m)"),
) -> None:
    """Set or clear your Slack status."""
    def _status() -> dict[str, Any]:
        client = SlackClient()
        expiration = 0
        if expires:
            expiration = _parse_duration(expires)
        return client.set_status(text, emoji=emoji, expiration=expiration)

    _run_command("status", _status)


def _parse_time(time_str: str) -> int:
    """Parse a time string into a Unix timestamp.

    Supports:
    - Relative: 'in 2h', 'in 30m', 'in 1h30m', '2h', '30m'
    - Unix timestamp: '1751234567'
    """
    time_str = time_str.strip()

    # Strip leading "in " for relative times
    if time_str.lower().startswith("in "):
        time_str = time_str[3:]

    # Check if it's already a Unix timestamp
    if time_str.isdigit() and len(time_str) >= 10:
        return int(time_str)

    # Try relative duration
    return _parse_duration(time_str)


@app.command()
def schedule(
    target: str = typer.Argument(..., help="Channel (#name or ID) or person's name"),
    message: str = typer.Argument(..., help="Message text to send"),
    at: str = typer.Option(..., "--at", "-a", help="When to send (e.g. 'in 2h', 'in 30m', or Unix timestamp)"),
) -> None:
    """Schedule a message for later delivery."""
    def _schedule() -> dict[str, Any]:
        client = SlackClient()
        channel_id = client.resolve_target(target)
        post_at = _parse_time(at)
        return client.schedule_message(channel_id, message, post_at)

    _run_command("schedule", _schedule)


if __name__ == "__main__":
    app()
