# Session 010 — Stage 5 Negative-Panel Construction and Graves Null Closure

**Date:** 2026-08-28  
**Status:** COMPLETE

## Session objective

Advance Stage 5 from the frozen native-positive ProLIF proof-of-life toward a blinded negative-panel POD by:

1. completing the preregistered Graves/DOCK geometric-decoy investigation without post hoc tuning;
2. determining whether DOCK can supply a naturally generated, physically plausible adversarial negative;
3. if the Graves route returns null, establishing experimentally supported human A2A molecular negatives independently of ProLIF;
4. qualifying generated negative poses under the frozen physical-plausibility gate while preserving ProLIF blindness;
5. leaving the panel ready for a second unrelated generator family and blind ProLIF POD in Session 011.

## Starting state

At Session 010 start:

- native A2A ProLIF positives were already established and frozen;
- ProLIF was the frozen Stage-5 interaction reader;
- the Graves/DOCK literature doctrine had been established;
- DOCK was the preferred independent/adversarial generator lineage;
- ProLIF was embargoed from prospective negatives;
- the primary unresolved problem was construction of independently eligible negative controls.

The strict Graves-style geometric-decoy interpretation used in this session required:

- physical plausibility;
- an alternative pose with **RMSD > 3.0 Å** from the experimental reference;
- native-like sampling in the relevant search, with native-like defined as **RMSD ≤ 2.0 Å**;
- the alternative to score better than the best native-like pose for a Graves scoring-decoy classification;
- no post hoc tuning after the preregistered null ladder was started.

## 1. Cognate DOCK searches

### 1.1 XAC / 3REY

The qualified XAC/3REY system remained the first cognate control.

A deeper A1 search with `match_goal 5000` produced 20 saved poses. All 20 were near-native.

Result:

- native-like sampling: **YES**;
- >3.0 Å alternatives: **NO**;
- Graves geometric decoy: **NO**.

This branch was closed without further tuning.

### 1.2 Fresh 5OLH canonical receptor preparation

A fresh canonical 5OLH receptor preparation was completed using the pinned pydock3/Blastermaster stack.

The correct initialization/run contract was recovered from the installed source:

```python
bm = Blastermaster()
bm.new(job_dir_path=...)
bm.run(job_dir_path=..., config_file_path=...)
```

The completed preparation produced all required DOCK artifacts:

- `INDOCK`;
- `matching_spheres.sph`;
- `vdw.bmp`;
- `vdw.vdw`;
- `trim.electrostatics.phi`;
- `ligand.desolv.heavy`;
- `ligand.desolv.hydrogen`;
- `rec.crg.pdb`.

Deposited 9XT was confirmed to lie within the generated VDW grid:

- `9XT_CONTAINED = True`;
- matching spheres = 24.

### 1.3 9XT canonical ligand preparation

9XT canonical preparation was completed through the qualified ligand-preparation path:

- SYBYL MOL2;
- AMSOL water and hexadecane calculations;
- validated direct torsional-strain calculation;
- strain annotation;
- DB2 generation.

Final strain:

- total strain = **0.87**;
- maximum strain = **0.51**;
- frozen 8/3 strain gate = **PASS**.

### 1.4 9XT / 5OLH cognate docking

The frozen DOCK search generated 20 poses.

All 20 were near-native.

Result:

- native-like sampling: **YES**;
- >3.0 Å alternatives: **NO**;
- Graves geometric decoy: **NO**.

No deeper cognate search was opened.

## 2. Preregistered Graves cross-docking ladder

The Graves 2005 primary paper was checked directly before the cross-docking experiment. Two corrections were frozen:

- the geometric-decoy RMSD threshold is strictly **>3.0 Å**;
- the approximately 200,000 compounds in Graves were the screened ACD library, not a count of confirmed nonbinders.

The cross-docking null ladder was preregistered as:

1. 9XT → 3REY;
2. if no qualifying Graves decoy, XAC → 5OLH;
3. if the reverse direction also fails, **STOP and reassess**.

No third receptor, altered `match_goal`, relaxed bump criterion, or other parameter tuning was permitted inside the ladder.

### 2.1 Frozen receptor-frame alignment

5OLH was aligned onto 3REY using all mutually corresponding whole-receptor Cα atoms.

Frozen method:

- whole-receptor Cα pairs only;
- no ligand atoms;
- no binding-site-only fit;
- no outlier rejection;
- no scaling;
- proper Kabsch rigid rotation only;
- `det(R)=+1`;
- the same receptor-derived rigid transform was applied unchanged to deposited 9XT.

Alignment result:

- `N_CA_PAIRS = 281`;
- pre-fit Cα RMSD = **73.021735 Å**;
- post-fit Cα RMSD = **0.893302 Å**;
- `det(R) = 1.000000000000`.

The **0.893302 Å** post-fit whole-receptor Cα RMSD was frozen as the frame-transfer error to report alongside ligand RMSDs.

Ligand RMSDs used graph-mapped heavy-atom correspondence with no ligand-on-ligand fitting or post hoc symmetry minimization.

### 2.2 9XT → 3REY

The frozen cross-dock produced six saved poses.

| Rank | DOCK score | Ligand RMSD (Å) | Receptor Cα RMSD (Å) | Class |
|---:|---:|---:|---:|---|
| 1 | -26.00 | 12.046 | 0.893 | Alternative |
| 2 | -25.71 | 11.442 | 0.893 | Alternative |
| 3 | -24.29 | 12.098 | 0.893 | Alternative |
| 4 | -24.23 | 12.167 | 0.893 | Alternative |
| 5 | -23.03 | 12.098 | 0.893 | Alternative |
| 6 | -21.82 | 12.639 | 0.893 | Alternative |

No pose was ≤2.0 Å.

Therefore:

- native-like sampling: **NO**;
- alternatives: **YES**;
- `BEST_NATIVE_SCORE = NONE`;
- `GRAVES_DECOYS = []`;
- verdict: **NO_GRAVES_DECOY__NO_NATIVE_SAMPLING**.

This was a sampling failure, not a Graves scoring failure.

### 2.3 XAC → 5OLH

The reverse reference was generated from the mathematical inverse of the already-frozen 5OLH→3REY transformation rather than by a new fit.

Inverse-transform checks:

- transformed XAC atoms = **31**;
- same receptor Cα pairs = **281**;
- receptor Cα RMSD = **0.893302 Å**;
- `det(R) = 1.000000000000`;
- maximum orthogonality error = **4.369e-13**.

The frozen XAC→5OLH cross-dock produced:

- matched orientations = **1,041**;
- saved poses = **0**;
- minimization steps = **0**;
- outcome = **bump rejection**.

Therefore native-like sampling was absent and no Graves scoring-decoy classification was possible.

### 2.4 Graves ladder verdict

The preregistered Graves geometric-decoy ladder is a **completed null**.

Observed pattern:

- cognate docking recovered native-like solutions but did not retain gross alternatives;
- cross-docking produced gross alternatives or complete bump rejection but lost native-like sampling;
- no search reproduced the Graves condition of sampling both native-like and wrong solutions while ranking the wrong solution better.

The Graves/DOCK ladder is closed for the current Stage-5 validation cycle and must not be reopened or tuned.

## 3. Pivot to independently established experimental molecular negatives

After closure of the geometric-decoy ladder, negative eligibility was moved to independent experimental biological status rather than manufactured pose wrongness.

The primary source selected for P3 candidate discovery was:

Gao Z-G, Blaustein JB, Gross AS, Melman N, Jacobson KA. *N6-Substituted adenosine derivatives: selectivity, efficacy, and species differences at A3 adenosine receptors.* **Biochemical Pharmacology. 2003;65(10):1675–1684.**

The source contains direct human adenosine-receptor binding measurements.

Two candidates were prospectively frozen before DOCK, Vina, or ProLIF exposure.

### 3.1 P3-001 — S-ENBA

Frozen identity:

- S-ENBA / `(2S)-N6-(endo-norbornyl)adenosine`;
- PubChem CID **5311431**;
- ChEMBL **CHEMBL1877326**;
- InChIKey **YKPCEENRZZBDMC-XSMNFLGNSA-N**;
- formula **C17H23N5O4**;
- formal charge **0**.

Experimental provenance:

- hA1 `Ki = 0.38 ± 0.19 nM`;
- hA2A `Ki >10,000 nM`.

### 3.2 P3-002 — N6-cyclooctyladenosine

Frozen identity:

- PubChem CID **54333857**;
- ChEMBL **CHEMBL2113424**;
- InChIKey **TUBLKCBQFVQEOG-SCFUHWHPSA-N**;
- formula **C18H27N5O4**;
- formal charge **0**.

Experimental provenance:

- hA1 `Ki = 6.4 ± 1.4 nM`;
- hA2A `Ki >10,000 nM`.

Candidate selection was completed before pose generation and did not depend on DOCK score, Vina score, PoseBusters outcome, or ProLIF.

## 4. Canonical preparation of experimental negatives

Both frozen negatives were converted from their frozen stereochemical molecular graphs to reproducible 3D structures using fixed-seed ETKDG followed by geometry optimization.

Frozen ETKDG seed:

- **20260828**.

Identity audits reproduced the frozen InChIKeys exactly.

Heavy-atom counts:

- S-ENBA = **26**;
- N6-cyclooctyladenosine = **27**.

SDF→SYBYL MOL2 conversion preserved coordinates to approximately `5×10^-4 Å`.

Both candidates completed the qualified canonical DOCK ligand-preparation sequence:

- Antechamber/SYBYL MOL2;
- AMSOL water and hexadecane;
- validated direct torsional-strain API;
- strain annotation;
- `mol2db2_py3_strain`;
- canonical DB2.

Final strain results:

| Candidate | Total strain | Max strain | Frozen 8/3 gate |
|---|---:|---:|---|
| S-ENBA | 4.35 | 2.33 | PASS |
| N6-cyclooctyladenosine | 3.01 | 1.65 | PASS |

No strain threshold was changed.

## 5. DOCK-family experimental-negative generation

Both frozen candidates were docked into the already-qualified 3REY receptor using the unchanged frozen DOCK search.

### 5.1 S-ENBA

Result:

- matched orientations = **1,006**;
- total complexes = **27,162**;
- saved poses = **0**;
- outcome = **bump rejection**.

This branch is closed. S-ENBA remains an experimentally valid P3 negative but does not supply a DOCK-family panel pose under the frozen search.

### 5.2 N6-cyclooctyladenosine

Result:

- matched orientations = **1,004**;
- scored evaluations = **2,732**;
- total complexes = **27,108**;
- saved poses = **20**;
- DOCK rank-1 score = **-27.96**.

All 20 saved poses were subsequently evaluated under the frozen P1 implementation.

## 6. P1 physical-plausibility implementation

The earlier Stage-3B wrapper was not retained in the repository, so the instrument implementation was recovered explicitly while preserving the frozen scientific definition.

Frozen implementation for current negative qualification:

- PoseBusters **0.6.5**;
- shipped configuration: **`dock.yml`**;
- `_fast` configuration: **not used**;
- original generated coordinates, no repair/minimization;
- `mol_true=None`;
- `mol_cond=3REY rec.crg.pdb`;
- `full_report=True`.

For the N6-cyclooctyladenosine DOCK ensemble:

- all 20 poses passed the PoseBusters `dock.yml` headline physical-plausibility checks;
- all 20 had `num_pairwise_clashes_protein = 0`;
- DOCK rank 1 therefore qualifies as the deterministic highest-ranked P1-passing DOCK representative.

Frozen DOCK-family negative representative:

- candidate: **P3-002 N6-cyclooctyladenosine**;
- generator: **DOCK 3.8.5 lineage**;
- pose: **rank 1**;
- DOCK score: **-27.96**;
- P3: **PASS**;
- P1: **PASS**;
- protein clashes: **0**;
- ProLIF exposure: **NONE**.

## 7. Fresh Vina secondary/generalization controls

The established Session-007 local environment split was recovered and reused:

- `sbdd-eval`: preparation/evaluation, including Meeko 0.7.1 and PoseBusters 0.6.5;
- `sbdd-dock`: AutoDock Vina 1.2.7 pose generation.

The frozen Vina protocol was reused unchanged:

- AutoDock Vina **1.2.7**;
- scoring = `vina`;
- rigid 3REY receptor;
- center = `(49.535806, 23.214581, 34.764065)`;
- box = `20 × 20 × 20 Å`;
- exhaustiveness = **32**;
- seed = **20260816**;
- `num_modes = 20`;
- `energy_range = 5 kcal/mol`.

Ligand preparation used Meeko **0.7.1** with the established default Gasteiger-charge path.

### 7.1 S-ENBA / Vina

Fresh Vina generation produced 20 modes.

Rank-1 affinity:

- **-7.871 kcal/mol**.

The exported SDF contained 20 molecules with 26 heavy atoms each.

The evaluated Vina ensemble passed the frozen PoseBusters P1 gate across all 20 modes; rank 1 was P1 PASS with zero protein clashes.

### 7.2 N6-cyclooctyladenosine / Vina

Fresh Vina generation produced 20 modes.

Rank-1 affinity:

- **-5.922 kcal/mol**.

The exported SDF contained 20 molecules with 27 heavy atoms each.

Fresh Vina poses remained ProLIF-unseen at session close.

### 7.3 Vina independence status

Vina participated in earlier ProLIF development and therefore **must not be represented as the second independent generator family** for the blinded specificity panel.

The fresh experimental-negative Vina poses are retained as useful unseen **secondary/generalization controls**, but they do not satisfy the unrelated-generator-family requirement.

## 8. ProLIF embargo status

At Session 010 close:

- ProLIF has **not** seen the new DOCK experimental-negative representative;
- ProLIF has **not** seen the fresh Vina experimental-negative ensembles;
- no negative-panel membership decision has been conditioned on ProLIF output.

The blind negative-panel POD has therefore not yet started.

## 9. Final Session-010 status

### Completed

- native ProLIF positive arm remains frozen;
- 5OLH canonical DOCK receptor preparation completed;
- 9XT canonical ligand preparation completed;
- cognate XAC and 9XT DOCK searches completed;
- strict Graves cross-docking null ladder completed and closed;
- whole-receptor 5OLH→3REY transform frozen with 281 Cα pairs and 0.893302 Å post-fit RMSD;
- two experimental hA2A-negative P3 candidates frozen before generation;
- both experimental negatives completed canonical ligand preparation and strain qualification;
- N6-cyclooctyladenosine supplied a P1-qualified independent DOCK-family negative;
- fresh Vina 1.2.7 experimental-negative ensembles generated without ProLIF exposure;
- PoseBusters 0.6.5 `dock.yml` P1 implementation made explicit and preserved.

### Remaining blocker

One genuinely **second unrelated generator-family negative** must be generated and P1-qualified before the negative panel is frozen and before ProLIF sees any new negative.

Vina does not satisfy this independence requirement because it participated in earlier ProLIF development.

## 10. Next-session roadmap

Session 011 should begin directly at the single remaining blocker:

1. use OpenCode to obtain/implement the second unrelated generator-family negative without reopening the completed DOCK/Graves work;
2. apply the already-frozen PoseBusters 0.6.5 `dock.yml` P1 gate;
3. if a qualifying second-family negative is obtained, freeze exact negative-panel membership and provenance;
4. only after panel freeze, remove the ProLIF embargo and perform the blind frozen-ProLIF POD;
5. record the Stage-5 validation verdict before beginning post-validation witness concordance.

## Do not reopen in Session 011

- the completed Graves geometric-decoy ladder;
- XAC/3REY or 9XT/5OLH DOCK tuning;
- bump relaxation;
- `match_goal` escalation for decoy hunting;
- new cognate receptors solely to hunt a Graves decoy;
- experimental P3 candidate selection;
- S-ENBA or N6-cyclooctyladenosine identity/provenance;
- the canonical ligand-preparation stack;
- the frozen 8/3 strain gate;
- PoseBusters version/configuration;
- Vina's status as a familiar/development lineage rather than the second independent generator;
- ProLIF parameters or positive-panel definitions.

## Preservation requirement

Preserve all Session-010 artifacts, including:

- successful and failed DOCK runs;
- 5OLH Blastermaster preparation artifacts;
- AMSOL and strain intermediates;
- Graves alignment and transformed-reference artifacts;
- cross-docking null outputs;
- P3 candidate source/provenance files;
- canonical DB2s;
- PoseBusters full reports;
- Vina PDBQT/SDF ensembles;
- failed/bump branches.

No Session-010 validation artifact should be deleted merely because it is not expected to appear in the final pipeline.
