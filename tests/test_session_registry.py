from __future__ import annotations

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
        self.assertEqual(snapshot.sessions[0].session_id, summary.session_id)
        self.assertEqual(snapshot.sessions[0].resource_name, "GPIB0::1::INSTR")
        self.assertEqual(snapshot.sessions[0].timeout_ms, 2000)

    def test_close_invokes_callback(self) -> None:
        registry = SessionRegistry()
        resource = DummyResource()
        summary = registry.open(resource_name="USB0::1::INSTR", resource=resource)

        result = registry.close(summary.session_id, close_callback=lambda handle: handle.close())

        self.assertTrue(result.closed)
        self.assertTrue(resource.closed)
        self.assertEqual(len(registry.list_summaries().sessions), 0)

    def test_unknown_session_raises(self) -> None:
        registry = SessionRegistry()
        with self.assertRaises(UnknownSessionError):
            registry.require("missing")


if __name__ == "__main__":
    unittest.main()
