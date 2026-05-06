"""Tests for the analyze() method."""

import pytest
import pandas as pd
import numpy as np
from taguchi.design import TaguchiDesign


class TestAnalyzeBasic:
    """Basic analysis tests."""

    def test_analyze_low_high_columns(self):
        """Test that analyze() creates Low and High columns."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0] * 10}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        assert "A (Low)" in df.columns
        assert "A (High)" in df.columns
        assert "B (Low)" in df.columns
        assert "B (High)" in df.columns

    def test_analyze_effect_columns(self):
        """Test that analyze() creates Effect columns."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0]}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        assert "A Effect" in df.columns

    def test_analyze_contribution_columns(self):
        """Test that analyze() creates Contribution columns."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"result": sum(factors)}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        assert "A Contribution" in df.columns
        assert "B Contribution" in df.columns

    def test_contributions_sum_to_100(self):
        """Test that contributions sum to 100%."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0] + factors[1] / 10}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        contributions = df[["A Contribution", "B Contribution"]].iloc[-1]
        total = contributions.sum()
        assert abs(total - 100) < 0.1


class TestAnalyzeWithRepetitions:
    """Analysis tests with multiple repetitions."""

    def test_analyze_with_reps_creates_average(self):
        """Test that analyze() with reps creates average columns."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0] + factors[-1] * 0.1}

        design.run(mock_func, ["result"], repetitions=3)
        design.analyze()

        df = design.taguchi_design["result"]
        assert "result average" in df.columns
        assert "result standard deviation" in df.columns

    def test_analyze_with_reps_creates_analysis(self):
        """Test that analyze() with reps analyzes average and std."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0]}

        design.run(mock_func, ["result"], repetitions=2)
        design.analyze()

        df = design.taguchi_design["result"]
        # Should have analysis rows for both average and std
        assert "A (Low)" in df.columns


class TestAnalyzeMultipleResponses:
    """Tests with multiple responses."""

    def test_analyze_multiple_responses(self):
        """Test analyze() with multiple responses."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"r1": factors[0], "r2": factors[0] * 2}

        design.run(mock_func, ["r1", "r2"], repetitions=1)
        design.analyze()

        assert "r1" in design.taguchi_design
        assert "r2" in design.taguchi_design

        df1 = design.taguchi_design["r1"]
        df2 = design.taguchi_design["r2"]

        assert "A (Low)" in df1.columns
        assert "A (Low)" in df2.columns
        assert "A Contribution" in df1.columns
        assert "A Contribution" in df2.columns

    def test_analyze_independent_results(self):
        """Test that analysis is independent for each response."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"r1": factors[0], "r2": factors[0] ** 2}

        design.run(mock_func, ["r1", "r2"], repetitions=1)
        design.analyze()

        df1 = design.taguchi_design["r1"]
        df2 = design.taguchi_design["r2"]

        # Effects should be different
        effect1 = df1["A Effect"].iloc[-1]
        effect2 = df2["A Effect"].iloc[-1]
        assert effect1 != effect2


class TestAnalyzeNumericalCorrectness:
    """Tests for numerical correctness of analysis."""

    def test_effect_calculation(self):
        """Test that effects are calculated correctly."""
        design_spec = {"A": [0, 10]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0]}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        # Low level = 0, High level = 10
        # All low runs should average to 0, all high runs to 10
        low_mean = df["A (Low)"].iloc[-1]
        high_mean = df["A (High)"].iloc[-1]
        effect = df["A Effect"].iloc[-1]

        assert abs(low_mean - 0) < 0.01
        assert abs(high_mean - 10) < 0.01
        assert abs(effect - 10) < 0.01

    def test_ss_calculation(self):
        """Test that sum of squares is calculated correctly."""
        design_spec = {"A": [1, 3]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0]}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        effect = df["A Effect"].iloc[-1]
        ss = df["A SS"].iloc[-1]

        # SS should be effect squared
        expected_ss = effect ** 2
        assert abs(ss - expected_ss) < 0.01
