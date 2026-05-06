# Testing

The library ships a `pytest`-based test suite in `tests/`. Install the dev extras to pull in `pytest` and `pytest-cov`:

```bash
pip install -e ".[dev]"
```

Run the full suite:

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ -v --cov=taguchi
```

`pyproject.toml` sets `testpaths = ["tests"]` and `addopts = "-v"`, so plain `pytest` from the repo root works as well.

## Test modules

| File | Coverage |
|---|---|
| `tests/test_arrays.py` | Array data integrity, that fresh copies are returned, that mutation does not leak across calls. |
| `tests/test_design.py` | `TaguchiDesign` initialisation, factor-letter assignment, column labelling, multi-instance isolation, validation errors. |
| `tests/test_analysis.py` | Effect / SS / contribution numerics, repetition handling, save/load round-trips. |

## What the suite verifies

The current tests focus on:

- Correct construction of the experimental matrix from any of the four arrays.
- Letter-and-interaction renaming for arbitrary `assignation` lists.
- That `experimental_design` validation rejects mismatched assignation lengths and unknown matrix names.
- That two `TaguchiDesign` instances do not share underlying DataFrames (no aliased state).
- Numerical correctness of `analyze()` — the contribution columns sum to 100 % (or 0 % for null SS).
- Save / load round-trips: metadata, factor values, response columns, and the mixed-type index all survive a zip-and-back cycle.
- Repetition handling: per-rep, average, and standard-deviation columns are populated correctly.

## Adding a test

Mirror the existing module layout:

```python
# tests/test_my_feature.py
import pytest
from taguchi import TaguchiDesign

def test_my_feature():
    design = TaguchiDesign({"A": [1, 2]}, [0], matrix="L8")
    assert design.matrix_name == "L8"
```

Conventions used in the existing suite:

- One `class TestXxx:` per logical area.
- Tests are short, single-assertion-where-possible.
- Use `pytest.raises(ValueError)` for validation errors.
- Avoid hitting matplotlib in unit tests; for plot-related code, exercise the data path and trust the matplotlib API surface.

## Continuous integration

There is no CI workflow committed at this point — running `pytest` locally before opening a PR is the expected baseline. Contributions adding a GitHub Actions workflow would be welcome.
