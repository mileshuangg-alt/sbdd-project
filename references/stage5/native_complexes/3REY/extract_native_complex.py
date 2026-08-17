from pathlib import Path

from Bio.PDB import PDBIO, PDBParser, Select


INPUT_PDB = Path(
    "references/stage5/native_complexes/3REY.pdb"
)

OUTPUT_DIR = Path(
    "references/stage5/native_complexes/3REY"
)

RECEPTOR_PDB = OUTPUT_DIR / "3REY_receptor_raw.pdb"
LIGAND_PDB = OUTPUT_DIR / "3REY_XAC_native_raw.pdb"

CHAIN_ID = "A"
LIGAND_NAME = "XAC"
LIGAND_NUMBER = 999


class ReceptorSelect(Select):
    """Keep only standard protein residues from chain A."""

    def accept_chain(self, chain):
        return chain.id == CHAIN_ID

    def accept_residue(self, residue):
        return residue.id[0] == " "


class LigandSelect(Select):
    """Keep only the crystallographic XAC ligand."""

    def accept_chain(self, chain):
        return chain.id == CHAIN_ID

    def accept_residue(self, residue):
        return (
            residue.get_resname() == LIGAND_NAME
            and residue.id[1] == LIGAND_NUMBER
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(
        "3REY",
        str(INPUT_PDB),
    )

    io = PDBIO()
    io.set_structure(structure)

    io.save(
        str(RECEPTOR_PDB),
        ReceptorSelect(),
    )

    io.save(
        str(LIGAND_PDB),
        LigandSelect(),
    )

    print(f"Raw receptor written: {RECEPTOR_PDB}")
    print(f"Native XAC written: {LIGAND_PDB}")


if __name__ == "__main__":
    main()
