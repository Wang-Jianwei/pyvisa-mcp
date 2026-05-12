from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal


ServerTransport = Literal["stdio", "sse", "streamable-http"]

DEFAULT_SERVER_NAME = "PyVISA MCP"
DEFAULT_SERVER_INSTRUCTIONS = (
    "Expose PyVISA-backed instrument discovery, diagnostics, and session-based "
    "message operations through MCP."
)
DEFAULT_PREFERRED_TRANSPORT: ServerTransport = "stdio"
DEFAULT_RESOURCE_QUERY = "?*::INSTR"
DEFAULT_OPEN_TIMEOUT_MS = 0
DEFAULT_TIMEOUT_MS = 2000


def normalize_backend_argument(backend: str | None) -> str:
    if not backend:
        return ""
    normalized = backend.strip()
    if not normalized:
        return ""
    if "@" in normalized:
        return normalized
    return f"@{normalized}"


def normalize_transport_argument(transport: str | None) -> ServerTransport:
    normalized = (transport or "").strip().lower()
    if normalized == "sse":
        return "sse"
    if normalized == "streamable-http":
        return "streamable-http"
    return DEFAULT_PREFERRED_TRANSPORT


@dataclass(slots=True)
class ServerConfig:
    server_name: str = DEFAULT_SERVER_NAME
    server_instructions: str = DEFAULT_SERVER_INSTRUCTIONS
    preferred_transport: ServerTransport = DEFAULT_PREFERRED_TRANSPORT
    default_backend: str | None = None
    default_resource_query: str = DEFAULT_RESOURCE_QUERY
    default_open_timeout_ms: int = DEFAULT_OPEN_TIMEOUT_MS
    default_timeout_ms: int = DEFAULT_TIMEOUT_MS

    @classmethod
    def from_env(cls) -> "ServerConfig":
        backend = os.getenv("PYVISA_MCP_BACKEND") or None
        return cls(
            server_name=os.getenv("PYVISA_MCP_SERVER_NAME", DEFAULT_SERVER_NAME),
            server_instructions=os.getenv(
                "PYVISA_MCP_SERVER_INSTRUCTIONS",
                DEFAULT_SERVER_INSTRUCTIONS,
            ),
            preferred_transport=normalize_transport_argument(
                os.getenv(
                    "PYVISA_MCP_TRANSPORT",
                    DEFAULT_PREFERRED_TRANSPORT,
                )
            ),
            default_backend=backend,
            default_resource_query=os.getenv(
                "PYVISA_MCP_DEFAULT_QUERY",
                DEFAULT_RESOURCE_QUERY,
            ),
            default_open_timeout_ms=int(
                os.getenv(
                    "PYVISA_MCP_DEFAULT_OPEN_TIMEOUT_MS",
                    str(DEFAULT_OPEN_TIMEOUT_MS),
                )
            ),
            default_timeout_ms=int(
                os.getenv(
                    "PYVISA_MCP_DEFAULT_TIMEOUT_MS",
                    str(DEFAULT_TIMEOUT_MS),
                )
            ),
        )

    @property
    def backend_argument(self) -> str:
        return normalize_backend_argument(self.default_backend)
