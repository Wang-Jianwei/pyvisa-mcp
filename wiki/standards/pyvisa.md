---
title: PyVISA
status: active
updated: 2026-05-08
tags:
  - standard
  - pyvisa
  - visa
source_notes:
  - ../../raw/notes/2026-05-08-pyvisa-basics.md
---

# PyVISA

## Working model

PyVISA should be treated as a high-level object model centered on `ResourceManager` and resource instances.

## Key architecture notes

- PyVISA documents low-level, middle-level, and high-level layers.
- This project should prefer the high-level layer unless a specific requirement forces otherwise.
- `ResourceManager` is the entry point for backend selection, resource discovery, and resource opening.

## Backends

- Default usage typically relies on the IVI backend.
- Other backends can be selected with the `@backend` suffix.
- Backend discovery and diagnostics are operationally important and should be surfaced by the MCP server.

## Common operations to expose first

- list resources
- open resource
- close resource
- write
- read
- query
- read bytes when needed for troubleshooting
- get/set common attributes
- inspect resource info and current session settings

## Operational concerns

The first implementation should explicitly handle:
- missing VISA library
- architecture mismatch
- invalid session
- timeout configuration
- read/write termination configuration
- query delay and chunk size for message-based devices

## Diagnostics

- `pyvisa-info` is a key environment diagnostic surface.
- `pyvisa-shell` is useful for manual validation and sim-backend testing.
- PyVISA runtime logging is relevant for troubleshooting support.
