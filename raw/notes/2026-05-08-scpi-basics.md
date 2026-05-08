# 2026-05-08 SCPI Basics

## Summary

SCPI (Standard Commands for Programmable Instruments) is a standard command language used by many programmable instruments. In practice, PyVISA transports bytes and messages to instruments, while SCPI often defines the command/query syntax carried inside those messages.

## Core model

- SCPI commands are built from hierarchical keywords separated by colons.
- Queries are commands ending with `?`.
- A controller sends commands and receives response messages.
- A command may represent:
  - an event/action
  - a setting
  - a query for the current value

## Common syntax rules

- Uppercase letters indicate the minimum short form accepted by the instrument.
- Lowercase letters indicate optional completion of the long form.
- A colon descends the command tree.
- A space separates the command path from its parameters.
- Multiple parameters are comma-separated.
- Query commands end with `?`.

## Common data forms

- Numeric parameters
- Extended numeric parameters with units such as `1.2GHz`
- Discrete parameters such as `ON|OFF`
- Boolean parameters (`ON`, `OFF`, `1`, `0`)
- String parameters in quotes
- Binary or definite block payloads for larger data transfers

## Query behavior notes

- SCPI uses a command/query pattern extensively.
- `*IDN?` is the most common device identification query and is a natural first smoke test.
- Response formats are usually more rigid than accepted input formats.
- A common principle is forgiving listening and precise talking:
  - instruments may accept multiple equivalent parameter forms
  - instrument responses are usually emitted in a consistent, narrower format

## Relevance to PyVISA and this project

- Many MCP tools will likely send SCPI strings through PyVISA message-based resources.
- A minimal useful workflow is:
  - list resources
  - open a message-based resource
  - send `*IDN?`
  - read/query the response
- Termination characters and timeouts are often the difference between a working SCPI exchange and a timeout.

## Sources

- https://helpfiles.keysight.com/csg/n7625/Content/RT/basics.htm
- PyVISA communication and resources documentation used for the VISA/SCPI interaction notes
