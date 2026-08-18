from pathlib import Path
import re

from meeko import PDBQTMolecule, RDKitMolCreate
import prolif as plf
from rdkit import Chem
from rdkit.Chem import rdMolAlign

from test_native_reader_controls import (
    find_anchor_interactions,
    interaction_names,
    load_protein,
    run_interaction_reader,
)


ROOT = Path("references/stage5")

POSES_PDBQT = (
    ROOT
    / "docking"
    / "3REY"
    / "vina"
    / "3REY_XAC_poses.pdbqt"
)

PREPARED_LIGAND_PDBQT = (
    ROOT
    / "docking"
    / "3REY"
    / "3REY_XAC.pdbqt"
)

NATIVE_LIGAND_SDF = (
    ROOT
    / "native_complexes"
    / "3REY"
    / "3REY_XAC_native_pH7.4_restored.sdf"
)

NATIVE_RECEPTOR_PQR = (
    ROOT
    / "native_complexes"
    / "3REY"
    / "3REY_receptor_pH7.4_restored.pqr"
)

EXPECTED_POSES = 20
RMSD_CUTOFF = 2.0

EXPECTED_ANCHOR_CLASSES = {
    "phe168": {
        "Hydrophobic",
        "VdWContact",
    },
    "asn253": {
        "HBAcceptor",
        "VdWContact",
    },
}


def parse_model_blocks(path):
    text = path.read_text()
    blocks = re.findall(
        r"MODEL\s+\d+\n(.*?)ENDMDL",
        text,
        flags=re.DOTALL,
    )

    if len(blocks) != EXPECTED_POSES:
        raise AssertionError(
            f"Expected {EXPECTED_POSES} MODEL blocks, "
            f"found {len(blocks)}."
        )

    return blocks


def parse_index_map_from_text(text):
    pairs = []

    for line in text.splitlines():
        if not line.startswith("REMARK INDEX MAP"):
            continue

        values = [int(value) for value in line.split()[3:]]

        if len(values) % 2 != 0:
            raise AssertionError(
                "REMARK INDEX MAP contains an odd number "
                "of integers."
            )

        for index in range(0, len(values), 2):
            pairs.append(
                (
                    values[index],
                    values[index + 1],
                )
            )

    if not pairs:
        raise AssertionError("No REMARK INDEX MAP records found.")

    return tuple(pairs)


def parse_vina_score(block):
    for line in block.splitlines():
        if line.startswith("REMARK VINA RESULT"):
            return float(line.split()[3])

    raise AssertionError("Missing REMARK VINA RESULT record.")


def load_native_ligand():
    native = Chem.SDMolSupplier(
        str(NATIVE_LIGAND_SDF),
        removeHs=False,
    )[0]

    if native is None:
        raise ValueError(
            f"Failed to load native ligand: {NATIVE_LIGAND_SDF}"
        )

    return native


def heavy_smiles(mol):
    return Chem.MolToSmiles(
        Chem.RemoveHs(mol),
        canonical=True,
        isomericSmiles=True,
    )


def reconstruct_poses():
    pdbqt_mol = PDBQTMolecule.from_file(
        str(POSES_PDBQT),
        poses_to_read=EXPECTED_POSES,
    )

    pose_count = pdbqt_mol._pose_data["n_poses"]
    if pose_count != EXPECTED_POSES:
        raise AssertionError(
            f"Expected {EXPECTED_POSES} parsed poses, "
            f"found {pose_count}."
        )

    molecules = RDKitMolCreate.from_pdbqt_mol(pdbqt_mol)

    if len(molecules) != 1 or molecules[0] is None:
        raise AssertionError(
            "Expected exactly one reconstructed ligand molecule."
        )

    pose_mol = molecules[0]

    if pose_mol.GetNumConformers() != EXPECTED_POSES:
        raise AssertionError(
            f"Expected {EXPECTED_POSES} reconstructed conformers, "
            f"found {pose_mol.GetNumConformers()}."
        )

    scores = list(pdbqt_mol._pose_data["free_energies"])
    if len(scores) != EXPECTED_POSES:
        raise AssertionError(
            f"Expected {EXPECTED_POSES} Vina scores, "
            f"found {len(scores)}."
        )

    return pose_mol, scores


def assert_index_maps_are_stable(blocks):
    prepared_map = parse_index_map_from_text(
        PREPARED_LIGAND_PDBQT.read_text()
    )

    for rank, block in enumerate(blocks, start=1):
        pose_map = parse_index_map_from_text(block)

        if pose_map != prepared_map:
            raise AssertionError(
                f"Pose {rank} index map differs from prepared ligand."
            )

    return prepared_map


def copy_single_conformer(mol, conformer_index):
    single = Chem.Mol(mol)
    conformer = Chem.Conformer(
        mol.GetConformer(conformer_index)
    )

    single.RemoveAllConformers()
    single.AddConformer(
        conformer,
        assignId=True,
    )

    return single


def calculate_rmsd_by_pose(pose_mol, native):
    pose_heavy = Chem.RemoveHs(pose_mol)
    native_heavy = Chem.RemoveHs(native)

    rmsds = []

    for conformer_index in range(EXPECTED_POSES):
        rmsd = rdMolAlign.CalcRMS(
            pose_heavy,
            native_heavy,
            conformer_index,
            0,
            symmetrizeConjugatedTerminalGroups=True,
        )

        rmsds.append(float(rmsd))

    return rmsds


def evaluate_pose_interactions(protein, pose_mol, conformer_index):
    single = copy_single_conformer(
        pose_mol,
        conformer_index,
    )

    ligand = plf.Molecule.from_rdkit(single)
    interactions = run_interaction_reader(
        protein,
        ligand,
    )

    phe168 = find_anchor_interactions(
        interactions,
        "PHE",
        168,
    )

    asn253 = find_anchor_interactions(
        interactions,
        "ASN",
        253,
    )

    phe168_interactions = interaction_names(phe168)
    asn253_interactions = interaction_names(asn253)

    return {
        "phe168_recovered": (
            EXPECTED_ANCHOR_CLASSES["phe168"]
            <= phe168_interactions
        ),
        "phe168_interactions": sorted(
            phe168_interactions
        ),
        "asn253_recovered": (
            EXPECTED_ANCHOR_CLASSES["asn253"]
            <= asn253_interactions
        ),
        "asn253_interactions": sorted(
            asn253_interactions
        ),
    }


def validate_chemistry(pose_mol, native):
    pose_heavy = Chem.RemoveHs(pose_mol)
    native_heavy = Chem.RemoveHs(native)

    pose_smiles = Chem.MolToSmiles(
        pose_heavy,
        canonical=True,
        isomericSmiles=True,
    )

    native_smiles = Chem.MolToSmiles(
        native_heavy,
        canonical=True,
        isomericSmiles=True,
    )

    if pose_smiles != native_smiles:
        raise AssertionError(
            "Reconstructed pose chemistry differs from native XAC: "
            f"{pose_smiles} != {native_smiles}"
        )

    formal_charge = Chem.GetFormalCharge(pose_mol)
    if formal_charge != 1:
        raise AssertionError(
            f"Reconstructed formal charge is {formal_charge}, "
            "expected +1."
        )

    heavy_atoms = pose_mol.GetNumHeavyAtoms()
    if heavy_atoms != 31:
        raise AssertionError(
            f"Reconstructed heavy-atom count is {heavy_atoms}, "
            "expected 31."
        )

    return {
        "heavy_smiles": pose_smiles,
        "formal_charge": formal_charge,
        "heavy_atoms": heavy_atoms,
    }


def main():
    for path in (
        POSES_PDBQT,
        PREPARED_LIGAND_PDBQT,
        NATIVE_LIGAND_SDF,
        NATIVE_RECEPTOR_PQR,
    ):
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Required non-empty input missing: {path}"
            )

    blocks = parse_model_blocks(POSES_PDBQT)
    scores_from_blocks = [
        parse_vina_score(block)
        for block in blocks
    ]

    index_map = assert_index_maps_are_stable(blocks)

    native = load_native_ligand()
    pose_mol, scores = reconstruct_poses()

    if scores != scores_from_blocks:
        raise AssertionError(
            "Scores parsed by Meeko differ from PDBQT block scores."
        )

    chemistry = validate_chemistry(
        pose_mol,
        native,
    )

    protein_results = load_protein(NATIVE_RECEPTOR_PQR)
    protein = protein_results["protein"]

    rmsds = calculate_rmsd_by_pose(
        pose_mol,
        native,
    )

    results = []
    first_success = None

    for conformer_index in range(EXPECTED_POSES):
        interaction_result = evaluate_pose_interactions(
            protein,
            pose_mol,
            conformer_index,
        )

        rank = conformer_index + 1
        rmsd_pass = rmsds[conformer_index] <= RMSD_CUTOFF
        pose_pass = (
            rmsd_pass
            and interaction_result["phe168_recovered"]
            and interaction_result["asn253_recovered"]
        )

        result = {
            "rank": rank,
            "vina_score": scores[conformer_index],
            "rmsd": rmsds[conformer_index],
            "rmsd_pass": rmsd_pass,
            "pose_pass": pose_pass,
            **interaction_result,
        }

        results.append(result)

        if pose_pass and first_success is None:
            first_success = rank

    print("3REY / XAC self-redocking validation")
    print("=" * 72)
    print("Parsed poses:", EXPECTED_POSES)
    print("Index-map pairs:", len(index_map))
    print("Heavy-atom canonical SMILES:", chemistry["heavy_smiles"])
    print("Formal charge:", chemistry["formal_charge"])
    print("Heavy atoms:", chemistry["heavy_atoms"])
    print(
        "Required Phe168 classes:",
        sorted(EXPECTED_ANCHOR_CLASSES["phe168"]),
    )
    print(
        "Required Asn253 classes:",
        sorted(EXPECTED_ANCHOR_CLASSES["asn253"]),
    )
    print("Native receptor:", NATIVE_RECEPTOR_PQR)
    print("Anchor numbering audit:", protein_results["anchor_audit"])
    print()
    print(
        "Rank,VinaScore,RMSD,Phe168Recovered,"
        "Phe168Interactions,Asn253Recovered,"
        "Asn253Interactions,PosePass"
    )

    for result in results:
        print(
            f"{result['rank']},"
            f"{result['vina_score']:.3f},"
            f"{result['rmsd']:.3f},"
            f"{result['phe168_recovered']},"
            f"{';'.join(result['phe168_interactions'])},"
            f"{result['asn253_recovered']},"
            f"{';'.join(result['asn253_interactions'])},"
            f"{result['pose_pass']}"
        )

    print()

    if first_success is None:
        print(
            "3REY / XAC RESULT: FAIL "
            "(no retained pose satisfied RMSD <= 2.0 A "
            "AND Phe168 AND Asn253 recovery)"
        )
    else:
        print(
            "3REY / XAC RESULT: PASS "
            f"(first successful pose rank: {first_success})"
        )


if __name__ == "__main__":
    main()
