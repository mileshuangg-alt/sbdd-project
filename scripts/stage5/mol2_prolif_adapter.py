from dataclasses import dataclass
from pathlib import Path

import numpy as np
import prolif as plf
from rdkit import Chem


@dataclass(frozen=True)
class Mol2CoordinateAudit:
    atom_count: int
    has_conformer: bool
    max_abs_coordinate_deviation: float
    rms_coordinate_deviation: float


@dataclass(frozen=True)
class Mol2ProlifLoadResult:
    rdkit_molecule: Chem.Mol
    prolif_molecule: plf.Molecule
    coordinate_audit: Mol2CoordinateAudit


def parse_mol2_atom_coordinates(path: Path) -> np.ndarray:
    """Parse MOL2 atom coordinates directly from the frozen atom block."""

    coordinates = []
    in_atom_block = False

    with path.open() as handle:
        for line in handle:
            stripped = line.strip()

            if stripped == "@<TRIPOS>ATOM":
                in_atom_block = True
                continue

            if stripped.startswith("@<TRIPOS>"):
                in_atom_block = False

            if not in_atom_block or not stripped:
                continue

            fields = stripped.split()
            if len(fields) < 5:
                raise ValueError(
                    f"Malformed MOL2 atom record in {path}: {line.rstrip()}"
                )

            coordinates.append(
                [
                    float(fields[2]),
                    float(fields[3]),
                    float(fields[4]),
                ]
            )

    if not coordinates:
        raise ValueError(f"No MOL2 atom coordinates found: {path}")

    return np.asarray(coordinates, dtype=float)


def rdkit_conformer_coordinates(molecule: Chem.Mol) -> np.ndarray:
    """Return RDKit conformer coordinates in atom-index order."""

    if molecule.GetNumConformers() != 1:
        raise ValueError(
            "MOL2 ligand must contain exactly one conformer; "
            f"found {molecule.GetNumConformers()}."
        )

    conformer = molecule.GetConformer()
    coordinates = []

    for atom_index in range(molecule.GetNumAtoms()):
        position = conformer.GetAtomPosition(atom_index)
        coordinates.append([position.x, position.y, position.z])

    return np.asarray(coordinates, dtype=float)


def coordinate_audit(
    parsed_coordinates: np.ndarray,
    rdkit_coordinates: np.ndarray,
) -> Mol2CoordinateAudit:
    """Compare parsed MOL2 coordinates with the RDKit conformer."""

    if parsed_coordinates.shape != rdkit_coordinates.shape:
        raise ValueError(
            "Parsed MOL2 and RDKit coordinate arrays differ in shape: "
            f"{parsed_coordinates.shape} != {rdkit_coordinates.shape}."
        )

    delta = rdkit_coordinates - parsed_coordinates

    atom_squared_distances = np.sum(delta * delta, axis=1)

    return Mol2CoordinateAudit(
        atom_count=int(parsed_coordinates.shape[0]),
        has_conformer=True,
        max_abs_coordinate_deviation=float(np.max(np.abs(delta))),
        rms_coordinate_deviation=float(np.sqrt(np.mean(atom_squared_distances))),
    )


def load_mol2_ligand_for_prolif(path: Path) -> plf.Molecule:
    """Load a MOL2 ligand through RDKit into ProLIF without editing coordinates."""

    return load_mol2_ligand_for_prolif_with_audit(path).prolif_molecule


def load_mol2_ligand_for_prolif_with_audit(
    path: Path,
) -> Mol2ProlifLoadResult:
    """Load MOL2 -> RDKit -> ProLIF and report coordinate preservation."""

    parsed_coordinates = parse_mol2_atom_coordinates(path)

    rdkit_molecule = Chem.MolFromMol2File(
        str(path),
        sanitize=True,
        removeHs=False,
        cleanupSubstructures=False,
    )

    if rdkit_molecule is None:
        raise ValueError(f"RDKit failed to parse MOL2 ligand: {path}")

    rdkit_coordinates = rdkit_conformer_coordinates(rdkit_molecule)
    audit = coordinate_audit(
        parsed_coordinates,
        rdkit_coordinates,
    )

    prolif_molecule = plf.Molecule.from_rdkit(
        rdkit_molecule
    )

    return Mol2ProlifLoadResult(
        rdkit_molecule=rdkit_molecule,
        prolif_molecule=prolif_molecule,
        coordinate_audit=audit,
    )
