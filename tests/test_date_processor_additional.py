"""Additional tests for date message processor batch and error-handling flows."""

from unittest.mock import MagicMock
import os

import pytest

os.environ.setdefault("SMTP_USERNAME", "sender@example.com")
os.environ.setdefault("SMTP_PASSWORD", "smtp-secret")
os.environ.setdefault("TO_EMAIL", "ops@example.com")

from src.modules.parsers.message.date_processor import DateRangeMessageProcessor
from src.modules.parsers.message.exceptions import MessageNotFoundError


def _build_date_processor():
    processor = DateRangeMessageProcessor.__new__(DateRangeMessageProcessor)
    processor.mail_connector = MagicMock()
    processor.error_processor = MagicMock()
    return processor


def test_process_email_by_id_returns_unsuccessful_for_short_id():
    processor = _build_date_processor()

    assert processor.process_email_by_id("<>") == {
        "start_month": None,
        "end_month": None,
        "success": False,
    }


def test_process_email_by_id_raises_when_message_not_found():
    processor = _build_date_processor()
    processor.upd_index = MagicMock(return_value={"missing": 0})

    with pytest.raises(MessageNotFoundError):
        processor.process_email_by_id("<missing>")


def test_process_all_emails_collects_success_and_failures():
    processor = _build_date_processor()
    processor.db_client = MagicMock()
    processor.db_client.get_all_message_ids.return_value = {
        "ok-message": "1",
        "failed-message": "2",
    }

    def _fake_process(message_id):
        if message_id == "failed-message":
            raise RuntimeError("broken")
        return {"start_month": "2026-01-01", "end_month": "2026-01-31", "success": True}

    processor.process_email_by_id = MagicMock(side_effect=_fake_process)

    results = processor.process_all_emails()

    assert len(results) == 2
    assert results[0]["message_id"] == "ok-message"
    assert results[0]["status"] == "success"
    assert results[1]["message_id"] == "failed-message"
    assert results[1]["status"] == "failed"
    assert results[1]["result"]["success"] is False
    assert "broken" in results[1]["error"]
