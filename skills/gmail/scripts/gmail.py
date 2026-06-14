#!/usr/bin/env python3
# /// script
# dependencies = [
#     "typer",
#     "beautifulsoup4",
# ]
# ///
"""Gmail Read CLI - read-only Gmail source-material retrieval."""

from __future__ import annotations

import imaplib
import json
import os
import re
import ssl
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup
import typer


# ---------------------------------------------------------------------------
# Env file loading
# ---------------------------------------------------------------------------

_ENV_FILE_PATHS = [
    Path.home() / ".claude" / "gmail" / ".env",
    Path.cwd() / ".claude" / "gmail.env",
]


def _load_env_files() -> list[Path]:
    """Load skill-specific env files into os.environ. Later files override earlier files."""
    loaded: list[Path] = []
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
                    os.environ[key.strip()] = value
            loaded.append(p)
    return loaded


_LOADED_ENV_FILES = _load_env_files()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ErrorCode(str, Enum):
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    AUTH_FAILED = "AUTH_FAILED"
    NETWORK_ERROR = "NETWORK_ERROR"
    MAILBOX_NOT_FOUND = "MAILBOX_NOT_FOUND"
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    IMAP_ERROR = "IMAP_ERROR"
    PARSE_ERROR = "PARSE_ERROR"


class GmailError(Exception):
    def __init__(self, code: ErrorCode, message: str, suggestions: list[str] | None = None):
        self.code = code
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def output_success(command: str, result: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "command": command,
        "result": result,
        "metadata": metadata or {},
    }


def output_error(command: str, error: GmailError) -> dict[str, Any]:
    err: dict[str, Any] = {"code": error.code.value, "message": error.message}
    if error.suggestions:
        err["suggestions"] = error.suggestions
    return {"success": False, "command": command, "error": err}


def emit(data: dict[str, Any]) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Query composition
# ---------------------------------------------------------------------------


def _quote_gmail_value(value: str) -> str:
    value = value.strip()
    if any(ch.isspace() for ch in value) or '"' in value:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _format_gmail_date(value: str, flag: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y/%m/%d")
    except ValueError:
        raise GmailError(
            ErrorCode.INVALID_INPUT,
            f"Invalid {flag} date '{value}'. Expected YYYY-MM-DD.",
            suggestions=["Use a date like 2026-01-31"],
        )


def _parse_positive_int(value: str, flag: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise GmailError(
            ErrorCode.INVALID_INPUT,
            f"Invalid {flag} value '{value}'. Expected a positive integer.",
        )
    if parsed <= 0:
        raise GmailError(
            ErrorCode.INVALID_INPUT,
            f"Invalid {flag} value '{value}'. Expected a positive integer.",
        )
    return parsed


def build_gmail_query(
    *,
    raw_query: str | None = None,
    from_value: str | None = None,
    subject: str | None = None,
    text: str | None = None,
    label: str | None = None,
    after: str | None = None,
    before: str | None = None,
    include_sent: bool = False,
    include_spam_trash: bool = False,
) -> str:
    """Compose deterministic Gmail raw search syntax for the Public CLI Contract."""
    tokens: list[str] = []
    if raw_query and raw_query.strip():
        tokens.append(raw_query.strip())
    if from_value:
        tokens.append(f"from:{_quote_gmail_value(from_value)}")
    if subject:
        tokens.append(f"subject:{_quote_gmail_value(subject)}")
    if text:
        tokens.append(_quote_gmail_value(text))
    if label:
        tokens.append(f"label:{_quote_gmail_value(label)}")
    if after:
        tokens.append(f"after:{_format_gmail_date(after, '--after')}")
    if before:
        tokens.append(f"before:{_format_gmail_date(before, '--before')}")
    if not include_sent:
        tokens.append("-in:sent")
    if not include_spam_trash:
        tokens.extend(["-in:spam", "-in:trash"])
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Configuration and backend boundary
# ---------------------------------------------------------------------------


def _require_credentials() -> tuple[str, str]:
    user = os.environ.get("GMAIL_USER", "")
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not user or not password:
        raise GmailError(
            ErrorCode.MISSING_CREDENTIALS,
            "GMAIL_USER and GMAIL_APP_PASSWORD must be set for Gmail access.",
            suggestions=[
                "Add GMAIL_USER and GMAIL_APP_PASSWORD to ~/.claude/gmail/.env",
                "Or add them to ./.claude/gmail.env for this project",
                "Use a Gmail app password, not your normal account password",
            ],
        )
    return user, password


GMAIL_IMAP_HOST = "imap.gmail.com"
GMAIL_IMAP_PORT = 993


def _ok(status: Any) -> bool:
    if isinstance(status, bytes):
        status = status.decode("ascii", "ignore")
    return str(status).upper() == "OK"


def _decode_imap_text(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def _parse_mailbox_line(raw: bytes | str) -> dict[str, Any]:
    text = _decode_imap_text(raw)
    attrs_match = re.search(r"\((.*?)\)", text)
    attributes = attrs_match.group(1).split() if attrs_match else []
    quoted = re.findall(r'"((?:\\.|[^"])*)"', text)
    name = quoted[-1] if quoted else text.rsplit(" ", 1)[-1].strip('"')
    name = name.replace('\\"', '"').replace('\\\\', '\\')
    return {"name": name, "attributes": attributes}


def _normalize_label(label: str) -> str:
    label = label.strip().strip('"')
    if label.startswith("\\"):
        label = label[1:]
    return label


def _parse_labels_from_fetch(fetch_text: str) -> list[str]:
    match = re.search(r"X-GM-LABELS \((.*?)\)", fetch_text)
    if not match:
        return []
    raw_labels = match.group(1)
    labels = re.findall(r'"((?:\\.|[^"])*)"|(\\?[^\s]+)', raw_labels)
    normalized: list[str] = []
    for quoted, bare in labels:
        value = quoted or bare
        if value:
            normalized.append(_normalize_label(value))
    return normalized


def _extract_fetch_response(data: list[Any]) -> tuple[str, bytes]:
    for item in data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            prefix = _decode_imap_text(item[0])
            return prefix, item[1]
    raise GmailError(ErrorCode.PARSE_ERROR, "IMAP fetch response did not contain a message body.")


def _extract_fetch_id(fetch_text: str, attr: str) -> str | None:
    match = re.search(rf"{re.escape(attr)}\s+(\d+)", fetch_text)
    return match.group(1) if match else None


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _message_from_bytes(raw_message: bytes):
    try:
        return BytesParser(policy=policy.default).parsebytes(raw_message)
    except Exception as e:
        raise GmailError(ErrorCode.PARSE_ERROR, f"Could not parse email message: {e}")


def _part_text(part: Any) -> str:
    try:
        content = part.get_content()
        return content if isinstance(content, str) else str(content)
    except Exception:
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, "replace")


def extract_normalized_body(message: Any) -> str:
    """Return normalized plain text, preferring text/plain over HTML."""
    plain_parts: list[str] = []
    html_parts: list[str] = []

    candidates = message.walk() if message.is_multipart() else [message]
    for part in candidates:
        if part.is_multipart():
            continue
        if part.get_content_disposition() == "attachment" or part.get_filename():
            continue
        content_type = part.get_content_type()
        if content_type == "text/plain":
            plain_parts.append(_part_text(part))
        elif content_type == "text/html":
            html_parts.append(_part_text(part))

    if plain_parts:
        return normalize_whitespace("\n".join(plain_parts))
    if html_parts:
        html = "\n".join(html_parts)
        return normalize_whitespace(BeautifulSoup(html, "html.parser").get_text(" "))
    return ""


def _truncate_text(text: str, max_chars: int) -> dict[str, Any]:
    returned = text[:max_chars]
    return {
        "text": returned,
        "truncated": len(text) > max_chars,
        "max_chars": max_chars,
        "original_chars": len(text),
        "returned_chars": len(returned),
    }


def extract_attachment_metadata(message: Any) -> list[dict[str, Any]]:
    attachments: list[dict[str, Any]] = []
    candidates = message.walk() if message.is_multipart() else [message]
    for part in candidates:
        filename = part.get_filename()
        disposition = part.get_content_disposition()
        if disposition != "attachment" and not filename:
            continue
        item: dict[str, Any] = {
            "filename": filename,
            "content_type": part.get_content_type(),
        }
        content_length = part.get("Content-Length")
        if content_length and content_length.isdigit():
            item["size"] = int(content_length)
        else:
            payload = part.get_payload(decode=False)
            if isinstance(payload, str):
                item["size"] = len(payload.encode("utf-8", "replace"))
        attachments.append(item)
    return attachments


def _format_message_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return value


def _sender(value: str | None) -> dict[str, str]:
    name, address = parseaddr(value or "")
    return {"name": name, "email": address}


def _base_message_fields(message: Any, *, uid: bytes, fetch_text: str) -> dict[str, Any]:
    gmail_id = _extract_fetch_id(fetch_text, "X-GM-MSGID") or uid.decode("ascii", "ignore")
    thread_id = _extract_fetch_id(fetch_text, "X-GM-THRID") or gmail_id
    return {
        "id": gmail_id,
        "threadId": thread_id,
        "date": _format_message_date(message.get("Date")),
        "from": _sender(message.get("From")),
        "subject": message.get("Subject", ""),
        "labels": _parse_labels_from_fetch(fetch_text),
        "attachments": extract_attachment_metadata(message),
    }


def _message_metadata(
    raw_message: bytes,
    *,
    uid: bytes,
    fetch_text: str,
    snippet_chars: int,
) -> dict[str, Any]:
    message = _message_from_bytes(raw_message)
    body = extract_normalized_body(message)
    snippet = _truncate_text(body, snippet_chars)
    return {
        **_base_message_fields(message, uid=uid, fetch_text=fetch_text),
        "snippet": snippet["text"],
        "snippet_truncated": snippet["truncated"],
    }


def _message_body_result(
    raw_message: bytes,
    *,
    uid: bytes,
    fetch_text: str,
    max_chars: int,
) -> dict[str, Any]:
    message = _message_from_bytes(raw_message)
    body = extract_normalized_body(message)
    return {
        **_base_message_fields(message, uid=uid, fetch_text=fetch_text),
        "body": _truncate_text(body, max_chars),
    }


def _message_direction(message: dict[str, Any], user: str) -> str:
    labels = {str(label).lower() for label in message.get("labels", [])}
    sender = message.get("from", {}).get("email", "").lower()
    if "sent" in labels or sender == user.lower():
        return "sent"
    return "received"


class GmailBackend:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        self._imap: Any | None = None

    def _connect(self) -> Any:
        if self._imap is not None:
            return self._imap
        try:
            self._imap = imaplib.IMAP4_SSL(
                GMAIL_IMAP_HOST,
                GMAIL_IMAP_PORT,
                ssl_context=ssl.create_default_context(),
            )
            self._imap.login(self.user, self.password)
            return self._imap
        except imaplib.IMAP4.error as e:
            raise GmailError(
                ErrorCode.AUTH_FAILED,
                "Gmail rejected the configured credentials.",
                suggestions=[
                    "Check GMAIL_USER",
                    "Create a fresh Gmail app password and update GMAIL_APP_PASSWORD",
                ],
            ) from e
        except OSError as e:
            raise GmailError(
                ErrorCode.NETWORK_ERROR,
                f"Could not connect to Gmail IMAP: {e}",
                suggestions=["Check your network connection", "Try again in a moment"],
            ) from e

    def _close(self) -> None:
        if self._imap is None:
            return
        try:
            self._imap.logout()
        except Exception:
            pass
        finally:
            self._imap = None

    def _labels_connected(self) -> list[dict[str, Any]]:
        imap = self._connect()
        status, data = imap.list()
        if not _ok(status):
            raise GmailError(ErrorCode.IMAP_ERROR, "Could not list Gmail mailboxes/labels.")
        return [_parse_mailbox_line(item) for item in data or [] if item]

    def _select_mailbox(self, mailbox: str) -> tuple[str, str]:
        mailbox_key = mailbox.lower()
        if mailbox_key not in {"all", "inbox"}:
            raise GmailError(
                ErrorCode.INVALID_INPUT,
                f"Invalid --mailbox value '{mailbox}'. Expected 'all' or 'inbox'.",
            )

        resolved_key = "inbox"
        resolved_name = "INBOX"
        if mailbox_key == "all":
            labels = self._labels_connected()
            all_mail = next(
                (label for label in labels if "\\All" in label.get("attributes", [])),
                None,
            )
            if all_mail:
                resolved_key = "all"
                resolved_name = all_mail["name"]
        status, _ = self._connect().select(resolved_name, readonly=True)
        if not _ok(status):
            raise GmailError(
                ErrorCode.MAILBOX_NOT_FOUND,
                f"Could not open Gmail mailbox '{resolved_name}' read-only.",
            )
        return resolved_key, resolved_name

    def _search_uids(self, query: str) -> list[bytes]:
        return self._search_uids_by("X-GM-RAW", query)

    def _search_uids_by(self, key: str, value: str) -> list[bytes]:
        status, data = self._connect().uid("SEARCH", None, key, value)
        if not _ok(status):
            raise GmailError(ErrorCode.IMAP_ERROR, "Gmail IMAP search failed.")
        raw = data[0] if data else b""
        if isinstance(raw, str):
            raw = raw.encode()
        return raw.split()

    def _fetch_message(self, uid: bytes) -> tuple[str, bytes]:
        status, data = self._connect().uid(
            "FETCH",
            uid,
            "(X-GM-MSGID X-GM-THRID X-GM-LABELS BODY.PEEK[])",
        )
        if not _ok(status):
            raise GmailError(ErrorCode.IMAP_ERROR, f"Could not fetch Gmail message UID {uid!r}.")
        return _extract_fetch_response(data or [])

    def doctor(self) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            resolved_key, resolved_name = self._select_mailbox("all")
            return (
                {
                    "status": "ok",
                    "authenticated": True,
                    "mailbox": {"scope": resolved_key, "name": resolved_name},
                },
                {
                    "backend": "imap",
                    "mailbox": resolved_key,
                    "resolved_mailbox": resolved_name,
                    "readonly": True,
                },
            )
        finally:
            self._close()

    def labels(self) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            return (
                {"labels": self._labels_connected()},
                {"backend": "imap", "readonly": True},
            )
        finally:
            self._close()

    def search(self, **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        query = str(kwargs.get("query", ""))
        mailbox = str(kwargs.get("mailbox", "all"))
        limit = int(kwargs.get("limit", 20))
        snippet_chars = int(kwargs.get("snippet_chars", 500))
        try:
            resolved_key, resolved_name = self._select_mailbox(mailbox)
            uids = self._search_uids(query)
            selected_uids = list(reversed(uids))[:limit]
            messages: list[dict[str, Any]] = []
            for uid in selected_uids:
                fetch_text, raw_message = self._fetch_message(uid)
                messages.append(
                    _message_metadata(
                        raw_message,
                        uid=uid,
                        fetch_text=fetch_text,
                        snippet_chars=snippet_chars,
                    )
                )
            return (
                {
                    "query": query,
                    "messages": messages,
                    "count": len(messages),
                    "truncated": len(uids) > limit,
                },
                {
                    "backend": "imap",
                    "mailbox": resolved_key,
                    "resolved_mailbox": resolved_name,
                    "readonly": True,
                },
            )
        finally:
            self._close()

    def get_message(self, message_id: str, max_chars: int) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            resolved_key, resolved_name = self._select_mailbox("all")
            uids = self._search_uids_by("X-GM-MSGID", message_id)
            if not uids and message_id.isdigit():
                uids = [message_id.encode("ascii")]
            if not uids:
                raise GmailError(
                    ErrorCode.MESSAGE_NOT_FOUND,
                    f"No Gmail message found for id '{message_id}'.",
                )
            uid = uids[-1]
            fetch_text, raw_message = self._fetch_message(uid)
            return (
                {"message": _message_body_result(raw_message, uid=uid, fetch_text=fetch_text, max_chars=max_chars)},
                {
                    "backend": "imap",
                    "mailbox": resolved_key,
                    "resolved_mailbox": resolved_name,
                    "readonly": True,
                },
            )
        finally:
            self._close()

    def get_thread(
        self,
        thread_id: str,
        max_messages: int,
        max_chars_per_message: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            resolved_key, resolved_name = self._select_mailbox("all")
            uids = self._search_uids_by("X-GM-THRID", thread_id)
            if not uids:
                raise GmailError(
                    ErrorCode.MESSAGE_NOT_FOUND,
                    f"No Gmail thread found for id '{thread_id}'.",
                )
            messages: list[dict[str, Any]] = []
            for uid in uids[:max_messages]:
                fetch_text, raw_message = self._fetch_message(uid)
                message = _message_body_result(
                    raw_message,
                    uid=uid,
                    fetch_text=fetch_text,
                    max_chars=max_chars_per_message,
                )
                message["direction"] = _message_direction(message, self.user)
                messages.append(message)
            return (
                {
                    "threadId": thread_id,
                    "messages": messages,
                    "count": len(messages),
                    "truncated": len(uids) > max_messages,
                },
                {
                    "backend": "imap",
                    "mailbox": resolved_key,
                    "resolved_mailbox": resolved_name,
                    "readonly": True,
                },
            )
        finally:
            self._close()


def _run_backend_command(command: str, action: str, *args: Any, **kwargs: Any) -> None:
    try:
        user, password = _require_credentials()
        backend = GmailBackend(user, password)
        result, metadata = getattr(backend, action)(*args, **kwargs)
        emit(output_success(command, result, metadata))
    except GmailError as e:
        emit(output_error(command, e))
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="gmail",
    help="Read-only Gmail source-material retrieval for agents.",
    add_completion=False,
)


@app.command()
def config() -> None:
    """Show resolved Gmail configuration without printing secret values."""
    emit(
        output_success(
            "config",
            {
                "env_files": [
                    {"path": str(p), "loaded": p in _LOADED_ENV_FILES}
                    for p in _ENV_FILE_PATHS
                ],
                "credentials": {
                    "gmail_user_present": bool(os.environ.get("GMAIL_USER")),
                    "gmail_app_password_present": bool(os.environ.get("GMAIL_APP_PASSWORD")),
                },
            },
            {"network": False},
        )
    )


@app.command()
def doctor() -> None:
    """Check read-only Gmail connectivity."""
    _run_backend_command("doctor", "doctor")


@app.command()
def search(
    from_value: Optional[str] = typer.Option(None, "--from", help="Sender, domain, or sender text"),
    after: Optional[str] = typer.Option(None, "--after", help="Start date, YYYY-MM-DD"),
    before: Optional[str] = typer.Option(None, "--before", help="End date, YYYY-MM-DD"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Subject text"),
    text: Optional[str] = typer.Option(None, "--text", help="Body/topic text"),
    query: Optional[str] = typer.Option(None, "--query", help="Raw Gmail search query"),
    label: Optional[str] = typer.Option(None, "--label", help="Gmail label"),
    mailbox: str = typer.Option("all", "--mailbox", help="Mailbox scope: all or inbox"),
    limit: str = typer.Option("20", "--limit", help="Maximum results"),
    snippet_chars: str = typer.Option("500", "--snippet-chars", help="Maximum snippet characters"),
    include_sent: bool = typer.Option(False, "--include-sent", help="Include sent mail in discovery search"),
    include_spam_trash: bool = typer.Option(False, "--include-spam-trash", help="Include spam/trash"),
) -> None:
    """Search Gmail messages."""
    try:
        gmail_query = build_gmail_query(
            raw_query=query,
            from_value=from_value,
            subject=subject,
            text=text,
            label=label,
            after=after,
            before=before,
            include_sent=include_sent,
            include_spam_trash=include_spam_trash,
        )
        limit_value = _parse_positive_int(limit, "--limit")
        snippet_chars_value = _parse_positive_int(snippet_chars, "--snippet-chars")
    except GmailError as e:
        emit(output_error("search", e))
        raise typer.Exit(code=1)
    _run_backend_command(
        "search",
        "search",
        query=gmail_query,
        from_value=from_value,
        after=after,
        before=before,
        subject=subject,
        text=text,
        label=label,
        mailbox=mailbox,
        limit=limit_value,
        snippet_chars=snippet_chars_value,
        include_sent=include_sent,
        include_spam_trash=include_spam_trash,
    )


@app.command()
def get(
    message_id: str,
    max_chars: str = typer.Option("8000", "--max-chars", help="Maximum body characters"),
) -> None:
    """Read one selected Gmail message."""
    try:
        max_chars_value = _parse_positive_int(max_chars, "--max-chars")
    except GmailError as e:
        emit(output_error("get", e))
        raise typer.Exit(code=1)
    _run_backend_command("get", "get_message", message_id, max_chars_value)


@app.command()
def thread(
    thread_id: str,
    max_messages: str = typer.Option("10", "--max-messages", help="Maximum messages to return"),
    max_chars_per_message: str = typer.Option(
        "6000", "--max-chars-per-message", help="Maximum body characters per message"
    ),
) -> None:
    """Read one selected Gmail thread."""
    try:
        max_messages_value = _parse_positive_int(max_messages, "--max-messages")
        max_chars_value = _parse_positive_int(max_chars_per_message, "--max-chars-per-message")
    except GmailError as e:
        emit(output_error("thread", e))
        raise typer.Exit(code=1)
    _run_backend_command(
        "thread",
        "get_thread",
        thread_id,
        max_messages_value,
        max_chars_value,
    )


@app.command()
def labels() -> None:
    """List Gmail labels/mailboxes."""
    _run_backend_command("labels", "labels")


if __name__ == "__main__":
    app()
