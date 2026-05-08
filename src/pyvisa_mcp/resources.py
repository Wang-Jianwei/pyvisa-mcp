from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from .config import ServerConfig
from .schemas import CapabilitySummary
from .session_registry import SessionRegistry
from .visa_adapter import VisaAdapter

RESOURCE_URIS = [
    "pyvisa-mcp://backend/status",
    "pyvisa-mcp://resources/visible",
    "pyvisa-mcp://sessions",
    "pyvisa-mcp://capabilities",
]


def register_resources(
    mcp: Any,
    *,
    adapter: VisaAdapter,
    registry: SessionRegistry,
    config: ServerConfig,
    tool_names: list[str],
) -> None:
    @mcp.resource("pyvisa-mcp://backend/status")
    def backend_status() -> str:
        """Expose backend readiness as a passive JSON resource."""
        return _json_dump(adapter.backend_status())

    @mcp.resource("pyvisa-mcp://resources/visible")
    def visible_resources() -> str:
        """Expose the default visible resource inventory as JSON."""
        return _json_dump(adapter.list_visible_resources(config.default_resource_query))

    @mcp.resource("pyvisa-mcp://sessions")
    def session_registry_snapshot() -> str:
        """Expose the currently opened MCP-managed sessions as JSON."""
        return _json_dump(registry.list_summaries())

    @mcp.resource("pyvisa-mcp://capabilities")
    def capability_summary() -> str:
        """Expose the current server capability summary as JSON."""
        return _json_dump(
            CapabilitySummary(
                server_name=config.server_name,
                preferred_transport=config.preferred_transport,
                tools=tool_names,
                resources=RESOURCE_URIS,
            )
        )


def _json_dump(value: Any) -> str:
    return json.dumps(asdict(value), indent=2, sort_keys=True)
