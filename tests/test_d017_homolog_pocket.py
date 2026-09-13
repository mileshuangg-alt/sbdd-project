from pathlib import Path
import unittest

from evaluation.d017_homolog_pocket import identify_pocket_residues
from evaluation.pocket_models import ResidueID


class D017HomologPocketTests(unittest.TestCase):
    def test_identify_pocket_residues_applies_frozen_cutoff(self):
        receptor_atoms = (
            {
                "_atom_site.auth_asym_id": "R",
                "_atom_site.auth_seq_id": "87",
                "_atom_site.auth_comp_id": "VAL",
                "_atom_site.pdbx_PDB_ins_code": "?",
                "_atom_site.type_symbol": "C",
                "_atom_site.Cartn_x": "0.0",
                "_atom_site.Cartn_y": "0.0",
                "_atom_site.Cartn_z": "0.0",
            },
            {
                "_atom_site.auth_asym_id": "R",
                "_atom_site.auth_seq_id": "87",
                "_atom_site.auth_comp_id": "VAL",
                "_atom_site.pdbx_PDB_ins_code": "?",
                "_atom_site.type_symbol": "C",
                "_atom_site.Cartn_x": "1.0",
                "_atom_site.Cartn_y": "0.0",
                "_atom_site.Cartn_z": "0.0",
            },
            {
                "_atom_site.auth_asym_id": "R",
                "_atom_site.auth_seq_id": "88",
                "_atom_site.auth_comp_id": "LEU",
                "_atom_site.pdbx_PDB_ins_code": "?",
                "_atom_site.type_symbol": "C",
                "_atom_site.Cartn_x": "4.5",
                "_atom_site.Cartn_y": "0.0",
                "_atom_site.Cartn_z": "0.0",
            },
            {
                "_atom_site.auth_asym_id": "R",
                "_atom_site.auth_seq_id": "91",
                "_atom_site.auth_comp_id": "THR",
                "_atom_site.pdbx_PDB_ins_code": "?",
                "_atom_site.type_symbol": "C",
                "_atom_site.Cartn_x": "4.51",
                "_atom_site.Cartn_y": "0.0",
                "_atom_site.Cartn_z": "0.0",
            },
        )

        ligand_atoms = (
            {
                "_atom_site.Cartn_x": "0.0",
                "_atom_site.Cartn_y": "0.0",
                "_atom_site.Cartn_z": "0.0",
            },
        )

        pocket = identify_pocket_residues(
            receptor_heavy_atoms=receptor_atoms,
            ligand_heavy_atoms=ligand_atoms,
            cutoff=4.5,
        )

        self.assertEqual(
            pocket,
            (
                ResidueID(
                    chain="R",
                    number="87",
                    insertion_code="",
                    name="VAL",
                ),
                ResidueID(
                    chain="R",
                    number="88",
                    insertion_code="",
                    name="LEU",
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
