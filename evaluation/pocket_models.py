from dataclasses import dataclass


@dataclass(frozen=True)
class P2RankPocket:
    """One pocket predicted by P2Rank."""

    name: str
    rank: int
    score: float
    probability: float
    sas_points: int
    surf_atoms: int
    center: tuple[float, float, float]
    residue_ids: tuple[str, ...]
    surf_atom_ids: tuple[int, ...]


@dataclass(frozen=True, order=True)
class ResidueID:
    """Identity of one residue in the source structure."""

    chain: str
    number: str
    insertion_code: str
    name: str


@dataclass(frozen=True)
class PocketSelection:
    """Frozen instruction selecting one predicted pocket."""

    method: str
    value: str


@dataclass(frozen=True)
class FileProvenance:
    """Identity of a retained file."""

    path: str
    sha256: str


@dataclass(frozen=True)
class PocketLineage:
    """Frozen role of a predicted pocket."""

    conditioning_role: bool
    primary_stage3b_role: bool
    selection_frozen_before_generation: bool


@dataclass(frozen=True)
class PredictedPocketMetadata:
    """Metadata and provenance for a predicted pocket."""

    artifact_type: str
    pocket_method: str
    p2rank_version: str
    source_structure: FileProvenance
    predictions_output: FileProvenance
    residues_output: FileProvenance
    selected_pocket: P2RankPocket
    materialized_residues: tuple[ResidueID, ...]
    selection_config: FileProvenance
    lineage: PocketLineage
