# FAQ

## Why use Taguchi designs instead of grid / random search?

A two-level orthogonal array reduces the experimental cost from `2^n` (full factorial) to a fixed array size while still recovering every main effect — and, for L16/L32, the two-factor interactions you choose to study. For 7 factors you go from 128 runs to 8; for 15 factors from 32 768 to 16. This matters when each "run" is an expensive CNN training job or a physical lab experiment.

## How do I pick `assignation`?

1. Pick the array with [[Orthogonal Arrays]].
2. Inspect `get_assignation(name)` to see which columns hold which interactions.
3. Place factors so that important pairwise interactions land on free columns. For four factors on L16, `[0, 2, 4, 6]` is a known-good pattern.

If two factors share an interaction column, the rename is silently a no-op and the interaction becomes confounded with that factor — a common surprise.

## What does the dict order in `experimental_design` control?

It determines factor letters. The first key becomes `A`, the second `B`, and so on. The `assignation` list then maps each letter to a column index in the orthogonal array. Re-ordering the keys changes which letter each factor uses (and therefore the labels you'll see in plots and analyses), but it does not change the experimental matrix once the assignation is matched.

## I get `RuntimeError: analyze() must be called after run()`

You must call `run()` (or, in MCP, `add_results`) *before* `analyze()`. The library enforces ordering because `analyze()` reads response columns that only exist after a run.

## Pareto / effect plots fail with "requires run() and analyze()"

Same root cause — call them after `analyze()`.

## My emergency CSV file appeared in the working directory

That's by design. When `func` raises during `run()` and no `progress_path` was supplied, the library writes `./emergency_save.csv` so partial results aren't lost, then re-raises the exception. Pass `progress_path="some/checkpoint.csv"` to control where it lands; the emergency save sits next to it as `some/checkpoint.emergency.csv`.

## Save / load lost my integer index

CSV serialisation turns row indices into strings. The classmethod `TaguchiDesign.load()` calls `_restore_index()` to reverse this for the experimental rows, leaving the `"analysis"` summary row as a string. If you bypass `load()` and read the CSVs directly, you'll see string indices.

## Can I have more than two levels per factor?

Not with the current arrays. Only two-level designs are supported. Three-level support (L9, L18, L27) is on the [[Contributing]] wishlist.

## How do I expose this to Claude Desktop?

Install the MCP extra (`pip install -e ".[mcp]"`), point Claude Desktop's `claude_desktop_config.json` at the `tagupy-mcp` console script, and restart. See [[MCP Server]] for the JSON snippet and full troubleshooting.

## Where are the plots saved?

By default, `pareto_plot()` writes to `./pareto_plots/` and `effect_plots()` writes to `./effect_plots/`. Pass `path=...` to customise. The MCP server's plot tools default to `./tagupy_plots/<experiment_id>/<effects|pareto>/`.

## My `additive_model_prediction` doesn't match what I see in the data

The additive model assumes interactions are negligible. If your Pareto chart shows a two-letter column (`AB`, `AC`, …) carrying significant contribution, the prediction will diverge from reality. Either pick column placements that disentangle the interaction, or use a higher-resolution array like L32.

## How do I cite the library?

```bibtex
@software{reyes_taguchi_2025,
  author = {Reyes-Carmenaty, Guillermo},
  title  = {taguchi: Taguchi Design of Experiments Library},
  year   = {2025},
}
```
