from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable
from uuid import uuid4

from .schemas import CloseResourceResult, SessionRegistrySnapshot, SessionSummary


class UnknownSessionError(KeyError):
    """Raised when a requested session id does not exist."""


@dataclass(slots=True)
class ManagedSession:
    session_id: str
    resource_name: str
    resource: object
    timeout_ms: int | None = None
    read_termination: str | None = None
    write_termination: str | None = None
    query_delay_s: float | None = None
    chunk_size: int | None = None

    def to_summary(self) -> SessionSummary:
        return SessionSummary(
            session_id=self.session_id,
            resource_name=self.resource_name,
            timeout_ms=self.timeout_ms,
            read_termination=self.read_termination,
            write_termination=self.write_termination,
            query_delay_s=self.query_delay_s,
            chunk_size=self.chunk_size,
        )


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, ManagedSession] = {}
        self._lock = RLock()

    def open(
        self,
        *,
        resource_name: str,
        resource: object,
        timeout_ms: int | None = None,
        read_termination: str | None = None,
        write_termination: str | None = None,
        query_delay_s: float | None = None,
        chunk_size: int | None = None,
    ) -> SessionSummary:
        managed = ManagedSession(
            session_id=str(uuid4()),
            resource_name=resource_name,
            resource=resource,
            timeout_ms=timeout_ms,
            read_termination=read_termination,
            write_termination=write_termination,
            query_delay_s=query_delay_s,
            chunk_size=chunk_size,
        )
        with self._lock:
            self._sessions[managed.session_id] = managed
        return managed.to_summary()

    def require(self, session_id: str) -> ManagedSession:
        with self._lock:
            managed = self._sessions.get(session_id)
        if managed is None:
            raise UnknownSessionError(session_id)
        return managed

    def list_summaries(self) -> SessionRegistrySnapshot:
        with self._lock:
            sessions = [managed.to_summary() for managed in self._sessions.values()]
        sessions.sort(key=lambda item: item.session_id)
        return SessionRegistrySnapshot(session_count=len(sessions), sessions=sessions)

    def update_runtime_settings(
        self,
        session_id: str,
        *,
        timeout_ms: int | None = None,
        read_termination: str | None = None,
        write_termination: str | None = None,
        query_delay_s: float | None = None,
        chunk_size: int | None = None,
    ) -> SessionSummary:
        managed = self.require(session_id)
        with self._lock:
            if timeout_ms is not None:
                managed.timeout_ms = timeout_ms
            if read_termination is not None:
                managed.read_termination = read_termination
            if write_termination is not None:
                managed.write_termination = write_termination
            if query_delay_s is not None:
                managed.query_delay_s = query_delay_s
            if chunk_size is not None:
                managed.chunk_size = chunk_size
            return managed.to_summary()

    def close(
        self,
        session_id: str,
        *,
        close_callback: Callable[[object], None] | None = None,
    ) -> CloseResourceResult:
        with self._lock:
            managed = self._sessions.pop(session_id, None)
        if managed is None:
            raise UnknownSessionError(session_id)
        if close_callback is not None:
            close_callback(managed.resource)
        return CloseResourceResult(
            session_id=session_id,
            closed=True,
            resource_name=managed.resource_name,
        )

    def close_all(
        self,
        *,
        close_callback: Callable[[object], None] | None = None,
    ) -> int:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for managed in sessions:
            if close_callback is not None:
                close_callback(managed.resource)
        return len(sessions)
