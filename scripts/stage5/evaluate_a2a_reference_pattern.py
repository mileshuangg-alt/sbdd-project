from pathlib import Path

import pandas as pd
from rdkit import Chem
from test_native_reader_controls import (
    find_anchor_interactions,
    interaction_names,
    load_protein,
    run_interaction_reader,
)


STAGE3_INPUT = Path(
    "experiments/phase1_diffsbdd/evaluation/stage3_input.sdf"
)

STAGE3_RESULTS = Path(
    "experiments/phase1_diffsbdd/evaluation/structure.csv"
)

RECEPTOR_PATH = Path(
    "experiments/phase1_diffsbdd/evaluation/"
    "prepared_3rfm_pocket_pH7.4_restored.pqr"
)

OUTPUT_PATH = Path(
    "experiments/phase1_diffsbdd/evaluation/"
    "stage5_a2a_reference_pattern.csv"
)


def load_stage5_ids(
    stage3_results_path: Path,
) -> list[int]:
    """Load original molecule IDs that survived Stage 3."""

    results = pd.read_csv(
        stage3_results_path
    )

    survivors = results[
        results["stage3_passes"]
    ]

    stage5_ids = (
        survivors["molecule_id"]
        .astype(int)
        .tolist()
    )

    return stage5_ids


def load_stage5_molecules(
    sdf_path: Path,
    stage5_ids: list[int],
) -> list[tuple[int, Chem.Mol]]:
    """Load Stage-3 survivors with original coordinates and IDs."""

    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        sanitize=False,
        removeHs=False,
    )

    molecules = []

    for mol in supplier:
        if mol is None:
            continue

        if not mol.HasProp(
            "molecule_id"
        ):
            raise ValueError(
                "Stage-3 molecule is missing molecule_id."
            )

        molecule_id = int(
            mol.GetProp(
                "molecule_id"
            )
        )

        if molecule_id in stage5_ids:
            molecules.append(
                (
                    molecule_id,
                    Chem.Mol(mol),
                )
            )

    found_ids = {
        molecule_id
        for molecule_id, _ in molecules
    }

    missing_ids = (
        set(stage5_ids)
        - found_ids
    )

    if missing_ids:
        raise ValueError(
            "Missing Stage-5 molecule IDs: "
            f"{sorted(missing_ids)}"
        )

    return molecules


def evaluate_molecule(
    molecule_id: int,
    molecule: Chem.Mol,
    protein,
) -> dict:
    """Characterize the frozen A2A reference pattern."""

    ligand = load_ligand_from_molecule(
        molecule
    )

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

    phe_classes = sorted(
        interaction_names(
            phe168
        )
    )

    asn_classes = sorted(
        interaction_names(
            asn253
        )
    )

    phe168_reproduced = (
        "Hydrophobic" in phe_classes
        or
        "PiStacking" in phe_classes
    )

    asn253_reproduced = (
        "HBAcceptor" in asn_classes
    )

    reference_pattern_reproduced = (
        phe168_reproduced
        and
        asn253_reproduced
    )

    molecule_result = {
        "molecule_id": molecule_id,
        "phe168_interactions":
            ";".join(phe_classes),
        "asn253_interactions":
            ";".join(asn_classes),
        "phe168_reference_feature":
            phe168_reproduced,
        "asn253_reference_feature":
            asn253_reproduced,
        "a2a_reference_pattern":
            reference_pattern_reproduced,
        "claims_status":
            "claims capped pending gate validation",
        "pose_basis":
            "generator-provided coordinates",
    }

    return molecule_result


def load_ligand_from_molecule(
    molecule: Chem.Mol,
):
    """Convert an existing RDKit pose to ProLIF without changing coordinates."""

    import prolif as plf

    ligand = plf.Molecule.from_rdkit(
        molecule
    )

    return ligand


def save_results(
    results: list[dict],
    output_path: Path,
) -> None:
    """Save Stage-5 A2A characterization results."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(
        results
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Stage-5 characterization saved: "
        f"{output_path}"
    )


def main() -> list[dict]:
    """Run frozen A2A characterization on Stage-3 survivors."""

    stage5_ids = load_stage5_ids(
        STAGE3_RESULTS
    )

    molecules = load_stage5_molecules(
        STAGE3_INPUT,
        stage5_ids,
    )

    protein = load_protein(
        RECEPTOR_PATH
    )["protein"]

    results = []

    for molecule_id, molecule in molecules:
        molecule_result = evaluate_molecule(
            molecule_id,
            molecule,
            protein,
        )

        results.append(
            molecule_result
        )

    save_results(
        results,
        OUTPUT_PATH,
    )

    reproduced = sum(
        result["a2a_reference_pattern"]
        for result in results
    )

    print()
    print(
        f"Stage-3 survivors characterized: "
        f"{len(results)}"
    )

    print(
        f"A2A reference pattern reproduced: "
        f"{reproduced}/{len(results)}"
    )

    print(
        "Claims status: "
        "CAPPED PENDING GATE VALIDATION"
    )

    return results


if __name__ == "__main__":
    main()
