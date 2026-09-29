#!/usr/bin/env python
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_AIZYNTHFINDER_COMMIT = "9859f5bc6c04c342b828aff20001504c238d7ac1"
AIZYNTHFINDER_SOURCE_DIR = Path("/opt/aizynthfinder-src")


def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _module_path(module: Any) -> str | None:
    path = getattr(module, "__file__", None)
    if path is None:
        return None
    return str(Path(path))


def _observed_aizynthfinder_source_commit(
    source_dir: Path = AIZYNTHFINDER_SOURCE_DIR,
) -> dict[str, Any]:
    if not source_dir.exists():
        return {
            "observed_source_commit": None,
            "observed_source_commit_status": "source_dir_missing",
            "observed_source_commit_error": f"missing source directory: {source_dir}",
        }

    try:
        completed = subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return {
            "observed_source_commit": None,
            "observed_source_commit_status": "git_rev_parse_failed",
            "observed_source_commit_error": str(exc),
        }

    return {
        "observed_source_commit": completed.stdout.strip(),
        "observed_source_commit_status": "observed",
        "observed_source_commit_error": None,
    }


def _inchi_metadata() -> dict[str, Any]:
    try:
        from rdkit.Chem import inchi
    except Exception as exc:  # pragma: no cover - exercised in container
        return {
            "available": False,
            "module_path": None,
            "backend_version": None,
            "backend_version_status": "unavailable",
            "error": repr(exc),
        }

    metadata: dict[str, Any] = {
        "available": hasattr(inchi, "MolToInchiKey"),
        "module_path": _module_path(inchi),
        "backend_version": None,
        "backend_version_status": "unavailable",
        "exposed_version_fields": {},
        "mol_to_inchikey_available": hasattr(inchi, "MolToInchiKey"),
    }

    _add_exposed_inchi_version_fields(inchi, metadata)

    if metadata["exposed_version_fields"]:
        metadata["backend_version_status"] = "exposed_by_rdkit"
        metadata["backend_version"] = metadata["exposed_version_fields"]

    return metadata



def _add_exposed_inchi_version_fields(
    inchi_module: Any,
    metadata: dict[str, Any],
) -> None:
    for name in ("INCHI_VERSION", "InchiVersion", "inchiVersion", "__version__"):
        if hasattr(inchi_module, name):
            value = getattr(inchi_module, name)
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    continue
            metadata["exposed_version_fields"][name] = str(value)


def collect_runtime_probe() -> dict[str, Any]:
    import aizynthfinder
    import rdkit

    try:
        import numpy
    except Exception:  # pragma: no cover - optional defensive path
        numpy = None
    try:
        import pandas
    except Exception:  # pragma: no cover - optional defensive path
        pandas = None

    observed_commit = _observed_aizynthfinder_source_commit()

    return {
        "schema_version": 1,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "aizynthfinder": {
            "version": _package_version("aizynthfinder"),
            "package_path": _module_path(aizynthfinder),
            "expected_commit": os.environ.get(
                "D026_AIZYNTHFINDER_COMMIT",
                EXPECTED_AIZYNTHFINDER_COMMIT,
            ),
            **observed_commit,
        },
        "rdkit": {
            "version": getattr(rdkit, "__version__", None),
            "package_path": _module_path(rdkit),
            "inchi": _inchi_metadata(),
        },
        "packages": {
            "numpy": getattr(numpy, "__version__", None) if numpy else None,
            "pandas": getattr(pandas, "__version__", None) if pandas else None,
        },
    }


def main() -> int:
    print(json.dumps(collect_runtime_probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
