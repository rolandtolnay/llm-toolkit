#!/usr/bin/env python3
# /// script
# dependencies = [
#     "typer",
#     "beautifulsoup4",
# ]
# ///
"""Gmail Read CLI - read-only Gmail source-material retrieval."""

from __future__ import annotations

import base64
import imaplib
import json
import os
import quopri
import re
import shlex
import ssl
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from bs4 import BeautifulSoup
import typer


# ---------------------------------------------------------------------------
# Env file loading
# ---------------------------------------------------------------------------

_GMAIL_ENV_KEYS = ("GMAIL_USER", "GMAIL_APP_PASSWORD")
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class EnvSourceStatus:
    kind: str
    loaded: bool
    path: str | None = None
    skipped: bool = False
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind, "loaded": self.loaded}
        if self.path is not None:
            data["path"] = self.path
        if self.skipped:
            data["skipped"] = True
        if self.reason:
            data["reason"] = self.reason
        return data


@dataclass
class GmailConfig:
    user: str
    app_password: str
    sources: list[EnvSourceStatus]


def _env_file_paths() -> list[tuple[str, Path]]:
    return [
        ("project_env_file", Path.cwd() / ".claude" / "gmail.env"),
        ("user_env_file", Path.home() / ".claude" / "gmail" / ".env"),
    ]


def _agents_env_json_paths() -> list[Path]:
    """Return candidate Pi/Agents env.json locations without reading protected contents."""
    paths: list[Path] = []
    configured = os.environ.get("AGENTS_ENV_JSON")
    if configured:
        paths.append(Path(configured).expanduser())
    paths.extend(
        [
            Path.home() / ".config" / "agents" / "env.json",
            Path.home() / ".agents" / "env.json",
            Path.home() / ".pi" / "agents" / "env.json",
            Path.home() / ".pi" / "agent" / "agents" / "env.json",
        ]
    )
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key = key.strip()
        if key and sep and _ENV_NAME_RE.match(key):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            values[key] = value
    return values


def _coerce_env_json_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict) and isinstance(value.get("value"), str):
        return value["value"]
    return None


def _extract_env_json_values(data: Any) -> dict[str, str]:
    if not isinstance(data, dict):
        return {}

    raw_values: dict[str, Any] = {}
    raw_values.update(data)
    for key in ("env", "environment", "environmentVariables"):
        nested = data.get(key)
        if isinstance(nested, dict):
            raw_values.update(nested)

    values: dict[str, str] = {}
    for key, value in raw_values.items():
        if not isinstance(key, str) or key not in _GMAIL_ENV_KEYS:
            continue
        coerced = _coerce_env_json_value(value)
        if coerced is not None:
            values[key] = coerced
    return values


def _missing_keys(values: dict[str, str]) -> set[str]:
    return {key for key in _GMAIL_ENV_KEYS if not values.get(key)}


def _fill_missing_credentials(target: dict[str, str], values: dict[str, str]) -> None:
    for key in _GMAIL_ENV_KEYS:
        value = values.get(key)
        if value and not target.get(key):
            target[key] = value


def _login_shell_commands() -> list[list[str]]:
    shells: list[str] = []
    configured_shell = os.environ.get("SHELL")
    if configured_shell:
        shells.append(configured_shell)
    shells.extend(["/bin/zsh", "/bin/bash", "/bin/sh"])

    python = shlex.quote(sys.executable)
    code = (
        "import json, os; "
        "print('__GMAIL_ENV_JSON_START__'); "
        "print(json.dumps(dict(os.environ))); "
        "print('__GMAIL_ENV_JSON_END__')"
    )
    commands: list[list[str]] = []
    seen: set[str] = set()
    for shell in shells:
        if shell in seen or not Path(shell).exists():
            continue
        seen.add(shell)
        shell_name = Path(shell).name
        flags = "-lic" if shell_name in {"bash", "zsh"} else "-lc"
        commands.append([shell, flags, f"{python} -c {shlex.quote(code)}"])
    return commands


def _read_login_shell_environment(missing_keys: set[str]) -> dict[str, str]:
    env = dict(os.environ)
    for command in _login_shell_commands():
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                env=env,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue

        start = result.stdout.find("__GMAIL_ENV_JSON_START__")
        end = result.stdout.find("__GMAIL_ENV_JSON_END__", start)
        if start == -1 or end == -1:
            continue
        payload = result.stdout[start + len("__GMAIL_ENV_JSON_START__") : end].strip()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        values = {
            key: value
            for key, value in data.items()
            if key in missing_keys and isinstance(value, str) and value
        }
        if values:
            return values
    return {}


def _resolve_gmail_config(*, load_shell_env: bool = False) -> GmailConfig:
    values = {key: os.environ.get(key, "") for key in _GMAIL_ENV_KEYS}
    sources = [
        EnvSourceStatus(
            "process_env",
            loaded=any(values.values()),
            reason="highest priority when set",
        )
    ]

    for kind, path in _env_file_paths():
        loaded = False
        if path.is_file():
            try:
                file_values = _parse_env_file(path)
            except OSError:
                file_values = {}
            else:
                loaded = True
                _fill_missing_credentials(values, file_values)
        sources.append(EnvSourceStatus(kind, loaded=loaded, path=str(path)))

    for path in _agents_env_json_paths():
        loaded = False
        if path.is_file():
            try:
                json_values = _extract_env_json_values(json.loads(path.read_text()))
            except (OSError, json.JSONDecodeError):
                json_values = {}
            else:
                loaded = True
                _fill_missing_credentials(values, json_values)
        sources.append(EnvSourceStatus("agents_env_json", loaded=loaded, path=str(path)))

    missing = _missing_keys(values)
    if load_shell_env and missing:
        shell_values = _read_login_shell_environment(missing)
        _fill_missing_credentials(values, shell_values)
        sources.append(EnvSourceStatus("login_shell_env", loaded=bool(shell_values)))
    else:
        reason = "not requested" if not load_shell_env else "credentials already present"
        sources.append(EnvSourceStatus("login_shell_env", loaded=False, skipped=True, reason=reason))

    return GmailConfig(
        user=values.get("GMAIL_USER", ""),
        app_password=values.get("GMAIL_APP_PASSWORD", ""),
        sources=sources,
    )


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


def _require_credentials(*, load_shell_env: bool = False) -> tuple[str, str]:
    config = _resolve_gmail_config(load_shell_env=load_shell_env)
    if not config.user or not config.app_password:
        raise GmailError(
            ErrorCode.MISSING_CREDENTIALS,
            "GMAIL_USER and GMAIL_APP_PASSWORD must be set for Gmail access.",
            suggestions=[
                "Export GMAIL_USER and GMAIL_APP_PASSWORD in the process environment",
                "Or add them to ~/.claude/gmail/.env or ./.claude/gmail.env",
                "Or add them to an agents/env.json source such as ~/.config/agents/env.json",
                "If they are exported only from shell startup files, rerun with --load-shell-env",
                "Use a Gmail app password, not your normal account password",
            ],
        )
    return config.user, config.app_password


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


def _imap_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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


def _normalize_body_parts(plain_parts: list[str], html_parts: list[str]) -> str:
    if plain_parts:
        return normalize_whitespace("\n".join(plain_parts))
    if html_parts:
        html = "\n".join(html_parts)
        return normalize_whitespace(BeautifulSoup(html, "html.parser").get_text(" "))
    return ""


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

    return _normalize_body_parts(plain_parts, html_parts)


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


@dataclass
class BodyPartSpec:
    number: str
    content_type: str
    encoding: str
    charset: str | None = None
    filename: str | None = None
    disposition: str | None = None
    size: int | None = None


@dataclass
class FetchedMessage:
    uid: bytes
    fetch_text: str
    headers: Any
    plain_parts: list[str]
    html_parts: list[str]
    attachments: list[dict[str, Any]]


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


def _tokenize_bodystructure(value: str) -> list[Any]:
    tokens: list[Any] = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            out: list[str] = []
            while i < len(value):
                ch = value[i]
                if ch == "\\" and i + 1 < len(value):
                    out.append(value[i + 1])
                    i += 2
                    continue
                if ch == '"':
                    i += 1
                    break
                out.append(ch)
                i += 1
            tokens.append("".join(out))
            continue
        start = i
        while i < len(value) and not value[i].isspace() and value[i] not in "()":
            i += 1
        atom = value[start:i]
        if atom.upper() == "NIL":
            tokens.append(None)
        elif re.fullmatch(r"\d+", atom):
            tokens.append(int(atom))
        else:
            tokens.append(atom)
    return tokens


def _parse_bodystructure_tokens(tokens: list[Any], pos: int = 0) -> tuple[Any, int]:
    if pos >= len(tokens):
        raise GmailError(ErrorCode.PARSE_ERROR, "Unexpected end of BODYSTRUCTURE response.")
    token = tokens[pos]
    if token == "(":
        pos += 1
        items: list[Any] = []
        while pos < len(tokens) and tokens[pos] != ")":
            item, pos = _parse_bodystructure_tokens(tokens, pos)
            items.append(item)
        if pos >= len(tokens):
            raise GmailError(ErrorCode.PARSE_ERROR, "Unclosed BODYSTRUCTURE list.")
        return items, pos + 1
    if token == ")":
        raise GmailError(ErrorCode.PARSE_ERROR, "Unexpected BODYSTRUCTURE close paren.")
    return token, pos + 1


def _extract_parenthesized(value: str, start: int) -> str:
    depth = 0
    in_quote = False
    escaped = False
    for i in range(start, len(value)):
        ch = value[i]
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_quote:
            escaped = True
            continue
        if ch == '"':
            in_quote = not in_quote
            continue
        if in_quote:
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return value[start : i + 1]
    raise GmailError(ErrorCode.PARSE_ERROR, "Could not parse BODYSTRUCTURE response.")


def _bodystructure_from_fetch(fetch_text: str) -> Any:
    marker = fetch_text.upper().find("BODYSTRUCTURE")
    if marker == -1:
        raise GmailError(ErrorCode.PARSE_ERROR, "IMAP fetch response did not include BODYSTRUCTURE.")
    start = fetch_text.find("(", marker)
    if start == -1:
        raise GmailError(ErrorCode.PARSE_ERROR, "IMAP BODYSTRUCTURE response was malformed.")
    bodystructure_text = _extract_parenthesized(fetch_text, start)
    parsed, _ = _parse_bodystructure_tokens(_tokenize_bodystructure(bodystructure_text))
    return parsed


def _params_to_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, list):
        return {}
    params: dict[str, str] = {}
    for i in range(0, len(value) - 1, 2):
        key = value[i]
        val = value[i + 1]
        if isinstance(key, str) and val is not None:
            params[key.upper()] = str(val)
    return params


def _disposition_from_node(node: list[Any]) -> tuple[str | None, dict[str, str]]:
    for item in node[7:]:
        if (
            isinstance(item, list)
            and item
            and isinstance(item[0], str)
            and item[0].upper() in {"ATTACHMENT", "INLINE"}
        ):
            return item[0].lower(), _params_to_dict(item[1] if len(item) > 1 else None)
    return None, {}


def _body_part_specs(node: Any, prefix: str = "") -> list[BodyPartSpec]:
    if not isinstance(node, list) or not node:
        return []
    if isinstance(node[0], list):
        specs: list[BodyPartSpec] = []
        part_index = 1
        for child in node:
            if not isinstance(child, list):
                break
            number = f"{prefix}.{part_index}" if prefix else str(part_index)
            specs.extend(_body_part_specs(child, number))
            part_index += 1
        return specs

    if len(node) < 7 or not isinstance(node[0], str) or not isinstance(node[1], str):
        return []
    params = _params_to_dict(node[2])
    disposition, disposition_params = _disposition_from_node(node)
    filename = disposition_params.get("FILENAME") or params.get("NAME")
    size = node[6] if isinstance(node[6], int) else None
    return [
        BodyPartSpec(
            number=prefix or "1",
            content_type=f"{node[0].lower()}/{node[1].lower()}",
            encoding=str(node[5] or "7BIT"),
            charset=params.get("CHARSET"),
            filename=filename,
            disposition=disposition,
            size=size,
        )
    ]


def _attachment_from_part(part: BodyPartSpec) -> dict[str, Any]:
    attachment: dict[str, Any] = {
        "filename": part.filename,
        "content_type": part.content_type,
    }
    if part.size is not None:
        attachment["size"] = part.size
    return attachment


def _is_attachment_part(part: BodyPartSpec) -> bool:
    return part.disposition == "attachment" or bool(part.filename)


def _decode_body_payload(payload: bytes, part: BodyPartSpec) -> str:
    encoding = part.encoding.upper()
    data = payload
    if encoding == "BASE64":
        try:
            data = base64.b64decode(payload, validate=False)
        except Exception:
            data = payload
    elif encoding in {"QUOTED-PRINTABLE", "QUOTEDPRINTABLE"}:
        data = quopri.decodestring(payload)
    return data.decode(part.charset or "utf-8", "replace")


def _message_public_id(fetch_text: str, uid: bytes) -> tuple[str, str]:
    gmail_id = _extract_fetch_id(fetch_text, "X-GM-MSGID")
    if gmail_id:
        return gmail_id, "gmail"
    return f"imap-uid:{uid.decode('ascii', 'ignore')}", "imap-uid"


def _base_message_fields(fetched: FetchedMessage) -> dict[str, Any]:
    message_id, id_source = _message_public_id(fetched.fetch_text, fetched.uid)
    thread_id = _extract_fetch_id(fetched.fetch_text, "X-GM-THRID") or message_id
    return {
        "id": message_id,
        "idSource": id_source,
        "threadId": thread_id,
        "date": _format_message_date(fetched.headers.get("Date")),
        "from": _sender(fetched.headers.get("From")),
        "subject": fetched.headers.get("Subject", ""),
        "labels": _parse_labels_from_fetch(fetched.fetch_text),
        "attachments": fetched.attachments,
    }


def _message_metadata(fetched: FetchedMessage, *, snippet_chars: int) -> dict[str, Any]:
    body = _normalize_body_parts(fetched.plain_parts, fetched.html_parts)
    snippet = _truncate_text(body, snippet_chars)
    return {
        **_base_message_fields(fetched),
        "snippet": snippet["text"],
        "snippet_truncated": snippet["truncated"],
    }


def _message_body_result(fetched: FetchedMessage, *, max_chars: int) -> dict[str, Any]:
    body = _normalize_body_parts(fetched.plain_parts, fetched.html_parts)
    return {
        **_base_message_fields(fetched),
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
        status, _ = self._connect().select(_imap_quote(resolved_name), readonly=True)
        if not _ok(status):
            raise GmailError(
                ErrorCode.MAILBOX_NOT_FOUND,
                f"Could not open Gmail mailbox '{resolved_name}' read-only.",
            )
        return resolved_key, resolved_name

    def _search_uids(self, query: str) -> list[bytes]:
        return self._search_uids_by("X-GM-RAW", query)

    def _search_uids_by(self, key: str, value: str) -> list[bytes]:
        search_value = _imap_quote(value) if key == "X-GM-RAW" else value
        status, data = self._connect().uid("SEARCH", None, key, search_value)
        if not _ok(status):
            raise GmailError(ErrorCode.IMAP_ERROR, "Gmail IMAP search failed.")
        raw = data[0] if data else b""
        if isinstance(raw, str):
            raw = raw.encode()
        return raw.split()

    def _fetch_body_part(self, uid: bytes, part: BodyPartSpec) -> bytes:
        status, data = self._connect().uid("FETCH", uid, f"(BODY.PEEK[{part.number}])")
        if not _ok(status):
            raise GmailError(
                ErrorCode.IMAP_ERROR,
                f"Could not fetch Gmail message UID {uid!r} body part {part.number}.",
            )
        _, payload = _extract_fetch_response(data or [])
        return payload

    def _fetch_message(self, uid: bytes) -> FetchedMessage:
        status, data = self._connect().uid(
            "FETCH",
            uid,
            "(X-GM-MSGID X-GM-THRID X-GM-LABELS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])",
        )
        if not _ok(status):
            raise GmailError(ErrorCode.IMAP_ERROR, f"Could not fetch Gmail message UID {uid!r}.")
        fetch_text, header_bytes = _extract_fetch_response(data or [])
        headers = _message_from_bytes(header_bytes)
        parts = _body_part_specs(_bodystructure_from_fetch(fetch_text))
        attachments = [_attachment_from_part(part) for part in parts if _is_attachment_part(part)]
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in parts:
            if _is_attachment_part(part):
                continue
            if part.content_type not in {"text/plain", "text/html"}:
                continue
            payload = self._fetch_body_part(uid, part)
            text = _decode_body_payload(payload, part)
            if part.content_type == "text/plain":
                plain_parts.append(text)
            else:
                html_parts.append(text)
        return FetchedMessage(
            uid=uid,
            fetch_text=fetch_text,
            headers=headers,
            plain_parts=plain_parts,
            html_parts=html_parts,
            attachments=attachments,
        )

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

    def search(
        self,
        *,
        query: str,
        mailbox: str = "all",
        limit: int = 20,
        snippet_chars: int = 500,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            resolved_key, resolved_name = self._select_mailbox(mailbox)
            uids = self._search_uids(query)
            selected_uids = list(reversed(uids))[:limit]
            messages: list[dict[str, Any]] = []
            for uid in selected_uids:
                messages.append(
                    _message_metadata(
                        self._fetch_message(uid),
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
            if message_id.startswith("imap-uid:"):
                fallback_uid = message_id.removeprefix("imap-uid:")
                if not fallback_uid.isdigit():
                    raise GmailError(
                        ErrorCode.INVALID_INPUT,
                        "Invalid imap-uid fallback identifier.",
                        suggestions=["Use the exact id returned by search"],
                    )
                uids = [fallback_uid.encode("ascii")]
            else:
                uids = self._search_uids_by("X-GM-MSGID", message_id)
            if not uids:
                raise GmailError(
                    ErrorCode.MESSAGE_NOT_FOUND,
                    f"No Gmail message found for id '{message_id}'.",
                )
            uid = uids[-1]
            return (
                {"message": _message_body_result(self._fetch_message(uid), max_chars=max_chars)},
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
                message = _message_body_result(
                    self._fetch_message(uid),
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


def _run_backend_command(
    command: str,
    action: Callable[[GmailBackend], tuple[dict[str, Any], dict[str, Any]]],
    *,
    load_shell_env: bool = False,
) -> None:
    try:
        user, password = _require_credentials(load_shell_env=load_shell_env)
        result, metadata = action(GmailBackend(user, password))
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
def config(
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
    ),
) -> None:
    """Show resolved Gmail configuration without printing secret values."""
    resolved = _resolve_gmail_config(load_shell_env=load_shell_env)
    emit(
        output_success(
            "config",
            {
                "credential_sources": [source.to_dict() for source in resolved.sources],
                "credentials": {
                    "gmail_user_present": bool(resolved.user),
                    "gmail_app_password_present": bool(resolved.app_password),
                },
            },
            {"network": False},
        )
    )


@app.command()
def doctor(
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
    ),
) -> None:
    """Check read-only Gmail connectivity."""
    _run_backend_command("doctor", lambda backend: backend.doctor(), load_shell_env=load_shell_env)


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
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
    ),
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
        lambda backend: backend.search(
            query=gmail_query,
            mailbox=mailbox,
            limit=limit_value,
            snippet_chars=snippet_chars_value,
        ),
        load_shell_env=load_shell_env,
    )


@app.command()
def get(
    message_id: str,
    max_chars: str = typer.Option("8000", "--max-chars", help="Maximum body characters"),
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
    ),
) -> None:
    """Read one selected Gmail message."""
    try:
        max_chars_value = _parse_positive_int(max_chars, "--max-chars")
    except GmailError as e:
        emit(output_error("get", e))
        raise typer.Exit(code=1)
    _run_backend_command(
        "get",
        lambda backend: backend.get_message(message_id, max_chars_value),
        load_shell_env=load_shell_env,
    )


@app.command()
def thread(
    thread_id: str,
    max_messages: str = typer.Option("10", "--max-messages", help="Maximum messages to return"),
    max_chars_per_message: str = typer.Option(
        "6000", "--max-chars-per-message", help="Maximum body characters per message"
    ),
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
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
        lambda backend: backend.get_thread(thread_id, max_messages_value, max_chars_value),
        load_shell_env=load_shell_env,
    )


@app.command()
def labels(
    load_shell_env: bool = typer.Option(
        False,
        "--load-shell-env",
        help="Opt in to reading exported Gmail credentials from a login shell.",
    ),
) -> None:
    """List Gmail labels/mailboxes."""
    _run_backend_command("labels", lambda backend: backend.labels(), load_shell_env=load_shell_env)


if __name__ == "__main__":
    app()
