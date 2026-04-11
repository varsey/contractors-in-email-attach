"""Tests for configuration loading and environment validation behavior."""

import importlib
import os

import pytest


def _reload_cfg_module(monkeypatch, env_values):
    for key in ["EMAIL", "PASS", "SERVER", "EMAIL2", "PASS2"]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    module = importlib.import_module("src.config.cfg")
    return importlib.reload(module)


def test_config_creds_and_creds2_from_environment(monkeypatch):
    cfg = _reload_cfg_module(
        monkeypatch,
        {
            "EMAIL": "primary@example.com",
            "PASS": "secret",
            "SERVER": "imap.example.com",
            "EMAIL2": "secondary@example.com",
            "PASS2": "secondary-secret",
        },
    )

    config = cfg.Config()

    assert config.creds == {
        "email": "primary@example.com",
        "password": "secret",
        "server": "imap.example.com",
        "mail_folder": cfg.MAIL_FOLDER,
    }
    assert config.creds2 == {
        "email": "secondary@example.com",
        "password": "secondary-secret",
        "server": "imap.example.com",
        "mail_folder": cfg.MAIL_FOLDER,
    }


def test_config_raises_when_required_values_missing(monkeypatch):
    cfg = _reload_cfg_module(
        monkeypatch,
        {
            "EMAIL": "primary@example.com",
            "PASS": "secret",
        },
    )

    with pytest.raises(ValueError, match="One of the EMAIL, PASS, SERVER parameter is not set"):
        cfg.Config()
