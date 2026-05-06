"""Tests for the arrays module."""

import pytest
import pandas as pd
from taguchi.arrays import get_array, get_assignation, AVAILABLE_ARRAYS


class TestArrayFunctions:
    """Tests for array access functions."""

    def test_get_array_l8(self):
        """Test L8 array retrieval."""
        arr = get_array("L8")
        assert isinstance(arr, pd.DataFrame)
        assert arr.shape == (8, 7)

    def test_get_array_l16(self):
        """Test L16 array retrieval."""
        arr = get_array("L16")
        assert isinstance(arr, pd.DataFrame)
        assert arr.shape == (16, 15)

    def test_get_array_l32(self):
        """Test L32 array retrieval."""
        arr = get_array("L32")
        assert isinstance(arr, pd.DataFrame)
        assert arr.shape == (32, 31)

    def test_get_array_l32_inv(self):
        """Test L32-inv array retrieval."""
        arr = get_array("L32-inv")
        assert isinstance(arr, pd.DataFrame)
        assert arr.shape == (32, 31)

    def test_get_array_invalid(self):
        """Test that invalid array name raises ValueError."""
        with pytest.raises(ValueError):
            get_array("L99")

    def test_array_isolation(self):
        """Test that modifying returned array doesn't affect future calls."""
        arr1 = get_array("L8")
        arr1.iloc[0, 0] = "Modified"

        arr2 = get_array("L8")
        assert arr2.iloc[0, 0] != "Modified"

    def test_get_assignation_l8(self):
        """Test L8 assignation table retrieval."""
        assign = get_assignation("L8")
        assert isinstance(assign, pd.DataFrame)
        assert assign.shape == (6, 6)

    def test_get_assignation_l16(self):
        """Test L16 assignation table retrieval."""
        assign = get_assignation("L16")
        assert isinstance(assign, pd.DataFrame)
        assert assign.shape[0] == 14

    def test_get_assignation_invalid(self):
        """Test that invalid assignation name raises ValueError."""
        with pytest.raises(ValueError):
            get_assignation("L99")

    def test_assignation_isolation(self):
        """Test that modifying assignation doesn't affect future calls."""
        a1 = get_assignation("L8")
        a1.iloc[0, 0] = -9999

        a2 = get_assignation("L8")
        assert a2.iloc[0, 0] != -9999

    def test_available_arrays(self):
        """Test that AVAILABLE_ARRAYS contains all expected arrays."""
        assert "L8" in AVAILABLE_ARRAYS
        assert "L16" in AVAILABLE_ARRAYS
        assert "L32" in AVAILABLE_ARRAYS
        assert "L32-inv" in AVAILABLE_ARRAYS
        assert len(AVAILABLE_ARRAYS) == 4

    def test_array_content_low_high(self):
        """Test that arrays contain only Low/High level values."""
        for array_name in AVAILABLE_ARRAYS:
            arr = get_array(array_name)
            unique_vals = set()
            for col in arr.columns:
                unique_vals.update(arr[col].unique())
            assert unique_vals == {"Low level", "High level"}
