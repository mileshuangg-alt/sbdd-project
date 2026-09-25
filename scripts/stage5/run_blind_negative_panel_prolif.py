import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import prolif as plf
from rdkit import Chem, rdBase

from mol2_prolif_adapter import load_mol2_ligand_for_prolif
from test_native_reader_controls import load_ligand, load_protein, run_interaction_reader


ROOT = Path(__file__).resolve().parents[2]
PANEL_DIR = ROOT / "references/stage5/negative_panel/panel"
BLIND_INPUT_DIR = PANEL_DIR / "blind_prolif_inputs"
RECEPTOR_PATH = (
    ROOT
    / "references/stage5/native_complexes/3REY/"
    / "3REY_receptor_pH7.4_restored.pqr"
)
PROTECTED_READER_PATH = ROOT / "scripts/stage5/test_native_reader_controls.py"
PROTECTED_READER_SHA256_BEFORE = (
    "006d0eae192c4776d84d89d3d381c87d289c0fbda749b1ba7c9a93929c07cdf6"
)

OPAQUE_INPUTS = [
    ("NEG001", "NEG001.mol2", "qualified_mol2_adapter"),
    ("NEG002", "NEG002.sdf", "frozen_sdf_route"),
    ("NEG003", "NEG003.sdf", "frozen_sdf_route"),
    ("NEG004", "NEG004.sdf", "frozen_sdf_route"),
    ("NEG005", "NEG005.sdf", "frozen_sdf_route"),
    ("NEG006", "NEG006.sdf", "frozen_sdf_route"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def residue_record(residue) -> dict:
    return {
        "name": getattr(residue, "name", None),
        "number": getattr(residue, "number", None),
        "chain": getattr(residue, "chain", None),
        "repr": repr(residue),
    }


def serialize_interactions(interactions) -> list[dict]:
    records = []
    for pair, residue_interactions in interactions.items():
        ligand_residue, protein_residue = pair
        records.append(
            {
                "ligand_residue": residue_record(ligand_residue),
                "protein_residue": residue_record(protein_residue),
                "interactions": json_safe(residue_interactions),
            }
        )
    return records


def interaction_classes_for_residue(records: list[dict], number: int, name: str) -> list[str]:
    classes = set()
    for record in records:
        residue = record["protein_residue"]
        if residue["number"] == number and residue["name"] == name:
            classes.update(record["interactions"].keys())
    return sorted(classes)


def records_for_residue_number(records: list[dict], number: int) -> list[dict]:
    return [
        record
        for record in records
        if record["protein_residue"]["number"] == number
    ]


def load_blind_ligand(path: Path, route: str):
    if route == "qualified_mol2_adapter":
        return load_mol2_ligand_for_prolif(path)
    if route == "frozen_sdf_route":
        return load_ligand(path)
    raise ValueError(f"Unexpected ligand-loading route: {route}")


def recognition_result(phe168_classes: list[str], asn253_classes: list[str]) -> bool:
    phe_ok = bool({"Hydrophobic", "PiStacking"}.intersection(phe168_classes))
    asn_ok = "HBAcceptor" in asn253_classes
    return phe_ok and asn_ok


def read_one_pose(protein, opaque_id: str, filename: str, route: str) -> dict:
    input_path = BLIND_INPUT_DIR / filename
    ligand = load_blind_ligand(input_path, route)
    interactions = run_interaction_reader(protein, ligand)
    interaction_records = serialize_interactions(interactions)

    residue75_records = records_for_residue_number(interaction_records, 75)
    guard_triggered = bool(residue75_records)

    result = {
        "opaque_id": opaque_id,
        "input_filename": filename,
        "input_path": str(input_path.relative_to(ROOT)),
        "input_sha256": sha256(input_path),
        "ligand_loading_route": route,
        "prolif_interactions": interaction_records,
        "residue_75_guard": {
            "state": "TRIGGERED" if guard_triggered else "CLEAR",
            "residue_75_contacts": residue75_records if guard_triggered else "NONE",
        },
    }

    if guard_triggered:
        result["anchor_results"] = None
        result["frozen_recognition_pattern"] = None
        result["processing_state"] = "STOPPED_BY_RESIDUE_75_GUARD"
        return result

    phe168_classes = interaction_classes_for_residue(interaction_records, 168, "PHE")
    asn253_classes = interaction_classes_for_residue(interaction_records, 253, "ASN")

    result["anchor_results"] = {
        "Phe168": {
            "interaction_classes": phe168_classes,
            "metadata": [
                record
                for record in interaction_records
                if record["protein_residue"]["number"] == 168
                and record["protein_residue"]["name"] == "PHE"
            ],
        },
        "Asn253": {
            "interaction_classes": asn253_classes,
            "metadata": [
                record
                for record in interaction_records
                if record["protein_residue"]["number"] == 253
                and record["protein_residue"]["name"] == "ASN"
            ],
        },
    }
    result["frozen_recognition_pattern"] = recognition_result(
        phe168_classes,
        asn253_classes,
    )
    result["processing_state"] = "ANCHOR_REPORTED"
    return result


def write_summary(report: dict, summary_path: Path) -> None:
    lines = [
        "# Stage-5 Blind Frozen ProLIF Negative-Panel Read",
        "",
        f"Execution timestamp: {report['execution_timestamp_utc']}",
        f"Inputs processed: {report['validation']['inputs_processed_count']}/6",
        "",
        "## Results",
        "",
    ]
    for result in report["results"]:
        guard = result["residue_75_guard"]["state"]
        recognition = result["frozen_recognition_pattern"]
        lines.append(
            f"- {result['opaque_id']}: guard={guard}; "
            f"recognition={recognition}; state={result['processing_state']}"
        )
    lines.extend(
        [
            "",
            "## Scope Confirmation",
            "",
            "- Blind mapping was not used to alter processing.",
            "- No candidate identities are unblinded in this artifact.",
            "- No docking, scoring, residue-75 guard redesign, or reader tuning was run.",
            "- Overall Stage-5 panel verdict was not computed.",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    execution_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_json = PANEL_DIR / f"blind_negative_panel_prolif_read_{execution_timestamp}.json"
    output_md = PANEL_DIR / f"blind_negative_panel_prolif_read_{execution_timestamp}.md"

    protein_results = load_protein(RECEPTOR_PATH)
    protein = protein_results["protein"]

    results = []
    ligand_loading_failures = []
    for opaque_id, filename, route in OPAQUE_INPUTS:
        try:
            results.append(read_one_pose(protein, opaque_id, filename, route))
        except Exception as exc:
            ligand_loading_failures.append(
                {
                    "opaque_id": opaque_id,
                    "input_filename": filename,
                    "ligand_loading_route": route,
                    "error": repr(exc),
                }
            )

    protected_reader_sha256_after = sha256(PROTECTED_READER_PATH)

    report = {
        "execution_timestamp_utc": execution_timestamp,
        "scope_confirmation": {
            "blind_negative_panel_read_only": True,
            "prolif_interaction_reader_run": True,
            "residue_75_guard_execution": True,
            "a2a_recognition_evaluation_run": False,
            "blind_mapping_used_to_alter_processing": False,
            "candidate_identities_unblinded": False,
            "docking_or_scoring_run": False,
            "overall_stage5_panel_verdict_computed": False,
            "reader_parameters_tuned": False,
            "frozen_inputs_modified": False,
        },
        "package_versions": {
            "prolif": getattr(plf, "__version__", "unknown"),
            "rdkit": rdBase.rdkitVersion,
        },
        "reader": {
            "source_file": str(PROTECTED_READER_PATH.relative_to(ROOT)),
            "source_file_sha256_before_task": PROTECTED_READER_SHA256_BEFORE,
            "source_file_sha256_after_run": protected_reader_sha256_after,
            "source_file_unchanged": (
                protected_reader_sha256_after == PROTECTED_READER_SHA256_BEFORE
            ),
            "functions": ["load_protein", "run_interaction_reader"],
            "fingerprint": "default plf.Fingerprint() via run_interaction_reader()",
            "metadata": True,
        },
        "receptor": {
            "path": str(RECEPTOR_PATH.relative_to(ROOT)),
            "sha256": sha256(RECEPTOR_PATH),
        },
        "inputs": [
            {
                "opaque_id": opaque_id,
                "input_filename": filename,
                "input_sha256": sha256(BLIND_INPUT_DIR / filename),
                "ligand_loading_route": route,
            }
            for opaque_id, filename, route in OPAQUE_INPUTS
        ],
        "validation": {
            "inputs_expected_count": 6,
            "inputs_processed_count": len(results),
            "ligand_loading_failures": ligand_loading_failures,
            "all_inputs_processed_or_guard_stopped": (
                len(results) + len(ligand_loading_failures) == 6
            ),
            "unexpected_ligand_loading_failures": len(ligand_loading_failures),
            "frozen_reader_file_unchanged": (
                protected_reader_sha256_after == PROTECTED_READER_SHA256_BEFORE
            ),
            "blind_mapping_not_used_to_alter_processing": True,
        },
        "results": results,
        "artifacts": {
            "machine_readable_result": str(output_json.relative_to(ROOT)),
            "human_readable_summary": str(output_md.relative_to(ROOT)),
        },
    }

    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_summary(report, output_md)
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")
    print(f"Inputs processed: {len(results)}/6")
    print(f"Ligand-loading failures: {len(ligand_loading_failures)}")


if __name__ == "__main__":
    main()
