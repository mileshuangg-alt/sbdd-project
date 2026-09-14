import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from rdkit import Chem


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

from evaluation.plip_witness import (  # noqa: E402
    load_plip_witness_config,
    summarize_plip_xml_for_case,
)


def parse_args():
    """Parse command-line arguments for PLIP concordance measurement."""

    parser = argparse.ArgumentParser(
        description="Run configured PLIP witness concordance measurements."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the PLIP witness JSON config.",
    )
    parser.add_argument(
        "--measurement-id",
        required=True,
        help="Configured concordance measurement ID to run.",
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Base path for relative artifact paths in config.",
    )

    return parser.parse_args()


def select_measurement(config, measurement_id):
    """Select one configured concordance measurement."""

    for measurement in config.get("concordance_measurements", []):
        if measurement["measurement_id"] == measurement_id:
            return measurement

    raise ValueError(
        f"No configured concordance measurement: {measurement_id}"
    )


def resolve_path(base_path, path_text):
    """Resolve a config path against the repository base path."""

    path = Path(path_text)
    if path.is_absolute():
        return path
    return Path(base_path) / path


def load_pose(pose_path, pose_format):
    """Load one frozen ligand pose without generating coordinates."""

    if pose_format == "rdkit_mol":
        molecule = pose_path
    elif pose_format == "mol2":
        molecule = Chem.MolFromMol2File(
            str(pose_path),
            sanitize=False,
            removeHs=False,
        )
    elif pose_format == "sdf":
        supplier = Chem.SDMolSupplier(
            str(pose_path),
            sanitize=False,
            removeHs=False,
        )
        molecule = next(
            (mol for mol in supplier if mol is not None),
            None,
        )
    else:
        raise ValueError(
            f"Unsupported pose format: {pose_format}"
        )

    if molecule is None:
        raise ValueError(
            f"Could not load pose: {pose_path}"
        )

    if molecule.GetNumConformers() != 1:
        raise ValueError(
            "Frozen pose must contain exactly one conformer: "
            f"{pose_path}"
        )

    return molecule


def assign_ligand_pdb_metadata(molecule, ligand, first_serial):
    """Assign configured PDB residue metadata without changing coordinates."""

    molecule = Chem.Mol(
        molecule
    )

    for atom in molecule.GetAtoms():
        atom_name = atom_name_for_pdb(
            atom,
            atom.GetIdx() + 1,
        )
        residue_info = Chem.AtomPDBResidueInfo()
        residue_info.SetName(
            atom_name
        )
        residue_info.SetResidueName(
            ligand["hetid"]
        )
        residue_info.SetResidueNumber(
            int(ligand["position"])
        )
        residue_info.SetChainId(
            ligand["chain"]
        )
        residue_info.SetSerialNumber(
            first_serial + atom.GetIdx()
        )
        residue_info.SetIsHeteroAtom(
            True
        )
        atom.SetMonomerInfo(
            residue_info
        )

    return molecule


def atom_name_for_pdb(atom, atom_number):
    """Return a fixed-width atom name for RDKit PDB output."""

    if atom.HasProp("_TriposAtomName"):
        name = atom.GetProp(
            "_TriposAtomName"
        )
    else:
        name = f"{atom.GetSymbol()}{atom_number}"

    name = name[:4]
    return f"{name:<4}"


def pqr_to_pdb_lines(receptor_path):
    """Convert PQR atom records to PDB atom records as a format adapter."""

    pdb_lines = []
    atom_count = 0

    with receptor_path.open("r") as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                continue

            fields = line.split()
            if len(fields) < 10:
                raise ValueError(
                    f"Unexpected receptor PQR atom line: {line.rstrip()}"
                )

            record = fields[0]
            serial = int(fields[1])
            atom_name = fields[2]
            resname = fields[3]
            chain = fields[4]
            resid = int(fields[5])
            x = float(fields[6])
            y = float(fields[7])
            z = float(fields[8])
            element = element_from_atom_name(
                atom_name
            )

            pdb_lines.append(
                format_pdb_atom_line(
                    record,
                    serial,
                    atom_name,
                    resname,
                    chain,
                    resid,
                    x,
                    y,
                    z,
                    element,
                )
            )
            atom_count += 1

    if atom_count == 0:
        raise ValueError(
            f"No receptor atom records found: {receptor_path}"
        )

    return pdb_lines, atom_count


def format_pdb_atom_line(
    record,
    serial,
    atom_name,
    resname,
    chain,
    resid,
    x,
    y,
    z,
    element,
):
    """Format one PDB ATOM/HETATM line."""

    return (
        f"{record:<6}{serial:>5} "
        f"{atom_name:^4} "
        f"{resname:>3} {chain:1}"
        f"{resid:>4}    "
        f"{x:>8.3f}{y:>8.3f}{z:>8.3f}"
        f"{1.00:>6.2f}{0.00:>6.2f}          "
        f"{element:>2}\n"
    )


def element_from_atom_name(atom_name):
    """Infer a PDB element field from an atom name."""

    letters = "".join(
        character
        for character in atom_name
        if character.isalpha()
    )
    if not letters:
        return ""
    if letters[0].upper() == "H":
        return "H"
    return letters[0].upper()


def ligand_to_pdb_lines(molecule, ligand, first_serial):
    """Convert a frozen ligand pose to PDB lines preserving coordinates."""

    molecule = assign_ligand_pdb_metadata(
        molecule,
        ligand,
        first_serial,
    )
    pdb_block = Chem.MolToPDBBlock(
        molecule
    )

    return [
        line + "\n"
        for line in pdb_block.splitlines()
        if line.startswith(("HETATM", "CONECT"))
    ]


def write_complex_input(receptor_path, case, output_path):
    """Write a derived PLIP complex input without modifying source artifacts."""

    receptor_lines, receptor_atom_count = pqr_to_pdb_lines(
        receptor_path
    )
    molecule = load_pose(
        case["resolved_pose_path"],
        case["pose_format"],
    )
    ligand_lines = ligand_to_pdb_lines(
        molecule,
        case["ligand"],
        receptor_atom_count + 1,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        "".join(receptor_lines)
        + "TER\n"
        + "".join(ligand_lines)
        + "END\n"
    )


def run_plip(complex_path, output_dir, output_name, plip_settings):
    """Run PLIP once for one configured complex."""

    expected_xml = output_dir / f"{output_name}.xml"
    expected_txt = output_dir / f"{output_name}.txt"
    expected_protonated = output_dir / f"{complex_path.stem}_protonated.pdb"
    log_path = output_dir / f"{output_name}_plip_command.log"

    expected_outputs = [
        expected_xml,
        expected_txt,
        expected_protonated,
    ]

    existing_outputs = [
        path
        for path in expected_outputs
        if path.exists()
    ]
    if existing_outputs:
        if len(existing_outputs) != len(expected_outputs):
            raise FileExistsError(
                "Refusing to rerun PLIP over partial existing outputs: "
                f"{existing_outputs}"
            )

        return {
            "xml": expected_xml,
            "txt": expected_txt,
            "protonated_pdb": expected_protonated,
            "command_log": log_path,
        }

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    command = [
        "plip",
        "--file",
        str(complex_path),
        "--out",
        str(output_dir),
        "--name",
        output_name,
        "--maxthreads",
        str(plip_settings.get("maxthreads", 1)),
    ]

    if plip_settings.get("xml", False):
        command.append("--xml")
    if plip_settings.get("txt", False):
        command.append("--txt")
    if plip_settings.get("nofix", False):
        command.append("--nofix")

    completed = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )

    log_path.write_text(
        "COMMAND\n"
        + " ".join(command)
        + "\n\nSTDOUT\n"
        + completed.stdout
        + "\nSTDERR\n"
        + completed.stderr
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"PLIP failed for {complex_path}; see {log_path}"
        )

    for path in expected_outputs:
        if not path.exists():
            raise FileNotFoundError(
                f"Expected PLIP output was not created: {path}"
            )

    return {
        "xml": expected_xml,
        "txt": expected_txt,
        "protonated_pdb": expected_protonated,
        "command_log": log_path,
    }


def build_case_report(summary, case):
    """Build a compact ProLIF-vs-PLIP concordance record."""

    interactions_by_residue = {
        residue_id: []
        for residue_id in summary["observed_counts"]
    }
    for interaction in summary["observed_interactions"]:
        interactions_by_residue.setdefault(
            interaction["residue_id"],
            [],
        ).append(
            interaction
        )

    role_reproduction = {
        role["role_id"]: role
        for role in summary["configured_role_reproduction"]
    }
    role_concordance = {}

    for role_id, plip_role in role_reproduction.items():
        prolif_role = case["prolif"].get(
            "role_reproduction",
            {},
        ).get(role_id)

        if prolif_role is None:
            continue

        role_concordance[role_id] = {
            "prolif_reproduced": prolif_role["reproduced"],
            "plip_reproduced": plip_role["reproduced"],
            "concordant": (
                prolif_role["reproduced"]
                == plip_role["reproduced"]
            ),
        }

    prolif_reproduced = case["prolif"][
        "complete_pattern_reproduced"
    ]
    plip_reproduced = summary["witness_reproduced"]

    report = {
        "case_id": case["case_id"],
        "display_name": case.get("display_name"),
        "pose_path": case["pose_path"],
        "pose_record_id": case.get("pose_record_id"),
        "source_representative_path": case.get(
            "source_representative_path"
        ),
        "selected_ligand": summary["selected_ligand"],
        "plip_observed_interactions_by_residue": interactions_by_residue,
        "plip_role_reproduction": role_reproduction,
        "role_concordance": role_concordance,
        "plip_complete_pattern_reproduced": plip_reproduced,
        "prolif_observed_interactions_by_residue": case["prolif"][
            "observed_interactions_by_residue"
        ],
        "prolif_role_reproduction": case["prolif"].get(
            "role_reproduction",
            {},
        ),
        "prolif_complete_pattern_reproduced": prolif_reproduced,
        "complete_pattern_concordant": plip_reproduced == prolif_reproduced,
    }

    if "molecule_id" in case:
        report["molecule_id"] = case["molecule_id"]

    return report


def load_measurement_cases(measurement, base_path):
    """Load explicitly configured cases or derive a cohort from artifacts."""

    if "cohort" not in measurement:
        return measurement["cases"]

    cohort = measurement["cohort"]
    result_path = resolve_path(
        base_path,
        cohort["prolif_result_path"],
    )
    pose_sdf_path = resolve_path(
        base_path,
        cohort["pose_sdf_path"],
    )
    molecule_id_column = cohort["molecule_id_column"]

    rows = []
    with result_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(
                row
            )

    if not rows:
        raise ValueError(
            f"Configured cohort result file has no rows: {result_path}"
        )

    molecule_ids = [
        int(row[molecule_id_column])
        for row in rows
    ]
    molecules = load_sdf_molecules_by_id(
        pose_sdf_path,
        cohort["pose_molecule_id_property"],
        molecule_ids,
    )

    cases = []
    for row in rows:
        molecule_id = int(
            row[molecule_id_column]
        )
        case_id = f"{cohort['output_case_prefix']}_{molecule_id}"
        role_reproduction = {}
        observed_by_residue = {}

        for role in measurement["configured_roles"]:
            role_id = role["role_id"]
            role_columns = cohort["role_columns"][role_id]
            interactions = split_interaction_text(
                row[role_columns["observed_interactions_column"]]
            )
            role_reproduction[role_id] = {
                "reproduced": parse_bool(
                    row[role_columns["reproduced_column"]]
                ),
                "observed_interactions": interactions,
            }
            observed_by_residue[role["residue_id"]] = interactions

        cases.append(
            {
                "case_id": case_id,
                "display_name": case_id,
                "molecule_id": molecule_id,
                "pose_path": cohort["pose_sdf_path"],
                "pose_record_id": molecule_id,
                "pose_format": "rdkit_mol",
                "molecule": molecules[molecule_id],
                "ligand": cohort["ligand"],
                "prolif": {
                    "observed_interactions_by_residue": observed_by_residue,
                    "role_reproduction": role_reproduction,
                    "complete_pattern_reproduced": parse_bool(
                        row[cohort["complete_pattern_column"]]
                    ),
                },
            }
        )

    return cases


def load_sdf_molecules_by_id(sdf_path, molecule_id_property, molecule_ids):
    """Load selected SDF records by configured molecule ID property."""

    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        sanitize=False,
        removeHs=False,
    )
    wanted = set(
        molecule_ids
    )
    molecules = {}

    for molecule in supplier:
        if molecule is None:
            continue
        if not molecule.HasProp(molecule_id_property):
            continue

        molecule_id = int(
            molecule.GetProp(molecule_id_property)
        )
        if molecule_id in wanted:
            molecules[molecule_id] = Chem.Mol(
                molecule
            )

    missing = wanted - set(molecules)
    if missing:
        raise ValueError(
            "Configured cohort molecules missing from SDF: "
            f"{sorted(missing)}"
        )

    return molecules


def parse_bool(value):
    """Parse boolean values from retained artifacts."""

    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False

    raise ValueError(
        f"Cannot parse boolean value: {value!r}"
    )


def split_interaction_text(value):
    """Split semicolon-delimited retained interaction text."""

    if value is None or value == "":
        return []

    return [
        item
        for item in value.split(";")
        if item
    ]


def summarize_role_concordance(case_reports):
    """Summarize role-level concordance for all roles present."""

    role_ids = sorted(
        {
            role_id
            for report in case_reports
            for role_id in report["role_concordance"]
        }
    )
    summaries = {}

    for role_id in role_ids:
        role_reports = [
            report
            for report in case_reports
            if role_id in report["role_concordance"]
        ]
        discordant = [
            report
            for report in role_reports
            if not report["role_concordance"][role_id]["concordant"]
        ]
        concordant_count = len(role_reports) - len(discordant)
        summaries[role_id] = {
            "case_count": len(role_reports),
            "concordant_count": concordant_count,
            "concordance_fraction": (
                concordant_count / len(role_reports)
                if role_reports
                else None
            ),
            "discordant_ids": [
                report.get("molecule_id", report["case_id"])
                for report in discordant
            ],
        }

    return summaries


def complete_pattern_table(case_reports):
    """Build a complete-pattern ProLIF-vs-PLIP 2x2 table."""

    table = {
        "prolif_true_plip_true": 0,
        "prolif_true_plip_false": 0,
        "prolif_false_plip_true": 0,
        "prolif_false_plip_false": 0,
    }

    for report in case_reports:
        prolif = str(
            report["prolif_complete_pattern_reproduced"]
        ).lower()
        plip = str(
            report["plip_complete_pattern_reproduced"]
        ).lower()
        table[f"prolif_{prolif}_plip_{plip}"] += 1

    return table


def complete_pattern_discordant_ids(case_reports):
    """Return case IDs with discordant complete-pattern calls."""

    return [
        report.get("molecule_id", report["case_id"])
        for report in case_reports
        if not report["complete_pattern_concordant"]
    ]


def write_construction_note(output_root, measurement, case_reports):
    """Document the derived PLIP input construction."""

    lines = [
        "# PLIP Witness Concordance Derived Inputs\n",
        "\n",
        f"Measurement: `{measurement['measurement_id']}`\n",
        "\n",
        "The frozen receptor and frozen pose artifacts were not modified. ",
        "Each PLIP complex PDB is a derived input containing a PDB-format ",
        "adapter view of the configured receptor plus one configured ligand ",
        "pose. Ligand coordinates are read from the configured frozen pose ",
        "without conformer generation, repair, minimization, or coordinate ",
        "optimization. PDB output is limited to PDB coordinate precision.\n",
        "\n",
    ]

    for report in case_reports:
        lines.extend(
            [
                f"## {report['case_id']}\n",
                "\n",
                f"Pose artifact: `{report['pose_path']}`\n",
                "\n",
                "PLIP selected ligand: ",
                json.dumps(
                    report["selected_ligand"],
                    sort_keys=True,
                ),
                "\n\n",
            ]
        )

    (output_root / "DERIVED_INPUTS.md").write_text(
        "".join(lines)
    )


def hash_file(path):
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(
                block
            )

    return digest.hexdigest()


def write_hashes(output_root):
    """Write SHA-256 hashes for generated concordance artifacts."""

    paths = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file()
        and path.name != "SHA256SUMS.txt"
    )

    lines = []
    for path in paths:
        lines.append(
            f"{hash_file(path)}  {path.relative_to(output_root)}\n"
        )

    (output_root / "SHA256SUMS.txt").write_text(
        "".join(lines)
    )


def run_measurement(config, measurement, base_path):
    """Construct inputs, run PLIP, summarize, and compare to ProLIF."""

    measurement = {
        **measurement,
        "configured_roles": config["configured_roles"],
    }

    output_root = resolve_path(
        base_path,
        measurement["output_root"],
    )
    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    receptor_path = resolve_path(
        base_path,
        measurement["receptor"]["path"],
    )
    case_reports = []

    for case in load_measurement_cases(
        measurement,
        base_path,
    ):
        if case["pose_format"] == "rdkit_mol":
            resolved_pose_path = case["molecule"]
        else:
            resolved_pose_path = resolve_path(
                base_path,
                case["pose_path"],
            )

        case = {
            **case,
            "resolved_pose_path": resolved_pose_path,
        }
        case_dir = output_root / case["case_id"]
        input_path = case_dir / "input" / "plip_complex.pdb"
        plip_dir = case_dir / "plip"

        if not input_path.exists():
            write_complex_input(
                receptor_path,
                case,
                input_path,
            )
        outputs = run_plip(
            input_path,
            plip_dir,
            case["case_id"],
            measurement["plip_settings"],
        )
        summary = summarize_plip_xml_for_case(
            outputs["xml"],
            config,
            case,
        )
        case_report = build_case_report(
            summary,
            case,
        )
        case_report["derived_input_path"] = str(input_path)
        case_report["plip_outputs"] = {}
        for key, value in outputs.items():
            if isinstance(value, Path):
                case_report["plip_outputs"][key] = str(value)
            else:
                case_report["plip_outputs"][key] = value

        summary_path = case_dir / "plip_summary.json"
        concordance_path = case_dir / "concordance.json"
        summary_path.write_text(
            json.dumps(
                summary,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        concordance_path.write_text(
            json.dumps(
                case_report,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        case_report["summary_path"] = str(summary_path)
        case_report["concordance_path"] = str(concordance_path)
        case_reports.append(
            case_report
        )

    concordance_count = sum(
        report["complete_pattern_concordant"]
        for report in case_reports
    )
    measurement_summary = {
        "measurement_id": measurement["measurement_id"],
        "witness_id": config["witness_id"],
        "target_id": config["target_id"],
        "stage5_verdict_instrument": config.get(
            "stage5_verdict_instrument"
        ),
        "instrument_role": config.get("instrument_role"),
        "prolif_result_path": measurement.get(
            "prolif_result_path",
            measurement.get("cohort", {}).get("prolif_result_path"),
        ),
        "case_count": len(case_reports),
        "complete_pattern_concordant_count": concordance_count,
        "complete_pattern_concordance_fraction": (
            concordance_count / len(case_reports)
            if case_reports
            else None
        ),
        "role_concordance": summarize_role_concordance(
            case_reports
        ),
        "complete_pattern_2x2": complete_pattern_table(
            case_reports
        ),
        "complete_pattern_discordant_ids": complete_pattern_discordant_ids(
            case_reports
        ),
        "case_reports": case_reports,
    }

    (output_root / "concordance_summary.json").write_text(
        json.dumps(
            measurement_summary,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    write_construction_note(
        output_root,
        measurement,
        case_reports,
    )
    write_hashes(
        output_root
    )

    return measurement_summary


def main():
    """Run a configured PLIP witness concordance measurement."""

    args = parse_args()
    config = load_plip_witness_config(
        args.config
    )
    measurement = select_measurement(
        config,
        args.measurement_id,
    )
    summary = run_measurement(
        config,
        measurement,
        args.base_path,
    )
    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
