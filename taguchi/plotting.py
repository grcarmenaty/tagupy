"""Convenience plotting wrappers for TaguchiDesign.

This module provides standalone functions for common plotting operations.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .design import TaguchiDesign


def pareto_plot(design: "TaguchiDesign", **kwargs) -> None:
    """Convenience wrapper for TaguchiDesign.pareto_plot().

    Parameters
    ----------
    design : TaguchiDesign
        The design object to plot.
    **kwargs
        Passed to TaguchiDesign.pareto_plot().
    """
    design.pareto_plot(**kwargs)


def effect_plots(design: "TaguchiDesign", **kwargs) -> None:
    """Convenience wrapper for TaguchiDesign.effect_plots().

    Parameters
    ----------
    design : TaguchiDesign
        The design object to plot.
    **kwargs
        Passed to TaguchiDesign.effect_plots().
    """
    design.effect_plots(**kwargs)
