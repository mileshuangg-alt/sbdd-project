"""Materialize exact-coordinate D017 receptor-only mmCIF inputs."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.d017_construct_audit import (  # noqa: E402
    parse_fasta,
    parse_reference_spans,
    sha256_file,
    write_audit_artifact,
)
from evaluation.d017_receptor_input import extract_receptor_mmcif  # noqa: E402


D017 = ROOT / "references" / "stage5" / "d017"


def main() -> None:
    materialization_path = D017 / "receptor_input_materialization.json"
    manifest_path = D017 / "calibration_structure_manifest.json"
    materialization = json.loads(materialization_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    config_path = D017 / materialization["active_config"]
    if sha256_file(config_path) != materialization["active_config_sha256"]:
        raise ValueError("Active D017 configuration hash does not match frozen record")
    if sha256_file(manifest_path) != materialization["manifest_sha256"]:
        raise ValueError("Frozen D017 manifest hash does not match the materialization record")
    manifest_pairs = {
        (row[f"{role}_pdb"], row[f"{role}_chain"])
        for row in manifest["rows"]
        for role in ("target", "homolog")
    }
    fasta_by_accession = {
        parse_fasta(path)[0]: path
        for path in (D017 / "canonical_sequences").glob("*.fasta")
    }
    selections = []
    for structure_id, author_chain in sorted(manifest_pairs):
        structure_path = D017 / "structures" / "raw" / f"{structure_id}.cif"
        accessions = {
            span.accession
            for span in parse_reference_spans(structure_path, author_chain)
            if span.accession in fasta_by_accession
        }
        if len(accessions) != 1:
            raise ValueError(
                f"Expected one frozen canonical sequence for {structure_id} {author_chain}"
            )
        accession = accessions.pop()
        selections.append((structure_id, author_chain, structure_path, fasta_by_accession[accession]))
    records = [
        extract_receptor_mmcif(
            structure_id=structure_id,
            structure_path=structure_path,
            author_chain=author_chain,
            fasta_path=fasta_path,
            output_path=D017 / "receptor_inputs" / f"{structure_id}_{author_chain}.cif",
        )
        for structure_id, author_chain, structure_path, fasta_path in selections
    ]
    write_audit_artifact(
        {
            "schema_version": 1,
            "decision_id": "D017",
            "artifact_type": "POSITION_ONLY_RECEPTOR_MAPPING",
            "inputs": {
                "materialization": {
                    "path": str(materialization_path),
                    "sha256": sha256_file(materialization_path),
                },
                "active_config": {
                    "path": str(config_path), "sha256": sha256_file(config_path),
                },
                "manifest": {
                    "path": str(manifest_path), "sha256": sha256_file(manifest_path),
                },
                "canonical_fastas": [
                    {"path": str(path), "sha256": sha256_file(path)}
                    for path in sorted(fasta_by_accession.values())
                ],
            },
            "receptor_inputs": records,
        },
        D017 / "receptor_inputs" / "position_only_mapping.json",
    )


if __name__ == "__main__":
    main()
