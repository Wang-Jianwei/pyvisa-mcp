# PyVISA MCP

PyVISA MCP is a Python MCP server project for instrument control. It is being built around PyVISA for device communication and FastMCP for protocol exposure.

This repository is intentionally dual-purpose:

- a Python implementation workspace
- an LLM-maintained project wiki under `raw/` and `wiki/`

## Current status

The repository currently includes:

- wiki bootstrap and project records
- initial raw research notes for PyVISA, MCP, SCPI, and project decisions
- a first Python package scaffold
- a first FastMCP server entrypoint and typed tool/resource schema layer
- context-rich tool and resource result models with counts and resource metadata
- a sim-backed smoke test path using `pyvisa-sim` custom profiles
- a first interactive CLI mode that launches the local server and talks to it through a real MCP stdio session

## Planned implementation path

1. Python package scaffold
2. FastMCP server entrypoint
3. PyVISA adapter layer
4. Session registry
5. Tool and resource schema refinement
6. Tests and environment diagnostics

## Install

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
pip install -e .
```

To run the sim-backed smoke validation:

```bash
pip install -e .[dev,sim]
```

## Packaging

Build wheel and sdist locally:

```bash
python -m build --no-isolation
```

When using `--no-isolation`, install the build backend into the current environment first:

```bash
python -m pip install -U setuptools wheel build
python -m build --no-isolation
```

In this repository, if you are using the checked-in virtual environment, run:

```bash
.venv\Scripts\python.exe -m pip install -U setuptools wheel build
.venv\Scripts\python.exe -m build --no-isolation
```

## Run

```bash
python -m pyvisa_mcp.server
```

Or, after installation:

```bash
pyvisa-mcp
```

## CLI

Launch the interactive CLI against the local server:

```bash
pyvisa-mcp-cli
```

Launch it against the repository-local sim backend:

```bash
pyvisa-mcp-cli --backend tests/fixtures/pyvisa_sim.yaml@sim
```

Useful first commands inside the REPL:

- `help`
- `backend`
- `visible ?*`
- `open ASRL2::INSTR --timeout-ms 2500`
- `query "*IDN?"`
- `close`
- `exit`

For debugging and automated interaction, the CLI also supports:

- `--json` to render responses as JSON
- `--no-prompt` to suppress the prompt when driving the REPL from piped stdin

## Test

```bash
python -m unittest discover -s tests
```

The sim-backed smoke test uses a repository-local `pyvisa-sim` profile and exercises the adapter through a real `profile.yaml@sim` backend argument.
The CLI integration test also drives that same sim backend through a real stdio MCP session.

## First exposed capabilities

Tools:

- list visible resources
- open resource
- close resource
- write message
- read message
- query message
- inspect resource info
- get backend diagnostics
- get/set resource attributes

Resources:

- backend status
- visible resource inventory
- current session registry snapshot
- project capability summary

## Knowledge base entry points

- `AGENTS.md` for repository workflow rules
- `wiki/index.md` for the maintained knowledge index
- `wiki/log.md` for the chronological activity log
