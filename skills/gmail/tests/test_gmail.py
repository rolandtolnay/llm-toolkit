import importlib.util
import json
import sys
from email.message import EmailMessage
from pathlib import Path

import pytest
from typer.testing import CliRunner


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gmail.py"


def load_gmail_module():
    spec = importlib.util.spec_from_file_location("gmail_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_config_reports_credential_sources_and_masks_credentials(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    user_env_dir = home / ".claude" / "gmail"
    project_env_dir = project / ".claude"
    user_env_dir.mkdir(parents=True)
    project_env_dir.mkdir(parents=True)
    (user_env_dir / ".env").write_text(
        "GMAIL_USER=user-file@example.com\nGMAIL_APP_PASSWORD=user-file-secret\n"
    )
    (project_env_dir / "gmail.env").write_text(
        "GMAIL_USER=project-file@example.com\nGMAIL_APP_PASSWORD=project-file-secret\n"
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()

    result = CliRunner().invoke(module.app, ["config"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["command"] == "config"
    assert data["result"]["credentials"] == {
        "gmail_user_present": True,
        "gmail_app_password_present": True,
    }
    assert {"kind": "project_env_file", "loaded": True, "path": str(project_env_dir / "gmail.env")} in data[
        "result"
    ]["credential_sources"]
    assert {"kind": "user_env_file", "loaded": True, "path": str(user_env_dir / ".env")} in data["result"][
        "credential_sources"
    ]
    assert "project-file-secret" not in result.stdout
    assert "user-file-secret" not in result.stdout
    assert "project-file@example.com" not in result.stdout
    assert "user-file@example.com" not in result.stdout


def test_process_env_wins_over_config_files(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project_env_dir = project / ".claude"
    project_env_dir.mkdir(parents=True)
    (project_env_dir / "gmail.env").write_text(
        "GMAIL_USER=file@example.com\nGMAIL_APP_PASSWORD=file-secret\n"
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GMAIL_USER", "env@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "env-secret")
    module = load_gmail_module()
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            seen["user"] = user
            seen["password"] = password

        def labels(self):
            return ({"labels": []}, {"backend": "imap", "readonly": True})

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["labels"])

    assert result.exit_code == 0
    assert seen == {"user": "env@example.com", "password": "env-secret"}
    assert "file-secret" not in result.stdout


def test_project_env_file_wins_over_user_env_file(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    user_env_dir = home / ".claude" / "gmail"
    project_env_dir = project / ".claude"
    user_env_dir.mkdir(parents=True)
    project_env_dir.mkdir(parents=True)
    (user_env_dir / ".env").write_text(
        "GMAIL_USER=user-file@example.com\nGMAIL_APP_PASSWORD=user-file-secret\n"
    )
    (project_env_dir / "gmail.env").write_text(
        "GMAIL_USER=project-file@example.com\nGMAIL_APP_PASSWORD=project-file-secret\n"
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            seen["user"] = user
            seen["password"] = password

        def labels(self):
            return ({"labels": []}, {"backend": "imap", "readonly": True})

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["labels"])

    assert result.exit_code == 0
    assert seen == {"user": "project-file@example.com", "password": "project-file-secret"}
    assert "user-file-secret" not in result.stdout


def test_user_env_file_wins_over_agents_env_json(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    user_env_dir = home / ".claude" / "gmail"
    agents_dir = home / ".config" / "agents"
    user_env_dir.mkdir(parents=True)
    agents_dir.mkdir(parents=True)
    project.mkdir()
    (user_env_dir / ".env").write_text(
        "GMAIL_USER=user-file@example.com\nGMAIL_APP_PASSWORD=user-file-secret\n"
    )
    (agents_dir / "env.json").write_text(
        json.dumps(
            {
                "env": {
                    "GMAIL_USER": "agent-json@example.com",
                    "GMAIL_APP_PASSWORD": "agent-json-secret",
                }
            }
        )
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            seen["user"] = user
            seen["password"] = password

        def labels(self):
            return ({"labels": []}, {"backend": "imap", "readonly": True})

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["labels"])

    assert result.exit_code == 0
    assert seen == {"user": "user-file@example.com", "password": "user-file-secret"}
    assert "agent-json-secret" not in result.stdout


def test_agents_env_json_fills_missing_credentials_without_printing_values(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    agents_dir = home / ".config" / "agents"
    agents_dir.mkdir(parents=True)
    project.mkdir()
    (agents_dir / "env.json").write_text(
        json.dumps(
            {
                "env": {
                    "GMAIL_USER": "agent-json@example.com",
                    "GMAIL_APP_PASSWORD": "agent-json-secret",
                }
            }
        )
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()

    result = CliRunner().invoke(module.app, ["config"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["result"]["credentials"] == {
        "gmail_user_present": True,
        "gmail_app_password_present": True,
    }
    assert {"kind": "agents_env_json", "loaded": True, "path": str(agents_dir / "env.json")} in data[
        "result"
    ]["credential_sources"]
    assert "agent-json-secret" not in result.stdout
    assert "agent-json@example.com" not in result.stdout


def test_shell_env_is_ignored_by_default_and_loaded_when_requested(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    fake_shell = tmp_path / "fake-shell"
    fake_shell.write_text(
        "#!/bin/sh\n"
        "cat <<'EOF'\n"
        "__GMAIL_ENV_JSON_START__\n"
        '{"GMAIL_USER":"shell@example.com","GMAIL_APP_PASSWORD":"shell-secret"}\n'
        "__GMAIL_ENV_JSON_END__\n"
        "EOF\n"
    )
    fake_shell.chmod(0o755)

    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SHELL", str(fake_shell))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()

    default_result = CliRunner().invoke(module.app, ["config"])
    loaded_result = CliRunner().invoke(module.app, ["config", "--load-shell-env"])

    assert default_result.exit_code == 0
    default_data = json.loads(default_result.stdout)
    assert default_data["result"]["credentials"] == {
        "gmail_user_present": False,
        "gmail_app_password_present": False,
    }
    assert {"kind": "login_shell_env", "loaded": False, "skipped": True, "reason": "not requested"} in default_data[
        "result"
    ]["credential_sources"]

    assert loaded_result.exit_code == 0
    loaded_data = json.loads(loaded_result.stdout)
    assert loaded_data["result"]["credentials"] == {
        "gmail_user_present": True,
        "gmail_app_password_present": True,
    }
    assert {"kind": "login_shell_env", "loaded": True} in loaded_data["result"]["credential_sources"]
    assert "shell-secret" not in loaded_result.stdout
    assert "shell@example.com" not in loaded_result.stdout


def test_doctor_reports_readonly_connectivity(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            seen["user"] = user
            seen["password"] = password

        def doctor(self):
            return (
                {"status": "ok", "authenticated": True, "mailbox": {"name": "[Gmail]/All Mail"}},
                {"backend": "imap", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["doctor"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data == {
        "success": True,
        "command": "doctor",
        "result": {
            "status": "ok",
            "authenticated": True,
            "mailbox": {"name": "[Gmail]/All Mail"},
        },
        "metadata": {"backend": "imap", "readonly": True},
    }
    assert seen == {"user": "me@example.com", "password": "secret"}


def test_doctor_returns_structured_error_with_suggestions(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def doctor(self):
            raise module.GmailError(
                module.ErrorCode.AUTH_FAILED,
                "Gmail rejected the configured credentials.",
                suggestions=["Check GMAIL_USER", "Create a new Gmail app password"],
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["doctor"])

    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data == {
        "success": False,
        "command": "doctor",
        "error": {
            "code": "AUTH_FAILED",
            "message": "Gmail rejected the configured credentials.",
            "suggestions": ["Check GMAIL_USER", "Create a new Gmail app password"],
        },
    }
    assert "secret" not in result.stdout


def test_labels_returns_success_envelope_from_backend(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def labels(self):
            return (
                {"labels": [{"name": "INBOX", "attributes": ["\\HasNoChildren"]}]},
                {"backend": "imap", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["labels"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "success": True,
        "command": "labels",
        "result": {"labels": [{"name": "INBOX", "attributes": ["\\HasNoChildren"]}]},
        "metadata": {"backend": "imap", "readonly": True},
    }


def test_search_missing_credentials_returns_stable_error(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    module = load_gmail_module()

    result = CliRunner().invoke(module.app, ["search", "--from", "example.com"])

    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["command"] == "search"
    assert data["error"]["code"] == "MISSING_CREDENTIALS"
    assert data["error"]["suggestions"]


def test_search_query_defaults_exclude_sent_spam_and_trash(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def search(self, **kwargs):
            seen.update(kwargs)
            return (
                {"query": kwargs["query"], "messages": [], "count": 0, "truncated": False},
                {"backend": "imap", "mailbox": "all", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["search"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["result"]["query"] == "-in:sent -in:spam -in:trash"
    assert seen["query"] == "-in:sent -in:spam -in:trash"


def test_search_query_combines_raw_and_structured_flags(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def search(self, **kwargs):
            return (
                {"query": kwargs["query"], "messages": [], "count": 0, "truncated": False},
                {"backend": "imap", "mailbox": "all", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(
        module.app,
        [
            "search",
            "--query",
            "has:attachment newer_than:30d",
            "--from",
            "example.com",
            "--subject",
            "weekly digest",
            "--include-sent",
            "--include-spam-trash",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["result"]["query"] == (
        'has:attachment newer_than:30d from:example.com subject:"weekly digest"'
    )


def test_search_query_represents_all_structured_filters(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def search(self, **kwargs):
            return (
                {"query": kwargs["query"], "messages": [], "count": 0, "truncated": False},
                {"backend": "imap", "mailbox": "all", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(
        module.app,
        [
            "search",
            "--from",
            "sender@example.com",
            "--subject",
            "Quarterly Report",
            "--text",
            "pricing memo",
            "--label",
            "Newsletters",
            "--after",
            "2026-01-01",
            "--before",
            "2026-02-01",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["result"]["query"] == (
        'from:sender@example.com subject:"Quarterly Report" "pricing memo" '
        'label:Newsletters after:2026/01/01 before:2026/02/01 '
        '-in:sent -in:spam -in:trash'
    )


def test_invalid_search_date_fails_before_backend_access(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    called = {"backend": False}

    class FakeBackend:
        def __init__(self, user, password):
            called["backend"] = True

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["search", "--after", "2026-99-01"])

    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["command"] == "search"
    assert data["error"]["code"] == "INVALID_INPUT"
    assert called["backend"] is False


def test_invalid_search_limit_fails_before_backend_access(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    called = {"backend": False}

    class FakeBackend:
        def __init__(self, user, password):
            called["backend"] = True

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["search", "--limit", "0"])

    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["command"] == "search"
    assert data["error"]["code"] == "INVALID_INPUT"
    assert called["backend"] is False


def raw_email(subject="Hello", body="Body text"):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "Sender <sender@example.com>"
    msg["To"] = "me@example.com"
    msg["Date"] = "Mon, 12 Jan 2026 10:00:00 +0000"
    msg.set_content(body)
    return msg.as_bytes()


PLAIN_BODYSTRUCTURE = '("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 24 1 NIL NIL NIL NIL)'
MIXED_BODYSTRUCTURE = (
    '(("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 11 1 NIL NIL NIL NIL)'
    '("APPLICATION" "PDF" ("NAME" "report.pdf") NIL NIL "BASE64" 20 NIL '
    '("ATTACHMENT" ("FILENAME" "report.pdf")) NIL NIL) "MIXED" ("BOUNDARY" "x") NIL NIL NIL)'
)


def fetch_prefix(bodystructure=PLAIN_BODYSTRUCTURE, msgid="999", thrid="888", labels="\\Inbox"):
    return (
        f'101 (X-GM-MSGID {msgid} X-GM-THRID {thrid} X-GM-LABELS ({labels}) '
        f'BODYSTRUCTURE {bodystructure} BODY[HEADER.FIELDS (DATE FROM SUBJECT)] {{1}}'
    ).encode()


class FakeIMAPBase:
    mailboxes = [b'(\\HasNoChildren \\All) "/" "[Gmail]/All Mail"']

    def __init__(self, host="imap.gmail.com", port=993, ssl_context=None):
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.selected = None
        self.login_args = None
        self.search_args = None
        self.fetch_commands = []

    def login(self, user, password):
        self.login_args = (user, password)
        return "OK", [b"authenticated"]

    def list(self):
        return "OK", self.mailboxes

    def select(self, mailbox, readonly=False):
        self.selected = (mailbox, readonly)
        return "OK", [b"1"]

    def logout(self):
        return "OK", [b"bye"]


def test_backend_search_selects_all_mail_readonly(monkeypatch):
    module = load_gmail_module()
    instances = []

    class FakeIMAP(FakeIMAPBase):
        mailboxes = [
            b'(\\HasNoChildren \\All) "/" "[Gmail]/All Mail"',
            b'(\\HasNoChildren) "/" "INBOX"',
        ]

        def __init__(self, host, port, ssl_context=None):
            super().__init__(host, port, ssl_context)
            instances.append(self)

        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                self.search_args = args
                return "OK", [b"101"]
            if command.upper() == "FETCH":
                fetch_command = args[1]
                if "BODYSTRUCTURE" in fetch_command:
                    return "OK", [(fetch_prefix(), raw_email()), b")"]
                if "BODY.PEEK[1]" in fetch_command:
                    return "OK", [(b"101 (BODY[1] {9}", b"Body text"), b")"]
            raise AssertionError((command, args))

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", FakeIMAP)

    result, metadata = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=50
    )

    assert instances[0].login_args == ("me@example.com", "secret")
    assert instances[0].selected == ('"[Gmail]/All Mail"', True)
    assert instances[0].search_args == (None, "X-GM-RAW", '"from:example.com"')
    assert metadata == {
        "backend": "imap",
        "mailbox": "all",
        "resolved_mailbox": "[Gmail]/All Mail",
        "readonly": True,
    }
    assert result["messages"][0]["id"] == "999"
    assert result["messages"][0]["threadId"] == "888"


def test_get_returns_selected_message_body_with_truncation(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def get_message(self, message_id, max_chars):
            seen["message_id"] = message_id
            seen["max_chars"] = max_chars
            return (
                {
                    "message": {
                        "id": message_id,
                        "threadId": "thread-1",
                        "body": {
                            "text": "hello",
                            "truncated": True,
                            "max_chars": 5,
                            "original_chars": 11,
                            "returned_chars": 5,
                        },
                    }
                },
                {"backend": "imap", "mailbox": "all", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(module.app, ["get", "gmail-1", "--max-chars", "5"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["command"] == "get"
    assert data["result"]["message"]["body"]["text"] == "hello"
    assert data["result"]["message"]["body"]["truncated"] is True
    assert seen == {"message_id": "gmail-1", "max_chars": 5}


def test_thread_returns_direction_markers_and_per_message_caps(monkeypatch):
    module = load_gmail_module()
    monkeypatch.setenv("GMAIL_USER", "me@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    seen = {}

    class FakeBackend:
        def __init__(self, user, password):
            pass

        def get_thread(self, thread_id, max_messages, max_chars_per_message):
            seen["thread_id"] = thread_id
            seen["max_messages"] = max_messages
            seen["max_chars_per_message"] = max_chars_per_message
            return (
                {
                    "threadId": thread_id,
                    "messages": [
                        {"id": "m1", "direction": "received", "body": {"text": "hello", "max_chars": 6}},
                        {"id": "m2", "direction": "sent", "body": {"text": "reply", "max_chars": 6}},
                    ],
                    "count": 2,
                    "truncated": False,
                },
                {"backend": "imap", "mailbox": "all", "readonly": True},
            )

    monkeypatch.setattr(module, "GmailBackend", FakeBackend, raising=False)

    result = CliRunner().invoke(
        module.app,
        ["thread", "thread-1", "--max-messages", "2", "--max-chars-per-message", "6"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert [message["direction"] for message in data["result"]["messages"]] == ["received", "sent"]
    assert seen == {
        "thread_id": "thread-1",
        "max_messages": 2,
        "max_chars_per_message": 6,
    }


def test_backend_search_falls_back_to_inbox_when_all_mail_missing(monkeypatch):
    module = load_gmail_module()
    instances = []

    class FakeIMAP(FakeIMAPBase):
        mailboxes = [b'(\\HasNoChildren) "/" "INBOX"']

        def __init__(self, host, port, ssl_context=None):
            super().__init__(host, port, ssl_context)
            instances.append(self)

        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b""]
            raise AssertionError(command)

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", FakeIMAP)

    result, metadata = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=50
    )

    assert instances[0].selected == ('"INBOX"', True)
    assert metadata["mailbox"] == "inbox"
    assert metadata["resolved_mailbox"] == "INBOX"
    assert result["messages"] == []


def test_search_results_are_bounded_snippets_without_bodies(monkeypatch):
    module = load_gmail_module()

    class FakeIMAP(FakeIMAPBase):
        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b"101"]
            if command.upper() == "FETCH":
                self.fetch_commands.append(args[1])
                fetch_command = args[1]
                assert "BODY.PEEK[]" not in fetch_command
                if "BODYSTRUCTURE" in fetch_command:
                    return "OK", [(fetch_prefix(), raw_email()), b")"]
                if "BODY.PEEK[1]" in fetch_command:
                    return "OK", [(b"101 (BODY[1] {26}", b"0123456789 extra body text"), b")"]
            raise AssertionError((command, args))

    instances = []

    def fake_factory(*args, **kwargs):
        imap = FakeIMAP(*args, **kwargs)
        instances.append(imap)
        return imap

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", fake_factory)

    result, _ = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=10
    )

    message = result["messages"][0]
    assert message["snippet"] == "0123456789"
    assert message["snippet_truncated"] is True
    assert "body" not in message
    assert instances[0].fetch_commands == [
        "(X-GM-MSGID X-GM-THRID X-GM-LABELS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])",
        "(BODY.PEEK[1])",
    ]


def test_attachment_metadata_from_bodystructure_without_fetching_attachment_payload(monkeypatch):
    module = load_gmail_module()

    class FakeIMAP(FakeIMAPBase):
        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b"101"]
            if command.upper() == "FETCH":
                fetch_command = args[1]
                self.fetch_commands.append(fetch_command)
                assert "BODY.PEEK[]" not in fetch_command
                assert "BODY.PEEK[2]" not in fetch_command
                if "BODYSTRUCTURE" in fetch_command:
                    return "OK", [(fetch_prefix(bodystructure=MIXED_BODYSTRUCTURE), raw_email()), b")"]
                if "BODY.PEEK[1]" in fetch_command:
                    return "OK", [(b"101 (BODY[1] {11}", b"hello world"), b")"]
            raise AssertionError((command, args))

    instances = []

    def fake_factory(*args, **kwargs):
        imap = FakeIMAP(*args, **kwargs)
        instances.append(imap)
        return imap

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", fake_factory)

    result, _ = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=100
    )

    message = result["messages"][0]
    assert message["snippet"] == "hello world"
    assert message["attachments"] == [
        {"filename": "report.pdf", "content_type": "application/pdf", "size": 20}
    ]
    assert instances[0].fetch_commands == [
        "(X-GM-MSGID X-GM-THRID X-GM-LABELS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])",
        "(BODY.PEEK[1])",
    ]


def test_numeric_gmail_message_id_does_not_fallback_to_unrelated_imap_uid(monkeypatch):
    module = load_gmail_module()

    class FakeIMAP(FakeIMAPBase):
        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                assert args == (None, "X-GM-MSGID", "999")
                return "OK", [b""]
            if command.upper() == "FETCH":
                raise AssertionError("numeric Gmail ID should not be treated as an IMAP UID")
            raise AssertionError((command, args))

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", FakeIMAP)

    with pytest.raises(module.GmailError) as exc:
        module.GmailBackend("me@example.com", "secret").get_message("999", 100)

    assert exc.value.code == module.ErrorCode.MESSAGE_NOT_FOUND


def test_body_extraction_prefers_plain_text_and_falls_back_from_html():
    module = load_gmail_module()
    msg = EmailMessage()
    msg.set_content(" plain\n\n  text\twins ")
    msg.add_alternative("<p>html loses</p>", subtype="html")

    assert module.extract_normalized_body(msg) == "plain text wins"

    html_only = EmailMessage()
    html_only.add_alternative("<div>Hello <b>world</b></div>", subtype="html")

    assert module.extract_normalized_body(html_only) == "Hello world"
    assert module._truncate_text("abcdef", 3) == {
        "text": "abc",
        "truncated": True,
        "max_chars": 3,
        "original_chars": 6,
        "returned_chars": 3,
    }


def test_attachment_metadata_excludes_attachment_content():
    module = load_gmail_module()
    msg = EmailMessage()
    msg.set_content("See attached")
    msg.add_attachment(
        b"binary-secret-content",
        maintype="application",
        subtype="pdf",
        filename="report.pdf",
    )

    attachments = module.extract_attachment_metadata(msg)

    assert len(attachments) == 1
    assert attachments[0]["filename"] == "report.pdf"
    assert attachments[0]["content_type"] == "application/pdf"
    assert "content" not in attachments[0]
    assert "payload" not in attachments[0]
    assert "binary-secret-content" not in json.dumps(attachments)
