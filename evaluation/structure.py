import csv
from pathlib import Path
from turtle import st

from rdkit import Chem
from posebusters import PoseBusters
import pandas as pd
import numpy as np
from Bio.PDB.Polypeptide import is_aa
from Bio.PDB import PDBIO, PDBParser, Select


def load_stage3_molecule_ids(properties_csv_path):
    """Load molecule IDs that passed the Stage 2 Rule-of-Five gate."""

    properties_csv_path = Path(properties_csv_path)

    if not properties_csv_path.exists():
        raise FileNotFoundError(
            f"Stage 2 results file not found: {properties_csv_path}")

    stage3_ids = []

    with properties_csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row["ro5_passes"] == "True":
                stage3_ids.append(int(row["molecule_id"]))

    return stage3_ids


def write_stage3_input_sdf(sdf_path, stage3_ids, output_path):
    """Write Stage 3-eligible molecules while preserving original coordinates."""

    sdf_path = Path(sdf_path)
    output_path = Path(output_path)

    if not sdf_path.exists():
        raise FileNotFoundError(f"SDF file not found: {sdf_path}")
    # Create the output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Read the original SDF file and filter molecules based on stage3_ids
    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        sanitize=False,
        removeHs=False,
    )

    molecules = list(supplier)

    writer = Chem.SDWriter(str(output_path))

    for molecule_id in stage3_ids:
        mol = molecules[molecule_id]

        # Preserve provenance in the Stage 3 input artifact.

        mol.SetProp("molecule_id", str(molecule_id))

        writer.write(mol)

    writer.close()
    print(f"Stage 3 input molecules written: {len(stage3_ids)}")
    print(f"Stage 3 input SDF: {output_path}")


def evaluate_structure(stage3_sdf_path):
    """Run Stage 3A PoseBusters structural evaluation."""

    stage3_sdf_path = Path(stage3_sdf_path)

    if not stage3_sdf_path.exists():
        raise FileNotFoundError(
            f"Stage 3 input SDF file not found: {stage3_sdf_path}")

    # Run the full ligand intrinsic PoseBusters suite.

    buster = PoseBusters(config="mol")

    results = buster.bust(
        str(stage3_sdf_path),
        full_report=True,
    )
    return results


def apply_structure_gate(results):
    """Apply the predeclared D003 3A attrition gate"""

    gate_columns = [
        "bond_lengths",
        "bond_angles",
        "internal_steric_clash",
    ]

    gated_results = results.copy()

    gated_results["stage3a_passes"] = gated_results[
        gate_columns
    ].all(axis=1)

    return gated_results


def attach_molecule_ids(results, stage3_ids):
    """Attach original molecule IDs to PoseBusters results."""

    if len(results) != len(stage3_ids):
        raise ValueError(
            "PoseBusters result count do not match Stage 3 molecule count."
        )

    results = results.copy()
    results.insert(0, "molecule_id", stage3_ids)

    return results


def save_structure_results(results, output_path):
    """Save the full Stage 3A PoseBusters report to CSV."""

    output_path = Path(output_path)

   # Create the output directory if needed.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(output_path, index=False)

    print(f"Stage 3 PoseBusters results saved to: {output_path}")


def select_pocket_residues(
        pdb_path,
        reference_ligand_path,
        distance_cutoff=8.0):
    """Select standard amino-acid residues near a reference ligand."""

    pdb_path = Path(pdb_path)
    reference_ligand_path = Path(reference_ligand_path)

    if not pdb_path.exists():
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    if not reference_ligand_path.exists():
        raise FileNotFoundError(
            f"Reference ligand file not found: {reference_ligand_path}")

    # Load the protein structure
    structure = PDBParser(QUIET=True).get_structure("", str(pdb_path))[0]

    # Load the reference ligand and preserve its deposited coordinates.
    ligand = Chem.SDMolSupplier(
        str(reference_ligand_path),
        sanitize=False,
        removeHs=False,
    )[0]

    ligand_coords = ligand.GetConformer().GetPositions()

    pocket_residues = []

    for residue in structure.get_residues():

        # only standard amino-acid residues belong to the pocket.
        if not is_aa(residue.get_resname(), standard=True):
            continue

        residue_coords = np.array(
            [atom.get_coord() for atom in residue.get_atoms()]
        )

        # Compute every residue-atom to ligand-atom distance.
        distances = np.linalg.norm(
            residue_coords[:, None, :] - ligand_coords[None, :, :],
            axis=2,
        )

        if distances.min() < distance_cutoff:
            pocket_residues.append(residue)

    return pocket_residues


class PocketResidueSelect(Select):
    """Select only residues belonging to the defined evaluation pocket."""

    def __init__(self, pocket_residues):
        self.pocket_residue_ids = {
            (
                residue.get_parent().id,
                residue.id,
            )
            for residue in pocket_residues
        }

    def accept_residue(self, residue):
        residue_id = (
            residue.get_parent().id,
            residue.id,
        )
        return residue_id in self.pocket_residue_ids


def write_prepared_pocket(
        pdb_path,
        reference_ligand_path,
        output_path,
        distance_cutoff=8.0):
    """Write the explicit Stage 3B pocket artifact."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    structure = PDBParser(QUIET=True).get_structure(
        "",
        str(pdb_path),
    )

    pocket_residues = select_pocket_residues(
        pdb_path,
        reference_ligand_path,
        distance_cutoff=distance_cutoff,
    )

    io = PDBIO()
    io.set_structure(structure)

    io.save(
        str(output_path),
        PocketResidueSelect(pocket_residues),
    )

    print(f"Pocket residues: {len(pocket_residues)}")
    print(f"Prepared pocket saved to: {output_path}")
# begin stage 3b


def evaluate_structure_3b(stage3_sdf_path, prepared_pocket_path):
    """Run Stage 3B pocket-relative PoseBusters evaluation."""

    stage3_sdf_path = Path(stage3_sdf_path)
    prepared_pocket_path = Path(prepared_pocket_path)

    if not stage3_sdf_path.exists():
        raise FileNotFoundError(
            f"Stage 3 input SDF not found: {stage3_sdf_path}"
        )

    if not prepared_pocket_path.exists():
        raise FileNotFoundError(
            f"Prepared pocket not found: {prepared_pocket_path}"
        )
    buster = PoseBusters(config="dock")

    results = buster.bust(
        mol_pred=str(stage3_sdf_path),
        mol_cond=str(prepared_pocket_path),
        full_report=True,
    )

    buster = PoseBusters(config="dock")

    results = buster.bust(
        mol_pred=str(stage3_sdf_path),
        mol_cond=str(prepared_pocket_path),
        full_report=True,
    )

    return results


def apply_structure_3b_gate(results):
    """Apply the predeclared D003 Stage 3B attrition gate."""

    gated_results = results.copy()

    gated_results["stage3b_passes"] = gated_results[
        "minimum_distance_to_protein"
    ]

    return gated_results


def combine_structure_results(stage3a_csv_path, stage3b_csv_path):
    """Combine Stage 3A and Stage 3B gate outcomes by original molecule ID."""

    stage3a = pd.read_csv(stage3a_csv_path)
    stage3b = pd.read_csv(stage3b_csv_path)

    combined = stage3a[
        [
            "molecule_id",
            "bond_lengths",
            "bond_angles",
            "internal_steric_clash",
            "stage3a_passes",
        ]
    ].merge(
        stage3b[
            [
                "molecule_id",
                "minimum_distance_to_protein",
                "stage3b_passes",
            ]
        ],
        on="molecule_id",
        how="inner",
        validate="one_to_one",
    )

    combined["stage3_passes"] = (
        combined["stage3a_passes"]
        & combined["stage3b_passes"]
    )

    return combined


def save_combined_structure_results(results, output_path):
    """Save the combined Stage 3 gate results."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(output_path, index=False)

    print(f"Combined Stage 3 results saved to: {output_path}")
