"""Materialize the read-only D017 construct-boundary audit artifact."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.d017_construct_audit import (  # noqa: E402
    audit_construct,
    sha256_file,
    write_audit_artifact,
)


D017 = ROOT / "references" / "stage5" / "d017"


def main() -> None:
    selection_path = D017 / "construct_boundary_audit_selection.json"
    manifest_path = D017 / "calibration_structure_manifest.json"
    config_path = D017 / "usalign_20220227_config.json"
    selection = json.loads(selection_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if sha256_file(config_path) != manifest["measurement_config_sha256"]:
        raise ValueError("Frozen D017 measurement config hash does not match the manifest")
    records = [
        audit_construct(
            structure_id=item["structure_id"],
            structure_path=D017 / item["source_mmcif"],
            author_chain=item["author_chain"],
            fasta_path=D017 / item["canonical_fasta"],
        )
        for item in selection["constructs"]
    ]
    audit = {
        "schema_version": 1,
        "decision_id": "D017",
        "audit_type": "READ_ONLY_CONSTRUCT_BOUNDARY_AUDIT",
        "inputs": {
            "selection": {"path": str(selection_path), "sha256": sha256_file(selection_path)},
            "manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path)},
            "measurement_config": {"path": str(config_path), "sha256": sha256_file(config_path)},
        },
        "constructs": records,
    }
    write_audit_artifact(audit, D017 / "construct_boundary_audit.json")


if __name__ == "__main__":
    main()
