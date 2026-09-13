"""D017 experimentally ligand-defined homolog-pocket helpers."""

from pathlib import Path

from evaluation.d017_construct_audit import (
    _read_loop,
    parse_coordinate_atoms,
    sha256_file,
)
from evaluation.pocket_models import ResidueID
from math import dist
from typing import Any
import numpy as np


def select_ligand_instance(
    *,
    structure_path: Path,
    component: str,
    author_chain: str,
    author_residue_number: str,
) -> tuple[dict[str, str], ...]:
    """Select one deposited ligand instance by frozen author identifiers."""

    atoms = tuple(
        _read_loop(
            structure_path,
            "_atom_site.",
        )
    )

    ligand_atoms = tuple(
        atom
        for atom in atoms
        if (
            atom["_atom_site.group_PDB"] == "HETATM"
            and atom["_atom_site.auth_comp_id"] == component
            and atom["_atom_site.auth_asym_id"] == author_chain
            and atom["_atom_site.auth_seq_id"] == author_residue_number
        )
    )

    if not ligand_atoms:
        raise ValueError(
            "No deposited ligand atoms matched the configured ligand instance"
        )

    return ligand_atoms


def select_heavy_atoms(
    atoms: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    """Return deposited non-hydrogen atoms."""

    heavy_atoms = tuple(
        atom
        for atom in atoms
        if atom["_atom_site.type_symbol"].strip().upper() not in {"H", "D"}
    )

    if not heavy_atoms:
        raise ValueError("No heavy atoms remain after filtering")

    return heavy_atoms


def select_receptor_heavy_atoms(
    *,
    structure_path: Path,
    author_chain: str,
) -> tuple[dict[str, str], ...]:
    """Return deposited heavy atoms from one receptor author chain."""

    receptor_atoms = parse_coordinate_atoms(
        structure_path,
        author_chain,
    )

    return select_heavy_atoms(receptor_atoms)


def atom_distance(
    atom_a: dict[str, str],
    atom_b: dict[str, str],
) -> float:
    """Return the Euclidean distance in Å between two deposited atoms."""

    coordinates_a = (
        float(atom_a["_atom_site.Cartn_x"]),
        float(atom_a["_atom_site.Cartn_y"]),
        float(atom_a["_atom_site.Cartn_z"]),
    )

    coordinates_b = (
        float(atom_b["_atom_site.Cartn_x"]),
        float(atom_b["_atom_site.Cartn_y"]),
        float(atom_b["_atom_site.Cartn_z"]),
    )

    return dist(coordinates_a, coordinates_b)


def identify_pocket_residues(
    *,
    receptor_heavy_atoms: tuple[dict[str, str], ...],
    ligand_heavy_atoms: tuple[dict[str, str], ...],
    cutoff: float = 4.5,
) -> tuple[ResidueID, ...]:
    """Return receptor residues with any heavy atom within cutoff of the ligand."""

    pocket_residues: set[ResidueID] = set()

    for receptor_atom in receptor_heavy_atoms:
        residue = ResidueID(
            chain=receptor_atom["_atom_site.auth_asym_id"],
            number=receptor_atom["_atom_site.auth_seq_id"],
            insertion_code=(
                ""
                if receptor_atom["_atom_site.pdbx_PDB_ins_code"] in {".", "?"}
                else receptor_atom["_atom_site.pdbx_PDB_ins_code"]
            ),
            name=receptor_atom["_atom_site.auth_comp_id"],
        )

        for ligand_atom in ligand_heavy_atoms:
            if atom_distance(receptor_atom, ligand_atom) <= cutoff:
                pocket_residues.add(residue)
                break

    ordered_pocket_residues = tuple(
        sorted(
            pocket_residues,
            key=lambda residue: int(residue.number),
        )
    )

    return ordered_pocket_residues


def collect_pocket_distance_evidence(
    *,
    receptor_heavy_atoms: tuple[dict[str, str], ...],
    ligand_heavy_atoms: tuple[dict[str, str], ...],
    pocket_residues: tuple[ResidueID, ...],
    cutoff: float = 4.5,
) -> dict[ResidueID, dict[str, object]]:
    """Retain the minimum-distance atom pair for each pocket residue."""

    pocket_set = set(pocket_residues)
    evidence: dict[ResidueID, dict[str, object]] = {}

    for receptor_atom in receptor_heavy_atoms:
        residue = ResidueID(
            chain=receptor_atom["_atom_site.auth_asym_id"],
            number=receptor_atom["_atom_site.auth_seq_id"],
            insertion_code=(
                ""
                if receptor_atom["_atom_site.pdbx_PDB_ins_code"] in {".", "?"}
                else receptor_atom["_atom_site.pdbx_PDB_ins_code"]
            ),
            name=receptor_atom["_atom_site.auth_comp_id"],
        )

        if residue not in pocket_set:
            continue

        for ligand_atom in ligand_heavy_atoms:
            distance = atom_distance(
                receptor_atom,
                ligand_atom,
            )

            if distance > cutoff:
                continue

            current = evidence.get(residue)

            if (
                current is None
                or distance < current["distance_angstrom"]
            ):
                evidence[residue] = {
                    "distance_angstrom": distance,
                    "receptor_atom_site_id": receptor_atom["_atom_site.id"],
                    "receptor_atom": receptor_atom["_atom_site.auth_atom_id"],
                    "ligand_atom_site_id": ligand_atom["_atom_site.id"],
                    "ligand_atom": ligand_atom["_atom_site.auth_atom_id"],
                }

    missing = pocket_set - set(evidence)

    if missing:
        raise ValueError(
            "Pocket residues lack qualifying atom-distance evidence: "
            f"{sorted(missing, key=lambda residue: int(residue.number))}"
        )

    return evidence


def map_pocket_residues(
    *,
    pocket_residues: tuple[ResidueID, ...],
    correspondence: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    """Map homolog-pocket residues through the frozen US-align correspondence."""

    correspondence_by_homolog: dict[ResidueID, dict[str, object]] = {}

    for column in correspondence["columns"]:
        homolog = column["homolog_residue"]

        if homolog is None:
            continue

        homolog_residue = ResidueID(
            chain=homolog["chain"],
            number=homolog["number"],
            insertion_code=homolog["insertion_code"],
            name=homolog["name"],
        )

        if homolog_residue in correspondence_by_homolog:
            raise ValueError(
                f"Homolog residue occurs more than once in correspondence: "
                f"{homolog_residue}"
            )

        correspondence_by_homolog[homolog_residue] = column

    mapped_pocket = []

    for homolog_residue in pocket_residues:
        column = correspondence_by_homolog.get(homolog_residue)

        if column is None:
            raise ValueError(
                f"Pocket residue is absent from homolog correspondence: "
                f"{homolog_residue}"
            )

        target = column["target_residue"]

        target_residue = None

        if target is not None:
            target_residue = ResidueID(
                chain=target["chain"],
                number=target["number"],
                insertion_code=target["insertion_code"],
                name=target["name"],
            )

        mapped_pocket.append(
            {
                "homolog_residue": homolog_residue,
                "target_residue": target_residue,
                "alignment_column": column["alignment_column"],
                "identical": column["identical"],
            }
        )

    return tuple(mapped_pocket)


def calculate_mapping_coverage(
    mapped_pocket: tuple[dict[str, object], ...],
) -> float:
    """Return the fraction of homolog-pocket residues mapped to target residues."""

    total_residues = len(mapped_pocket)

    if total_residues == 0:
        raise ValueError(
            "Cannot calculate mapping coverage for an empty homolog pocket"
        )

    mapped_residues = sum(
        record["target_residue"] is not None
        for record in mapped_pocket
    )

    mapping_coverage = mapped_residues / total_residues

    return mapping_coverage


def calculate_pocket_sequence_identity(
    mapped_pocket: tuple[dict[str, object], ...],
) -> float:
    """Return sequence identity among mapped homolog-pocket residues."""

    mapped_records = tuple(
        record
        for record in mapped_pocket
        if record["target_residue"] is not None
    )

    if not mapped_records:
        raise ValueError(
            "Cannot calculate pocket sequence identity without mapped residues"
        )

    identical_residues = sum(
        record["identical"]
        for record in mapped_records
    )

    pocket_sequence_identity = (
        identical_residues / len(mapped_records)
    )

    return pocket_sequence_identity


def calculate_pocket_rmsd(
    *,
    mapped_pocket: tuple[dict[str, object], ...],
    target_atoms_by_residue: dict[ResidueID, tuple[tuple[float, float, float], ...]],
    homolog_atoms_by_residue: dict[ResidueID, tuple[tuple[float, float, float], ...]],
) -> float:
    """Calculate optimal local-superposition RMSD for mapped pocket Cα pairs."""

    mapped_pairs = tuple(
        record
        for record in mapped_pocket
        if record["target_residue"] is not None
    )

    if not mapped_pairs:
        raise ValueError(
            "Cannot calculate pocket RMSD without mapped pocket residues"
        )

    target_coordinates = []
    homolog_coordinates = []

    for record in mapped_pairs:
        target_residue = record["target_residue"]
        homolog_residue = record["homolog_residue"]

        target_ca = target_atoms_by_residue[target_residue][0]
        homolog_ca = homolog_atoms_by_residue[homolog_residue][0]

        target_coordinates.append(target_ca)
        homolog_coordinates.append(homolog_ca)

    if len(target_coordinates) < 3:
        raise ValueError(
            "At least three mapped C-alpha pairs are required for local RMSD"
        )

    return optimal_superposition_rmsd(
        reference_coordinates=target_coordinates,
        mobile_coordinates=homolog_coordinates,
    )


def get_ca_coordinate(
    *,
    atoms: tuple[dict[str, str], ...],
    residue: ResidueID,
) -> tuple[float, float, float]:
    """Return the deposited C-alpha coordinate for one residue."""

    matches = tuple(
        atom
        for atom in atoms
        if (
            atom["_atom_site.group_PDB"] == "ATOM"
            and atom["_atom_site.auth_asym_id"] == residue.chain
            and atom["_atom_site.auth_seq_id"] == residue.number
            and (
                ""
                if atom["_atom_site.pdbx_PDB_ins_code"] in {".", "?"}
                else atom["_atom_site.pdbx_PDB_ins_code"]
            )
            == residue.insertion_code
            and atom["_atom_site.auth_comp_id"] == residue.name
            and atom["_atom_site.auth_atom_id"] == "CA"
        )
    )

    if len(matches) == 0:
        raise ValueError(
            f"No C-alpha atom found for residue: {residue}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Multiple C-alpha atoms found for residue: {residue}"
        )

    atom = matches[0]

    return (
        float(atom["_atom_site.Cartn_x"]),
        float(atom["_atom_site.Cartn_y"]),
        float(atom["_atom_site.Cartn_z"]),
    )


def optimal_superposition(
    *,
    reference_coordinates: tuple[tuple[float, float, float], ...],
    mobile_coordinates: tuple[tuple[float, float, float], ...],
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[float, float, float], ...],
    tuple[float, float, float],
    float,
]:
    """Optimally superpose mobile coordinates onto reference coordinates."""

    if len(reference_coordinates) != len(mobile_coordinates):
        raise ValueError(
            "Reference and mobile coordinate sets must have equal length"
        )

    if len(reference_coordinates) < 3:
        raise ValueError(
            "At least three coordinate pairs are required for "
            "rigid-body superposition"
        )

    reference = np.asarray(reference_coordinates, dtype=float)
    mobile = np.asarray(mobile_coordinates, dtype=float)

    reference_centroid = reference.mean(axis=0)
    mobile_centroid = mobile.mean(axis=0)

    reference_centered = reference - reference_centroid
    mobile_centered = mobile - mobile_centroid

    covariance = mobile_centered.T @ reference_centered

    u_matrix, _, v_transpose = np.linalg.svd(covariance)

    rotation = u_matrix @ v_transpose

    if np.linalg.det(rotation) < 0.0:
        v_transpose[-1, :] *= -1.0
        rotation = u_matrix @ v_transpose

    translation = reference_centroid - mobile_centroid @ rotation

    transformed_mobile = mobile @ rotation + translation

    transformed_coordinates = tuple(
        tuple(float(value) for value in coordinate)
        for coordinate in transformed_mobile
    )

    rotation_matrix = tuple(
        tuple(float(value) for value in row)
        for row in rotation
    )

    translation_vector = tuple(
        float(value)
        for value in translation
    )

    rmsd = calculate_rmsd(
        reference_coordinates=reference_coordinates,
        transformed_coordinates=transformed_coordinates,
    )

    return (
        transformed_coordinates,
        rotation_matrix,
        translation_vector,
        rmsd,
    )


def calculate_rmsd(
    *,
    reference_coordinates: tuple[tuple[float, float, float], ...],
    transformed_coordinates: tuple[tuple[float, float, float], ...],
) -> float:
    """Calculate RMSD between corresponding coordinates."""

    if len(reference_coordinates) != len(transformed_coordinates):
        raise ValueError(
            "Reference and transformed coordinate sets must have equal length"
        )

    if not reference_coordinates:
        raise ValueError(
            "Cannot calculate RMSD from an empty coordinate set"
        )

    squared_distances = []

    for reference, transformed in zip(
        reference_coordinates,
        transformed_coordinates,
    ):
        squared_distance = sum(
            (reference[index] - transformed[index]) ** 2
            for index in range(3)
        )
        squared_distances.append(squared_distance)

    mean_squared_distance = (
        sum(squared_distances)
        / len(squared_distances)
    )

    rmsd = mean_squared_distance ** 0.5

    return rmsd


def calculate_pocket_rmsd(
    *,
    mapped_pocket: tuple[dict[str, object], ...],
    target_atoms: tuple[dict[str, str], ...],
    homolog_atoms: tuple[dict[str, str], ...],
) -> dict[str, object]:
    """Calculate the optimal local-superposition RMSD for mapped pocket C-alpha pairs."""

    mapped_records = tuple(
        record
        for record in mapped_pocket
        if record["target_residue"] is not None
    )

    if len(mapped_records) < 3:
        raise ValueError(
            "At least three mapped pocket residues are required "
            "for local C-alpha RMSD"
        )

    target_coordinates = []
    homolog_coordinates = []

    for record in mapped_records:
        target_residue = record["target_residue"]
        homolog_residue = record["homolog_residue"]

        target_coordinates.append(
            get_ca_coordinate(
                atoms=target_atoms,
                residue=target_residue,
            )
        )

        homolog_coordinates.append(
            get_ca_coordinate(
                atoms=homolog_atoms,
                residue=homolog_residue,
            )
        )

    (
        transformed_homolog_coordinates,
        rotation,
        translation,
        rmsd,
    ) = optimal_superposition(
        reference_coordinates=tuple(target_coordinates),
        mobile_coordinates=tuple(homolog_coordinates),
    )
    result = {
        "mapped_pair_count": len(mapped_records),
        "target_ca_coordinates": tuple(target_coordinates),
        "homolog_ca_coordinates": tuple(homolog_coordinates),
        "transformed_homolog_ca_coordinates": transformed_homolog_coordinates,
        "rotation": rotation,
        "translation": translation,
        "pocket_superposition_rmsd": rmsd,
    }

    return result


def build_pocket_measurement_result(
    *,
    pocket_residues: tuple[ResidueID, ...],
    pocket_evidence: dict[ResidueID, dict[str, object]],
    mapped_pocket: tuple[dict[str, object], ...],
    mapping_coverage: float,
    pocket_sequence_identity: float,
    pocket_rmsd_result: dict[str, object],
) -> dict[str, object]:
    """Assemble the complete quantitative D017 homolog-pocket result."""

    mapped_residue_count = sum(
        record["target_residue"] is not None
        for record in mapped_pocket
    )

    unmapped_residue_count = (
        len(pocket_residues) - mapped_residue_count
    )

    result = {
        "total_homolog_pocket_residues": len(pocket_residues),
        "mapped_homolog_pocket_residues": mapped_residue_count,
        "unmapped_homolog_pocket_residues": unmapped_residue_count,
        "unmapped_pocket_residues": tuple(
            record["homolog_residue"]
            for record in mapped_pocket
            if record["target_residue"] is None
        ),
        "mapping_coverage": mapping_coverage,
        "identical_mapped_residue_pairs": sum(
            record["identical"]
            for record in mapped_pocket
            if record["target_residue"] is not None
        ),
        "pocket_sequence_identity": pocket_sequence_identity,
        "pocket_superposition_rmsd": (
            pocket_rmsd_result["pocket_superposition_rmsd"]
        ),
        "pocket_residues": pocket_residues,
        "pocket_distance_evidence": pocket_evidence,
        "mapped_pocket_residues": mapped_pocket,
        "local_superposition": {
            "rotation": pocket_rmsd_result["rotation"],
            "translation": pocket_rmsd_result["translation"],
            "target_ca_coordinates": (
                pocket_rmsd_result["target_ca_coordinates"]
            ),
            "homolog_ca_coordinates": (
                pocket_rmsd_result["homolog_ca_coordinates"]
            ),
            "transformed_homolog_ca_coordinates": (
                pocket_rmsd_result["transformed_homolog_ca_coordinates"]
            ),
        },
    }

    return result


def build_pocket_measurement_artifact(
    *,
    decision_id: str,
    calibration_row_id: str,
    target_structure_path: Path,
    target_pdb_id: str,
    target_chain: str,
    homolog_structure_path: Path,
    homolog_pdb_id: str,
    homolog_chain: str,
    homolog_ligand_component: str,
    homolog_ligand_instance: str,
    usalign_stdout_path: Path,
    usalign_config_path: Path,
    measurement_result: dict[str, object],
) -> dict[str, object]:
    """Assemble provenance and quantitative D017 result for JSON serialization."""

    artifact = {
        "schema_version": 1,
        "decision_id": decision_id,
        "calibration_row_id": calibration_row_id,
        "target": {
            "pdb_id": target_pdb_id,
            "chain": target_chain,
            "structure_path": str(target_structure_path),
            "structure_sha256": sha256_file(target_structure_path),
        },
        "homolog": {
            "pdb_id": homolog_pdb_id,
            "chain": homolog_chain,
            "structure_path": str(homolog_structure_path),
            "structure_sha256": sha256_file(homolog_structure_path),
        },
        "ligand": {
            "component": homolog_ligand_component,
            "instance": homolog_ligand_instance,
        },
        "pocket_definition": {
            "distance_cutoff_angstrom": 4.5,
            "atom_type": "heavy_atoms",
            "source": "experimentally_bound_homolog_ligand",
        },
        "usalign": {
            "stdout_path": str(usalign_stdout_path),
            "stdout_sha256": sha256_file(usalign_stdout_path),
            "config_path": str(usalign_config_path),
            "config_sha256": sha256_file(usalign_config_path),
        },
        "measurement": _json_ready(measurement_result),
    }

    return artifact


def _json_ready(value: object) -> object:
    """Convert typed D017 result objects into JSON-serializable values."""

    if isinstance(value, ResidueID):
        return {
            "chain": value.chain,
            "number": value.number,
            "insertion_code": value.insertion_code,
            "name": value.name,
        }

    if isinstance(value, dict):
        if all(isinstance(key, str) for key in value):
            return {
                key: _json_ready(item)
                for key, item in value.items()
            }

        return [
            {
                "key": _json_ready(key),
                "value": _json_ready(item),
            }
            for key, item in value.items()
        ]

    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]

    if isinstance(value, list):
        return [_json_ready(item) for item in value]

    return value
