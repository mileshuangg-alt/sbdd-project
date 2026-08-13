from pathlib import Path

from rdkit import Chem
# imports chemical property calculators from rdkit
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdMolDescriptors
import csv


def load_valid_molecule_ids(validity_csv_path):
    """Load molecule IDs that passed stage 1 checks"""

    validity_csv_path = Path(validity_csv_path)

    if not validity_csv_path.exists():
        raise FileNotFoundError(
            f"Validity result files not found: {validity_csv_path}")

    valid_ids = []

    with validity_csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["sanitized"] == "True":
                valid_ids.append(int(row["molecule_id"]))

    return valid_ids


def calculate_properties(mol):
    """Calculate molecular properties for a given RDKit molecule object"""

    molecular_weight = Descriptors.MolWt(mol)
    clogp = Crippen.MolLogP(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    rotatable_bonds = Lipinski.NumRotatableBonds(mol)
    qed = QED.qed(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()

    # Sum of the formal charge of all atoms in the molecule
    formal_charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
    properties = {
        "molecular_weight": molecular_weight,
        "clogp": clogp,
        "tpsa": tpsa,
        "hbd": hbd,
        "hba": hba,
        "rotatable_bonds": rotatable_bonds,
        "qed": qed,
        "heavy_atoms": heavy_atoms,
        "formal_charge": formal_charge
    }

    return properties


def evaluate_properties(sdf_path, valid_ids):
    """Calculate molecular properties for Stage 1-valid molecules"""

    sdf_path = Path(sdf_path)

    if not sdf_path.exists():
        raise FileNotFoundError(f"SDF file not found: {sdf_path}")
    # Load molecules from the SDF file without sanitization or hydrogen removal
    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        sanitize=False,
        removeHs=False)
    molecules = list(supplier)
    results = []

    for molecule_id in valid_ids:
        mol = molecules[molecule_id]

        # Stage 1 already established that the molecule can be sanitized.
        # Sanitize again here so RDkit descriptors operate on a sanitized
        # molecule.
        Chem.SanitizeMol(mol)

        # Calculate the raw molecular property profile.

        properties = calculate_properties(mol)

        # Classify the property profile using Rule-of-Five criteria.
        ro5_results = classify_rule_of_five(properties)

        # Combine provenance, raw properties, and Rule-of-Five classification.

        result = {
            "molecule_id": molecule_id,
            **properties,
            **ro5_results
        }
        results.append(result)

    return results


def classify_rule_of_five(properties):
    """Classify a molecular property profile using Lipinski Rule-of-Five criteria"""

    mw_pass = properties["molecular_weight"] <= 500
    clogp_pass = properties["clogp"] <= 5
    hbd_pass = properties["hbd"] <= 5
    hba_pass = properties["hba"] <= 10

    violations = sum([
        not mw_pass,
        not clogp_pass,
        not hbd_pass,
        not hba_pass
    ])
    ro5_results = {
        "ro5_mw_pass": mw_pass,
        "ro5_clogp_pass": clogp_pass,
        "ro5_hbd_pass": hbd_pass,
        "ro5_hba_pass": hba_pass,
        "ro5_violations": violations,
        "ro5_passes": violations == 0,
    }

    return ro5_results


def save_property_results(results, output_csv_path):
    """Save Stage 2 molecular property results to a CSV file"""

    output_path = Path(output_csv_path)

    # Create the output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "molecule_id",
        "molecular_weight",
        "clogp",
        "tpsa",
        "hbd",
        "hba",
        "rotatable_bonds",
        "qed",
        "heavy_atoms",
        "formal_charge",
        "ro5_mw_pass",
        "ro5_clogp_pass",
        "ro5_hbd_pass",
        "ro5_hba_pass",
        "ro5_violations",
        "ro5_passes"
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    print(f"Property results saved to {output_csv_path}")


def summarize_properties(results):
    """Summarize Stage 2 molecular and Rule-of-Five property results"""

    total_molecules = len(results)

    ro5_passed = sum(result["ro5_passes"] for result in results)

    ro5_flagged = total_molecules - ro5_passed

    survival_rate = (
        ro5_passed / total_molecules if total_molecules > 0 else 0
    )

    print(f"Total molecules evaluated: {total_molecules}")
    print(f"Total molecules passing Rule-of-Five: {ro5_passed}")
    print(f"Total molecules flagged by Rule-of-Five: {ro5_flagged}")
    print(f"Zero-violate rate: {survival_rate:.2%}")

    summary = {
        "total_molecules": total_molecules,
        "ro5_passed": ro5_passed,
        "ro5_flagged": ro5_flagged,
        "survival_rate": survival_rate
    }

    return summary
