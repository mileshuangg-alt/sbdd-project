# Stage 5 Primary Negative Panel Freeze — D021 Run-2 rDock Expansion

**Freeze date:** 2026-09-23  
**Status:** FROZEN  
**Panel:** Primary Stage-5 negative panel

## Decision

The primary Stage-5 negative panel is frozen at **six candidates**:

- one previously frozen DOCK-lineage P3-002 representative from Session 011;
- five newly qualified rDock Run-2 XAC adversarial poses.

No new eligibility or selection rule is introduced by this freeze.

## Generation-family composition

| Generation family | Count | Proportion |
|---|---:|---:|
| DOCK | 1 | 1/6 |
| rDock | 5 | 5/6 |
| **Total** | **6** | **6/6** |

Generation-family identity remains attached to every candidate after blinding for prespecified post-run stratification.

## DOCK-lineage candidate

- Candidate: P3-002 N6-cyclooctyladenosine
- Generator lineage: DOCK 3.8.5
- Representative: rank 1
- DOCK score: -27.96
- P1: PASS
- P2: PASS
- P3: PASS
- P4: retained exactly as recorded in Session 011
- Protein clashes: 0
- ProLIF exposure before freeze: NONE

Authoritative Session-011 artifact:

`/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/p3_candidates/P3-002_N6-cyclooctyladenosine/p1_posebusters_dock/poses/rank_01.mol2`

SHA-256:

`a232d950008861f3ee87d73e880b9e1627afa06a47182b3a1a249f4cf61eaddf`

## rDock Run-2 candidates

- Parent ligand/complex: XAC / 3REY
- Generation lineage: rDock v24.04.204-legacy
- Git commit: `3c029ecc65898166b234716b1609fb46212cbc6d`
- Search: D021 Run-2
- P1: PASS
- P2: PASS
- P3: PASS
- P4: PASS
- ProLIF exposure before freeze: NONE

| Pose ID | RMSD (A) | d_rel | rDock score |
|---:|---:|---:|---:|
| 1 | 13.327538799745 | 0.850982332709 | -1.28039 |
| 11 | 10.835889637740 | 0.790085137621 | -1.63705 |
| 29 | 10.946424202775 | 0.921300640305 | -3.32868 |
| 35 | 11.811384287668 | 0.830795339174 | -3.53497 |
| 44 | 11.241392784130 | 0.868115621503 | 2.13362 |

The authoritative Run-2 measurement artifact is:
`references/stage5/d021_rdock_3REY_XAC_single_shot_qualification_20260917/run2_d020_measurement_v2/XAC_3REY_run2_d020_measurements.csv`

The authoritative rDock production archive is:
`references/stage5/d021_rdock_3REY_XAC_single_shot_qualification_20260917/XAC_3REY_run2.sd`

## Downstream use

The six candidates constitute the complete primary negative input for the frozen Stage-5 validation reader.

No candidate may be removed, substituted, or reselected based on downstream reader results.

No pose-specific tiebreaker is introduced.

No pose-sensitivity claim is authorized by this freeze.

