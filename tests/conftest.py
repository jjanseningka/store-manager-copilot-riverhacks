"""Pytest configuration shared by every test in the suite.

Empty for now: ``pyproject.toml`` already sets ``pythonpath = ["src"]`` so
the sample package imports without further setup. Add shared fixtures
here as the suite grows — keep them named for the value they produce,
not the action they perform (``authenticated_user``, not ``setup_user``).
"""
