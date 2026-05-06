# MCP Server

The `tagupy_mcp` package exposes the full TaguchiDesign API as a [Model Context Protocol](https://modelcontextprotocol.io/) server, so any MCP-compatible AI assistant (Claude Desktop, Open WebUI, Continue.dev, …) can design and run Taguchi experiments through natural-language prompts.

This page summarises the surface area; the canonical reference is `README_MCP.md` at the repository root.

## Install

From inside the repository:

```bash
pip install -e ".[mcp]"
```

That installs the `tagupy-mcp` console script and the `mcp ≥ 1.0` dependency. Verify with:

```bash
tagupy-mcp --help
```

## Run

| Mode | Command | Use case |
|---|---|---|
| stdio (default) | `tagupy-mcp` *or* `tagupy-mcp --transport stdio` | Claude Desktop and most local MCP clients. |
| SSE / HTTP | `tagupy-mcp --transport sse [--host 0.0.0.0] [--port 8000]` | Remote or multi-client deployments; endpoint `http://<host>:<port>/sse`. |

## Connect to Claude Desktop

Add to `claude_desktop_config.json` (location depends on OS — see `README_MCP.md`):

```json
{
  "mcpServers": {
    "tagupy": {
      "command": "tagupy-mcp",
      "args": []
    }
  }
}
```

Restart Claude Desktop. The `tagupy` server should appear under **MCP Servers**.

## Tools (11)

| Tool | Purpose |
|---|---|
| `list_arrays` | Metadata for L8 / L16 / L32 / L32-inv plus their assignation tables. |
| `create_experiment` | Define factors, levels, array, column assignment → returns `experiment_id`. |
| `get_orthogonal_array` | Full run matrix for a given experiment. |
| `add_results` | Supply measured response values (single or per-repetition). |
| `analyze` | Compute effects, SS, % contributions, grand mean. |
| `get_factor_effects` | Sorted factor-effect table for one response. |
| `get_optimal_levels` | Additive-model optimum + predicted response (maximise / minimise). |
| `plot_main_effects` | PNG main-effect / interaction plots. |
| `plot_pareto` | PNG Pareto contribution charts. |
| `save_experiment` | Serialise to `.zip` archive. |
| `load_experiment` | Restore a previously saved experiment. |

### Typical session

1. `list_arrays` → pick an array.
2. `create_experiment` → define factors and assignation, receive `experiment_id`.
3. `get_orthogonal_array` → run those factor combinations in your lab/simulator.
4. `add_results` → push measurements back.
5. `analyze` → factor effects + contributions.
6. `get_factor_effects` and/or `get_optimal_levels` → focused summary.
7. `plot_main_effects` / `plot_pareto` → figures saved to disk.
8. `save_experiment` → persist to `.zip`.

## Resources (2)

| URI | Content |
|---|---|
| `tagupy://arrays` | Live metadata for all built-in arrays. |
| `tagupy://experiment/{id}` | Full state snapshot of one running experiment. |

## In-memory store

Experiments live in the dict `tagupy_mcp.tools._EXPERIMENTS` for the duration of the process. Each entry carries:

```python
{
    "experiment_id": str,
    "name":          str,
    "design":        TaguchiDesign,
    "created_at":    str,           # ISO-8601 UTC
    "state":         str,           # 'created' | 'has_results' | 'analyzed'
    "plot_dir":      str,           # last directory used for plots
}
```

State transitions are linear: `created → has_results → analyzed`. To re-enter results for a different scenario, call `create_experiment` again to obtain a fresh ID — `add_results` refuses to overwrite.

## Adding measurements without running through Python

Use `add_results` whenever the experiments were carried out outside the library (lab measurements, external simulators, etc.). The helper `_add_results_to_design()` in `tagupy_mcp.tools` replicates the internal state changes that `TaguchiDesign.run()` performs, so `analyze`, `pareto_plot`, and `effect_plots` all work afterwards.

Two formats are accepted:

```python
# Single measurement per run
{"accuracy": [0.85, 0.87, 0.82, 0.91, 0.88, 0.79, 0.93, 0.86]}

# Multiple repetitions per run
{"accuracy": [[0.85, 0.86], [0.87, 0.88], ...]}    # repetitions=2
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'taguchi'`** — install with `pip install -e ".[mcp]"` from the repo root.
- **`ModuleNotFoundError: No module named 'mcp'`** — same fix; the `[mcp]` extra pulls in the SDK.
- **Claude Desktop "Failed to connect"** — verify the `command` path in `claude_desktop_config.json`. On Windows, use double backslashes or forward slashes in JSON paths. Run `tagupy-mcp --transport stdio` manually to surface import errors.
- **Plots not appearing** — they are saved to disk; the tool returns absolute paths. Default directory is `./tagupy_plots/<experiment_id>/<effects|pareto>/` relative to the CWD where the server was started.
- **"Results have already been added"** — each experiment accepts `add_results` once. Call `create_experiment` again for a fresh ID.
