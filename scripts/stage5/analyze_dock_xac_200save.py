from dataclasses import dataclass
from pathlib import Path
import gzip
import re
from rdkit import Chem
from rdkit.Chem import rdFMCS
from math import sqrt
import numpy as np
from rdkit.Chem import GetPeriodicTable
from scripts.stage5.test_native_reader_controls import load_protein


ROOT = Path(__file__).resolve().parents[2]
DOCK_XAC_200SAVE_ARCHIVE = (
    ROOT
    / "references/stage5/dock385/3REY"
    / "xac_adversarial_A1_matchgoal5000"
    / "measurement_200save/test.mol2.gz"
)

EXPECTED_POSES = 200
EXPECTED_HEAVY_ATOMS = 31
EXPECTED_CONFORMERS = 1

NATIVE_XAC_REFERENCE = (
    ROOT
    / "references/stage5/native_complexes/3REY"
    / "3REY_XAC_native_pH7.4_restored.sdf"
)

NATIVE_RECEPTOR_PQR = (
    ROOT
    / "references/stage5/native_complexes/3REY"
    / "3REY_receptor_pH7.4_restored.pqr"
)


@dataclass(frozen=True)
class DockPoseRecord:
    rank: int
    matchnum: int
    total_energy: float
    mol2_text: str


def parse_dock_pose_archive(
    path: Path,
    expected_pose_count: int | None = None,
) -> list[DockPoseRecord]:
    """Parse a DOCK MOL2 archive into score-ranked pose records."""
    with gzip.open(path, "rt") as handle:
        text = handle.read()

    blocks = re.split(
        r"(?=^##########\s+Name:)",
        text,
        flags=re.MULTILINE,
    )

    records: list[DockPoseRecord] = []

    for block in blocks:
        if not block.strip():
            continue

        rank_match = re.search(
            r"^##########\s+Rank:\s+(\d+)\s*$",
            block,
            flags=re.MULTILINE,
        )
        matchnum_match = re.search(
            r"^##########\s+Matchnum:\s+(\d+)\s*$",
            block,
            flags=re.MULTILINE,
        )
        energy_match = re.search(
            r"^##########\s+Total Energy:\s+([-+0-9.eE]+)\s*$",
            block,
            flags=re.MULTILINE,
        )

        if not (
            rank_match
            and matchnum_match
            and energy_match
        ):
            raise ValueError(
                "Pose block is missing Rank, Matchnum, "
                "or Total Energy."
            )

        records.append(
            DockPoseRecord(
                rank=int(rank_match.group(1)),
                matchnum=int(matchnum_match.group(1)),
                total_energy=float(energy_match.group(1)),
                mol2_text=block,
            )
        )

    records.sort(key=lambda record: record.rank)

    expected_ranks = list(range(1, len(records) + 1))
    observed_ranks = [record.rank for record in records]

    if observed_ranks != expected_ranks:
        raise ValueError(
            "DOCK ranks are not exactly 1..N: "
            f"{observed_ranks}"
        )

    if (
        expected_pose_count is not None
        and len(records) != expected_pose_count
    ):
        raise ValueError(
            f"Expected {expected_pose_count} DOCK poses, "
            f"found {len(records)}."
        )

    return records


@dataclass(frozen=True)
class RDockPoseRecord:
    pose_id: int
    name: str
    score: float
    sd_block: str


def parse_rdock_sd_archive(
    path: Path,
    expected_pose_count: int | None = None,
) -> list[RDockPoseRecord]:
    """Parse a frozen rDock SD archive into ordered pose records.

    pose_id is the 1-based SD record order. It is deliberately not called
    rank because the rDock SD archive does not contain an explicit rank field.
    """
    text = path.read_text()

    blocks = text.split("$$$$")

    records: list[RDockPoseRecord] = []

    for block in blocks:
        if not block.strip():
            continue

        lines = block.splitlines()

        if len(lines) < 4:
            raise ValueError(
                f"{path}: encountered an incomplete SD record"
            )

        name = lines[0].strip()

        score_match = re.search(
            r">[ \t]+<SCORE>\s*\n"
            r"([^\r\n]+)",
            block,
        )

        if score_match is None:
            raise ValueError(
                f"{path}: SD record {len(records) + 1} "
                "is missing <SCORE>"
            )

        try:
            score = float(score_match.group(1).strip())
        except ValueError as exc:
            raise ValueError(
                f"{path}: SD record {len(records) + 1} "
                "has a non-numeric <SCORE>"
            ) from exc

        if not np.isfinite(score):
            raise ValueError(
                f"{path}: SD record {len(records) + 1} "
                "has a non-finite <SCORE>"
            )

        records.append(
            RDockPoseRecord(
                pose_id=len(records) + 1,
                name=name,
                score=score,
                sd_block=block + "$$$$",
            )
        )

    if expected_pose_count is not None and len(records) != expected_pose_count:
        raise ValueError(
            f"{path}: expected {expected_pose_count} rDock poses, "
            f"found {len(records)}"
        )

    return records


def reconstruct_rdock_pose_molecule(
    record: RDockPoseRecord,
    expected_heavy_atoms: int = EXPECTED_HEAVY_ATOMS,
) -> Chem.Mol:
    """Reconstruct one frozen rDock SD record as an RDKit molecule.

    The rDock SD writer places a library/version string on the mol-block
    header. The parser also preserves a leading blank separator line.
    This adapter normalizes only those header-format differences; atom
    coordinates,
    atom ordering, bonds, and the generated pose are unchanged.
    """
    sd_block = record.sd_block.rstrip()

    if sd_block.endswith("$$$$"):
        sd_block = sd_block[:-4].rstrip()

    lines = sd_block.splitlines()

    # The SD record parser preserves a leading blank line before the
    # molecule name. Remove only those leading blank separator lines.
    while lines and not lines[0].strip():
        lines.pop(0)

    if len(lines) < 5:
        raise ValueError(
            f"rDock pose {record.pose_id} has an incomplete mol block."
        )

    # After removing the SD separator, the rDock header is:
    #
    #   line 1: molecule name
    #   line 2: rDOCK program/version
    #   line 3: libRbt.so/version
    #   line 4: V2000 counts line
    #
    # RDKit expects line 3 to be a normal comment/header line, so replace
    # only the rDock library/version field.
    lines[2] = ""

    mol_block = "\n".join(lines)

    molecule = Chem.MolFromMolBlock(
        mol_block,
        sanitize=False,
        removeHs=False,
    )

    if molecule is None:
        raise ValueError(
            f"Could not reconstruct rDock pose {record.pose_id}."
        )

    heavy_atoms = molecule.GetNumHeavyAtoms()

    if heavy_atoms != expected_heavy_atoms:
        raise ValueError(
            f"rDock pose {record.pose_id} has {heavy_atoms} "
            f"heavy atoms; expected {expected_heavy_atoms}."
        )

    conformers = molecule.GetNumConformers()

    if conformers != EXPECTED_CONFORMERS:
        raise ValueError(
            f"rDock pose {record.pose_id} has {conformers} "
            f"conformers; expected {EXPECTED_CONFORMERS}."
        )

    conformer = molecule.GetConformer()

    for atom_index in range(molecule.GetNumAtoms()):
        position = conformer.GetAtomPosition(atom_index)

        if not (
            np.isfinite(position.x)
            and np.isfinite(position.y)
            and np.isfinite(position.z)
        ):
            raise ValueError(
                f"rDock pose {record.pose_id} contains "
                f"non-finite coordinates at atom {atom_index}."
            )

    return molecule


def measure_rdock_pose_d020(
    record: RDockPoseRecord,
    reference_molecule: Chem.Mol,
    receptor_positions: np.ndarray,
    receptor_atomic_numbers: tuple[int, ...],
) -> dict[str, float | int]:
    """Measure one frozen rDock pose using the frozen D020 functions.

    This function performs measurement only. It does not classify the pose,
    apply RMSD bands, determine physical plausibility, or select a negative.
    """
    pose = reconstruct_rdock_pose_molecule(record)

    rmsd = calculate_symmetry_corrected_rmsd(
        pose,
        reference_molecule,
    )

    d_rel = calculate_d_rel(
        pose,
        receptor_positions,
        receptor_atomic_numbers,
    )

    result = {
        "pose_id": record.pose_id,
        "score": float(record.score),
        "rmsd": float(rmsd),
        "d_rel": float(d_rel),
    }

    return result


def write_rdock_p1_survivor_sdf(
    records: list[RDockPoseRecord],
    measurement_rows: list[dict[str, float | int]],
    output_path: Path,
) -> None:
    """Write only the D020 RMSD >= 3.0 Å rDock survivors for P1."""
    measurement_by_pose_id = {
        int(row["pose_id"]): row
        for row in measurement_rows
    }

    survivors = []

    for record in records:
        row = measurement_by_pose_id[record.pose_id]

        if float(row["rmsd"]) >= 3.0:
            survivors.append((record, row))

    if len(survivors) != 48:
        raise ValueError(
            "Expected exactly 48 RMSD >= 3.0 Å survivors; "
            f"found {len(survivors)}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = Chem.SDWriter(str(output_path))

    try:
        for record, row in survivors:
            pose = reconstruct_rdock_pose_molecule(record)

            pose.SetProp("pose_id", str(record.pose_id))
            pose.SetProp(
                "rdock_score",
                f"{record.score:.10f}",
            )
            pose.SetProp(
                "d020_rmsd",
                f'{float(row["rmsd"]):.12f}',
            )
            pose.SetProp(
                "d020_d_rel",
                f'{float(row["d_rel"]):.12f}',
            )

            writer.write(pose)
    finally:
        writer.close()


def load_dock_xac_200save_records(
    path: Path = DOCK_XAC_200SAVE_ARCHIVE,
) -> list[DockPoseRecord]:
    """Load the frozen 200-pose DOCK XAC measurement archive."""
    return parse_dock_pose_archive(
        path,
        expected_pose_count=EXPECTED_POSES,
    )


def reconstruct_pose_molecule(record: DockPoseRecord):
    """Reconstruct one frozen DOCK pose as an RDKit molecule."""
    molecule = Chem.MolFromMol2Block(
        record.mol2_text,
        sanitize=False,
        removeHs=False,
    )

    if molecule is None:
        raise ValueError(
            f"Could not reconstruct DOCK pose rank {record.rank}."
        )

    heavy_atoms = molecule.GetNumHeavyAtoms()
    if heavy_atoms != EXPECTED_HEAVY_ATOMS:
        raise ValueError(
            f"DOCK pose rank {record.rank} has {heavy_atoms} "
            f"heavy atoms; expected {EXPECTED_HEAVY_ATOMS}."
        )

    conformers = molecule.GetNumConformers()
    if conformers != EXPECTED_CONFORMERS:
        raise ValueError(
            f"DOCK pose rank {record.rank} has {conformers} "
            f"conformers; expected {EXPECTED_CONFORMERS}."
        )

    return molecule


def reconstruct_pose_molecules(
    records: list[DockPoseRecord],
) -> list[Chem.Mol]:
    """Reconstruct all parsed DOCK pose records as RDKit molecules."""
    return [
        reconstruct_pose_molecule(record)
        for record in records
    ]


def load_xac_reference(
    path: Path = NATIVE_XAC_REFERENCE,
) -> Chem.Mol:
    """Load and validate the frozen experimental 3REY/XAC reference.

    The reference is the experimentally observed XAC pose in the
    3REY target frame. No coordinate transformation or fitting is
    performed here.
    """
    supplier = Chem.SDMolSupplier(
        str(path),
        removeHs=False,
    )

    if len(supplier) != 1:
        raise ValueError(
            f"Expected exactly one XAC reference molecule in {path}; "
            f"found {len(supplier)}."
        )

    reference = supplier[0]

    if reference is None:
        raise ValueError(
            f"Failed to load XAC reference: {path}"
        )

    if reference.GetNumHeavyAtoms() != EXPECTED_HEAVY_ATOMS:
        raise ValueError(
            "XAC reference has "
            f"{reference.GetNumHeavyAtoms()} heavy atoms; "
            f"expected {EXPECTED_HEAVY_ATOMS}."
        )

    if reference.GetNumConformers() != 1:
        raise ValueError(
            "XAC reference must contain exactly one conformer; "
            f"found {reference.GetNumConformers()}."
        )

    return reference


def validate_xac_chemistry(
    pose: Chem.Mol,
    reference: Chem.Mol,
) -> dict:
    """Validate XAC heavy-atom graph and report charge/protonation.

    The graph check intentionally ignores hydrogens, formal charge, and
    bond-order/aromaticity differences. Charge and protonation state are
    reported separately rather than used to fail graph validation.
    """
    pose_heavy = Chem.RemoveHs(
        pose,
        sanitize=False,
    )
    reference_heavy = Chem.RemoveHs(
        reference,
        sanitize=False,
    )

    pose_heavy_atoms = pose_heavy.GetNumAtoms()
    reference_heavy_atoms = reference_heavy.GetNumAtoms()

    if pose_heavy_atoms != EXPECTED_HEAVY_ATOMS:
        raise ValueError(
            f"DOCK pose has {pose_heavy_atoms} heavy atoms; "
            f"expected {EXPECTED_HEAVY_ATOMS}."
        )

    if reference_heavy_atoms != EXPECTED_HEAVY_ATOMS:
        raise ValueError(
            f"XAC reference has {reference_heavy_atoms} heavy atoms; "
            f"expected {EXPECTED_HEAVY_ATOMS}."
        )

    mcs = rdFMCS.FindMCS(
        [pose_heavy, reference_heavy],
        atomCompare=rdFMCS.AtomCompare.CompareElements,
        bondCompare=rdFMCS.BondCompare.CompareAny,
        ringMatchesRingOnly=False,
        completeRingsOnly=False,
    )

    graph_identical = (
        not mcs.canceled
        and mcs.numAtoms == EXPECTED_HEAVY_ATOMS
        and mcs.numBonds == pose_heavy.GetNumBonds()
        and mcs.numBonds == reference_heavy.GetNumBonds()
    )

    if not graph_identical:
        raise ValueError(
            "DOCK pose heavy-atom graph differs from frozen "
            "3REY/XAC reference."
        )

    pose_formal_charge = Chem.GetFormalCharge(pose)
    reference_formal_charge = Chem.GetFormalCharge(reference)
    pose_hydrogens = sum(
        1
        for atom in pose.GetAtoms()
        if atom.GetAtomicNum() == 1
    )
    reference_hydrogens = sum(
        1
        for atom in reference.GetAtoms()
        if atom.GetAtomicNum() == 1
    )

    return {
        "graph_identical": graph_identical,
        "pose_heavy_atoms": pose_heavy_atoms,
        "reference_heavy_atoms": reference_heavy_atoms,
        "heavy_bonds": mcs.numBonds,
        "pose_formal_charge": pose_formal_charge,
        "reference_formal_charge": reference_formal_charge,
        "formal_charge_delta": (
            pose_formal_charge - reference_formal_charge
        ),
        "pose_explicit_hydrogens": pose_hydrogens,
        "reference_explicit_hydrogens": reference_hydrogens,
        "explicit_hydrogen_delta": (
            pose_hydrogens - reference_hydrogens
        ),
        "charge_or_protonation_difference": (
            pose_formal_charge != reference_formal_charge
            or pose_hydrogens != reference_hydrogens
        ),
    }


def build_xac_heavy_atom_mappings(
    pose: Chem.Mol,
    reference: Chem.Mol,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all complete XAC heavy-atom mappings.

    Correspondence is defined from element identity and molecular
    connectivity only. Bond order, aromaticity, hydrogens, formal charge,
    chirality, and coordinates do not determine the mapping.

    Multiple complete mappings are retained for the downstream
    symmetry-corrected RMSD calculation.
    """
    pose_heavy = Chem.RemoveHs(
        pose,
        sanitize=False,
    )
    reference_heavy = Chem.RemoveHs(
        reference,
        sanitize=False,
    )

    if (
        pose_heavy.GetNumAtoms() != EXPECTED_HEAVY_ATOMS
        or reference_heavy.GetNumAtoms() != EXPECTED_HEAVY_ATOMS
    ):
        raise ValueError(
            "XAC heavy-atom mapping requires both molecules to have "
            f"{EXPECTED_HEAVY_ATOMS} heavy atoms."
        )

    mcs = rdFMCS.FindMCS(
        [pose_heavy, reference_heavy],
        atomCompare=rdFMCS.AtomCompare.CompareElements,
        bondCompare=rdFMCS.BondCompare.CompareAny,
        ringMatchesRingOnly=False,
        completeRingsOnly=False,
        matchChiralTag=False,
    )

    if mcs.canceled:
        raise ValueError(
            "XAC heavy-atom MCS calculation was canceled."
        )

    if mcs.numAtoms != EXPECTED_HEAVY_ATOMS:
        raise ValueError(
            "MCS does not cover all XAC heavy atoms: "
            f"found {mcs.numAtoms}, "
            f"expected {EXPECTED_HEAVY_ATOMS}."
        )

    if (
        mcs.numBonds != pose_heavy.GetNumBonds()
        or mcs.numBonds != reference_heavy.GetNumBonds()
    ):
        raise ValueError(
            "MCS does not preserve the complete XAC heavy-atom "
            "connectivity graph."
        )

    query = Chem.MolFromSmarts(
        mcs.smartsString
    )

    if query is None:
        raise ValueError(
            "Failed to construct the connectivity query from the XAC MCS."
        )

    pose_matches = pose_heavy.GetSubstructMatches(
        query,
        uniquify=False,
    )
    reference_matches = reference_heavy.GetSubstructMatches(
        query,
        uniquify=False,
    )

    if not pose_matches or not reference_matches:
        raise ValueError(
            "Complete XAC MCS could not be matched back onto "
            "one or both heavy-atom graphs."
        )

    mappings = []

    for pose_match in pose_matches:
        for reference_match in reference_matches:
            mapping = tuple(
                (pose_match[query_index], reference_match[query_index])
                for query_index in range(
                    query.GetNumAtoms()
                )
            )

            pose_indices = [
                pose_index
                for pose_index, _ in mapping
            ]
            reference_indices = [
                reference_index
                for _, reference_index in mapping
            ]

            if (
                len(set(pose_indices))
                != EXPECTED_HEAVY_ATOMS
            ):
                continue

            if (
                len(set(reference_indices))
                != EXPECTED_HEAVY_ATOMS
            ):
                continue

            mappings.append(mapping)

    if not mappings:
        raise ValueError(
            "No complete chemically valid XAC heavy-atom mapping "
            "could be constructed."
        )

    mappings = tuple(dict.fromkeys(mappings))
    return mappings


def calculate_symmetry_corrected_rmsd(
    pose: Chem.Mol,
    reference: Chem.Mol,
) -> float:
    """Calculate the minimum heavy-atom XAC RMSD across valid mappings.

    Coordinates are compared directly in the existing receptor frame.
    No ligand fitting or coordinate superposition is performed.
    """
    pose_heavy = Chem.RemoveHs(
        pose,
        sanitize=False,
    )
    reference_heavy = Chem.RemoveHs(
        reference,
        sanitize=False,
    )

    mappings = build_xac_heavy_atom_mappings(
        pose_heavy,
        reference_heavy,
    )

    pose_conformer = pose_heavy.GetConformer()
    reference_conformer = reference_heavy.GetConformer()

    rmsds = []

    for mapping in mappings:
        squared_distance_sum = 0.0

        for pose_index, reference_index in mapping:
            pose_position = pose_conformer.GetAtomPosition(
                pose_index
            )
            reference_position = (
                reference_conformer.GetAtomPosition(
                    reference_index
                )
            )

            dx = pose_position.x - reference_position.x
            dy = pose_position.y - reference_position.y
            dz = pose_position.z - reference_position.z

            squared_distance_sum += (
                dx * dx
                + dy * dy
                + dz * dz
            )

        rmsd = sqrt(
            squared_distance_sum
            / EXPECTED_HEAVY_ATOMS
        )

        rmsds.append(rmsd)

    if not rmsds:
        raise ValueError(
            "No valid XAC atom mappings were available "
            "for RMSD calculation."
        )

    return min(rmsds)


def calculate_d_rel(
    ligand: Chem.Mol,
    receptor_positions: np.ndarray,
    receptor_atomic_numbers: tuple[int, ...],
) -> float:
    """Calculate frozen PoseBusters-style protein-ligand d_rel.

    d_rel is the minimum intermolecular heavy-atom distance divided by
    the sum of the corresponding van der Waals radii.

    Van der Waals radii are taken from RDKit's PeriodicTable.GetRvdw()
    table, corresponding to the RDKit/Bondi radius source used by the
    frozen PoseBusters-derived preregistration.

    Coordinates are compared directly in the supplied common receptor
    frame. No fitting, alignment, or coordinate modification occurs.
    """
    ligand_heavy = Chem.RemoveHs(
        ligand,
        sanitize=False,
    )

    if ligand_heavy.GetNumConformers() != 1:
        raise ValueError(
            "d_rel requires exactly one ligand conformer."
        )

    receptor_positions = np.asarray(
        receptor_positions,
        dtype=float,
    )

    if receptor_positions.ndim != 2 or receptor_positions.shape[1] != 3:
        raise ValueError(
            "receptor_positions must have shape (N, 3)."
        )

    if len(receptor_atomic_numbers) != len(receptor_positions):
        raise ValueError(
            "Receptor atomic-number count does not match "
            "receptor coordinate count."
        )

    if len(receptor_positions) == 0:
        raise ValueError(
            "d_rel requires at least one receptor heavy atom."
        )

    periodic_table = GetPeriodicTable()

    ligand_conformer = ligand_heavy.GetConformer()

    ligand_positions = np.asarray(
        [
            ligand_conformer.GetAtomPosition(index)
            for index in range(
                ligand_heavy.GetNumAtoms()
            )
        ],
        dtype=float,
    )

    ligand_atomic_numbers = np.asarray(
        [
            atom.GetAtomicNum()
            for atom in ligand_heavy.GetAtoms()
        ],
        dtype=int,
    )

    receptor_radii = np.asarray(
        [
            periodic_table.GetRvdw(
                int(atomic_number)
            )
            for atomic_number in receptor_atomic_numbers
        ],
        dtype=float,
    )

    ligand_radii = np.asarray(
        [
            periodic_table.GetRvdw(
                int(atomic_number)
            )
            for atomic_number in ligand_atomic_numbers
        ],
        dtype=float,
    )

    distances = (
        ligand_positions[:, None, :]
        - receptor_positions[None, :, :]
    )

    pairwise_distances = np.linalg.norm(
        distances,
        axis=2,
    )

    normalized_distances = (
        pairwise_distances
        / (
            ligand_radii[:, None]
            + receptor_radii[None, :]
        )
    )

    normalized_distances = float(np.min(normalized_distances))
    return normalized_distances


def load_3rey_receptor_heavy_atoms(
    path: Path = NATIVE_RECEPTOR_PQR,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Load heavy-atom coordinates/elements from the frozen 3REY receptor.

    The receptor is loaded through the existing validated native-reader
    pathway so the same prepared 3REY coordinate frame is used for the
    XAC reference and d_rel measurement.

    No coordinate transformation or fitting is performed.
    """
    protein_results = load_protein(path)
    protein = protein_results["protein"]

    conformer = protein.GetConformer()

    positions = []
    atomic_numbers = []

    for atom_index, atom in enumerate(protein.GetAtoms()):
        if atom.GetAtomicNum() == 1:
            continue

        position = conformer.GetAtomPosition(atom_index)

        positions.append(
            (
                position.x,
                position.y,
                position.z,
            )
        )
        atomic_numbers.append(
            atom.GetAtomicNum()
        )

    coordinates = np.asarray(
        positions,
        dtype=float,
    )

    atomic_numbers_tuple = tuple(
        atomic_numbers
    )

    if coordinates.ndim != 2 or coordinates.shape[1] != 3:
        raise ValueError(
            "3REY receptor heavy-atom coordinates must have shape (N, 3)."
        )

    if len(atomic_numbers_tuple) != len(coordinates):
        raise ValueError(
            "3REY receptor atomic-number count does not match "
            "coordinate count."
        )

    if not np.isfinite(coordinates).all():
        raise ValueError(
            "3REY receptor heavy-atom coordinates contain non-finite values."
        )

    if not len(coordinates):
        raise ValueError(
            "No 3REY receptor heavy atoms were loaded."
        )

    return coordinates, atomic_numbers_tuple


def reconstruct_dock_orientation(
    ligand_coordinates: np.ndarray,
    coml: np.ndarray,
    comr: np.ndarray,
    rotation: np.ndarray,
) -> np.ndarray:
    """Reconstruct one DOCK-generated ligand orientation.

    DOCK's frozen transform convention from transfm_conf.f is:

        transformed = comr + rotation * (coords - coml)

    The persisted output_match representation stores:
        coml: ligand match-center, shape (3,)
        comr: receptor match-center, shape (3,)
        rotation: 3x3 rotation matrix

    Parameters
    ----------
    ligand_coordinates
        Original ligand coordinates, shape (N, 3).
    coml
        Persisted ligand match-center, shape (3,).
    comr
        Persisted receptor match-center, shape (3,).
    rotation
        Persisted 3x3 DOCK rotation matrix.

    Returns
    -------
    np.ndarray
        Reconstructed coordinates, shape (N, 3).
    """
    ligand_coordinates = np.asarray(ligand_coordinates, dtype=float)
    coml = np.asarray(coml, dtype=float)
    comr = np.asarray(comr, dtype=float)
    rotation = np.asarray(rotation, dtype=float)

    if ligand_coordinates.ndim != 2 or ligand_coordinates.shape[1] != 3:
        raise ValueError(
            "ligand_coordinates must have shape (N, 3)"
        )

    if coml.shape != (3,):
        raise ValueError("coml must have shape (3,)")

    if comr.shape != (3,):
        raise ValueError("comr must have shape (3,)")

    if rotation.shape != (3, 3):
        raise ValueError("rotation must have shape (3, 3)")

    if not np.isfinite(ligand_coordinates).all():
        raise ValueError("ligand_coordinates contains non-finite values")

    if not np.isfinite(coml).all():
        raise ValueError("coml contains non-finite values")

    if not np.isfinite(comr).all():
        raise ValueError("comr contains non-finite values")

    if not np.isfinite(rotation).all():
        raise ValueError("rotation contains non-finite values")

    centered = ligand_coordinates - coml
    return centered @ rotation.T + comr


def load_dock_orientation_archives(
    comr_path: Path,
    coml_path: Path,
    rot_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load line-aligned DOCK orientation archives.

    The pinned DOCK output_match writer emits three gzip-compressed text
    streams with one orientation per line:

        comr: 3 values
        coml: 3 values
        rot: 9 values in Fortran column-major order:
             rot11, rot21, rot31,
             rot12, rot22, rot32,
             rot13, rot23, rot33

    The three streams are required to have identical record counts and are
    returned in their existing archive order.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        coml: shape (N, 3)
        comr: shape (N, 3)
        rot: shape (N, 3, 3)
    """
    import gzip

    def read_values(path: Path, expected_width: int) -> list[list[float]]:
        records: list[list[float]] = []

        with gzip.open(path, "rt") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                fields = stripped.split()

                if len(fields) != expected_width:
                    raise ValueError(
                        f"{path}: line {line_number} has "
                        f"{len(fields)} values; expected {expected_width}"
                    )

                try:
                    values = [float(value) for value in fields]
                except ValueError as exc:
                    raise ValueError(
                        f"{path}: line {line_number} contains "
                        "a non-numeric value"
                    ) from exc

                if not np.isfinite(values).all():
                    raise ValueError(
                        f"{path}: line {line_number} contains "
                        "a non-finite value"
                    )

                records.append(values)

        return records

    comr_records = read_values(comr_path, 3)
    coml_records = read_values(coml_path, 3)
    rot_records = read_values(rot_path, 9)

    counts = (
        len(comr_records),
        len(coml_records),
        len(rot_records),
    )

    if len(set(counts)) != 1:
        raise ValueError(
            "DOCK orientation archives have mismatched record counts: "
            f"comr={counts[0]}, coml={counts[1]}, rot={counts[2]}"
        )

    comr = np.asarray(comr_records, dtype=float)
    coml = np.asarray(coml_records, dtype=float)

    rot_flat = np.asarray(rot_records, dtype=float)

    # DOCK writes Fortran column-major matrix entries:
    # [r11, r21, r31, r12, r22, r32, r13, r23, r33].
    rot = rot_flat.reshape((-1, 3, 3), order="F")

    return coml, comr, rot


def reconstruct_dock_orientation_population(
    ligand_coordinates: np.ndarray,
    coml: np.ndarray,
    comr: np.ndarray,
    rotations: np.ndarray,
) -> np.ndarray:
    """Reconstruct an entire persisted DOCK orientation population.

    Each orientation uses the frozen DOCK transform:

        transformed = comr + rotation @ (coords - coml)

    The first axis of the returned array preserves the archive order.

    Parameters
    ----------
    ligand_coordinates
        Original ligand coordinates, shape (N_atoms, 3).
    coml
        Ligand match-centers, shape (N_poses, 3).
    comr
        Receptor match-centers, shape (N_poses, 3).
    rotations
        Rotation matrices, shape (N_poses, 3, 3).

    Returns
    -------
    np.ndarray
        Reconstructed coordinates, shape (N_poses, N_atoms, 3).
    """
    ligand_coordinates = np.asarray(ligand_coordinates, dtype=float)
    coml = np.asarray(coml, dtype=float)
    comr = np.asarray(comr, dtype=float)
    rotations = np.asarray(rotations, dtype=float)

    if ligand_coordinates.ndim != 2 or ligand_coordinates.shape[1] != 3:
        raise ValueError("ligand_coordinates must have shape (N_atoms, 3)")

    if coml.ndim != 2 or coml.shape[1] != 3:
        raise ValueError("coml must have shape (N_poses, 3)")

    if comr.shape != coml.shape:
        raise ValueError("comr must have the same shape as coml")

    if rotations.ndim != 3 or rotations.shape[1:] != (3, 3):
        raise ValueError(
            "rotations must have shape (N_poses, 3, 3)"
        )

    n_poses = coml.shape[0]

    if comr.shape[0] != n_poses or rotations.shape[0] != n_poses:
        raise ValueError(
            "orientation arrays must contain the same number of poses"
        )

    if not (
        np.isfinite(ligand_coordinates).all()
        and np.isfinite(coml).all()
        and np.isfinite(comr).all()
        and np.isfinite(rotations).all()
    ):
        raise ValueError("orientation inputs contain non-finite values")

    centered = ligand_coordinates[None, :, :] - coml[:, None, :]

    reconstructed = np.einsum(
        "pij,paj->pai",
        rotations,
        centered,
    )

    reconstructed += comr[:, None, :]

    return reconstructed


def measure_d020_population(
    reconstructed_coordinates: np.ndarray,
    reference_molecule: Chem.Mol,
    receptor_positions: np.ndarray,
    receptor_atomic_numbers: np.ndarray,
    pose_template: Chem.Mol,
) -> list[dict[str, float | int]]:
    """Measure frozen D020 quantities for a reconstructed pose population.

    This function performs measurement only. It does not classify poses as
    near-native, alternative, physically plausible, or eligible.

    Parameters
    ----------
    reconstructed_coordinates
        Reconstructed ligand coordinates in archive order,
        shape (N_poses, N_atoms, 3).
    reference_molecule
        Frozen experimental XAC reference molecule used by D020 RMSD.
    receptor_positions
        Frozen 3REY receptor heavy-atom coordinates used by D020 d_rel.
    receptor_atomic_numbers
        Atomic numbers corresponding to receptor_positions.
    pose_template
        Molecule carrying the frozen XAC molecular graph and atom ordering.
        Its conformer is replaced temporarily with each reconstructed pose.

    Returns
    -------
    list[dict]
        One measurement record per pose, preserving archive order. Each record
        contains:
            orient_index
            rmsd
            d_rel
    """
    reconstructed_coordinates = np.asarray(
        reconstructed_coordinates,
        dtype=float,
    )

    if reconstructed_coordinates.ndim != 3:
        raise ValueError(
            "reconstructed_coordinates must have shape "
            "(N_poses, N_atoms, 3)"
        )

    if reconstructed_coordinates.shape[2] != 3:
        raise ValueError(
            "reconstructed_coordinates must have final dimension 3"
        )

    if not np.isfinite(reconstructed_coordinates).all():
        raise ValueError(
            "reconstructed_coordinates contains non-finite values"
        )

    n_poses, n_atoms, _ = reconstructed_coordinates.shape

    if pose_template.GetNumConformers() == 0:
        raise ValueError(
            "pose_template must contain a conformer"
        )

    if pose_template.GetNumAtoms() != n_atoms:
        raise ValueError(
            "pose_template atom count does not match reconstructed "
            f"coordinates: {pose_template.GetNumAtoms()} != {n_atoms}"
        )

    results: list[dict[str, float | int]] = []

    for orient_index in range(n_poses):
        pose = Chem.Mol(pose_template)
        conformer = pose.GetConformer()

        coordinates = reconstructed_coordinates[orient_index]

        for atom_index, coordinate in enumerate(coordinates):
            conformer.SetAtomPosition(
                atom_index,
                coordinate,
            )

        rmsd = calculate_symmetry_corrected_rmsd(
            pose,
            reference_molecule,
        )

        d_rel = calculate_d_rel(
            pose,
            receptor_positions,
            receptor_atomic_numbers,
        )

        results.append(
            {
                "orient_index": orient_index + 1,
                "rmsd": float(rmsd),
                "d_rel": float(d_rel),
            }
        )

    return results


def measure_d021_persisted_orientation_population(
    comr_path: Path,
    coml_path: Path,
    rot_path: Path,
) -> list[dict[str, float | int]]:
    """Measure the complete persisted D021 orientation population.

    Loads the three frozen DOCK output_match archives, reconstructs every
    persisted orientation, and applies the frozen D020 RMSD and d_rel
    measurements in archive order.

    This function performs measurement orchestration only. It does not
    classify or select candidates.
    """
    coml, comr, rotations = load_dock_orientation_archives(
        comr_path,
        coml_path,
        rot_path,
    )

    reference = load_xac_reference()

    receptor_positions, receptor_atomic_numbers = (
        load_3rey_receptor_heavy_atoms()
    )

    ligand_coordinates = np.asarray(
        reference.GetConformer().GetPositions(),
        dtype=float,
    )

    reconstructed = reconstruct_dock_orientation_population(
        ligand_coordinates=ligand_coordinates,
        coml=coml,
        comr=comr,
        rotations=rotations,
    )

    return measure_d020_population(
        reconstructed_coordinates=reconstructed,
        reference_molecule=reference,
        receptor_positions=receptor_positions,
        receptor_atomic_numbers=receptor_atomic_numbers,
        pose_template=reference,
    )


def write_d021_measurement_csv(
    results: list[dict[str, float | int]],
    output_path: Path,
) -> None:
    """Write the complete raw D021 measurement population."""
    import csv

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["orient_index", "rmsd", "d_rel"])

        for record in results:
            writer.writerow(
                [
                    record["orient_index"],
                    f'{record["rmsd"]:.12f}',
                    f'{record["d_rel"]:.12f}',
                ]
            )


def main() -> None:
    root = Path(__file__).resolve().parents[2]

    archive_dir = (
        root
        / "references/stage5/dock385/d021_orientation_archive"
    )

    output_path = (
        root
        / "references/stage5/dock385/"
          "d021_orientation_measurement/"
          "d021_A1_all_7989_measurements.csv"
    )

    results = measure_d021_persisted_orientation_population(
        archive_dir / "orientations_mol000001_comr.gz",
        archive_dir / "orientations_mol000001_coml.gz",
        archive_dir / "orientations_mol000001_rot.gz",
    )

    if len(results) != 7989:
        raise RuntimeError(
            f"Expected 7989 measurements, got {len(results)}"
        )

    write_d021_measurement_csv(
        results,
        output_path,
    )

    print(f"wrote {len(results)} measurements")
    print(output_path)


if __name__ == "__main__":
    main()
