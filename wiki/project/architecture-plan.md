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

# Architecture Plan

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
