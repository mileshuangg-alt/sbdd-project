from pathlib import Path

from Bio.PDB import PDBIO

from prepare_native_reader_receptors import (
    audit_anchor_residues,
    audit_heavy_atom_preservation,
    audit_his250,
    audit_hydrogens,
    calculate_heavy_atom_displacements,
    extract_his250_pka,
    load_structure,
    print_altloc_selections,
    print_restoration_records,
    resolve_altlocs,
    run_pdb2pqr_to_paths,
    write_restored_pqr,
    COORD_TOLERANCE,
)


INPUT_PDB = Path(
    "experiments/phase1_diffsbdd/evaluation/"
    "prepared_3rfm_pocket.pdb"
)

OUTPUT_DIR = Path(
    "experiments/phase1_diffsbdd/evaluation"
)

ALTLOC_RESOLVED_PDB = (
    OUTPUT_DIR
    / "prepared_3rfm_pocket_altloc_resolved.pdb"
)

RAW_PQR = (
    OUTPUT_DIR
    / "prepared_3rfm_pocket_pH7.4.pqr"
)

PDB2PQR_LOG = (
    OUTPUT_DIR
    / "prepared_3rfm_pocket_pH7.4.log"
)

RESTORED_PQR = (
    OUTPUT_DIR
    / "prepared_3rfm_pocket_pH7.4_restored.pqr"
)


def write_altloc_resolved_pdb():
    """Persist the deterministic receptor conformer used for preparation."""

    structure = load_structure(
        INPUT_PDB,
        "3RFM_pocket_input",
    )

    altloc_selections = resolve_altlocs(
        structure
    )

    io = PDBIO()
    io.set_structure(structure)
    io.save(str(ALTLOC_RESOLVED_PDB))

    return ALTLOC_RESOLVED_PDB, altloc_selections


def main():
    """Create an interaction-ready pH-7.4 3RFM pocket PQR."""

    if not INPUT_PDB.is_file():
        raise FileNotFoundError(
            f"3RFM pocket PDB not found: {INPUT_PDB}"
        )

    print()
    print("=" * 72)
    print("3RFM interaction-ready pocket receptor")
    print("=" * 72)

    raw_pdb, altloc_selections = write_altloc_resolved_pdb()

    print_altloc_selections(
        altloc_selections
    )

    raw_structure = load_structure(
        raw_pdb,
        "3RFM_pocket_raw",
    )

    anchors = audit_anchor_residues(
        raw_structure,
        "3RFM",
    )

    output_pqr, output_log = run_pdb2pqr_to_paths(
        raw_pdb,
        RAW_PQR,
        PDB2PQR_LOG,
    )

    prepared_structure = load_structure(
        output_pqr,
        "3RFM_pocket_prepared",
    )

    preservation = audit_heavy_atom_preservation(
        raw_structure,
        prepared_structure,
        "3RFM",
    )

    total_atoms, hydrogen_count = audit_hydrogens(
        prepared_structure
    )

    his250 = audit_his250(
        prepared_structure,
        "3RFM",
    )

    his250_pka = extract_his250_pka(
        output_log
    )

    write_results = write_restored_pqr(
        output_pqr,
        prepared_structure,
        RESTORED_PQR,
    )

    persisted_structure = load_structure(
        RESTORED_PQR,
        "3RFM_pocket_persisted_restored",
    )

    persisted_audit = calculate_heavy_atom_displacements(
        raw_structure,
        persisted_structure,
    )

    if persisted_audit["max_displacement"] > COORD_TOLERANCE:
        raise ValueError(
            "3RFM: persisted restored receptor does not preserve "
            "input heavy-atom geometry; max displacement="
            f"{persisted_audit['max_displacement']:.6f} A"
        )

    persisted_total_atoms, persisted_hydrogens = audit_hydrogens(
        persisted_structure
    )

    persisted_his250 = audit_his250(
        persisted_structure,
        "3RFM",
    )

    if persisted_total_atoms != total_atoms:
        raise ValueError(
            "3RFM: atom count changed during restored-PQR persistence."
        )

    if persisted_hydrogens != hydrogen_count:
        raise ValueError(
            "3RFM: hydrogen count changed during restored-PQR persistence."
        )

    if persisted_his250["state"] != his250["state"]:
        raise ValueError(
            "3RFM: His250 state changed during restored-PQR persistence."
        )

    print("Anchor residues:", anchors)
    print("Raw heavy atoms:", preservation["raw_heavy_atoms"])
    print("Prepared heavy atoms:", preservation["prepared_heavy_atoms"])
    print("Matched input heavy atoms:", preservation["matched_heavy_atoms"])
    print("Added heavy atoms:", preservation["added_heavy_atoms"])
    print("Total prepared atoms:", total_atoms)
    print("Hydrogens:", hydrogen_count)
    print(
        "Pre-restoration max heavy-atom displacement:",
        f"{preservation['pre_max_displacement']:.6f} A",
    )
    print(
        "Pre-restoration mean heavy-atom displacement:",
        f"{preservation['pre_mean_displacement']:.6f} A",
    )
    print(
        "Post-restoration max heavy-atom displacement:",
        f"{preservation['post_max_displacement']:.6f} A",
    )
    print(
        "Post-restoration mean heavy-atom displacement:",
        f"{preservation['post_mean_displacement']:.6f} A",
    )
    print("Input heavy atoms processed:", preservation["processed_heavy_atoms"])
    print(
        "Parent-attached hydrogens processed:",
        preservation["processed_hydrogens"],
    )
    print("Input heavy atoms actually moved:", preservation["moved_heavy_atoms"])
    print(
        "Parent-attached hydrogens actually moved:",
        preservation["moved_hydrogens"],
    )
    print_restoration_records(
        preservation["restoration_records"]
    )
    print("His250 state:", his250["state"])
    print("His250 HD1:", his250["HD1"])
    print("His250 HE2:", his250["HE2"])
    print(
        "His250 PROPKA pKa:",
        f"{his250_pka:.2f}" if his250_pka is not None else "not parsed",
    )
    print("Persisted restored atoms:", write_results["written_atoms"])
    print("Persisted restored hydrogens:", persisted_hydrogens)
    print(
        "Persisted post-restoration max heavy-atom displacement:",
        f"{persisted_audit['max_displacement']:.6f} A",
    )
    print("Persisted His250 state:", persisted_his250["state"])
    print("Altloc-resolved PDB:", ALTLOC_RESOLVED_PDB)
    print("Raw PDB2PQR receptor:", RAW_PQR)
    print("Restored receptor:", RESTORED_PQR)
    print("Preparation log:", PDB2PQR_LOG)
    print(
        "PASS: 3RFM interaction-ready receptor preparation, "
        "restoration, persistence, and anchor audits passed."
    )


if __name__ == "__main__":
    main()
