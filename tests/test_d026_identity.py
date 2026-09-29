import unittest

from evaluation.d026_identity import smiles_to_inchikey


class D026IdentityTests(unittest.TestCase):
    def test_ethanol_identity(self):
        self.assertEqual(
            smiles_to_inchikey("CCO"),
            "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
        )

    def test_invalid_smiles_rejected(self):
        with self.assertRaises(Exception):
            smiles_to_inchikey("not-a-valid-smiles")


if __name__ == "__main__":
    unittest.main()
