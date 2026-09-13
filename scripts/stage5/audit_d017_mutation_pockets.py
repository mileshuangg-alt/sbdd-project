"""Materialize the frozen D017 mutation pocket-membership audit."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.d017_construct_audit import sha256_file, write_audit_artifact  # noqa: E402
from evaluation.d017_mutation_pocket_audit import (  # noqa: E402
    audit_mutation_pocket,
    ligand_instances_by_structure,
)


D017 = ROOT / "references" / "stage5" / "d017"


def main() -> None:
    manifest_path = D017 / "calibration_structure_manifest.json"
    mapping_path = D017 / "receptor_inputs" / "position_only_mapping.json"
    manifest = json.loads(manifest_path.read_text())
    mapping = json.loads(mapping_path.read_text())
    ligand_instances = ligand_instances_by_structure(manifest)
    records = []
    for receptor in mapping["receptor_inputs"]:
        key = (receptor["structure_id"], receptor["selected_author_chain"])
        if key not in ligand_instances:
            raise ValueError(f"No frozen manifest ligand instance for {key}")
        structure_path = Path(receptor["source_structure"]["path"])
        for mutation in receptor["residue_mappings"]:
            if mutation["mutation_flag"]:
                records.append(audit_mutation_pocket(
                    structure_id=key[0], author_chain=key[1], structure_path=structure_path,
                    ligand_instance=ligand_instances[key], mutation=mutation,
                ))
    write_audit_artifact(
        {
            "schema_version": 1,
            "decision_id": "D017",
            "artifact_type": "FROZEN_4_5_ANGSTROM_MUTATION_POCKET_AUDIT",
            "inputs": {
                "mapping_artifact": {"path": str(mapping_path), "sha256": sha256_file(mapping_path)},
                "manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path)},
            },
            "mutation_audits": records,
        },
        D017 / "receptor_inputs" / "mutation_pocket_audit.json",
    )


if __name__ == "__main__":
    main()
