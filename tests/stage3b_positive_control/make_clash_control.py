from pathlib import Path

from Bio.PDB import PDBParser
from rdkit import Chem


INPUT_SDF = Path(
    "experiments/phase1_diffsbdd/evaluation/stage3_input.sdf"
)

POCKET_PDB = Path(
    "experiments/phase1_diffsbdd/evaluation/prepared_3rfm_pocket.pdb"
)

OUTPUT_SDF = Path(
    "tests/stage3b_positive_control/"
    "stage3b_forced_clash_control.sdf"
)

SOURCE_MOLECULE_ID = 0


def main():
    """Create a Stage 3B positive control with a forced protein clash."""

    supplier = Chem.SDMolSupplier(
        str(INPUT_SDF),
        sanitize=False,
        removeHs=False,
    )

    source_mol = None

    for mol in supplier:
        if mol is None:
            continue

        if (
            mol.HasProp("molecule_id")
            and int(mol.GetProp("molecule_id")) == SOURCE_MOLECULE_ID
        ):
            source_mol = Chem.Mol(mol)
            break

    if source_mol is None:
        raise ValueError(
            f"Could not find molecule_id {SOURCE_MOLECULE_ID}"
        )

    structure = PDBParser(QUIET=True).get_structure(
        "pocket",
        str(POCKET_PDB),
    )

    # Use the first protein atom in the prepared pocket as an
    # explicit steric-clash target.
    target_atom = next(structure.get_atoms())
    target_coord = target_atom.get_coord()

    residue = target_atom.get_parent()
    chain = residue.get_parent()

    conformer = source_mol.GetConformer()

    # Translate the entire ligand rigidly so ligand atom 0 lies
    # directly on top of the selected protein atom.
    ligand_coord = conformer.GetAtomPosition(0)

    dx = float(target_coord[0]) - ligand_coord.x
    dy = float(target_coord[1]) - ligand_coord.y
    dz = float(target_coord[2]) - ligand_coord.z

    for atom_index in range(source_mol.GetNumAtoms()):
        position = conformer.GetAtomPosition(atom_index)

        conformer.SetAtomPosition(
            atom_index,
            (
                position.x + dx,
                position.y + dy,
                position.z + dz,
            ),
        )

    source_mol.SetProp(
        "control_type",
        "stage3b_forced_protein_ligand_clash",
    )
    source_mol.SetProp(
        "source_molecule_id",
        str(SOURCE_MOLECULE_ID),
    )
    source_mol.SetProp(
        "target_chain",
        str(chain.id),
    )
    source_mol.SetProp(
        "target_residue",
        f"{residue.get_resname()}_{residue.id[1]}",
    )
    source_mol.SetProp(
        "target_protein_atom",
        target_atom.get_name(),
    )

    OUTPUT_SDF.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    writer = Chem.SDWriter(str(OUTPUT_SDF))
    writer.write(source_mol)
    writer.close()

    print(f"Control written: {OUTPUT_SDF}")
    print(f"Source molecule ID: {SOURCE_MOLECULE_ID}")
    print(
        "Forced clash target: "
        f"chain {chain.id}, "
        f"{residue.get_resname()} {residue.id[1]}, "
        f"atom {target_atom.get_name()}"
    )
    print(
        "Ligand atom 0 translated directly onto "
        "the target protein atom."
    )


if __name__ == "__main__":
    main()
