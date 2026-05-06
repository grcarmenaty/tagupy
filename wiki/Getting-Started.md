# Getting Started

This page walks you from a fresh clone to a complete experiment in roughly five minutes.

## Requirements

- Python ≥ 3.9
- numpy ≥ 1.24
- pandas ≥ 2.0
- matplotlib ≥ 3.7

The MCP server additionally requires `mcp ≥ 1.0` (Python ≥ 3.10).

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/grcarmenaty/tagupy.git
cd tagupy
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dev]"   # adds pytest + pytest-cov for the test suite
pip install -e ".[mcp]"   # adds the mcp SDK for the MCP server
```

After installing the `mcp` extra, the `tagupy-mcp` console script becomes available on your `PATH`.

## Smoke test

Verify the import works:

```bash
python -c "from taguchi import TaguchiDesign, AVAILABLE_ARRAYS; print(AVAILABLE_ARRAYS)"
# ['L8', 'L16', 'L32', 'L32-inv']
```

## Run the bundled example

A minimal end-to-end script lives in `examples/basic_usage.py`. It defines four CNN-style hyperparameters, runs a noisy mock objective, analyses the results, and writes both Pareto and effect plots to disk:

```bash
python examples/basic_usage.py
```

Expected artefacts:

- `pareto_plots/accuracy.png`, `pareto_plots/loss.png`
- `effect_plots/accuracy-A.png`, `effect_plots/accuracy-B.png`, …
- `example_design.zip` — full design state, reloadable with `TaguchiDesign.load()`.

## Notebook walkthrough

For a publication-quality narrative (the workflow that motivated the library — CNN transfer learning for vibration-based SHM), open the Jupyter notebook:

```bash
cd examples/
jupyter notebook tagupy_example.ipynb
```

It uses a fast `scikit-learn` surrogate so it runs on any machine with no GPU.

## Next steps

- Read [[Concepts]] to understand orthogonal arrays, factor letters, interactions, and the additive model.
- Skim [[Workflow]] for the canonical design → run → analyse → plot → save sequence.
- Browse [[API Reference]] for full method signatures.
