# ============================================================
# Project0 - Common Services
#
# File: test_logging_config.py
#
# Purpose:
#     Verify application-wide logging configuration,
#     log level selection, formatting, and fallback behavior.
#
# ============================================================

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import project0.common.logging_config as logging_config


EXPECTED_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def test_configure_logging_uses_configured_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basic_config = Mock()

    monkeypatch.setattr(
        logging_config,
        "SETTINGS",
        SimpleNamespace(log_level="DEBUG"),
    )
    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        basic_config,
    )

    logging_config.configure_logging()

    basic_config.assert_called_once_with(
        level=logging.DEBUG,
        format=EXPECTED_FORMAT,
    )


def test_configure_logging_accepts_case_insensitive_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basic_config = Mock()

    monkeypatch.setattr(
        logging_config,
        "SETTINGS",
        SimpleNamespace(log_level="warning"),
    )
    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        basic_config,
    )

    logging_config.configure_logging()

    basic_config.assert_called_once_with(
        level=logging.WARNING,
        format=EXPECTED_FORMAT,
    )


def test_configure_logging_falls_back_to_info_for_invalid_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basic_config = Mock()

    monkeypatch.setattr(
        logging_config,
        "SETTINGS",
        SimpleNamespace(log_level="NOT_A_LEVEL"),
    )
    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        basic_config,
    )

    logging_config.configure_logging()

    basic_config.assert_called_once_with(
        level=logging.INFO,
        format=EXPECTED_FORMAT,
    )


def test_configure_logging_uses_expected_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basic_config = Mock()

    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        basic_config,
    )

    logging_config.configure_logging()

    _, keyword_arguments = basic_config.call_args

    assert keyword_arguments["format"] == EXPECTED_FORMAT


def test_configure_logging_calls_basic_config_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basic_config = Mock()

    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        basic_config,
    )

    logging_config.configure_logging()

    basic_config.assert_called_once()


def test_configure_logging_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        logging_config.logging,
        "basicConfig",
        Mock(),
    )

    result = logging_config.configure_logging()

    assert result is None
