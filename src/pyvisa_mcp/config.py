from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_SERVER_NAME = "PyVISA MCP"
DEFAULT_SERVER_INSTRUCTIONS = (
    "Expose PyVISA-backed instrument discovery, diagnostics, and session-based "
    "message operations through MCP."
)
DEFAULT_PREFERRED_TRANSPORT = "stdio"
DEFAULT_RESOURCE_QUERY = "?*::INSTR"
DEFAULT_OPEN_TIMEOUT_MS = 0
DEFAULT_TIMEOUT_MS = 2000


@dataclass(slots=True)
class ServerConfig:
    server_name: str = DEFAULT_SERVER_NAME
    server_instructions: str = DEFAULT_SERVER_INSTRUCTIONS
    preferred_transport: str = DEFAULT_PREFERRED_TRANSPORT
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
            preferred_transport=os.getenv(
                "PYVISA_MCP_TRANSPORT",
                DEFAULT_PREFERRED_TRANSPORT,
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
        if not self.default_backend:
            return ""
        if self.default_backend.startswith("@"):
            return self.default_backend
        return f"@{self.default_backend}"
