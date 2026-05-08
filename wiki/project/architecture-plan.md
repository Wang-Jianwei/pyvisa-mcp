---
title: Architecture Plan
status: active
updated: 2026-05-08
tags:
  - project
  - architecture
  - implementation
source_notes:
  - ../../raw/notes/2026-05-08-project-decisions.md
  - ../../raw/notes/2026-05-08-pyvisa-basics.md
  - ../../raw/notes/2026-05-08-mcp-basics.md
  - ../../raw/notes/2026-05-08-scpi-basics.md
---

## Architecture Plan

## Phase order

1. Wiki bootstrap and project records
2. Python package scaffold
3. FastMCP server entrypoint
4. PyVISA adapter layer
5. Session registry
6. Tools and resources schema design
7. Tests and environment diagnostics

## Proposed module split

- `server.py` - FastMCP entrypoint and lifespan wiring
- `config.py` - runtime configuration for backend selection and environment handling
- `visa_adapter.py` - concentrated PyVISA integration and error normalization
- `session_registry.py` - opened resource lifecycle and MCP-facing session IDs
- `schemas.py` - input/output models for tools and resources
- `tools.py` - action-oriented MCP tools
- `resources.py` - passive context resources

## Current scaffold output

The repository now includes a first-pass Python scaffold matching the proposed split:

- `pyproject.toml` for packaging and dependencies
- `README.md` for project entry instructions
- `src/pyvisa_mcp/` for the main package
- `tests/` for the first stdlib-only bootstrap tests

The code currently provides:

- a FastMCP server factory and entrypoint
- a `ServerConfig` environment-backed configuration model
- backend argument normalization that supports both shorthand backends and explicit `profile.yaml@sim` sim backends
- a `VisaAdapter` with lazy PyVISA integration boundaries
- a `SessionRegistry` for MCP-managed resource sessions
- dataclass-based schemas for tools and resources with result counts and operation context
- first-pass tool and resource registration functions

## First tool set

- list visible resources
- open resource
- close resource
- write message
- read message
- query message
- inspect resource info
- get diagnostic/environment information
- get or set selected resource attributes

## First resource set

- backend status
- visible resource inventory
- current session registry snapshot
- project capability summary

## Testing strategy

- unit tests with mocks around adapter and registry logic
- sim-backend or shell-assisted validation where practical
- real hardware smoke tests only as a second layer

## Current verification depth

The repository now has stdlib-only tests for:

- configuration defaults and environment overrides
- session registry open/close behavior
- tool-layer attribute coercion and session updates
- mocked tool flow for list/open/query/close
- mocked `VisaAdapter` behavior for resource discovery, open, message operations, and resource info reads
- structured error returns for adapter and tool failure paths
- passive resource JSON serialization with counts and capability inventory
- `pyvisa-sim` smoke validation through a custom repository-local sim profile
- server-level FastMCP integration checks for registered tools, registered resources, and session-backed tool flow

The next verification step should focus on broader sim-profile command coverage beyond the current `*IDN?` path and, later, transport-level end-to-end checks around actual MCP client/server execution.
