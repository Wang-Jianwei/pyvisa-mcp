from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.visa_adapter import VisaAdapter


@unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
class PyvisaSimSmokeTests(unittest.TestCase):
    def test_adapter_uses_custom_sim_profile_for_list_open_and_query(self) -> None:
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        adapter = VisaAdapter(default_backend=f"{profile.as_posix()}@sim")

        inventory = adapter.list_visible_resources("?*")

        self.assertIsNone(inventory.error)
        self.assertEqual(inventory.backend_hint, f"{profile.as_posix()}@sim")
        self.assertIn("ASRL2::INSTR", [item.resource_name for item in inventory.resources])

        resource = adapter.open_resource(resource_name="ASRL2::INSTR", timeout_ms=2500)
        try:
            response = adapter.query_message(resource, "*IDN?")
        finally:
            adapter.close_resource(resource)

        self.assertEqual(response, "PYVISA-MCP,SIM,0.1\n")


if __name__ == "__main__":
    unittest.main()