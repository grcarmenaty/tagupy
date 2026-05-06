# Orthogonal Arrays

The library ships four built-in two-level orthogonal arrays. All array data and interaction tables live in `taguchi/arrays.py`. Arrays are stored as immutable raw dicts and rebuilt as fresh DataFrames on every access — multiple `TaguchiDesign` instances cannot accidentally mutate shared state.

## Public API

| Symbol | Description |
|---|---|
| `AVAILABLE_ARRAYS` | `['L8', 'L16', 'L32', 'L32-inv']` |
| `get_array(name)` | Fresh `pd.DataFrame` of the chosen array (rows = runs, cols = column indices) |
| `get_assignation(name)` | Fresh `pd.DataFrame` of the interaction-assignation table |

```python
from taguchi.arrays import AVAILABLE_ARRAYS, get_array, get_assignation

print(AVAILABLE_ARRAYS)            # ['L8', 'L16', 'L32', 'L32-inv']
oa = get_array("L8")               # 8-row × 7-col DataFrame of 'Low level' / 'High level'
ass = get_assignation("L8")        # 6-row × 6-col interaction lookup
```

Both functions raise `ValueError` for unknown names.

## Array specifications

### L8 — 8 runs, up to 7 factors

Resolution III. Best for quick screening with 3–7 factors when interactions can be ignored. Every two-factor interaction is aliased with at least one main effect.

```
Runs:    8
Columns: 7   (indices 0..6)
```

### L16 — 16 runs, up to 15 factors *(most common choice)*

Resolution IV when fewer than 8 main factors are used. Allows estimating two-factor interactions via the assignation table. Default array used by `TaguchiDesign(..., matrix="L16")`.

```
Runs:    16
Columns: 15  (indices 0..14)
```

Independent two-factor interaction columns can be obtained for many factor combinations — e.g. assigning factors to columns `[0, 2, 4, 6]` keeps their pairwise interactions on distinct columns.

### L32 — 32 runs, up to 31 factors

For studies needing higher resolution or more factors than L16 supports. 31 estimable degrees of freedom.

### L32-inv — 32 runs, inverted levels

Structurally identical to L32 but with every Low/High swapped. Useful when:
- The baseline configuration corresponds to "High" of every factor.
- You want to verify analysis robustness by inverting all levels.

## The interaction assignation table

`get_assignation(name)` returns a square-ish lookup whose `[i, j]` entry is the column that holds the interaction of the factors in columns `i` and `j` (1-based for compatibility with classical Taguchi tables; the library handles the offset internally).

`TaguchiDesign.__init__` walks this table for each ordered factor-letter pair and renames the matching column to the `"AB"`/`"AC"`/… form. If the interaction column has already been assigned to a main factor, the rename is a no-op — meaning the interaction is *confounded* with that factor.

## Choosing an array

| Situation | Recommended array |
|---|---|
| 3–7 main factors, no interactions of interest | L8 |
| 4–8 main factors, want to study some 2-factor interactions | L16 |
| Up to 15 factors, can afford 16 runs | L16 |
| 9–15 main factors, want clean 2-factor interactions | L32 |
| Default level inverted (baseline = "High") | L32-inv |

## Constructing custom assignments

The assignation table is the source of truth for which column hides which interaction. To pick *non-confounded* main-effect placements:

1. Look at the assignation table for your chosen array.
2. Pick column indices for your factors such that the interaction columns they generate are distinct from any other factor column.

A reliable pattern for L16 is `[0, 2, 4, 6]` for four factors (gives independent two-factor interactions on columns 1, 3, 5, 7).
