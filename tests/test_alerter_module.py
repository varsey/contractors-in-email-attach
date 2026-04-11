"""Tests for alert sender behavior with SMTP success and failure paths."""

import importlib


def _load_alerter(monkeypatch):
    monkeypatch.setenv("SMTP_USERNAME", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-secret")
    monkeypatch.setenv("TO_EMAIL", "ops@example.com,admin@example.com")
    module = importlib.import_module("src.modules.alerter.alerter")
    return importlib.reload(module)


def test_send_email_alert_success(monkeypatch):
    alerter = _load_alerter(monkeypatch)

    class DummySMTP:
        def __init__(self, *_args, **_kwargs):
            self.started_tls = False
            self.logged_in = None
            self.sent = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            self.started_tls = True

        def login(self, username, password):
            self.logged_in = (username, password)

        def sendmail(self, from_addr, to_addrs, message):
            self.sent = (from_addr, to_addrs, message)

    smtp_instance = DummySMTP()
    monkeypatch.setattr(alerter.smtplib, "SMTP", lambda *_args, **_kwargs: smtp_instance)

    alerter.send_email_alert("partner@example.com")

    assert smtp_instance.started_tls is True
    assert smtp_instance.logged_in == ("sender@example.com", "smtp-secret")
    assert smtp_instance.sent[0] == "sender@example.com"
    assert smtp_instance.sent[1] == ["ops@example.com", "admin@example.com"]
    assert "Subject:" in smtp_instance.sent[2]
    assert "From: sender@example.com" in smtp_instance.sent[2]
    assert "To: ops@example.com, admin@example.com" in smtp_instance.sent[2]


def test_send_email_alert_handles_smtp_errors(monkeypatch):
    alerter = _load_alerter(monkeypatch)

    class BrokenSMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            raise RuntimeError("smtp unavailable")

    monkeypatch.setattr(alerter.smtplib, "SMTP", lambda *_args, **_kwargs: BrokenSMTP())

    alerter.send_email_alert("partner@example.com")
