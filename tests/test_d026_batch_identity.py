import csv
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.d026_batch_identity import (
    D026BatchError,
    FILTERED_RECORDS_HEADER,
    ZINC_METADATA_HEADER,
    connectivity_match,
    d026_pilot_waiver,
    full_key_match,
    inchikey_connectivity_layer,
    transform_candidate_b_identities,
    write_d026_pilot_waiver,
)


FULL_KEY_A = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
FULL_KEY_A_STEREO_DIFF = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"
FULL_KEY_B = "BBBBBBBBBBBBBB-BBBBBBBBBB-C"


def write_tsv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


class D026BatchIdentityTests(unittest.TestCase):
    def make_source_tree(self, root, source_file, rows):
        path = root / source_file[:2] / source_file
        write_tsv(path, ZINC_METADATA_HEADER, rows)
        return path

    def make_filtered_records(self, path, rows):
        write_tsv(path, FILTERED_RECORDS_HEADER, rows)

    def run_transform(self, directory, filtered_rows, source_rows, key_map):
        root = Path(directory) / "2D"
        filtered = Path(directory) / "filtered_records.tsv"
        output = Path(directory) / "identity.tsv"
        summary = Path(directory) / "summary.json"
        self.make_source_tree(root, "AAEA.txt", source_rows)
        self.make_filtered_records(filtered, filtered_rows)

        def fake_smiles_to_inchikey(smiles):
            return key_map[smiles]

        return transform_candidate_b_identities(
            filtered_records_path=filtered,
            source_root=root,
            output_tsv_path=output,
            summary_json_path=summary,
            container_environment_id="sha256:020a8c810e5f4285fe4479c6d6aa6bc987393834480a24dd9a513631668851b4",
            smiles_to_inchikey=fake_smiles_to_inchikey,
        )

    def test_connectivity_layer_is_first_14_characters(self):
        self.assertEqual(
            inchikey_connectivity_layer("ABCDEFGHIJKLMN-STEREO-TAIL"),
            "ABCDEFGHIJKLMN",
        )

    def test_full_key_and_connectivity_key_are_distinct(self):
        self.assertFalse(full_key_match(FULL_KEY_A, FULL_KEY_A_STEREO_DIFF))
        self.assertTrue(connectivity_match(FULL_KEY_A, FULL_KEY_A_STEREO_DIFF))

    def test_full_key_mismatch_with_connectivity_match_does_not_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_transform(
                directory,
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    ("CCO", "ZINC1", FULL_KEY_A, 46.0, 0.1, 30, 10, "AAEA", "")
                ],
                key_map={"CCO": FULL_KEY_A_STEREO_DIFF},
            )

            self.assertEqual(result["exit_code"], 0)
            summary = result["summary"]
            self.assertEqual(summary["processed_count"], 1)
            self.assertEqual(summary["full_key_matches"], 0)
            self.assertEqual(summary["full_key_mismatches"], 1)
            self.assertEqual(summary["connectivity_matches"], 1)
            self.assertEqual(summary["connectivity_mismatches"], 0)
            self.assertEqual(summary["stopping_status"], "completed")

            output = Path(result["output_tsv"]).read_text()
            self.assertIn("false\ttrue\tAAEA.txt\t2\n", output)

    def test_connectivity_mismatch_causes_immediate_nonzero_stop(self):
        calls = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "2D"
            filtered = Path(directory) / "filtered_records.tsv"
            output = Path(directory) / "identity.tsv"
            summary_path = Path(directory) / "summary.json"
            self.make_source_tree(
                root,
                "AAEA.txt",
                [
                    ("CCO", "ZINC1", FULL_KEY_A, 46.0, 0.1, 30, 10, "AAEA", ""),
                    ("CCN", "ZINC2", FULL_KEY_A, 45.0, 0.1, 30, 10, "AAEA", ""),
                ],
            )
            self.make_filtered_records(
                filtered,
                [("CCO", "ZINC1", "AAEA.txt", 2), ("CCN", "ZINC2", "AAEA.txt", 3)],
            )

            def fake_smiles_to_inchikey(smiles):
                calls.append(smiles)
                return FULL_KEY_B

            result = transform_candidate_b_identities(
                filtered,
                root,
                output,
                summary_path,
                "env-id",
                smiles_to_inchikey=fake_smiles_to_inchikey,
            )

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(calls, ["CCO"])
            self.assertEqual(result["summary"]["processed_count"], 1)
            self.assertEqual(result["summary"]["input_record_count"], 2)
            self.assertEqual(result["summary"]["connectivity_mismatches"], 1)
            self.assertEqual(
                result["summary"]["stopping_status"],
                "stopped_connectivity_mismatch",
            )
            self.assertEqual(
                result["summary"]["first_connectivity_mismatch"]["zinc_id"],
                "ZINC1",
            )

    def test_source_lineage_verification_rejects_smiles_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(D026BatchError, "SMILES lineage mismatch"):
                self.run_transform(
                    directory,
                    filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                    source_rows=[
                        ("CCN", "ZINC1", FULL_KEY_A, 46.0, 0.1, 30, 10, "AAEA", "")
                    ],
                    key_map={"CCO": FULL_KEY_A},
                )

    def test_summary_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            result_a = self.run_transform(
                Path(directory) / "a",
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    ("CCO", "ZINC1", FULL_KEY_A, 46.0, 0.1, 30, 10, "AAEA", "")
                ],
                key_map={"CCO": FULL_KEY_A},
            )
            result_b = self.run_transform(
                Path(directory) / "b",
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    ("CCO", "ZINC1", FULL_KEY_A, 46.0, 0.1, 30, 10, "AAEA", "")
                ],
                key_map={"CCO": FULL_KEY_A},
            )

            summary_a = Path(result_a["summary_json"]).read_text()
            summary_b = Path(result_b["summary_json"]).read_text()
            self.assertEqual(summary_a, summary_b)
            self.assertEqual(json.loads(summary_a), result_a["summary"])

    def test_waiver_artifact_has_explicit_case_labels(self):
        waiver = d026_pilot_waiver()
        self.assertEqual(
            waiver["mismatch_case_counts"][
                "A_input_stereo_present_but_D026_key_empty_stereo_layer"
            ],
            3,
        )
        self.assertEqual(
            waiver["mismatch_case_counts"][
                "B_input_stereo_absent_but_ZINC_key_has_stereo"
            ],
            0,
        )
        self.assertEqual(
            waiver["mismatch_case_counts"][
                "C_both_keys_have_stereo_but_stereo_layer_differs"
            ],
            4,
        )
        self.assertTrue(waiver["connectivity_concordance_required"])
        self.assertFalse(waiver["full_historical_zinc_inchikey_concordance_required"])
        self.assertEqual(
            waiver["seven_record_audit_artifact"],
            {
                "path": "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_7_mismatches.tsv",
                "sha256": "0fd004af4052729dc14c196833fea823d26dfbc6498aea6fd39a8b96bfb900f6",
                "role": "input/reference to this waiver",
                "rewritten_by_this_artifact": False,
            },
        )
        self.assertEqual(
            waiver["pilot_summary_artifact"],
            {
                "path": "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_summary.json",
                "sha256": "a8e7bd2eace3f111f646d63b16c67becb732056b9a3e78c2a846b0f39bd10632",
                "role": "associated preserved pilot summary artifact",
            },
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "waiver.json"
            result = write_d026_pilot_waiver(output)
            self.assertEqual(json.loads(output.read_text()), waiver)
            self.assertIn("waiver_sha256", result)


if __name__ == "__main__":
    unittest.main()
