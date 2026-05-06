# API Reference

This page documents every public entry point in the `taguchi` package. The MCP server's tools are documented separately in [[MCP Server]].

## Package layout

```
taguchi/
├── __init__.py     re-exports TaguchiDesign, AVAILABLE_ARRAYS, get_array, get_assignation
├── arrays.py       orthogonal-array data + accessors
├── design.py       the TaguchiDesign class
└── plotting.py     thin convenience wrappers around design.pareto_plot / design.effect_plots

tagupy_mcp/
├── __init__.py
├── server.py       FastMCP entry point (tagupy-mcp console script)
└── tools.py        tool & resource registration
```

## `taguchi.TaguchiDesign`

Two-level orthogonal-array DOE class.

### `__init__(experimental_design, assignation, matrix="L16")`

| Parameter | Type | Description |
|---|---|---|
| `experimental_design` | `dict[str, list]` | Ordered factor → `[low, high]` mapping. Order = letter assignment (`A`, `B`, …). |
| `assignation` | `Iterable[int]` | Zero-based column indices to assign each factor to. |
| `matrix` | `str` | One of `"L8"`, `"L16"` (default), `"L32"`, `"L32-inv"`. |

**Raises** `ValueError` for unknown matrices or mismatched assignation length.

**Sets attributes:**

| Attribute | Type | Notes |
|---|---|---|
| `experimental_design` | `dict` | Echo of input. |
| `experimental_matrix` | `pd.DataFrame` | Run matrix with actual factor *values* (not Low/High strings). |
| `taguchi_design` | `pd.DataFrame` | Raw orthogonal array with letter + interaction renames. *After `run()` becomes `dict[str, pd.DataFrame]`.* |
| `columns` | `list[str]` | All column labels (letters, two-letter interactions, unused numeric labels). |
| `responses` | `list[str]` | Empty until `run()` is called. |
| `repetitions` | `int` | Set by `run()`. Default `1`. |
| `matrix_name` | `str` | E.g. `"L16"`. |
| `assignation` | `list[str]` | String-cast column indices. |
| `taguchi_assignation` | `pd.DataFrame` | Interaction assignation table. |
| `experiences` | `list` | Run-row indices. |

### `run(func, responses, randomize=False, repetitions=1, progress_path=None)`

Execute the design.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `func` | `Callable` | — | Receives `list[factor_value]`; with `repetitions > 1` an extra `int` (rep index) is appended. Must return `dict[response_name, value]`. |
| `responses` | `list[str]` | — | Names of responses returned by `func`. |
| `randomize` | `bool` | `False` | Shuffle row order with `np.random.shuffle`. |
| `repetitions` | `int` | `1` | Number of replications per row. |
| `progress_path` | `str \| Path \| None` | `None` | Checkpoint CSV path. Deleted on clean exit. Emergency CSV (`<path>.emergency.csv`, or `./emergency_save.csv`) is written if `func` raises. |

After `run()`, `self.taguchi_design` becomes a dict keyed by response name. Each value is a DataFrame containing the design columns plus result columns (and per-rep / average / std columns when `repetitions > 1`).

### `analyze()`

Compute factor effects and contributions.

For every column `c` in `self.columns`, adds:

- `"{c} (Low)"` — mean response at Low level.
- `"{c} (High)"` — mean response at High level.
- `"{c} Effect"` — High − Low.
- `"{c} SS"` — Effect² (sum of squares).
- `"{c} Contribution"` — SS as % of total SS.

Appends a single `"analysis"` row carrying these summary values.

**Raises** `RuntimeError` if called before `run()`.

### `pareto_plot(title=None, path=None, font_family="Liberation Serif", font_size=12)`

Generate one Pareto contribution chart per response. Each PNG shows ranked column contributions plus a cumulative line.

| Parameter | Default |
|---|---|
| `title` | `None` (defaults to response name) |
| `path` | `./pareto_plots/` |
| `font_family` | `"Liberation Serif"` |
| `font_size` | `12` |

**Raises** `RuntimeError` if called before `run()` and `analyze()`.

### `effect_plots(limits=None, percentage=None, path=None, font_family="Liberation Serif", font_size=12)`

Generate main-effect and interaction plots.

- Single-letter columns produce two-point Low → High plots.
- Two-letter columns produce two-line interaction plots.

| Parameter | Type | Notes |
|---|---|---|
| `limits` | `list[[float, float] \| None]` | Per-response y-axis range. Length must equal `len(self.responses)`. |
| `percentage` | `list[bool]` | Format y-axis as percentages per response. |
| `path` | `str \| Path` | Default `./effect_plots/`. |
| `font_family`, `font_size` | matplotlib settings | |

**Raises** `RuntimeError` if called before `run()`.

### `save(path)`

Serialise the design to a zip archive containing `metadata.json`, `experimental_matrix.csv`, and one `taguchi_design_<response>.csv` per response (or `taguchi_design_raw.csv` if `run()` has not been called).

### `TaguchiDesign.load(path)` *(classmethod)*

Restore a design previously written with `save()`. Returns a fully-initialised `TaguchiDesign` (constructed via `__new__`, bypassing `__init__`). The mixed-type DataFrame index is restored via `_restore_index()`.

## `taguchi.arrays`

| Symbol | Description |
|---|---|
| `AVAILABLE_ARRAYS` | `['L8', 'L16', 'L32', 'L32-inv']` |
| `get_array(name) -> pd.DataFrame` | Fresh copy of the named array. |
| `get_assignation(name) -> pd.DataFrame` | Fresh copy of the interaction-assignation table. |

Both raise `ValueError` for unknown names.

## `taguchi.plotting`

Thin convenience wrappers — useful when you want functional-style invocation:

```python
from taguchi.plotting import pareto_plot, effect_plots
pareto_plot(design, path="./pareto")
effect_plots(design, path="./effects")
```

`pareto_plot(design, **kwargs)` and `effect_plots(design, **kwargs)` simply forward to `design.pareto_plot(**kwargs)` / `design.effect_plots(**kwargs)`.

## Module metadata

```python
import taguchi
taguchi.__version__   # '0.1.0'
```
