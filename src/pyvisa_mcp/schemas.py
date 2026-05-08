from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OperationError(BaseModel):
    code: str = Field(description="Machine-readable error code. By default this is the originating exception class name or a normalized tool-level code.")
    message: str = Field(description="Human-readable error message explaining why the operation failed.")
    details: dict[str, Any] | None = Field(default=None, description="Optional structured error details for future extension.")


class BackendStatus(BaseModel):
    available: bool = Field(description="Whether PyVISA and the configured backend are currently available for use.")
    preferred_transport: str = Field(description="Transport the server is currently configured to use, typically 'stdio'.")
    backend_hint: str | None = Field(default=None, description="Backend argument passed or inferred for ResourceManager creation, such as '@sim' or 'profile.yaml@sim'.")
    pyvisa_version: str | None = Field(default=None, description="Detected PyVISA version when the import succeeds.")
    resource_manager_ready: bool = Field(default=False, description="Whether a ResourceManager instance could be created successfully.")
    import_error: str | None = Field(default=None, description="Import or initialization error string when the backend is unavailable.")


class VisibleResource(BaseModel):
    resource_name: str = Field(description="Canonical VISA resource name returned by the backend discovery query.")
    alias: str | None = Field(default=None, description="Optional backend alias for the resource when one is configured.")
    interface_type: str | None = Field(default=None, description="Backend-reported interface type for the resource, such as serial, TCPIP, USB, or GPIB.")
    resource_class: str | None = Field(default=None, description="VISA resource class, typically 'INSTR' for instrument sessions.")


class VisibleResourcesResult(BaseModel):
    query: str = Field(description="Resource query expression that was executed against the current backend.")
    backend_hint: str | None = Field(default=None, description="Backend argument used for discovery, if one was configured.")
    resource_count: int = Field(default=0, description="Number of resources returned in the resources list.")
    resources: list[VisibleResource] = Field(default_factory=list, description="Visible resources reported by the backend for the supplied query.")
    error: OperationError | None = Field(default=None, description="Structured error when resource discovery fails.")


class SessionSummary(BaseModel):
    session_id: str = Field(description="Opaque MCP-managed session identifier returned after opening a resource.")
    resource_name: str = Field(description="Resource name currently bound to this MCP-managed session.")
    timeout_ms: int | None = Field(default=None, description="Current session timeout in milliseconds.")
    read_termination: str | None = Field(default=None, description="Current read termination string applied to the session, if any.")
    write_termination: str | None = Field(default=None, description="Current write termination string applied to the session, if any.")
    query_delay_s: float | None = Field(default=None, description="Current query delay in seconds applied to the session, if any.")
    chunk_size: int | None = Field(default=None, description="Current read chunk size in bytes for the session, if any.")


class SessionRegistrySnapshot(BaseModel):
    session_count: int = Field(default=0, description="Number of sessions currently tracked by the MCP session registry.")
    sessions: list[SessionSummary] = Field(default_factory=list, description="Snapshot of all currently open MCP-managed sessions.")


class OpenResourceResult(BaseModel):
    resource_name: str = Field(description="Resource name requested by the open operation.")
    session: SessionSummary | None = Field(default=None, description="Session details when the resource opens successfully.")
    error: OperationError | None = Field(default=None, description="Structured error when the open operation fails.")


class CloseResourceResult(BaseModel):
    session_id: str = Field(description="Session identifier that the close operation targeted.")
    closed: bool = Field(description="Whether the target session was closed successfully.")
    resource_name: str | None = Field(default=None, description="Resource name that was associated with the closed session, when known.")
    error: OperationError | None = Field(default=None, description="Structured error when the close operation fails.")


class WriteMessageResult(BaseModel):
    session_id: str = Field(description="Session identifier targeted by the write operation.")
    message: str = Field(description="Raw command or payload string that was written to the instrument.")
    resource_name: str | None = Field(default=None, description="Resource name bound to the target session, when known.")
    bytes_written: int | None = Field(default=None, description="Backend-reported byte count for the write operation, when available.")
    error: OperationError | None = Field(default=None, description="Structured error when the write operation fails.")


class ReadMessageResult(BaseModel):
    session_id: str = Field(description="Session identifier targeted by the read operation.")
    resource_name: str | None = Field(default=None, description="Resource name bound to the target session, when known.")
    data: str | None = Field(default=None, description="String data returned by the read operation.")
    error: OperationError | None = Field(default=None, description="Structured error when the read operation fails.")


class QueryMessageResult(BaseModel):
    session_id: str = Field(description="Session identifier targeted by the query operation.")
    command: str = Field(description="Query command string that was sent to the instrument.")
    resource_name: str | None = Field(default=None, description="Resource name bound to the target session, when known.")
    delay_s: float | None = Field(default=None, description="Optional per-call query delay in seconds used for this query.")
    response: str | None = Field(default=None, description="String response returned by the instrument for the query.")
    error: OperationError | None = Field(default=None, description="Structured error when the query operation fails.")


class ResourceInfoDetails(BaseModel):
    interface_type: str | None = Field(default=None, description="Backend-reported interface type for the resource.")
    interface_board_number: int | None = Field(default=None, description="Board number associated with the interface, when reported by the backend.")
    resource_class: str | None = Field(default=None, description="VISA resource class, such as 'INSTR'.")
    resource_name: str | None = Field(default=None, description="Resolved resource name reported by the backend.")
    alias: str | None = Field(default=None, description="Optional backend alias for the resource.")


class ResourceInfoResult(BaseModel):
    resource_name: str = Field(description="Resource name that was inspected.")
    backend_hint: str | None = Field(default=None, description="Backend argument used to resolve the resource information, if configured.")
    info: ResourceInfoDetails | None = Field(default=None, description="Extended backend metadata for the target resource when available.")
    error: OperationError | None = Field(default=None, description="Structured error when resource inspection fails.")


class AttributeResult(BaseModel):
    session_id: str = Field(description="Session identifier targeted by the attribute operation.")
    attribute: str = Field(description="Python-level or VISA-level attribute name that was read or written.")
    resource_name: str | None = Field(default=None, description="Resource name bound to the target session, when known.")
    value: Any | None = Field(default=None, description="Current or updated attribute value returned by the operation.")
    error: OperationError | None = Field(default=None, description="Structured error when the attribute operation fails.")


class CapabilitySummary(BaseModel):
    server_name: str = Field(description="Server name reported by the current FastMCP instance.")
    preferred_transport: str = Field(description="Transport configured for the server, typically 'stdio'.")
    tool_count: int = Field(default=0, description="Number of MCP tools currently exposed by the server.")
    resource_count: int = Field(default=0, description="Number of MCP resources currently exposed by the server.")
    tools: list[str] = Field(default_factory=list, description="Names of the tools currently registered on the server.")
    resources: list[str] = Field(default_factory=list, description="URIs of the resources currently registered on the server.")
