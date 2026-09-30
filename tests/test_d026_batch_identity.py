import csv
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.d026_batch_identity import (
    D026BatchError,
    FILTERED_RECORDS_HEADER,
    ZINC_METADATA_HEADER,
    _summary,
    build_d026_quarantine_record,
    classify_d026_quarantine,
    connectivity_match,
    d026_pilot_waiver,
    full_key_match,
    inchikey_connectivity_layer,
    record_d026_quarantine,
    transform_candidate_b_identities,
    write_d026_pilot_waiver,
)


FULL_KEY_A = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
FULL_KEY_A_STEREO_DIFF = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"
FULL_KEY_B = "BBBBBBBBBBBBBB-BBBBBBBBBB-C"

OFFENDING_SMILES = r"N=C(NO)N[N]N=C1C=C[N+]\(=O)N=C1"


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
        quarantine = Path(directory) / "quarantine.tsv"
        self.make_source_tree(root, "AAEA.txt", source_rows)
        self.make_filtered_records(filtered, filtered_rows)

        def fake_smiles_to_inchikey(smiles):
            return key_map[smiles]

        result = transform_candidate_b_identities(
            filtered_records_path=filtered,
            source_root=root,
            output_tsv_path=output,
            summary_json_path=summary,
            quarantine_tsv_path=quarantine,
            container_environment_id=(
                "sha256:020a8c810e5f4285fe4479c6d6aa6bc987393834480a24dd9a513631668851b4"
            ),
            smiles_to_inchikey=fake_smiles_to_inchikey,
        )

        return result

    def test_connectivity_layer_is_first_14_characters(self):
        self.assertEqual(
            inchikey_connectivity_layer("ABCDEFGHIJKLMN-STEREO-TAIL"),
            "ABCDEFGHIJKLMN",
        )

    def test_full_key_and_connectivity_key_are_distinct(self):
        self.assertFalse(
            full_key_match(FULL_KEY_A, FULL_KEY_A_STEREO_DIFF)
        )
        self.assertTrue(
            connectivity_match(FULL_KEY_A, FULL_KEY_A_STEREO_DIFF)
        )

    def test_full_key_mismatch_with_connectivity_match_does_not_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_transform(
                directory,
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    (
                        "CCO",
                        "ZINC1",
                        FULL_KEY_A,
                        46.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    )
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
            quarantine = Path(directory) / "quarantine.tsv"

            self.make_source_tree(
                root,
                "AAEA.txt",
                [
                    (
                        "CCO",
                        "ZINC1",
                        FULL_KEY_A,
                        46.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    ),
                    (
                        "CCN",
                        "ZINC2",
                        FULL_KEY_A,
                        45.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    ),
                ],
            )
            self.make_filtered_records(
                filtered,
                [
                    ("CCO", "ZINC1", "AAEA.txt", 2),
                    ("CCN", "ZINC2", "AAEA.txt", 3),
                ],
            )

            def fake_smiles_to_inchikey(smiles):
                calls.append(smiles)
                return FULL_KEY_B

            result = transform_candidate_b_identities(
                filtered_records_path=filtered,
                source_root=root,
                output_tsv_path=output,
                summary_json_path=summary_path,
                quarantine_tsv_path=quarantine,
                container_environment_id="env-id",
                smiles_to_inchikey=fake_smiles_to_inchikey,
            )

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(calls, ["CCO"])
            self.assertEqual(result["summary"]["processed_count"], 1)
            self.assertEqual(result["summary"]["input_record_count"], 2)
            self.assertEqual(
                result["summary"]["connectivity_mismatches"],
                1,
            )
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
            with self.assertRaisesRegex(
                D026BatchError,
                "SMILES lineage mismatch",
            ):
                self.run_transform(
                    directory,
                    filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                    source_rows=[
                        (
                            "CCN",
                            "ZINC1",
                            FULL_KEY_A,
                            46.0,
                            0.1,
                            30,
                            10,
                            "AAEA",
                            "",
                        )
                    ],
                    key_map={"CCO": FULL_KEY_A},
                )

    def test_summary_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            result_a = self.run_transform(
                Path(directory) / "a",
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    (
                        "CCO",
                        "ZINC1",
                        FULL_KEY_A,
                        46.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    )
                ],
                key_map={"CCO": FULL_KEY_A},
            )
            result_b = self.run_transform(
                Path(directory) / "b",
                filtered_rows=[("CCO", "ZINC1", "AAEA.txt", 2)],
                source_rows=[
                    (
                        "CCO",
                        "ZINC1",
                        FULL_KEY_A,
                        46.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    )
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
        self.assertFalse(
            waiver["full_historical_zinc_inchikey_concordance_required"]
        )
        self.assertEqual(
            waiver["seven_record_audit_artifact"],
            {
                "path": (
                    "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/"
                    "stereo_audit_7_mismatches.tsv"
                ),
                "sha256": (
                    "0fd004af4052729dc14c196833fea823d26dfbc6498aea6fd39a8b96bfb900f6"
                ),
                "role": "input/reference to this waiver",
                "rewritten_by_this_artifact": False,
            },
        )
        self.assertEqual(
            waiver["pilot_summary_artifact"],
            {
                "path": (
                    "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/"
                    "stereo_audit_summary.json"
                ),
                "sha256": (
                    "a8e7bd2eace3f111f646d63b16c67becb732056b9a3e78c2a846b0f39bd10632"
                ),
                "role": "associated preserved pilot summary artifact",
            },
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "waiver.json"
            result = write_d026_pilot_waiver(output)
            self.assertEqual(json.loads(output.read_text()), waiver)
            self.assertIn("waiver_sha256", result)

    def test_exotic_valence_quarantine_classifier(self):
        ordinary = "CCN(CC)C(=O)C"

        self.assertEqual(
            classify_d026_quarantine(OFFENDING_SMILES),
            (
                "D026_EXOTIC_VALENCE_Q1",
                "D026_EXOTIC_VALENCE_Q2",
            ),
        )
        self.assertEqual(classify_d026_quarantine(ordinary), ())
        self.assertEqual(classify_d026_quarantine("CCN(=O)C"), ())

    def test_build_d026_quarantine_record_preserves_lineage(self):
        record = build_d026_quarantine_record(
            smiles=OFFENDING_SMILES,
            zinc_id="687728612",
            source_file="AAEE.txt",
            source_line_number=2172,
            quarantine_reasons=(
                "D026_EXOTIC_VALENCE_Q1",
                "D026_EXOTIC_VALENCE_Q2",
            ),
        )

        self.assertEqual(
            record,
            {
                "smiles": OFFENDING_SMILES,
                "zinc_id": "687728612",
                "source_file": "AAEE.txt",
                "source_line_number": 2172,
                "quarantine_reasons": [
                    "D026_EXOTIC_VALENCE_Q1",
                    "D026_EXOTIC_VALENCE_Q2",
                ],
            },
        )

        with self.assertRaises(ValueError):
            build_d026_quarantine_record(
                smiles="CCO",
                zinc_id="ZINC1",
                source_file="AAEA.txt",
                source_line_number=2,
                quarantine_reasons=(),
            )

    def test_record_d026_quarantine_does_not_affect_connectivity_counts(self):
        counts = {
            "processed_count": 2,
            "quarantined_count": 0,
            "full_key_matches": 2,
            "full_key_mismatches": 0,
            "connectivity_matches": 2,
            "connectivity_mismatches": 0,
        }
        record_d026_quarantine(
            counts=counts,
        )

        self.assertEqual(counts["quarantined_count"], 1)
        self.assertEqual(counts["processed_count"], 2)
        self.assertEqual(counts["connectivity_matches"], 2)
        self.assertEqual(counts["connectivity_mismatches"], 0)

    def test_summary_quarantine_denominator_accounting(self):
        summary = _summary(
            container_environment_id="env-id",
            input_artifact_sha256="input-sha",
            input_record_count=5,
            counts={
                "processed_count": 4,
                "quarantined_count": 1,
                "full_key_matches": 4,
                "full_key_mismatches": 0,
                "connectivity_matches": 4,
                "connectivity_mismatches": 0,
            },
            stopping_status="completed",
            first_connectivity_mismatch=None,
        )

        self.assertEqual(summary["input_record_count"], 5)
        self.assertEqual(summary["quarantined_count"], 1)
        self.assertEqual(summary["eligible_record_count"], 4)
        self.assertEqual(summary["processed_count"], 4)
        self.assertEqual(summary["connectivity_matches"], 4)
        self.assertEqual(summary["connectivity_concordance_fraction"], 1.0)

    def test_summary_allows_partial_processed_count_after_connectivity_stop(
            self):
        summary = _summary(
            container_environment_id="env-id",
            input_artifact_sha256="input-sha",
            input_record_count=5,
            counts={
                "processed_count": 3,
                "quarantined_count": 1,
                "full_key_matches": 3,
                "full_key_mismatches": 0,
                "connectivity_matches": 2,
                "connectivity_mismatches": 1,
            },
            stopping_status="stopped_connectivity_mismatch",
            first_connectivity_mismatch={"zinc_id": "ZINC4"},
        )

        self.assertEqual(summary["eligible_record_count"], 4)
        self.assertEqual(summary["processed_count"], 3)
        self.assertEqual(summary["connectivity_mismatches"], 1)

    def test_quarantine_skips_identity_and_excludes_record_from_denominator(
            self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "2D"
            filtered = Path(directory) / "filtered_records.tsv"
            output = Path(directory) / "identity.tsv"
            summary = Path(directory) / "summary.json"
            quarantine = Path(directory) / "quarantine.tsv"

            source_rows = [
                (
                    "CCO",
                    "ZINC1",
                    FULL_KEY_A,
                    46.0,
                    0.1,
                    30,
                    10,
                    "AAEA",
                    "",
                ),
                (
                    OFFENDING_SMILES,
                    "687728612",
                    FULL_KEY_A,
                    197.158,
                    -1.343,
                    30,
                    10,
                    "AAEA",
                    "",
                ),
            ]
            self.make_source_tree(root, "AAEA.txt", source_rows)

            self.make_filtered_records(
                filtered,
                [
                    ("CCO", "ZINC1", "AAEA.txt", 2),
                    (OFFENDING_SMILES, "687728612", "AAEA.txt", 3),
                ],
            )

            calls = []

            def fake_smiles_to_inchikey(smiles):
                calls.append(smiles)
                return FULL_KEY_A

            result = transform_candidate_b_identities(
                filtered_records_path=filtered,
                source_root=root,
                output_tsv_path=output,
                summary_json_path=summary,
                quarantine_tsv_path=quarantine,
                container_environment_id="env-id",
                smiles_to_inchikey=fake_smiles_to_inchikey,
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(calls, ["CCO"])
            self.assertEqual(result["summary"]["input_record_count"], 2)
            self.assertEqual(result["summary"]["quarantined_count"], 1)
            self.assertEqual(result["summary"]["eligible_record_count"], 1)
            self.assertEqual(result["summary"]["processed_count"], 1)
            self.assertEqual(result["summary"]["connectivity_matches"], 1)
            self.assertEqual(result["summary"]["connectivity_mismatches"], 0)

            quarantine_text = quarantine.read_text()
            self.assertIn("687728612", quarantine_text)
            self.assertIn("D026_EXOTIC_VALENCE_Q1", quarantine_text)
            self.assertIn("D026_EXOTIC_VALENCE_Q2", quarantine_text)

    def test_nonquarantined_connectivity_mismatch_still_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "2D"
            filtered = Path(directory) / "filtered_records.tsv"
            output = Path(directory) / "identity.tsv"
            summary = Path(directory) / "summary.json"
            quarantine = Path(directory) / "quarantine.tsv"

            self.make_source_tree(
                root,
                "AAEA.txt",
                [
                    (
                        "CCO",
                        "ZINC1",
                        FULL_KEY_B,
                        46.0,
                        0.1,
                        30,
                        10,
                        "AAEA",
                        "",
                    )
                ],
            )
            self.make_filtered_records(
                filtered,
                [("CCO", "ZINC1", "AAEA.txt", 2)],
            )

            result = transform_candidate_b_identities(
                filtered_records_path=filtered,
                source_root=root,
                output_tsv_path=output,
                summary_json_path=summary,
                quarantine_tsv_path=quarantine,
                container_environment_id="env-id",
                smiles_to_inchikey=lambda _smiles: FULL_KEY_A,
            )

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(
                result["summary"]["stopping_status"],
                "stopped_connectivity_mismatch",
            )
            self.assertEqual(
                result["summary"]["connectivity_mismatches"],
                1,
            )
            self.assertEqual(result["summary"]["quarantined_count"], 0)


if __name__ == "__main__":
    unittest.main()
