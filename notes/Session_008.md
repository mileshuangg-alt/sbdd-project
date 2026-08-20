# Session 008 — Stage 5 fallback validation and target-interaction framework

**Date:** 2026-08-19 to 2026-08-20  
**Status:** COMPLETE

## Session objective

Resolve the remaining Stage-5 methodology after closure of the independent docking-validation arm.

The session began with D007 pending reference-pose fallback validation.

The goals were to:

1. investigate a physically plausible negative-control strategy;
2. determine whether the fallback could support hard attrition;
3. generalize Stage 5 beyond the current A2A benchmark;
4. freeze the A2A characterization definition before inspecting DiffSBDD Stage-5 outcomes;
5. complete the 16-molecule DiffSBDD Stage-5 baseline characterization.

---

## Starting state

The native ProLIF interaction reader had already passed its experimental proof of life on:

- 3REY / XAC;
- 5OLH / Vipadenant;
- 5OLO / Tozadenant.

Independent docking validation had closed as a documented negative result.

Candidates:

- Vina — permanent fail;
- AM1-BCC — eliminated before execution;
- smina / Vinardo — permanent fail;
- GNINA CNN rescore — permanent fail;
- limited receptor flexibility — considered but not selected.

The original docking-dependent Stage-5 design was blocked.

---

## Reference-pose negative-control investigation

A synthetic negative-control strategy was developed using rigid rotations of native experimental ligand poses.

The goal was to identify a pose condition that:

1. remained physically plausible under Stage 3B; but
2. disrupted experimentally grounded A2A recognition.

Ligands were rotated rigidly around their principal geometric axes while preserving:

- ligand centroid;
- internal molecular geometry;
- native receptor coordinates.

The initial predeclared rotation grid was:

- 10°
- 20°
- 30°
- 45°

across three ligand principal axes.

Structural analysis confirmed centroid displacement and internal-distance changes were numerical zero within floating-point precision.

Larger rotations frequently produced severe protein overlap.

---

## Stage-3B screening

The 10° candidates were screened using the existing PoseBusters Stage-3B pocket-relative evaluator.

Principal axis 1 was the only 10° rule that remained physically plausible across all three native controls.

The 10° axis-1 condition therefore became the candidate subtle negative.

ProLIF evaluation showed that all three 10° controls retained their native Phe168 and Asn253 recognition patterns.

The 10° condition was therefore insufficiently disruptive.

---

## Midpoint follow-up

A single data-informed midpoint follow-up at 15° axis 1 was explicitly allowed.

Stopping rule:

- if 15° failed physical plausibility, stop;
- if 15° remained plausible but retained the interaction pattern, stop;
- no further degree-by-degree optimization.

Stage-3B results at 15° axis 1:

- 3REY — PASS, zero clashes;
- 5OLH — PASS, zero clashes;
- 5OLO — PASS, zero clashes.

ProLIF evaluation again retained the native recognition patterns across all three controls.

At 20° axis 1:

- 3REY remained Stage-3B plausible;
- 5OLH remained Stage-3B plausible;
- 5OLO failed physical plausibility with protein clashes.

Conclusion:

**A universal principal-axis rigid rotation did not produce a physically plausible interaction-disrupted negative across the three cognate chemotypes.**

The rotation-based negative-control strategy was closed and not adopted.

No additional angle tuning was permitted.

---

## Stage-5 conceptual pivot

The negative-control result prompted separation of two questions:

1. how much target–ligand interaction evidence exists;
2. whether the implemented computational gate has earned hard-claim authority.

Stage 5 was redefined as the **target–ligand interaction evidence layer**.

The framework is method-generalized while target-specific compatibility definitions remain target-specific.

Canonical evidence levels were established:

Level 1 - sufficient for validated compatibility testing  
Level 2 - sufficient for interaction characterization  
Level 3 - insufficient for target-compatibility assessment

A target without a three-dimensional structure is out of scope for Stage 5 entirely.

Evidence level and gate validation are separate.

A Level-1 target may still have its claims capped if its implemented hard gate has not established discrimination.

---

## Gate-validation rule

Hard attrition requires both:

- sensitivity on cognate positive controls; and
- discrimination on plausible-but-wrong negative poses.

A negative pose that fails physical plausibility does not establish Stage-5 discrimination.

Gate validation is target-specific and implementation-specific.

A gate validated on one target earns no hard-claim authority on another.

Validation outcomes are recorded as:

- ESTABLISHED
- NOT ESTABLISHED

Targets are not demoted because gate validation remains incomplete.

Instead:

**CLAIMS CAPPED PENDING GATE VALIDATION**

Under a capped gate, outputs are reported as pattern reproduction rather than Stage-5 PASS/FAIL.

---

## Level-3 fork

For structurally defined targets with insufficient target–ligand interaction evidence:

### VERDICT

Target compatibility is INCONCLUSIVE.

No target-specific feasibility claim is permitted.

### LANE

Molecules are not failed because of the evidence gap.

They continue through stages whose claims do not require target-interaction evidence.

Predicted-pocket characterization using P2Rank or fpocket is permitted, but the nominated site must remain labeled as a prediction.

Level-3 molecules carry an interaction-unverified flag.

---

## A2A evidence assignment

A2A was assigned:

**LEVEL 1**

because direct experimental cognate target–ligand complexes are available.

The A2A evidence level was kept separate from the validation status of the implemented gate.

---

## Frozen A2A reference-recognition definition

The definition was derived before inspecting the DiffSBDD Stage-5 baseline.

Native experimental complexes:

- 3REY / XAC;
- 5OLH / Vipadenant;
- 5OLO / Tozadenant.

Conserved recognition roles:

### Phe168

Hydrophobic or aromatic recognition.

Operational ProLIF definition:

**Hydrophobic OR PiStacking**

### Asn253

Ligand hydrogen-bond-acceptor recognition.

Operational ProLIF definition:

**HBAcceptor**

Combined frozen definition:

**(Phe168 Hydrophobic OR PiStacking) AND (Asn253 HBAcceptor)**

VdWContact is retained for characterization but is not required by the frozen pattern.

---

## DiffSBDD Stage-5 input provenance

`stage3_input.sdf` contained 18 Stage-3-eligible molecules.

The finalized Stage-3 results identified 16 survivors:

0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19.

Original molecule IDs were preserved as the provenance key.

Stage 5 did not renumber molecules.

Generator-provided ligand coordinates were not modified.

---

## 3RFM coordinate-frame correction

An initial Stage-5 characterization incorrectly paired DiffSBDD poses generated in the 3RFM coordinate frame with the 3REY receptor.

That result produced 0/16 reference-pattern reproduction and was declared invalid and superseded.

The error was identified before scientific interpretation.

The experimental 3REY/5OLH/5OLO complexes define the A2A reference pattern, but DiffSBDD poses must be measured against the receptor representation in their own 3RFM coordinate frame.

---

## Interaction-ready 3RFM receptor

The existing Stage-3B artifact:

`experiments/phase1_diffsbdd/evaluation/prepared_3rfm_pocket.pdb`

contained:

- Phe168;
- Asn253;
- correct heavy-atom geometry;
- zero explicit hydrogens.

It was therefore sufficient for Stage-3B geometry but not for the validated ProLIF interaction pathway.

The existing validated receptor-preparation methodology was reused.

The 3RFM pocket was prepared with:

- PDB2PQR / PROPKA;
- pH 7.4;
- explicit hydrogens;
- deterministic alternate-location handling;
- heavy-atom coordinate restoration;
- topology and displacement audits;
- Phe168 / Asn253 numbering audit;
- His250 protonation audit.

Preparation result:

- raw heavy atoms: 286;
- prepared heavy atoms: 287;
- added heavy atom: terminal HIS A 278 OXT;
- hydrogens added: 295;
- original heavy-atom maximum displacement after restoration: 0.000000 Å.

The resulting interaction-ready receptor was:

`prepared_3rfm_pocket_pH7.4_restored.pqr`

The evaluator was updated to load it through the validated `load_protein()` pathway.

---

## Independent 3RFM proof of life

A native 3RFM / caffeine proof-of-life test was performed using:

- the interaction-ready 3RFM receptor;
- deposited native caffeine heavy-atom coordinates;
- the validated ProLIF reader;
- the already frozen A2A reference definition.

Observed:

Phe168:
- PiStacking
- VdWContact

Asn253:
- HBAcceptor
- VdWContact

Frozen A2A reference-recognition pattern:

**REPRODUCED**

The native 3RFM control therefore provided an independent same-coordinate-frame positive proof of life for the final DiffSBDD Stage-5 implementation.

This established sensitivity in the 3RFM implementation.

It did not establish plausible-negative discrimination.

---

## DiffSBDD Stage-5 characterization result

The corrected Stage-5 evaluator was applied to the 16 Stage-3 survivors using their unmodified generator-provided poses.

Results:

- Phe168 reference feature reproduced: **15/16**
- Asn253 reference feature reproduced: **4/16**
- complete frozen A2A reference pattern reproduced: **3/16**

Complete-pattern molecule IDs:

- 0
- 3
- 18

The permitted result statement is:

**3/16 generator-provided DiffSBDD poses reproduced the predeclared A2A reference-recognition pattern.**

This is not a Stage-5 survival rate.

No Stage-5 attrition was applied.

The result remains conditional on the generator-provided poses.

---

## Final Stage-5 status

A2A target–ligand evidence:

**LEVEL 1**

Positive sensitivity:

**ESTABLISHED**

Hard-gate discrimination:

**NOT ESTABLISHED**

Claims status:

**CAPPED PENDING GATE VALIDATION**

Current Stage-5 role:

**TARGET-INTERACTION CHARACTERIZATION**

DiffSBDD Stage-5 baseline:

**COMPLETE**

FLOWR Stage-5 evaluation:

**FUTURE — MUST USE THE IDENTICAL FROZEN PATHWAY**

---

## Session conclusion

Session 8 closed the unresolved Stage-5 methodological branch without forcing a hard attrition gate unsupported by validation.

The project now has:

- a generator-independent Stage-5 evidence framework;
- explicit evidence levels;
- a separate target-specific gate-validation layer;
- a frozen A2A reference-recognition definition;
- an interaction-ready 3RFM receptor;
- an independent native 3RFM proof of life;
- a completed non-attritional DiffSBDD Stage-5 baseline.

The failed docking and plausible-negative experiments remain documented negative results rather than being hidden or tuned away.

Stage 5 is now ready to be applied identically to future generators, including FLOWR, under the same frozen A2A characterization pathway.