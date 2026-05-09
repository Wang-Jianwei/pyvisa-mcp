# Wiki Log

## [2026-05-08] init | bootstrap workspace wiki

What changed

- Added the raw layer bootstrap note and the first wiki navigation pages.
- Turned `AGENTS.md` into the live schema for this repository.

Files added or updated

- `AGENTS.md`
- `raw/README.md`
- `wiki/index.md`
- `wiki/log.md`

Why it matters

- The repository now has an explicit operating model for future research, design, implementation, and verification work.

## [2026-05-08] ingest | seed pyvisa mcp scpi notes

What changed

- Added first-pass raw notes for PyVISA, MCP, SCPI, and project decisions.
- Added first-pass wiki summary pages derived from those notes.

Files added or updated

- `raw/notes/2026-05-08-pyvisa-basics.md`
- `raw/notes/2026-05-08-mcp-basics.md`
- `raw/notes/2026-05-08-scpi-basics.md`
- `raw/notes/2026-05-08-project-decisions.md`
- `wiki/overview/project-overview.md`
- `wiki/concepts/mcp.md`
- `wiki/standards/pyvisa.md`
- `wiki/standards/scpi.md`
- `wiki/project/architecture-plan.md`
- `wiki/sources/source-register.md`

Why it matters

- The project now has a durable local knowledge baseline that later implementation work can build on without re-deriving the same context from scratch.

## [2026-05-08] init | materialize raw support directories

What changed

- Added placeholder directories for imported materials, binary assets, and source inventories.

Files added or updated

- `raw/external/README.md`
- `raw/assets/README.md`
- `raw/sources/README.md`

Why it matters

- The raw layer now has explicit landing zones for future ingest work beyond hand-written research notes.

## [2026-05-08] implementation | bootstrap python package and schema layer

What changed

- Added the first Python package scaffold, packaging metadata, and repository ignore rules.
- Added a FastMCP server entrypoint, configuration model, PyVISA adapter boundary, session registry, and first-pass tool/resource schemas.
- Added bootstrap tests for configuration and session registry behavior.

Files added or updated

- `.gitignore`
- `README.md`
- `pyproject.toml`
- `src/pyvisa_mcp/__init__.py`
- `src/pyvisa_mcp/config.py`
- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/session_registry.py`
- `src/pyvisa_mcp/visa_adapter.py`
- `src/pyvisa_mcp/tools.py`
- `src/pyvisa_mcp/resources.py`
- `src/pyvisa_mcp/server.py`
- `tests/test_config.py`
- `tests/test_session_registry.py`
- `wiki/project/architecture-plan.md`

Why it matters

- The repository has moved from documentation-only bootstrap into an executable Python project skeleton aligned with the existing wiki plan.

## [2026-05-08] verification | validate installed runtime and server creation

What changed

- Configured a local virtual environment for the workspace.
- Installed the project into that environment.
- Verified that `create_server()` now instantiates `FastMCP` successfully.
- Added a regression test to lock in the `ServerConfig.from_env()` default fallback behavior.

Files added or updated

- `tests/test_config.py`
- `wiki/log.md`

Why it matters

- The project is no longer only structurally valid; it has now passed a real import-and-create runtime check in its configured Python environment.

## [2026-05-08] implementation | extend mocked adapter and tool flow coverage

What changed

- Added mocked `VisaAdapter` tests for resource discovery, open-time runtime settings, message helpers, and resource info reads.
- Extended tool-layer tests to cover list/open/query/close session flow without hardware dependencies.

Files added or updated

- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The repository now protects the main PyVISA MCP control path with focused mocked tests, reducing the chance of regressions before sim or hardware validation.

## [2026-05-08] implementation | add structured error-path coverage

What changed

- Added tests for `VisaAdapter` failure handling around import, resource manager setup, resource listing, and resource info reads.
- Added tests for tool-layer structured error returns covering open failures, query failures, unknown sessions, and close-session error codes.

Files added or updated

- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The project now verifies both success paths and key failure paths for the current mocked PyVISA MCP surface, making the bootstrap behavior more dependable before sim-backed validation.

## [2026-05-08] implementation | support custom sim backends and richer result metadata

What changed

- Relaxed backend argument normalization so the server can pass explicit `profile.yaml@sim` backend strings through to PyVISA.
- Enriched tool and resource result models with counts and resource-level context such as `resource_name`, `backend_hint`, and operation metadata.
- Added passive resource tests to lock in the new JSON shape.

Files added or updated

- `README.md`
- `src/pyvisa_mcp/config.py`
- `src/pyvisa_mcp/resources.py`
- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/session_registry.py`
- `src/pyvisa_mcp/tools.py`
- `src/pyvisa_mcp/visa_adapter.py`
- `tests/test_config.py`
- `tests/test_resources.py`
- `tests/test_session_registry.py`
- `tests/test_tools.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The MCP surface now returns more self-describing payloads, and the adapter can target repository-local `pyvisa-sim` profiles instead of only shorthand backends like `@sim`.

## [2026-05-08] verification | add sim-backed smoke validation

What changed

- Added a repository-local `pyvisa-sim` fixture profile and a smoke test that lists resources, opens a simulated instrument, and queries `*IDN?` through `VisaAdapter`.
- Re-ran focused tests covering backend normalization, passive resources, and the new sim-backed adapter path.

Files added or updated

- `tests/fixtures/pyvisa_sim.yaml`
- `tests/test_pyvisa_sim_smoke.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The project now has a real backend-backed validation layer between pure mocks and physical hardware, which reduces risk in the PyVISA integration boundary.

## [2026-05-08] verification | add server-level fastmcp integration checks

What changed

- Added async integration tests against `create_server()` using FastMCP public APIs such as `list_tools`, `list_resources`, `call_tool`, and `read_resource`.
- Verified that the server registers the expected tool and resource inventory and that a sim-backed open/query/close session flow updates the session resource snapshot correctly.

Files added or updated

- `tests/test_server.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The project now validates the MCP surface one layer above the adapter and registration helpers, reducing the chance that wiring or FastMCP integration regressions slip past the lower-level tests.

## [2026-05-08] implementation | add interactive cli mode

What changed

- Added a new `pyvisa-mcp-cli` console entrypoint for launching a local interactive terminal against the project server.
- Implemented a CLI runtime that starts the server as a subprocess, opens a real MCP stdio session, and maps REPL commands onto the existing tools and resources.
- Added first-pass REPL commands for backend diagnostics, resource listing, session lifecycle, message operations, resource reads, and attribute access.

Files added or updated

- `pyproject.toml`
- `src/pyvisa_mcp/cli.py`
- `src/pyvisa_mcp/cli_runtime.py`
- `README.md`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The repository now has a practical terminal interface for real MCP-shaped interaction and debugging, without bypassing the stdio transport layer.

## [2026-05-08] verification | validate cli repl against sim backend

What changed

- Added focused CLI command tests for session reuse, JSON output mode switching, and missing-session errors.
- Added a process-level CLI integration test that pipes commands through the REPL while it talks to the repository-local `pyvisa-sim` backend.
- Re-ran the focused CLI test slice to confirm the first implementation batch works end to end.

Files added or updated

- `tests/test_cli.py`
- `tests/test_cli_integration.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The new CLI is not only syntactically present; it now has proof that it can drive a real stdio MCP session through the same sim-backed path used by the rest of the repository validation story.

## [2026-05-08] implementation | enrich tool parameter schemas for agents

What changed

- Added parameter-level schema descriptions to the MCP tools using typed annotations and Pydantic field metadata.
- Clarified the semantics of resource names, session IDs, timeouts, termination strings, query delays, attribute names, and attribute values at the schema layer instead of leaving agents to infer them from names alone.

Files added or updated

- `src/pyvisa_mcp/tools.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- Agent-facing tool discovery now carries more of the operational meaning needed to choose correct arguments without reading implementation code.

## [2026-05-08] verification | lock parameter descriptions into server schemas

What changed

- Added a server integration test that inspects the FastMCP-exposed tool schemas and asserts that key parameter descriptions are present.
- Re-ran the focused server integration slice to verify the richer schema metadata is actually visible through the MCP surface.

Files added or updated

- `tests/test_server.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- This prevents future refactors from silently dropping the schema descriptions that agents rely on when selecting tool arguments.

## [2026-05-08] implementation | enrich result schemas for agents

What changed

- Converted the agent-facing result models from plain dataclasses to Pydantic models with field descriptions.
- Updated resource JSON serialization to use model dumping so the same result models work for both MCP tool schemas and passive resources.

Files added or updated

- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/resources.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- Agents can now see more of the meaning of result payloads directly in the MCP output schemas instead of inferring everything from field names alone.

## [2026-05-08] verification | lock result descriptions into server schemas

What changed

- Added server integration assertions that inspect FastMCP output schemas and verify key result-field descriptions are present.
- Re-ran focused server and resource tests to verify schema exposure and JSON serialization after the model conversion.

Files added or updated

- `tests/test_server.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- This prevents future schema refactors from silently regressing the result metadata that agents can use when interpreting tool responses.

## [2026-05-08] implementation | add schema examples for agent guidance

What changed

- Added representative examples to key input schema fields such as resource names, session IDs, commands, timeouts, and attribute values.
- Added representative examples to key result schema fields such as session identifiers, resource names, responses, attribute values, backend hints, and normalized error codes.

Files added or updated

- `src/pyvisa_mcp/tools.py`
- `src/pyvisa_mcp/schemas.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- Agents now get concrete examples alongside descriptions, which reduces guesswork when selecting arguments or interpreting common response fields.

## [2026-05-08] verification | lock schema examples into server output

What changed

- Added server integration assertions that inspect FastMCP input and output schemas and verify that key examples are present.
- Re-ran the focused server schema test slice to confirm the examples survive schema generation.

Files added or updated

- `tests/test_server.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- This prevents future refactors from silently removing the concrete examples that improve agent-side tool selection and result interpretation.

## [2026-05-08] implementation | add binary visa payload tools

What changed

- Added binary read, write, and query operations to the adapter, tool layer, and CLI.
- Added structured binary payload schemas that support either inline base64 transport or server-managed temporary-file references.
- Extended the session registry so temporary binary files are cleaned up automatically when sessions close.

Files added or updated

- `README.md`
- `src/pyvisa_mcp/cli_runtime.py`
- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/session_registry.py`
- `src/pyvisa_mcp/tools.py`
- `src/pyvisa_mcp/visa_adapter.py`
- `tests/test_cli.py`
- `tests/test_server.py`
- `tests/test_session_registry.py`
- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The MCP surface can now move raw instrument bytes without forcing them through text-oriented APIs, while still giving callers a choice between inline transport and temporary-file handoff.

## [2026-05-08] verification | validate binary payload paths

What changed

- Ran focused tests covering binary adapter helpers, binary tools, session temp-file cleanup, CLI rendering, and schema exposure.
- Confirmed that server-managed temporary binary files are removed when the owning session closes.

Files added or updated

- `tests/test_cli.py`
- `tests/test_server.py`
- `tests/test_session_registry.py`
- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/log.md`

Why it matters

- Binary support now has executable regression coverage across the adapter, tool, CLI, and schema layers instead of relying on design intent alone.

## [2026-05-09] verification | add sim-backed binary query validation

What changed

- Extended the repository-local `pyvisa-sim` fixture with a UTF-8-backed binary query response.
- Added a real-backend adapter smoke test for `query_binary_message` and a CLI process test for `query-bin` JSON output.
- Captured the current `pyvisa-sim` constraint that fixture values are UTF-8 encoded strings with `\r` and `\n` normalization, not an arbitrary raw-byte literal format.

Files added or updated

- `raw/notes/2026-05-08-pyvisa-basics.md`
- `tests/fixtures/pyvisa_sim.yaml`
- `tests/test_cli_integration.py`
- `tests/test_pyvisa_sim_smoke.py`
- `wiki/project/architecture-plan.md`
- `wiki/standards/pyvisa.md`
- `wiki/log.md`

Why it matters

- The repository now proves that the binary MCP path works against a real simulated backend, while also documenting the current boundary of what the sim fixture format can and cannot represent.

## [2026-05-09] implementation | add caller managed binary output paths

What changed

- Added optional `output_file_path` support to binary read and binary query tools.
- Extended binary payload metadata so responses explicitly state whether a returned file path will be cleaned up on session close.
- Updated the CLI so `read-bin` and `query-bin` can target caller-managed file paths directly.

Files added or updated

- `README.md`
- `src/pyvisa_mcp/cli_runtime.py`
- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/tools.py`
- `tests/test_cli.py`
- `tests/test_cli_integration.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- Callers can now persist binary captures to a chosen path without depending on the session-scoped temp-file lifecycle, while still preserving the existing auto-cleanup behavior for server-managed temp files.

## [2026-05-09] verification | validate caller managed binary output paths

What changed

- Added focused tests for explicit output-file handling in the tool layer, CLI parsing, CLI rendering, and CLI process integration.
- Verified that caller-managed output files remain on disk after session close while server-managed temp files continue to be cleaned up.

Files added or updated

- `tests/test_cli.py`
- `tests/test_cli_integration.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `wiki/log.md`

Why it matters

- The binary file handoff contract is now executable and explicit, reducing ambiguity about file ownership and cleanup semantics for agents and users.

## [2026-05-09] implementation | add binary output overwrite policy

What changed

- Added an explicit `output_file_conflict` policy to binary read and query tools.
- Kept the default behavior safe by refusing to overwrite existing caller-managed files unless `overwrite` is requested.
- Extended CLI parsing so `read-bin` and `query-bin` can opt into overwrite explicitly.

Files added or updated

- `README.md`
- `src/pyvisa_mcp/cli_runtime.py`
- `src/pyvisa_mcp/tools.py`
- `tests/test_cli.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- This prevents accidental data loss when callers target a stable output path, while still allowing intentional replacement when a workflow needs it.

## [2026-05-09] verification | validate binary output overwrite policy

What changed

- Added focused tool and CLI tests for default file-exists failures and explicit overwrite handling.
- Added CLI process integration coverage showing that real sim-backed binary queries respect the overwrite policy.
- Added schema assertions that expose the overwrite-policy parameter to agents.

Files added or updated

- `tests/test_cli.py`
- `tests/test_cli_integration.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `wiki/log.md`

Why it matters

- The overwrite semantics are now both documented and executable, which reduces ambiguity for automation and keeps caller-managed capture paths safe by default.

## [2026-05-09] implementation | add binary numeric value tools

What changed

- Added adapter, schema, tool, and CLI support for decoding binary numeric blocks through `read_binary_values` and `query_binary_values`.
- Exposed datatype, header format, endianness, termination expectation, and optional query delay as explicit tool and CLI parameters.
- Returned decoded numeric arrays inline so agents can inspect value blocks directly without an extra file handoff step.

Files added or updated

- `README.md`
- `src/pyvisa_mcp/cli_runtime.py`
- `src/pyvisa_mcp/schemas.py`
- `src/pyvisa_mcp/tools.py`
- `src/pyvisa_mcp/visa_adapter.py`
- `tests/test_cli.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/project/architecture-plan.md`
- `wiki/log.md`

Why it matters

- The MCP surface can now represent the common SCPI waveform pattern of binary numeric blocks as structured arrays, not only as opaque bytes.

## [2026-05-09] verification | validate binary numeric value tools

What changed

- Added focused adapter tests for binary value decoding parameter passthrough and unsupported-resource errors.
- Added focused tool, CLI, and server-schema tests for decoded numeric arrays and their argument metadata.
- Kept this batch mock-first because the current repository-local `pyvisa-sim` fixture format does not yet provide a realistic numeric binary block path.

Files added or updated

- `tests/test_cli.py`
- `tests/test_server.py`
- `tests/test_tools.py`
- `tests/test_visa_adapter.py`
- `wiki/log.md`

Why it matters

- Numeric binary-value support now has executable regression coverage across the adapter, tool, CLI, and schema layers, while the current real-backend gap is explicitly documented instead of being left implicit.
