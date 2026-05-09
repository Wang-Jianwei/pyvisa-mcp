from __future__ import annotations

from time import sleep
from typing import Any

from .config import normalize_backend_argument
from .schemas import BackendStatus, OperationError, ResourceInfoDetails, ResourceInfoResult, VisibleResource, VisibleResourcesResult


class VisaAdapterError(RuntimeError):
    """Raised when PyVISA-backed operations fail."""


def operation_error_from_exception(exc: Exception, *, code: str | None = None) -> OperationError:
    return OperationError(
        code=code or exc.__class__.__name__,
        message=str(exc),
    )


class VisaAdapter:
    def __init__(self, default_backend: str | None = None, preferred_transport: str = "stdio") -> None:
        self._default_backend = default_backend
        self._preferred_transport = preferred_transport
        self._resource_manager: object | None = None

    @property
    def backend_argument(self) -> str:
        return normalize_backend_argument(self._default_backend)

    def backend_status(self) -> BackendStatus:
        pyvisa, import_error = self._try_import_pyvisa()
        if pyvisa is None:
            return BackendStatus(
                available=False,
                preferred_transport=self._preferred_transport,
                backend_hint=self.backend_argument or None,
                pyvisa_version=None,
                resource_manager_ready=False,
                import_error=import_error,
            )
        try:
            self._get_resource_manager()
        except Exception as exc:  # pragma: no cover - runtime environment dependent
            return BackendStatus(
                available=False,
                preferred_transport=self._preferred_transport,
                backend_hint=self.backend_argument or None,
                pyvisa_version=getattr(pyvisa, "__version__", None),
                resource_manager_ready=False,
                import_error=str(exc),
            )
        return BackendStatus(
            available=True,
            preferred_transport=self._preferred_transport,
            backend_hint=self.backend_argument or None,
            pyvisa_version=getattr(pyvisa, "__version__", None),
            resource_manager_ready=True,
            import_error=None,
        )

    def list_visible_resources(self, query: str) -> VisibleResourcesResult:
        try:
            manager = self._get_resource_manager()
            resources = manager.list_resources(query)
            info_map = manager.list_resources_info(query)
        except Exception as exc:
            return VisibleResourcesResult(
                query=query,
                backend_hint=self.backend_argument or None,
                error=operation_error_from_exception(exc),
            )

        visible_resources: list[VisibleResource] = []
        for resource_name in resources:
            info = info_map.get(resource_name)
            visible_resources.append(
                VisibleResource(
                    resource_name=resource_name,
                    alias=getattr(info, "alias", None) if info is not None else None,
                    interface_type=self._stringify(getattr(info, "interface_type", None)),
                    resource_class=getattr(info, "resource_class", None) if info is not None else None,
                )
            )
        return VisibleResourcesResult(
            query=query,
            backend_hint=self.backend_argument or None,
            resource_count=len(visible_resources),
            resources=visible_resources,
        )

    def open_resource(
        self,
        *,
        resource_name: str,
        open_timeout_ms: int = 0,
        timeout_ms: int | None = None,
        read_termination: str | None = None,
        write_termination: str | None = None,
        query_delay_s: float | None = None,
        chunk_size: int | None = None,
    ) -> object:
        manager = self._get_resource_manager()
        resource = manager.open_resource(resource_name, open_timeout=open_timeout_ms)
        self.apply_runtime_settings(
            resource,
            timeout_ms=timeout_ms,
            read_termination=read_termination,
            write_termination=write_termination,
            query_delay_s=query_delay_s,
            chunk_size=chunk_size,
        )
        return resource

    def close_resource(self, resource: object) -> None:
        close_method = getattr(resource, "close", None)
        if callable(close_method):
            close_method()

    def write_message(self, resource: object, message: str) -> int | None:
        return getattr(resource, "write")(message)

    def write_binary_message(self, resource: object, payload: bytes) -> int | None:
        write_raw = getattr(resource, "write_raw", None)
        if not callable(write_raw):
            raise VisaAdapterError("Binary write is unavailable for this resource")
        return write_raw(payload)

    def read_message(self, resource: object) -> str:
        return str(getattr(resource, "read")())

    def read_binary_message(self, resource: object) -> bytes:
        read_raw = getattr(resource, "read_raw", None)
        if not callable(read_raw):
            raise VisaAdapterError("Binary read is unavailable for this resource")
        return bytes(read_raw())

    def query_message(self, resource: object, command: str, *, delay_s: float | None = None) -> str:
        query = getattr(resource, "query")
        if delay_s is None:
            return str(query(command))
        return str(query(command, delay=delay_s))

    def query_binary_message(self, resource: object, command: str | bytes, *, delay_s: float | None = None) -> bytes:
        if isinstance(command, bytes):
            self.write_binary_message(resource, command)
        else:
            getattr(resource, "write")(command)
        if delay_s is not None:
            sleep(delay_s)
        return self.read_binary_message(resource)

    def read_binary_values(
        self,
        resource: object,
        *,
        data_type: str = "f",
        is_big_endian: bool = False,
        header_format: str = "ieee",
        expect_termination: bool = True,
    ) -> list[Any]:
        read_binary_values = getattr(resource, "read_binary_values", None)
        if not callable(read_binary_values):
            raise VisaAdapterError("Binary values read is unavailable for this resource")
        values = read_binary_values(
            datatype=data_type,
            is_big_endian=is_big_endian,
            header_fmt=header_format,
            expect_termination=expect_termination,
            container=list,
        )
        return list(values)

    def query_binary_values(
        self,
        resource: object,
        command: str,
        *,
        data_type: str = "f",
        is_big_endian: bool = False,
        header_format: str = "ieee",
        expect_termination: bool = True,
        delay_s: float | None = None,
    ) -> list[Any]:
        query_binary_values = getattr(resource, "query_binary_values", None)
        if not callable(query_binary_values):
            raise VisaAdapterError("Binary values query is unavailable for this resource")
        kwargs: dict[str, Any] = {
            "datatype": data_type,
            "is_big_endian": is_big_endian,
            "header_fmt": header_format,
            "expect_termination": expect_termination,
            "container": list,
        }
        if delay_s is not None:
            kwargs["delay"] = delay_s
        values = query_binary_values(command, **kwargs)
        return list(values)

    def read_resource_info(self, resource_name: str) -> ResourceInfoResult:
        try:
            manager = self._get_resource_manager()
            info = manager.resource_info(resource_name, extended=True)
        except Exception as exc:
            return ResourceInfoResult(
                resource_name=resource_name,
                backend_hint=self.backend_argument or None,
                error=operation_error_from_exception(exc),
            )
        return ResourceInfoResult(
            resource_name=resource_name,
            backend_hint=self.backend_argument or None,
            info=ResourceInfoDetails(
                interface_type=self._stringify(getattr(info, "interface_type", None)),
                interface_board_number=getattr(info, "interface_board_number", None),
                resource_class=getattr(info, "resource_class", None),
                resource_name=getattr(info, "resource_name", None),
                alias=getattr(info, "alias", None),
            ),
        )

    def get_attribute(self, resource: object, attribute: str) -> Any:
        if hasattr(resource, attribute):
            return getattr(resource, attribute)
        pyvisa, import_error = self._try_import_pyvisa()
        if pyvisa is None:
            raise VisaAdapterError(import_error or f"Attribute '{attribute}' is unavailable")
        attribute_id = getattr(pyvisa.constants, attribute, None)
        if attribute_id is None or not hasattr(resource, "get_visa_attribute"):
            raise VisaAdapterError(f"Unsupported attribute: {attribute}")
        return resource.get_visa_attribute(attribute_id)

    def set_attribute(self, resource: object, attribute: str, value: Any) -> Any:
        if hasattr(resource, attribute):
            setattr(resource, attribute, value)
            return getattr(resource, attribute)
        pyvisa, import_error = self._try_import_pyvisa()
        if pyvisa is None:
            raise VisaAdapterError(import_error or f"Attribute '{attribute}' is unavailable")
        attribute_id = getattr(pyvisa.constants, attribute, None)
        if attribute_id is None or not hasattr(resource, "set_visa_attribute"):
            raise VisaAdapterError(f"Unsupported attribute: {attribute}")
        resource.set_visa_attribute(attribute_id, value)
        return value

    def apply_runtime_settings(
        self,
        resource: object,
        *,
        timeout_ms: int | None = None,
        read_termination: str | None = None,
        write_termination: str | None = None,
        query_delay_s: float | None = None,
        chunk_size: int | None = None,
    ) -> None:
        if timeout_ms is not None and hasattr(resource, "timeout"):
            resource.timeout = timeout_ms
        if read_termination is not None and hasattr(resource, "read_termination"):
            resource.read_termination = read_termination
        if write_termination is not None and hasattr(resource, "write_termination"):
            resource.write_termination = write_termination
        if query_delay_s is not None and hasattr(resource, "query_delay"):
            resource.query_delay = query_delay_s
        if chunk_size is not None and hasattr(resource, "chunk_size"):
            resource.chunk_size = chunk_size

    def _get_resource_manager(self) -> Any:
        if self._resource_manager is not None:
            return self._resource_manager
        pyvisa, import_error = self._try_import_pyvisa()
        if pyvisa is None:
            raise VisaAdapterError(import_error or "PyVISA is unavailable")
        argument = self.backend_argument
        self._resource_manager = pyvisa.ResourceManager(argument) if argument else pyvisa.ResourceManager()
        return self._resource_manager

    @staticmethod
    def _try_import_pyvisa() -> tuple[Any | None, str | None]:
        try:
            import pyvisa  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            return None, str(exc)
        return pyvisa, None

    @staticmethod
    def _stringify(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
