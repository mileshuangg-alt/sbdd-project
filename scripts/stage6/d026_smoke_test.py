#!/usr/bin/env python
from __future__ import annotations

import json
import platform
import sys

from d026_runtime_probe import collect_runtime_probe


EXPECTED_PYTHON_VERSION = "3.11.11"
EXPECTED_RDKIT_VERSION = "2023.09.6"
EXPECTED_AIZYNTHFINDER_VERSION = "4.4.1"
EXPECTED_AIZYNTHFINDER_COMMIT = "9859f5bc6c04c342b828aff20001504c238d7ac1"


def run_smoke_test() -> dict:
    from aizynthfinder.chem import Molecule

    probe = collect_runtime_probe()
    mol = Molecule(smiles="CCO", sanitize=True)
    checks = {
        "python_is_3_11_11": platform.python_version() == EXPECTED_PYTHON_VERSION,
        "rdkit_is_2023_9_6": probe["rdkit"]["version"] == EXPECTED_RDKIT_VERSION,
        "aizynthfinder_is_4_4_1": (
            probe["aizynthfinder"]["version"] == EXPECTED_AIZYNTHFINDER_VERSION
        ),
        "aizynthfinder_expected_commit_recorded": (
            probe["aizynthfinder"]["expected_commit"]
            == EXPECTED_AIZYNTHFINDER_COMMIT
        ),
        "aizynthfinder_observed_commit_matches_expected": (
            probe["aizynthfinder"]["observed_source_commit"]
            == EXPECTED_AIZYNTHFINDER_COMMIT
        ),
        "rdkit_inchi_available": probe["rdkit"]["inchi"]["available"] is True,
        "aizynthfinder_molecule_inchikey": bool(mol.inchi_key),
    }
    return {
        "schema_version": 1,
        "checks": checks,
        "probe": probe,
        "smoke_molecule": {
            "smiles": "CCO",
            "inchi_key": mol.inchi_key,
        },
        "passed": all(checks.values()),
    }


def main() -> int:
    result = run_smoke_test()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
