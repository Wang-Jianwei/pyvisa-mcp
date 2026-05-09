---
title: Architecture Plan
status: active
updated: 2026-05-09
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
- `cli.py` - interactive terminal entrypoint for local MCP-driven testing and operator workflows
- `cli_runtime.py` - stdio client/session bridge and REPL command dispatch
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
- a CLI runtime that launches the local server and reuses the official MCP stdio client/session APIs
- backend argument normalization that supports both shorthand backends and explicit `profile.yaml@sim` sim backends
- a `VisaAdapter` with lazy PyVISA integration boundaries
- a `SessionRegistry` for MCP-managed resource sessions
- BaseModel-backed schemas for tools and resources with result counts, operation context, descriptions, and examples
- parameter-level tool schema descriptions so agents can see runtime semantics beyond names and primitive types
- BaseModel-backed result schemas with field-level descriptions that flow into FastMCP output schemas
- targeted schema examples on key input and output fields so agents can see representative session IDs, resource names, commands, attribute names, and error codes
- binary VISA read, write, and query support with explicit `base64` and `temp_file` payload modes
- server-managed temporary binary file cleanup tied to MCP session lifecycle
- optional caller-managed output paths for binary read and query operations when a stable file location is needed beyond session close
- explicit output-file conflict policy so caller-managed captures fail safely by default and only overwrite when requested
- first-pass tool and resource registration functions

## First tool set

- list visible resources
- open resource
- close resource
- write message
- read message
- query message
- write binary message
- read binary message
- query binary message
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
- CLI command dispatch tests for REPL session reuse and output mode changes
- CLI process integration against the repository-local sim backend over a real stdio MCP session
- tool schema checks that confirm FastMCP exposes parameter descriptions to agents
- output schema checks that confirm FastMCP exposes result-field descriptions to agents
- schema checks that confirm FastMCP exposes representative examples for key input and output fields
- mocked binary tool coverage for base64 and temporary-file payload paths
- session-registry cleanup checks for server-managed temporary binary files
- sim-backed binary query validation through the repository-local `pyvisa-sim` profile and the CLI process path
- explicit-output-file checks proving caller-managed binary captures survive session close
- overwrite-policy checks proving existing caller-managed files are preserved by default and replaced only when explicitly requested

The next verification step should focus on broader sim-profile command coverage beyond the current `*IDN?` and UTF-8-backed binary `CURV?` paths, plus richer CLI command coverage for attribute and resource-info workflows.
