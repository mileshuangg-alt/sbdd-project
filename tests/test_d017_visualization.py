from pathlib import Path
import tempfile
import unittest

from evaluation.d017_visualization import write_whole_structure_pml


class D017VisualizationTests(unittest.TestCase):
    def test_whole_structure_review_pml_is_deterministic_and_non_destructive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_pml = root / "review.pml"
            output_png = root / "review.png"

            kwargs = {
                "superposition_cif": Path("superposition.cif"),
                "reference_cif": Path("reference.cif"),
                "superposition_chain": "X",
                "reference_chain": "Y",
                "output_png": output_png,
                "output_pml": output_pml,
            }

            write_whole_structure_pml(**kwargs)
            first = output_pml.read_text()
            write_whole_structure_pml(**kwargs)

            self.assertEqual(first, output_pml.read_text())

            self.assertIn("load superposition.cif, structure1", first)
            self.assertIn("load reference.cif, structure2", first)
            self.assertIn("remove structure1 and not chain X", first)
            self.assertIn("remove structure2 and not chain Y", first)

            self.assertIn("show cartoon, structure1", first)
            self.assertIn("show cartoon, structure2", first)
            self.assertIn("color blue, structure1", first)
            self.assertIn("color red, structure2", first)
            self.assertIn("set cartoon_transparency, 0.55, structure1", first)
            self.assertIn("set cartoon_transparency, 0.20, structure2", first)

            self.assertIn("set cartoon_oval_width, 0.20", first)
            self.assertIn("set cartoon_loop_radius, 0.12", first)
            self.assertIn("bg_color white", first)
            self.assertIn("set ray_shadow, 0", first)
            self.assertIn("ray 1800, 1800", first)

            self.assertNotIn("remove not n. CA", first)
            self.assertNotIn("run ", first)


if __name__ == "__main__":
    unittest.main()
