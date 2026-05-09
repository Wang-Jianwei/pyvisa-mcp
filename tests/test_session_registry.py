from __future__ import annotations

from pathlib import Path
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.session_registry import SessionRegistry, UnknownSessionError


class DummyResource:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class SessionRegistryTests(unittest.TestCase):
    def test_open_and_list_session(self) -> None:
        registry = SessionRegistry()
        summary = registry.open(resource_name="GPIB0::1::INSTR", resource=DummyResource(), timeout_ms=2000)
        snapshot = registry.list_summaries()

        self.assertEqual(len(snapshot.sessions), 1)
        self.assertEqual(snapshot.session_count, 1)
        self.assertEqual(snapshot.sessions[0].session_id, summary.session_id)
        self.assertEqual(snapshot.sessions[0].resource_name, "GPIB0::1::INSTR")
        self.assertEqual(snapshot.sessions[0].timeout_ms, 2000)

    def test_close_invokes_callback(self) -> None:
        registry = SessionRegistry()
        resource = DummyResource()
        summary = registry.open(resource_name="USB0::1::INSTR", resource=resource)

        result = registry.close(summary.session_id, close_callback=lambda handle: handle.close())

        self.assertTrue(result.closed)
        self.assertEqual(result.resource_name, "USB0::1::INSTR")
        self.assertTrue(resource.closed)
        self.assertEqual(len(registry.list_summaries().sessions), 0)

    def test_unknown_session_raises(self) -> None:
        registry = SessionRegistry()
        with self.assertRaises(UnknownSessionError):
            registry.require("missing")

    def test_close_removes_registered_temp_files(self) -> None:
        registry = SessionRegistry()
        summary = registry.open(resource_name="USB0::1::INSTR", resource=DummyResource())
        temp_dir = Path(tempfile.mkdtemp())
        temp_file = temp_dir / "capture.bin"
        temp_file.write_bytes(b"\x00\x01")
        registry.register_temp_file(summary.session_id, temp_file)

        registry.close(summary.session_id)

        self.assertFalse(temp_file.exists())

    def test_close_all_removes_registered_temp_files(self) -> None:
        registry = SessionRegistry()
        first = registry.open(resource_name="USB0::1::INSTR", resource=DummyResource())
        second = registry.open(resource_name="USB0::2::INSTR", resource=DummyResource())
        temp_dir = Path(tempfile.mkdtemp())
        first_file = temp_dir / "first.bin"
        second_file = temp_dir / "second.bin"
        first_file.write_bytes(b"a")
        second_file.write_bytes(b"b")
        registry.register_temp_file(first.session_id, first_file)
        registry.register_temp_file(second.session_id, second_file)

        closed_count = registry.close_all()

        self.assertEqual(closed_count, 2)
        self.assertFalse(first_file.exists())
        self.assertFalse(second_file.exists())


if __name__ == "__main__":
    unittest.main()
