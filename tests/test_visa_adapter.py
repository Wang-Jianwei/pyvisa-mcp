from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.visa_adapter import VisaAdapter


class FakeResourceInfo:
    def __init__(
        self,
        *,
        alias: str | None = None,
        interface_type: object | None = None,
        resource_class: str | None = None,
        interface_board_number: int | None = None,
        resource_name: str | None = None,
    ) -> None:
        self.alias = alias
        self.interface_type = interface_type
        self.resource_class = resource_class
        self.interface_board_number = interface_board_number
        self.resource_name = resource_name


class FakeResource:
    def __init__(self) -> None:
        self.timeout = None
        self.read_termination = None
        self.write_termination = None
        self.query_delay = None
        self.chunk_size = None
        self.closed = False
        self.writes: list[str] = []
        self.raw_writes: list[bytes] = []
        self.raw_reads: list[bytes] = [b"\x00\x01RAW", b"\x23\x34QUERY"]

    def write(self, message: str) -> int:
        self.writes.append(message)
        return len(message)

    def write_raw(self, payload: bytes) -> int:
        self.raw_writes.append(payload)
        return len(payload)

    def read(self) -> str:
        return "READ:OK"

    def read_raw(self) -> bytes:
        return self.raw_reads.pop(0)

    def query(self, command: str, delay: float | None = None) -> str:
        if delay is None:
            return f"QUERY:{command}"
        return f"QUERY:{command}:delay={delay}"

    def close(self) -> None:
        self.closed = True


class FakeResourceManager:
    def __init__(self, resource: FakeResource) -> None:
        self._resource = resource
        self.open_calls: list[tuple[str, int]] = []

    def list_resources(self, query: str):
        self.last_list_query = query
        return ("TCPIP0::1::INSTR", "USB0::2::INSTR")

    def list_resources_info(self, query: str):
        self.last_info_query = query
        return {
            "TCPIP0::1::INSTR": FakeResourceInfo(
                alias="scope",
                interface_type="tcpip",
                resource_class="INSTR",
            ),
            "USB0::2::INSTR": FakeResourceInfo(
                alias=None,
                interface_type="usb",
                resource_class="INSTR",
            ),
        }

    def open_resource(self, resource_name: str, open_timeout: int = 0):
        self.open_calls.append((resource_name, open_timeout))
        return self._resource

    def resource_info(self, resource_name: str, extended: bool = True):
        if not extended:
            raise AssertionError("expected extended=True")
        return FakeResourceInfo(
            alias="scope",
            interface_type="tcpip",
            resource_class="INSTR",
            interface_board_number=0,
            resource_name=resource_name,
        )


class FailingResourceManager:
    def list_resources(self, query: str):
        del query
        raise RuntimeError("list failure")

    def list_resources_info(self, query: str):
        del query
        raise RuntimeError("info failure")

    def resource_info(self, resource_name: str, extended: bool = True):
        del resource_name, extended
        raise RuntimeError("resource info failure")


class VisaAdapterTests(unittest.TestCase):
    def test_backend_status_reports_import_failure(self) -> None:
        adapter = VisaAdapter(default_backend="sim")

        with patch.object(VisaAdapter, "_try_import_pyvisa", return_value=(None, "import failed")):
            status = adapter.backend_status()

        self.assertFalse(status.available)
        self.assertEqual(status.backend_hint, "@sim")
        self.assertEqual(status.import_error, "import failed")

    def test_backend_status_reports_resource_manager_failure(self) -> None:
        adapter = VisaAdapter()

        with patch.object(VisaAdapter, "_try_import_pyvisa", return_value=(type("PyVisaStub", (), {"__version__": "1.0"}), None)):
            with patch.object(VisaAdapter, "_get_resource_manager", side_effect=RuntimeError("rm failed")):
                status = adapter.backend_status()

        self.assertFalse(status.available)
        self.assertEqual(status.pyvisa_version, "1.0")
        self.assertEqual(status.import_error, "rm failed")

    def test_list_visible_resources_maps_manager_output(self) -> None:
        resource = FakeResource()
        adapter = VisaAdapter()
        adapter._resource_manager = FakeResourceManager(resource)

        result = adapter.list_visible_resources("?*")

        self.assertIsNone(result.error)
        self.assertEqual(result.query, "?*")
        self.assertEqual(len(result.resources), 2)
        self.assertEqual(result.resources[0].resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(result.resources[0].alias, "scope")
        self.assertEqual(result.resources[0].interface_type, "tcpip")

    def test_list_visible_resources_returns_structured_error_on_manager_failure(self) -> None:
        adapter = VisaAdapter()
        adapter._resource_manager = FailingResourceManager()

        result = adapter.list_visible_resources("?*")

        self.assertEqual(result.query, "?*")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "RuntimeError")
        self.assertEqual(result.error.message, "list failure")

    def test_open_resource_applies_runtime_settings(self) -> None:
        resource = FakeResource()
        manager = FakeResourceManager(resource)
        adapter = VisaAdapter()
        adapter._resource_manager = manager

        opened = adapter.open_resource(
            resource_name="TCPIP0::1::INSTR",
            open_timeout_ms=25,
            timeout_ms=3000,
            read_termination="\n",
            write_termination="\r\n",
            query_delay_s=0.5,
            chunk_size=8192,
        )

        self.assertIs(opened, resource)
        self.assertEqual(manager.open_calls, [("TCPIP0::1::INSTR", 25)])
        self.assertEqual(resource.timeout, 3000)
        self.assertEqual(resource.read_termination, "\n")
        self.assertEqual(resource.write_termination, "\r\n")
        self.assertEqual(resource.query_delay, 0.5)
        self.assertEqual(resource.chunk_size, 8192)

    def test_message_and_info_helpers_delegate_to_resource_manager_and_resource(self) -> None:
        resource = FakeResource()
        adapter = VisaAdapter()
        adapter._resource_manager = FakeResourceManager(resource)

        bytes_written = adapter.write_message(resource, "*IDN?")
        binary_bytes_written = adapter.write_binary_message(resource, b"\x01\x02\x03")
        read_data = adapter.read_message(resource)
        binary_read_data = adapter.read_binary_message(resource)
        query_data = adapter.query_message(resource, "*IDN?", delay_s=0.25)
        binary_query_data = adapter.query_binary_message(resource, "CURV?")
        info_result = adapter.read_resource_info("TCPIP0::1::INSTR")
        adapter.close_resource(resource)

        self.assertEqual(bytes_written, 5)
        self.assertEqual(binary_bytes_written, 3)
        self.assertEqual(read_data, "READ:OK")
        self.assertEqual(binary_read_data, b"\x00\x01RAW")
        self.assertEqual(query_data, "QUERY:*IDN?:delay=0.25")
        self.assertEqual(binary_query_data, b"\x23\x34QUERY")
        self.assertIsNone(info_result.error)
        self.assertEqual(info_result.info.resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(info_result.info.interface_board_number, 0)
        self.assertEqual(resource.raw_writes, [b"\x01\x02\x03"])
        self.assertEqual(resource.writes, ["*IDN?", "CURV?"])
        self.assertTrue(resource.closed)

    def test_binary_helpers_raise_when_resource_lacks_raw_methods(self) -> None:
        class TextOnlyResource:
            def write(self, message: str) -> int:
                return len(message)

            def read(self) -> str:
                return "READ:OK"

        adapter = VisaAdapter()
        resource = TextOnlyResource()

        with self.assertRaisesRegex(Exception, "Binary write is unavailable"):
            adapter.write_binary_message(resource, b"abc")
        with self.assertRaisesRegex(Exception, "Binary read is unavailable"):
            adapter.read_binary_message(resource)

    def test_read_resource_info_returns_structured_error_on_failure(self) -> None:
        adapter = VisaAdapter()
        adapter._resource_manager = FailingResourceManager()

        result = adapter.read_resource_info("TCPIP0::1::INSTR")

        self.assertEqual(result.resource_name, "TCPIP0::1::INSTR")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "RuntimeError")
        self.assertEqual(result.error.message, "resource info failure")


if __name__ == "__main__":
    unittest.main()