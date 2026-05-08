# 2026-05-08 Project Decisions

## Confirmed scope

- Current project scope is Python only.
- The earlier mention of a C++ server is ignored.
- The repository must be bootstrapped as both:
  - an implementation workspace
  - an LLM-maintained project wiki

## Confirmed technical direction

- Phase 1 transport priority is STDIO.
- Prefer FastMCP for the first MCP server implementation.
- Prefer PyVISA high-level APIs and object model over exposing raw VISA functions.
- Design should anticipate wider coverage, but implementation may proceed in phases.

## Workflow decisions

- Before substantive code work, bootstrap the wiki framework.
- Important research findings must be written to `raw/` and then synthesized into `wiki/`.
- Important decisions must not live only in chat.
- `wiki/index.md` and `wiki/log.md` are mandatory maintenance files.

## Initial implementation track

1. Wiki bootstrap and project record setup
2. Python package scaffold
3. FastMCP server entrypoint
4. PyVISA adapter layer
5. Session registry
6. Tool and resource schema design
7. Tests and environment diagnostics
