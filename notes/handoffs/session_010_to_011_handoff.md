# Session 010 → Session 011 Handoff

**Date:** 2026-08-28  
**Next-session objective:** Obtain and P1-qualify the second genuinely unrelated generator-family negative, freeze the negative panel, then perform the blind frozen-ProLIF POD.

## Current Stage-5 state

Stage 5 is near the blind POD boundary.

The native-positive ProLIF arm is already frozen. The strict Graves/DOCK geometric-decoy program has been completed as a preregistered null. Two experimental human-A2A negatives were frozen before generation. One of them now supplies a P1-qualified DOCK-family negative. Fresh Vina controls also exist but do not count as the second independent generator family because Vina participated in earlier ProLIF development.

**ProLIF remains embargoed from all newly constructed negatives.**

## Frozen decisions that carry forward

### ProLIF

- ProLIF remains the frozen Stage-5 interaction reader.
- Do not change ProLIF version, interaction definitions, parameters, or positive-panel interpretation before the blind POD.
- Do not expose any new negative to ProLIF until exact negative-panel membership is frozen.

### P1 physical plausibility

Use exactly:

- PoseBusters **0.6.5**;
- shipped **`dock.yml`** configuration;
- original generated coordinates;
- no coordinate repair or minimization;
- `mol_true=None`;
- qualified receptor supplied as `mol_cond`;
- preserve `full_report=True` output.

The P1 implementation is now explicit and should not be redesigned in Session 011.

### Experimental P3 negatives

The following identities and negative statuses were frozen before pose generation:

**P3-001 — S-ENBA**

- PubChem CID 5311431;
- ChEMBL CHEMBL1877326;
- InChIKey YKPCEENRZZBDMC-XSMNFLGNSA-N;
- hA2A `Ki >10,000 nM`;
- hA1 `Ki = 0.38 ± 0.19 nM`.

**P3-002 — N6-cyclooctyladenosine**

- PubChem CID 54333857;
- ChEMBL CHEMBL2113424;
- InChIKey TUBLKCBQFVQEOG-SCFUHWHPSA-N;
- hA2A `Ki >10,000 nM`;
- hA1 `Ki = 6.4 ± 1.4 nM`.

Primary P3 provenance: Gao et al., *Biochemical Pharmacology* (2003).

Do not replace these candidates based on downstream generator convenience or ProLIF behavior.

## What Session 010 established

### 1. Graves geometric-decoy program returned a preregistered null

Cognate searches:

- XAC→3REY: native-like recovery, no qualifying >3 Å alternative;
- deeper XAC A1 search: 20/20 near-native;
- 9XT→5OLH: 20/20 near-native.

Cross-docking ladder:

**9XT→3REY**

- six saved poses;
- ligand RMSDs approximately 11.4–12.6 Å;
- no ≤2 Å native-like pose;
- therefore sampling failure, not a Graves scoring decoy.

**XAC→5OLH**

- 1,041 matched orientations;
- zero saved poses;
- bump rejection;
- therefore no Graves scoring-decoy classification.

The null ladder is closed. Do not tune or reopen it.

### 2. Frozen receptor-frame transform

5OLH→3REY whole-receptor alignment:

- 281 mutually corresponding Cα pairs;
- post-fit Cα RMSD = **0.893302 Å**;
- `det(R)=1`;
- no ligand atoms, binding-site-only fitting, outlier rejection, scaling, or reflection.

The same receptor-derived transform was used for ligand reference transfer. The inverse transform was used for the reverse direction rather than performing a new fit.

### 3. Experimental-negative canonical preparation succeeded

Both P3 candidates passed the frozen 8/3 strain gate:

| Candidate | Total strain | Max strain |
|---|---:|---:|
| S-ENBA | 4.35 | 2.33 |
| N6-cyclooctyladenosine | 3.01 | 1.65 |

Both canonical DB2s and all preparation intermediates must be preserved.

### 4. Independent DOCK-family negative is qualified

**P3-002 N6-cyclooctyladenosine / DOCK rank 1**

- DOCK rank-1 score = **-27.96**;
- P3 = PASS;
- P1 = PASS under PoseBusters 0.6.5 `dock.yml`;
- protein clashes = 0;
- ProLIF exposure = NONE.

All 20 saved P3-002 DOCK poses passed P1, but rank 1 is the deterministic highest-ranked P1-passing representative.

**P3-001 S-ENBA / DOCK**

- 1,006 matched orientations;
- 27,162 total complexes;
- zero saved poses;
- bump rejection.

Do not rerun or tune the S-ENBA DOCK branch.

### 5. Fresh Vina secondary controls exist

Frozen Session-007 Vina protocol:

- AutoDock Vina 1.2.7;
- 3REY rigid receptor;
- center `(49.535806, 23.214581, 34.764065)`;
- box `20 × 20 × 20 Å`;
- exhaustiveness 32;
- seed 20260816;
- 20 modes;
- energy range 5 kcal/mol.

Fresh runs:

- S-ENBA: 20 modes, rank 1 = **-7.871 kcal/mol**;
- N6-cyclooctyladenosine: 20 modes, rank 1 = **-5.922 kcal/mol**.

At least the evaluated Vina ensemble passed P1 across all 20 modes with rank 1 P1 PASS and zero protein clashes.

However, **Vina is a familiar/development lineage and must not be counted as the second independent generator family.** Retain these poses as secondary/generalization controls only.

## Current panel status

### Positive arm

Frozen and complete.

### Negative arm

**Qualified independent member already available:**

- P3-002 N6-cyclooctyladenosine / DOCK rank 1 / P1 PASS.

**Secondary non-independent controls available:**

- fresh Vina experimental-negative poses, still ProLIF-unseen.

**Remaining blocker:**

- one P1-qualified negative from a genuinely second unrelated generator family.

## Session 011 immediate tasks

1. Use OpenCode to obtain/implement the second unrelated generator-family negative.
2. Keep generation/evaluation separated: generator writes files; P1 consumes files.
3. Do not use ProLIF to select, rank, filter, or troubleshoot candidate poses.
4. Apply the frozen PoseBusters 0.6.5 `dock.yml` P1 gate.
5. Once one second-family negative passes P1, freeze exact negative-panel membership and provenance.
6. Record hashes/paths for the exact frozen negative pose files.
7. Only then remove the ProLIF embargo.
8. Run the frozen ProLIF reader blindly on the frozen positive and negative panel.
9. Record the Stage-5 POD verdict before beginning independent-witness concordance.

## Do not reopen

Do not spend Session 011 on any of the following:

- further Graves literature interpretation;
- another Graves cross-dock direction;
- new cognate receptors solely to hunt geometric decoys;
- `match_goal` tuning;
- bump relaxation;
- rebuilding 5OLH receptor preparation;
- rebuilding XAC or 9XT ligand preparation;
- changing the 8/3 strain gate;
- replacing S-ENBA or N6-cyclooctyladenosine because another molecule is easier to generate;
- changing PoseBusters version/configuration;
- treating Vina as an independent second family;
- running ProLIF before panel freeze;
- changing ProLIF parameters after seeing negative behavior.

## Environment / execution facts worth retaining

### Local Mac

`sbdd-eval`:

- RDKit 2026.03.5;
- PoseBusters 0.6.5;
- ProLIF 2.2.0;
- Meeko 0.7.1;
- MolScrub 0.2.2.

`sbdd-dock`:

- AutoDock Vina 1.2.7;
- pose generation only.

The Session-007 split remains intentional:

- `sbdd-eval` → preparation/evaluation;
- `sbdd-dock` → Vina pose generation.

### gpu-dev1

The legacy DOCK 3.8.5 preparation/docking stack remains server-side and should not be rediscovered or rebuilt during Session 011 unless a genuinely new server-state fact requires it.

## Workflow rule reinforced by Session 010

Before asking the user to run exploratory commands or rediscover operational details:

1. inspect prior session conclusions/history;
2. inspect retained session logs/handoffs and Git/project artifacts;
3. use uploaded artifacts where available;
4. only then query a live machine for genuinely absent or execution-state-specific information.

Also track machine, environment, working directory, required inputs, and expected outputs explicitly across host boundaries.

## Preservation requirement

Preserve all Session-010 intermediates and null results, including failed/bump runs. Do not delete artifacts merely because they are not expected in the final pipeline.

## Starting principle for Session 011

**There is one pre-POD blocker, not an open-ended methodology problem:** obtain one P1-qualified negative from a second genuinely unrelated generator family, freeze the panel, then run ProLIF blind.
