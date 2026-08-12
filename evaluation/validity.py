# Using Path allows for a clean way to handle filesystem paths.
from pathlib import Path
# RDKit allows us to handle molecular structures and chemical sanitization.
from rdkit import Chem
# CSV module is used to write the results of the validity checks to a CSV file.
import csv


def check_validity(sdf_path):
    """Check RDKit sanitization for every molecule in an SDF file."""
    # Convert sdf_path to a Path object for easier handling.
    sdf_path = Path(sdf_path)
    # Check if the provided path exists and is a file.
    if not sdf_path.exists() or not sdf_path.is_file():
        raise FileNotFoundError(
            f"The file {sdf_path} does not exist or is not a valid file.")
    # Read every molecule from the SDF file using RDKit's SDMolSupplier
    # without sanitization and without removing hydrogens.
    supplier = Chem.SDMolSupplier(
        str(sdf_path),
        sanitize=False,
        removeHs=False,)
    # Materialize the supplier so we can count the number of molecules and
    # check their validity.
    molecules = list(supplier)
    print(f"Input SDF file: {sdf_path}")
    print(f"Number of molecules in the SDF file: {len(molecules)}")
    # Store results of validity checks in a list.
    results = []

    for molecule_id, mol in enumerate(molecules):
        # Check if the molecule is None, which indicates a failure to parse.
        if mol is None:
            results.append({"molecule_id": molecule_id,
                           "parsed": False,
                            "sanitized": False,
                            "failure_reason": "RDKit failed to parse the molecule."})
            continue
        # Attempt to sanitize the molecule. If it fails, mark it as invalid.
        try:
            Chem.SanitizeMol(mol)
            results.append({"molecule_id": molecule_id,
                           "parsed": True,
                            "sanitized": True,
                            "failure_reason": None})
        except Exception as error:
            results.append({"molecule_id": molecule_id,
                           "parsed": True,
                            "sanitized": False,
                            "failure_reason": str(error)})
    return results


def save_validity_results(results, output_csv_path):
    """Save the validity check results to a CSV file."""
    # Convert output_csv_path to a Path object for easier handling.
    output_csv_path = Path(output_csv_path)
    # Create the parent directory for the output CSV file if it doesn't exist.
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    # Define the field names for the CSV file.
    fieldnames = ["molecule_id", "parsed", "sanitized", "failure_reason"]
    # Write the results to the CSV file.
    with output_csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        print(f"Validity results saved to: {output_csv_path}")


def summarize_validity(results):
    """Summarize the validity check results."""

    # Count the total number of evaluated input molecules.
    total_molecules = len(results)

    # Count the number of molecules that were successfully parsed.
    parsed = sum(result["parsed"] for result in results)

    # Count the number of molecules that were successfully sanitized.
    sanitized = sum(result["sanitized"] for result in results)

    # Count the number of molecules that failed to parse.
    failed_parsing = total_molecules - parsed

    # Count molecules that parsed successfully but failed sanitization.
    failed_sanitization = parsed - sanitized

    # Count all molecules that failed the complete validity stage.
    total_failed = total_molecules - sanitized

    # Calculate the fraction of input records surviving the validity stage.
    survival_rate = sanitized / total_molecules if total_molecules > 0 else 0.0

    # Print a human-readable summary.
    print(f"Total molecules evaluated: {total_molecules}")
    print(f"Successfully parsed molecules: {parsed}")
    print(f"Failed to parse molecules: {failed_parsing}")
    print(f"Successfully sanitized molecules: {sanitized}")
    print(f"Failed sanitization after parsing: {failed_sanitization}")
    print(f"Total molecules failing validity: {total_failed}")
    print(f"Survival rate: {survival_rate:.2%}")

    # Return the same summary in machine-readable form.
    summary = {
        "total_molecules": total_molecules,
        "parsed": parsed,
        "failed_parsing": failed_parsing,
        "sanitized": sanitized,
        "failed_sanitization": failed_sanitization,
        "total_failed": total_failed,
        "survival_rate": survival_rate,
    }

    return summary
