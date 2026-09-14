from pathlib import Path
import unittest

from evaluation.plip_witness import (
    load_plip_witness_config,
    summarize_plip_xml,
    summarize_qualification_panel,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT
    / "references/stage5/plip_witness/a2a_witness_config.json"
)


class PlipWitnessTests(unittest.TestCase):
    def setUp(self):
        self.config = load_plip_witness_config(
            CONFIG_PATH
        )

    def summarize_case(self, case):
        return summarize_plip_xml(
            ROOT / case["xml_path"],
            self.config,
            panel_id=case["panel_id"],
        )

    def configured_cases(self):
        return self.config["qualification_panel"]["cases"]

    def residue_id_for_requirement(self, interaction_class, direction=None):
        for role in self.config["configured_roles"]:
            for requirement in role["requires_any"]:
                if requirement["interaction_class"] != interaction_class:
                    continue

                if requirement.get("direction") == direction:
                    return role["residue_id"]

        raise AssertionError(
            "No configured role requirement found for "
            f"{interaction_class}:{direction}"
        )

    def requirement_for_class(self, interaction_class):
        for role in self.config["configured_roles"]:
            for requirement in role["requires_any"]:
                if requirement["interaction_class"] == interaction_class:
                    return role, requirement

        raise AssertionError(
            "No configured role requirement found for "
            f"{interaction_class}"
        )

    def test_qualification_panel_reproduces_all_positive_controls(self):
        summary = summarize_qualification_panel(
            self.config,
            base_path=ROOT,
        )

        self.assertEqual(
            summary["summary_count"],
            3,
        )
        self.assertEqual(
            summary["witness_reproduced_count"],
            3,
        )
        self.assertTrue(
            summary["witness_reproduced"]
        )

    def test_hydrophobic_and_pi_stacking_detection(self):
        cases = self.configured_cases()
        xac = self.summarize_case(
            cases[0]
        )
        vipadenant = self.summarize_case(
            cases[1]
        )
        aromatic_residue_id = self.residue_id_for_requirement(
            "Hydrophobic"
        )

        self.assertEqual(
            xac["observed_counts"][aromatic_residue_id]["by_class"]["Hydrophobic"],
            1,
        )
        self.assertEqual(
            xac["observed_counts"][aromatic_residue_id]["by_class"]["PiStacking"],
            1,
        )
        self.assertEqual(
            vipadenant["observed_counts"][aromatic_residue_id]["by_class"]["PiStacking"],
            2,
        )

    def test_hbond_directional_requirement_counts_only_configured_direction(self):
        cases = self.configured_cases()
        xac = self.summarize_case(
            cases[0]
        )
        hbond_role, hbond_requirement = self.requirement_for_class(
            "HydrogenBond"
        )
        hbond_residue_id = hbond_role["residue_id"]
        required_direction = hbond_requirement["direction"]

        counts = xac["observed_counts"][hbond_residue_id]
        hbond_roles = [
            role
            for role in xac["configured_role_reproduction"]
            if role["residue_id"] == hbond_residue_id
        ]

        self.assertEqual(
            counts["by_class_and_direction"]["HydrogenBond:protein_donor"],
            1,
        )
        self.assertEqual(
            counts["by_class_and_direction"]["HydrogenBond:ligand_donor"],
            1,
        )
        self.assertIn(
            f"HydrogenBond:{required_direction}",
            counts["by_class_and_direction"],
        )
        self.assertEqual(
            hbond_roles[0]["matched_count"],
            1,
        )
        self.assertTrue(
            hbond_roles[0]["reproduced"]
        )

    def test_multiple_interactions_at_one_residue_are_preserved(self):
        cases = self.configured_cases()
        tozadenant = self.summarize_case(
            cases[2]
        )
        aromatic_residue_id = self.residue_id_for_requirement(
            "PiStacking"
        )
        hbond_residue_id = self.residue_id_for_requirement(
            "HydrogenBond",
            direction=self.requirement_for_class(
                "HydrogenBond"
            )[1]["direction"],
        )

        self.assertEqual(
            tozadenant["observed_counts"][aromatic_residue_id]["by_class"]["PiStacking"],
            2,
        )
        self.assertEqual(
            tozadenant["observed_counts"][hbond_residue_id]["by_class"]["HydrogenBond"],
            3,
        )

    def test_selected_ligand_ignores_unrelated_hetero_compounds(self):
        cases = self.configured_cases()
        case_with_unrelated_ligands = cases[2]
        tozadenant = self.summarize_case(
            case_with_unrelated_ligands
        )

        self.assertEqual(
            {
                "hetid": tozadenant["selected_ligand"]["hetid"],
                "chain": tozadenant["selected_ligand"]["chain"],
                "position": tozadenant["selected_ligand"]["position"],
            },
            case_with_unrelated_ligands["ligand"],
        )
        self.assertGreater(
            len(tozadenant["ignored_ligands"]),
            0,
        )

        selected_key = (
            tozadenant["selected_ligand"]["hetid"],
            tozadenant["selected_ligand"]["chain"],
            tozadenant["selected_ligand"]["position"],
        )
        ignored_keys = {
            (
                ligand["hetid"],
                ligand["chain"],
                ligand["position"],
            )
            for ligand in tozadenant["ignored_ligands"]
        }

        self.assertNotIn(
            selected_key,
            ignored_keys,
        )

    def test_target_specific_definitions_are_loaded_from_config(self):
        role_ids = {
            role["role_id"]
            for role in self.config["configured_roles"]
        }
        residue_ids = {
            residue["residue_id"]
            for residue in self.config["configured_residues"]
        }
        cases = self.configured_cases()
        summary = self.summarize_case(
            cases[1]
        )

        self.assertEqual(
            role_ids,
            {
                role["role_id"]
                for role in summary["configured_role_reproduction"]
            },
        )
        self.assertEqual(
            residue_ids,
            set(summary["observed_counts"]),
        )


if __name__ == "__main__":
    unittest.main()
