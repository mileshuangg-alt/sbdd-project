# Session 012 — Stage-5 Pose-Level Adversarial Sampling Diagnostic

**Session date:** 2026-09-15

## 200-save retention diagnostic

The preregistered 200-save measurement was completed using the frozen Session-010 A1 XAC/3REY DOCK setup, with only `number_save` and `number_write` increased from 20 to 200.

The measurement evaluated all 200 saved, score-ranked XAC poses.

### Results

- poses evaluated = 200;
- RMSD minimum = 0.5045455233785068 Å;
- RMSD maximum = 0.6279398324885965 Å;
- RMSD mean = 0.5741562261346086 Å;
- RMSD <= 2.0 Å = 200/200;
- RMSD > 2.0 Å = 0/200;
- `d_rel` minimum = 0.9032485336292032;
- `d_rel` maximum = 0.9292307923112898;
- `d_rel` mean = 0.9154592016105315;
- `d_rel >= 0.75` = 200/200;
- RMSD > 2.0 Å and `d_rel >= 0.75` = 0/200;
- first eligible alternative rank = none.

### D020 failure branch

Under the frozen D020 eligibility rule, no eligible genuinely alternative physically plausible XAC pose was obtained from the 200-save score-ranked population.

The preregistered failure branch therefore applies:

> **No eligible genuinely alternative physically plausible pose was obtained from the 200-save score-ranked population.**

The result does not reopen, retune, or invalidate the closed Session-010 Graves/DOCK geometric-decoy ladder.

The measurement establishes only that increasing retention from 20 to 200 within the frozen A1 search did not expose a physically plausible pose with RMSD >2.0 Å.

It does not establish that DOCK cannot generate genuinely alternative physically plausible poses under a different sampling mechanism.

No ProLIF results were used in candidate selection or interpretation of this measurement.

## Measurement artifact

The 200-pose source archive is:

`references/stage5/dock385/3REY/xac_adversarial_A1_matchgoal5000/measurement_200save/test.mol2.gz`

The measurement was performed with the frozen A1 setup and only the saved-pose controls changed from 20 to 200.

## Status

The D020 preregistered retention diagnostic is complete.

The purpose-built search contract remains unfrozen.

---

## D021 continuation — rDock Run-2 audit and primary-panel expansion

The next Session-012 work continued directly from the D020 200-save failure branch and the frozen Session-011 validation boundary.

The authoritative rDock Run-2 archive was remeasured with the frozen D020 machinery because the original Run-2 measurement table had not been preserved.

Authoritative archive:

`references/stage5/d021_rdock_3REY_XAC_single_shot_qualification_20260917/XAC_3REY_run2.sd`

Superseding measurement artifact:

`references/stage5/d021_rdock_3REY_XAC_single_shot_qualification_20260917/run2_d020_measurement_v2/XAC_3REY_run2_d020_measurements.csv`

The remeasurement reproduced the historical Run-2 summary:

```text
poses = 50
near-native = 1
alternatives = 49

RMSD min = 1.0622873991472819 A
RMSD max = 13.524631893279377 A

d_rel min = 0.7856314103933344
d_rel max = 0.9213006403054211
```

Among the 49 alternatives:

```text
RMSD >= 3.0 A:          48
2.0 A < RMSD < 3.0 A:    1
```

The single intermediate-zone pose was excluded by the frozen D020 rule.

### P4 scoring audit

Run-2 file order was not treated as score rank because the `<SCORE>` sequence was non-monotonic.

Rank was derived from the pinned rDock scoring convention rather than file order.

Five candidates satisfied the frozen P1-P4 eligibility requirements:

```text
poses 44, 1, 11, 29, 35
```

All five were P1-P4 eligible.

No frozen tiebreak existed, so no post-result tiebreak was invented.

### P1 physical-plausibility qualification

The frozen PoseBusters 0.6.5 `dock` configuration was applied to all 48 RMSD >= 3.0 A alternatives using original generated coordinates and no repair/minimization.

All 48 passed the frozen P1 hard gate.

### Negative-panel expansion

The existing Session-011 DOCK rank-1 P3-002 representative remained the DOCK-lineage seat.

The five qualified rDock XAC poses became the rDock-lineage seats.

The resulting primary negative panel was frozen as:

```text
DOCK  = 1/6
rDock = 5/6
TOTAL = 6/6
```

Panel membership was frozen before any new negative was exposed to ProLIF.

The authoritative panel artifacts were preserved under:

`references/stage5/negative_panel/panel/`

---

## Frozen reader and blind-input preparation

The unchanged historical ProLIF reader remained authoritative:

`scripts/stage5/test_native_reader_controls.py`

Frozen reader environment:

```text
ProLIF 2.2.0
sbdd-eval
```

Frozen A2A recognition definition:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

`VdWContact` remained characterization evidence only and did not satisfy the Phe168 arm.

The six frozen negative inputs were assembled under opaque IDs:

```text
NEG001
NEG002
NEG003
NEG004
NEG005
NEG006
```

The blind mapping was not used to alter processing or interpret results.

---

## MOL2 adapter qualification

The DOCK representative was preserved as MOL2 while the historical reader's native negative route used SDF. A separate MOL2-to-ProLIF adapter was therefore implemented without modifying the frozen reader.

NEG001 adapter qualification established:

```text
atom count: 54
conformer present: true

maximum MOL2 -> RDKit coordinate deviation: 0.0 A
RMS coordinate deviation:                  0.0 A

ProLIF atom count: 54
```

The qualification also recorded complete per-atom and per-bond chemical-perception information, including element, formal charge, aromaticity, bond endpoints, bond order, and bond aromaticity.

The frozen reader remained byte-for-byte unchanged.

The qualification was limited to adapter correctness:
- coordinate preservation through MOL2 -> RDKit;
- successful RDKit -> ProLIF molecule construction;
- chemical-perception audit.

No blind interaction reader was run during adapter qualification.

---

## Residue-75 guard recovery

Before the six-member blind read, the historical Session-011 residue-75 guard was recovered verbatim.

The guard exists because the earlier receptor-artifact comparison identified the largest coordinate discrepancy at residue 75 CD2.

Frozen execution rule:

- if a blind pose contacts residue 75, flag that pose and stop on it;
- otherwise continue reporting the frozen anchor interactions.

The preserved definition does not specify residue name or chain, so those were not reconstructed.

Residue 75 is audit/guard evidence, not part of the A2A recognition definition.

---

## Blind six-member ProLIF negative-panel read

The six frozen opaque negatives were read through the unchanged historical ProLIF 2.2.0 pathway.

Execution summary:

```text
inputs processed:            6/6
ligand-loading failures:    0
residue-75 guard:            6/6 CLEAR
strict recognition result:   6/6 FALSE
```

The six poses remained recognition-negative under the frozen criterion.

Representative interaction-class pattern:

- NEG001: Phe168 `VdWContact`; Asn253 none.
- NEG002: Phe168 `VdWContact`; Asn253 none.
- NEG003: Phe168 none; Asn253 none.
- NEG004: Phe168 `VdWContact`; Asn253 `HBAcceptor + VdWContact`.
- NEG005: Phe168 `VdWContact`; Asn253 `HBAcceptor + VdWContact`.
- NEG006: Phe168 `VdWContact`; Asn253 none.

NEG004 and NEG005 demonstrated why the strict interaction-class rule matters: Asn253 HBAcceptor alone does not rescue a pose whose Phe168 interaction is only VdWContact.

The blind read did not initially compute the overall panel verdict.

The result artifact metadata was subsequently corrected, without rerunning ProLIF, so that it explicitly records:

```text
frozen A2A recognition pattern evaluated: true
per-pose recognition results recorded:   true
overall Stage-5 panel verdict computed:  false
overall Stage-5 panel verdict:           NOT_COMPUTED
```

Corrected blind artifact:

`references/stage5/negative_panel/panel/blind_negative_panel_prolif_read_20260924T004822Z.json`

SHA-256:

`0b230fd7b8e15644760963a85430e58ce97e3cba2acfdb131e75eadafc06a3ee`

No interaction results changed during the metadata correction.

---

## D022 — symmetric discriminator semantics

A framework gap was identified in the meaning of “experimental positives retained.”

The historical native ProLIF proof-of-life criterion was broader:

```text
any Phe168 interaction
AND
any Asn253 interaction
```

The later frozen A2A recognition criterion was narrower:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

D022 froze the stricter interaction-class rule as the criterion for both arms of the Stage-5 panel verdict.

The historical proof-of-life criterion remains valid as the historical instrument-qualification record and is not retroactively rewritten.

D022 also froze failure handling: an experimental positive failing the strict rule would remain a failure under D022; the rule could not be loosened post hoc to force a passing panel.

---

## Retrieval-only experimental-positive audit

After D022 was frozen, the preserved positive interaction-class evidence was retrieved without rerunning ProLIF.

Results:

| Experimental positive | Phe168 | Asn253 | D022 retained |
|---|---|---|---|
| 3REY / XAC | Hydrophobic | HBAcceptor | yes |
| 5OLH / Vipadenant (9XT) | PiStacking | HBAcceptor | yes |
| 5OLO / Tozadenant (9XW) | Hydrophobic + PiStacking | HBAcceptor | yes |

D022 panel validation therefore produced:

```text
experimental positives retained: 3/3
primary-panel negatives rejected: 6/6
```

The retrieval-derived positive-arm audit artifact was:

`references/stage5/d022_positive_arm_audit_20260925.json`

SHA-256:

`441fd06afd883637615d33e6a58644cca5fb67d8d373b164584f413217e11e49`

The full historical machine-readable positive ProLIF interaction object was not retained, but preserved interaction-class evidence was sufficient to apply D022.

---

## D023 — authority to apply the validated gate to the DiffSBDD cohort

The 16 Stage-3-surviving DiffSBDD molecules had previously been measured under the frozen A2A recognition criterion.

Preserved measurement:

```text
Phe168 feature:    15/16
Asn253 feature:     4/16
complete pattern:   3/16
```

Complete-pattern reproductions:

```text
molecule IDs 0, 3, 18
```

D012 had intentionally kept the 3/16 result as characterization-only and explicitly stated that the 13 non-reproducing molecules were not Stage-5 failures.

Following successful gate validation, D023 was approved as an **authority decision**.

D023 did not change the recognition criterion and did not rerun or reinterpret the preserved measurements.

The 3/16 outcome was known at decision time. D023 is therefore documented as a post-validation authority grant, not a blinded criterion-selection decision.

### Mechanical Stage-5 disposition

```text
Stage-5 input cohort:                 16
Retained through Stage 5:              3/16
Retained molecule IDs:                 0, 3, 18
Attrited from cascade progression:    13/16
```

The 13 attrited molecules remain permanently retained as characterization evidence.

The generator failure-mode pattern is preserved:

```text
Phe168:    15/16
Asn253:     4/16
Complete:   3/16
```

Attrition means failure to reproduce the frozen A2A molecule-level recognition criterion under the validated gate. It does not establish experimental nonbinding, biological inactivity, or pose-level incorrectness.

D023 mechanical disposition artifact:

`references/stage5/d023_diffsbdd_stage5_disposition_20260925.json`

SHA-256:

`929db9d1a1b25d4af109d3e3c328e31c5d1cbf596035fc86941c8c88a906e445`

D023 Markdown companion was finalized alongside the JSON and preserves the same per-molecule disposition.

---

## D019 witness concordance

The independently qualified PLIP witness remained a witness only and did not replace ProLIF as the Stage-5 instrument.

For the frozen 16-member DiffSBDD cohort:

```text
ProLIF false / PLIP false: 13
ProLIF true  / PLIP true:   3
discordant:                 0
complete-pattern concordance: 16/16
```

The witness therefore corroborated the frozen interaction-pattern measurements without establishing a separate verdict criterion.

---

## Final Stage-5 evidence freeze

The final Stage-5 evidence package was assembled from preserved results without scientific reruns.

Final frozen validation counts:

```text
A2A evidence level:              LEVEL 1

Experimental positives retained: 3/3
Primary negatives rejected:      6/6

Residue-75 guard clear:          6/6
```

Final DiffSBDD cascade disposition:

```text
Stage 5 entering: 16
Stage 5 retained:  3
Stage 5 attrited: 13
```

The three retained molecules are IDs 0, 3, and 18.

The 13 attrited molecules remain permanent characterization evidence.

Final evidence-freeze artifacts:

`references/stage5/stage5_final_evidence_freeze_20260925.json`

SHA-256:

`a8acad71cfe6b06207017285c70a182b56a9135c319dbe890382415e4cc557ae`

`references/stage5/stage5_final_evidence_freeze_20260925.md`

The corrected Markdown SHA-256 was recorded after restoring the scientific table headers and updating the D023 Markdown hash in the Evidence Index:

`ce11d19b81119ca0700062cb43649d06523c0345a839871328d67f2c35958191`

The final freeze explicitly preserves the distinction between:
- validation evidence;
- DiffSBDD cascade disposition;
- permanent characterization evidence.

No scientific reruns were performed during evidence closure.

---

## README update and Phase-1 baseline status

The project README was updated to reflect the finalized Stage-5 methodology and current baseline.

Stage 5 is now represented as:

```text
Target–Ligand Interaction Evidence
```

with:
- A2A Level 1 interaction evidence;
- ProLIF 2.2.0 as the frozen verdict instrument;
- PLIP as the independent witness;
- the frozen strict A2A recognition criterion;
- validated molecule-level authority;
- explicit claim boundaries;
- DiffSBDD Stage-5 attrition.

The current strict cascade is now:

```text
20 generated
    ↓
19 / 20 Stage 1
    ↓
18 / 19 Stage 2
    ↓
16 / 18 Stage 3
    ↓
16 / 16 Stage 4
    ↓
 3 / 16 Stage 5
    ↓
Stage 6 — Synthetic Feasibility
```

Current cumulative strict cascade survival:

```text
3 / 20 = 15%
```

The README also records that the FLOWR comparator arm is deferred until the complete DiffSBDD baseline cascade is implemented and frozen. FLOWR must subsequently use the same frozen cascade without downstream recalibration from FLOWR outcomes.

---

## Session-012 closure status

Session 012 began with a D020 preregistered 200-save diagnostic and continued through D021 frozen-panel construction, blind ProLIF execution, D022 criterion/positive-retention resolution, D023 authority approval, mechanical DiffSBDD Stage-5 attrition, README finalization, and final evidence freezing.

### Scientific status

```text
D020 diagnostic:                 COMPLETE
D021 panel qualification:        COMPLETE
Primary negative panel:          FROZEN, 6 candidates
Blind ProLIF negative read:      COMPLETE, 6/6 rejected
D022 symmetric criterion:        FROZEN
D022 validation:                 3/3 positives, 6/6 negatives
D023 gate authority:             APPROVED / FROZEN
DiffSBDD Stage-5 disposition:    3/16 retained, 13/16 attrited
Stage-5 evidence freeze:         COMPLETE
README Stage-5 update:           COMPLETE
```

### Claim boundary

The completed Stage-5 evidence supports bounded A2A molecule-level interaction-pattern claims.

It does not establish:
- general pose sensitivity;
- universal or general specificity;
- experimental binding;
- biological efficacy;
- transfer of A2A validation authority to another target.

The 13 Stage-5-attrited DiffSBDD molecules are not called nonbinders or scientifically invalid. Their preserved measurements remain permanent characterization evidence.

### Preservation

All Stage-5 implementation, validation, failed-branch, panel, blind-read, witness, disposition, and evidence-freeze artifacts are to remain preserved.

No scientific artifact is deleted merely because it is not expected to appear in the final forward pipeline.

### Next stage

Stage 5 is now closed and frozen for the Phase-1 DiffSBDD baseline.

The next scientific stage is:

**Stage 6 — Synthetic Feasibility**

The FLOWR comparator remains deferred until the complete DiffSBDD baseline cascade is built and frozen.

---

## Session-012 final status

**Status: CLOSED — Stage-5 validation, authority, DiffSBDD disposition, evidence freeze, and README closure complete.**

No additional Stage-5 rerun is authorized or required for the current DiffSBDD baseline.
