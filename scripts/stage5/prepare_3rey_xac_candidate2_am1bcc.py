from pathlib import Path
import csv
import math
import subprocess

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdPartialCharges


ROOT = Path("references/stage5/docking")

SOURCE_SDF = (
    ROOT
    / "3REY"
    / "3REY_XAC_docking_input.sdf"
)

CANDIDATE1_PDBQT = (
    ROOT
    / "3REY"
    / "3REY_XAC.pdbqt"
)

OUTPUT_DIR = (
    ROOT
    / "candidate2_am1bcc"
    / "3REY"
)

ANTECHAMBER_INPUT_MOL2 = OUTPUT_DIR / "XAC_candidate2_input.mol2"
ANTECHAMBER_OUTPUT_MOL2 = OUTPUT_DIR / "XAC_AM1BCC_antechamber.mol2"
MAPPED_SDF = OUTPUT_DIR / "XAC_AM1BCC_mapped.sdf"
CHARGE_LEDGER = OUTPUT_DIR / "XAC_AM1BCC_charges.tsv"
CANDIDATE2_PDBQT = OUTPUT_DIR / "XAC_candidate2.pdbqt"

CHARGE_PROP = "AM1BCCCharge"
EXPECTED_TOTAL_ATOMS = 60
EXPECTED_HEAVY_ATOMS = 31
EXPECTED_FORMAL_CHARGE = 1
COORD_TOLERANCE = 1e-4
CHARGE_SUM_TOLERANCE = 1e-4


def load_source_mol():
    mol = Chem.SDMolSupplier(
        str(SOURCE_SDF),
        removeHs=False,
    )[0]

    if mol is None:
        raise ValueError(
            f"Failed to load source molecule: {SOURCE_SDF}"
        )

    if mol.GetNumAtoms() != EXPECTED_TOTAL_ATOMS:
        raise AssertionError(
            f"Expected {EXPECTED_TOTAL_ATOMS} atoms, "
            f"found {mol.GetNumAtoms()}."
        )

    if mol.GetNumHeavyAtoms() != EXPECTED_HEAVY_ATOMS:
        raise AssertionError(
            f"Expected {EXPECTED_HEAVY_ATOMS} heavy atoms, "
            f"found {mol.GetNumHeavyAtoms()}."
        )

    if Chem.GetFormalCharge(mol) != EXPECTED_FORMAL_CHARGE:
        raise AssertionError(
            f"Expected formal charge +{EXPECTED_FORMAL_CHARGE}, "
            f"found {Chem.GetFormalCharge(mol)}."
        )

    return mol


def atom_name(index):
    return f"A{index + 1:03d}"


def mol2_atom_type(atom):
    if atom.GetAtomicNum() == 1:
        return "H"

    if atom.GetAtomicNum() == 6:
        if atom.GetIsAromatic():
            return "C.ar"

        if any(
            bond.GetBondType() == Chem.BondType.DOUBLE
            for bond in atom.GetBonds()
        ):
            return "C.2"

        return "C.3"

    if atom.GetAtomicNum() == 7:
        if atom.GetIsAromatic():
            return "N.ar"

        if atom.GetFormalCharge() > 0:
            return "N.4"

        return "N.3"

    if atom.GetAtomicNum() == 8:
        if any(
            bond.GetBondType() == Chem.BondType.DOUBLE
            for bond in atom.GetBonds()
        ):
            return "O.2"

        return "O.3"

    return atom.GetSymbol()


def mol2_bond_type(bond):
    if bond.GetIsAromatic():
        return "ar"

    if bond.GetBondType() == Chem.BondType.SINGLE:
        return "1"

    if bond.GetBondType() == Chem.BondType.DOUBLE:
        return "2"

    if bond.GetBondType() == Chem.BondType.TRIPLE:
        return "3"

    return "1"


def write_mol2(mol, path):
    conformer = mol.GetConformer()
    lines = [
        "@<TRIPOS>MOLECULE\n",
        "XAC\n",
        f"{mol.GetNumAtoms()} {mol.GetNumBonds()} 1 0 0\n",
        "SMALL\n",
        "USER_CHARGES\n",
        "\n",
        "@<TRIPOS>ATOM\n",
    ]

    for atom in mol.GetAtoms():
        index = atom.GetIdx()
        position = conformer.GetAtomPosition(index)
        lines.append(
            f"{index + 1:7d} "
            f"{atom_name(index):<8s} "
            f"{position.x:10.4f} "
            f"{position.y:10.4f} "
            f"{position.z:10.4f} "
            f"{mol2_atom_type(atom):<8s} "
            f"1 XAC {float(atom.GetFormalCharge()):10.6f}\n"
        )

    lines.append("@<TRIPOS>BOND\n")

    for bond_index, bond in enumerate(mol.GetBonds(), start=1):
        lines.append(
            f"{bond_index:6d} "
            f"{bond.GetBeginAtomIdx() + 1:5d} "
            f"{bond.GetEndAtomIdx() + 1:5d} "
            f"{mol2_bond_type(bond)}\n"
        )

    lines.extend([
        "@<TRIPOS>SUBSTRUCTURE\n",
        "     1 XAC         1 TEMP              0 ****  ****    0 ROOT\n",
    ])

    path.write_text("".join(lines))


def run_antechamber():
    command = [
        "conda",
        "run",
        "-n",
        "sbdd-charge",
        "antechamber",
        "-i",
        ANTECHAMBER_INPUT_MOL2.name,
        "-fi",
        "mol2",
        "-o",
        ANTECHAMBER_OUTPUT_MOL2.name,
        "-fo",
        "mol2",
        "-c",
        "bcc",
        "-nc",
        "1",
        "-m",
        "1",
        "-at",
        "gaff2",
        "-s",
        "2",
    ]

    result = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
        cwd=OUTPUT_DIR,
    )

    return command, result


def parse_mol2_charges(path, source_mol):
    charges = []
    names = []
    elements = []
    in_atom_section = False

    for line in path.read_text().splitlines():
        if line.startswith("@<TRIPOS>ATOM"):
            in_atom_section = True
            continue

        if line.startswith("@<TRIPOS>"):
            in_atom_section = False
            continue

        if not in_atom_section or not line.strip():
            continue

        fields = line.split()
        names.append(fields[1])
        atom_type = fields[5]
        elements.append(
            "Cl" if atom_type.startswith("Cl") else
            "Br" if atom_type.startswith("Br") else
            atom_type[0]
        )
        charges.append(float(fields[-1]))

    if len(charges) != source_mol.GetNumAtoms():
        raise AssertionError(
            f"Expected {source_mol.GetNumAtoms()} AM1-BCC charges, "
            f"found {len(charges)}."
        )

    expected_names = [
        atom_name(index)
        for index in range(source_mol.GetNumAtoms())
    ]

    if names != expected_names:
        raise AssertionError(
            "Antechamber atom names/order changed; cannot map "
            "charges back to original atom order."
        )

    expected_elements = [
        atom.GetSymbol()
        for atom in source_mol.GetAtoms()
    ]

    if elements != expected_elements:
        raise AssertionError(
            "Antechamber element sequence differs from original "
            "atom order."
        )

    return charges


def calculate_candidate1_gasteiger(mol):
    copy = Chem.Mol(mol)
    rdPartialCharges.ComputeGasteigerCharges(copy)
    charges = []

    for atom in copy.GetAtoms():
        charge = atom.GetDoubleProp("_GasteigerCharge")
        if not math.isfinite(charge):
            raise AssertionError(
                "Non-finite Candidate-1 Gasteiger charge."
            )
        charges.append(float(charge))

    return charges


def attach_charges_and_write_sdf(mol, charges, path):
    charged = Chem.Mol(mol)

    for atom, charge in zip(charged.GetAtoms(), charges):
        atom.SetDoubleProp(CHARGE_PROP, float(charge))

    writer = Chem.SDWriter(str(path))
    writer.write(charged)
    writer.close()

    return charged


def write_charge_ledger(mol, candidate1_charges, candidate2_charges, path):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "original_atom_index",
                "element",
                "atom_name",
                "candidate1_gasteiger_charge",
                "candidate2_am1bcc_charge",
                "delta_charge",
            ],
            delimiter="\t",
        )
        writer.writeheader()

        for atom in mol.GetAtoms():
            index = atom.GetIdx()
            c1 = candidate1_charges[index]
            c2 = candidate2_charges[index]
            writer.writerow(
                {
                    "original_atom_index": index + 1,
                    "element": atom.GetSymbol(),
                    "atom_name": atom_name(index),
                    "candidate1_gasteiger_charge": f"{c1:.6f}",
                    "candidate2_am1bcc_charge": f"{c2:.6f}",
                    "delta_charge": f"{c2 - c1:.6f}",
                }
            )


def run_meeko_candidate2():
    command = [
        "mk_prepare_ligand.py",
        "-i",
        str(MAPPED_SDF),
        "-o",
        str(CANDIDATE2_PDBQT),
        "--charge_model",
        "read",
        "--charge_atom_prop",
        CHARGE_PROP,
        "--add_index_map",
    ]

    result = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
        cwd=Path.cwd(),
    )

    return command, result


def bond_signature(mol):
    return sorted(
        (
            bond.GetBeginAtomIdx(),
            bond.GetEndAtomIdx(),
            str(bond.GetBondType()),
            bond.GetIsAromatic(),
        )
        for bond in mol.GetBonds()
    )


def assert_source_invariants(source, mapped):
    if Chem.MolToSmiles(
        Chem.RemoveHs(source),
        canonical=True,
        isomericSmiles=True,
    ) != Chem.MolToSmiles(
        Chem.RemoveHs(mapped),
        canonical=True,
        isomericSmiles=True,
    ):
        raise AssertionError("Heavy-atom canonical SMILES changed.")

    if source.GetNumAtoms() != mapped.GetNumAtoms():
        raise AssertionError("Total atom count changed.")

    if source.GetNumHeavyAtoms() != mapped.GetNumHeavyAtoms():
        raise AssertionError("Heavy-atom count changed.")

    source_elements = [atom.GetSymbol() for atom in source.GetAtoms()]
    mapped_elements = [atom.GetSymbol() for atom in mapped.GetAtoms()]
    if source_elements != mapped_elements:
        raise AssertionError("Element sequence changed.")

    if bond_signature(source) != bond_signature(mapped):
        raise AssertionError("Bond graph changed.")

    source_formal = [atom.GetFormalCharge() for atom in source.GetAtoms()]
    mapped_formal = [atom.GetFormalCharge() for atom in mapped.GetAtoms()]
    if source_formal != mapped_formal:
        raise AssertionError("Formal charges changed.")

    source_coords = source.GetConformer().GetPositions()
    mapped_coords = mapped.GetConformer().GetPositions()
    max_displacement = float(
        np.linalg.norm(
            source_coords - mapped_coords,
            axis=1,
        ).max()
    )
    if max_displacement > COORD_TOLERANCE:
        raise AssertionError(
            "Coordinates changed: max displacement "
            f"{max_displacement:.6f} A."
        )

    return max_displacement


def read_pdbqt_index_map(path):
    pairs = []
    for line in path.read_text().splitlines():
        if not line.startswith("REMARK INDEX MAP"):
            continue
        values = [int(value) for value in line.split()[3:]]
        for index in range(0, len(values), 2):
            pairs.append((values[index], values[index + 1]))
    return tuple(pairs)


def pdbqt_atom_records(path):
    records = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            fields = line.split()
            records.append(
                {
                    "line": line,
                    "serial": int(fields[1]),
                    "name": fields[2],
                    "resname": fields[3],
                    "resid": fields[4],
                    "x": float(fields[5]),
                    "y": float(fields[6]),
                    "z": float(fields[7]),
                    "charge": float(fields[-2]),
                    "atom_type": fields[-1],
                }
            )
    return records


def pdbqt_topology_lines(path):
    prefixes = (
        "ROOT",
        "ENDROOT",
        "BRANCH",
        "ENDBRANCH",
        "TORSDOF",
    )
    return [
        line
        for line in path.read_text().splitlines()
        if line.startswith(prefixes)
    ]


def assert_pdbqt_invariants():
    candidate1_map = read_pdbqt_index_map(CANDIDATE1_PDBQT)
    candidate2_map = read_pdbqt_index_map(CANDIDATE2_PDBQT)

    if candidate1_map != candidate2_map:
        raise AssertionError("Meeko index map changed.")

    c1_atoms = pdbqt_atom_records(CANDIDATE1_PDBQT)
    c2_atoms = pdbqt_atom_records(CANDIDATE2_PDBQT)

    if len(c1_atoms) != len(c2_atoms):
        raise AssertionError("PDBQT atom count changed.")

    for left, right in zip(c1_atoms, c2_atoms):
        for key in (
            "serial",
            "name",
            "resname",
            "resid",
            "atom_type",
        ):
            if left[key] != right[key]:
                raise AssertionError(
                    f"PDBQT atom order/type changed at {key}."
                )

        for key in ("x", "y", "z"):
            if abs(left[key] - right[key]) > 1e-3:
                raise AssertionError("PDBQT coordinates changed.")

    if pdbqt_topology_lines(CANDIDATE1_PDBQT) != pdbqt_topology_lines(CANDIDATE2_PDBQT):
        raise AssertionError("ROOT/BRANCH/TORSDOF topology changed.")

    return {
        "index_map_pairs": len(candidate2_map),
        "pdbqt_atoms": len(c2_atoms),
    }


def validate_am1bcc_charges(charges):
    missing = sum(charge is None for charge in charges)
    non_finite = sum(
        not math.isfinite(charge)
        for charge in charges
        if charge is not None
    )
    charge_sum = float(sum(charges))

    if missing != 0:
        raise AssertionError("Missing AM1-BCC charges detected.")

    if non_finite != 0:
        raise AssertionError("Non-finite AM1-BCC charges detected.")

    if abs(charge_sum - 1.0) > CHARGE_SUM_TOLERANCE:
        raise AssertionError(
            "AM1-BCC charge sum is outside tolerance: "
            f"{charge_sum:.6f}."
        )

    return {
        "missing": missing,
        "non_finite": non_finite,
        "sum": charge_sum,
        "minimum": min(charges),
        "maximum": max(charges),
    }


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    source = load_source_mol()

    write_mol2(
        source,
        ANTECHAMBER_INPUT_MOL2,
    )

    antechamber_command, antechamber_result = run_antechamber()

    am1bcc_charges = parse_mol2_charges(
        ANTECHAMBER_OUTPUT_MOL2,
        source,
    )
    charge_stats = validate_am1bcc_charges(
        am1bcc_charges
    )

    candidate1_charges = calculate_candidate1_gasteiger(
        source
    )

    mapped = attach_charges_and_write_sdf(
        source,
        am1bcc_charges,
        MAPPED_SDF,
    )

    write_charge_ledger(
        source,
        candidate1_charges,
        am1bcc_charges,
        CHARGE_LEDGER,
    )

    max_displacement = assert_source_invariants(
        source,
        mapped,
    )

    meeko_command, meeko_result = run_meeko_candidate2()

    pdbqt_stats = assert_pdbqt_invariants()

    print("Candidate-2 3REY/XAC AM1-BCC pre-dock preparation")
    print("=" * 72)
    print("Antechamber command:", " ".join(antechamber_command))
    print("Meeko command:", " ".join(meeko_command))
    print("AM1-BCC charge sum:", f"{charge_stats['sum']:.6f}")
    print("Missing AM1-BCC charges:", charge_stats["missing"])
    print("Non-finite AM1-BCC charges:", charge_stats["non_finite"])
    print("Mapped atoms:", len(am1bcc_charges))
    print(
        "AM1-BCC charge range:",
        f"{charge_stats['minimum']:.6f}",
        "to",
        f"{charge_stats['maximum']:.6f}",
    )
    print("Max coordinate displacement:", f"{max_displacement:.6f} A")
    print("Meeko index-map pairs:", pdbqt_stats["index_map_pairs"])
    print("PDBQT atom count:", pdbqt_stats["pdbqt_atoms"])
    print("Antechamber stdout:")
    print(antechamber_result.stdout.strip())
    print("Antechamber stderr:")
    print(antechamber_result.stderr.strip())
    print("Meeko stdout:")
    print(meeko_result.stdout.strip())
    print("Meeko stderr:")
    print(meeko_result.stderr.strip())
    print("Output MOL2:", ANTECHAMBER_OUTPUT_MOL2)
    print("Charge ledger:", CHARGE_LEDGER)
    print("Mapped charge SDF:", MAPPED_SDF)
    print("Candidate-2 PDBQT:", CANDIDATE2_PDBQT)
    print("READY FOR DOCKING: YES")


if __name__ == "__main__":
    main()
