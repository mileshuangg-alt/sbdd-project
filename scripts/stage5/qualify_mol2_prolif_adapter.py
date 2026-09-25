import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import prolif as plf
from rdkit import Chem, rdBase

from mol2_prolif_adapter import load_mol2_ligand_for_prolif_with_audit


ROOT = Path(__file__).resolve().parents[2]
NEG001_PATH = (
    ROOT
    / "references/stage5/negative_panel/panel/blind_prolif_inputs/NEG001.mol2"
)
PROTECTED_READER_PATH = ROOT / "scripts/stage5/test_native_reader_controls.py"
OUTPUT_DIR = (
    ROOT
    / "references/stage5/negative_panel/panel/mol2_adapter_qualification"
)
REPORT_PATH = OUTPUT_DIR / "NEG001_mol2_adapter_qualification.json"
SUMMARY_PATH = OUTPUT_DIR / "NEG001_mol2_adapter_qualification.md"
PROTECTED_READER_SHA256_BEFORE = (
    "006d0eae192c4776d84d89d3d381c87d289c0fbda749b1ba7c9a93929c07cdf6"
)
PROTECTED_READER_SHA256_BEFORE_PROVENANCE = (
    "Captured with `shasum -a 256 scripts/stage5/"
    "test_native_reader_controls.py` before this adapter task edited files."
)

NATIVE_CONTROLS = [
    {
        "control_id": "3REY_XAC",
        "pdb_id": "3REY",
        "ligand_code": "XAC",
        "path": ROOT
        / "references/stage5/native_complexes/3REY/"
        / "3REY_XAC_native_pH7.4_restored.sdf",
    },
    {
        "control_id": "5OLH_9XT",
        "pdb_id": "5OLH",
        "ligand_code": "9XT",
        "path": ROOT
        / "references/stage5/native_complexes/5OLH/"
        / "5OLH_9XT_native_pH7.4_restored.sdf",
    },
    {
        "control_id": "5OLO_9XW",
        "pdb_id": "5OLO",
        "ligand_code": "9XW",
        "path": ROOT
        / "references/stage5/native_complexes/5OLO/"
        / "5OLO_9XW_native_pH7.4_restored.sdf",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_sdf(path: Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(
        str(path),
        removeHs=False,
    )
    molecule = supplier[0]

    if molecule is None:
        raise ValueError(f"RDKit failed to parse SDF ligand: {path}")

    return molecule


def bond_order_label(bond: Chem.Bond) -> str:
    if bond.GetIsAromatic():
        return "AROMATIC"
    return str(bond.GetBondType())


def atom_record(atom: Chem.Atom) -> dict:
    return {
        "atom_index": atom.GetIdx(),
        "element": atom.GetSymbol(),
        "formal_charge": atom.GetFormalCharge(),
        "is_aromatic": atom.GetIsAromatic(),
    }


def bond_record(bond: Chem.Bond) -> dict:
    return {
        "begin_atom_index": bond.GetBeginAtomIdx(),
        "end_atom_index": bond.GetEndAtomIdx(),
        "bond_order": bond_order_label(bond),
        "is_aromatic": bond.GetIsAromatic(),
    }


def chemistry_record(label: str, path: Path, molecule: Chem.Mol) -> dict:
    atoms = [atom_record(atom) for atom in molecule.GetAtoms()]
    bonds = [bond_record(bond) for bond in molecule.GetBonds()]

    return {
        "label": label,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "atom_count": molecule.GetNumAtoms(),
        "bond_count": molecule.GetNumBonds(),
        "atoms": atoms,
        "bonds": bonds,
        "bond_order_counts": descriptor_counts(
            [bond["bond_order"] for bond in bonds]
        ),
        "formal_charge_counts": descriptor_counts(
            [atom["formal_charge"] for atom in atoms]
        ),
        "aromaticity_counts": descriptor_counts(
            [atom["is_aromatic"] for atom in atoms]
        ),
    }


def descriptor_counts(values: list) -> dict:
    counts = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def compare_records(neg001: dict, native: dict) -> dict:
    differences = []

    for field in ["atom_count", "bond_count"]:
        if neg001[field] != native[field]:
            differences.append(
                {
                    "field": field,
                    "NEG001": neg001[field],
                    "native_control": native[field],
                }
            )

    for field in [
        "bond_order_counts",
        "formal_charge_counts",
        "aromaticity_counts",
    ]:
        if neg001[field] != native[field]:
            differences.append(
                {
                    "field": field,
                    "NEG001": neg001[field],
                    "native_control": native[field],
                }
            )

    return {
        "native_control": native["label"],
        "method": (
            "Cross-molecule descriptive comparison only. NEG001 and this "
            "native control are different ligand identities, so differences "
            "are not parser/perception mismatches and no atom mapping is "
            "attempted."
        ),
        "difference_count": len(differences),
        "differences": differences,
    }


def package_versions() -> dict:
    return {
        "python": platform.python_version(),
        "rdkit": rdBase.rdkitVersion,
        "prolif": getattr(plf, "__version__", "unknown"),
        "numpy": np.__version__,
    }


def write_summary(report: dict) -> None:
    coordinate = report["coordinate_preservation"]
    comparison_lines = []

    for comparison in report["chemical_perception"]["comparisons"]:
        comparison_lines.append(
            f"- {comparison['native_control']}: "
            f"{comparison['difference_count']} descriptive differences"
        )

    content = "\n".join(
        [
            "# NEG001 MOL2 ProLIF Adapter Qualification",
            "",
            "Qualification review status: "
            f"{report['qualification_review_status']}",
            "",
            "## Adapter",
            "",
            f"- Path: {report['adapter']['path']}",
            f"- Function: {report['adapter']['function']}",
            "",
            "## Coordinate Preservation",
            "",
            f"- Atom count: {coordinate['atom_count']}",
            f"- Has conformer: {coordinate['has_conformer']}",
            "- Maximum absolute coordinate deviation: "
            f"{coordinate['max_abs_coordinate_deviation']}",
            "- RMS coordinate deviation: "
            f"{coordinate['rms_coordinate_deviation']}",
            "- Tolerance: none invented; raw deviations are reported.",
            "",
            "## Chemical Perception Records",
            "",
            *comparison_lines,
            "",
            "## Protected-File Check",
            "",
            "- `scripts/stage5/test_native_reader_controls.py` "
            f"byte-for-byte unchanged: {report['protected_file_check']['unchanged']}",
            "",
            "## Scope Confirmation",
            "",
            "- NEG001 interaction reader run: not run",
            "- blind six-pose ProLIF POD: not run",
        ]
    )

    SUMMARY_PATH.write_text(content + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    protected_sha256_after = sha256(PROTECTED_READER_PATH)

    adapter_result = load_mol2_ligand_for_prolif_with_audit(
        NEG001_PATH
    )

    neg001_record = chemistry_record(
        "NEG001_MOL2_RDKit",
        NEG001_PATH,
        adapter_result.rdkit_molecule,
    )

    native_records = []
    for control in NATIVE_CONTROLS:
        molecule = load_sdf(
            control["path"]
        )
        native_records.append(
            chemistry_record(
                control["control_id"],
                control["path"],
                molecule,
            )
        )

    comparisons = [
        compare_records(
            neg001_record,
            native_record,
        )
        for native_record in native_records
    ]

    report = {
        "qualification_review_status": "PENDING_HUMAN_REVIEW",
        "mechanical_execution": {
            "adapter_constructed_prolif_molecule": (
                adapter_result.prolif_molecule is not None
            ),
            "coordinate_audit_completed": True,
            "protected_reader_unchanged": (
                protected_sha256_after == PROTECTED_READER_SHA256_BEFORE
            ),
            "chemical_perception_record_completed": True,
        },
        "scope": {
            "adapter_qualification_only": True,
            "neg001_interaction_reader_run": False,
            "blind_six_pose_prolif_pod_run": False,
            "geometry_modified": False,
            "chemistry_repaired_or_normalized": False,
        },
        "adapter": {
            "path": "scripts/stage5/mol2_prolif_adapter.py",
            "function": "load_mol2_ligand_for_prolif",
            "route": "MOL2 -> RDKit MolFromMol2File -> plf.Molecule.from_rdkit",
            "rdkit_parameters": {
                "sanitize": True,
                "removeHs": False,
                "cleanupSubstructures": False,
            },
        },
        "package_versions": package_versions(),
        "inputs": {
            "NEG001": {
                "path": str(NEG001_PATH.relative_to(ROOT)),
                "sha256": sha256(NEG001_PATH),
            },
            "native_controls": [
                {
                    "label": record["label"],
                    "path": record["path"],
                    "sha256": record["sha256"],
                }
                for record in native_records
            ],
        },
        "coordinate_preservation": {
            "method": (
                "Coordinates parsed directly from the frozen MOL2 ATOM "
                "block were compared with the RDKit conformer coordinates "
                "immediately before plf.Molecule.from_rdkit(). RMS is the "
                "root mean square per-atom Euclidean deviation. No tolerance "
                "was applied."
            ),
            "atom_count": adapter_result.coordinate_audit.atom_count,
            "has_conformer": adapter_result.coordinate_audit.has_conformer,
            "prolif_atom_count": adapter_result.prolif_molecule.GetNumAtoms(),
            "max_abs_coordinate_deviation": (
                adapter_result.coordinate_audit.max_abs_coordinate_deviation
            ),
            "rms_coordinate_deviation": (
                adapter_result.coordinate_audit.rms_coordinate_deviation
            ),
        },
        "chemical_perception": {
            "comparison_method": (
                "NEG001 MOL2 RDKit perception is compared to the native "
                "control SDF RDKit perception used by the frozen reader. "
                "NEG001 and native controls are different ligand identities; "
                "cross-molecule aggregate differences are records for human "
                "review, not parser/perception mismatches. No atom mapping, "
                "repair, or normalization is performed."
            ),
            "NEG001": neg001_record,
            "native_controls": native_records,
            "comparisons": comparisons,
        },
        "protected_file_check": {
            "path": str(PROTECTED_READER_PATH.relative_to(ROOT)),
            "sha256_before_task": PROTECTED_READER_SHA256_BEFORE,
            "sha256_before_task_provenance": (
                PROTECTED_READER_SHA256_BEFORE_PROVENANCE
            ),
            "sha256_after_task": protected_sha256_after,
            "unchanged": (
                protected_sha256_after == PROTECTED_READER_SHA256_BEFORE
            ),
        },
        "artifacts": {
            "machine_readable_report": str(REPORT_PATH.relative_to(ROOT)),
            "human_readable_summary": str(SUMMARY_PATH.relative_to(ROOT)),
        },
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    write_summary(report)

    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(
        "Qualification review status: "
        f"{report['qualification_review_status']}"
    )


if __name__ == "__main__":
    main()
