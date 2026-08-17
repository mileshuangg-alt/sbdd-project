from pathlib import Path

import numpy as np
from Bio.PDB import PDBParser
from rdkit import Chem
from rdkit.Geometry import Point3D


TEMPLATE_SDF = Path(
    "references/stage5/native_complexes/3REY/XAC_ideal.sdf"
)

CRYSTAL_PDB = Path(
    "references/stage5/native_complexes/3REY/"
    "3REY_XAC_native_raw.pdb"
)

OUTPUT_SDF = Path(
    "references/stage5/native_complexes/3REY/"
    "3REY_XAC_native_chemistry.sdf"
)


def main():
    """Combine authoritative XAC chemistry with native 3REY coordinates."""

    # Load the authoritative RCSB chemical definition.
    template = Chem.SDMolSupplier(
        str(TEMPLATE_SDF),
        removeHs=False,
    )[0]

    if template is None:
        raise ValueError("Failed to load authoritative XAC template.")

    # Remove template hydrogens.
    #
    # We want the 31 authoritative heavy atoms here. Hydrogens will be
    # assigned later under the frozen pH 7.4 preparation policy.
    ligand = Chem.RemoveHs(template)

    # Load the crystallographic XAC coordinates.
    parser = PDBParser(QUIET=True)
    crystal = parser.get_structure(
        "XAC",
        str(CRYSTAL_PDB),
    )

    crystal_atoms = list(crystal.get_atoms())

    if ligand.GetNumAtoms() != len(crystal_atoms):
        raise ValueError(
            "Heavy-atom count mismatch: "
            f"template={ligand.GetNumAtoms()}, "
            f"crystal={len(crystal_atoms)}"
        )

    # Verify element-by-element correspondence before transferring
    # any coordinates.
    template_elements = [
        atom.GetSymbol()
        for atom in ligand.GetAtoms()
    ]

    crystal_elements = [
        atom.element.strip()
        for atom in crystal_atoms
    ]

    if template_elements != crystal_elements:
        raise ValueError(
            "Template/crystal element ordering does not match."
        )

    # Preserve the original crystal coordinates for the audit.
    crystal_coords = np.array(
        [atom.coord for atom in crystal_atoms],
        dtype=float,
    )

    # Replace the idealized RCSB coordinates with the deposited
    # 3REY coordinates.
    conformer = Chem.Conformer(ligand.GetNumAtoms())

    for atom_index, coord in enumerate(crystal_coords):
        conformer.SetAtomPosition(
            atom_index,
            Point3D(
                float(coord[0]),
                float(coord[1]),
                float(coord[2]),
            ),
        )

    ligand.RemoveAllConformers()
    ligand.AddConformer(
        conformer,
        assignId=True,
    )

    # Confirm that authoritative chemistry still sanitizes.
    Chem.SanitizeMol(ligand)

    ligand.SetProp("_Name", "3REY_XAC_native")
    ligand.SetProp("source_pdb", "3REY")
    ligand.SetProp("source_ligand", "XAC")
    ligand.SetProp("source_residue", "A:999")
    ligand.SetProp(
        "coordinate_provenance",
        "deposited_3REY_XAC_coordinates",
    )
    ligand.SetProp(
        "chemistry_provenance",
        "RCSB_XAC_ideal_chemical_component",
    )

    writer = Chem.SDWriter(str(OUTPUT_SDF))
    writer.write(ligand)
    writer.close()

    # Reload the written artifact and verify that serialization
    # itself did not alter coordinates.
    written = Chem.SDMolSupplier(
        str(OUTPUT_SDF),
        removeHs=False,
    )[0]

    if written is None:
        raise ValueError("Failed to reload written XAC SDF.")

    written_coords = written.GetConformer().GetPositions()

    differences = np.linalg.norm(
        written_coords - crystal_coords,
        axis=1,
    )

    max_difference = float(differences.max())

    canonical_smiles = Chem.MolToSmiles(
        written,
        canonical=True,
        isomericSmiles=True,
    )

    print(f"Output: {OUTPUT_SDF}")
    print(f"Heavy atoms: {written.GetNumHeavyAtoms()}")
    print(f"Bonds: {written.GetNumBonds()}")
    print(f"Canonical SMILES: {canonical_smiles}")
    print(
        "Max crystal-coordinate difference: "
        f"{max_difference:.6f} Å"
    )

    if max_difference > 1e-4:
        raise ValueError(
            "Written XAC coordinates do not exactly match "
            "the crystallographic coordinates."
        )

    print(
        "PASS: authoritative XAC chemistry combined with "
        "3REY coordinates preserved within SDF serialization precision."
    )


if __name__ == "__main__":
    main()
