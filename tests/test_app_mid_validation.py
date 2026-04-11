import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("EMAIL", "sender@example.com")
os.environ.setdefault("PASS", "secret")
os.environ.setdefault("SERVER", "imap.example.com")
os.environ.setdefault("EMAIL2", "sender2@example.com")
os.environ.setdefault("PASS2", "secret2")

with patch("src.modules.email.client.EmailClient.setup_mail_connector", return_value=MagicMock()):
    from app import app


def test_parsing_endpoint_requires_mid_param():
    client = app.test_client()

    response = client.get("/api/parsing/")

    assert response.status_code == 400
    assert "mid" in response.get_json()["error"]


def test_parsing_v2_endpoint_requires_non_empty_mid_param():
    client = app.test_client()

    response = client.get("/api/parsing/v2/?mid=   ")

    assert response.status_code == 400
    assert "mid" in response.get_json()["error"]
