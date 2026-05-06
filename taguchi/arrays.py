"""Orthogonal array definitions for Taguchi design of experiments.

This module provides access to standard orthogonal arrays (L8, L16, L32, L32-inv)
and their interaction assignation tables. Arrays are stored as immutable raw data
and returned as fresh DataFrames to prevent accidental mutation.
"""

from typing import Optional
import pandas as pd

# Raw orthogonal array data (stored as dicts to avoid mutation at module level)
_ARRAYS_RAW = {
    "L8": {
        "0": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
        "1": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "2": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "3": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "4": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "5": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "6": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
    },
    "L16": {  # noqa: E501
        "0": ["Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level"],
        "1": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
        "2": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "3": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "4": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "5": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "6": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "7": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
        "8": ["High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level"],
        "9": ["High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level"],
        "10": ["High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level"],
        "11": ["High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level"],
        "12": ["High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level"],
        "13": ["High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level"],
        "14": ["High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level"],
    },
    "L32": {  # noqa: E501
        "0": ["Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level"],
        "1": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
        "2": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "3": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "4": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "5": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "6": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "7": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
        "8": ["High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level"],
        "9": ["High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level"],
        "10": ["High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level"],
        "11": ["High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level"],
        "12": ["High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level"],
        "13": ["High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level"],
        "14": ["High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level"],
        "15": ["High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level"],
        "16": ["Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level"],
        "17": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level"],
        "18": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level"],
        "19": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level"],
        "20": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level"],
        "21": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level"],
        "22": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level"],
        "23": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level"],
        "24": ["High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
        "25": ["High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "26": ["High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "27": ["High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "28": ["High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "29": ["High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "30": ["High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
    },
    "L32-inv": {  # noqa: E501
        "0": ["High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level"],
        "1": ["High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level"],
        "2": ["High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level"],
        "3": ["High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level"],
        "4": ["High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level"],
        "5": ["High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level"],
        "6": ["High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level"],
        "7": ["High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level"],
        "8": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
        "9": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "10": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "11": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "12": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "13": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "14": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
        "15": ["Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level"],
        "16": ["High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level"],
        "17": ["High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level"],
        "18": ["High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level"],
        "19": ["High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level"],
        "20": ["High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level"],
        "21": ["High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level"],
        "22": ["High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level"],
        "23": ["High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level"],
        "24": ["Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level"],
        "25": ["Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level"],
        "26": ["Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level"],
        "27": ["Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "High level", "Low level", "High level", "Low level", "High level", "Low level", "High level", "Low level"],
        "28": ["Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level"],
        "29": ["Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "Low level", "Low level", "High level", "High level", "High level", "High level", "Low level", "Low level", "High level", "High level", "Low level", "Low level"],
        "30": ["Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "Low level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "High level", "Low level", "Low level", "Low level", "Low level"],
    },
}

# Assignation tables (interaction assignments)
_ASSIGNATIONS_RAW = {
    "L8": {
        "1": [3, 2, 5, 4, 7, 6],
        "2": [2, 1, 6, 7, 4, 5],
        "3": [5, 6, 7, 6, 5, 4],
        "4": [4, 7, 6, 1, 2, 3],
        "5": [7, 4, 5, 2, 3, 2],
        "6": [6, 5, 4, 3, 2, 1],
    },
    "L16": {
        "1": [3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14],
        "2": [2, 1, 6, 7, 4, 5, 10, 11, 8, 9, 14, 15, 12, 13],
        "3": [5, 6, 7, 6, 5, 4, 13, 14, 15, 14, 13, 12, 11, 10],
        "4": [4, 7, 6, 1, 2, 3, 12, 15, 14, 9, 10, 11, 8, 7],
        "5": [7, 4, 5, 2, 3, 2, 15, 12, 13, 10, 11, 10, 9, 8],
        "6": [6, 5, 4, 3, 2, 1, 14, 13, 12, 11, 10, 9, 7, 6],
        "7": [11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6],
        "8": [10, 13, 12, 15, 14, 15, 14, 13, 12, 11, 10, 9, 6, 5],
        "9": [13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4],
        "10": [12, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3],
        "11": [15, 12, 13, 10, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2],
        "12": [14, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3],
        "13": [9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4],
        "14": [8, 9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5],
    },
    "L32": {
        "1": [3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30],
        "2": [2, 1, 6, 7, 4, 5, 10, 11, 8, 9, 14, 15, 12, 13, 18, 19, 16, 17, 22, 23, 20, 21, 26, 27, 24, 25, 30, 31, 28, 29],
        "3": [5, 6, 7, 6, 5, 4, 13, 14, 15, 14, 13, 12, 11, 10, 21, 22, 23, 22, 21, 20, 19, 18, 29, 30, 31, 30, 29, 28, 27, 26],
        "4": [4, 7, 6, 1, 2, 3, 12, 15, 14, 9, 10, 11, 8, 7, 20, 23, 22, 17, 18, 19, 16, 15, 28, 31, 30, 25, 26, 27, 24, 23],
        "5": [7, 4, 5, 2, 3, 2, 15, 12, 13, 10, 11, 10, 9, 8, 23, 20, 21, 18, 19, 18, 17, 16, 31, 28, 29, 26, 27, 26, 25, 24],
        "6": [6, 5, 4, 3, 2, 1, 14, 13, 12, 11, 10, 9, 7, 6, 22, 21, 20, 19, 18, 17, 15, 14, 30, 29, 28, 27, 26, 25, 23, 22],
        "7": [11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 27, 28, 29, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20],
        "8": [10, 13, 12, 15, 14, 15, 14, 13, 12, 11, 10, 9, 6, 5, 26, 29, 28, 31, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21],
        "9": [13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 29, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18],
        "10": [12, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 28, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17],
        "11": [15, 12, 13, 10, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 31, 28, 29, 26, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16],
        "12": [14, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 30, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13],
        "13": [9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18],
        "14": [8, 9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 24, 25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19],
        "15": [11, 8, 9, 6, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 27, 24, 25, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12],
        "16": [19, 20, 21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4],
        "17": [18, 21, 20, 23, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3],
        "18": [21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 2, 1, 2],
        "19": [20, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1],
        "20": [23, 20, 21, 18, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 1, 4, 3, 2],
        "21": [22, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 1, 4, 3],
        "22": [17, 18, 19, 20, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6],
        "23": [16, 19, 18, 21, 20, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 6, 5],
        "24": [19, 20, 21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4],
        "25": [18, 21, 20, 23, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3],
        "26": [21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 2, 1, 2],
        "27": [20, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1],
        "28": [23, 20, 21, 18, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 1, 4, 3, 2],
        "29": [22, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 1, 4, 3],
        "30": [25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4],
    },
    "L32-inv": {
        "1": [3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30],
        "2": [2, 1, 6, 7, 4, 5, 10, 11, 8, 9, 14, 15, 12, 13, 18, 19, 16, 17, 22, 23, 20, 21, 26, 27, 24, 25, 30, 31, 28, 29],
        "3": [5, 6, 7, 6, 5, 4, 13, 14, 15, 14, 13, 12, 11, 10, 21, 22, 23, 22, 21, 20, 19, 18, 29, 30, 31, 30, 29, 28, 27, 26],
        "4": [4, 7, 6, 1, 2, 3, 12, 15, 14, 9, 10, 11, 8, 7, 20, 23, 22, 17, 18, 19, 16, 15, 28, 31, 30, 25, 26, 27, 24, 23],
        "5": [7, 4, 5, 2, 3, 2, 15, 12, 13, 10, 11, 10, 9, 8, 23, 20, 21, 18, 19, 18, 17, 16, 31, 28, 29, 26, 27, 26, 25, 24],
        "6": [6, 5, 4, 3, 2, 1, 14, 13, 12, 11, 10, 9, 7, 6, 22, 21, 20, 19, 18, 17, 15, 14, 30, 29, 28, 27, 26, 25, 23, 22],
        "7": [11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 27, 28, 29, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20],
        "8": [10, 13, 12, 15, 14, 15, 14, 13, 12, 11, 10, 9, 6, 5, 26, 29, 28, 31, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21],
        "9": [13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 29, 30, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18],
        "10": [12, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 28, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17],
        "11": [15, 12, 13, 10, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 31, 28, 29, 26, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16],
        "12": [14, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 30, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13],
        "13": [9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18],
        "14": [8, 9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 24, 25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19],
        "15": [11, 8, 9, 6, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 27, 24, 25, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12],
        "16": [19, 20, 21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4],
        "17": [18, 21, 20, 23, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3],
        "18": [21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 2, 1, 2],
        "19": [20, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1],
        "20": [23, 20, 21, 18, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 1, 4, 3, 2],
        "21": [22, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 1, 4, 3],
        "22": [17, 18, 19, 20, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6],
        "23": [16, 19, 18, 21, 20, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 6, 5],
        "24": [19, 20, 21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4],
        "25": [18, 21, 20, 23, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3],
        "26": [21, 22, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 2, 1, 2],
        "27": [20, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1],
        "28": [23, 20, 21, 18, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 1, 4, 3, 2],
        "29": [22, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 1, 4, 3],
        "30": [25, 26, 27, 28, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4],
    },
}

AVAILABLE_ARRAYS = ["L8", "L16", "L32", "L32-inv"]


def get_array(name: str) -> pd.DataFrame:
    """Return a fresh copy of the orthogonal array.

    Parameters
    ----------
    name : str
        Name of the array ('L8', 'L16', 'L32', or 'L32-inv').

    Returns
    -------
    pd.DataFrame
        Orthogonal array with "Low level" and "High level" values.
        Row indices are run numbers (0-based).
        Column indices are column labels (string keys).

    Raises
    ------
    ValueError
        If the array name is not recognized.
    """
    if name not in AVAILABLE_ARRAYS:
        raise ValueError(
            f"Unknown array '{name}'. Available: {AVAILABLE_ARRAYS}"
        )
    return pd.DataFrame(_ARRAYS_RAW[name])


def get_assignation(name: str) -> pd.DataFrame:
    """Return a fresh copy of the interaction assignation table.

    Parameters
    ----------
    name : str
        Name of the array ('L8', 'L16', 'L32', or 'L32-inv').

    Returns
    -------
    pd.DataFrame
        Assignation table showing which columns interact with each other.
        Rows are factor indices; columns are interaction partners.

    Raises
    ------
    ValueError
        If the array name is not recognized.
    """
    if name not in AVAILABLE_ARRAYS:
        raise ValueError(
            f"Unknown array '{name}'. Available: {AVAILABLE_ARRAYS}"
        )
    return pd.DataFrame(_ASSIGNATIONS_RAW[name])
