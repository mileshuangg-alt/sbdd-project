import csv
import hashlib
import json
from pathlib import Path
from dataclasses import asdict
from evaluation.pocket_models import (
    FileProvenance,
    P2RankPocket,
    PocketLineage,
    PocketSelection,
    PredictedPocketMetadata,
    ResidueID,
)
from evaluation.pocket_models import P2RankPocket


# ---------------------------------------------------------------------------
# Native P2Rank prediction parsing
# ---------------------------------------------------------------------------


def load_p2rank_predictions(
    path: Path,
) -> list[P2RankPocket]:
    """Load native P2Rank pocket predictions."""

    predictions = []

    with path.open(newline="") as handle:
        reader = csv.DictReader(
            handle,
            skipinitialspace=True,
        )

        # Normalize whitespace in the P2Rank header names.
        reader.fieldnames = [
            fieldname.strip()
            for fieldname in (reader.fieldnames or [])
        ]

        required_columns = {
            "name",
            "rank",
            "score",
            "probability",
            "sas_points",
            "surf_atoms",
            "center_x",
            "center_y",
            "center_z",
            "residue_ids",
            "surf_atom_ids",
        }

        missing_columns = (
            required_columns
            - set(reader.fieldnames)
        )

        if missing_columns:
            raise ValueError(
                "P2Rank prediction file is missing "
                f"required columns: "
                f"{sorted(missing_columns)}"
            )

        for row in reader:
            # Convert the native row into a P2RankPocket object.
            predictions.append(
                P2RankPocket(
                    name=row["name"].strip(),
                    rank=int(row["rank"]),
                    score=float(row["score"]),
                    probability=float(row["probability"]),
                    sas_points=int(row["sas_points"]),
                    surf_atoms=int(row["surf_atoms"]),
                    center=(
                        float(row["center_x"]),
                        float(row["center_y"]),
                        float(row["center_z"]),
                    ),
                    residue_ids=tuple(
                        row["residue_ids"].split()
                        if row["residue_ids"].strip()
                        else []
                    ),
                    surf_atom_ids=tuple(
                        int(value)
                        for value in row["surf_atom_ids"].split()
                    ),
                )
            )

    return predictions


# ---------------------------------------------------------------------------
# Prospective pocket selection
# ---------------------------------------------------------------------------


def select_predicted_pocket(
    predictions: list[P2RankPocket],
    selection: PocketSelection,
) -> P2RankPocket:
    """Select one P2Rank pocket from frozen configuration."""

    method = selection.method
    value = selection.value

    if method != "p2rank_name":
        raise ValueError(
            f"Unsupported selection method: {method}"
        )

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "P2Rank pocket selection requires a "
            "non-empty string value."
        )

    # Match the configured pocket name exactly.
    matches = [
        pocket
        for pocket in predictions
        if pocket.name == value
    ]

    if len(matches) == 0:
        raise ValueError(
            f"Configured P2Rank pocket not found: {value!r}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Configured P2Rank pocket is ambiguous: {value!r}"
        )

    return matches[0]


# ---------------------------------------------------------------------------
# Source-PDB atom indexing
# ---------------------------------------------------------------------------


def load_pdb_atoms_by_serial(
    path: Path,
) -> dict[int, str]:
    """Load source-PDB ATOM records by serial number."""

    atoms = {}

    with path.open() as handle:
        for line in handle:
            if not line.startswith("ATOM"):
                continue

            # Read the fixed-width PDB atom serial field.
            serial_text = line[6:11].strip()

            if not serial_text:
                raise ValueError(
                    "PDB ATOM record has no serial number: "
                    f"{line.rstrip()}"
                )

            serial = int(serial_text)

            if serial in atoms:
                raise ValueError(
                    f"Duplicate PDB atom serial number: {serial}"
                )

            # Keep the original PDB record.
            atoms[serial] = line

    return atoms


# ---------------------------------------------------------------------------
# P2Rank atom-level pocket selection
# ---------------------------------------------------------------------------


def get_predicted_pocket_atoms(
    selected_pocket: P2RankPocket,
    atoms_by_serial: dict[int, str],
) -> list[str]:
    """Return source-PDB ATOM records selected by P2Rank."""

    surf_atom_ids = selected_pocket.surf_atom_ids

    if not surf_atom_ids:
        raise ValueError(
            "Selected P2Rank pocket contains no surface atom IDs."
        )

    # Check that every P2Rank atom ID exists in the source PDB.
    missing_ids = [
        serial
        for serial in surf_atom_ids
        if serial not in atoms_by_serial
    ]

    if missing_ids:
        raise ValueError(
            "P2Rank surface atom IDs are missing from "
            f"the input protein: {missing_ids}"
        )

    # Return the original PDB records in P2Rank order.
    return [
        atoms_by_serial[serial]
        for serial in surf_atom_ids
    ]


# ---------------------------------------------------------------------------
# P2Rank atoms -> source-PDB residue identities
# ---------------------------------------------------------------------------


def get_touched_residues(
    selected_pocket: P2RankPocket,
    pdb_atoms: dict[int, str],
) -> list[ResidueID]:
    """Identify source-PDB residues touched by P2Rank atoms."""

    surf_atom_ids = selected_pocket.surf_atom_ids

    if not surf_atom_ids:
        raise ValueError(
            "Selected P2Rank pocket contains no surface atom IDs."
        )

    # Check that every P2Rank atom ID exists in the source PDB.
    missing_ids = [
        serial
        for serial in surf_atom_ids
        if serial not in pdb_atoms
    ]

    if missing_ids:
        raise ValueError(
            "P2Rank surface atom IDs are missing from "
            f"the input protein: {missing_ids}"
        )

    residues = set()

    for serial in surf_atom_ids:
        # Retrieve the original PDB atom record.
        line = pdb_atoms[serial]

        # Read the parent residue from the fixed-width PDB fields.
        chain = line[21].strip()
        residue_number = line[22:26].strip()
        insertion_code = line[26].strip()
        residue_name = line[17:20].strip()

        residues.add(
            ResidueID(
                chain=chain,
                number=residue_number,
                insertion_code=insertion_code,
                name=residue_name,
            )
        )

    # Sort by structural identity while preserving numeric PDB ordering.
    def residue_sort_key(residue: ResidueID) -> tuple[str, int | str, str, str]:
        number = (
            int(residue.number)
            if residue.number.lstrip("-").isdigit()
            else residue.number
        )
        return (
            residue.chain,
            number,
            residue.insertion_code,
            residue.name,
        )

    return sorted(residues, key=residue_sort_key)


# ---------------------------------------------------------------------------
# Residue identities -> complete source-PDB residues
# ---------------------------------------------------------------------------


def get_complete_residue_atoms(
    touched_residues: list[ResidueID],
    pdb_path: Path,
) -> list[str]:
    """Return all source-PDB ATOM records for touched residues."""

    # Build the set of residues selected by the P2Rank atom mapping.
    residue_keys = {
        (
            residue.chain,
            residue.number,
            residue.insertion_code,
            residue.name,
        )
        for residue in touched_residues
    }

    pocket_atoms = []

    with pdb_path.open() as handle:
        for line in handle:
            if not line.startswith("ATOM"):
                continue

            # Read residue identity from the original PDB.
            chain = line[21].strip()
            residue_number = line[22:26].strip()
            insertion_code = line[26].strip()
            residue_name = line[17:20].strip()

            residue_key = (
                chain,
                residue_number,
                insertion_code,
                residue_name,
            )

            # Include every atom from each selected residue.
            if residue_key in residue_keys:
                pocket_atoms.append(line)

    if not pocket_atoms:
        raise ValueError(
            "No ATOM records matched the selected pocket residues."
        )

    return pocket_atoms


# ---------------------------------------------------------------------------
# Predicted-pocket structure materialization
# ---------------------------------------------------------------------------


def write_predicted_pocket(
    complete_residue_atoms: list[str],
    output_path: Path,
) -> None:
    """Write the residue-complete predicted-pocket PDB."""

    if not complete_residue_atoms:
        raise ValueError(
            "Cannot write a predicted pocket with no ATOM records."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w") as handle:
        for line in complete_residue_atoms:
            # Preserve each source-PDB ATOM record.
            handle.write(
                line
                if line.endswith("\n")
                else line + "\n"
            )

        handle.write("END\n")


# ---------------------------------------------------------------------------
# Complete-residue pocket validation
# ---------------------------------------------------------------------------


def validate_complete_residue_pocket(
    complete_residue_atoms: list[str],
    touched_residues: list[ResidueID],
    source_pdb_path: Path,
) -> None:
    """Validate residue membership and completeness."""

    # Residues identified from the P2Rank-selected surface atoms.
    expected_residues = set(
        touched_residues
    )

    # Collect the original ATOM records for each selected residue.
    source_atoms_by_residue = {}

    with source_pdb_path.open() as handle:
        for line in handle:
            if not line.startswith("ATOM"):
                continue

            residue = ResidueID(
                chain=line[21].strip(),
                number=line[22:26].strip(),
                insertion_code=line[26].strip(),
                name=line[17:20].strip(),
            )

            if residue in expected_residues:
                source_atoms_by_residue.setdefault(
                    residue,
                    [],
                ).append(line)

    # Organize the derived ATOM records by residue.
    derived_atoms_by_residue = {}

    for line in complete_residue_atoms:
        residue = ResidueID(
            chain=line[21].strip(),
            number=line[22:26].strip(),
            insertion_code=line[26].strip(),
            name=line[17:20].strip(),
        )

        derived_atoms_by_residue.setdefault(
            residue,
            [],
        ).append(line)

    # Check that the derived pocket contains exactly the selected residues.
    derived_residues = set(
        derived_atoms_by_residue
    )

    if derived_residues != expected_residues:
        raise ValueError(
            "Derived pocket residue membership does not "
            "match the P2Rank-touched residue set."
        )

    # For every selected residue, check if the derived ATOM records match
    # the original source-PDB records. Check atom membership,
    # ordering, identity, and coordinates.
    for residue in expected_residues:
        source_atoms = source_atoms_by_residue.get(
            residue,
            [],
        )

        derived_atoms = derived_atoms_by_residue.get(
            residue,
            [],
        )

        if derived_atoms != source_atoms:
            raise ValueError(
                "Derived pocket does not preserve the complete "
                f"source-PDB residue: {residue}"
            )


# ---------------------------------------------------------------------------
# File provenance
# ---------------------------------------------------------------------------


def sha256_file(
    path: Path,
) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Predicted-pocket metadata
# ---------------------------------------------------------------------------


def build_predicted_pocket_metadata(
    *,
    source_structure_path: Path,
    predictions_path: Path,
    residues_path: Path,
    selected_pocket: P2RankPocket,
    touched_residues: list[ResidueID],
    selection_config_path: Path,
    p2rank_version: str,
) -> PredictedPocketMetadata:
    """Build provenance for one frozen predicted pocket."""

    # Hash the files used to construct the pocket.
    source_structure = FileProvenance(
        path=str(source_structure_path),
        sha256=sha256_file(
            source_structure_path
        ),
    )

    predictions_output = FileProvenance(
        path=str(predictions_path),
        sha256=sha256_file(
            predictions_path
        ),
    )

    residues_output = FileProvenance(
        path=str(residues_path),
        sha256=sha256_file(
            residues_path
        ),
    )

    selection_config = FileProvenance(
        path=str(selection_config_path),
        sha256=sha256_file(
            selection_config_path
        ),
    )

    # Record the D015 conditioning and Stage-3B roles.
    lineage = PocketLineage(
        conditioning_role=True,
        primary_stage3b_role=True,
        selection_frozen_before_generation=True,
    )

    # Freeze the materialized residue list.
    materialized_residues = tuple(
        touched_residues
    )

    # Assemble the metadata object.
    metadata = PredictedPocketMetadata(
        artifact_type="PREDICTED POCKET",
        pocket_method="P2Rank",
        p2rank_version=p2rank_version,
        source_structure=source_structure,
        predictions_output=predictions_output,
        residues_output=residues_output,
        selected_pocket=selected_pocket,
        materialized_residues=materialized_residues,
        selection_config=selection_config,
        lineage=lineage,
    )

    return metadata


def write_predicted_pocket_metadata(
    metadata: PredictedPocketMetadata,
    output_path: Path,
) -> None:
    """Write predicted-pocket metadata as JSON."""

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w") as handle:
        # Convert the typed metadata object to JSON only at the file boundary.
        json.dump(
            asdict(metadata),
            handle,
            indent=2,
        )
        handle.write("\n")


def load_pocket_selection(
    path: Path,
) -> PocketSelection:
    """Load and validate a frozen pocket-selection config."""

    with path.open() as handle:
        config = json.load(handle)

    if config.get("schema_version") != 1:
        raise ValueError(
            "Unsupported pocket-selection schema version: "
            f"{config.get('schema_version')!r}"
        )

    method = config.get("method")
    value = config.get("value")

    if method != "p2rank_name":
        raise ValueError(
            "Unsupported pocket-selection method: "
            f"{method!r}"
        )

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "P2Rank pocket selection requires a "
            "non-empty string value."
        )

    return PocketSelection(
        method=method,
        value=value,
    )


def build_predicted_pocket_artifact(
    *,
    source_structure_path: Path,
    predictions_path: Path,
    residues_path: Path,
    selection_config_path: Path,
    output_structure_path: Path,
    output_metadata_path: Path,
    p2rank_version: str,
) -> PredictedPocketMetadata:
    """Build and validate one P2Rank-predicted pocket artifact."""

    # Load the frozen pocket-selection config.
    selection = load_pocket_selection(
        selection_config_path
    )

    # Load the native P2Rank pocket predictions.
    predictions = load_p2rank_predictions(
        predictions_path
    )

    # Apply the configured pocket selection.
    selected_pocket = select_predicted_pocket(
        predictions,
        selection,
    )

    # Index the original source-PDB atoms by serial number.
    atoms_by_serial = load_pdb_atoms_by_serial(
        source_structure_path
    )

    # Identify source-PDB residues touched by P2Rank-selected atoms.
    touched_residues = get_touched_residues(
        selected_pocket,
        atoms_by_serial,
    )

    # Expand the touched residues to complete source-PDB residues.
    complete_residue_atoms = get_complete_residue_atoms(
        touched_residues,
        source_structure_path,
    )

    # Validate residue membership and complete source-PDB preservation.
    validate_complete_residue_pocket(
        complete_residue_atoms,
        touched_residues,
        source_structure_path,
    )

    # Write the residue-complete predicted-pocket structure.
    write_predicted_pocket(
        complete_residue_atoms,
        output_structure_path,
    )

    # Build the provenance object for the derived artifact.
    metadata = build_predicted_pocket_metadata(
        source_structure_path=source_structure_path,
        predictions_path=predictions_path,
        residues_path=residues_path,
        selected_pocket=selected_pocket,
        touched_residues=touched_residues,
        selection_config_path=selection_config_path,
        p2rank_version=p2rank_version,
    )

    # Serialize provenance to JSON.
    write_predicted_pocket_metadata(
        metadata,
        output_metadata_path,
    )

    return metadata
