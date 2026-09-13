import json
from pathlib import Path
import tempfile
import unittest

from evaluation.d017_construct_audit import (
    audit_construct,
    parse_coordinate_atoms,
    parse_coordinate_residues,
    parse_fasta,
    parse_reference_spans,
    sha256_file,
    write_audit_artifact,
)
from evaluation.d017_receptor_input import extract_receptor_mmcif
from evaluation.d017_mutation_pocket_audit import (
    audit_mutation_pocket,
    ligand_instances_by_structure,
)


ROOT = Path(__file__).resolve().parents[1]


class D017ConstructAuditTests(unittest.TestCase):
    def test_primary_constructs_are_unambiguous_and_preserve_author_ids(self):
        cases = (
            ("3EML", "A", "ADORA2A_P29274.fasta"),
            ("7XY7", "R", "ADORA2B_P29275.fasta"),
            ("9EHS", "R", "ADORA3_P0DMS8.fasta"),
        )
        for structure_id, chain, fasta in cases:
            with self.subTest(structure_id=structure_id):
                audit = audit_construct(
                    structure_id=structure_id,
                    structure_path=ROOT /
                    "references/stage5/d017/structures/raw" /
                    f"{structure_id}.cif",
                    author_chain=chain,
                    fasta_path=ROOT /
                    "references/stage5/d017/canonical_sequences" /
                    fasta,
                )
                self.assertEqual(audit["status"], "PASS")
                self.assertGreater(
                    audit["coordinate_bearing_canonical_residue_count"], 0)
                self.assertGreaterEqual(
                    audit["coordinate_bearing_noncanonical_residue_count"], 0)
                mapping = audit["construct_to_canonical_mapping"]
                self.assertTrue(mapping)
                self.assertEqual(mapping[0]["author_residue"]["chain"], chain)
                self.assertIn("insertion_code", mapping[0]["author_residue"])

    def test_engineered_coordinate_segment_is_reported_when_present(self):
        audit = audit_construct(
            structure_id="3EML",
            structure_path=ROOT /
            "references/stage5/d017/structures/raw/3EML.cif",
            author_chain="A",
            fasta_path=ROOT /
            "references/stage5/d017/canonical_sequences/ADORA2A_P29274.fasta",
        )
        self.assertGreater(
            audit["coordinate_bearing_noncanonical_residue_count"], 0)
        self.assertTrue(audit["non_receptor_engineered_construct_spans"])
        self.assertTrue(
            audit["canonical_residues_without_experimental_coordinates"])

    def test_fasta_and_hash_parsing(self):
        fasta = ROOT / "references/stage5/d017/canonical_sequences/ADORA2A_P29274.fasta"
        accession, sequence = parse_fasta(fasta)
        self.assertEqual(accession, "P29274")
        self.assertEqual(len(sequence), 412)
        self.assertEqual(
            sha256_file(fasta),
            "fa327e00c2245b9aa5aa65816f078bdd5664de1531fb8404c2b5f60d8e96f239")
        active_config = ROOT / "references/stage5/d017/usalign_20220227_config_v2.json"
        self.assertEqual(
            sha256_file(active_config),
            "6b98a09dcdc103a9c86aa640bc68a72e1685528ff7b5848df326048a99b2d6e6",
        )
        adora1 = ROOT / "references/stage5/d017/canonical_sequences/ADORA1_P30542.fasta"
        self.assertEqual(
            sha256_file(adora1),
            "b737a73f9d6c134d0df89ce558deb1e72b84309df0967db13675b7205dfc2c89",
        )

    def test_ambiguous_when_no_reference_span_matches_fasta(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "wrong.fasta"
            fasta.write_text(">sp|P99999|TEST_HUMAN test\nACDE\n")
            audit = audit_construct(
                structure_id="3EML",
                structure_path=ROOT /
                "references/stage5/d017/structures/raw/3EML.cif",
                author_chain="A",
                fasta_path=fasta,
            )
        self.assertEqual(audit["status"], "AMBIGUOUS")
        self.assertIn(
            "no deposited reference span matches",
            audit["ambiguous_regions"][0])

    def test_singleton_reference_category_matches_loop_reference_category(
            self):
        loop_spans = parse_reference_spans(
            ROOT / "references/stage5/d017/structures/raw/4UG2.cif", "A"
        )
        with tempfile.TemporaryDirectory() as directory:
            singleton = Path(directory) / "singleton.cif"
            singleton.write_text(
                """data_TEST
_struct_ref_seq.align_id 1
_struct_ref_seq.ref_id 1
_struct_ref_seq.pdbx_PDB_id_code TEST
_struct_ref_seq.pdbx_strand_id A
_struct_ref_seq.seq_align_beg 1
_struct_ref_seq.seq_align_end 317
_struct_ref_seq.pdbx_db_accession P29274
_struct_ref_seq.db_align_beg 1
_struct_ref_seq.db_align_end 317
#
"""
            )
            singleton_spans = parse_reference_spans(singleton, "A")
        self.assertEqual(singleton_spans, loop_spans[:1])

    def test_serialization_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            write_audit_artifact({"schema_version": 1, "records": []}, output)
            self.assertEqual(json.loads(output.read_text()), {
                             "schema_version": 1, "records": []})

    def test_coordinate_parser_uses_author_chain(self):
        residues = parse_coordinate_residues(
            ROOT / "references/stage5/d017/structures/raw/3EML.cif", "A"
        )
        self.assertEqual(residues[0].chain, "A")
        self.assertEqual(residues[0].number, "3")

    def test_position_only_mmcif_extraction_preserves_coordinates_and_flags_mutations(
            self):
        with tempfile.TemporaryDirectory() as directory:
            source = ROOT / "references/stage5/d017/structures/raw/9EHS.cif"
            output = Path(directory) / "9EHS_R.cif"
            mapping = extract_receptor_mmcif(
                structure_id="9EHS",
                structure_path=source,
                author_chain="R",
                fasta_path=ROOT /
                "references/stage5/d017/canonical_sequences/ADORA3_P0DMS8.fasta",
                output_path=output,
            )
            self.assertTrue(any(item["mutation_flag"]
                            for item in mapping["residue_mappings"]))
            atom_site_headers = [
                line
                for line in output.read_text().splitlines(keepends=True)
                if line.startswith("_atom_site.")
            ]
            self.assertTrue(atom_site_headers)
            self.assertTrue(
                all(line.endswith(" \n") for line in atom_site_headers)
            )

            self.assertEqual(sum(item["mutation_flag"]
                             for item in mapping["residue_mappings"]), 2)
            self.assertTrue(mapping["excluded_coordinate_bearing_residues"])
            source_atom = next(atom for atom in parse_coordinate_atoms(source, "R") if int(
                atom["_atom_site.id"]) == mapping["residue_mappings"][0]["source_atom_ids"][0])
            output_atom = next(
                atom for atom in parse_coordinate_atoms(output, "R")
                if atom["_atom_site.id"] == source_atom["_atom_site.id"]
            )
            self.assertEqual(
                output_atom["_atom_site.Cartn_x"],
                source_atom["_atom_site.Cartn_x"])
            self.assertEqual(
                output_atom["_atom_site.Cartn_y"],
                source_atom["_atom_site.Cartn_y"])
            self.assertEqual(
                output_atom["_atom_site.Cartn_z"],
                source_atom["_atom_site.Cartn_z"])
            self.assertEqual(
                output_atom["_atom_site.auth_seq_id"],
                source_atom["_atom_site.auth_seq_id"])

    def test_mmcif_extraction_preserves_insertion_code(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = directory_path / "source.cif"
            source.write_text(
                """data_TEST
#
loop_
_struct_ref_seq.pdbx_strand_id
_struct_ref_seq.seq_align_beg
_struct_ref_seq.seq_align_end
_struct_ref_seq.db_align_beg
_struct_ref_seq.db_align_end
_struct_ref_seq.pdbx_db_accession
R 1 1 1 1 P00001
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM 1 C CA . ALA R 1 1 A 1.23456 2.34567 3.45678 1.00 2.00 ? 10 ALA R CA 1
#
"""
            )
            fasta = directory_path / "canonical.fasta"
            fasta.write_text(">sp|P00001|TEST_HUMAN test\nA\n")
            output = directory_path / "output.cif"
            extract_receptor_mmcif(
                structure_id="TEST", structure_path=source, author_chain="R",
                fasta_path=fasta, output_path=output,
            )
            atom = parse_coordinate_atoms(output, "R")[0]
            self.assertEqual(atom["_atom_site.pdbx_PDB_ins_code"], "A")
            self.assertEqual(atom["_atom_site.auth_seq_id"], "10")
            self.assertEqual(atom["_atom_site.Cartn_x"], "1.23456")

    def test_position_only_mmcif_serialization_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "3EML_A.cif"
            kwargs = {
                "structure_id": "3EML",
                "structure_path": ROOT /
                "references/stage5/d017/structures/raw/3EML.cif",
                "author_chain": "A",
                "fasta_path": ROOT /
                "references/stage5/d017/canonical_sequences/ADORA2A_P29274.fasta",
                "output_path": output,
            }
            first = extract_receptor_mmcif(**kwargs)
            first_bytes = output.read_bytes()
            second = extract_receptor_mmcif(**kwargs)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, output.read_bytes())

    def test_mutation_pocket_audit_uses_frozen_manifest_ligand(self):
        mapping_path = ROOT / "references/stage5/d017/receptor_inputs/position_only_mapping.json"
        manifest_path = ROOT / "references/stage5/d017/calibration_structure_manifest.json"
        mapping = json.loads(mapping_path.read_text())
        manifest = json.loads(manifest_path.read_text())
        receptor = next(
            item for item in mapping["receptor_inputs"] if item["structure_id"] == "9EHS")
        mutation = next(
            item for item in receptor["residue_mappings"] if item["mutation_flag"])
        audit = audit_mutation_pocket(
            structure_id="9EHS",
            author_chain="R",
            structure_path=Path(receptor["source_structure"]["path"]),
            ligand_instance=ligand_instances_by_structure(manifest)[("9EHS", "R")],
            mutation=mutation,
        )
        self.assertFalse(audit["in_ligand_defined_pocket"])
        self.assertEqual(audit["ligand_instance"]["component"], "A1BII")
        self.assertEqual(
            audit["minimum_distance_pair"]["receptor_atom"]["atom_site_id"],
            "4886",
        )
        self.assertIn(
            int(audit["minimum_distance_pair"]["receptor_atom"]["atom_site_id"]),
            mutation["source_atom_ids"],
        )


if __name__ == "__main__":
    unittest.main()
