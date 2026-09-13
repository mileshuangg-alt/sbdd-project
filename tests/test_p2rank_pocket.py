from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.p2rank_pocket import (
    build_predicted_pocket_artifact,
    build_predicted_pocket_metadata,
    get_complete_residue_atoms,
    get_predicted_pocket_atoms,
    get_touched_residues,
    load_p2rank_predictions,
    load_pdb_atoms_by_serial,
    load_pocket_selection,
    select_predicted_pocket,
    validate_complete_residue_pocket,
    write_predicted_pocket,
    write_predicted_pocket_metadata,
)
from evaluation.pocket_models import P2RankPocket, PocketSelection, ResidueID


def pdb_atom(
    serial,
    atom_name,
    residue_name,
    chain,
    residue_number,
    x,
    y,
    z,
    element,
    insertion_code="",
):
    return (
        f"ATOM  {serial:5d} {atom_name:<4} {residue_name:>3} "
        f"{chain:1}{residue_number:4d}{insertion_code:1}   "
        f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           "
        f"{element:>2}\n"
    )


class P2RankPocketCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tmpdir.name)

        self.atom_1 = pdb_atom(
            1,
            "N",
            "ALA",
            "A",
            1,
            1.0,
            2.0,
            3.0,
            "N",
        )
        self.atom_2 = pdb_atom(
            2,
            "CA",
            "ALA",
            "A",
            1,
            2.0,
            3.0,
            4.0,
            "C",
        )
        self.atom_3 = pdb_atom(
            3,
            "C",
            "ALA",
            "A",
            1,
            3.0,
            4.0,
            5.0,
            "C",
        )
        self.atom_4 = pdb_atom(
            4,
            "N",
            "GLY",
            "A",
            2,
            4.0,
            5.0,
            6.0,
            "N",
        )
        self.atom_5 = pdb_atom(
            5,
            "CA",
            "GLY",
            "A",
            2,
            5.0,
            6.0,
            7.0,
            "C",
        )
        self.atom_6 = pdb_atom(
            6,
            "N",
            "SER",
            "B",
            3,
            6.0,
            7.0,
            8.0,
            "N",
        )

        self.source_pdb = self.write_text(
            "synthetic_source.pdb",
            "".join(
                [
                    self.atom_1,
                    self.atom_2,
                    self.atom_3,
                    self.atom_4,
                    self.atom_5,
                    self.atom_6,
                    "HETATM    7  C1  LIG A 101       9.000   9.000   9.000  1.00 20.00           C\n",
                    "END\n",
                ]
            ),
        )
        self.predictions = self.write_predictions(
            "predictions.csv",
            [
                {
                    "name": "pocket_alpha",
                    "rank": "2",
                    "score": "11.5",
                    "probability": "0.41",
                    "sas_points": "17",
                    "surf_atoms": "2",
                    "center_x": "1.1",
                    "center_y": "2.2",
                    "center_z": "3.3",
                    "residue_ids": "A_1 A_2",
                    "surf_atom_ids": "2 4",
                },
                {
                    "name": "pocket_beta",
                    "rank": "1",
                    "score": "99.0",
                    "probability": "0.99",
                    "sas_points": "23",
                    "surf_atoms": "1",
                    "center_x": "9.0",
                    "center_y": "8.0",
                    "center_z": "7.0",
                    "residue_ids": "B_3",
                    "surf_atom_ids": "6",
                },
            ],
        )
        self.residues_output = self.write_text(
            "p2rank_residues.csv",
            "name,residue_ids\npocket_alpha,A_1 A_2\n",
        )
        self.selection_config = self.write_json(
            "selection.json",
            {
                "schema_version": 1,
                "method": "p2rank_name",
                "value": "pocket_alpha",
            },
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def write_text(self, name, text):
        path = self.workdir / name
        path.write_text(text)
        return path

    def write_json(self, name, value):
        path = self.workdir / name
        path.write_text(json.dumps(value, indent=2) + "\n")
        return path

    def write_predictions(self, name, rows):
        header = [
            "name",
            "rank",
            "score",
            "probability",
            "sas_points",
            "surf_atoms",
            "center_x",
            "center_y",
            "center_z",
            "residue_ids",
            "surf_atom_ids",
        ]
        lines = [",".join(header)]
        for row in rows:
            lines.append(
                ",".join(
                    row[column]
                    for column in header
                )
            )
        return self.write_text(
            name,
            "\n".join(lines) + "\n",
        )

    def selected_alpha(self):
        predictions = load_p2rank_predictions(
            self.predictions
        )
        return select_predicted_pocket(
            predictions,
            PocketSelection(
                method="p2rank_name",
                value="pocket_alpha",
            ),
        )

    def test_valid_p2rank_prediction_parsing(self):
        predictions = load_p2rank_predictions(
            self.predictions
        )

        self.assertEqual(
            len(predictions),
            2,
        )
        self.assertEqual(
            predictions[0],
            P2RankPocket(
                name="pocket_alpha",
                rank=2,
                score=11.5,
                probability=0.41,
                sas_points=17,
                surf_atoms=2,
                center=(1.1, 2.2, 3.3),
                residue_ids=("A_1", "A_2"),
                surf_atom_ids=(2, 4),
            ),
        )

    def test_malformed_or_missing_prediction_columns_raise(self):
        missing_probability = self.write_text(
            "missing_probability.csv",
            "name,rank,score,sas_points,surf_atoms,center_x,center_y,center_z,residue_ids,surf_atom_ids\n"
            "pocket_alpha,1,2.0,3,4,0.0,0.0,0.0,A_1,2\n",
        )
        malformed_rank = self.write_predictions(
            "malformed_rank.csv",
            [
                {
                    "name": "pocket_alpha",
                    "rank": "not_an_int",
                    "score": "2.0",
                    "probability": "0.5",
                    "sas_points": "3",
                    "surf_atoms": "4",
                    "center_x": "0.0",
                    "center_y": "0.0",
                    "center_z": "0.0",
                    "residue_ids": "A_1",
                    "surf_atom_ids": "2",
                }
            ],
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing required columns",
        ):
            load_p2rank_predictions(
                missing_probability
            )
        with self.assertRaises(ValueError):
            load_p2rank_predictions(
                malformed_rank
            )

    def test_missing_p2rank_prediction_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_p2rank_predictions(
                self.workdir / "does_not_exist.csv"
            )

    def test_configured_pocket_selection_ignores_rank_and_probability(self):
        selected = self.selected_alpha()

        self.assertEqual(
            selected.name,
            "pocket_alpha",
        )
        self.assertEqual(
            selected.rank,
            2,
        )
        self.assertEqual(
            selected.probability,
            0.41,
        )

    def test_missing_configured_pocket_raises(self):
        predictions = load_p2rank_predictions(
            self.predictions
        )

        with self.assertRaisesRegex(
            ValueError,
            "not found",
        ):
            select_predicted_pocket(
                predictions,
                PocketSelection(
                    method="p2rank_name",
                    value="missing_pocket",
                ),
            )

    def test_ambiguous_configured_pocket_raises(self):
        predictions = [
            self.selected_alpha(),
            self.selected_alpha(),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "ambiguous",
        ):
            select_predicted_pocket(
                predictions,
                PocketSelection(
                    method="p2rank_name",
                    value="pocket_alpha",
                ),
            )

    def test_missing_p2rank_atom_ids_in_source_pdb_raise(self):
        atoms_by_serial = load_pdb_atoms_by_serial(
            self.source_pdb
        )
        selected = P2RankPocket(
            name="pocket_missing_atom",
            rank=1,
            score=1.0,
            probability=0.5,
            sas_points=1,
            surf_atoms=1,
            center=(0.0, 0.0, 0.0),
            residue_ids=(),
            surf_atom_ids=(999,),
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing from the input protein",
        ):
            get_predicted_pocket_atoms(
                selected,
                atoms_by_serial,
            )
        with self.assertRaisesRegex(
            ValueError,
            "missing from the input protein",
        ):
            get_touched_residues(
                selected,
                atoms_by_serial,
            )

    def test_empty_surface_atom_selection_raises(self):
        atoms_by_serial = load_pdb_atoms_by_serial(
            self.source_pdb
        )
        selected = P2RankPocket(
            name="pocket_empty",
            rank=1,
            score=1.0,
            probability=0.5,
            sas_points=1,
            surf_atoms=0,
            center=(0.0, 0.0, 0.0),
            residue_ids=(),
            surf_atom_ids=(),
        )

        with self.assertRaisesRegex(
            ValueError,
            "no surface atom IDs",
        ):
            get_predicted_pocket_atoms(
                selected,
                atoms_by_serial,
            )
        with self.assertRaisesRegex(
            ValueError,
            "no surface atom IDs",
        ):
            get_touched_residues(
                selected,
                atoms_by_serial,
            )

    def test_atom_to_touched_residue_mapping(self):
        atoms_by_serial = load_pdb_atoms_by_serial(
            self.source_pdb
        )

        self.assertEqual(
            get_touched_residues(
                self.selected_alpha(),
                atoms_by_serial,
            ),
            [
                ResidueID(
                    chain="A",
                    number="1",
                    insertion_code="",
                    name="ALA",
                ),
                ResidueID(
                    chain="A",
                    number="2",
                    insertion_code="",
                    name="GLY",
                ),
            ],
        )

    def test_complete_residue_expansion_and_atom_record_preservation(self):
        touched_residues = [
            ResidueID(
                chain="A",
                number="1",
                insertion_code="",
                name="ALA",
            ),
            ResidueID(
                chain="A",
                number="2",
                insertion_code="",
                name="GLY",
            ),
        ]

        self.assertEqual(
            get_complete_residue_atoms(
                touched_residues,
                self.source_pdb,
            ),
            [
                self.atom_1,
                self.atom_2,
                self.atom_3,
                self.atom_4,
                self.atom_5,
            ],
        )

    def test_complete_residue_pocket_invariant(self):
        touched_residues = [
            ResidueID(
                chain="A",
                number="1",
                insertion_code="",
                name="ALA",
            ),
        ]
        complete_atoms = [
            self.atom_1,
            self.atom_2,
            self.atom_3,
        ]

        validate_complete_residue_pocket(
            complete_atoms,
            touched_residues,
            self.source_pdb,
        )
        with self.assertRaisesRegex(
            ValueError,
            "complete source-PDB residue",
        ):
            validate_complete_residue_pocket(
                [self.atom_1, self.atom_2],
                touched_residues,
                self.source_pdb,
            )

    def test_metadata_construction_and_stable_config_hash(self):
        selected = self.selected_alpha()
        touched_residues = [
            ResidueID(
                chain="A",
                number="1",
                insertion_code="",
                name="ALA",
            )
        ]
        copy_path = self.write_text(
            "selection_copy.json",
            self.selection_config.read_text(),
        )

        metadata = build_predicted_pocket_metadata(
            source_structure_path=self.source_pdb,
            predictions_path=self.predictions,
            residues_path=self.residues_output,
            selected_pocket=selected,
            touched_residues=touched_residues,
            selection_config_path=self.selection_config,
            p2rank_version="synthetic-p2rank",
        )
        metadata_from_copy = build_predicted_pocket_metadata(
            source_structure_path=self.source_pdb,
            predictions_path=self.predictions,
            residues_path=self.residues_output,
            selected_pocket=selected,
            touched_residues=touched_residues,
            selection_config_path=copy_path,
            p2rank_version="synthetic-p2rank",
        )

        self.assertEqual(
            metadata.artifact_type,
            "PREDICTED POCKET",
        )
        self.assertEqual(
            metadata.pocket_method,
            "P2Rank",
        )
        self.assertTrue(
            metadata.lineage.conditioning_role,
        )
        self.assertTrue(
            metadata.lineage.primary_stage3b_role,
        )
        self.assertTrue(
            metadata.lineage.selection_frozen_before_generation,
        )
        self.assertEqual(
            metadata.selection_config.sha256,
            metadata_from_copy.selection_config.sha256,
        )

    def test_materialized_pocket_predicted_provenance_marker_lives_in_metadata(self):
        output_structure = self.workdir / "predicted_pocket.pdb"
        output_metadata = self.workdir / "predicted_pocket_metadata.json"

        metadata = build_predicted_pocket_artifact(
            source_structure_path=self.source_pdb,
            predictions_path=self.predictions,
            residues_path=self.residues_output,
            selection_config_path=self.selection_config,
            output_structure_path=output_structure,
            output_metadata_path=output_metadata,
            p2rank_version="synthetic-p2rank",
        )

        self.assertEqual(
            output_structure.read_text(),
            "".join(
                [
                    self.atom_1,
                    self.atom_2,
                    self.atom_3,
                    self.atom_4,
                    self.atom_5,
                    "END\n",
                ]
            ),
        )
        self.assertEqual(
            metadata.artifact_type,
            "PREDICTED POCKET",
        )
        self.assertEqual(
            json.loads(output_metadata.read_text())["artifact_type"],
            "PREDICTED POCKET",
        )

    def test_metadata_json_serialization(self):
        metadata = build_predicted_pocket_metadata(
            source_structure_path=self.source_pdb,
            predictions_path=self.predictions,
            residues_path=self.residues_output,
            selected_pocket=self.selected_alpha(),
            touched_residues=[
                ResidueID(
                    chain="A",
                    number="1",
                    insertion_code="",
                    name="ALA",
                )
            ],
            selection_config_path=self.selection_config,
            p2rank_version="synthetic-p2rank",
        )
        output_path = self.workdir / "metadata.json"

        write_predicted_pocket_metadata(
            metadata,
            output_path,
        )

        self.assertEqual(
            json.loads(output_path.read_text()),
            json.loads(
                json.dumps(asdict(metadata))
            ),
        )

    def test_config_loading(self):
        selection = load_pocket_selection(
            self.selection_config
        )

        self.assertEqual(
            selection,
            PocketSelection(
                method="p2rank_name",
                value="pocket_alpha",
            ),
        )
        with self.assertRaisesRegex(
            ValueError,
            "schema version",
        ):
            load_pocket_selection(
                self.write_json(
                    "bad_schema.json",
                    {
                        "schema_version": 2,
                        "method": "p2rank_name",
                        "value": "pocket_alpha",
                    },
                )
            )

    def test_write_predicted_pocket_rejects_empty_materialization(self):
        with self.assertRaisesRegex(
            ValueError,
            "no ATOM records",
        ):
            write_predicted_pocket(
                [],
                self.workdir / "empty.pdb",
            )


if __name__ == "__main__":
    unittest.main()
