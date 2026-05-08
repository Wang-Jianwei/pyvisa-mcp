from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.config import ServerConfig
from pyvisa_mcp.resources import RESOURCE_URIS, register_resources
from pyvisa_mcp.schemas import BackendStatus, ResourceInfoResult, VisibleResource, VisibleResourcesResult
from pyvisa_mcp.session_registry import SessionRegistry
from pyvisa_mcp.tools import TOOL_NAMES


class FakeMCP:
    def __init__(self) -> None:
        self.resources: dict[str, object] = {}

    def resource(self, uri: str):
        def decorator(func: object) -> object:
            self.resources[uri] = func
            return func

        return decorator


class DummyAdapter:
    def backend_status(self) -> BackendStatus:
        return BackendStatus(
            available=True,
            preferred_transport="stdio",
            backend_hint="@sim",
            pyvisa_version="1.14.1",
            resource_manager_ready=True,
        )

    def list_visible_resources(self, query: str) -> VisibleResourcesResult:
        return VisibleResourcesResult(
            query=query,
            backend_hint="@sim",
            resource_count=1,
            resources=[VisibleResource(resource_name="ASRL2::INSTR", resource_class="INSTR")],
        )

    def read_resource_info(self, resource_name: str) -> ResourceInfoResult:
        return ResourceInfoResult(resource_name=resource_name, backend_hint="@sim")


class ResourceRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mcp = FakeMCP()
        self.adapter = DummyAdapter()
        self.registry = SessionRegistry()
        session = self.registry.open(resource_name="ASRL2::INSTR", resource=object(), timeout_ms=1500)
        self.session_id = session.session_id
        register_resources(
            self.mcp,
            adapter=self.adapter,
            registry=self.registry,
            config=ServerConfig(default_backend="@sim"),
            tool_names=TOOL_NAMES,
        )

    def test_visible_resources_resource_exposes_counts_and_backend_hint(self) -> None:
        payload = json.loads(self.mcp.resources["pyvisa-mcp://resources/visible"]())

        self.assertEqual(payload["backend_hint"], "@sim")
        self.assertEqual(payload["resource_count"], 1)
        self.assertEqual(payload["resources"][0]["resource_name"], "ASRL2::INSTR")

    def test_session_snapshot_resource_exposes_session_count(self) -> None:
        payload = json.loads(self.mcp.resources["pyvisa-mcp://sessions"]())

        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["resource_name"], "ASRL2::INSTR")

    def test_capability_resource_exposes_inventory_counts(self) -> None:
        payload = json.loads(self.mcp.resources["pyvisa-mcp://capabilities"]())

        self.assertEqual(payload["tool_count"], len(TOOL_NAMES))
        self.assertEqual(payload["resource_count"], len(RESOURCE_URIS))
        self.assertEqual(payload["resources"], RESOURCE_URIS)


if __name__ == "__main__":
    unittest.main()