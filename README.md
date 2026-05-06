# taguchi - Taguchi Design of Experiments Library

A production-quality Python library for Taguchi experimental design, orthogonal arrays, and signal-to-noise analysis. Designed for hyperparameter optimization in deep learning and other scientific research applications.

## Overview

This library implements Taguchi's Design of Experiments (DOE) methodology, enabling efficient exploration of experimental factor spaces using orthogonal arrays. It is particularly useful for CNN hyperparameter tuning in vibration-based structural health monitoring (SHM) research.

### Key Features

- **Four orthogonal arrays**: L8, L16, L32, L32-inv for two-level factorial designs
- **Robust run execution**: Progress checkpointing, emergency saves, and error handling
- **Comprehensive analysis**: Main effects, interaction effects, factor contributions
- **Visualization tools**: Pareto charts and main effect plots
- **Save/load functionality**: Archive designs as zip files for reproducibility
- **Repetition support**: Built-in handling of repeated measurements
- **pandas 2.0+ compatible**: Uses modern pandas APIs

## Installation

Install from the source directory:

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from taguchi import TaguchiDesign
import numpy as np

# Define experimental factors
design_spec = {
    "Learning rate": [1e-4, 1e-3],
    "Batch size": [16, 64],
    "Num filters": [16, 64],
    "Dropout": [0.2, 0.5],
}

# Create L16 design
design = TaguchiDesign(design_spec, assignation=[0, 2, 4, 6], matrix="L16")

# Run experiments
def objective(factors):
    """Simulate training and return metrics."""
    lr, batch, filters, dropout = factors[:4]
    accuracy = 0.5 + 0.2 * lr + 0.1 * (batch / 32)
    return {"accuracy": accuracy, "loss": 1.0 - accuracy}

design.run(objective, responses=["accuracy", "loss"], repetitions=2)

# Analyze and visualize
design.analyze()
design.pareto_plot(path="./pareto_plots")
design.effect_plots(path="./effect_plots")

# Save for later
design.save("my_experiment.zip")
```

## API Reference

### TaguchiDesign Class

Main class for managing Taguchi experimental designs.

| Method | Description |
|--------|-------------|
| `__init__(experimental_design, assignation, matrix="L16")` | Initialize design with factors and orthogonal array |
| `run(func, responses, randomize=False, repetitions=1, progress_path=None)` | Execute experiments by calling func for each run |
| `analyze()` | Compute factor effects and variability contributions |
| `pareto_plot(title=None, path="./pareto_plots", font_family="Liberation Serif", font_size=12)` | Generate Pareto contribution charts |
| `effect_plots(limits=None, percentage=None, path="./effect_plots", font_family="Liberation Serif", font_size=12)` | Generate main effect plots |
| `save(path)` | Save design state to zip archive |
| `load(path)` (classmethod) | Load previously saved design from zip archive |

### Arrays Module

Access orthogonal array data.

| Function | Description |
|----------|-------------|
| `get_array(name: str) -> pd.DataFrame` | Get a fresh copy of orthogonal array (L8, L16, L32, L32-inv) |
| `get_assignation(name: str) -> pd.DataFrame` | Get interaction assignation table for array |
| `AVAILABLE_ARRAYS` | List of supported array names |

### Plotting Module

Convenience wrappers for visualization.

| Function | Description |
|----------|-------------|
| `pareto_plot(design, **kwargs)` | Convenience wrapper for design.pareto_plot() |
| `effect_plots(design, **kwargs)` | Convenience wrapper for design.effect_plots() |

## Supported Orthogonal Arrays

- **L8**: 8 runs, 7 factors (2-level)
- **L16**: 16 runs, 15 factors (2-level)
- **L32**: 32 runs, 31 factors (2-level)
- **L32-inv**: Inverted L32 array (31 factors, 32 runs)

## Research Context

This library is designed for:

**Taguchi experimental design for CNN transfer learning hyperparameter optimization in vibration-based structural health monitoring (SHM)**

The methodology enables efficient exploration of hyperparameter spaces such as:
- Learning rate (pre-training vs. fine-tuning)
- Batch size (memory constraints, convergence)
- Network width (filter counts)
- Regularization (dropout, L1/L2)
- Training dynamics (epochs, early stopping)

By using orthogonal arrays, the library reduces the experimental runs needed from 2^n (full factorial) to a carefully chosen subset while maintaining the ability to estimate main effects and key interactions.

## Example Workflow

Two ready-to-run examples are provided in `examples/`:

### Jupyter notebook — `examples/tagupy_example.ipynb` ⭐ recommended

A publication-quality walkthrough of the full workflow, directly inspired by the SHM
paper that motivated this library. Covers:

1. Defining factors and levels (CFDAC vs FRF, ResNet-18 vs ResNet-34, frequency lines, learning rate)
2. Generating and inspecting the L8 orthogonal array
3. Running experiments via a fast `scikit-learn` surrogate (runnable on any machine, no GPU required)
4. Signal-to-noise analysis — factor effects, sums of squares, percentage contributions
5. Pareto chart and main effect plots, rendered inline
6. Optimal-level identification and additive-model prediction
7. Save / load for reproducibility

Open with Jupyter:
```bash
cd examples/
jupyter notebook tagupy_example.ipynb
```

### Python script — `examples/basic_usage.py`

Minimal script demonstrating the core API. Runs from the command line:

```bash
python examples/basic_usage.py
```

## Requirements

- Python 3.9+
- numpy >= 1.24.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0

## Testing

Run tests with pytest:

```bash
pytest tests/
pytest tests/ -v --cov=taguchi
```

Test modules cover:
- Array data integrity and isolation
- Design initialization and validation
- Experiment execution and error handling
- Analysis correctness and numerical accuracy
- Save/load functionality

## Implementation Notes

### Design Principles

1. **Immutability**: Orthogonal arrays stored as immutable module-level data; fresh copies provided on each access
2. **Pandas 2.0+ compatibility**: No deprecated APIs (append, inplace=True on Series.replace)
3. **Progress checkpointing**: Long experiments can be resumed from checkpoints
4. **Isolation**: Multiple design instances do not share state

### Bug Fixes from Original Code

This refactored version fixes several issues present in the original research code:

1. Eliminated `pd.DataFrame.append()` (removed in pandas 2.0)
2. Removed `inplace=True` from Series operations
3. Fixed mean calculation bug: `np.mean(repetition_values)` instead of `np.mean(repetition_values[row])`
4. Protected orthogonal array data from accidental mutation via `.copy()`
5. Made progress/emergency save paths configurable
6. Replaced temp file usage in save() with `zipfile.writestr()`
7. Replaced hacky dummy init in load() with classmethod and `__new__()`
8. Fixed variable name collision in pareto plot generation
9. Ensured DataFrame references are copied per response in run()

## Citation

If you use this library in your research, please cite:

```bibtex
@software{reyes_taguchi_2025,
  author = {Reyes-Carmenaty, Guillermo},
  title = {taguchi: Taguchi Design of Experiments Library},
  year = {2025},
  url = {https://github.com/yourusername/taguchi}
}
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome. Please ensure:
- All tests pass: `pytest tests/`
- Code follows PEP 8
- Docstrings in NumPy format
- Type hints on all public functions

## Contact

Guillermo Reyes-Carmenaty (grcarmenaty@gmail.com)

Institut Químic de Sarrià (IQS), Universitat Ramon Llull, Barcelona, Spain
