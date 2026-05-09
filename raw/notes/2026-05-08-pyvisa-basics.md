# 2026-05-08 PyVISA Basics

## Summary

PyVISA is a Python package for controlling instruments through the VISA standard across interfaces such as GPIB, RS232, USB, and Ethernet. It is best treated as a high-level, object-oriented frontend centered on `ResourceManager` and resource objects rather than as a direct exposure of raw VISA functions.

## Key facts

- PyVISA can use multiple backends.
- Default usage starts with `pyvisa.ResourceManager()`.
- `ResourceManager.list_resources()` discovers available resources.
- `ResourceManager.open_resource()` returns the matching Python resource class.
- Common message-based operations are `write`, `read`, and `query`.
- `query` is effectively `write` followed by `read`.
- The main runtime tuning knobs for message-based instruments are:
  - `timeout`
  - `read_termination`
  - `write_termination`
  - `query_delay`
  - `chunk_size`
- PyVISA documents three layers:
  - Low-level shared-library wrapper
  - Middle-level Python wrappers around VISA calls
  - High-level object model (`ResourceManager`, `Resource`)
- For compatibility and maintainability, the high-level API should be the primary abstraction for this project.

## Backend notes

- `ResourceManager()` is equivalent to `ResourceManager('@ivi')` when the default IVI backend is used.
- Other backends can be selected using the `@backend` suffix.
- PyVISA can discover custom backends by importing packages named like `pyvisa_somename`.
- PyVISA Shell supports switching to simulated or pure Python backends, including `-b sim`.
- `pyvisa-sim` stores dialogues as bytes internally, so binary-path validation can exercise real `read_raw` flows.
- The current `pyvisa-sim` YAML parser only normalizes `\r` and `\n` escapes before UTF-8 encoding string values, so repository-local sim fixtures are suitable for UTF-8-backed binary smoke tests but not arbitrary `\xNN` raw-byte literals.

## Diagnostics and operations

- `pyvisa-info` reports machine, Python, and backend information.
- `pyvisa-shell` provides an interactive shell for listing, opening, reading, writing, querying, inspecting attributes, and testing termchar settings.
- `pyvisa.log_to_screen()` enables runtime logging for debugging.
- PyVISA is documented as thread-safe starting from version 1.6.

## Relevance to this project

- The MCP server should model instrument access around `ResourceManager` and opened resources.
- Tools should focus first on high-value message-based workflows rather than the full VISA surface.
- Diagnostics should expose enough information for users to resolve backend discovery, timeout, and session problems.

## Sources

- https://pyvisa.readthedocs.io/en/latest/
- https://pyvisa.readthedocs.io/en/latest/advanced/architecture.html
- https://pyvisa.readthedocs.io/en/latest/advanced/backends.html
- https://pyvisa.readthedocs.io/en/latest/api/resourcemanager.html
- https://pyvisa.readthedocs.io/en/latest/introduction/communication.html
- https://pyvisa.readthedocs.io/en/latest/introduction/resources.html
- https://pyvisa.readthedocs.io/en/latest/introduction/shell.html
- https://pyvisa.readthedocs.io/en/latest/faq/faq.html
