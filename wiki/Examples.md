# Examples

Two ready-to-run examples ship with the repository in `examples/`.

## `examples/basic_usage.py` — minimal script

Runs from the command line. Defines four CNN-style hyperparameters, runs a noisy mock objective on L16 with 2 repetitions, analyses, plots, and saves.

```bash
python examples/basic_usage.py
```

Excerpt:

```python
experimental_design = {
    "Learning rate": [1e-4, 1e-3],
    "Batch size":    [16, 64],
    "Num filters":   [16, 64],
    "Dropout rate":  [0.2, 0.5],
}

design = TaguchiDesign(experimental_design, assignation=[0, 2, 4, 6], matrix="L16")
design.run(objective_function, responses=["accuracy", "loss"], repetitions=2)
design.analyze()
design.pareto_plot(path="./pareto_plots")
design.effect_plots(path="./effect_plots")
design.save("example_design.zip")

loaded = TaguchiDesign.load("example_design.zip")
```

Artefacts produced:

- `pareto_plots/accuracy.png`, `pareto_plots/loss.png`
- `effect_plots/<response-letter>.png` per factor and interaction
- `example_design.zip`

## `examples/tagupy_example.ipynb` — notebook walkthrough ⭐ recommended

A publication-quality narrative directly inspired by the SHM paper that motivated the library. Covers:

1. Defining factors and levels (CFDAC vs FRF, ResNet-18 vs ResNet-34, frequency lines, learning rate).
2. Generating and inspecting the L8 orthogonal array.
3. Running experiments via a fast `scikit-learn` surrogate (no GPU needed).
4. Signal-to-noise analysis — factor effects, sums of squares, percentage contributions.
5. Pareto chart and main effect plots, rendered inline.
6. Optimal-level identification and additive-model prediction.
7. Save / load for reproducibility.

Open with:

```bash
cd examples/
jupyter notebook tagupy_example.ipynb
```

A pre-saved archive is included as `examples/shm_taguchi_experiment.zip` so you can jump straight to the analysis section without re-running the surrogate.

## Reusable patterns

### Single-response, single-repetition

```python
design = TaguchiDesign({"A": [10, 20], "B": [0, 1]}, assignation=[0, 1], matrix="L8")
design.run(lambda f: {"y": f[0] * 2 + f[1] * 5}, responses=["y"])
design.analyze()
```

### Multiple responses

```python
design.run(my_func, responses=["accuracy", "loss", "latency"])
design.analyze()
design.pareto_plot()
```

### Repetitions with stochastic functions

```python
def stochastic(factors):
    *vals, rep = factors            # rep is the repetition index
    return {"score": noisy_eval(vals)}

design.run(stochastic, responses=["score"], repetitions=3)
```

The library appends per-rep columns (`score (Repetition 0)`, …) plus `score average` and `score standard deviation`.

### Long experiments with checkpointing

```python
design.run(
    expensive_train,
    responses=["accuracy"],
    progress_path="run_checkpoint.csv",
)
```

If `expensive_train` raises, the partial results are dumped to `run_checkpoint.emergency.csv` before the exception propagates.

### Pulling external measurements into the library

If you ran the experiments outside Python, use the MCP server's `add_results` tool — see [[MCP Server]] — or directly call the helper:

```python
from tagupy_mcp.tools import _add_results_to_design
_add_results_to_design(design, {"accuracy": [...]}, repetitions=1)
design.analyze()
```
