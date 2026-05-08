from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
class CliIntegrationTests(unittest.TestCase):
    def test_cli_repl_can_drive_sim_backend_from_piped_input(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyvisa_mcp.cli",
                "--backend",
                f"{profile.as_posix()}@sim",
                "--json",
                "--no-prompt",
            ],
            input="visible ?*\nopen ASRL2::INSTR --timeout-ms 2500\nquery \"*IDN?\"\nclose\nexit\n",
            capture_output=True,
            text=True,
            cwd=root,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"resource_name": "ASRL2::INSTR"', completed.stdout)
        self.assertIn('"response": "PYVISA-MCP,SIM,0.1\\n"', completed.stdout)
        self.assertIn('"closed": true', completed.stdout)


if __name__ == "__main__":
    unittest.main()