from pathlib import Path
from urllib.request import urlopen

from rdkit import Chem
from rdkit.Geometry import Point3D
import prolif as plf

from test_native_reader_controls import (
    find_anchor_interactions,
    interaction_names,
    load_protein,
    run_interaction_reader,
)


RECEPTOR_PATH = Path(
    "experiments/phase1_diffsbdd/evaluation/"
    "prepared_3rfm_pocket_pH7.4_restored.pqr"
)

PDB_URL = "https://files.rcsb.org/download/3RFM.pdb"

# RCSB CCD CFF heavy-atom graph. Coordinates are replaced with the
# deposited 3RFM CFF heavy-atom coordinates before ProLIF is run.
CFF_ATOMS = [
    ("N1", "N", True),
    ("C2", "C", True),
    ("C10", "C", False),
    ("C6", "C", True),
    ("N3", "N", True),
    ("O11", "O", False),
    ("C12", "C", False),
    ("C4", "C", True),
    ("C5", "C", True),
    ("N9", "N", True),
    ("O13", "O", False),
    ("N7", "N", True),
    ("C8", "C", True),
    ("C14", "C", False),
]

CFF_BONDS = [
    ("N1", "C2", Chem.BondType.AROMATIC),
    ("N1", "C10", Chem.BondType.SINGLE),
    ("N1", "C6", Chem.BondType.AROMATIC),
    ("C2", "N3", Chem.BondType.AROMATIC),
    ("C2", "O11", Chem.BondType.DOUBLE),
    ("C6", "C5", Chem.BondType.AROMATIC),
    ("C6", "O13", Chem.BondType.DOUBLE),
    ("N3", "C12", Chem.BondType.SINGLE),
    ("N3", "C4", Chem.BondType.AROMATIC),
    ("C4", "C5", Chem.BondType.AROMATIC),
    ("C4", "N9", Chem.BondType.AROMATIC),
    ("C5", "N7", Chem.BondType.AROMATIC),
    ("N9", "C8", Chem.BondType.AROMATIC),
    ("N7", "C8", Chem.BondType.AROMATIC),
    ("N7", "C14", Chem.BondType.SINGLE),
]


def fetch_3rfm_pdb() -> str:
    with urlopen(PDB_URL) as response:
        return response.read().decode("utf-8")


def deposited_cff_coordinates(pdb_text: str) -> dict[str, tuple[float, float, float]]:
    coords = {}

    for line in pdb_text.splitlines():
        if not line.startswith("HETATM"):
            continue

        if line[17:20].strip() != "CFF":
            continue

        if line[21].strip() != "A":
            continue

        if int(line[22:26].strip()) != 330:
            continue

        element = line[76:78].strip().upper()
        if element == "H":
            continue

        atom_name = line[12:16].strip()
        coords[atom_name] = (
            float(line[30:38]),
            float(line[38:46]),
            float(line[46:54]),
        )

    expected = {name for name, _, _ in CFF_ATOMS}
    if set(coords) != expected:
        raise ValueError(
            "3RFM CFF atom-name mismatch: "
            f"missing={sorted(expected - set(coords))}; "
            f"extra={sorted(set(coords) - expected)}"
        )

    return coords


def build_native_cff(coords: dict[str, tuple[float, float, float]]):
    editable = Chem.RWMol()
    atom_indices = {}

    for name, element, aromatic in CFF_ATOMS:
        atom = Chem.Atom(element)
        atom.SetIsAromatic(aromatic)
        index = editable.AddAtom(atom)
        atom_indices[name] = index

    for atom_1, atom_2, bond_type in CFF_BONDS:
        editable.AddBond(
            atom_indices[atom_1],
            atom_indices[atom_2],
            bond_type,
        )

    mol = editable.GetMol()
    Chem.SanitizeMol(mol)

    conformer = Chem.Conformer(mol.GetNumAtoms())
    for name, _, _ in CFF_ATOMS:
        x, y, z = coords[name]
        conformer.SetAtomPosition(
            atom_indices[name],
            Point3D(x, y, z),
        )

    mol.AddConformer(conformer, assignId=True)
    mol.SetProp("_Name", "3RFM_CFF_native")

    # Generate only hydrogen coordinates; deposited heavy atoms remain fixed.
    return Chem.AddHs(mol, addCoords=True)


def main():
    if not RECEPTOR_PATH.is_file():
        raise FileNotFoundError(
            f"Interaction-ready 3RFM receptor not found: {RECEPTOR_PATH}"
        )

    pdb_text = fetch_3rfm_pdb()
    coords = deposited_cff_coordinates(pdb_text)
    ligand_rdkit = build_native_cff(coords)

    protein_results = load_protein(RECEPTOR_PATH)
    protein = protein_results["protein"]
    ligand = plf.Molecule.from_rdkit(ligand_rdkit)

    interactions = run_interaction_reader(protein, ligand)

    phe168 = find_anchor_interactions(
        interactions,
        "PHE",
        168,
    )
    asn253 = find_anchor_interactions(
        interactions,
        "ASN",
        253,
    )

    phe_classes = sorted(interaction_names(phe168))
    asn_classes = sorted(interaction_names(asn253))

    phe168_reproduced = (
        "Hydrophobic" in phe_classes
        or "PiStacking" in phe_classes
    )
    asn253_reproduced = "HBAcceptor" in asn_classes
    pattern_reproduced = phe168_reproduced and asn253_reproduced

    print("3RFM native CFF Stage-5 proof of life")
    print("=" * 72)
    print("Receptor:", RECEPTOR_PATH)
    print("Ligand source:", PDB_URL)
    print("Ligand:", "CFF / caffeine / chain A residue 330")
    print("Ligand heavy atoms:", ligand_rdkit.GetNumHeavyAtoms())
    print("Ligand total atoms:", ligand_rdkit.GetNumAtoms())
    print("Anchor numbering audit:", protein_results["anchor_audit"])
    print("Validated receptor hydrogens:", protein_results["validated_hydrogens"])
    print("Phe168 interaction classes:", phe_classes)
    print("Asn253 interaction classes:", asn_classes)
    print("Phe168 reference feature reproduced:", phe168_reproduced)
    print("Asn253 reference feature reproduced:", asn253_reproduced)
    print("Frozen A2A reference-recognition pattern reproduced:", pattern_reproduced)


if __name__ == "__main__":
    main()
