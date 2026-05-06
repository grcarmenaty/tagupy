"""Tests for the TaguchiDesign class."""

import pytest
import pandas as pd
from taguchi.design import TaguchiDesign


class TestTaguchiDesignInit:
    """Tests for TaguchiDesign initialization."""

    def test_init_basic(self):
        """Test basic initialization with 2 factors."""
        design_spec = {"Factor A": [1, 2], "Factor B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        assert design.experimental_design == design_spec
        assert design.matrix_name == "L8"
        assert design.responses == []
        assert design.repetitions == 1

    def test_init_l16(self):
        """Test initialization with L16 matrix."""
        design_spec = {
            "LR": [1e-4, 1e-3],
            "Batch": [16, 64],
            "Epochs": [10, 100],
            "Dropout": [0.2, 0.5],
        }
        design = TaguchiDesign(design_spec, [0, 2, 4, 6], matrix="L16")

        assert len(design.experimental_matrix) == 16
        assert design.experimental_matrix.shape[1] == 4

    def test_init_invalid_matrix(self):
        """Test that invalid matrix name raises ValueError."""
        design_spec = {"A": [1, 2]}
        with pytest.raises(ValueError):
            TaguchiDesign(design_spec, [0], matrix="L99")

    def test_experimental_matrix_values(self):
        """Test that experimental matrix has correct low/high values."""
        design_spec = {"Factor A": [100, 200], "Factor B": ["Low", "High"]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        # Check that values are substituted correctly
        assert 100 in design.experimental_matrix["Factor A"].values
        assert 200 in design.experimental_matrix["Factor A"].values
        assert "Low" in design.experimental_matrix["Factor B"].values
        assert "High" in design.experimental_matrix["Factor B"].values

    def test_design_isolation(self):
        """Test that multiple instances don't share state."""
        design_spec1 = {"A": [1, 2]}
        design_spec2 = {"B": [3, 4]}

        d1 = TaguchiDesign(design_spec1, [0], matrix="L8")
        d2 = TaguchiDesign(design_spec2, [1], matrix="L8")

        # Modify d1's experimental matrix
        d1.experimental_matrix.iloc[0, 0] = 999

        # d2 should not be affected
        assert d2.experimental_matrix.iloc[0, 0] != 999


class TestTaguchiDesignColumns:
    """Tests for column naming and structure."""

    def test_columns_list(self):
        """Test that columns list is properly populated."""
        design_spec = {"A": [1, 2], "B": [3, 4]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        assert "A" in design.columns
        assert "B" in design.columns

    def test_taguchi_design_is_dataframe_before_run(self):
        """Test that taguchi_design is DataFrame before run()."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        assert isinstance(design.taguchi_design, pd.DataFrame)


class TestTaguchiDesignRun:
    """Tests for the run() method."""

    def test_run_single_response(self):
        """Test running with a single response."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"result": sum(factors)}

        design.run(mock_func, ["result"], repetitions=1)

        assert isinstance(design.taguchi_design, dict)
        assert "result" in design.taguchi_design
        assert design.responses == ["result"]
        assert design.repetitions == 1

    def test_run_multiple_responses(self):
        """Test running with multiple responses."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"r1": factors[0], "r2": factors[0] * 2}

        design.run(mock_func, ["r1", "r2"], repetitions=1)

        assert "r1" in design.taguchi_design
        assert "r2" in design.taguchi_design

    def test_run_with_repetitions(self):
        """Test running with multiple repetitions."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            rep_index = factors[-1]  # Last element is repetition index
            return {"result": factors[0] + rep_index}

        design.run(mock_func, ["result"], repetitions=3)

        assert design.repetitions == 3
        df = design.taguchi_design["result"]
        assert "result average" in df.columns
        assert "result standard deviation" in df.columns

    def test_run_exception_handling(self):
        """Test that exceptions in func are properly re-raised."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def failing_func(factors):
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            design.run(failing_func, ["result"], repetitions=1)


class TestTaguchiDesignAnalyze:
    """Tests for the analyze() method."""

    def test_analyze_basic(self):
        """Test basic analysis functionality."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"result": factors[0] + factors[1] / 10}

        design.run(mock_func, ["result"], repetitions=1)
        design.analyze()

        df = design.taguchi_design["result"]
        assert "A (Low)" in df.columns
        assert "A (High)" in df.columns
        assert "A Effect" in df.columns
        assert "A Contribution" in df.columns

    def test_analyze_requires_run(self):
        """Test that analyze() requires run() to be called first."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        with pytest.raises(RuntimeError):
            design.analyze()


class TestTaguchiDesignSaveLoad:
    """Tests for save() and load() methods."""

    def test_save_and_load(self, tmp_path):
        """Test saving and loading a design."""
        design_spec = {"A": [1, 2], "B": [10, 20]}
        design = TaguchiDesign(design_spec, [0, 1], matrix="L8")

        def mock_func(factors):
            return {"r": factors[0] + factors[1] / 10}

        design.run(mock_func, ["r"], repetitions=1)

        # Save
        save_path = tmp_path / "design.zip"
        design.save(save_path)
        assert save_path.exists()

        # Load
        loaded = TaguchiDesign.load(save_path)
        assert loaded.experimental_design == design_spec
        assert loaded.responses == ["r"]
        assert loaded.repetitions == 1
        assert loaded.matrix_name == "L8"

    def test_load_preserves_data(self, tmp_path):
        """Test that load() preserves experimental data."""
        design_spec = {"A": [1, 2]}
        design = TaguchiDesign(design_spec, [0], matrix="L8")

        def mock_func(factors):
            return {"r": factors[0] ** 2}

        design.run(mock_func, ["r"], repetitions=1)
        design.analyze()

        save_path = tmp_path / "design.zip"
        design.save(save_path)

        loaded = TaguchiDesign.load(save_path)
        original_df = design.taguchi_design["r"]
        loaded_df = loaded.taguchi_design["r"]

        pd.testing.assert_frame_equal(original_df, loaded_df)
