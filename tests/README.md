# tests

Automated tests live here. The layout mirrors `src/` one-to-one:
`src/foo/bar.py` → `tests/foo/test_bar.py`. The 041-python-tests rule
spells out the conventions.

## Running

```bash
make test           # runs pytest tests/
pytest tests/       # equivalent, when pytest is on PATH
pytest tests/sample/test_greeter.py::test_greet_returns_friendly_message_for_simple_name
```

`conftest.py` puts `src/` on `sys.path` so tests can `from sample.greeter
import greet` without needing an editable install. Replace with a real
`pyproject.toml` + `pip install -e .` (or `uv sync`) once the project
grows past a single sample package.

## Conventions (mirrors `.cursor/rules/041-python-tests.mdc`)

- Test names describe behaviour: `test_returns_empty_when_input_is_none`.
- Keep AAA sections visible: Arrange / Act / Assert with blank lines.
- Mock the boundary, not the language.
- No real network, real DB, or real filesystem outside `tmp_path`.
