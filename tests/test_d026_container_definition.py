import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.stage6.d026_runtime_probe import (
    _add_exposed_inchi_version_fields,
    _inchi_metadata,
    _observed_aizynthfinder_source_commit,
)


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "containers/stage6/d026/Dockerfile"


class D026ContainerDefinitionTests(unittest.TestCase):
    def test_dockerfile_pins_immutable_inputs(self):
        text = DOCKERFILE.read_text()

        self.assertIn("FROM d026-python-base:3.11.11-pinned", text)
        self.assertIn('LABEL org.opencontainers.image.base.name="python:3.11.11"', text)
        self.assertIn(
            'LABEL org.opencontainers.image.base.digest="sha256:'
            '4ca910a51a1a474e5d95aa52455331b2a942eeae3c498be1ad7a2ff9b00bf"',
            text,
        )
        self.assertNotIn("FROM python:3.11.11", text)
        self.assertNotIn("FROM python@sha256", text)
        self.assertIn("rdkit==2023.9.6", text)
        self.assertIn("9859f5bc6c04c342b828aff20001504c238d7ac1", text)
        self.assertIn("git checkout 9859f5bc6c04c342b828aff20001504c238d7ac1", text)
        self.assertNotIn("@main", text)
        self.assertNotIn("latest", text)

    def test_dockerfile_does_not_embed_project_data_or_bks_paths(self):
        text = DOCKERFILE.read_text()

        forbidden = (
            "/nfs/",
            "BKS",
            "zinc20/2D",
            "references/stage6/d025_shared_stock/source",
            "zinc_stock.hdf5",
            "COPY .",
            "COPY references",
            "COPY data",
            "ssh",
            "credential",
            "secret",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_probe_reports_unavailable_inchi_metadata_without_fabricating_version(self):
        with mock.patch.dict("sys.modules", {"rdkit.Chem.inchi": None}):
            metadata = _inchi_metadata()

        self.assertFalse(metadata["available"])
        self.assertIsNone(metadata["backend_version"])
        self.assertEqual(metadata["backend_version_status"], "unavailable")

    def test_probe_does_not_fabricate_inchi_version_when_module_exposes_none(self):
        class FakeInchiModule:
            pass

        metadata = {
            "backend_version": None,
            "backend_version_status": "unavailable",
            "exposed_version_fields": {},
        }
        _add_exposed_inchi_version_fields(FakeInchiModule(), metadata)

        self.assertEqual(metadata["exposed_version_fields"], {})
        self.assertIsNone(metadata["backend_version"])
        self.assertEqual(metadata["backend_version_status"], "unavailable")

    def test_probe_reports_observed_source_commit_from_runtime_git_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "aizynthfinder-src"
            source_dir.mkdir()
            completed = subprocess.CompletedProcess(
                args=["git"],
                returncode=0,
                stdout="9859f5bc6c04c342b828aff20001504c238d7ac1\n",
                stderr="",
            )
            with mock.patch(
                "scripts.stage6.d026_runtime_probe.subprocess.run",
                return_value=completed,
            ) as run_mock:
                metadata = _observed_aizynthfinder_source_commit(source_dir)

        self.assertEqual(
            metadata["observed_source_commit"],
            "9859f5bc6c04c342b828aff20001504c238d7ac1",
        )
        self.assertEqual(metadata["observed_source_commit_status"], "observed")
        self.assertIsNone(metadata["observed_source_commit_error"])
        run_mock.assert_called_once_with(
            ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_probe_reports_null_observed_commit_when_source_dir_missing(self):
        metadata = _observed_aizynthfinder_source_commit(
            Path("/definitely/not/a/d026/source/path")
        )

        self.assertIsNone(metadata["observed_source_commit"])
        self.assertEqual(
            metadata["observed_source_commit_status"],
            "source_dir_missing",
        )
        self.assertIn("missing source directory", metadata["observed_source_commit_error"])

    def test_probe_reports_null_observed_commit_when_git_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "aizynthfinder-src"
            source_dir.mkdir()
            with mock.patch(
                "scripts.stage6.d026_runtime_probe.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["git"]),
            ):
                metadata = _observed_aizynthfinder_source_commit(source_dir)

        self.assertIsNone(metadata["observed_source_commit"])
        self.assertEqual(
            metadata["observed_source_commit_status"],
            "git_rev_parse_failed",
        )

    def test_probe_script_contains_machine_readable_json_entrypoint(self):
        script = (ROOT / "scripts/stage6/d026_runtime_probe.py").read_text()
        self.assertIn("json.dumps", script)
        self.assertIn("sort_keys=True", script)
        self.assertIn("observed_source_commit", script)
        self.assertIn("git", script)
        self.assertIn("rev-parse", script)

    def test_smoke_test_requires_observed_commit_match(self):
        script = (ROOT / "scripts/stage6/d026_smoke_test.py").read_text()
        self.assertIn("aizynthfinder_observed_commit_matches_expected", script)
        self.assertIn("observed_source_commit", script)

    def test_inventory_script_sorts_packages(self):
        script = (ROOT / "scripts/stage6/d026_package_inventory.py").read_text()
        self.assertIn("sorted(records", script)
        self.assertIn("json.dumps", script)


if __name__ == "__main__":
    unittest.main()
