# Workflow

The canonical tagupy workflow is six steps. Each step maps to one or two `TaguchiDesign` calls.

```
1. design  →  2. inspect  →  3. run  →  4. analyse  →  5. plot  →  6. save / load
```

## 1. Design

Pick an array and assign factors to columns.

```python
from taguchi import TaguchiDesign

design = TaguchiDesign(
    experimental_design={
        "Learning rate": [1e-4, 1e-3],
        "Batch size":    [16, 64],
        "Num filters":   [16, 64],
        "Dropout":       [0.2, 0.5],
    },
    assignation=[0, 2, 4, 6],
    matrix="L16",
)
```

Rules:

- The dict order determines factor letters: `Learning rate → A`, `Batch size → B`, etc.
- `len(assignation) == len(experimental_design)`.
- Every level pair must be exactly two values: `[low, high]`.

## 2. Inspect

```python
design.experimental_matrix       # The runs you must execute
design.columns                   # Column labels: 'A', 'B', 'AB', 'C', ...
design.taguchi_design            # Raw orthogonal array with letter renames
```

## 3. Run

You provide a callable `func(factors) → dict[response, value]`.

```python
def objective(factors):
    lr, batch, filters, dropout = factors[:4]
    accuracy = train_cnn(lr, batch, filters, dropout)
    return {"accuracy": accuracy, "loss": 1.0 - accuracy}

design.run(
    objective,
    responses=["accuracy", "loss"],
    repetitions=2,                 # 2 reps per run
    randomize=False,               # set True to shuffle row order
    progress_path="checkpoint.csv" # optional checkpointing
)
```

When `repetitions > 1`, your `func` receives one extra integer (the rep index) appended to `factors`.

### Robustness features

- **Checkpointing** — if `progress_path` is set, the partial results CSV is rewritten after every run and deleted on clean completion.
- **Emergency save** — on any exception inside `func`, the in-progress data is dumped to `<progress_path>.emergency.csv` (or `./emergency_save.csv`) before the exception is re-raised.

### Externally-measured results

If you ran experiments outside Python (e.g. in a lab) and want to feed the values back into the library, use the MCP server's `add_results` tool — see [[MCP Server]] — or the `_add_results_to_design()` helper in `tagupy_mcp.tools`.

## 4. Analyse

```python
design.analyze()
```

Adds analysis columns and an `"analysis"` row to each response's DataFrame. Inspect them with:

```python
df = design.taguchi_design["accuracy"]
df.loc["analysis", [f"{c} Contribution" for c in design.columns]]
```

## 5. Plot

```python
design.pareto_plot(path="./pareto")          # one PNG per response
design.effect_plots(path="./effects")        # main + interaction plots
```

Customisation:

```python
design.pareto_plot(
    path="./pareto",
    title="My experiment",
    font_family="DejaVu Sans",
    font_size=14,
)

design.effect_plots(
    path="./effects",
    limits=[[0.5, 1.0], None],   # per-response y-axis limits
    percentage=[True, False],    # format y-axis as %?
)
```

The convenience wrappers `taguchi.plotting.pareto_plot(design, **kwargs)` and `taguchi.plotting.effect_plots(design, **kwargs)` simply forward to the methods above.

## 6. Save / Load

```python
design.save("experiment.zip")

# Later, in a fresh process:
loaded = TaguchiDesign.load("experiment.zip")
loaded.responses           # ['accuracy', 'loss']
loaded.taguchi_design      # dict of DataFrames, fully restored
```

The archive contains:

| File | Contents |
|---|---|
| `metadata.json` | Factor definitions, column labels, response names, repetition count, array name, original assignation |
| `experimental_matrix.csv` | The factor-value matrix |
| `taguchi_design_<response>.csv` | One CSV per response (after `run()`) |
| `taguchi_design_raw.csv` | Pre-`run()` design only (when no responses recorded) |

CSV round-trips turn integer row indices into strings; `_restore_index()` recovers the mixed-type index (`int` for runs, `"analysis"` for the summary row).

## Determining optimal levels

`TaguchiDesign` itself does not include an optimal-levels helper, but you can compute it directly from the analysis row:

```python
import pandas as pd
df = design.taguchi_design["accuracy"].loc["analysis"]
factor_letters = [c for c in design.columns if len(c) == 1 and c.isalpha()]
for letter in factor_letters:
    low  = df[f"{letter} (Low)"]
    high = df[f"{letter} (High)"]
    print(letter, "→", "High" if high > low else "Low")
```

Through the MCP server, the `get_optimal_levels` tool wraps this logic and returns the additive-model prediction.
