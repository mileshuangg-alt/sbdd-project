from pathlib import Path
import gzip
import importlib.util
import unittest
from scripts.stage5.analyze_dock_xac_200save import (
    EXPECTED_CONFORMERS,
    EXPECTED_HEAVY_ATOMS,
    build_xac_heavy_atom_mappings,
    calculate_symmetry_corrected_rmsd,
    load_3rey_receptor_heavy_atoms,
    load_dock_orientation_archives,
    load_dock_xac_200save_records,
    load_xac_reference,
    measure_d020_population,
    measure_d021_persisted_orientation_population,
    RDockPoseRecord,
    parse_rdock_sd_archive,
    reconstruct_dock_orientation,
    reconstruct_dock_orientation_population,
    reconstruct_pose_molecules,
    reconstruct_rdock_pose_molecule,
    validate_xac_chemistry,
    calculate_d_rel,
    measure_rdock_pose_d020,




)
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts/stage5/analyze_dock_xac_200save.py"
)
ARCHIVE_PATH = (
    ROOT
    / "references/stage5/dock385/3REY"
    / "xac_adversarial_A1_matchgoal5000"
    / "measurement_200save/test.mol2.gz"
)

ARCHIVE_DIR = (
    ROOT
    / "references/stage5/dock385/d021_orientation_archive"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "analyze_dock_xac_200save",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DockXac200SaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.records = cls.module.load_dock_xac_200save_records(
            ARCHIVE_PATH
        )

    def test_parser_reads_frozen_200_pose_archive(self):
        self.assertEqual(
            len(self.records),
            self.module.EXPECTED_POSES,
        )
        self.assertEqual(
            [record.rank for record in self.records],
            list(range(1, self.module.EXPECTED_POSES + 1)),
        )

        first = self.records[0]
        self.assertEqual(first.rank, 1)
        self.assertEqual(first.matchnum, 26)
        self.assertAlmostEqual(
            first.total_energy,
            -26.669317,
        )

    def test_parser_preserves_complete_pose_text(self):
        with gzip.open(ARCHIVE_PATH, "rt") as handle:
            archive_text = handle.read()

        self.assertEqual(
            "".join(record.mol2_text for record in self.records),
            archive_text,
        )
        self.assertTrue(
            self.records[0].mol2_text.startswith(
                "##########                 Name:"
            )
        )
        self.assertIn(
            "@<TRIPOS>MOLECULE",
            self.records[0].mol2_text,
        )

    def test_reconstruction_invariants_for_all_poses(self):
        molecules = self.module.reconstruct_pose_molecules(
            self.records
        )

        self.assertEqual(
            len(molecules),
            self.module.EXPECTED_POSES,
        )

        for molecule in molecules:
            self.assertEqual(
                molecule.GetNumHeavyAtoms(),
                self.module.EXPECTED_HEAVY_ATOMS,
            )
            self.assertEqual(
                molecule.GetNumConformers(),
                self.module.EXPECTED_CONFORMERS,
            )

    def test_all_poses_match_reference_heavy_atom_graph(self):
        reference = self.module.load_xac_reference()
        molecules = self.module.reconstruct_pose_molecules(
            self.records
        )

        results = [
            self.module.validate_xac_chemistry(
                molecule,
                reference,
            )
            for molecule in molecules
        ]

        self.assertEqual(
            len(results),
            self.module.EXPECTED_POSES,
        )

        for result in results:
            self.assertTrue(result["graph_identical"])
            self.assertEqual(
                result["pose_heavy_atoms"],
                self.module.EXPECTED_HEAVY_ATOMS,
            )
            self.assertEqual(
                result["reference_heavy_atoms"],
                self.module.EXPECTED_HEAVY_ATOMS,
            )

    def test_charge_and_protonation_difference_is_reported_separately(self):
        reference = self.module.load_xac_reference()
        molecule = self.module.reconstruct_pose_molecule(
            self.records[0]
        )

        result = self.module.validate_xac_chemistry(
            molecule,
            reference,
        )

        self.assertTrue(result["graph_identical"])
        self.assertTrue(
            result["charge_or_protonation_difference"]
        )
        self.assertEqual(result["pose_formal_charge"], 0)
        self.assertEqual(result["reference_formal_charge"], 1)
        self.assertEqual(result["formal_charge_delta"], -1)
        self.assertEqual(result["explicit_hydrogen_delta"], -1)

    def test_all_dock_xac_poses_have_complete_heavy_atom_mappings(self):
        records = load_dock_xac_200save_records()
        molecules = reconstruct_pose_molecules(records)
        reference = load_xac_reference()

        assert len(records) == 200
        assert len(molecules) == 200

        for molecule in molecules:
            validate_xac_chemistry(
                molecule,
                reference,
            )

            mappings = build_xac_heavy_atom_mappings(
                molecule,
                reference,
            )

            assert mappings

            for mapping in mappings:
                assert len(mapping) == EXPECTED_HEAVY_ATOMS

                pose_indices = [
                    pose_index
                    for pose_index, _ in mapping
                ]
                reference_indices = [
                    reference_index
                    for _, reference_index in mapping
                ]

                assert len(set(pose_indices)) == EXPECTED_HEAVY_ATOMS
                assert len(set(reference_indices)) == EXPECTED_HEAVY_ATOMS

                for pose_index, reference_index in mapping:
                    assert (
                        molecule.GetAtomWithIdx(
                            pose_index
                        ).GetAtomicNum()
                        == reference.GetAtomWithIdx(
                            reference_index
                        ).GetAtomicNum()
                    )

    def test_all_dock_xac_poses_have_symmetry_corrected_rmsd(self):
        records = load_dock_xac_200save_records()
        molecules = reconstruct_pose_molecules(records)
        reference = load_xac_reference()

        assert len(molecules) == 200

        rmsds = []

        for molecule in molecules:
            validate_xac_chemistry(
                molecule,
                reference,
            )

            mappings = build_xac_heavy_atom_mappings(
                molecule,
                reference,
            )

            assert len(mappings) == 4

            rmsd = calculate_symmetry_corrected_rmsd(
                molecule,
                reference,
            )

            rmsds.append(rmsd)

        assert len(rmsds) == 200
        assert all(rmsd >= 0.0 for rmsd in rmsds)
        assert all(rmsd < float("inf") for rmsd in rmsds)

    def test_3rey_receptor_heavy_atoms_are_loaded_in_frozen_frame(self):
        coordinates, atomic_numbers = (
            load_3rey_receptor_heavy_atoms()
        )

        self.assertEqual(coordinates.ndim, 2)
        self.assertEqual(coordinates.shape[1], 3)
        self.assertEqual(
            len(coordinates),
            len(atomic_numbers),
        )
        self.assertGreater(len(coordinates), 0)
        self.assertTrue(np.isfinite(coordinates).all())
        self.assertTrue(
            all(
                atomic_number > 1
                for atomic_number in atomic_numbers
            )
        )

    def test_all_dock_xac_poses_have_frozen_d_rel_measurements(self):
        records = load_dock_xac_200save_records()
        molecules = reconstruct_pose_molecules(records)
        receptor_positions, receptor_atomic_numbers = (
            load_3rey_receptor_heavy_atoms()
        )

        assert len(records) == 200
        assert len(molecules) == 200

        d_rels = []

        for molecule in molecules:
            value = calculate_d_rel(
                molecule,
                receptor_positions,
                receptor_atomic_numbers,
            )
            d_rels.append(value)

        assert len(d_rels) == 200
        assert all(value > 0.0 for value in d_rels)
        assert all(np.isfinite(value) for value in d_rels)

    def test_reconstruct_dock_orientation_applies_frozen_dock_transform(self):
        ligand_coordinates = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        )

        coml = np.array([1.0, 1.0, 1.0])
        comr = np.array([10.0, 20.0, 30.0])

        rotation = np.array(
            [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        )

        reconstructed = reconstruct_dock_orientation(
            ligand_coordinates,
            coml,
            comr,
            rotation,
        )

        expected = np.array(
            [
                [11.0, 20.0, 29.0],
                [10.0, 19.0, 29.0],
                [11.0, 19.0, 30.0],
            ]
        )

        np.testing.assert_allclose(
            reconstructed,
            expected,
            rtol=0.0,
            atol=1e-12,
        )

    def test_load_dock_orientation_archives_are_complete_and_aligned(self):
        comr_path = ARCHIVE_DIR / "orientations_mol000001_comr.gz"

        coml_path = ARCHIVE_DIR / "orientations_mol000001_coml.gz"
        rot_path = ARCHIVE_DIR / "orientations_mol000001_rot.gz"

        coml, comr, rot = load_dock_orientation_archives(
            comr_path,
            coml_path,
            rot_path,
        )

        self.assertEqual(coml.shape, (7989, 3))
        self.assertEqual(comr.shape, (7989, 3))
        self.assertEqual(rot.shape, (7989, 3, 3))

        self.assertTrue(np.isfinite(coml).all())
        self.assertTrue(np.isfinite(comr).all())
        self.assertTrue(np.isfinite(rot).all())

        np.testing.assert_allclose(
            comr[0],
            np.array([48.34800, 23.40925, 30.40525]),
            rtol=0.0,
            atol=1e-12,
        )

        np.testing.assert_allclose(
            coml[0],
            np.array([48.34800, 23.40925, 30.40525]),
            rtol=0.0,
            atol=1e-12,
        )

        np.testing.assert_allclose(
            rot[0],
            np.eye(3),
            rtol=0.0,
            atol=1e-12,
        )

        np.testing.assert_allclose(
            rot[1],
            np.array(
                [
                    [-0.3630, 0.8651, -0.3460],
                    [0.8737, 0.1870, -0.4491],
                    [-0.3238, -0.4654, -0.8237],
                ]
            ),
            rtol=0.0,
            atol=1e-12,
        )

    def test_reconstruct_dock_orientation_population_is_complete(self):
        archive_dir = (
            ROOT
            / "references/stage5/dock385/d021_orientation_archive"
        )

        coml, comr, rotations = load_dock_orientation_archives(
            archive_dir / "orientations_mol000001_comr.gz",
            archive_dir / "orientations_mol000001_coml.gz",
            archive_dir / "orientations_mol000001_rot.gz",
        )

        reference = load_xac_reference()
        conformer = reference.GetConformer()
        ligand_coordinates = np.asarray(
            conformer.GetPositions(),
            dtype=float,
        )

        reconstructed = reconstruct_dock_orientation_population(
            ligand_coordinates,
            coml,
            comr,
            rotations,
        )

        self.assertEqual(
            reconstructed.shape[0],
            coml.shape[0],
        )
        self.assertEqual(
            reconstructed.shape[0],
            7989,
        )
        self.assertEqual(
            reconstructed.shape[1],
            ligand_coordinates.shape[0],
        )
        self.assertEqual(
            reconstructed.shape[2],
            3,
        )

        self.assertTrue(np.isfinite(reconstructed).all())

        # The first archived orientation has identity rotation and
        # coml == comr, so its coordinates must equal the original XAC
        # coordinates exactly to the precision represented by the archive.
        np.testing.assert_allclose(
            reconstructed[0],
            ligand_coordinates,
            rtol=0.0,
            atol=1e-4,
        )

    def test_measure_d020_population_returns_one_raw_record_per_pose(self):
        reference = load_xac_reference()
        receptor_positions, receptor_atomic_numbers = (
            load_3rey_receptor_heavy_atoms()
        )

        conformer = reference.GetConformer()
        ligand_coordinates = np.asarray(
            conformer.GetPositions(),
            dtype=float,
        )

        translated = ligand_coordinates + np.array(
            [1.0, 0.5, -0.25],
        )

        reconstructed = np.stack(
            [
                ligand_coordinates,
                translated,
            ],
            axis=0,
        )

        results = measure_d020_population(
            reconstructed_coordinates=reconstructed,
            reference_molecule=reference,
            receptor_positions=receptor_positions,
            receptor_atomic_numbers=receptor_atomic_numbers,
            pose_template=reference,
        )

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["orient_index"], 1)
        self.assertEqual(results[1]["orient_index"], 2)

        self.assertTrue(
            np.isfinite(results[0]["rmsd"])
        )
        self.assertTrue(
            np.isfinite(results[0]["d_rel"])
        )
        self.assertTrue(
            np.isfinite(results[1]["rmsd"])
        )
        self.assertTrue(
            np.isfinite(results[1]["d_rel"])
        )

        self.assertAlmostEqual(
            results[0]["rmsd"],
            0.0,
            places=10,
        )

        self.assertNotEqual(
            results[0]["rmsd"],
            results[1]["rmsd"],
        )

    def test_measure_d021_persisted_orientation_population_returns_7989_records(
        self,
    ):
        archive_dir = (
            ROOT
            / "references/stage5/dock385/d021_orientation_archive"
        )

        results = measure_d021_persisted_orientation_population(
            archive_dir / "orientations_mol000001_comr.gz",
            archive_dir / "orientations_mol000001_coml.gz",
            archive_dir / "orientations_mol000001_rot.gz",
        )

        self.assertEqual(len(results), 7989)

        for expected_index, record in enumerate(results, start=1):
            self.assertEqual(
                record["orient_index"],
                expected_index,
            )
            self.assertTrue(np.isfinite(record["rmsd"]))
            self.assertTrue(np.isfinite(record["d_rel"]))

    def test_parse_rdock_sd_archive_preserves_all_50_records_and_scores(self):
        archive = (
            ROOT
            / "references/stage5/"
            "d021_rdock_3REY_XAC_single_shot_qualification_20260917/"
            "XAC_3REY_run2.sd"
        )

        records = parse_rdock_sd_archive(
            archive,
            expected_pose_count=50,
        )

        self.assertEqual(len(records), 50)

        self.assertEqual(records[0].pose_id, 1)
        self.assertEqual(records[-1].pose_id, 50)

        self.assertEqual(
            records[0].name,
            "XAC_3REY_CCD_neutral",
        )

        self.assertAlmostEqual(
            records[0].score,
            -1.28039,
            places=5,
        )

        self.assertAlmostEqual(
            records[27].score,
            -13.2078,
            places=4,
        )

        self.assertAlmostEqual(
            records[43].score,
            2.13362,
            places=5,
        )

        self.assertAlmostEqual(
            records[49].score,
            -6.7006,
            places=4,
        )

        self.assertTrue(
            all(
                record.sd_block.lstrip().startswith(
                    "XAC_3REY_CCD_neutral"
                )
                for record in records
            )
        )

    def test_reconstruct_all_50_rdock_run2_poses(self):
        archive = (
            ROOT
            / "references/stage5/"
            "d021_rdock_3REY_XAC_single_shot_qualification_20260917/"
            "XAC_3REY_run2.sd"
        )

        records = parse_rdock_sd_archive(
            archive,
            expected_pose_count=50,
        )

        molecules = [
            reconstruct_rdock_pose_molecule(record)
            for record in records
        ]

        self.assertEqual(len(molecules), 50)

        for pose_id, molecule in enumerate(molecules, start=1):
            with self.subTest(pose_id=pose_id):
                self.assertEqual(
                    molecule.GetNumHeavyAtoms(),
                    EXPECTED_HEAVY_ATOMS,
                )
                self.assertEqual(
                    molecule.GetNumConformers(),
                    EXPECTED_CONFORMERS,
                )

                conformer = molecule.GetConformer()

                for atom_index in range(molecule.GetNumAtoms()):
                    position = conformer.GetAtomPosition(atom_index)

                    self.assertTrue(np.isfinite(position.x))
                    self.assertTrue(np.isfinite(position.y))
                    self.assertTrue(np.isfinite(position.z))

    def test_reconstruct_rdock_pose_preserves_first_pose_coordinates(self):
        archive = (
            ROOT
            / "references/stage5/"
            "d021_rdock_3REY_XAC_single_shot_qualification_20260917/"
            "XAC_3REY_run2.sd"
        )

        records = parse_rdock_sd_archive(
            archive,
            expected_pose_count=50,
        )

        molecule = reconstruct_rdock_pose_molecule(records[0])

        self.assertEqual(
            molecule.GetNumAtoms(),
            35,
        )
        self.assertEqual(
            molecule.GetNumHeavyAtoms(),
            EXPECTED_HEAVY_ATOMS,
        )
        self.assertEqual(
            molecule.GetNumConformers(),
            EXPECTED_CONFORMERS,
        )

        position = molecule.GetConformer().GetAtomPosition(0)

        self.assertAlmostEqual(position.x, 49.7176, places=4)
        self.assertAlmostEqual(position.y, 26.2972, places=4)
        self.assertAlmostEqual(position.z, 46.2933, places=4)


if __name__ == "__main__":
    unittest.main()
