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

APPROVED_MAX_PHASE = 4
APPROVED_MOLECULE_TYPE = "Small molecule"


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
                "molecule_chembl_ids": [],
                "parent_molecule_chembl_ids": [],
                "canonical_smiles": cannonical_smiles,
                "activity_ids": [],
                "document_chembl_ids": [],
                "pchembl_values": [],
            }
        ligand = ligands_by_smiles[cannonical_smiles]
        molecule_id = activity["molecule_chembl_id"]
        if molecule_id not in ligand["molecule_chembl_ids"]:
            ligand["molecule_chembl_ids"].append(
                activity["molecule_chembl_id"])

        parent_id = activity["parent_molecule_chembl_id"]

        if (
            parent_id is not None
            and parent_id not in ligand["parent_molecule_chembl_ids"]
        ):
            ligand["parent_molecule_chembl_ids"].append(parent_id)

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
        "molecule_chembl_ids",
        "parent_molecule_chembl_ids",
        "activity_ids",
        "document_chembl_ids",
        "pchembl_values",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for ligand in ligands:
            row = ligand.copy()

            row["molecule_chembl_ids"] = ";".join(
                ligand["molecule_chembl_ids"]
            )

            row["parent_molecule_chembl_ids"] = ";".join(
                ligand["parent_molecule_chembl_ids"]
            )

            row["activity_ids"] = ";".join(
                str(x) for x in ligand["activity_ids"]
            )

            row["document_chembl_ids"] = ";".join(
                str(x) for x in ligand["document_chembl_ids"]
            )

            row["pchembl_values"] = ";".join(
                str(x) for x in ligand["pchembl_values"]
            )

            writer.writerow(row)

    print(
        f"Reference ligands saved to {output_path} "
        f"({len(ligands)} ligands)."
    )


def get_approved_drugs():
    """Retrieve a lazy query for approved small-molecule"""
    approved_drugs = new_client.molecule.filter(
        max_phase=APPROVED_MAX_PHASE,
        molecule_type=APPROVED_MOLECULE_TYPE,
    ).only(

        [
            "molecule_chembl_id",
            "pref_name",
            "max_phase",
            "molecule_type",
            "molecule_structures",
            "molecule_hierarchy",
            "first_approval",
            "withdrawn_flag",
        ]
    )

    return approved_drugs


def get_parent_molecule(parent_chembl_id):
    """Retrieve the parent molecule record for a given parent ChEMBL ID"""

    parent_molecule = new_client.molecule.get(parent_chembl_id)

    if not parent_molecule:
        raise ValueError(
            f"Parent molecule not found for ChEMBL ID: {parent_chembl_id}")

    return parent_molecule


def get_parent_chembl_id(drug):
    """Return the parent ChEMBL ID for an approved drug record."""

    hierarchy = drug.get("molecule_hierarchy") or {}

    return hierarchy.get("parent_chembl_id")


def build_approved_drug_reference(approved_drugs):
    """Build a parent-normalized approved-drug reference set."""

    parent_cache = {}
    drugs_by_smiles = {}
    skipped_no_structure = 0

    for index, drug in enumerate(approved_drugs, start=1):

        if index % 250 == 0:
            print(
                f"Processed {index} approved records; "
                f"{len(drugs_by_smiles)} unique structures; "
                f"{len(parent_cache)} external parent lookups."
            )

        parent_chembl_id = get_parent_chembl_id(drug)
        molecule_chembl_id = drug["molecule_chembl_id"]

        # Case 1:
        # ChEMBL provides no parent relationship.
        if parent_chembl_id is None:
            structures = drug.get("molecule_structures") or {}

            if not structures.get("canonical_smiles"):
                skipped_no_structure += 1
                continue

            parent = drug
            parent_chembl_id = molecule_chembl_id

        # Case 2:
        # The approved record is already its own parent.
        elif parent_chembl_id == molecule_chembl_id:
            parent = drug

        # Case 3:
        # We have already retrieved this external parent.
        elif parent_chembl_id in parent_cache:
            parent = parent_cache[parent_chembl_id]

        # Case 4:
        # Retrieve the external parent from ChEMBL.
        else:
            parent = get_parent_molecule(parent_chembl_id)
            parent_cache[parent_chembl_id] = parent

        # All cases above now resolve to a parent molecule.
        structures = parent.get("molecule_structures") or {}
        smiles = structures.get("canonical_smiles")

        if not smiles:
            skipped_no_structure += 1
            continue

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            skipped_no_structure += 1
            continue

        canonical_smiles = Chem.MolToSmiles(
            mol,
            canonical=True,
            isomericSmiles=True,
        )

        # Create one reference entry per unique canonical structure.
        if canonical_smiles not in drugs_by_smiles:
            drugs_by_smiles[canonical_smiles] = {
                "canonical_smiles": canonical_smiles,
                "parent_molecule_chembl_id": parent_chembl_id,
                "parent_pref_name": parent.get("pref_name"),
                "approved_chembl_ids": [],
                "approved_pref_names": [],
                "first_approvals": [],
                "withdrawn_flags": [],
            }

        reference = drugs_by_smiles[canonical_smiles]

        # Preserve all approved ChEMBL records associated
        # with this normalized structure.
        if (
            molecule_chembl_id
            not in reference["approved_chembl_ids"]
        ):
            reference["approved_chembl_ids"].append(
                molecule_chembl_id
            )

        # Preserve approved drug names.
        pref_name = drug.get("pref_name")

        if (
            pref_name is not None
            and pref_name not in reference["approved_pref_names"]
        ):
            reference["approved_pref_names"].append(
                pref_name
            )

        # Preserve approval years.
        first_approval = drug.get("first_approval")

        if (
            first_approval is not None
            and first_approval not in reference["first_approvals"]
        ):
            reference["first_approvals"].append(
                first_approval
            )

        # Preserve withdrawal status.
        withdrawn_flag = drug.get("withdrawn_flag")

        if (
            withdrawn_flag is not None
            and withdrawn_flag not in reference["withdrawn_flags"]
        ):
            reference["withdrawn_flags"].append(
                withdrawn_flag
            )

    print(
        f"Skipped {skipped_no_structure} approved records "
        f"with no resolvable molecular structure."
    )

    return list(drugs_by_smiles.values())


def save_approved_drug_reference(drugs, output_path):
    """Save the frozen approved-drug reference set to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "canonical_smiles",
        "parent_molecule_chembl_id",
        "parent_pref_name",
        "approved_chembl_ids",
        "approved_pref_names",
        "first_approvals",
        "withdrawn_flags",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for drug in drugs:
            row = drug.copy()

            row["approved_chembl_ids"] = ";".join(
                drug["approved_chembl_ids"]
            )

            row["approved_pref_names"] = ";".join(
                drug["approved_pref_names"]
            )

            row["first_approvals"] = ";".join(
                str(x) for x in drug["first_approvals"]
            )

            row["withdrawn_flags"] = ";".join(
                str(x) for x in drug["withdrawn_flags"]
            )

            writer.writerow(row)

    print(
        f"Approved-drug reference saved to {output_path} "
        f"({len(drugs)} drugs)."
    )
