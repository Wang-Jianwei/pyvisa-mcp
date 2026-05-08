---
title: MCP
status: active
updated: 2026-05-08
tags:
  - concept
  - mcp
  - protocol
source_notes:
  - ../../raw/notes/2026-05-08-mcp-basics.md
---

# MCP

## What matters here

MCP is the protocol layer that lets an AI host discover and use the capabilities exposed by this project.

## Participants

- Host: the AI application that connects to servers
- Client: the host-side connection for a specific server
- Server: this project, exposing PyVISA-backed capabilities

## Primitives

### Tools

Use tools for actions and state changes.

Examples for this project:
- open a VISA resource
- write a command
- query an instrument
- set a timeout
- close a session

### Resources

Use resources for passive or read-mostly context.

Examples for this project:
- visible resource inventory
- backend diagnostic information
- session summaries
- capability descriptions

### Prompts

Prompts are reusable user-invoked templates. They are useful later, but are not a phase-1 requirement.

## Transport position

- Phase 1 should use STDIO.
- Streamable HTTP should remain a planned later extension.

## Implementation choice

Use FastMCP first because it provides a direct path to typed tools/resources and works well with the official Python SDK workflow.
