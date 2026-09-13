"""Lossless position-only D017 receptor-input materialization."""

from dataclasses import asdict
from pathlib import Path

from evaluation.d017_construct_audit import (
    THREE_TO_ONE,
    _read_loop,
    audit_construct,
    parse_coordinate_atoms,
    parse_coordinate_residues,
    sha256_file,
)


def _write_mmcif_atoms(
    *,
    output_path: Path,
    structure_id: str,
    author_chain: str,
    atoms: tuple[dict[str, str], ...],
) -> None:
    """Write source atom-site values without numeric conversion or rounding."""

    columns = list(atoms[0]) if atoms else []
    if not columns:
        raise ValueError("Cannot materialize an empty receptor input")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                f"data_{structure_id}_{author_chain}_D017_RECEPTOR",
                "#",
                "loop_",
                *(f"{column} " for column in columns),
                *(" ".join(atom[column] for column in columns) for atom in atoms),
                "#",
            ]
        )
        + "\n"
    )


def _validate_exact_atom_preservation(
    *,
    output_path: Path,
    source_atoms: tuple[dict[str, str], ...],
) -> None:
    """Verify output atom records are ordered, traceable, and coordinate-exact."""

    output_atoms = tuple(_read_loop(output_path, "_atom_site."))
    if len(output_atoms) != len(source_atoms):
        raise ValueError(
            "Output mmCIF atom count differs from selected source atoms")
    identity_fields = (
        "_atom_site.id",
        "_atom_site.auth_asym_id",
        "_atom_site.auth_seq_id",
        "_atom_site.pdbx_PDB_ins_code",
        "_atom_site.auth_comp_id",
        "_atom_site.auth_atom_id",
        "_atom_site.label_seq_id",
    )
    coordinate_fields = (
        "_atom_site.Cartn_x",
        "_atom_site.Cartn_y",
        "_atom_site.Cartn_z",
    )
    for source, output in zip(source_atoms, output_atoms):
        if any(source[field] != output[field] for field in identity_fields):
            raise ValueError(
                "Output atom identity is not traceable to the source mmCIF")
        if any(source[field] != output[field] for field in coordinate_fields):
            raise ValueError(
                "Output atom coordinates differ from the source mmCIF")


def extract_receptor_mmcif(
    *,
    structure_id: str,
    structure_path: Path,
    author_chain: str,
    fasta_path: Path,
    output_path: Path,
) -> dict[str, object]:
    """Materialize canonical-position-mapped receptor coordinates as mmCIF."""

    audit = audit_construct(
        structure_id=structure_id,
        structure_path=structure_path,
        author_chain=author_chain,
        fasta_path=fasta_path,
    )
    if audit["status"] != "PASS":
        raise ValueError(
            f"Cannot extract an ambiguous receptor mapping for {structure_id}")
    atoms = parse_coordinate_atoms(structure_path, author_chain)
    atoms_by_position: dict[int, list[dict[str, str]]] = {}
    for atom in atoms:
        atoms_by_position.setdefault(
            int(atom["_atom_site.label_seq_id"]), []).append(atom)
    mappings = []
    mapped_positions = set()
    for mapping in audit["construct_to_canonical_mapping"]:
        deposited = mapping["author_residue"]
        position = deposited["label_sequence_id"]
        mapped_positions.add(position)
        deposited_residue = deposited["name"]
        deposited_letter = THREE_TO_ONE.get(deposited_residue)
        if deposited_letter is None:
            raise ValueError(
                f"Unsupported deposited residue identity: {deposited_residue}")
        mappings.append(
            {
                "deposited_author_residue": deposited,
                "deposited_residue": deposited_residue,
                "canonical_position": mapping["canonical_position"],
                "canonical_residue": mapping["canonical_residue"],
                "mutation_flag": deposited_letter != mapping["canonical_residue"],
                "mapping_status": "UNIQUE_CANONICAL_POSITION",
                "source_atom_ids": [
                    int(atom["_atom_site.id"])
                    for atom in atoms_by_position[position]
                ],
            }
        )
    unmapped_positions = {residue["label_sequence_id"]
                          for residue in audit["unmapped_coordinate_residues"]}
    excluded = []
    for residue in parse_coordinate_residues(structure_path, author_chain):
        if residue.label_sequence_id in mapped_positions:
            continue
        excluded.append(
            {
                "deposited_author_residue": asdict(residue),
                "deposited_residue": residue.name,
                "mapping_status": (
                    "UNMAPPED_COORDINATE_POSITION"
                    if residue.label_sequence_id in unmapped_positions
                    else "NONCANONICAL_COORDINATE_POSITION"
                ),
                "source_atom_ids": [
                    int(atom["_atom_site.id"])
                    for atom in atoms_by_position[residue.label_sequence_id]
                ],
            }
        )
    selected_atoms = tuple(atom for atom in atoms if int(
        atom["_atom_site.label_seq_id"]) in mapped_positions)
    _write_mmcif_atoms(
        output_path=output_path,
        structure_id=structure_id,
        author_chain=author_chain,
        atoms=selected_atoms,
    )
    _validate_exact_atom_preservation(
        output_path=output_path,
        source_atoms=selected_atoms)
    return {
        "structure_id": structure_id,
        "source_structure": audit["source_mmcif"],
        "selected_author_chain": author_chain,
        "canonical_sequence": {
            "accession": audit["canonical_receptor"]["accession"],
            **audit["canonical_fasta"],
        },
        "residue_mappings": mappings,
        "excluded_coordinate_bearing_residues": excluded,
        "mapped_coordinate_bearing_residue_count": len(mappings),
        "excluded_coordinate_bearing_residue_count": len(excluded),
        "output_receptor_mmcif": {
            "path": str(output_path),
            "sha256": sha256_file(output_path),
            "atom_count": len(selected_atoms),
        },
    }
