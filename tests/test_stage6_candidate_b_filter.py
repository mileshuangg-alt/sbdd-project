import json
from pathlib import Path
import tempfile
import unittest

from evaluation.stage6_candidate_b_filter import (
    ZINC_METADATA_HEADER,
    ZincMetadataParseError,
    ZincMetadataRecord,
    parse_zinc_metadata_line,
    passes_literature_filter,
    process_zinc_metadata_files,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/stage6_candidate_b/AAAA_sample.txt"


class Stage6CandidateBFilterTests(unittest.TestCase):
    def make_record(self, mwt, logp, reactive, purchasable):
        return ZincMetadataRecord(
            smiles="CCO",
            zinc_id="ZINC_TEST",
            inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
            mwt=mwt,
            logp=logp,
            reactive=reactive,
            purchasable=purchasable,
            tranche_name="AAAA",
            features="",
        )

    def test_frozen_boundary_predicate(self):
        cases = (
            ((250.0, 3.5, 30, 10), True),
            ((250.0, 3.5, 50, 10), True),
            ((250.01, 3.5, 30, 10), False),
            ((250.0, 3.51, 30, 10), False),
            ((250.0, 3.5, 0, 50), False),
            ((250.0, 3.5, 30, 9), False),
        )
        for values, expected in cases:
            with self.subTest(values=values):
                self.assertIs(
                    passes_literature_filter(self.make_record(*values)),
                    expected,
                )

    def test_exact_header_schema(self):
        header = "\t".join(ZINC_METADATA_HEADER)
        self.assertEqual(
            header,
            "smiles\tzinc_id\tinchikey\tmwt\tlogp\treactive\t"
            "purchasable\ttranche_name\tfeatures",
        )

    def test_parser_handles_crlf_and_empty_features(self):
        line = (
            "CCO\tZINC_TEST\tLFQSCWFLJHTTHZ-UHFFFAOYSA-N\t46.069\t"
            "-0.001\t30\t10\tAAAA\t\r\n"
        )
        record = parse_zinc_metadata_line(line, line_number=7)
        self.assertEqual(record.smiles, "CCO")
        self.assertEqual(record.zinc_id, "ZINC_TEST")
        self.assertEqual(record.inchikey, "LFQSCWFLJHTTHZ-UHFFFAOYSA-N")
        self.assertEqual(record.mwt, 46.069)
        self.assertEqual(record.logp, -0.001)
        self.assertEqual(record.reactive, 30)
        self.assertEqual(record.purchasable, 10)
        self.assertEqual(record.tranche_name, "AAAA")
        self.assertEqual(record.features, "")

    def test_parser_rejects_malformed_field_count(self):
        with self.assertRaisesRegex(
            ZincMetadataParseError,
            "line 11.*expected 9.*found 8",
        ):
            parse_zinc_metadata_line(
                "CCO\tZINC_TEST\tKEY\t46.0\t0.1\t30\t10\tAAAA\n",
                line_number=11,
            )

    def test_parser_rejects_invalid_numeric_fields(self):
        with self.assertRaisesRegex(
            ZincMetadataParseError,
            "Invalid numeric field.*line 12",
        ):
            parse_zinc_metadata_line(
                "CCO\tZINC_TEST\tKEY\tnot-a-float\t0.1\t30\t10\tAAAA\t\n",
                line_number=12,
            )

    def test_real_format_fixture_record_reactive_zero_fails(self):
        line = (
            "CO[C@H]1OC[C@@H](O)[C@H](O)[C@H]1O\t4371221\t"
            "ZBDGHWFPLXXWRD-MOJAZDJTSA-N\t164.157\t-1.928\t"
            "0\t50\tAAAA\t"
        )
        record = parse_zinc_metadata_line(line, line_number=2)
        self.assertEqual(record.reactive, 0)
        self.assertFalse(passes_literature_filter(record))

    def test_worker_writes_deterministic_outputs_and_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            result = process_zinc_metadata_files([FIXTURE], directory)
            output_dir = Path(directory)

            filtered = (output_dir / "filtered_records.tsv").read_text()
            self.assertEqual(
                filtered,
                "smiles\tzinc_id\tsource_file\tsource_line_number\n"
                "CCO\tZINC_PASS30\tAAAA_sample.txt\t3\n"
                "CCN\tZINC_PASS50\tAAAA_sample.txt\t4\n",
            )

            malformed = (output_dir / "malformed_records.tsv").read_text()
            self.assertEqual(
                malformed,
                "source_file\tsource_line_number\terror\trecord_json\n",
            )

            self.assertEqual(
                result["counts"],
                {
                    "input_records": 3,
                    "accepted_records": 2,
                    "rejected_records": 1,
                    "malformed_records": 0,
                },
            )

            manifest = json.loads(
                (output_dir / "aggregate_manifest.json").read_text()
            )
            self.assertEqual(manifest["counts"], result["counts"])
            self.assertEqual(
                manifest["filter"],
                {
                    "mwt_max": 250.0,
                    "logp_max": 3.5,
                    "reactive_allowed": [30, 50],
                    "purchasable_min": 10,
                },
            )

            checksums = (output_dir / "checksums.sha256").read_text()
            self.assertIn(
                f"{sha256_file(output_dir / 'filtered_records.tsv')}  "
                "filtered_records.tsv\n",
                checksums,
            )
            self.assertIn(
                f"{sha256_file(output_dir / 'aggregate_manifest.json')}  "
                "aggregate_manifest.json\n",
                checksums,
            )

    def test_worker_records_malformed_records_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "bad.txt"
            input_path.write_text(
                "\t".join(ZINC_METADATA_HEADER)
                + "\nCCO\tZINC_BAD\tKEY\tbad\t0.1\t30\t10\tAAAA\t\n",
                encoding="utf-8",
            )
            output_dir = Path(directory) / "out"
            result = process_zinc_metadata_files([input_path], output_dir)

            self.assertEqual(result["counts"]["malformed_records"], 1)
            malformed = (output_dir / "malformed_records.tsv").read_text()
            self.assertIn("bad.txt\t2\tInvalid numeric field", malformed)


if __name__ == "__main__":
    unittest.main()
