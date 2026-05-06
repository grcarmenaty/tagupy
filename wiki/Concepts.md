# Concepts

This page explains the vocabulary used throughout the library: orthogonal arrays, factor letters, interactions, the analysis output, and the additive model.

## Orthogonal arrays

A two-level orthogonal array is a balanced experimental matrix. Each column represents one of two levels (`"Low level"` or `"High level"`), and across any pair of columns every Low/High combination appears the same number of times. This balance is what makes effects estimable from a small fraction of the full factorial grid.

| Array | Runs | Columns | Max main factors |
|---|---|---|---|
| L8 | 8 | 7 | 7 |
| L16 | 16 | 15 | 15 |
| L32 | 32 | 31 | 31 |
| L32-inv | 32 | 31 | 31 (Low/High swapped vs L32) |

A full factorial for 7 two-level factors needs 2⁷ = 128 runs. L8 reduces this to 8 — at the cost of confounding interactions with main effects (resolution III). L16 and L32 give progressively higher resolution and let you study two-factor interactions.

See [[Orthogonal Arrays]] for full specifications.

## Factor letters and assignation

When you create a design, factors are mapped onto array columns in two stages:

1. **Letter assignment** — the *order of keys* in `experimental_design` determines the letter:
   first key → `A`, second → `B`, third → `C`, …
2. **Column assignment** — the `assignation` argument is the list of zero-based column indices the letters claim:
   ```python
   TaguchiDesign(
       {"LR": [...], "BS": [...], "EP": [...]},   # A=LR, B=BS, C=EP
       assignation=[0, 3, 5],                      # A→col 0, B→col 3, C→col 5
       matrix="L8",
   )
   ```

After construction, `design.columns` lists every column label: single letters for assigned factors (e.g. `"A"`, `"B"`), two-letter labels for two-factor interactions (e.g. `"AB"`, `"AC"`), and string-numeric labels for unused columns.

## Interactions

For each ordered pair of factor letters, the library consults the array's **assignation table** to find the column that holds their interaction, and renames it to e.g. `"AB"`. If that interaction column was already claimed by a main factor, the rename is a no-op — the interaction is *confounded* with that factor (correct behaviour for saturated designs, but a warning that you cannot disentangle the two effects from this design alone).

Tip: place main factors on columns that produce *distinct* interaction columns. The README example uses `[0, 2, 4, 6]` on L16 because that pattern gives independent two-factor interactions.

## The experimental matrix

`design.experimental_matrix` is a DataFrame holding the *values* (not Low/High strings) of each factor for each run. This is the matrix you actually go and execute in the lab or simulator.

`design.taguchi_design` is more bookkeeping: before `run()` it is the raw orthogonal array with letter renames; after `run()` it becomes a `dict[response → DataFrame]` carrying both the design and the measured values.

## Repetitions

Setting `repetitions > 1` causes `run()` to call your objective `r` times per row and store each rep in its own column (e.g. `"accuracy (Repetition 0)"`), plus per-row `average` and `standard deviation` columns. The downstream analysis uses the average column as the response.

## Analysis output

`design.analyze()` appends an `"analysis"` row plus, for every column `c`, five new columns:

| Column | Meaning |
|---|---|
| `c (Low)` | Mean response for runs where column `c` is at Low level |
| `c (High)` | Mean response for runs where column `c` is at High level |
| `c Effect` | `c (High) − c (Low)` |
| `c SS` | `Effect²` (sum of squares for column `c`) |
| `c Contribution` | `c SS` as a percentage of total SS |

Contributions sum to 100 % across all columns (or 0 % if total SS is zero).

## The additive model

For "larger-is-better" optimisation, the predicted optimum is

```
ŷ_opt  =  grand_mean  +  Σ_factors  (best_level_mean − grand_mean)
```

i.e. the grand mean plus, for every main factor, the deviation that its best level produces. This is the value `get_optimal_levels` and the `tagupy_mcp.tools._compute_optimal_levels` helper return as `additive_model_prediction`. It assumes interactions are negligible — the Pareto chart helps you check whether that assumption holds for your data.

## Glossary

- **Run / experience / trial** — one row of the design (one factor combination to test).
- **Response** — what you measure (`accuracy`, `loss`, `inference_time_ms`, …).
- **Effect** — change in mean response when a column moves from Low to High.
- **Sum of squares (SS)** — squared effect, used to rank columns.
- **Contribution %** — SS as a percentage of total SS.
- **Saturated design** — every column carries a factor; no degrees of freedom left for residual error.
- **Confounding / aliasing** — two effects share a column and cannot be separated from this design.
