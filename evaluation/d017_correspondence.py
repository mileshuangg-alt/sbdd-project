"""Residue correspondence from frozen D017 US-align output."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from evaluation.d017_construct_audit import (
    THREE_TO_ONE,
    parse_coordinate_residues,
)


def _residue_sequence(residues) -> str:
    """Return the one-letter sequence represented by ordered coordinate residues."""

    sequence = []
    for residue in residues:
        if residue.name not in THREE_TO_ONE:
            raise ValueError(
                f"Unsupported residue identity in receptor input: {residue.name}"
            )
        sequence.append(THREE_TO_ONE[residue.name])
    return "".join(sequence)


def parse_usalign_alignment(stdout_path: Path) -> tuple[str, str, str]:
    """Extract the two aligned sequences and annotation from US-align stdout."""

    lines = stdout_path.read_text().splitlines()

    marker = '(":" denotes residue pairs of d < 5.0 Angstrom'
    marker_indices = [
        i for i, line in enumerate(lines)
        if line.startswith(marker)
    ]
    if len(marker_indices) != 1:
        raise ValueError(
            f"Expected exactly one US-align alignment marker, found "
            f"{len(marker_indices)}"
        )

    start = marker_indices[0] + 1
    if start + 2 >= len(lines):
        raise ValueError("US-align alignment block is incomplete")

    target_alignment = lines[start].strip()
    annotation = lines[start + 1].rstrip("\n")
    homolog_alignment = lines[start + 2].strip()

    if not target_alignment or not homolog_alignment:
        raise ValueError("US-align alignment sequences are empty")

    if len(target_alignment) != len(homolog_alignment):
        raise ValueError("US-align aligned sequence lengths differ")

    if len(annotation) != len(target_alignment):
        raise ValueError(
            "US-align alignment annotation length differs from sequence length"
        )

    return target_alignment, annotation, homolog_alignment


def build_residue_correspondence(
    *,
    stdout_path: Path,
    target_receptor_cif: Path,
    target_chain: str,
    homolog_receptor_cif: Path,
    homolog_chain: str,
) -> dict[str, object]:
    """Build traceable deposited-residue correspondence from US-align output."""

    target_alignment, annotation, homolog_alignment = parse_usalign_alignment(
        stdout_path
    )

    target_residues = parse_coordinate_residues(
        target_receptor_cif, target_chain
    )
    homolog_residues = parse_coordinate_residues(
        homolog_receptor_cif, homolog_chain
    )

    target_sequence = _residue_sequence(target_residues)
    homolog_sequence = _residue_sequence(homolog_residues)

    if target_alignment.replace("-", "") != target_sequence:
        raise ValueError(
            "Ungapped US-align target sequence does not reproduce "
            "the target receptor input"
        )

    if homolog_alignment.replace("-", "") != homolog_sequence:
        raise ValueError(
            "Ungapped US-align homolog sequence does not reproduce "
            "the homolog receptor input"
        )

    target_index = 0
    homolog_index = 0
    columns = []

    for alignment_index, (target_aa, mark, homolog_aa) in enumerate(
        zip(target_alignment, annotation, homolog_alignment),
        start=1,
    ):
        if target_aa == "-" and homolog_aa == "-":
            raise ValueError(
                f"Invalid double-gap US-align column at {alignment_index}"
            )

        target_residue = None
        homolog_residue = None

        if target_aa != "-":
            target_residue = target_residues[target_index]
            expected = THREE_TO_ONE[target_residue.name]
            if target_aa != expected:
                raise ValueError(
                    f"Target residue mismatch at alignment column "
                    f"{alignment_index}: {target_aa} != {expected}"
                )
            target_index += 1

        if homolog_aa != "-":
            homolog_residue = homolog_residues[homolog_index]
            expected = THREE_TO_ONE[homolog_residue.name]
            if homolog_aa != expected:
                raise ValueError(
                    f"Homolog residue mismatch at alignment column "
                    f"{alignment_index}: {homolog_aa} != {expected}"
                )
            homolog_index += 1

        columns.append(
            {
                "alignment_column": alignment_index,
                "target_alignment_residue": target_aa,
                "homolog_alignment_residue": homolog_aa,
                "usalign_annotation": mark,
                "target_residue": (
                    asdict(target_residue)
                    if target_residue is not None
                    else None
                ),
                "homolog_residue": (
                    asdict(homolog_residue)
                    if homolog_residue is not None
                    else None
                ),
                "mapped_pair": (
                    target_residue is not None
                    and homolog_residue is not None
                ),
                "identical": (
                    target_residue is not None
                    and homolog_residue is not None
                    and target_aa == homolog_aa
                ),
            }
        )

    if target_index != len(target_residues):
        raise ValueError("Not all target receptor residues were consumed")

    if homolog_index != len(homolog_residues):
        raise ValueError("Not all homolog receptor residues were consumed")

    mapped_pairs = sum(column["mapped_pair"] for column in columns)

    return {
        "alignment_length": len(columns),
        "target_residue_count": len(target_residues),
        "homolog_residue_count": len(homolog_residues),
        "mapped_residue_pair_count": mapped_pairs,
        "columns": columns,
    }
