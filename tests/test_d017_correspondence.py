from pathlib import Path
import unittest

from evaluation.d017_correspondence import build_residue_correspondence


ROOT = Path(__file__).resolve().parents[1]


class D017CorrespondenceTests(unittest.TestCase):
    def test_p1_correspondence_consumes_exact_receptor_sequences(self):
        result = build_residue_correspondence(
            stdout_path=ROOT / (
                "references/stage5/d017/calibration_runs/P1/"
                "post_emitter_fix/stdout.txt"
            ),
            target_receptor_cif=ROOT / (
                "references/stage5/d017/receptor_inputs/2YDV_A.cif"
            ),
            target_chain="A",
            homolog_receptor_cif=ROOT / (
                "references/stage5/d017/receptor_inputs/6D9H_R.cif"
            ),
            homolog_chain="R",
        )

        self.assertEqual(result["alignment_length"], 314)
        self.assertEqual(result["target_residue_count"], 307)
        self.assertEqual(result["homolog_residue_count"], 288)

        # US-align reported aligned length = 281 for this frozen P1 run.
        self.assertEqual(result["mapped_residue_pair_count"], 281)

        self.assertEqual(
            sum(
                column["mapped_pair"]
                for column in result["columns"]
            ),
            281,
        )

        self.assertFalse(
            any(
                column["target_residue"] is None
                and column["homolog_residue"] is None
                for column in result["columns"]
            )
        )


if __name__ == "__main__":
    unittest.main()
