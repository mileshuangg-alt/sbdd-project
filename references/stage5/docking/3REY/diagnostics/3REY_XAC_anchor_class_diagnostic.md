**20-Pose Interaction-Class Table**

| Rank | RMSD Å | Phe168 ProLIF classes | Asn253 ProLIF classes |
|---:|---:|---|---|
| 1 | 10.332 | Hydrophobic; PiStacking | none |
| 2 | 6.476 | none | none |
| 3 | 10.808 | Hydrophobic; VdWContact | none |
| 4 | 10.409 | Hydrophobic; PiStacking | none |
| 5 | 10.802 | Hydrophobic | HBDonor; VdWContact |
| 6 | 10.667 | Hydrophobic; VdWContact | HBDonor; VdWContact |
| 7 | 1.826 | none | none |
| 8 | 9.963 | Hydrophobic | none |
| 9 | 10.673 | Hydrophobic | none |
| 10 | 8.437 | Hydrophobic; VdWContact | none |
| 11 | 9.031 | none | none |
| 12 | 7.779 | Hydrophobic | none |
| 13 | 10.303 | Hydrophobic | HBDonor; VdWContact |
| 14 | 6.697 | Hydrophobic; VdWContact | none |
| 15 | 10.787 | Hydrophobic; VdWContact | none |
| 16 | 4.027 | none | none |
| 17 | 10.942 | Hydrophobic; VdWContact | none |
| 18 | 6.157 | VdWContact | none |
| 19 | 8.308 | Hydrophobic; VdWContact | none |
| 20 | 9.044 | Hydrophobic | none |

**Pose 7 Contact Answer**

- Phe168: no ProLIF interaction detected.
- Asn253: no ProLIF interaction detected.
- Exact classes: none for both residues.
- Metadata: none returned for either residue.

**Poses 5/6/13 Compared To Native XAC**

Native crystallographic XAC:

- Phe168: `Hydrophobic`, `VdWContact`
- Asn253: `HBAcceptor`, `VdWContact`
- Native Asn253 `HBAcceptor` metadata: distance `2.868 Å`, DHA angle `137.9°`
- Native Phe168 metadata: `Hydrophobic` distance `3.853 Å`; `VdWContact` distance `3.398 Å`

Pose 5:

- Phe168 checkmark: `Hydrophobic`
- Phe168 metadata: distance `3.967 Å`
- Asn253 checkmark: `HBDonor`, `VdWContact`
- Asn253 `HBDonor` metadata: distance `3.097 Å`, DHA angle `152.4°`
- Asn253 `VdWContact` metadata: distance `2.176 Å`

Pose 6:

- Phe168 checkmark: `Hydrophobic`, `VdWContact`
- Phe168 metadata: `Hydrophobic` distance `3.575 Å`; `VdWContact` distance `2.503 Å`
- Asn253 checkmark: `HBDonor`, `VdWContact`
- Asn253 `HBDonor` metadata: distance `3.091 Å`, DHA angle `151.3°`
- Asn253 `VdWContact` metadata: distance `2.462 Å`

Pose 13:

- Phe168 checkmark: `Hydrophobic`
- Phe168 metadata: distance `3.748 Å`
- Asn253 checkmark: `HBDonor`, `VdWContact`
- Asn253 `HBDonor` metadata: distance `3.135 Å`, DHA angle `146.3°`
- Asn253 `VdWContact` metadata: distance `2.521 Å`

**Interpretation**

The far-pose anchor recoveries are not chemically the same as native XAC anchor recovery. Native XAC recovers Asn253 through `HBAcceptor` plus `VdWContact`, consistent with the crystallographic carbonyl accepting from Asn253. Poses 5, 6, and 13 recover Asn253 through `HBDonor` plus `VdWContact`, a different interaction class and geometry. The current anchor boolean is therefore measuring residue-level ProLIF interaction presence, not specifically the published native XAC anchor chemistry.
