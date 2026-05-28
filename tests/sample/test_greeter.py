"""Tests for ``sample.greeter``.

Mirrors ``src/sample/greeter.py``. Follows the AAA pattern from
``.cursor/rules/041-python-tests.mdc``.
"""

from __future__ import annotations

import pytest

from sample.greeter import greet


def test_greet_returns_friendly_message_for_simple_name() -> None:
    result = greet("Cursor")

    assert result == "Hello, Cursor!"


def test_greet_trims_surrounding_whitespace() -> None:
    result = greet("  Cursor\t\n")

    assert result == "Hello, Cursor!"


def test_greet_raises_on_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        greet("")


def test_greet_raises_on_whitespace_only_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        greet("   \n\t")
