import csv
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


MORGAN_RADIUS = 2
MORGAN_FP_SIZE = 2048
MORGAN_USE_CHIRALITY = True


def load_stage4_molecule_ids(structur_csv_path):
    """ Load molecule IDs that passed the Stage 3 gate."""

    structure_csv_path = Path(structur_csv_path)

    if not structure_csv_path.exists():
        raise FileNotFoundError(
            f"Stage 3 results file not found: {structure_csv_path}")

    stage4_ids = []

    with structure_csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row["stage3_passes"] == "True":
                stage4_ids.append(int(row["molecule_id"]))
    return stage4_ids


def load_stage4_molecules(sdf_path, stage4_ids):
    """Load Stage 4 molecules while preserving original molecule IDs."""

    sdf_path = Path(sdf_path)

    if not sdf_path.exists():
        raise FileNotFoundError(f"Stage 4 SDF file not found: {sdf_path}")

    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        removeHs=False,
        sanitize=True,
    )

    molecules_by_id = {}

    # Check that all Stage 4 molecules have a molecule_id property and build a
    # mapping

    for mol in supplier:
        if mol is None:
            continue
        if not mol.HasProp("molecule_id"):
            raise ValueError(
                "Stage 4 input molecule is missing molecule_id provenance."
            )

        molecule_id = int(mol.GetProp("molecule_id"))

        if molecule_id in stage4_ids:
            molecules_by_id[molecule_id] = mol

    selected = []

    for molecule_id in stage4_ids:
        if molecule_id not in molecules_by_id:
            raise ValueError(
                f"Stage 4 molecule_id={molecule_id} not found in input SDF."
            )

        selected.append(
            (molecule_id, molecules_by_id[molecule_id])
        )

    return selected


def make_morgan_generator():
    """ Create the predefined Stage 4 Moran fingerprint generator. """

    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=MORGAN_RADIUS,
        fpSize=MORGAN_FP_SIZE,
        includeChirality=MORGAN_USE_CHIRALITY,
    )
    return generator


def fingerprint_molecules(molecules):
    """ Generate Morgan fingerprints while preserving original molecule IDs. """

    generator = make_morgan_generator()

    fingerprints = []

    for molecule_id, mol in molecules:
        fingerprint = generator.GetFingerprint(mol)
        fingerprints.append((molecule_id, fingerprint))

    return fingerprints


def calculate_tanimoto(fingerprint1, fingerprint2):
    """ Calculate the Tanimoto similarity between two fingerprints. """

    similarity = DataStructs.TanimotoSimilarity(fingerprint1, fingerprint2)

    return similarity

# Set up complete, move on to Stage 4A analysis of fingerprints and novelty.


def evaluate_internal_similarity(fingerprints):
    """ Evaluate the internal similarity of a set of fingerprints. """

    similarities = []

    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            molecule_id1, fp1 = fingerprints[i]
            molecule_id2, fp2 = fingerprints[j]
            similarity = calculate_tanimoto(fp1, fp2)
            similarities.append({
                "molecule_id1": molecule_id1,
                "molecule_id2": molecule_id2,
                "similarity": similarity
            })

    return similarities


def summarize_internal_similarity(similarities):
    """Find the nearest generated neighbor for each molecule."""

    nearest_neighbors = {}

    for comparison in similarities:
        molecule_id1 = comparison["molecule_id1"]
        molecule_id2 = comparison["molecule_id2"]
        similarity = comparison["similarity"]

        for molecule_id, neighbor_id in [
            (molecule_id1, molecule_id2),
            (molecule_id2, molecule_id1),
        ]:
            if (
                molecule_id not in nearest_neighbors
                or similarity
                > nearest_neighbors[molecule_id][
                    "nearest_generated_similarity"
                ]
            ):
                nearest_neighbors[molecule_id] = {
                    "molecule_id": molecule_id,
                    "nearest_generated_neighbor_id": neighbor_id,
                    "nearest_generated_similarity": similarity,
                }

    return list(nearest_neighbors.values())


def summarize_pairwise_distribution(similarities):
    """ Summarize the pairwise similarity distribution. """

    similarity_values = [comparison["similarity"]
                         for comparison in similarities]

    if len(similarity_values) == 0:
        return {
            "mean_similarities": None,
            "std": None,
            "min": None,
            "max": None,
            "median": None
        }

    summary = {
        "number_pairs": len(similarity_values),
        "mean_similarity": float(np.mean(similarity_values)),
        "median_similarity": float(np.median(similarity_values)),
        "min_similarity": float(np.min(similarity_values)),
        "max_similarity": float(np.max(similarity_values)),
        "std_similarity": float(np.std(similarity_values, ddof=0)),
    }

    return summary

# Stage 4A analysis complete, move on to Stage 4B analysis of novelty
# against the reference ligand set.


def load_target_reference_ligands(reference_csv_path):
    """Load the reference ligand set for a given target."""

    reference_csv_path = Path(reference_csv_path)

    if not reference_csv_path.exists():
        raise FileNotFoundError(
            f"Target reference file not found: {reference_csv_path}")

    reference_ligands = []

    with reference_csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            smiles = row["canonical_smiles"]
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(
                    f"Could not parse target reference structure: {smiles}")

            reference_ligands.append({
                "canonical_smiles": smiles,
                "molecule_chembl_ids": row["molecule_chembl_ids"],
                "mol": mol,
            })
    return reference_ligands


def fingerprint_target_reference_ligands(reference_ligands):
    """Generate Morgan fingerprints for the reference ligand set."""

    generator = make_morgan_generator()

    fingerprints = []

    for ligand in reference_ligands:
        mol = ligand["mol"]
        fingerprint = generator.GetFingerprint(mol)
        fingerprints.append({
            "canonical_smiles": ligand["canonical_smiles"],
            "molecule_chembl_ids": ligand["molecule_chembl_ids"],
            "fingerprint": fingerprint,
        })

    return fingerprints


def evaluate_target_similarity(generated_fingerprints, reference_fingerprints):
    """Evaluate the similarity of generated molecules to the reference set."""

    results = []

    if not reference_fingerprints:
        raise ValueError("Target reference ligand set is empty.")

    for molecule_id, fingerprint in generated_fingerprints:
        comparisons = []

        for reference in reference_fingerprints:
            similarity = calculate_tanimoto(
                fingerprint, reference["fingerprint"])
            comparisons.append({
                "molecule_chembl_ids": reference["molecule_chembl_ids"],
                "canonical_smiles": reference["canonical_smiles"],
                "similarity": similarity,
            })
        comparisons.sort(key=lambda x: x["similarity"], reverse=True)

        nearest = comparisons[0]
        top5 = comparisons[:5]

        results.append({
            "molecule_id": molecule_id,
            "nearest_target_ligand_ids": nearest["molecule_chembl_ids"],
            "nearest_target_ligand_smiles": nearest["canonical_smiles"],
            "nearest_target_similarity": nearest["similarity"],
            "target_top5_mean_similarity": float(np.mean([c["similarity"] for c in top5])),
            "target_reference_count": len(reference_fingerprints), })
    return results


def summarize_target_similarity(results):
    """Summarize target space similarity across generated molecules."""

    nearest_values = [result["nearest_target_similarity"]
                      for result in results]
    top5_values = [result["target_top5_mean_similarity"]
                   for result in results]
    results_summary = {
        "number_molecules": len(results),
        "mean_nearest_similarity": float(np.mean(nearest_values)),
        "std_nearest_similarity": float(np.std(nearest_values, ddof=0)),
        "median_nearest_similarity": float(np.median(nearest_values)),
        "min_nearest_similarity": float(np.min(nearest_values)),
        "max_nearest_similarity": float(np.max(nearest_values)),
        "mean_top5_similarity": float(np.mean(top5_values)),
        "std_top5_similarity": float(np.std(top5_values, ddof=0)),
    }
    return results_summary


def save_target_similarity_results(results, output_path):
    """Save molecule-level Stage 4B results for the target similarity to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "molecule_id",
        "nearest_target_ligand_ids",
        "nearest_target_ligand_smiles",
        "nearest_target_similarity",
        "target_top5_mean_similarity",
        "target_reference_count",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(results)
    print(f"Saved Stage 4B target similarity results to {output_path}")


def load_approved_drug_reference(reference_csv_path):
    """Load the frozen approved-drug reference set."""

    reference_csv_path = Path(reference_csv_path)

    if not reference_csv_path.exists():
        raise FileNotFoundError(
            f"Approved-drug reference file not found: "
            f"{reference_csv_path}"
        )

    approved_drugs = []

    with reference_csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            smiles = row["canonical_smiles"]

            mol = Chem.MolFromSmiles(smiles)

            if mol is None:
                raise ValueError(
                    f"Could not parse approved-drug structure: {smiles}"
                )
            approved_drugs.append({
                "canonical_smiles": smiles,
                "parent_molecule_chembl_id": row["parent_molecule_chembl_id"],
                "parent_pref_name": row["parent_pref_name"],
                "approved_chembl_ids": row["approved_chembl_ids"],
                "approved_pref_names": row["approved_pref_names"],
                "first_approvals": row["first_approvals"],
                "withdrawn_flags": row["withdrawn_flags"],
                "mol": mol,
            })
    return approved_drugs


def fingerprint_approved_drugs(approved_drugs):
    """Generate Morgan fingerprints for approved-drug reference structures."""

    generator = make_morgan_generator()

    fingerprints = []

    for drug in approved_drugs:
        fingerprint = generator.GetFingerprint(drug["mol"])
        fingerprints.append({
            "parent_molecule_chembl_id": drug["parent_molecule_chembl_id"],
            "parent_pref_name": drug["parent_pref_name"],
            "approved_chembl_ids": drug["approved_chembl_ids"],
            "approved_pref_names": drug["approved_pref_names"],
            "first_approvals": drug["first_approvals"],
            "withdrawn_flags": drug["withdrawn_flags"],
            "canonical_smiles": drug["canonical_smiles"],
            "fingerprint": fingerprint,

        })

    return fingerprints


def evaluate_approved_drug_similarity(
        generated_fingerprints,
        approved_fingerprints):
    """Compare generated molecules against approved-drug chemical space."""

    if not approved_fingerprints:
        raise ValueError("Approved-drug reference set is empty.")

    results = []

    for molecule_id, fingerprint in generated_fingerprints:
        comparisons = []

        for approved_drug in approved_fingerprints:
            similarity = calculate_tanimoto(
                fingerprint,
                approved_drug["fingerprint"]
            )

            comparisons.append({
                "parent_molecule_chembl_id":
                    approved_drug["parent_molecule_chembl_id"],
                "parent_pref_name":
                    approved_drug["parent_pref_name"],
                "approved_chembl_ids":
                    approved_drug["approved_chembl_ids"],
                "approved_pref_names":
                    approved_drug["approved_pref_names"],
                "first_approvals":
                    approved_drug["first_approvals"],
                "withdrawn_flags":
                    approved_drug["withdrawn_flags"],
                "canonical_smiles":
                    approved_drug["canonical_smiles"],
                "similarity":
                    similarity,
            })

        comparisons.sort(
            key=lambda x: x["similarity"],
            reverse=True
        )

        nearest = comparisons[0]
        top5 = comparisons[:5]

        results.append({
            "molecule_id":
                molecule_id,
            "nearest_approved_parent_id":
                nearest["parent_molecule_chembl_id"],
            "nearest_approved_parent_name":
                nearest["parent_pref_name"],
            "nearest_approved_drug_ids":
                nearest["approved_chembl_ids"],
            "nearest_approved_drug_names":
                nearest["approved_pref_names"],
            "nearest_approved_drug_smiles":
                nearest["canonical_smiles"],
            "nearest_approved_first_approvals":
                nearest["first_approvals"],
            "nearest_approved_withdrawn_flags":
                nearest["withdrawn_flags"],
            "nearest_approved_similarity":
                nearest["similarity"],
            "approved_top5_mean_similarity":
                float(np.mean([
                    comparison["similarity"]
                    for comparison in top5
                ])),
            "approved_reference_count":
                len(approved_fingerprints),
        })

    return results


def summarize_approved_drug_similarity(results):
    """Summarize approved-drug-space simiarity across generated molecules."""

    nearest_values = [
        result["nearest_approved_similarity"]
        for result in results
    ]

    top5_values = [
        result["approved_top5_mean_similarity"]
        for result in results
    ]

    results_summary = {
        "number_molecules": len(results),
        "mean_nearest_similarity": float(np.mean(nearest_values)),
        "std_nearest_similarity": float(np.std(nearest_values, ddof=0)),
        "median_nearest_similarity": float(np.median(nearest_values)),
        "min_nearest_similarity": float(np.min(nearest_values)),
        "max_nearest_similarity": float(np.max(nearest_values)),
        "mean_top5_similarity": float(np.mean(top5_values)),
        "std_top5_similarity": float(np.std(top5_values, ddof=0)),
    }

    return results_summary


def save_approved_drug_similarity_results(results, output_path):
    """Save molecule-level Stage 4B results for the approved-drug similarity to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "molecule_id",
        "nearest_approved_parent_id",
        "nearest_approved_parent_name",
        "nearest_approved_drug_ids",
        "nearest_approved_drug_names",
        "nearest_approved_drug_smiles",
        "nearest_approved_first_approvals",
        "nearest_approved_withdrawn_flags",
        "nearest_approved_similarity",
        "approved_top5_mean_similarity",
        "approved_reference_count",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(results)
    print(f"Saved Stage 4B approved-drug similarity results to {output_path}")


def save_internal_similarity_pairs(similarities, output_path):
    """Save all Stage 4A pairwise generated-molecule similarities."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(similarities).to_csv(
        output_path,
        index=False,
    )

    print(
        f"Saved Stage 4A pairwise similarities to "
        f"{output_path}"
    )


def save_internal_similarity_results(results, output_path):
    """Save molecule-level Stage 4A nearest-neighbor results."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(results).to_csv(
        output_path,
        index=False,
    )

    print(
        f"Saved Stage 4A molecule-level results to "
        f"{output_path}"
    )


def combine_novelty_results(
        stage4a_csv_path,
        stage4b_csv_path,
        stage4c_csv_path):
    """Combine Stage 4A, 4B, and 4C results by molecule ID."""

    stage4a = pd.read_csv(stage4a_csv_path)
    stage4b = pd.read_csv(stage4b_csv_path)
    stage4c = pd.read_csv(stage4c_csv_path)

    combined = stage4a.merge(
        stage4b,
        on="molecule_id",
        how="outer",
        validate="one_to_one",
    )

    combined = combined.merge(
        stage4c,
        on="molecule_id",
        how="outer",
        validate="one_to_one",
    )

    return combined


def save_combined_novelty_results(results, output_path):
    """Save the combined Stage 4 novelty results."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Combined Stage 4 results saved to: "
        f"{output_path}"
    )
