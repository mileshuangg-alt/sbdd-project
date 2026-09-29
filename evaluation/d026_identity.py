from __future__ import annotations

from aizynthfinder.chem import Molecule


def smiles_to_inchikey(smiles: str) -> str:
    """Return the D026 identity InChIKey for one source SMILES.

    Identity is computed exclusively through the frozen D026
    AiZynthFinder/RDKit environment. Source-provided InChIKeys are not
    consulted by this transformation.
    """
    molecule = Molecule(smiles=smiles, sanitize=True)
    inchikey = molecule.inchi_key

    if not inchikey:
        raise ValueError("SMILES produced no InChIKey")

    return inchikey
