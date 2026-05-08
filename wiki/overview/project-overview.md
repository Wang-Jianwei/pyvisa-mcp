---
title: Project Overview
status: active
updated: 2026-05-08
tags:
  - project
  - overview
  - pyvisa
  - mcp
source_notes:
  - ../../raw/notes/2026-05-08-project-decisions.md
  - ../../raw/notes/2026-05-08-pyvisa-basics.md
  - ../../raw/notes/2026-05-08-mcp-basics.md
  - ../../raw/notes/2026-05-08-scpi-basics.md
---

# Project Overview

## Goal

Build a Python MCP server that wraps PyVISA capabilities in a way that is practical for AI-assisted instrument control.

## Repository role

This repository is both:
- a future Python implementation workspace
- a maintained project wiki following the pattern described in [../../llm-wiki.md](../../llm-wiki.md)

## Scope baseline

- Python only
- STDIO first
- FastMCP first
- PyVISA high-level API first
- Design complete enough for growth, implementation phased for practicality

## Knowledge workflow

- `raw/` stores source-oriented captures and decision baselines.
- `wiki/` stores maintained summaries and project-facing synthesis.
- `AGENTS.md` defines how the repository must be maintained.

## Current bootstrap state

The wiki bootstrap phase is focused on making later implementation traceable. The initial knowledge baseline includes:
- PyVISA architecture and backend behavior
- MCP primitives and transport choices
- SCPI command/query patterns
- current scope and implementation decisions

## Next implementation track

See [../project/architecture-plan.md](../project/architecture-plan.md) for the current execution path.
