"""Frozen D017 4.5-Angstrom mutation-pocket audit."""

from math import dist
from pathlib import Path

from evaluation.d017_construct_audit import _read_loop, sha256_file


POCKET_DISTANCE_ANGSTROM = 4.5


def _atom_identifier(atom: dict[str, str]) -> dict[str, str]:
    return {
        "atom_site_id": atom["_atom_site.id"],
        "group": atom["_atom_site.group_PDB"],
        "element": atom["_atom_site.type_symbol"],
        "author_component": atom["_atom_site.auth_comp_id"],
        "author_chain": atom["_atom_site.auth_asym_id"],
        "author_residue_number": atom["_atom_site.auth_seq_id"],
        "author_insertion_code": atom["_atom_site.pdbx_PDB_ins_code"],
        "author_atom": atom["_atom_site.auth_atom_id"],
        "label_chain": atom["_atom_site.label_asym_id"],
        "label_sequence_id": atom["_atom_site.label_seq_id"],
        "coordinates": [
            atom["_atom_site.Cartn_x"],
            atom["_atom_site.Cartn_y"],
            atom["_atom_site.Cartn_z"],
        ],
    }


def _coordinates(atom: dict[str, str]) -> tuple[float, float, float]:
    return tuple(
        float(atom[field])
        for field in ("_atom_site.Cartn_x", "_atom_site.Cartn_y", "_atom_site.Cartn_z")
    )


def _parse_ligand_instance(instance: str) -> tuple[str, str, str]:
    fields = instance.split()
    if len(fields) != 3:
        raise ValueError(f"Unsupported frozen ligand instance: {instance!r}")
    return tuple(fields)


def ligand_instances_by_structure(manifest: dict[str, object]) -> dict[tuple[str, str], tuple[str, str, str]]:
    """Read the frozen manifest ligand instance for each selected chain."""

    values: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    for row in manifest["rows"]:
        for role in ("target", "homolog"):
            key = (row[f"{role}_pdb"], row[f"{role}_chain"])
            values.setdefault(key, set()).add(
                _parse_ligand_instance(row[f"{role}_ligand_instance"])
            )
    result = {}
    for key, instances in values.items():
        if len(instances) != 1:
            raise ValueError(f"Ambiguous frozen ligand instance for {key}")
        result[key] = instances.pop()
    return result


def audit_mutation_pocket(
    *,
    structure_id: str,
    author_chain: str,
    structure_path: Path,
    ligand_instance: tuple[str, str, str],
    mutation: dict[str, object],
) -> dict[str, object]:
    """Audit one mapped mutation against its frozen ligand instance."""

    rows = _read_loop(structure_path, "_atom_site.")
    component, ligand_chain, ligand_number = ligand_instance
    ligand_atoms = tuple(
        atom for atom in rows
        if atom["_atom_site.auth_comp_id"] == component
        and atom["_atom_site.auth_asym_id"] == ligand_chain
        and atom["_atom_site.auth_seq_id"] == ligand_number
        and atom["_atom_site.type_symbol"] != "H"
    )
    if not ligand_atoms:
        raise ValueError(f"Frozen ligand instance is absent from {structure_path}")
    residue = mutation["deposited_author_residue"]
    source_atom_ids = {str(value) for value in mutation["source_atom_ids"]}
    residue_atoms = tuple(
        atom for atom in rows
        if atom["_atom_site.id"] in source_atom_ids and atom["_atom_site.type_symbol"] != "H"
    )
    if not residue_atoms:
        raise ValueError("Mutation mapping has no traceable source heavy atoms")
    if any(atom["_atom_site.auth_asym_id"] != author_chain for atom in residue_atoms):
        raise ValueError("Mutation source atoms do not preserve the selected author chain")
    minimum, receptor_atom, ligand_atom = min(
        (
            dist(_coordinates(receptor_atom), _coordinates(ligand_atom)),
            receptor_atom,
            ligand_atom,
        )
        for receptor_atom in residue_atoms
        for ligand_atom in ligand_atoms
    )
    return {
        "structure_id": structure_id,
        "selected_author_chain": author_chain,
        "ligand_instance": {
            "component": component,
            "author_chain": ligand_chain,
            "author_residue_number": ligand_number,
        },
        "mutation": {
            "deposited_author_residue": residue,
            "deposited_residue": mutation["deposited_residue"],
            "canonical_position": mutation["canonical_position"],
            "canonical_residue": mutation["canonical_residue"],
            "mutation_flag": mutation["mutation_flag"],
            "mapping_status": mutation["mapping_status"],
            "source_atom_ids": mutation["source_atom_ids"],
        },
        "pocket_distance_cutoff_angstrom": POCKET_DISTANCE_ANGSTROM,
        "minimum_heavy_atom_distance_angstrom": minimum,
        "in_ligand_defined_pocket": minimum <= POCKET_DISTANCE_ANGSTROM,
        "minimum_distance_pair": {
            "receptor_atom": _atom_identifier(receptor_atom),
            "ligand_atom": _atom_identifier(ligand_atom),
        },
        "source_mmcif": {"path": str(structure_path), "sha256": sha256_file(structure_path)},
    }
