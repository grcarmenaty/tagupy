"""Tagupy MCP Server — Model Context Protocol interface for Taguchi DoE.

Exposes the full Tagupy / TaguchiDesign API as MCP tools and resources so that
any MCP-compatible AI assistant (Claude Desktop, Open WebUI, etc.) can design
and run Taguchi design-of-experiments workflows through natural-language prompts.

Usage
-----
stdio (default, for Claude Desktop)::

    tagupy-mcp

SSE (HTTP, for remote / multi-client deployments)::

    tagupy-mcp --transport sse [--host 0.0.0.0] [--port 8000]

Install::

    pip install -e ".[mcp]"          # inside taguchi_lib/
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
