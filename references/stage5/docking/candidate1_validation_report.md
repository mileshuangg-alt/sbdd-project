# Stage 5 Candidate-1 Self-Redocking Validation Report

## Corrected Anchor-Recovery Criterion

Anchor recovery requires the control-specific native interaction pattern established by the validated native-reader proof of life:

- correct anchor residue identity;
- experimentally validated ProLIF interaction class;
- correct donor / acceptor direction where applicable;
- match to that control's native crystallographic interaction pattern.

The earlier residue-level boolean was an under-implementation of D007's published-chemistry intent, not a new docking-protocol candidate.

For 3REY / XAC, the required native anchor pattern is:

| Anchor | Required class(es) |
| --- | --- |
| Phe168 | Hydrophobic, VdWContact |
| Asn253 | HBAcceptor, VdWContact |

The RMSD criterion remains unchanged:

```text
symmetry-aware heavy-atom RMSD to crystallographic ligand pose <= 2.0 A
```

Vina score remains descriptive only.

## 3REY / XAC

Input pose ensemble:

```text
references/stage5/docking/3REY/vina/3REY_XAC_poses.pdbqt
```

Frozen candidate-1 run:

```text
AutoDock Vina 1.2.7
scoring function: vina
rigid receptor
exhaustiveness: 32
seed: 20260816
maximum retained poses: 20
energy range: 5 kcal/mol
box: 20 A x 20 A x 20 A
box center: 49.535806 23.214581 34.764065
```

Evaluator checks passed:

- 20 poses parsed.
- Index-map pairs: 36.
- Reconstructed/native heavy-atom canonical SMILES match.
- Formal charge: +1.
- Heavy atoms: 31.
- Validated restored receptor loaded through the existing ProLIF adapter.
- Anchor numbering audit: Phe168 and Asn253 preserved.

Per-pose corrected results:

| Rank | Vina score | RMSD A | Phe168 classes | Phe168 native-pattern recovered? | Asn253 classes | Asn253 native-pattern recovered? | Pose pass? |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | -7.219 | 10.332 | Hydrophobic; PiStacking | no | none | no | no |
| 2 | -7.204 | 6.476 | none | no | none | no | no |
| 3 | -7.176 | 10.808 | Hydrophobic; VdWContact | yes | none | no | no |
| 4 | -7.149 | 10.409 | Hydrophobic; PiStacking | no | none | no | no |
| 5 | -7.149 | 10.802 | Hydrophobic | no | HBDonor; VdWContact | no | no |
| 6 | -7.147 | 10.667 | Hydrophobic; VdWContact | yes | HBDonor; VdWContact | no | no |
| 7 | -7.047 | 1.826 | none | no | none | no | no |
| 8 | -7.020 | 9.963 | Hydrophobic | no | none | no | no |
| 9 | -6.972 | 10.673 | Hydrophobic | no | none | no | no |
| 10 | -6.823 | 8.437 | Hydrophobic; VdWContact | yes | none | no | no |
| 11 | -6.816 | 9.031 | none | no | none | no | no |
| 12 | -6.792 | 7.779 | Hydrophobic | no | none | no | no |
| 13 | -6.724 | 10.303 | Hydrophobic | no | HBDonor; VdWContact | no | no |
| 14 | -6.719 | 6.697 | Hydrophobic; VdWContact | yes | none | no | no |
| 15 | -6.688 | 10.787 | Hydrophobic; VdWContact | yes | none | no | no |
| 16 | -6.632 | 4.027 | none | no | none | no | no |
| 17 | -6.623 | 10.942 | Hydrophobic; VdWContact | yes | none | no | no |
| 18 | -6.600 | 6.157 | VdWContact | no | none | no | no |
| 19 | -6.565 | 8.308 | Hydrophobic; VdWContact | yes | none | no | no |
| 20 | -6.557 | 9.044 | Hydrophobic | no | none | no | no |

3REY / XAC result:

```text
FAIL
```

No retained pose satisfies RMSD <= 2.0 A AND Phe168 native-pattern recovery AND Asn253 native-pattern recovery.

First successful pose rank: none.

## 5OLH / Vipadenant

Status: not evaluated.

Reason: candidate 1 stops at 3REY / XAC failure under the corrected Layer 2 criterion. The remaining self-redocking experiments are not reached after a failed earlier cognate positive.

## 5OLO / Tozadenant

Status: not evaluated.

Reason: candidate 1 stops at 3REY / XAC failure under the corrected Layer 2 criterion. The remaining self-redocking experiments are not reached after a failed earlier cognate positive.

## Final Candidate-1 Outcome

Candidate 1 fails Stage 5 Layer 2 docking-protocol proof of life.

The frozen candidate-1 docking protocol is not validated and does not earn permission to generate common Stage 5 control-panel poses.

No Vina parameters, receptor preparation, ligand preparation, ProLIF reader definitions, search boxes, or docking outputs were changed to obtain this result.
