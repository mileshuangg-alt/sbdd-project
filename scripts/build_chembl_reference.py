from chembl_webresource_client.new_client import new_client
from rdkit import Chem
import csv
from pathlib import Path
CHEMBL_RELEASE = 37

ADORA2A_TARGET_ID = "CHEMBL251"
TARGET_ORGANISM = "Homo sapiens"
TARGET_TYPE = "SINGLE PROTEIN"

ACTIVITY_TYPES = ["Ki", "Kd", "IC50", "EC50"]
MIN_PCHEMBL_VALUE = 6.0


def get_target_metadata(target_chembl_id):
    target = new_client.target.get(target_chembl_id)

    if target is None:
        raise ValueError(f"ChEMBL target not found: {target_chembl_id}")

    return target


def validate_target_metadata(target):
    """Validate that the ChEMBL target matches the declared reference criteria."""
    if target["target_chembl_id"] != ADORA2A_TARGET_ID:
        raise ValueError(
            f"ChEMBL target ID does not match: {
                target['target_chembl_id']} != {ADORA2A_TARGET_ID}")

    if target["organism"] != TARGET_ORGANISM:
        raise ValueError(
            f"ChEMBL target organism does not match: {
                target['organism']} != {TARGET_ORGANISM}")

    if target["target_type"] != TARGET_TYPE:
        raise ValueError(
            f"ChEMBL target type does not match: {
                target['target_type']} != {TARGET_TYPE}")
    return True


def get_target_activities(target_chembl_id):
    """Retrieve qualifying ChEMBL activities for the specified target."""
    activities = new_client.activity.filter(
        target_chembl_id=target_chembl_id,
        standard_type__in=ACTIVITY_TYPES,
        standard_value__isnull=False,
        standard_relation__in=["=", "<", "<="],
        pchembl_value__gte=MIN_PCHEMBL_VALUE,
    ).only(
        [
            "activity_id",
            "molecule_chembl_id",
            "parent_molecule_chembl_id",
            "canonical_smiles",
            "standard_type",
            "standard_relation",
            "standard_value",
            "standard_units",
            "pchembl_value",
            "assay_chembl_id",
            "target_chembl_id",
            "document_chembl_id",
        ]
    )

    return activities


def build_unique_ligands(activities):
    """Build unique target ligands from qualifying ChEMBL activities"""

    ligands_by_smiles = {}
    # Build a mapping of unique ligands by canonical SMILES
    for activity in activities:
        smiles = activity["canonical_smiles"]
        if not smiles:
            continue
    # Generate RDKit molecule from SMILES

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            continue

        cannonical_smiles = Chem.MolToSmiles(
            mol, canonical=True, isomericSmiles=True)
    # Check if the ligand is unique by canonical SMILES and add to the mapping
    # if so
        if cannonical_smiles not in ligands_by_smiles:
            ligands_by_smiles[cannonical_smiles] = {
                "molecule_chembl_id": [],
                "parent_molecule_chembl_id": [],
                "canonical_smiles": cannonical_smiles,
                "activity_ids": [],
                "document_chembl_ids": [],
                "pchembl_values": [],
            }
        ligand = ligands_by_smiles[cannonical_smiles]
        molecule_id = activity["molecule_chembl_id"]
        if molecule_id not in ligand["molecule_chembl_id"]:
            ligand["molecule_chembl_id"].append(activity["molecule_chembl_id"])

        parent_id = activity["parent_molecule_chembl_id"]

        if (
            parent_id is not None
            and parent_id not in ligand["parent_molecule_chembl_id"]
        ):
            ligand["parent_molecule_chembl_id"].append(parent_id)

        ligand["activity_ids"].append(activity["activity_id"])
        ligand["document_chembl_ids"].append(
            activity["document_chembl_id"])
        ligand["pchembl_values"].append(float(activity["pchembl_value"]))

    return list(ligands_by_smiles.values())


def save_reference_ligands(ligands, output_path):
    """Save the frozen target-ligand reference set to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "canonical_smiles",
        "molecule_chembl_id",
        "parent_molecule_chembl_id",
        "activity_ids",
        "document_chembl_ids",
        "pchembl_values",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ligand in ligands:
            row = ligand.copy()
            row["molecule_chembl_id"] = ";".join(["molecule_chembl_id"])
            row["parent_molecule_chembl_id"] = ";".join(
                row["parent_molecule_chembl_id"])
            row["activity_ids"] = ";".join(["activity_ids"])
            row["document_chembl_ids"] = ";".join(
                str(x) for x in ["document_chembl_ids"])
            row["pchembl_values"] = ";".join(
                [str(v) for v in ["pchembl_values"]])
            writer.writerow(row)

    print(
        f"Reference ligands saved to {output_path} ({
            len(ligands)} ligands).")
