# Contributing

Contributions of any size are welcome — bug fixes, additional orthogonal arrays, three-level support, plotting tweaks, MCP tools, more tests, documentation polish.

## Setting up

```bash
git clone https://github.com/grcarmenaty/tagupy.git
cd tagupy
pip install -e ".[dev,mcp]"
```

This pulls in `pytest`, `pytest-cov`, and the `mcp` SDK so the full test surface and the MCP server are available.

## Branching

The default integration branch is `main`. Long-lived feature branches are encouraged; please open a pull request once your branch is ready for review.

## Coding conventions

- **PEP 8** — keep lines under ~100 chars, prefer descriptive names.
- **Type hints on all public functions.**
- **NumPy-style docstrings** — see `taguchi/design.py` for the canonical examples.
- **Pandas 2.0+ idioms only.** Do not use `DataFrame.append`, `Series.replace(..., inplace=True)`, or other deprecated APIs.
- **Immutable shared state.** Module-level array data must be returned as fresh copies; never mutate `_ARRAYS_RAW` or `_ASSIGNATIONS_RAW`.
- **No silent failures.** Validate at boundaries with descriptive `ValueError` / `RuntimeError` messages.

## Tests

All changes must keep the suite green:

```bash
pytest tests/
```

When you add behaviour, add a test. When you fix a bug, add a regression test that fails on `main` and passes on your branch.

## Commit messages

Short imperative subject (≤72 chars), wrap the body at ~72 chars, explain *why* in the body when the diff alone is not enough. Example:

```
arrays: protect interaction tables from accidental mutation

Previously, get_assignation() returned a view into the module-level
dict, so consumers could (and did) mutate it. Switch to returning a
fresh DataFrame on every call to match the get_array() contract.
```

## Pull requests

- One logical change per PR; smaller diffs ship faster.
- Reference any related issue.
- Update or add documentation where the behaviour changed.
- Confirm `pytest` passes locally before requesting review.

## Filing issues

When reporting a bug, include:

1. Python, numpy, pandas, and matplotlib versions (`pip freeze | grep -E '^(numpy|pandas|matplotlib|taguchi)'`).
2. Minimal reproducible snippet.
3. Full traceback / screenshot.

## Areas where help is especially welcome

- Three-level orthogonal arrays (L9, L18, L27).
- Mixed-level designs.
- A GitHub Actions CI workflow.
- More comprehensive notebook tutorials.
- Translating the README sections into per-page wiki content.
