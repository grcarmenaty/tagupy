# Tagupy MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes the full **Tagupy** Taguchi design-of-experiments library as AI-callable tools.  Any MCP-compatible assistant — Claude Desktop, Open WebUI, Continue.dev, etc. — can design and run Taguchi experiments through natural-language prompts.

---

## Contents

- [What It Does](#what-it-does)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Connecting to Claude Desktop](#connecting-to-claude-desktop)
- [Connecting to Other MCP Clients](#connecting-to-other-mcp-clients)
- [Exposed Tools](#exposed-tools)
- [Exposed Resources](#exposed-resources)
- [End-to-End Example](#end-to-end-example)
- [Troubleshooting](#troubleshooting)

---

## What It Does

The server wraps `TaguchiDesign` (and the `arrays` module) in eleven MCP tools and two MCP resources:

| Tool | Purpose |
|---|---|
| `list_arrays` | List available orthogonal arrays (L8/L16/L32/L32-inv) and their properties |
| `create_experiment` | Define factors & levels, choose array, assign columns → returns experiment ID |
| `get_orthogonal_array` | Retrieve the full run matrix (which factor combinations to test) |
| `add_results` | Supply measured response values — one per run (or nested for repetitions) |
| `analyze` | Compute factor effects, SS, % contributions, grand mean |
| `get_factor_effects` | Focused factor-effect table, sorted by contribution |
| `get_optimal_levels` | Additive-model optimal combination + predicted response |
| `plot_main_effects` | Main-effect (and interaction) plots → PNG files |
| `plot_pareto` | Pareto contribution charts → PNG files |
| `save_experiment` | Serialise experiment state to a `.zip` archive |
| `load_experiment` | Restore experiment from a `.zip` archive |

Two **resources** (GET-able URIs) are also available:

| Resource | Content |
|---|---|
| `tagupy://arrays` | Metadata for all built-in arrays |
| `tagupy://experiment/{id}` | Live state snapshot of a running experiment |

---

## Prerequisites

- Python ≥ 3.10
- `taguchi_lib` package installed (see main `README.md`)
- `mcp` Python package (installed via the `[mcp]` optional extra below)

---

## Installation

From inside the `taguchi_lib/` directory:

```bash
pip install -e ".[mcp]"
```

This installs the `tagupy-mcp` console-script entry point along with the `mcp` SDK dependency.

To verify the installation:

```bash
tagupy-mcp --help
```

Expected output:

```
usage: tagupy-mcp [-h] [--transport {stdio,sse}] [--host HOST] [--port PORT]

Tagupy MCP Server — Taguchi design of experiments via MCP.
...
```

---

## Running the Server

### stdio transport (recommended for Claude Desktop)

```bash
tagupy-mcp
# or explicitly:
tagupy-mcp --transport stdio
```

The server reads MCP messages from **stdin** and writes responses to **stdout**.  This is the standard mode used by Claude Desktop and most local MCP clients.

### SSE / HTTP transport (for remote or multi-client deployments)

```bash
tagupy-mcp --transport sse
# custom host/port:
tagupy-mcp --transport sse --host 127.0.0.1 --port 9000
```

The server starts an HTTP server and exposes the MCP protocol over Server-Sent Events at `http://<host>:<port>/sse`.

---

## Connecting to Claude Desktop

1. Locate (or create) the Claude Desktop configuration file:

   | OS | Path |
   |---|---|
   | macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
   | Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
   | Linux | `~/.config/Claude/claude_desktop_config.json` |

2. Add the following entry under `"mcpServers"` (replace the Python path and `taguchi_lib` path with your actual locations):

```json
{
  "mcpServers": {
    "tagupy": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["-m", "tagupy_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/taguchi_lib"
      }
    }
  }
}
```

Or, if `tagupy-mcp` is on your `PATH` (i.e., installed in the active environment):

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

3. Restart Claude Desktop.  You should see **tagupy** listed under **MCP Servers** in the settings panel.

### Full example `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tagupy": {
      "command": "/usr/local/bin/tagupy-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

For a Windows environment where the package is installed in a project venv:

```json
{
  "mcpServers": {
    "tagupy": {
      "command": "C:\\Users\\YourName\\projects\\taguchi_lib\\.venv\\Scripts\\python.exe",
      "args": ["-m", "tagupy_mcp.server"],
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\projects\\taguchi_lib"
      }
    }
  }
}
```

---

## Connecting to Other MCP Clients

### SSE endpoint (Open WebUI, Continue.dev, etc.)

Start the server in SSE mode:

```bash
tagupy-mcp --transport sse --host 0.0.0.0 --port 8000
```

Then point your MCP client to: `http://localhost:8000/sse`

### Python MCP client (testing / scripting)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="tagupy-mcp",
    args=[],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print([t.name for t in tools.tools])
```

---

## Exposed Tools

### `list_arrays`

Returns metadata for all built-in orthogonal arrays.  Call this first to pick the right array for your experiment.

**No parameters.**

**Returns:** JSON with an `arrays` list — name, runs, columns, max_factors, description, assignation table.

---

### `create_experiment`

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `factors` | `dict[str, list]` | ✅ | `{"Factor name": [low_value, high_value], ...}` |
| `assignation` | `list[int]` | ✅ | Zero-based column index per factor |
| `matrix` | `str` | — | `"L8"`, `"L16"` (default), `"L32"`, `"L32-inv"` |
| `name` | `str` | — | Human-readable experiment label |

**Returns:** `experiment_id` (UUID), matrix preview, full run matrix.

**Example prompt:** *"Create a Taguchi L8 experiment with factors Learning rate (low=0.0001, high=0.001), Batch size (low=16, high=64), and Dropout (low=0.2, high=0.5), assigned to columns 0, 3, 5."*

---

### `get_orthogonal_array`

**Parameters:** `experiment_id` (str)

**Returns:** Full run matrix with actual factor values per run.

---

### `add_results`

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `experiment_id` | `str` | ✅ | UUID from `create_experiment` |
| `results` | `dict[str, list]` | ✅ | Response name → list of floats (one per run), or list of lists for repetitions |
| `repetitions` | `int` | — | Number of reps per run (default `1`) |

**Single-rep example:**
```json
{
  "experiment_id": "...",
  "results": {
    "accuracy": [0.85, 0.87, 0.82, 0.91, 0.88, 0.79, 0.93, 0.86]
  }
}
```

**Multi-rep example (2 repetitions, 8 runs):**
```json
{
  "experiment_id": "...",
  "results": {
    "accuracy": [
      [0.85, 0.86], [0.87, 0.88], [0.82, 0.80],
      [0.91, 0.92], [0.88, 0.87], [0.79, 0.81],
      [0.93, 0.94], [0.86, 0.85]
    ]
  },
  "repetitions": 2
}
```

---

### `analyze`

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `experiment_id` | `str` | ✅ | UUID |
| `response` | `str` | — | Specific response to analyse (default: all) |

**Returns:** Per-column low/high means, effects, SS, contribution %, grand mean.

---

### `get_factor_effects`

**Parameters:** `experiment_id`, `response`, `sort_by` (`"contribution_pct"` / `"effect"` / `"column"`)

---

### `get_optimal_levels`

**Parameters:** `experiment_id`, `response`, `optimize` (`"maximize"` / `"minimize"`)

**Returns:** Grand mean, optimal level per factor, additive model prediction.

---

### `plot_main_effects`

**Parameters:** `experiment_id`, `response` (optional), `output_dir` (optional), `font_family`, `font_size`

**Returns:** Absolute paths of all generated PNG files.

---

### `plot_pareto`

Same parameters as `plot_main_effects`.

**Returns:** Absolute paths of Pareto PNG files.

---

### `save_experiment`

**Parameters:** `experiment_id`, `path` (destination `.zip` file path)

---

### `load_experiment`

**Parameters:** `path` (`.zip` file), `name` (optional label)

**Returns:** New `experiment_id` for this session.

---

## Exposed Resources

### `tagupy://arrays`

Static resource listing all arrays — subscribe to keep an always-fresh array catalogue in the client context.

### `tagupy://experiment/{id}`

Live state of one experiment, updated after every tool call.

---

## End-to-End Example

Here is a complete conversation you might have with Claude Desktop after connecting this server:

---

**You:** I'm designing a CNN hyperparameter study.  My factors are: Learning rate (0.0001 vs 0.001), Batch size (16 vs 64), Num filters (16 vs 64), Dropout (0.2 vs 0.5).  Use an L16 array.

**Claude:** *(calls `create_experiment` with the four factors and suitable column assignments, e.g. `[0, 2, 4, 6]` for independent main effects)*

I've created experiment `a1b2c3d4...` on L16 (16 runs).  Here are the 16 factor combinations you need to test...

---

**You:** I've run all 16 experiments. Here are the accuracy results: [0.83, 0.85, 0.79, 0.88, 0.86, 0.81, 0.90, 0.84, 0.87, 0.82, 0.91, 0.85, 0.78, 0.89, 0.83, 0.92].

**Claude:** *(calls `add_results`, then `analyze`)*

Analysis complete.  The most influential factor is **Num filters** with 38.2% contribution, followed by **Learning rate** (27.4%).  Dropout has the smallest effect (6.1%).

---

**You:** What's the optimal configuration to maximise accuracy?

**Claude:** *(calls `get_optimal_levels` with `optimize="maximize"`)*

Optimal combination: Learning rate = 0.001 (High), Batch size = 16 (Low), Num filters = 64 (High), Dropout = 0.2 (Low).  Additive model prediction: **0.892 accuracy**.

---

**You:** Generate the Pareto chart.

**Claude:** *(calls `plot_pareto`)*

Pareto chart saved to `/home/user/tagupy_plots/.../pareto/accuracy.png`.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'taguchi'`**
Make sure `taguchi_lib` is installed: `pip install -e ".[mcp]"` from the `taguchi_lib/` directory.

**`ModuleNotFoundError: No module named 'mcp'`**
Install the MCP optional dependency: `pip install -e ".[mcp]"`.

**Claude Desktop shows "Failed to connect to MCP server"**
- Check that the `command` path in `claude_desktop_config.json` points to the correct Python executable or script.
- Run `tagupy-mcp --transport stdio` manually in a terminal and check for import errors.
- On Windows, use double backslashes or forward slashes in JSON paths.

**Plots not appearing**
The `plot_main_effects` and `plot_pareto` tools save PNGs to disk and return file paths.  Open them with any image viewer.  The default output directory is `./tagupy_plots/<experiment_id>/` relative to the working directory where the server was started.

**"Results have already been added" error**
Each experiment accepts results once.  To re-enter results with different values, call `create_experiment` again to get a fresh experiment ID.
