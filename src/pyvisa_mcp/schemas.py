from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationError:
    code: str
    message: str
    details: dict[str, Any] | None = None


@dataclass
class BackendStatus:
    available: bool
    preferred_transport: str
    backend_hint: str | None = None
    pyvisa_version: str | None = None
    resource_manager_ready: bool = False
    import_error: str | None = None


@dataclass
class VisibleResource:
    resource_name: str
    alias: str | None = None
    interface_type: str | None = None
    resource_class: str | None = None


@dataclass
class VisibleResourcesResult:
    query: str
    backend_hint: str | None = None
    resource_count: int = 0
    resources: list[VisibleResource] = field(default_factory=list)
    error: OperationError | None = None


@dataclass
class SessionSummary:
    session_id: str
    resource_name: str
    timeout_ms: int | None = None
    read_termination: str | None = None
    write_termination: str | None = None
    query_delay_s: float | None = None
    chunk_size: int | None = None


@dataclass
class SessionRegistrySnapshot:
    session_count: int = 0
    sessions: list[SessionSummary] = field(default_factory=list)


@dataclass
class OpenResourceResult:
    resource_name: str
    session: SessionSummary | None = None
    error: OperationError | None = None


@dataclass
class CloseResourceResult:
    session_id: str
    closed: bool
    resource_name: str | None = None
    error: OperationError | None = None


@dataclass
class WriteMessageResult:
    session_id: str
    message: str
    resource_name: str | None = None
    bytes_written: int | None = None
    error: OperationError | None = None


@dataclass
class ReadMessageResult:
    session_id: str
    resource_name: str | None = None
    data: str | None = None
    error: OperationError | None = None


@dataclass
class QueryMessageResult:
    session_id: str
    command: str
    resource_name: str | None = None
    delay_s: float | None = None
    response: str | None = None
    error: OperationError | None = None


@dataclass
class ResourceInfoDetails:
    interface_type: str | None = None
    interface_board_number: int | None = None
    resource_class: str | None = None
    resource_name: str | None = None
    alias: str | None = None


@dataclass
class ResourceInfoResult:
    resource_name: str
    backend_hint: str | None = None
    info: ResourceInfoDetails | None = None
    error: OperationError | None = None


@dataclass
class AttributeResult:
    session_id: str
    attribute: str
    resource_name: str | None = None
    value: Any | None = None
    error: OperationError | None = None


@dataclass
class CapabilitySummary:
    server_name: str
    preferred_transport: str
    tool_count: int = 0
    resource_count: int = 0
    tools: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
