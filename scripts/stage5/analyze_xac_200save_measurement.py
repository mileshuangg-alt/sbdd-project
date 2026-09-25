from scripts.stage5.analyze_dock_xac_200save import (
    load_dock_xac_200save_records,
    reconstruct_pose_molecules,
    load_xac_reference,
    validate_xac_chemistry,
    calculate_symmetry_corrected_rmsd,
    load_3rey_receptor_heavy_atoms,
    calculate_d_rel,
)

records = load_dock_xac_200save_records()
poses = reconstruct_pose_molecules(records)
reference = load_xac_reference()
receptor_positions, receptor_atomic_numbers = (
    load_3rey_receptor_heavy_atoms()
)

results = []

for record, pose in zip(records, poses):
    validate_xac_chemistry(pose, reference)

    rmsd = calculate_symmetry_corrected_rmsd(
        pose,
        reference,
    )

    d_rel = calculate_d_rel(
        pose,
        receptor_positions,
        receptor_atomic_numbers,
    )

    if rmsd <= 2.0:
        rmsd_band = "<=2.0"
    elif rmsd < 3.0:
        rmsd_band = ">2.0,<3.0"
    else:
        rmsd_band = ">=3.0"

    physically_plausible = d_rel >= 0.75
    eligible_alternative = (
        rmsd > 2.0
        and physically_plausible
    )

    results.append(
        (
            record.rank,
            record.matchnum,
            record.total_energy,
            rmsd,
            d_rel,
            rmsd_band,
            physically_plausible,
            eligible_alternative,
        )
    )

print(
    "rank,matchnum,total_energy,rmsd,d_rel,"
    "rmsd_band,physically_plausible,eligible_alternative"
)

for row in results:
    print(
        f"{row[0]},{row[1]},{row[2]:.6f},{row[3]:.6f},"
        f"{row[4]:.6f},{row[5]},{row[6]},{row[7]}"
    )

d_rels = [row[4] for row in results]
plausible = [row for row in results if row[6]]
eligible = [row for row in results if row[7]]

print()
print("SUMMARY")
print("poses:", len(results))
print("d_rel min:", min(d_rels))
print("d_rel max:", max(d_rels))
print("d_rel mean:", sum(d_rels) / len(d_rels))
print("d_rel >= 0.75:", len(plausible))
print("RMSD <= 2.0:", sum(row[3] <= 2.0 for row in results))
print("RMSD > 2.0:", sum(row[3] > 2.0 for row in results))
print(
    "RMSD > 2.0 and d_rel >= 0.75:",
    len(eligible),
)
print(
    "first eligible alternative rank:",
    eligible[0][0] if eligible else None,
)
