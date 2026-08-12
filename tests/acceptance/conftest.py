# ============================================================
# Project0 - Acceptance Test Infrastructure
#
# File: conftest.py
#
# Purpose:
#     Provide shared pytest configuration for Project0 browser
#     acceptance tests, including optional Playwright slow-motion
#     execution for human observation.
#
# ============================================================

"""Shared pytest configuration for Project0 acceptance tests."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register Project0-specific acceptance-test command-line options."""

    parser.addoption(
        "--ui-slowmo",
        action="store",
        type=int,
        default=0,
        metavar="MILLISECONDS",
        help=(
            "Delay Playwright browser operations by the specified number "
            "of milliseconds for human observation. Default: 0."
        ),
    )


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict,
    pytestconfig: pytest.Config,
) -> dict:
    """Add the configured UI observation delay to Playwright launch args."""

    slow_mo = pytestconfig.getoption("--ui-slowmo")

    if slow_mo < 0:
        raise pytest.UsageError("--ui-slowmo must be 0 or greater.")

    return {
        **browser_type_launch_args,
        "slow_mo": slow_mo,
    }
