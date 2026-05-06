"""Tagupy MCP tool and resource definitions.

All eleven MCP tools and two MCP resources are registered here via
``register_tools(mcp)`` and ``register_resources(mcp)``.  The module also
owns the in-memory experiment store (``_EXPERIMENTS``) that maps UUID strings
to running experiment state.

In-memory store layout
----------------------
Each entry in ``_EXPERIMENTS`` is a plain dict::

    {
        "name":       str,              # human label supplied at creation
        "design":     TaguchiDesign,    # live object
        "created_at": str,              # ISO-8601 timestamp
        "state":      str,              # "created" | "has_results" | "analyzed"
        "plot_dir":   str,              # last output dir used for plots
    }
"""

from __future__ import annotations

import json
import math
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd

from taguchi import TaguchiDesign
from taguchi.arrays import AVAILABLE_ARRAYS, get_array, get_assignation

# ---------------------------------------------------------------------------
# In-memory experiment store
# ---------------------------------------------------------------------------

_EXPERIMENTS: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Metadata about available arrays (used by list_arrays + resource)
# ---------------------------------------------------------------------------

_ARRAY_META: dict[str, dict[str, Any]] = {
    "L8": {
        "runs": 8,
        "columns": 7,
        "max_factors": 7,
        "recommended_max_main_effects": 7,
        "description": (
            "8-run two-level array. Supports up to 7 factors (columns 0-6). "
            "Commonly used for 3–7 factors when interactions are not of primary interest. "
            "Runs 8 experiments — ideal for quick screening."
        ),
    },
    "L16": {
        "runs": 16,
        "columns": 15,
        "max_factors": 15,
        "recommended_max_main_effects": 15,
        "description": (
            "16-run two-level array. Supports up to 15 factors (columns 0-14). "
            "The most commonly used array for 4–15 factors. Allows studying 2-factor "
            "interactions using the assignation table."
        ),
    },
    "L32": {
        "runs": 32,
        "columns": 31,
        "max_factors": 31,
        "recommended_max_main_effects": 31,
        "description": (
            "32-run two-level array. Supports up to 31 factors (columns 0-30). "
            "Used when L16 does not provide enough resolution or when many factors "
            "and interactions must be accommodated simultaneously."
        ),
    },
    "L32-inv": {
        "runs": 32,
        "columns": 31,
        "max_factors": 31,
        "recommended_max_main_effects": 31,
        "description": (
            "32-run two-level array with inverted levels (Low↔High swapped relative "
            "to L32). Structurally identical to L32 but useful when the baseline "
            "configuration should be the 'High level' of each factor, or to verify "
            "analysis by level inversion."
        ),
    },
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_experiment(experiment_id: str) -> dict[str, Any]:
    """Return the experiment record or raise a descriptive ValueError."""
    if experiment_id not in _EXPERIMENTS:
        raise ValueError(
            f"Experiment '{experiment_id}' not found. "
            f"Available IDs: {list(_EXPERIMENTS.keys()) or '(none yet)'}. "
            "Use create_experiment or load_experiment first."
        )
    return _EXPERIMENTS[experiment_id]


def _n_runs(design: TaguchiDesign) -> int:
    """Return the number of experimental runs, safe for load()-restored designs."""
    # `experiences` is set by __init__ but NOT by the classmethod load() which
    # calls __new__ directly.  Fall back to experimental_matrix row count.
    if hasattr(design, "experiences"):
        return len(design.experiences)
    return len(design.experimental_matrix)


def _design_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serialisable summary dict for an experiment record."""
    design: TaguchiDesign = record["design"]
    return {
        "experiment_id": record["experiment_id"],
        "name": record["name"],
        "state": record["state"],
        "created_at": record["created_at"],
        "matrix": design.matrix_name,
        "n_runs": _n_runs(design),
        "n_factors": len(design.experimental_design),
        "factors": {
            k: {"low": v[0], "high": v[1]}
            for k, v in design.experimental_design.items()
        },
        "assignation": design.assignation,
        "responses": design.responses,
        "repetitions": design.repetitions,
        "columns": design.columns,
    }


def _matrix_to_json(design: TaguchiDesign) -> list[dict[str, Any]]:
    """Convert experimental_matrix to a list of run dicts."""
    rows = []
    for run_idx, row in design.experimental_matrix.iterrows():
        entry: dict[str, Any] = {"run": int(run_idx)}
        entry.update({str(k): v for k, v in row.items()})
        rows.append(entry)
    return rows


def _add_results_to_design(
    design: TaguchiDesign,
    results: dict[str, list],
    repetitions: int = 1,
) -> None:
    """Populate *design* with externally-measured results (bypasses run()).

    This replicates the internal state changes that ``TaguchiDesign.run()``
    performs, so that ``analyze()``, ``pareto_plot()``, and ``effect_plots()``
    all work correctly afterwards.

    Parameters
    ----------
    design : TaguchiDesign
        A freshly created design whose ``taguchi_design`` is still a DataFrame
        (i.e., ``run()`` has not been called yet).
    results : dict[str, list]
        Mapping of response name to measured values.  For ``repetitions=1``,
        each value is a ``float`` and the list length must equal the number of
        runs.  For ``repetitions>1``, each value is a ``list[float]`` of
        length ``repetitions`` and the outer list length must equal the number
        of runs.
    repetitions : int, optional
        Number of replications per run.  Default ``1``.

    Raises
    ------
    ValueError
        If ``results`` is empty, lengths mismatch, or results have already
        been added to this design.
    RuntimeError
        If ``design.taguchi_design`` is already a dict (``run()`` already
        called or ``add_results`` called twice).
    """
    if isinstance(design.taguchi_design, dict):
        raise RuntimeError(
            "Results have already been added to this design. "
            "To re-enter results, create a new experiment with create_experiment."
        )

    if not results:
        raise ValueError("results dict must not be empty.")

    exp_indices = design.experimental_matrix.index.tolist()
    n_runs = len(exp_indices)

    design.responses = list(results.keys())
    design.repetitions = repetitions

    new_taguchi_design: dict[str, pd.DataFrame] = {}

    for response, values in results.items():
        df = design.taguchi_design.copy()

        if repetitions == 1:
            flat = list(values)
            if len(flat) != n_runs:
                raise ValueError(
                    f"Response '{response}': expected {n_runs} values "
                    f"(one per run), got {len(flat)}."
                )
            df[response] = np.nan
            for idx, val in zip(exp_indices, flat):
                try:
                    df.loc[idx, response] = float(val)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Response '{response}', run {idx}: "
                        f"cannot convert {val!r} to float — {exc}"
                    ) from exc

        else:
            nested = list(values)
            if len(nested) != n_runs:
                raise ValueError(
                    f"Response '{response}': expected {n_runs} rows "
                    f"(one per run), got {len(nested)}."
                )
            for rep in range(repetitions):
                df[f"{response} (Repetition {rep})"] = np.nan
            df[f"{response} average"] = np.nan
            df[f"{response} standard deviation"] = np.nan

            for idx, row_vals in zip(exp_indices, nested):
                if len(row_vals) != repetitions:
                    raise ValueError(
                        f"Response '{response}', run {idx}: "
                        f"expected {repetitions} repetition values, "
                        f"got {len(row_vals)}."
                    )
                row_arr = np.array(row_vals, dtype=float)
                for rep in range(repetitions):
                    df.loc[idx, f"{response} (Repetition {rep})"] = float(row_arr[rep])
                df.loc[idx, f"{response} average"] = float(np.mean(row_arr))
                df.loc[idx, f"{response} standard deviation"] = float(np.std(row_arr))

        new_taguchi_design[response] = df

    design.taguchi_design = new_taguchi_design


def _get_analysis_table(
    design: TaguchiDesign,
    response: str,
) -> dict[str, Any]:
    """Extract the analysis row from ``design.taguchi_design[response]``.

    Returns a structured dict with per-column statistics, grand mean,
    and the additive model details.
    """
    df = design.taguchi_design[response]
    analysis_row = df.loc["analysis"]

    exp_index = [i for i in df.index if i != "analysis"]

    if design.repetitions <= 1:
        data_col = response
    else:
        data_col = f"{response} average"

    # Grand mean over all experimental runs
    numeric_vals = pd.to_numeric(df.loc[exp_index, data_col], errors="coerce")
    grand_mean = float(np.nanmean(numeric_vals))

    columns_info: dict[str, Any] = {}
    total_ss = float(np.nansum(
        [float(analysis_row.get(f"{col} SS", np.nan)) for col in design.columns]
    ))

    for col in design.columns:
        low_avg = float(analysis_row.get(f"{col} (Low)", np.nan))
        high_avg = float(analysis_row.get(f"{col} (High)", np.nan))
        effect = float(analysis_row.get(f"{col} Effect", np.nan))
        ss = float(analysis_row.get(f"{col} SS", np.nan))
        contrib = float(analysis_row.get(f"{col} Contribution", np.nan))

        is_main_factor = len(col) == 1 and col.isalpha()
        factor_name: Optional[str] = None
        if is_main_factor:
            factor_idx = ord(col) - 65
            factor_keys = list(design.experimental_design.keys())
            if factor_idx < len(factor_keys):
                factor_name = factor_keys[factor_idx]

        columns_info[col] = {
            "type": "main_factor" if is_main_factor else "interaction",
            "factor_name": factor_name,
            "low_avg": None if math.isnan(low_avg) else low_avg,
            "high_avg": None if math.isnan(high_avg) else high_avg,
            "effect": None if math.isnan(effect) else effect,
            "ss": None if math.isnan(ss) else ss,
            "contribution_pct": None if math.isnan(contrib) else contrib,
        }

    return {
        "response": response,
        "grand_mean": grand_mean,
        "total_ss": total_ss if not math.isnan(total_ss) else None,
        "columns": columns_info,
    }


def _compute_optimal_levels(
    design: TaguchiDesign,
    response: str,
    optimize: str = "maximize",
) -> dict[str, Any]:
    """Compute the optimal factor-level combination using the additive model.

    Parameters
    ----------
    design : TaguchiDesign
        A design that has been both run and analysed.
    response : str
        The response variable to optimise.
    optimize : str
        ``'maximize'`` (default) or ``'minimize'``.

    Returns
    -------
    dict
        Keys: ``grand_mean``, ``optimal_levels``, ``additive_model_prediction``.
    """
    analysis_table = _get_analysis_table(design, response)
    grand_mean = analysis_table["grand_mean"]

    factor_letters = [
        col for col in design.columns
        if len(col) == 1 and col.isalpha()
    ]

    optimal_levels: dict[str, Any] = {}
    additive_correction = 0.0

    for col in factor_letters:
        info = analysis_table["columns"][col]
        low_avg = info["low_avg"]
        high_avg = info["high_avg"]

        if low_avg is None or high_avg is None:
            continue

        factor_idx = ord(col) - 65
        factor_keys = list(design.experimental_design.keys())
        factor_name = factor_keys[factor_idx] if factor_idx < len(factor_keys) else col
        low_val, high_val = design.experimental_design[factor_name]

        if optimize == "maximize":
            if high_avg >= low_avg:
                chosen_level, chosen_avg, chosen_val = "High", high_avg, high_val
            else:
                chosen_level, chosen_avg, chosen_val = "Low", low_avg, low_val
        else:  # minimize
            if low_avg <= high_avg:
                chosen_level, chosen_avg, chosen_val = "Low", low_avg, low_val
            else:
                chosen_level, chosen_avg, chosen_val = "High", high_avg, high_val

        additive_correction += chosen_avg - grand_mean

        optimal_levels[factor_name] = {
            "column": col,
            "optimal_level": chosen_level,
            "optimal_value": chosen_val,
            "low_value": low_val,
            "high_value": high_val,
            "low_avg_response": low_avg,
            "high_avg_response": high_avg,
            "delta": high_avg - low_avg,
        }

    prediction = grand_mean + additive_correction

    return {
        "grand_mean": grand_mean,
        "optimization": optimize,
        "additive_model_prediction": prediction,
        "optimal_levels": optimal_levels,
    }


# ---------------------------------------------------------------------------
# Tool / resource registration
# ---------------------------------------------------------------------------


def register_tools(mcp: Any) -> None:
    """Register all Tagupy MCP tools on *mcp* (a ``FastMCP`` instance).

    Call this once from ``server.py`` after creating the ``FastMCP`` object.
    """

    # ------------------------------------------------------------------
    # Tool 1 — create_experiment
    # ------------------------------------------------------------------

    @mcp.tool()
    def create_experiment(
        factors: dict[str, list],
        assignation: list[int],
        matrix: str = "L16",
        name: str = "",
    ) -> str:
        """Create a new Taguchi experiment and return its ID.

        Defines the experimental factors and their two levels, selects an
        orthogonal array, and assigns each factor to a specific column.  No
        actual experiments are run at this stage — use ``add_results`` to
        supply measured data and ``analyze`` to compute factor effects.

        Args:
            factors: Ordered dict mapping each factor name to a two-element
                list ``[low_value, high_value]``.  Example::

                    {
                        "Learning rate": [0.0001, 0.001],
                        "Batch size":    [16, 64],
                        "Dropout":       [0.2, 0.5]
                    }

                The order of keys determines the factor-letter assignment
                (first key → A, second → B, etc.).

            assignation: Zero-based column indices in the orthogonal array to
                assign factors to.  Length must equal ``len(factors)``.
                Use ``list_arrays`` or ``get_orthogonal_array`` (without an
                experiment ID) to inspect which columns are available and
                what their interaction structure looks like.  Example for 3
                non-interacting factors on L8: ``[0, 3, 5]``.

            matrix: Orthogonal array name.  One of ``"L8"`` (8 runs, ≤7
                factors), ``"L16"`` (16 runs, ≤15 factors), ``"L32"`` (32
                runs, ≤31 factors), or ``"L32-inv"`` (32 runs, inverted
                levels).  Default ``"L16"``.

            name: Optional human-readable label for this experiment.  Has no
                effect on computation.  Default ``""``.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str) — UUID to pass to all subsequent tools.
            * ``name`` (str)
            * ``matrix`` (str)
            * ``n_runs`` (int) — total number of trial runs.
            * ``n_factors`` (int)
            * ``factors`` (dict) — echo of the factor definitions.
            * ``assignation`` (list[int])
            * ``columns`` (list[str]) — all column labels in the design,
              including interaction columns named like ``"AB"``.
            * ``experimental_matrix`` (list[dict]) — the full run matrix
              showing actual factor values for each run.

        Raises:
            ValueError: If ``matrix`` is unknown, ``assignation`` length
                mismatches ``factors``, or any column index is out of range.
        """
        if matrix not in AVAILABLE_ARRAYS:
            raise ValueError(
                f"Unknown matrix '{matrix}'. "
                f"Available: {AVAILABLE_ARRAYS}. "
                "Use list_arrays for details."
            )

        n_factors = len(factors)
        if n_factors == 0:
            raise ValueError("factors must contain at least one entry.")
        if len(assignation) != n_factors:
            raise ValueError(
                f"len(assignation)={len(assignation)} but "
                f"len(factors)={n_factors}. They must be equal."
            )

        max_col = _ARRAY_META[matrix]["columns"] - 1
        for col_idx in assignation:
            if not (0 <= col_idx <= max_col):
                raise ValueError(
                    f"Column index {col_idx} is out of range for {matrix} "
                    f"(valid range: 0–{max_col})."
                )
        if len(set(assignation)) != len(assignation):
            raise ValueError("assignation contains duplicate column indices.")

        for fname, levels in factors.items():
            if len(levels) != 2:
                raise ValueError(
                    f"Factor '{fname}' must have exactly 2 levels "
                    f"[low, high], got {len(levels)}."
                )

        design = TaguchiDesign(
            experimental_design=factors,
            assignation=assignation,
            matrix=matrix,
        )

        exp_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "experiment_id": exp_id,
            "name": name or f"Experiment-{exp_id[:8]}",
            "design": design,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": "created",
            "plot_dir": "",
        }
        _EXPERIMENTS[exp_id] = record

        return json.dumps(
            {
                "experiment_id": exp_id,
                "name": record["name"],
                "matrix": design.matrix_name,
                "n_runs": _n_runs(design),
                "n_factors": n_factors,
                "factors": {
                    k: {"low": v[0], "high": v[1]} for k, v in factors.items()
                },
                "assignation": assignation,
                "columns": design.columns,
                "experimental_matrix": _matrix_to_json(design),
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 2 — get_orthogonal_array
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_orthogonal_array(experiment_id: str) -> str:
        """Retrieve the full experimental matrix for a given experiment.

        Returns the run matrix showing actual factor *values* (not "Low
        level"/"High level" strings) for every run.  The matrix is in the
        order that experiments should be conducted (or randomised, depending
        on experimental protocol).

        Args:
            experiment_id: UUID returned by ``create_experiment`` or
                ``load_experiment``.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``name`` (str)
            * ``matrix`` (str) — array name.
            * ``n_runs`` (int)
            * ``factors`` (list[str]) — factor names in column order.
            * ``runs`` (list[dict]) — each dict has ``"run"`` (0-based index)
              plus one key per factor name mapping to its value for that run.

        Raises:
            ValueError: If the experiment ID is not found.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]
        return json.dumps(
            {
                "experiment_id": experiment_id,
                "name": record["name"],
                "matrix": design.matrix_name,
                "n_runs": _n_runs(design),
                "factors": list(design.experimental_design.keys()),
                "runs": _matrix_to_json(design),
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 3 — add_results
    # ------------------------------------------------------------------

    @mcp.tool()
    def add_results(
        experiment_id: str,
        results: dict[str, list],
        repetitions: int = 1,
    ) -> str:
        """Supply observed experimental results for each trial run.

        Populates the design with measured response values so that
        ``analyze`` can compute factor effects and contributions.  This tool
        should be called **once** per experiment, after all physical (or
        simulated) runs have been completed.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            results: Dict mapping each response-variable name to its
                measured values.  Two layouts are supported:

                **Single repetition** (``repetitions=1``):
                A flat list of ``n_runs`` floats, one per run in the same
                order as the experimental matrix::

                    {
                        "accuracy": [0.85, 0.87, 0.82, 0.91,
                                     0.88, 0.79, 0.93, 0.86]
                    }

                **Multiple repetitions** (``repetitions>1``):
                A list of ``n_runs`` inner lists, each inner list having
                exactly ``repetitions`` floats::

                    {
                        "accuracy": [
                            [0.85, 0.86],
                            [0.87, 0.88],
                            ...
                        ]
                    }

                Multiple responses may be included simultaneously::

                    {
                        "accuracy": [...],
                        "inference_time_ms": [...]
                    }

            repetitions: Number of replications per run.  Must be ``1`` for
                flat result lists and ``>1`` for nested lists.  Default ``1``.

        Returns:
            JSON string confirming the update, with keys:

            * ``experiment_id`` (str)
            * ``state`` (str) — ``"has_results"``
            * ``responses`` (list[str]) — response names stored.
            * ``repetitions`` (int)
            * ``n_runs`` (int)
            * ``message`` (str) — human-readable confirmation.

        Raises:
            ValueError: If the experiment is not found, results is empty,
                list lengths mismatch the number of runs, or a value cannot
                be converted to float.
            RuntimeError: If results have already been added (call
                create_experiment to start fresh).
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if record["state"] != "created":
            raise RuntimeError(
                f"Experiment '{experiment_id}' already has results "
                f"(state='{record['state']}'). "
                "Create a new experiment to start over."
            )

        _add_results_to_design(design, results, repetitions)
        record["state"] = "has_results"

        n_runs = _n_runs(design)
        return json.dumps(
            {
                "experiment_id": experiment_id,
                "state": "has_results",
                "responses": design.responses,
                "repetitions": repetitions,
                "n_runs": n_runs,
                "message": (
                    f"Results stored for {len(results)} response(s) "
                    f"across {n_runs} runs "
                    f"({'single measurement' if repetitions == 1 else f'{repetitions} repetitions'} per run). "
                    "Call analyze next."
                ),
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 4 — analyze
    # ------------------------------------------------------------------

    @mcp.tool()
    def analyze(
        experiment_id: str,
        response: Optional[str] = None,
    ) -> str:
        """Run Taguchi SNR / mean-response analysis on experiment results.

        Computes, for every design column (main factors and interactions):
        low-level mean, high-level mean, effect (high − low), sum of squares,
        and percentage contribution to total variability.  Also returns the
        grand mean and the additive-model prediction for the optimal
        combination (largest effect per factor).

        Must be called **after** ``add_results``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            response: If provided, return analysis only for this response
                variable.  If omitted, all responses are analysed and
                returned.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``state`` (str) — ``"analyzed"``
            * ``analyses`` (dict) — one entry per response variable.
              Each entry contains:

              * ``grand_mean`` (float)
              * ``total_ss`` (float)
              * ``columns`` (dict) — keyed by column label (``"A"``, ``"B"``,
                ``"AB"``, ...).  Each sub-dict has ``type``,
                ``factor_name``, ``low_avg``, ``high_avg``, ``effect``,
                ``ss``, ``contribution_pct``.

        Raises:
            ValueError: If experiment not found, no results have been added,
                or the specified response name does not exist.
            RuntimeError: If called before ``add_results``.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if not isinstance(design.taguchi_design, dict):
            raise RuntimeError(
                f"Experiment '{experiment_id}' has no results yet. "
                "Call add_results first."
            )

        if response is not None and response not in design.responses:
            raise ValueError(
                f"Response '{response}' not found. "
                f"Available responses: {design.responses}."
            )

        design.analyze()
        record["state"] = "analyzed"

        target_responses = [response] if response is not None else design.responses
        analyses: dict[str, Any] = {}
        for resp in target_responses:
            analyses[resp] = _get_analysis_table(design, resp)

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "state": "analyzed",
                "analyses": analyses,
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 5 — get_factor_effects
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_factor_effects(
        experiment_id: str,
        response: str,
        sort_by: str = "contribution_pct",
    ) -> str:
        """Retrieve the factor effect table for a specific response variable.

        Returns only the main-factor and interaction columns that are assigned
        in the design, sorted by a chosen metric.  This is a lighter-weight
        alternative to ``analyze`` when you only need the effect summary.

        Must be called **after** ``analyze``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            response: The response variable name to query (e.g.
                ``"accuracy"``).

            sort_by: Column by which to sort the returned rows.  One of
                ``"contribution_pct"`` (default, descending), ``"effect"``
                (absolute value, descending), or ``"column"`` (alphabetical).

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``response`` (str)
            * ``grand_mean`` (float)
            * ``factor_effects`` (list[dict]) — sorted rows, each with:
              ``column``, ``factor_name``, ``type``, ``low_avg``,
              ``high_avg``, ``effect``, ``ss``, ``contribution_pct``.

        Raises:
            ValueError: If experiment not found, response not found, or
                ``analyze`` has not been run yet.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if record["state"] != "analyzed":
            raise ValueError(
                f"Experiment '{experiment_id}' has not been analysed yet "
                f"(state='{record['state']}'). Call analyze first."
            )

        if response not in design.responses:
            raise ValueError(
                f"Response '{response}' not found. "
                f"Available: {design.responses}."
            )

        table = _get_analysis_table(design, response)

        rows = [
            {"column": col, **info}
            for col, info in table["columns"].items()
        ]

        if sort_by == "contribution_pct":
            rows.sort(key=lambda r: (r["contribution_pct"] or 0.0), reverse=True)
        elif sort_by == "effect":
            rows.sort(key=lambda r: abs(r["effect"] or 0.0), reverse=True)
        else:
            rows.sort(key=lambda r: r["column"])

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "response": response,
                "grand_mean": table["grand_mean"],
                "factor_effects": rows,
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 6 — get_optimal_levels
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_optimal_levels(
        experiment_id: str,
        response: str,
        optimize: str = "maximize",
    ) -> str:
        """Return the recommended optimal factor-level combination.

        Uses the Taguchi additive model: for each main factor, selects the
        level (Low or High) that produces the best mean response.  The
        predicted performance at the optimal combination is estimated as::

            grand_mean + Σ (optimal_level_mean − grand_mean)

        Must be called **after** ``analyze``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            response: The response variable to optimise.

            optimize: ``"maximize"`` (default) — choose the level with the
                higher mean for each factor, i.e. "larger is better".
                ``"minimize"`` — choose the level with the lower mean, i.e.
                "smaller is better".

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``response`` (str)
            * ``optimization`` (str)
            * ``grand_mean`` (float)
            * ``additive_model_prediction`` (float) — predicted response at
              the optimal combination.
            * ``optimal_levels`` (dict) — keyed by factor name.  Each entry
              has ``column``, ``optimal_level`` (``"Low"``/``"High"``),
              ``optimal_value``, ``low_value``, ``high_value``,
              ``low_avg_response``, ``high_avg_response``, ``delta``.

        Raises:
            ValueError: If experiment not found, response not found,
                ``optimize`` is not ``"maximize"`` or ``"minimize"``, or
                ``analyze`` has not been run.
        """
        if optimize not in ("maximize", "minimize"):
            raise ValueError(
                f"optimize must be 'maximize' or 'minimize', got '{optimize}'."
            )

        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if record["state"] != "analyzed":
            raise ValueError(
                f"Experiment '{experiment_id}' has not been analysed yet. "
                "Call analyze first."
            )

        if response not in design.responses:
            raise ValueError(
                f"Response '{response}' not found. "
                f"Available: {design.responses}."
            )

        result = _compute_optimal_levels(design, response, optimize)

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "response": response,
                **result,
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 7 — plot_main_effects
    # ------------------------------------------------------------------

    @mcp.tool()
    def plot_main_effects(
        experiment_id: str,
        response: Optional[str] = None,
        output_dir: str = "",
        font_family: str = "DejaVu Sans",
        font_size: int = 12,
    ) -> str:
        """Generate main-effects (and interaction) plots and save as PNGs.

        Produces one PNG per factor column per response.  Single-letter
        columns (e.g. ``"A"``, ``"B"``) yield classic Taguchi main-effect
        plots (Low vs High means connected by a line).  Two-letter columns
        (e.g. ``"AB"``) yield interaction plots.

        Must be called **after** ``analyze``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            response: If provided, generate plots only for this response.
                If omitted, plots are generated for all responses.

            output_dir: Directory where PNGs are saved.  Created if it does
                not exist.  Defaults to ``./tagupy_plots/<experiment_id>/``
                in the current working directory.

            font_family: Matplotlib font family string.  Default
                ``"DejaVu Sans"`` (universally available).

            font_size: Base font size in points.  Default ``12``.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``output_dir`` (str) — absolute path to the output directory.
            * ``files`` (list[str]) — absolute paths to all generated PNGs.
            * ``n_files`` (int)

        Raises:
            ValueError: If experiment not found or ``analyze`` has not been
                run yet.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if record["state"] != "analyzed":
            raise ValueError(
                f"Experiment '{experiment_id}' has not been analysed yet. "
                "Call analyze first."
            )

        if output_dir:
            out_path = pathlib.Path(output_dir)
        else:
            out_path = pathlib.Path.cwd() / "tagupy_plots" / experiment_id / "effects"
        out_path.mkdir(parents=True, exist_ok=True)
        record["plot_dir"] = str(out_path)

        target_responses = (
            [response] if response is not None else design.responses
        )

        # Call the design's effect_plots method
        design.effect_plots(
            path=out_path,
            font_family=font_family,
            font_size=font_size,
        )

        # Collect the paths that were (or should have been) generated
        files: list[str] = []
        for resp in target_responses:
            data_col = resp if design.repetitions <= 1 else f"{resp} average"
            safe_resp = data_col.lower().replace(" ", "-")
            for col in design.columns:
                candidate = out_path / f"{safe_resp}-{col}.png"
                if candidate.exists():
                    files.append(str(candidate.resolve()))

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "output_dir": str(out_path.resolve()),
                "files": files,
                "n_files": len(files),
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 8 — plot_pareto
    # ------------------------------------------------------------------

    @mcp.tool()
    def plot_pareto(
        experiment_id: str,
        response: Optional[str] = None,
        output_dir: str = "",
        font_family: str = "DejaVu Sans",
        font_size: int = 12,
    ) -> str:
        """Generate Pareto contribution charts and save as PNGs.

        Each bar represents the percentage contribution of a design column
        (factor or interaction) to the total variability.  A cumulative line
        is overlaid.  One PNG is produced per response variable.

        Must be called **after** ``analyze``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            response: If provided, generate the Pareto chart only for this
                response.  If omitted, one chart per response is generated.

            output_dir: Directory where PNGs are saved.  Created if it does
                not exist.  Defaults to ``./tagupy_plots/<experiment_id>/pareto/``.

            font_family: Matplotlib font family.  Default ``"DejaVu Sans"``.

            font_size: Base font size in points.  Default ``12``.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``output_dir`` (str)
            * ``files`` (list[str]) — absolute path(s) of the generated PNGs.
            * ``n_files`` (int)

        Raises:
            ValueError: If experiment not found or ``analyze`` not yet run.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        if record["state"] != "analyzed":
            raise ValueError(
                f"Experiment '{experiment_id}' has not been analysed yet. "
                "Call analyze first."
            )

        if output_dir:
            out_path = pathlib.Path(output_dir)
        else:
            out_path = pathlib.Path.cwd() / "tagupy_plots" / experiment_id / "pareto"
        out_path.mkdir(parents=True, exist_ok=True)

        target_responses = (
            [response] if response is not None else design.responses
        )

        # Use a temporary title override if a single response is requested
        design.pareto_plot(
            path=out_path,
            font_family=font_family,
            font_size=font_size,
        )

        files: list[str] = []
        for resp in target_responses:
            safe_name = resp.lower().replace(" ", "-")
            candidate = out_path / f"{safe_name}.png"
            if candidate.exists():
                files.append(str(candidate.resolve()))

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "output_dir": str(out_path.resolve()),
                "files": files,
                "n_files": len(files),
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 9 — save_experiment
    # ------------------------------------------------------------------

    @mcp.tool()
    def save_experiment(
        experiment_id: str,
        path: str,
    ) -> str:
        """Serialise a Taguchi experiment to a zip archive.

        The archive preserves the full design state: factor definitions,
        orthogonal array, experimental matrix, result data, and analysis
        output (if ``analyze`` has been called).  It can be reloaded with
        ``load_experiment``.

        Args:
            experiment_id: UUID returned by ``create_experiment``.

            path: Destination file path for the zip archive, e.g.
                ``"/home/user/experiments/my_design.zip"``.  Parent
                directories are created if they do not exist.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str)
            * ``name`` (str)
            * ``path`` (str) — absolute path of the saved archive.
            * ``size_bytes`` (int) — file size of the archive.
            * ``state`` (str) — design state at time of save.

        Raises:
            ValueError: If the experiment is not found.
            OSError: If the file cannot be written.
        """
        record = _require_experiment(experiment_id)
        design: TaguchiDesign = record["design"]

        save_path = pathlib.Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        design.save(save_path)

        size = save_path.stat().st_size

        return json.dumps(
            {
                "experiment_id": experiment_id,
                "name": record["name"],
                "path": str(save_path.resolve()),
                "size_bytes": size,
                "state": record["state"],
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 10 — load_experiment
    # ------------------------------------------------------------------

    @mcp.tool()
    def load_experiment(
        path: str,
        name: str = "",
    ) -> str:
        """Reload a previously saved Taguchi experiment from a zip archive.

        Restores the full design state into the in-memory store and returns a
        new experiment ID.  The loaded experiment can be queried and further
        analysed like any freshly created one.

        Args:
            path: Path to the zip archive produced by ``save_experiment``.

            name: Optional human-readable label to assign to the reloaded
                experiment.  If omitted, defaults to the archive filename.

        Returns:
            JSON string with keys:

            * ``experiment_id`` (str) — newly assigned UUID for this session.
            * ``name`` (str)
            * ``matrix`` (str)
            * ``n_runs`` (int)
            * ``n_factors`` (int)
            * ``responses`` (list[str]) — response variables stored in the
              archive (empty if ``run()`` was never called before saving).
            * ``state`` (str) — inferred state: ``"created"``,
              ``"has_results"``, or ``"analyzed"``.
            * ``factors`` (dict)

        Raises:
            FileNotFoundError: If the archive path does not exist.
            ValueError: If the archive is malformed or incompatible.
        """
        load_path = pathlib.Path(path)
        if not load_path.exists():
            raise FileNotFoundError(
                f"Archive not found: '{load_path}'. "
                "Check the path and try again."
            )

        design = TaguchiDesign.load(load_path)

        # Infer state from the loaded design
        if not design.responses:
            state = "created"
        else:
            df0 = (
                design.taguchi_design[design.responses[0]]
                if isinstance(design.taguchi_design, dict)
                else None
            )
            if df0 is not None and "analysis" in df0.index:
                state = "analyzed"
            else:
                state = "has_results"

        exp_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "experiment_id": exp_id,
            "name": name or load_path.stem,
            "design": design,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": state,
            "plot_dir": "",
        }
        _EXPERIMENTS[exp_id] = record

        return json.dumps(
            {
                "experiment_id": exp_id,
                "name": record["name"],
                "matrix": design.matrix_name,
                "n_runs": _n_runs(design),
                "n_factors": len(design.experimental_design),
                "responses": design.responses,
                "state": state,
                "factors": {
                    k: {"low": v[0], "high": v[1]}
                    for k, v in design.experimental_design.items()
                },
            },
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 11 — list_arrays
    # ------------------------------------------------------------------

    @mcp.tool()
    def list_arrays() -> str:
        """List all built-in orthogonal arrays with their properties.

        Returns metadata for every available Taguchi orthogonal array so
        that callers can choose the right one for their experiment.

        Returns:
            JSON string with a top-level ``"arrays"`` list.  Each element
            has:

            * ``name`` (str) — array identifier for ``create_experiment``.
            * ``runs`` (int) — number of experimental runs required.
            * ``columns`` (int) — total number of columns (factors +
              interactions).
            * ``max_factors`` (int) — maximum number of 2-level main factors
              the array can accommodate.
            * ``description`` (str) — human-readable guidance.
            * ``assignation_table`` (dict) — the interaction assignation
              table: for row *i* and column *j*, the cell value is the
              column index that holds the interaction between factors at
              positions *i* and *j*.

        Notes:
            * L8 is best for quick screening with 3–7 factors.
            * L16 is the most common choice for 4–15 factors.
            * L32 / L32-inv are used when more resolution is needed.
        """
        output = []
        for name in AVAILABLE_ARRAYS:
            meta = _ARRAY_META[name]
            assignation_df = get_assignation(name)
            output.append(
                {
                    "name": name,
                    "runs": meta["runs"],
                    "columns": meta["columns"],
                    "max_factors": meta["max_factors"],
                    "description": meta["description"],
                    "assignation_table": assignation_df.to_dict(),
                }
            )
        return json.dumps({"arrays": output}, indent=2)


# ---------------------------------------------------------------------------
# Resource registration
# ---------------------------------------------------------------------------


def register_resources(mcp: Any) -> None:
    """Register MCP resources on *mcp*.

    Two resources are exposed:

    * ``tagupy://arrays`` — live snapshot of all built-in arrays.
    * ``tagupy://experiment/{id}`` — current state of one experiment.
    """

    @mcp.resource("tagupy://arrays")
    def arrays_resource() -> str:
        """List of all built-in Taguchi orthogonal arrays with metadata.

        Returns the same payload as the ``list_arrays`` tool, but as a
        persistent MCP resource that clients can subscribe to.
        """
        output = []
        for name in AVAILABLE_ARRAYS:
            meta = _ARRAY_META[name]
            output.append(
                {
                    "name": name,
                    "runs": meta["runs"],
                    "columns": meta["columns"],
                    "max_factors": meta["max_factors"],
                    "description": meta["description"],
                }
            )
        return json.dumps({"arrays": output}, indent=2)

    @mcp.resource("tagupy://experiment/{id}")
    def experiment_resource(id: str) -> str:
        """Current state snapshot of a given experiment.

        Args:
            id: The experiment UUID (same as ``experiment_id`` returned by
                ``create_experiment``).

        Returns:
            JSON string with the full experiment summary (same as the dict
            produced by ``_design_summary``), plus the current experimental
            matrix.

        Raises:
            ValueError: If the experiment ID is not found.
        """
        record = _require_experiment(id)
        summary = _design_summary(record)
        summary["experimental_matrix"] = _matrix_to_json(record["design"])
        return json.dumps(summary, indent=2)
