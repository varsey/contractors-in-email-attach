"""Additional tests for message processors covering network and branch-heavy flows."""

import imaplib
import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("SMTP_USERNAME", "sender@example.com")
os.environ.setdefault("SMTP_PASSWORD", "smtp-secret")
os.environ.setdefault("TO_EMAIL", "ops@example.com")

from src.modules.parsers.message.exceptions import MessageNotFoundError, NetworkError
from src.modules.parsers.message.inn_processor import INNMessageProcessor


def _build_inn_processor():
    processor = INNMessageProcessor.__new__(INNMessageProcessor)
    processor.mail_connector = MagicMock()
    processor.error_processor = MagicMock()
    return processor


def test_process_email_by_id_returns_empty_for_short_id():
    processor = _build_inn_processor()

    assert processor.process_email_by_id("<>") == {}


def test_process_email_by_id_raises_not_found_when_index_missing():
    processor = _build_inn_processor()
    processor.upd_index = MagicMock(return_value={"missing": 0})

    with pytest.raises(MessageNotFoundError):
        processor.process_email_by_id("<missing>")


def test_process_email_by_id_raises_network_error_on_imap_failure():
    processor = _build_inn_processor()
    processor.upd_index = MagicMock(side_effect=imaplib.IMAP4.error("connection failed"))

    with pytest.raises(NetworkError):
        processor.process_email_by_id("<message-id>")


def test_process_email_by_id_filters_masked_inn_values(monkeypatch):
    processor = _build_inn_processor()
    processor.upd_index = MagicMock(return_value={"message-id": b"1"})
    processor.see_msg = MagicMock(return_value=[(None, b"raw")])
    processor.get_message_attributes = MagicMock(return_value=({}, "mail-body", "sender@example.com"))
    processor.parse_attributes = MagicMock(
        return_value={
            "message": {"inn": ["1234567890", "123*", "123456789012"]},
            "attach": {"inn": ["1234567890", "456*", "1111111111"]},
        }
    )

    clear_calls = []
    monkeypatch.setattr("src.modules.parsers.message.inn_processor.clear_folders", lambda paths: clear_calls.append(paths))

    result = processor.process_email_by_id("<message-id>")

    assert sorted(result["inns"]) == ["1111111111", "1234567890", "123456789012"]
    assert clear_calls
