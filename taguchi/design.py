"""TaguchiDesign class for Taguchi experimental design of experiments.

This module provides the main ``TaguchiDesign`` class for setting up, running,
and analysing Taguchi orthogonal-array experiments. The internal data structure
mirrors the original research code so that CSV exports and zip archives are
fully backward-compatible.
"""

from __future__ import annotations

import json
import pathlib
import zipfile
from collections.abc import Callable, Iterable
from typing import Optional, Union

import numpy as np
import pandas as pd

from .arrays import AVAILABLE_ARRAYS, get_array, get_assignation


class TaguchiDesign:
    """Taguchi design of experiments using two-level orthogonal arrays.

    Supports L8, L16, L32, and L32-inv arrays. Interaction columns are
    automatically labelled using the array's interaction assignation table.

    Parameters
    ----------
    experimental_design : dict
        Ordered mapping of factor names to ``[low_value, high_value]`` pairs.
        The order of keys determines factor-letter assignment (first key ->
        factor A, second key -> factor B, etc.). Example::

            {
                "Learning rate": [1e-4, 1e-3],
                "Batch size":    [16,   64],
                "Epochs":        [50,   100],
            }

    assignation : Iterable[int]
        Zero-based column indices in the orthogonal array to assign each
        factor to. Length must equal ``len(experimental_design)``.
    matrix : str, optional
        Name of the orthogonal array.  One of ``'L8'``, ``'L16'``,
        ``'L32'``, ``'L32-inv'``.  Default ``'L16'``.

    Attributes
    ----------
    experimental_design : dict
        The factor definitions as supplied.
    experimental_matrix : pd.DataFrame
        Run matrix with actual factor *values* (Low/High replaced by the
        values from ``experimental_design``).
    taguchi_design : pd.DataFrame | dict[str, pd.DataFrame]
        Before ``run()``: the raw orthogonal array with factor letters and
        interaction labels as column names.
        After ``run()``: a dict mapping response name -> DataFrame that
        contains the full design plus result columns and (after ``analyze()``)
        analysis columns.
    columns : list[str]
        All column labels in the design (factor letters + interaction labels
        + unused numeric labels).
    responses : list[str]
        Response variable names (populated by ``run()``).
    repetitions : int
        Number of replications per run (set by ``run()``).
    matrix_name : str
        Name of the orthogonal array used.
    assignation : list[str]
        String-cast column indices used for factor assignment.

    Examples
    --------
    >>> design = TaguchiDesign(
    ...     {"LR": [1e-4, 1e-3], "BS": [16, 64]},
    ...     assignation=[0, 3],
    ...     matrix="L8",
    ... )
    >>> design.run(my_func, responses=["accuracy"])
    >>> design.analyze()
    >>> design.pareto_plot()
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        experimental_design: dict,
        assignation: Iterable,
        matrix: str = "L16",
    ) -> None:
        if matrix not in AVAILABLE_ARRAYS:
            raise ValueError(
                f"Unknown matrix '{matrix}'. Available: {AVAILABLE_ARRAYS}"
            )

        assignation_list = list(assignation)
        n_factors = len(experimental_design)
        if len(assignation_list) != n_factors:
            raise ValueError(
                f"len(assignation) == {len(assignation_list)} but "
                f"experimental_design has {n_factors} factors."
            )

        self.experimental_design: dict = experimental_design
        self.matrix_name: str = matrix
        self.assignation: list[str] = [str(i) for i in assignation_list]
        self.responses: list[str] = []
        self.repetitions: int = 1

        # Get fresh copies of the array data (prevents cross-instance mutation)
        raw_array: pd.DataFrame = get_array(matrix)
        self.taguchi_assignation: pd.DataFrame = get_assignation(matrix)

        # -----------------------------------------------------------------
        # Step 1 — assign factor letters and rename corresponding columns
        # -----------------------------------------------------------------
        # renamed_factors : letter -> factor_name  (e.g. {"A": "LR", "B": "BS"})
        # col_to_letter   : str(col_idx) -> letter (e.g. {"0": "A", "3": "B"})
        renamed_factors: dict[str, str] = {}
        col_to_letter: dict[str, str] = {}
        for i, key in enumerate(experimental_design.keys()):
            letter = chr(65 + i)           # "A", "B", "C", ...
            renamed_factors[letter] = key
            col_to_letter[self.assignation[i]] = letter

        # Rename factor columns in a fresh copy of the orthogonal array.
        self.taguchi_design: pd.DataFrame = raw_array.rename(columns=col_to_letter)

        # -----------------------------------------------------------------
        # Step 2 — build experimental_matrix (factor values, not Low/High)
        # -----------------------------------------------------------------
        factor_letters = sorted(renamed_factors.keys())
        exp_matrix = self.taguchi_design[factor_letters].copy()
        exp_matrix = exp_matrix.rename(columns=renamed_factors)
        for key, levels in experimental_design.items():
            low_val, high_val = levels[0], levels[1]
            exp_matrix[key] = exp_matrix[key].map(
                {"Low level": low_val, "High level": high_val}
            )
        self.experimental_matrix: pd.DataFrame = exp_matrix

        # -----------------------------------------------------------------
        # Step 3 — rename interaction columns using the assignation table
        #
        # The column snapshot is frozen before any interaction renaming so
        # that position indices remain stable throughout the loop.  For each
        # ordered pair of factor letters (A-B, A-C, B-C, ...) the assignation
        # table yields the raw column index that holds the interaction.  If
        # that column was already claimed by a factor, the rename is a no-op
        # (the interaction is confounded with that factor — correct behaviour
        # for saturated designs).
        # -----------------------------------------------------------------
        cols_snapshot: list[str] = self.taguchi_design.columns.tolist()

        for col_idx, col in enumerate(cols_snapshot):
            # Only process columns that are single factor letters
            if not (len(col) == 1 and col.isalpha()):
                continue
            interaction_renames: dict[str, str] = {}
            for other_col in cols_snapshot[col_idx + 1:]:
                if not (len(other_col) == 1 and other_col.isalpha()):
                    continue
                # Position of the other factor in the snapshot
                other_pos = str(int(cols_snapshot.index(other_col)))
                # Assignation table: row = col_idx, column = other_pos
                interaction_loc = self.taguchi_assignation[other_pos][col_idx]
                interaction_renames[str(interaction_loc)] = f"{col}{other_col}"
            self.taguchi_design = self.taguchi_design.rename(
                columns=interaction_renames
            )

        self.columns: list[str] = self.taguchi_design.columns.tolist()
        self.experiences: list = self.taguchi_design.index.tolist()

    # ------------------------------------------------------------------
    # Running experiments
    # ------------------------------------------------------------------

    def run(
        self,
        func: Callable,
        responses: list[str],
        randomize: bool = False,
        repetitions: int = 1,
        progress_path: Optional[Union[str, pathlib.Path]] = None,
    ) -> None:
        """Execute the experimental design by calling *func* for each run.

        Parameters
        ----------
        func : Callable
            Called once per experimental run (or once per repetition if
            ``repetitions > 1``).  Receives a ``list`` of factor values in
            the order defined by ``experimental_design``.  When
            ``repetitions > 1`` an extra ``int`` (zero-based repetition
            index) is appended to the list.  Must return a ``dict`` mapping
            each response name to its measured value.
        responses : list[str]
            Names of the response variables that *func* returns.
        randomize : bool, optional
            Shuffle the run order before execution.  Default ``False``.
        repetitions : int, optional
            Number of replications for each combination.  When > 1 the
            design records individual repetitions plus per-row average and
            standard deviation columns.  Default ``1``.
        progress_path : str or Path, optional
            Path to a CSV checkpoint file written after every run.  Deleted
            on successful completion.  Allows resuming interrupted long
            experiments.  Default ``None`` (no checkpointing).

        Raises
        ------
        Exception
            Any exception raised by *func* is re-raised after an emergency
            CSV save (``<progress_path>.emergency.csv`` or
            ``./emergency_save.csv``).
        """
        self.responses = list(responses)
        self.repetitions = repetitions

        if progress_path is not None:
            progress_path = pathlib.Path(progress_path)
            emergency_path = progress_path.with_suffix(".emergency.csv")
        else:
            emergency_path = pathlib.Path("emergency_save.csv")

        # Convert taguchi_design into one independent DataFrame per response
        new_taguchi_design: dict[str, pd.DataFrame] = {}
        for response in self.responses:
            new_taguchi_design[response] = self.taguchi_design.copy()
            if repetitions == 1:
                # Pre-allocate the single response column
                new_taguchi_design[response][response] = np.nan
            else:
                # Pre-allocate per-repetition + summary columns
                for rep in range(repetitions):
                    new_taguchi_design[response][f"{response} (Repetition {rep})"] = np.nan
                new_taguchi_design[response][f"{response} average"] = np.nan
                new_taguchi_design[response][f"{response} standard deviation"] = np.nan

        # Determine run order
        run_indices = list(self.experimental_matrix.index)
        if randomize:
            np.random.shuffle(run_indices)

        try:
            for row in run_indices:
                # Pass only factor values (from experimental_matrix, not the full design)
                factor_values = self.experimental_matrix.loc[row].tolist()

                if repetitions == 1:
                    result = func(factor_values)
                    for response in self.responses:
                        new_taguchi_design[response].loc[row, response] = (
                            result[response]
                        )
                else:
                    rep_values: dict[str, list] = {r: [] for r in self.responses}
                    for rep in range(repetitions):
                        result = func(factor_values + [rep])
                        for response in self.responses:
                            val = result[response]
                            new_taguchi_design[response].loc[
                                row, f"{response} (Repetition {rep})"
                            ] = val
                            rep_values[response].append(val)

                    # Compute per-row average and standard deviation
                    for response in self.responses:
                        arr = np.array(rep_values[response], dtype=float)
                        new_taguchi_design[response].loc[
                            row, f"{response} average"
                        ] = float(np.mean(arr))
                        new_taguchi_design[response].loc[
                            row, f"{response} standard deviation"
                        ] = float(np.std(arr))

                # Optional progress checkpoint
                if progress_path is not None:
                    for response in self.responses:
                        new_taguchi_design[response].to_csv(progress_path)

        except Exception:
            # Emergency save before re-raising
            for response in self.responses:
                new_taguchi_design[response].to_csv(emergency_path)
            raise

        # Remove progress file on clean completion
        if progress_path is not None and progress_path.exists():
            progress_path.unlink()

        self.taguchi_design = new_taguchi_design

    # ------------------------------------------------------------------
    # Statistical analysis
    # ------------------------------------------------------------------

    def analyze(self) -> None:
        """Compute factor effects and variability contributions.

        For each response, adds the following analysis columns to
        ``self.taguchi_design[response]`` (one set per factor/interaction
        column in the design):

        * ``"{col} (Low)"``        — mean response at the low level.
        * ``"{col} (High)"``       — mean response at the high level.
        * ``"{col} Effect"``       — high mean − low mean.
        * ``"{col} SS"``           — squared effect (sum of squares).
        * ``"{col} Contribution"`` — SS as a percentage of total SS.

        A single summary row (index ``"analysis"``) is appended to the
        DataFrame holding these computed values; the original experiment rows
        are unmodified.

        Must be called **after** ``run()``.

        Raises
        ------
        RuntimeError
            If called before ``run()``.
        """
        if not isinstance(self.taguchi_design, dict):
            raise RuntimeError(
                "analyze() must be called after run(). "
                "No response data is available yet."
            )

        for response in self.responses:
            df = self.taguchi_design[response]

            if self.repetitions <= 1:
                self._analyze_single(df, response, response)
            else:
                # Analyse the per-run average (primary metric for DOE)
                self._analyze_single(df, response, f"{response} average")

    def _analyze_single(
        self,
        df: pd.DataFrame,
        response: str,
        data_col: str,
    ) -> None:
        """Append analysis columns and a summary row to *df* (in-place).

        For each design column in ``self.columns``, computes the low-level
        average, high-level average, effect, sum of squares, and percentage
        contribution, storing them as new columns.  A single ``"analysis"``
        row is appended (or overwritten) with these summary values.

        Parameters
        ----------
        df : pd.DataFrame
            The response's design DataFrame (modified in-place).
        response : str
            Base response name (unused except for future extensibility).
        data_col : str
            Column name in *df* that holds the measured (or derived) values
            to analyse.
        """
        # Only operate on the original experiment rows (exclude any prior
        # analysis rows which would have NaN in the design columns).
        exp_index = [idx for idx in df.index if idx != "analysis"]
        exp_index_arr = np.array(exp_index)

        analysis: dict = {}

        # Per-column statistics
        for col in self.columns:
            col_data = df.loc[exp_index, col]
            low_mask  = col_data == "Low level"
            high_mask = col_data == "High level"

            low_idx   = exp_index_arr[low_mask.values]
            high_idx  = exp_index_arr[high_mask.values]

            low_vals  = pd.to_numeric(df.loc[low_idx,  data_col], errors="coerce")
            high_vals = pd.to_numeric(df.loc[high_idx, data_col], errors="coerce")

            low_avg  = float(np.mean(low_vals.dropna()))  if not low_vals.dropna().empty  else np.nan
            high_avg = float(np.mean(high_vals.dropna())) if not high_vals.dropna().empty else np.nan
            effect   = (high_avg - low_avg) if not (np.isnan(low_avg) or np.isnan(high_avg)) else np.nan
            ss       = effect ** 2 if not np.isnan(effect) else np.nan

            analysis[f"{col} (Low)"]  = low_avg
            analysis[f"{col} (High)"] = high_avg
            analysis[f"{col} Effect"] = effect
            analysis[f"{col} SS"]     = ss

        # Percentage contributions (normalised to 100 %)
        ss_values = [analysis[f"{col} SS"] for col in self.columns]
        total_ss  = float(np.nansum(ss_values))
        for col in self.columns:
            col_ss = analysis[f"{col} SS"]
            if total_ss != 0.0 and not np.isnan(col_ss):
                analysis[f"{col} Contribution"] = float(col_ss) / total_ss * 100.0
            else:
                analysis[f"{col} Contribution"] = 0.0

        # Add analysis columns to the DataFrame (NaN for experiment rows)
        for key in analysis:
            if key not in df.columns:
                df[key] = np.nan

        # Append / overwrite the summary row
        df.loc["analysis"] = np.nan
        for key, val in analysis.items():
            df.loc["analysis", key] = val

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def pareto_plot(
        self,
        title: Optional[str] = None,
        path: Optional[Union[str, pathlib.Path]] = None,
        font_family: str = "Liberation Serif",
        font_size: int = 12,
    ) -> None:
        """Generate Pareto charts of factor contributions for each response.

        One PNG per response is saved to *path*.

        Parameters
        ----------
        title : str, optional
            Custom chart title.  Defaults to the response name.
        path : str or Path, optional
            Output directory.  Defaults to ``./pareto_plots/``.
        font_family : str, optional
            Matplotlib font family string.  Default ``'Liberation Serif'``.
        font_size : int, optional
            Base font size in points.  Default ``12``.

        Raises
        ------
        RuntimeError
            If called before ``run()`` and ``analyze()``.
        """
        import matplotlib.pyplot as plt
        from matplotlib.ticker import PercentFormatter

        if not isinstance(self.taguchi_design, dict):
            raise RuntimeError("pareto_plot() requires run() and analyze().")

        out_dir = pathlib.Path(path) if path else pathlib.Path.cwd() / "pareto_plots"
        out_dir.mkdir(parents=True, exist_ok=True)

        plt.rcParams["font.family"] = font_family
        plt.rcParams["font.size"] = font_size

        for response in self.responses:
            df = self.taguchi_design[response]

            # Check that analyze() has been called
            contrib_cols = [f"{col} Contribution" for col in self.columns]
            if not all(c in df.columns for c in contrib_cols):
                continue

            # Read contributions from the analysis summary row
            y_raw = np.array(
                [float(df.loc["analysis", f"{col} Contribution"]) for col in self.columns],
                dtype=float,
            )
            x_raw = np.array(self.columns)

            order    = np.flip(np.argsort(y_raw))
            x_sorted = x_raw[order]
            y_sorted = y_raw[order]
            weights  = y_sorted / y_sorted.sum() if y_sorted.sum() != 0 else y_sorted
            cumsum   = weights.cumsum()

            fig, ax1 = plt.subplots(figsize=(max(len(self.columns), 6), 4))
            ax1.bar(x_sorted, y_sorted, width=1.0,
                    color="#3e7dfd", edgecolor="#3e7dfd", align="center")
            ax1.set_xlim([-0.5, len(x_sorted)])
            ax1.set_xlabel("Factors and interactions", fontsize=font_size)
            ax1.set_ylabel("Contribution (%)", fontsize=font_size)
            ax1.yaxis.set_major_formatter(PercentFormatter(xmax=100))
            ax1.set_xticklabels(list(ax1.get_xticklabels()), rotation=90)

            ax2 = ax1.twinx()
            ax2.plot(x_sorted, cumsum * 100, color="#010185",
                     marker="D", ms=3, lw=1)
            ax2.yaxis.set_major_formatter(PercentFormatter())
            ax2.set_ylabel("Cumulative contribution")

            chart_title = title or response
            plt.title(chart_title, fontsize=font_size)
            plt.tight_layout()

            safe_name = response.lower().replace(" ", "-")
            plt.savefig(out_dir / f"{safe_name}.png")
            plt.close()

    def effect_plots(
        self,
        limits: Optional[list] = None,
        percentage: Optional[list[bool]] = None,
        path: Optional[Union[str, pathlib.Path]] = None,
        font_family: str = "Liberation Serif",
        font_size: int = 12,
    ) -> None:
        """Generate main-effect and interaction plots for each response.

        For single-factor columns one plot is produced per factor; for
        interaction columns (two-letter labels like ``'AB'``) a two-line
        interaction plot is produced.

        Parameters
        ----------
        limits : list of [float, float], optional
            Y-axis ``[min, max]`` for each response.  Length must match
            ``len(self.responses)``.  ``None`` entries use auto-scaling.
        percentage : list[bool], optional
            Whether to format each response axis as a percentage.  Length
            must match ``len(self.responses)``.  Default all ``False``.
        path : str or Path, optional
            Output directory.  Defaults to ``./effect_plots/``.
        font_family : str, optional
            Matplotlib font family.  Default ``'Liberation Serif'``.
        font_size : int, optional
            Base font size in points.  Default ``12``.

        Raises
        ------
        RuntimeError
            If called before ``run()``.
        """
        import matplotlib.pyplot as plt
        from matplotlib.ticker import PercentFormatter

        if not isinstance(self.taguchi_design, dict):
            raise RuntimeError("effect_plots() requires run().")

        out_dir = pathlib.Path(path) if path else pathlib.Path.cwd() / "effect_plots"
        out_dir.mkdir(parents=True, exist_ok=True)

        plt.rcParams["font.family"] = font_family
        plt.rcParams["font.size"] = font_size

        if percentage is None:
            percentage = [False] * len(self.responses)

        for resp_idx, response in enumerate(self.responses):
            df = self.taguchi_design[response]

            if self.repetitions <= 1:
                data_col = response
            else:
                data_col = f"{response} average"

            if data_col not in df.columns:
                continue

            exp_index = [idx for idx in df.index if idx != "analysis"]

            for col in self.columns:
                is_interaction = len(col) >= 2 and col.isalpha()

                if not is_interaction:
                    avgs = []
                    for level in ("Low level", "High level"):
                        mask = df.loc[exp_index, col] == level
                        vals = pd.to_numeric(
                            df.loc[[i for i, m in zip(exp_index, mask.values) if m], data_col],
                            errors="coerce",
                        )
                        avg = float(np.mean(vals.dropna())) if not vals.dropna().empty else np.nan
                        avgs.append(avg)

                    arr = np.array(avgs, dtype=float)
                    _, ax = plt.subplots()
                    ax.plot(avgs, marker="D", ms=14, lw=1, color="#0054ff")

                    if limits is not None and limits[resp_idx] is not None:
                        ax.set_ylim(limits[resp_idx][0], limits[resp_idx][1])
                    else:
                        span = float(np.ptp(arr)) if np.ptp(arr) > 0 else 1.0
                        ax.set_ylim(float(np.nanmin(arr)) - 0.1 * span,
                                    float(np.nanmax(arr)) + 0.1 * span)

                    if percentage[resp_idx]:
                        ax.yaxis.set_major_formatter(PercentFormatter())

                    ax.set_xticks([0, 1])
                    ax.set_xticklabels(["Low", "High"])
                    ax.set_xlim([-0.5, 1.5])
                    ax.set_title(f"{col} - {data_col}")

                    safe_resp = data_col.lower().replace(" ", "-")
                    plt.savefig(out_dir / f"{safe_resp}-{col}.png")
                    plt.close()

                else:
                    f0, f1 = col[0], col[1]
                    row_labels = [f"{f1} low level", f"{f1} high level"]
                    col_labels = [f"{f0} low level", f"{f0} high level"]
                    effect_matrix = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)

                    for r_lev, f1_level in zip(row_labels, ("Low level", "High level")):
                        for c_lev, f0_level in zip(col_labels, ("Low level", "High level")):
                            mask_idx = [
                                i for i in exp_index
                                if df.loc[i, f0] == f0_level and df.loc[i, f1] == f1_level
                            ]
                            vals = pd.to_numeric(df.loc[mask_idx, data_col], errors="coerce")
                            effect_matrix.loc[r_lev, c_lev] = (
                                float(np.mean(vals.dropna())) if not vals.dropna().empty else np.nan
                            )

                    arr = effect_matrix.to_numpy(dtype=float)
                    fig, ax = plt.subplots()
                    ax.plot(effect_matrix[col_labels[0]], marker="D", ms=10, lw=1,
                            color="#0054ff", label=col_labels[0])
                    ax.plot(effect_matrix[col_labels[1]], marker="o", ms=10, lw=1,
                            color="#ff6c00", label=col_labels[1])

                    if limits is not None and limits[resp_idx] is not None:
                        ax.set_ylim(limits[resp_idx][0], limits[resp_idx][1])
                    else:
                        span = float(np.ptp(arr)) if np.ptp(arr) > 0 else 1.0
                        ax.set_ylim(float(np.nanmin(arr)) - 0.1 * span,
                                    float(np.nanmax(arr)) + 0.1 * span)

                    if percentage[resp_idx]:
                        ax.yaxis.set_major_formatter(PercentFormatter())

                    ax.set_xticks([0, 1])
                    ax.set_xticklabels(["Low", "High"])
                    ax.set_xlim([-0.5, 1.5])
                    ax.set_title(f"{col} - {data_col}")

                    box = ax.get_position()
                    ax.set_position([box.x0, box.y0 + box.height * 0.1,
                                     box.width, box.height * 0.9])
                    fig.legend(loc="lower center", fancybox=False, framealpha=1,
                               edgecolor="white", ncol=2, bbox_to_anchor=(0.5, -0.001))

                    safe_resp = data_col.lower().replace(" ", "-")
                    plt.savefig(out_dir / f"{safe_resp}-{col}.png")
                    plt.close()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Union[str, pathlib.Path]) -> None:
        """Serialise the design state to a zip archive."""
        out_path = pathlib.Path(path)

        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            metadata: dict = {
                "assignation":         self.assignation,
                "experimental_design": self.experimental_design,
                "columns":             self.columns,
                "responses":           self.responses,
                "repetitions":         self.repetitions,
                "matrix_name":         self.matrix_name,
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            zf.writestr("experimental_matrix.csv", self.experimental_matrix.to_csv())

            if isinstance(self.taguchi_design, dict):
                for response in self.responses:
                    zf.writestr(
                        f"taguchi_design_{response}.csv",
                        self.taguchi_design[response].to_csv(),
                    )
            else:
                zf.writestr("taguchi_design_raw.csv", self.taguchi_design.to_csv())

    @staticmethod
    def _restore_index(df: pd.DataFrame) -> pd.DataFrame:
        """Convert string index values back to int where possible.

        CSV round-trips turn integer indices into strings.  This helper
        restores the original mixed-type index (integers for run rows,
        string ``"analysis"`` for the summary row).
        """
        new_index = []
        for val in df.index:
            try:
                new_index.append(int(val))
            except (ValueError, TypeError):
                new_index.append(val)
        df.index = new_index
        return df

    @classmethod
    def load(cls, path: Union[str, pathlib.Path]) -> "TaguchiDesign":
        """Restore a TaguchiDesign from a zip archive."""
        in_path = pathlib.Path(path)

        with zipfile.ZipFile(in_path, "r") as zf:
            namelist = zf.namelist()

            with zf.open("metadata.json") as f:
                metadata = json.load(f)

            instance: TaguchiDesign = cls.__new__(cls)
            instance.experimental_design = metadata["experimental_design"]
            instance.assignation         = metadata["assignation"]
            instance.matrix_name         = metadata.get("matrix_name", "L16")
            instance.columns             = metadata["columns"]
            instance.responses           = metadata["responses"]
            instance.repetitions         = metadata["repetitions"]
            instance.taguchi_assignation = get_assignation(instance.matrix_name)

            with zf.open("experimental_matrix.csv") as f:
                instance.experimental_matrix = cls._restore_index(
                    pd.read_csv(f, index_col=0)
                )

            if instance.responses and all(
                f"taguchi_design_{r}.csv" in namelist for r in instance.responses
            ):
                instance.taguchi_design = {}
                for response in instance.responses:
                    with zf.open(f"taguchi_design_{response}.csv") as f:
                        instance.taguchi_design[response] = cls._restore_index(
                            pd.read_csv(f, index_col=0)
                        )
            elif "taguchi_design_raw.csv" in namelist:
                with zf.open("taguchi_design_raw.csv") as f:
                    instance.taguchi_design = cls._restore_index(
                        pd.read_csv(f, index_col=0)
                    )
            else:
                instance.taguchi_design = get_array(instance.matrix_name)

        return instance

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        n_factors = len(self.experimental_design)
        n_cols    = len(self.columns)
        n_runs    = len(self.experiences)
        return (
            f"TaguchiDesign("
            f"matrix={self.matrix_name!r}, "
            f"factors={n_factors}, "
            f"columns={n_cols}, "
            f"runs={n_runs}"
            f")"
        )
            f"runs={n_runs}"
            f")"
        )
        )
 = cls._restore_index(
                        pd.read_csv(f, index_col=0)
                    )
            else:
                instance.taguchi_design = get_array(instance.matrix_name)

        return instance

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        n_factors = len(self.experimental_design)
        n_cols    = len(self.columns)
        n_runs    = len(self.experiences)
        return (
            f"TaguchiDesign("
            f"matrix={self.matrix_name!r}, "
            f"factors={n_factors}, "
            f"columns={n_cols}, "
            f"runs={n_runs}"
            f")"
        )
