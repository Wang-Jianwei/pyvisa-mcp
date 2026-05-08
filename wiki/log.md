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
