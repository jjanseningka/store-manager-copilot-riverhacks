# src

Application code lives here, grouped by feature.

The starter ships with one placeholder package — `sample/` — so that
`make test`, `make lint`, and `make typecheck` have something real to run
against on day one. The agent rules in `.cursor/rules/040-python.mdc` and
`.cursor/rules/041-python-tests.mdc` already point at this layout.

## Replacing the sample

1. Rename `sample/` to your real package name (snake_case).
2. Update the import in `src/sample/__init__.py` (or delete the re-export).
3. Rename the matching folder under `tests/` so the mirror still holds.
4. Update `docs/architecture/project-map.md` and the file tree in `README.md`.

## Conventions

- One package per feature. Avoid a flat `src/utils.py` dumping ground.
- Mirror every `src/foo/bar.py` with `tests/foo/test_bar.py`.
- Public API lives in `__init__.py`. Implementation lives in sibling modules.
