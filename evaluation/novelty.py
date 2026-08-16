import csv
from pathlib import Path
import numpy as np
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
    """ Find the nearest generated neighbor for each molecule."""

    nearest_neighbors = {}

    for comparison in similarities:
        molecule_id1 = comparison["molecule_id1"]
        molecule_id2 = comparison["molecule_id2"]
        similarity = comparison["similarity"]

        for molecule_id, neighbor_id in [
                (molecule_id1, molecule_id2), (molecule_id2, molecule_id1)]:
            if molecule_id not in nearest_neighbors or similarity > nearest_neighbors[
                    molecule_id]["similarity"]:
                nearest_neighbors[molecule_id] = {
                    "neighbor_id": neighbor_id,
                    "molecule_id": molecule_id,
                    "similarity": similarity
                }
    neighbor_list = list(nearest_neighbors.values())

    return neighbor_list


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
