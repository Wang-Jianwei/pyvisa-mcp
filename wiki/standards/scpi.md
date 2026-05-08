---
title: SCPI
status: active
updated: 2026-05-08
tags:
  - standard
  - scpi
  - instrument-control
source_notes:
  - ../../raw/notes/2026-05-08-scpi-basics.md
  - ../../raw/notes/2026-05-08-pyvisa-basics.md
---

# SCPI

## Role in this project

SCPI is not the transport layer. It is usually the instrument command language transported through PyVISA message-based operations.

## Practical interaction model

- Commands set state or trigger actions.
- Queries end with `?` and return data.
- `*IDN?` is the natural first smoke-test query for instrument communication.

## Why SCPI matters to the MCP design

Many of the first MCP tools will either:
- send raw SCPI strings
- wrap common SCPI workflows in more structured tool interfaces

## Common failure modes

Most early communication failures will not be “SCPI is unsupported” but one of:
- wrong read termination
- wrong write termination
- timeout too short
- instrument-specific response timing
- command accepted but response not read correctly

## Design implication

The server should support both:
- low-level command/query style access for expert users
- higher-level workflows around common identification and diagnostic patterns
