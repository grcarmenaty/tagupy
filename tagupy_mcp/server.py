"""Tagupy MCP Server — entry point.

Creates the ``FastMCP`` application, registers all tools and resources from
``tools.py``, and provides a ``main()`` function that is wired to the
``tagupy-mcp`` console-script entry point declared in ``pyproject.toml``.

Transport modes
---------------
stdio (default — use with Claude Desktop and most MCP clients)::

    tagupy-mcp
    tagupy-mcp --transport stdio

SSE / HTTP (for remote or multi-client deployments)::

    tagupy-mcp --transport sse
    tagupy-mcp --transport sse --host 127.0.0.1 --port 9000

See ``README_MCP.md`` for full setup instructions.
"""

from __future__ import annotations

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from .tools import register_resources, register_tools

# ---------------------------------------------------------------------------
# FastMCP application
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="tagupy-mcp",
    instructions=(
        "You are connected to the Tagupy MCP server — a full implementation of "
        "Taguchi design of experiments (DoE) for two-level orthogonal arrays.\n\n"
        "## Typical workflow\n"
        "1. Call `list_arrays` to pick the right orthogonal array (L8/L16/L32/L32-inv).\n"
        "2. Call `create_experiment` with your factors, two levels each, and column "
        "   assignments.\n"
        "3. Call `get_orthogonal_array` to retrieve the run matrix (which combinations "
        "   to test and in which order).\n"
        "4. Run the physical or simulated experiments in the order listed.\n"
        "5. Call `add_results` to supply the measured response values.\n"
        "6. Call `analyze` to compute factor effects, sums of squares, and "
        "   percentage contributions.\n"
        "7. Call `get_factor_effects` or `get_optimal_levels` for a focused summary.\n"
        "8. Call `plot_main_effects` and/or `plot_pareto` to generate figures.\n"
        "9. Call `save_experiment` to persist the design to disk.\n\n"
        "## Available arrays\n"
        "- L8   →  8 runs, up to 7 factors\n"
        "- L16  → 16 runs, up to 15 factors  (most common)\n"
        "- L32  → 32 runs, up to 31 factors\n"
        "- L32-inv → 32 runs, inverted levels\n\n"
        "All factors must be two-level (Low / High). "
        "Results are held in memory for the duration of the session. "
        "Use save_experiment / load_experiment for persistence."
    ),
)

# Register all tools and resources
register_tools(mcp)
register_resources(mcp)

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    """Parse CLI arguments and start the MCP server.

    This function is wired to the ``tagupy-mcp`` console-script entry point.
    It supports two transport modes:

    * **stdio** (default): reads MCP messages from stdin and writes responses
      to stdout.  Use this with Claude Desktop and most CLI-based MCP clients.

    * **sse**: starts an HTTP server that exposes the MCP protocol over
      Server-Sent Events.  Use this for remote deployments or when multiple
      clients need to connect simultaneously.

    Exit codes
    ----------
    0 — clean shutdown.
    1 — argument error or unhandled exception.
    """
    parser = argparse.ArgumentParser(
        prog="tagupy-mcp",
        description="Tagupy MCP Server — Taguchi design of experiments via MCP.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help=(
            "Transport protocol.  "
            "'stdio' (default) for Claude Desktop / local clients; "
            "'sse' for HTTP-based remote clients."
        ),
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind when using --transport sse.  Default: 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind when using --transport sse.  Default: 8000.",
    )

    args = parser.parse_args()

    try:
        if args.transport == "sse":
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
