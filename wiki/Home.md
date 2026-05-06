# tagupy Wiki

**tagupy** is a production-quality Python library for [Taguchi Design of Experiments](https://en.wikipedia.org/wiki/Taguchi_methods) using two-level orthogonal arrays. It is targeted at hyperparameter optimisation in deep learning and other scientific research workflows where running every factor combination is infeasible.

The repository ships **two complementary entry points**:

| Package | What it provides |
|---|---|
| `taguchi` | The core Python library — `TaguchiDesign` class, orthogonal-array data, plotting helpers. |
| `tagupy_mcp` | A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the library as AI-callable tools (Claude Desktop, Open WebUI, Continue.dev, …). |

## Pages

- [[Getting Started]] — install, run the example, understand the output.
- [[Concepts]] — orthogonal arrays, factor levels, interactions, additive model.
- [[API Reference]] — every public class, method, and module.
- [[Orthogonal Arrays]] — L8 / L16 / L32 / L32-inv specifications and selection guide.
- [[Workflow]] — end-to-end recipe: design → run → analyze → plot → save/load.
- [[MCP Server]] — exposing tagupy to AI assistants.
- [[Examples]] — notebook walkthrough and minimal scripts.
- [[Testing]] — running the test suite and what each module covers.
- [[Contributing]] — coding conventions and how to submit changes.
- [[FAQ]] — common pitfalls and questions.

## At a glance

```python
from taguchi import TaguchiDesign

design = TaguchiDesign(
    {"Learning rate": [1e-4, 1e-3],
     "Batch size":    [16, 64],
     "Num filters":   [16, 64],
     "Dropout":       [0.2, 0.5]},
    assignation=[0, 2, 4, 6],
    matrix="L16",
)

design.run(my_train_fn, responses=["accuracy", "loss"], repetitions=2)
design.analyze()
design.pareto_plot()
design.effect_plots()
design.save("experiment.zip")
```

16 runs replace 2⁴ × 2 = 32 full-factorial combinations and still recover every main effect plus the key two-factor interactions.

## Citation

```bibtex
@software{reyes_taguchi_2025,
  author = {Reyes-Carmenaty, Guillermo},
  title  = {taguchi: Taguchi Design of Experiments Library},
  year   = {2025},
}
```

Maintained by **Guillermo Reyes-Carmenaty** — Institut Químic de Sarrià (IQS), Universitat Ramon Llull, Barcelona, Spain.
