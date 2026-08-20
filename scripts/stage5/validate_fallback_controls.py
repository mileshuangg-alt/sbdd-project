from pathlib import Path

from test_native_reader_controls import (
    find_anchor_interactions,
    interaction_names,
    load_ligand,
    load_protein,
    run_interaction_reader,
)


def evaluate_control(
    pdb_id: str,
    receptor_path: Path,
    ligand_path: Path,
) -> dict:
    """Evaluate anchor interactions for one perturbed fallback control."""

    protein_results = load_protein(
        receptor_path
    )

    protein = protein_results["protein"]

    ligand = load_ligand(
        ligand_path
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

    phe168_classes = sorted(
        interaction_names(
            phe168
        )
    )

    asn253_classes = sorted(
        interaction_names(
            asn253
        )
    )

    control_result = {
        "pdb_id": pdb_id,
        "phe168_interactions": phe168_classes,
        "asn253_interactions": asn253_classes,
    }

    return control_result


def print_results(
    results: list[dict],
) -> None:
    """Print perturbed-control interaction results."""

    print()
    print(
        "Stage-5 fallback subtle-negative controls"
    )

    print("=" * 72)

    for result in results:
        print()
        print(
            result["pdb_id"]
        )

        print(
            "  Phe168:",
            result[
                "phe168_interactions"
            ],
        )

        print(
            "  Asn253:",
            result[
                "asn253_interactions"
            ],
        )


def main() -> list[dict]:
    """Evaluate the three frozen axis-1 / 10-degree controls."""

    controls = [
        {
            "pdb_id": "3REY",
            "receptor_path": Path(
                "references/stage5/native_complexes/3REY/"
                "3REY_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/fallback/"
                "stage3b_candidates/"
                "3REY_axis1_15deg.sdf"
            ),
        },
        {
            "pdb_id": "5OLH",
            "receptor_path": Path(
                "references/stage5/native_complexes/5OLH/"
                "5OLH_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/fallback/"
                "stage3b_candidates/"
                "5OLH_axis1_15deg.sdf"
            ),
        },
        {
            "pdb_id": "5OLO",
            "receptor_path": Path(
                "references/stage5/native_complexes/5OLO/"
                "5OLO_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/fallback/"
                "stage3b_candidates/"
                "5OLO_axis1_15deg.sdf"
            ),
        },
    ]

    results = []

    for control in controls:
        control_result = evaluate_control(
            control["pdb_id"],
            control["receptor_path"],
            control["ligand_path"],
        )

        results.append(
            control_result
        )

    print_results(
        results
    )

    return results


if __name__ == "__main__":
    main()
