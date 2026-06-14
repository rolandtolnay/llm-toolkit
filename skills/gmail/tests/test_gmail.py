import importlib.util
import json
import sys
from email.message import EmailMessage
from pathlib import Path

from typer.testing import CliRunner


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gmail.py"


def load_gmail_module():
    spec = importlib.util.spec_from_file_location("gmail_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_config_reports_loaded_env_files_and_masks_credentials(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    global_env_dir = home / ".claude" / "gmail"
    local_env_dir = project / ".claude"
    global_env_dir.mkdir(parents=True)
    local_env_dir.mkdir(parents=True)
    project.mkdir(exist_ok=True)
    (global_env_dir / ".env").write_text(
        "GMAIL_USER=global@example.com\nGMAIL_APP_PASSWORD=global-secret\n"
    )
    (local_env_dir / "gmail.env").write_text(
        "GMAIL_USER=local@example.com\nGMAIL_APP_PASSWORD=local-secret\n"
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
    assert data["result"]["env_files"] == [
        {"path": str(global_env_dir / ".env"), "loaded": True},
        {"path": str(local_env_dir / "gmail.env"), "loaded": True},
    ]
    assert "global-secret" not in result.stdout
    assert "local-secret" not in result.stdout
    assert "global@example.com" not in result.stdout
    assert "local@example.com" not in result.stdout


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


def test_search_missing_credentials_returns_stable_error(monkeypatch):
    module = load_gmail_module()
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)

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


def test_backend_search_selects_all_mail_readonly(monkeypatch):
    module = load_gmail_module()
    instances = []

    class FakeIMAP:
        def __init__(self, host, port, ssl_context=None):
            self.host = host
            self.port = port
            self.selected = None
            instances.append(self)

        def login(self, user, password):
            self.login_args = (user, password)
            return "OK", [b"authenticated"]

        def list(self):
            return "OK", [
                b'(\\HasNoChildren \\All) "/" "[Gmail]/All Mail"',
                b'(\\HasNoChildren) "/" "INBOX"',
            ]

        def select(self, mailbox, readonly=False):
            self.selected = (mailbox, readonly)
            return "OK", [b"1"]

        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b"101"]
            if command.upper() == "FETCH":
                return "OK", [
                    (
                        b'101 (X-GM-MSGID 999 X-GM-THRID 888 X-GM-LABELS (\\Inbox) BODY[] {1}',
                        raw_email(),
                    ),
                    b")",
                ]
            raise AssertionError(command)

        def logout(self):
            return "OK", [b"bye"]

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", FakeIMAP)

    result, metadata = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=50
    )

    assert instances[0].login_args == ("me@example.com", "secret")
    assert instances[0].selected == ("[Gmail]/All Mail", True)
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

    class FakeIMAP:
        def __init__(self, host, port, ssl_context=None):
            self.selected = None
            instances.append(self)

        def login(self, user, password):
            return "OK", [b"authenticated"]

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "INBOX"']

        def select(self, mailbox, readonly=False):
            self.selected = (mailbox, readonly)
            return "OK", [b"1"]

        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b""]
            raise AssertionError(command)

        def logout(self):
            return "OK", [b"bye"]

    monkeypatch.setattr(module.imaplib, "IMAP4_SSL", FakeIMAP)

    result, metadata = module.GmailBackend("me@example.com", "secret").search(
        query="from:example.com", mailbox="all", limit=5, snippet_chars=50
    )

    assert instances[0].selected == ("INBOX", True)
    assert metadata["mailbox"] == "inbox"
    assert metadata["resolved_mailbox"] == "INBOX"
    assert result["messages"] == []


def test_search_results_are_bounded_snippets_without_bodies(monkeypatch):
    module = load_gmail_module()

    class FakeIMAP:
        def __init__(self, host, port, ssl_context=None):
            self.fetch_args = None

        def login(self, user, password):
            return "OK", [b"authenticated"]

        def list(self):
            return "OK", [b'(\\HasNoChildren \\All) "/" "[Gmail]/All Mail"']

        def select(self, mailbox, readonly=False):
            return "OK", [b"1"]

        def uid(self, command, *args):
            if command.upper() == "SEARCH":
                return "OK", [b"101"]
            if command.upper() == "FETCH":
                self.fetch_args = args
                return "OK", [
                    (
                        b'101 (X-GM-MSGID 999 X-GM-THRID 888 X-GM-LABELS (\\Inbox) BODY[] {1}',
                        raw_email(body="0123456789 extra body text"),
                    ),
                    b")",
                ]
            raise AssertionError(command)

        def logout(self):
            return "OK", [b"bye"]

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
    assert "BODY.PEEK[]" in instances[0].fetch_args[1]


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
