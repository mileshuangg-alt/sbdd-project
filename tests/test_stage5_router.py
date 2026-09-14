from pathlib import Path
import unittest

from evaluation.stage5 import (
    HOMOLOGY_INFERRED_LABEL,
    INTERACTION_UNVERIFIED_FLAG,
    LEVEL1_ROUTE,
    LEVEL2_ROUTE,
    LEVEL3_ROUTE,
    OUT_OF_SCOPE_ROUTE,
    build_stage5_report,
    load_stage5_target_config,
    validate_target_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET_CONFIG_DIR = (
    ROOT
    / "references/stage5/target_configs"
)
STAGE5_MODULE_PATH = ROOT / "evaluation/stage5.py"


def load_existing_level1_config():
    for config_path in sorted(
        TARGET_CONFIG_DIR.glob("*.json")
    ):
        config = load_stage5_target_config(
            config_path
        )
        if config["evidence"].get(
            "cognate_complex_available"
        ):
            return config

    raise AssertionError(
        "No existing Level-1 Stage-5 target config found."
    )


class Stage5RouterTests(unittest.TestCase):
    def test_no_structure_routes_out_of_scope(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_no_structure",
                "evidence": {
                    "structure_available": False,
                    "gate_validation": None,
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        self.assertIsNone(
            report["target_record"]["evidence"]["evidence_level"]
        )
        self.assertEqual(
            ruling["route"],
            OUT_OF_SCOPE_ROUTE,
        )
        self.assertEqual(
            ruling["verdict"],
            OUT_OF_SCOPE_ROUTE,
        )

    def test_level1_routes_to_configured_implementation_authority(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level1",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": True,
                    "gate_validation": "ESTABLISHED",
                },
                "interaction_implementation": {
                    "implementation_id": "frozen_reader",
                    "artifact_path": "artifacts/frozen_reader.csv",
                    "authority": {
                        "gate_validation": "NOT_ESTABLISHED",
                        "molecule_level_claims": True,
                        "hard_attrition": False,
                        "pose_level_claims": False,
                        "general_specificity": False,
                        "claims_status": (
                            "claims capped pending gate validation"
                        ),
                    },
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        self.assertEqual(
            ruling["route"],
            LEVEL1_ROUTE,
        )
        self.assertEqual(
            ruling["gate_validation"],
            "NOT_ESTABLISHED",
        )
        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )
        self.assertTrue(
            ruling["level1_authority"]["molecule_level_claims"]
        )
        self.assertFalse(
            ruling["level1_authority"]["pose_level_claims"]
        )
        self.assertEqual(
            ruling["claims_cap"],
            "claims capped pending gate validation",
        )
        self.assertEqual(
            ruling["target_specific_implementation"]["authority"]["claims_status"],
            "claims capped pending gate validation",
        )

    def test_level1_established_validation_with_bounded_authority(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level1_bounded",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": True,
                    "gate_validation": "ESTABLISHED",
                },
                "interaction_implementation": {
                    "implementation_id": "frozen_reader",
                    "authority": {
                        "gate_validation": "ESTABLISHED",
                        "molecule_level_claims": True,
                        "hard_attrition": False,
                        "pose_level_claims": False,
                        "general_specificity": False,
                    },
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        self.assertEqual(
            ruling["gate_validation"],
            "ESTABLISHED",
        )
        self.assertEqual(
            ruling["claims_mode"],
            "molecule_level_claims",
        )
        self.assertTrue(
            ruling["level1_authority"]["molecule_level_claims"]
        )
        self.assertFalse(
            ruling["level1_authority"]["hard_attrition"]
        )
        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )

    def test_established_validation_does_not_grant_hard_attrition(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level1_status_only",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": True,
                    "gate_validation": "ESTABLISHED",
                },
                "interaction_implementation": {
                    "implementation_id": "frozen_reader",
                    "authority": {
                        "gate_validation": "ESTABLISHED"
                    },
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        self.assertEqual(
            ruling["gate_validation"],
            "ESTABLISHED",
        )
        self.assertFalse(
            ruling["level1_authority"]["hard_attrition"]
        )
        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )

    def test_absent_authority_defaults_conservatively(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level1_absent_authority",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": True,
                    "gate_validation": "ESTABLISHED",
                },
                "interaction_implementation": {
                    "implementation_id": "frozen_reader"
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        for field in [
            "molecule_level_claims",
            "hard_attrition",
            "pose_level_claims",
            "general_specificity",
        ]:
            self.assertFalse(
                ruling["level1_authority"][field]
            )

        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )
        self.assertEqual(
            ruling["claims_cap"],
            "claims not authorized by frozen implementation authority",
        )

    def test_level2_homolog_route_derives_d018_conservation(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level2_homolog",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": False,
                    "apo_structure_available": False,
                    "homolog_complex_available": True,
                    "mapping_coverage": 1.0,
                    "mapped_pocket_residue_count": 14,
                    "pocket_superposition_rmsd": 0.4398073045565676,
                    "gate_validation": None,
                },
            }
        )

        evidence = report["target_record"]["evidence"]
        ruling = report["target_record"]["ruling"]

        self.assertTrue(
            evidence["level2_pocket_eligible"]
        )
        self.assertTrue(
            evidence["pocket_conserved"]
        )
        self.assertFalse(
            evidence["d018_conservation_rule"]["sequence_identity_used"]
        )

        self.assertEqual(
            ruling["route"],
            LEVEL2_ROUTE,
        )
        self.assertEqual(
            ruling["claims_mode"],
            "interaction_characterization",
        )
        self.assertIn(
            HOMOLOGY_INFERRED_LABEL,
            ruling["labels"],
        )
        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )

    def test_level2_apo_route_does_not_add_homology_label(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level2_apo",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": False,
                    "apo_structure_available": True,
                    "homolog_complex_available": False,
                    "gate_validation": None,
                },
            }
        )
        ruling = report["target_record"]["ruling"]

        self.assertEqual(
            ruling["route"],
            LEVEL2_ROUTE,
        )
        self.assertNotIn(
            HOMOLOGY_INFERRED_LABEL,
            ruling["labels"],
        )

    def test_level2_homolog_rejects_nonconserved_d018_measurements(self):
        with self.assertRaisesRegex(
            ValueError,
            "pocket_conserved to be True",
        ):
            build_stage5_report(
                {
                    "schema_version": 1,
                    "target_id": "test_level2_bad_homolog",
                    "evidence": {
                        "structure_available": True,
                        "cognate_complex_available": False,
                        "apo_structure_available": True,
                        "homolog_complex_available": True,
                        "mapping_coverage": 1.0,
                        "mapped_pocket_residue_count": 14,
                        "pocket_superposition_rmsd": 0.634376810782047,
                        "pocket_conserved": True,
                        "gate_validation": None,
                    },
                }
            )

    def test_gate_validation_message_lists_none_as_accepted(self):
        validation = validate_target_evidence(
            {
                "structure_available": True,
                "evidence_level": 3,
                "gate_validation": "UNKNOWN",
            }
        )

        self.assertIn(
            "Gate validation must be None, ESTABLISHED, "
            "or NOT_ESTABLISHED.",
            validation["errors"],
        )

        with self.assertRaisesRegex(
            ValueError,
            "None, ESTABLISHED, or NOT_ESTABLISHED",
        ):
            build_stage5_report(
                {
                    "schema_version": 1,
                    "target_id": "test_bad_authority_status",
                    "evidence": {
                        "structure_available": True,
                        "cognate_complex_available": True,
                        "gate_validation": None,
                    },
                    "interaction_implementation": {
                        "implementation_id": "frozen_reader",
                        "authority": {
                            "gate_validation": "UNKNOWN"
                        },
                    },
                }
            )

    def test_level3_verdict_lane_and_flag_propagate(self):
        report = build_stage5_report(
            {
                "schema_version": 1,
                "target_id": "test_level3",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": False,
                    "apo_structure_available": False,
                    "homolog_complex_available": False,
                    "pocket_conserved": False,
                    "gate_validation": None,
                },
            },
            molecule_records=[
                {
                    "molecule_id": "mol-1",
                    "stage3_geometry_verdict": "PASS",
                }
            ],
        )
        ruling = report["target_record"]["ruling"]
        molecule = report["molecules"][0]

        self.assertEqual(
            ruling["route"],
            LEVEL3_ROUTE,
        )
        self.assertEqual(
            ruling["verdict"],
            "INCONCLUSIVE",
        )
        self.assertEqual(
            ruling["lane"],
            "evaluation_continues",
        )
        self.assertIn(
            INTERACTION_UNVERIFIED_FLAG,
            ruling["flags"],
        )
        self.assertTrue(
            molecule["interaction_unverified"]
        )
        self.assertEqual(
            molecule["stage3_geometry_verdict"],
            "PASS",
        )
        self.assertEqual(
            molecule["stage5_reporting_bucket"],
            "interaction_unverified_separate_count",
        )

    def test_existing_level1_artifact_preserves_claim_boundary(self):
        config = load_existing_level1_config()
        report = build_stage5_report(
            config
        )
        ruling = report["target_record"]["ruling"]

        self.assertEqual(
            report["target_record"]["evidence"]["evidence_level"],
            1,
        )
        self.assertEqual(
            ruling["route"],
            LEVEL1_ROUTE,
        )
        self.assertEqual(
            ruling["gate_validation"],
            "NOT_ESTABLISHED",
        )
        self.assertFalse(
            ruling["hard_attrition_permitted"]
        )
        self.assertTrue(
            ruling["level1_authority"]["molecule_level_claims"]
        )
        self.assertFalse(
            ruling["level1_authority"]["hard_attrition"]
        )
        self.assertFalse(
            ruling["level1_authority"]["pose_level_claims"]
        )
        self.assertFalse(
            ruling["level1_authority"]["general_specificity"]
        )
        self.assertEqual(
            ruling["claims_cap"],
            "claims capped pending gate validation",
        )

    def test_generic_router_contains_no_target_specific_constants(self):
        config = load_existing_level1_config()
        source = STAGE5_MODULE_PATH.read_text()
        target_tokens = {
            config["target_id"],
            config["interaction_implementation"]["instrument"],
        }

        for complex_record in config["evidence"][
            "evidence_provenance"
        ]["experimental_complexes"]:
            target_tokens.add(
                complex_record["pdb_id"]
            )
            target_tokens.add(
                complex_record["ligand_name"]
            )

        for role in config["interaction_implementation"][
            "frozen_definition_artifact"
        ]["configured_roles"]:
            target_tokens.add(
                role["residue"]["name"]
            )
            target_tokens.add(
                str(role["residue"]["number"])
            )

        for token in target_tokens:
            self.assertNotIn(
                token,
                source,
            )


if __name__ == "__main__":
    unittest.main()
