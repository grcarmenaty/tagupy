"""Taguchi experimental design library.

A production-quality library for Taguchi design of experiments,
orthogonal arrays, and signal-to-noise analysis.
"""

from .design import TaguchiDesign
from .arrays import AVAILABLE_ARRAYS, get_array, get_assignation

__all__ = ["TaguchiDesign", "AVAILABLE_ARRAYS", "get_array", "get_assignation"]
__version__ = "0.1.0"
