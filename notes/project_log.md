# Project Log

| Session | Date | Objective | Status |
| --- | --- | --- | --- |
| 001 | 2026-08-05 | Understand DiffSBDD inference interface and establish initial project direction | ✅ Complete |
| 002 | 2026-08-11 | Reconstruct DiffSBDD environment and reproduce checkpoint inference | ✅ Complete |
| 003 | 2026-08-12 | Build Stage 1 of the generator-agnostic evaluation cascade: chemical validity | ✅ Complete |
| 004 | 2026-08-12 | Build Stage 2: molecular property profiling and Rule-of-Five feasibility classification | ✅ Complete |
| 005 | 2026-08-13 | Implement Stage 3 3D structural plausibility evaluation | ✅ |
| 006 | 2026-08-16 | Implement Stage 4 novelty / chemical-space characterization | ✅ Complete |
| 007 | 2026-08-16 to 2026-08-19 | Develop and validate the A2A Stage-5 target-compatibility methodology; qualify native ProLIF reading, test independent docking candidates, and establish the reference-pose fallback | ✅ Complete — native reader qualified; original independent docking arm closed as a documented negative result |
| 008 | 2026-08-20 | Generalize Stage 5 into the target–ligand interaction-evidence framework; separate evidence level from gate-validation authority, establish the Level-3 verdict/lane fork, and complete the A2A claims-capped characterization baseline | ✅ Complete — A2A Level 1; claims capped pending gate validation |
| 009 | 2026-08-21 to 2026-08-27 | Define the prospective Stage-5 proof-of-discrimination protocol, formalize adversarial-negative eligibility, and qualify the DOCK lineage by native 3REY/XAC redocking | ✅ Complete — DOCK proof of life established; ProLIF discrimination remains pending |

## 2026-08-28 — Session 010: Stage 5 negative-panel construction and Graves null closure

Session 010 completed the preregistered DOCK/Graves geometric-decoy program and closed it as a null without post hoc tuning. Cognate XAC→3REY and 9XT→5OLH searches recovered only native-like retained poses; the deeper XAC A1 search also produced 20/20 near-native poses. A whole-receptor 5OLH→3REY Kabsch alignment was frozen using 281 mutually corresponding Cα pairs, with post-fit RMSD 0.893302 Å and det(R)=1. The preregistered 9XT→3REY cross-dock generated six gross alternatives (~11.4–12.6 Å RMSD) but no ≤2 Å native-like pose, so it was a sampling failure rather than a Graves scoring decoy. The reverse XAC→5OLH cross-dock produced zero saved poses due to bump rejection. The Graves ladder is therefore closed and must not be reopened or tuned during the current Stage-5 validation cycle.

After the Graves null, Stage 5 pivoted to experimentally established human-A2A molecular negatives whose status was fixed independently of ProLIF. Gao et al. (Biochemical Pharmacology, 2003) was frozen as the primary P3 source. Two candidates were selected before any generation: S-ENBA (hA2A Ki >10,000 nM; hA1 Ki 0.38 ± 0.19 nM) and N6-cyclooctyladenosine (hA2A Ki >10,000 nM; hA1 Ki 6.4 ± 1.4 nM). Both completed canonical DOCK ligand preparation and passed the frozen strain gate: S-ENBA 4.35/2.33 and N6-cyclooctyladenosine 3.01/1.65 total/max strain.

Under the frozen 3REY DOCK search, S-ENBA produced no saved poses because of bump rejection. N6-cyclooctyladenosine produced 20 poses; all 20 passed the recovered P1 implementation using PoseBusters 0.6.5 `dock.yml` with zero protein clashes. DOCK rank 1 (score -27.96) is therefore the qualified independent DOCK-family negative representative and remains ProLIF-unseen.

Fresh AutoDock Vina 1.2.7 runs were also completed locally under the frozen Session-007 protocol for both experimental negatives, producing 20 modes each (rank 1: S-ENBA -7.871 kcal/mol; N6-cyclooctyladenosine -5.922 kcal/mol). These fresh poses remain ProLIF-unseen and are retained as secondary/generalization controls. Vina participated in earlier ProLIF development and therefore does not count as the second independent generator family.

Session 010 closes with one pre-POD blocker: obtain and P1-qualify one negative from a genuinely second unrelated generator family. Session 011 should use OpenCode for that task, freeze exact negative-panel membership, and only then perform the blind frozen-ProLIF POD. All Session-010 artifacts, including failed/bump branches and the Graves null outputs, must be preserved.
