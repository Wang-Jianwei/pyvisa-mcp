# 2026-05-08 MCP Basics

## Summary

Model Context Protocol (MCP) is an open standard for connecting AI applications to external systems through a client-server model. For this project, MCP is the protocol surface that will expose PyVISA-backed instrument capabilities to AI hosts.

## Core concepts

- MCP uses a client-server architecture.
- Important participants:
  - Host: the AI application, such as VS Code or another MCP-capable client.
  - Client: the connection manager created by the host for a specific server.
  - Server: the program that provides tools, resources, and prompts.
- MCP is stateful and begins with an `initialize` handshake plus capability negotiation.
- The data layer uses JSON-RPC 2.0.

## Server primitives

### Tools
- Model-controlled operations.
- Expose actions with JSON Schema input definitions.
- Discovered via `tools/list` and executed via `tools/call`.
- Best for instrument actions such as open, read, write, query, close, and attribute mutation.

### Resources
- Application-controlled contextual data.
- Expose fixed URIs or URI templates.
- Retrieved through resource list/read flows.
- Best for passive or read-mostly state such as visible resources, backend info, session summaries, or capability documentation.

### Prompts
- User-controlled reusable templates.
- Good for guided workflows, but likely secondary in the first implementation phase.

## Transport notes

- STDIO is a local transport based on standard input/output.
- Streamable HTTP is the preferred production transport in official docs.
- For this project, phase 1 should prioritize STDIO and keep HTTP as a later expansion path.

## SDK notes

- Official SDK tiers list Python as Tier 1.
- The Python SDK supports:
  - FastMCP for high-level server construction
  - low-level server APIs for more direct protocol control
  - stdio and HTTP transports
- FastMCP is the best fit for a first implementation because it reduces protocol boilerplate and aligns with official development tooling.

## Python SDK implementation notes

- FastMCP provides decorators for tools, resources, and prompts.
- FastMCP supports structured output from Python type annotations.
- Lifespan hooks can initialize shared application state.
- The SDK includes development workflows such as `uv run mcp dev server.py` for FastMCP-based servers.
- The low-level server API offers finer protocol control but is not necessary for the first milestone.

## Relevance to this project

- The MCP server should start with FastMCP and structured tool/resource schemas.
- The server should separate active instrument operations from passive context publication.
- The first transport should be STDIO.

## Sources

- https://modelcontextprotocol.io/introduction
- https://modelcontextprotocol.io/docs/learn/architecture
- https://modelcontextprotocol.io/docs/learn/server-concepts
- https://modelcontextprotocol.io/docs/sdk
- https://github.com/modelcontextprotocol/python-sdk
- https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md
