# Stage 5 DOCK Debugging and Implementation Report

**Session:** 009  
**System:** A2A adenosine receptor, 3REY/XAC  
**Purpose:** Personal implementation guide and project checkpoint  
**Status:** DOCK proof-of-life complete; ProLIF proof-of-discrimination next

## Executive summary

We did not begin Session 009 intending to make DOCK the center of the pipeline. DOCK entered the work because the Stage-5 validation design requires an independent source of credible adversarial poses for testing the frozen ProLIF interaction reader. Before a DOCK-generated wrong pose can be used as a meaningful negative, however, we need evidence that the same docking lineage can also find the correct pose. Otherwise a "negative" could simply reflect a broken search.

The initial 3REY/XAC experiment appeared to show exactly that problem: DOCK sampled thousands of orientations but saved zero poses. After a long debugging sequence, we learned that the search itself was not the primary failure. A handcrafted ligand DB2 carried placeholder torsional-strain values of `+9999.990`, while the frozen DOCK gate allowed total strain below 8 and maximum strain below 3. DOCK was therefore rejecting every ligand set because of invalid metadata before the physical pose could qualify.

We rebuilt XAC from the wwPDB Chemical Component Dictionary and the deposited 3REY coordinates, qualified the legacy AMSOL and strain-preparation path, generated a canonical DB2 with real strain values (6.180 total, 2.910 maximum), and reran DOCK without relaxing the frozen settings. DOCK saved three poses. All three were near-native, with direct-frame heavy-atom RMSDs of 0.560-0.592 Å.

The conclusion is deliberately narrow: **DOCK has a strong proof of life in this exact A2A control system.** It is now credible as an adversarial-decoy lineage for ProLIF validation. Vina remains the production docking default for the upcoming proof-of-discrimination cycle. A later matched Vina-versus-DOCK benchmark will determine whether DOCK deserves promotion or a larger production role.

## 1. Where DOCK sits in the project

The Stage-5 pipeline separates jobs that are easy to blur together:

- a **pose generator/docker** proposes how a ligand may sit in the pocket;
- an **interaction reader** measures contacts in that pose;
- a **validation panel** determines whether the reader is trustworthy enough to exercise hard attrition;
- an **independent witness** later checks concordance without rewriting the primary result.

The current role allocation is:

| Slot | Current role |
|---|---|
| Vina | Production pose-generation default for the upcoming ProLIF POD cycle |
| ProLIF | Frozen primary interaction reader / measurement instrument |
| DOCK | Qualified independent adversarial-decoy source; future docking candidate |
| PLIP (preferred) | Post-validation independent interaction witness |

This separation is intentional. DOCK is valuable partly because it is independent of the production docking lineage. It can challenge ProLIF with poses produced by a different search/scoring tradition.

## 2. What "proof of life" means here

A proof of life is a small, controlled experiment showing that an implementation can perform the basic scientific task required of it before its failures are interpreted biologically or methodologically.

For DOCK, the relevant question was:

> If given the known A2A receptor and its crystallographic ligand XAC, can our exact DOCK implementation recover the experimentally observed binding geometry under the frozen settings?

This matters for adversarial-negative construction. A displaced DOCK pose is much more informative if the same search also had access to a near-native solution. That is the logic behind the P2 eligibility rule in Session 009.

## 3. The first apparent failure

The original XAC runs were confusing. DOCK generated thousands of matches/orientations but reported no viable poses. The output suggested that the grids might be too small.

That message was not enough to identify the cause. A docking program can fail because of receptor preparation, ligand preparation, search geometry, scoring, file-format assumptions, or internal eligibility gates.

We therefore separated the problem into controls instead of treating "zero poses" as one monolithic failure.

## 4. Receptor-side qualification with compound 313

The repaired 3REY receptor was tested using DOCK's known compound 313 control. It produced 20 saved poses under the repaired grid setup.

This was an important diagnostic fork. It showed that the receptor/grid bundle and DOCK executable were capable of producing viable poses. The XAC failure therefore could not simply be attributed to a globally broken receptor preparation.

The 313 control did not prove that XAC was correct. It told us where to look next: the ligand lineage and DOCK's ligand-set acceptance logic.

## 5. The root cause: invalid strain bookkeeping

Inspection of the handcrafted XAC DB2 revealed the key values:

```text
+9999.990  +9999.990
```

These fields represented total and maximum strain metadata. The frozen INDOCK limits were:

```text
total_strain = 8
max_strain   = 3
```

Source inspection showed that DOCK checks these values when deciding whether a ligand set is acceptable. The placeholder values were therefore not harmless annotations. They guaranteed rejection.

This changed the interpretation of the entire failure:

**Before diagnosis:** "DOCK sampled XAC but could not find a viable physical pose."

**After diagnosis:** "The XAC DB2 was internally marked as catastrophically strained, so DOCK rejected every set before a pose could qualify."

That is why the earlier zero-pose result is no longer evidence against DOCK's search performance.

## 6. Why we abandoned the old ligand lineage

The strain problem was not the only warning sign. Earlier XAC MOL2 attempts also produced chemistry and parsing problems, including valence inconsistencies and failed sanitization/kekulization in some derived files.

Rather than repeatedly patching an uncertain representation, we restarted from an authoritative chemical definition.

The source chosen was the **wwPDB Chemical Component Dictionary (CCD)** entry for XAC, reconciled against the ligand actually deposited in 3REY.

The qualified XAC control is:

- formula: C21H28N6O4;
- formal/system charge: 0;
- 31 heavy atoms;
- 28 hydrogens;
- 59 total atoms;
- 61 bonds.

All 31 CCD heavy-atom names matched the deposited 3REY heavy atoms, and the heavy-atom coordinates agreed exactly at the stored precision: 0.000000 Å RMSD.

### Amended decision: the +1/60-atom branch

During debugging we explored a +1 protonated, 60-atom XAC representation. That was a useful hypothesis but **did not become the qualified proof-of-life lineage**. The successful control used the CCD-neutral 59-atom XAC and AMSOL `CHARGE=0`.

Future work may study alternative protonation states when scientifically justified, but the Session-009 DOCK qualification must not be retrospectively described as a +1/60-atom result.

## 7. Canonical ligand-preparation workflow

The final qualified route was:

1. **wwPDB CCD:** authoritative atom identities, connectivity, bond orders, hydrogens, and 3REY model coordinates.
2. **RDKit reconstruction:** build and sanitize the molecular graph without changing the coordinates.
3. **Lossless SDF:** serialize the validated graph.
4. **Antechamber/SYBYL typing:** assign atom types expected by the historical DOCK ligand toolchain.
5. **AMSOL 7.1:** calculate CM2 charges and water/hexadecane solvation terms.
6. **Torsional strain:** calculate real total and maximum strain instead of placeholder values.
7. **mol2db2_py3_strain:** construct the DOCK DB2 hierarchy.
8. **DB2 audit:** verify counts, strain records, connectivity, and coordinates.
9. **DOCK redocking:** test native recovery against the repaired 3REY receptor.

At the end of this chain, the DB2 still reproduced the input crystallographic geometry at 0.000000 Å all-atom and heavy-atom RMSD.

## 8. Legacy dependency work

### 8.1 Missing `libg2c.so.0`

AMSOL 7.1 is an old binary and depends on the GNU g77 runtime `libg2c.so.0`. That library was not available on gpu-dev1.

We sourced the compatibility runtime from the archived CERN CentOS 7 RPM:

```text
compat-libf2c-34-3.4.6-32.el7.x86_64.rpm
SHA256 1667b0ba674f3c2b5ba2b3603cf49d661e32ce4eda35b6dad37c26b43173fef1
```

The package was **extracted, not installed**. `file`, `readelf`, and `ldd` were used to verify that the extracted library had the expected `libg2c.so.0` SONAME and resolved AMSOL's only missing dynamic dependency. It was exposed locally with `LD_LIBRARY_PATH`.

This preserved the frozen system and environments while making the historical binary reproducible.

### 8.2 Unlicensed OpenEye charge call

The historical AMSOL-input helper imported OpenEye OEChem and used `OENetCharge()` to obtain the ligand net charge. The available OpenEye installation was unlicensed, so the helper created empty AMSOL input files.

Inspection showed that OEChem was not being used to construct the geometry. Its only functional role in that helper was net-charge determination.

For the qualified CCD-neutral XAC, system charge 0 had already been independently established. We therefore made an **isolated compatibility copy** of the helper in which that one call was replaced by `netcharge = 0`. The pinned source checkout was not modified.

This is an XAC-control compatibility decision, not a general license-free replacement for charge-state determination. A future ligand must supply the charge appropriate to the actual species being processed.

## 9. AMSOL qualification

With the legacy runtime and helper compatibility layer in place, AMSOL successfully completed both:

- SM5.42R water calculation;
- SM5.42R hexadecane calculation.

The postprocessor generated `output.mol2` and `output.solv`. The ligand retained all 59 atoms, all 61 bonds, atom names, atom types, and 0.000000 Å coordinate preservation.

The serialized CM2 atomic charges sum to -0.02 e even though the system charge is 0. This is retained as a serialization/precision observation. AMSOL itself reports charge 0, and no manual redistribution of charge was performed.

## 10. Real strain and the repaired DB2

The canonical torsional-strain calculation produced:

```text
total strain = 6.180
max strain   = 2.910
```

The frozen gates remained:

```text
total < 8
max   < 3
```

Both passed. Importantly, we did **not** relax the gate to make XAC pass.

The final DB2 strain record became:

```text
S      1      2  14 0 0      +6.180      +2.910
```

The maximum strain is close to the cutoff. That is useful context for future audits, but it is still a prospective pass under the frozen rule.

## 11. The decisive redocking experiment

The qualified DB2 was docked against the repaired receptor using the unchanged frozen settings. DOCK sampled 4,070 orientations and saved three viable poses.

Direct-frame heavy-atom RMSDs were:

| Rank | Score | Heavy-atom RMSD | Interpretation |
|---:|---:|---:|---|
| 1 | -26.623 | 0.592 Å | Native-like |
| 2 | -26.586 | 0.563 Å | Native-like |
| 3 | -26.553 | 0.560 Å | Native-like |

These RMSDs were calculated **without aligning the predicted pose back onto the crystal pose**. The receptor coordinate frame was already common to both structures. This makes the result a direct test of placement accuracy.

All 3/3 saved poses are far inside the predeclared ≤2 Å near-native boundary. The best is 0.560 Å.

## 12. What we learned

### The original zero-pose result was misleading

The search had not demonstrated a physical inability to recover XAC. Invalid strain metadata had made every ligand set administratively ineligible.

### Controls prevented a wrong conclusion

The 313 receptor control separated receptor failure from ligand failure. Source inspection then connected the DB2 metadata to DOCK's set-acceptance logic.

### File preparation is part of the scientific method

In docking, the input representation is not merely clerical. Protonation, atom typing, partial charges, solvation terms, conformer hierarchy, and strain metadata can determine whether a pose is ever evaluated or accepted.

### Expensive validation can justify a lightweight production reader

The purpose of this DOCK work is not that every future generated molecule must pass through this entire legacy stack. The value is that ProLIF can be challenged using negatives from a docking lineage that has itself been demonstrated to recover the correct state.

## 13. Current architectural decision

### What stays fixed now

For the upcoming ProLIF proof-of-discrimination cycle:

- **Vina stays the production pose generator.**
- **ProLIF stays the frozen primary interaction reader.**
- **DOCK supplies one qualified adversarial-negative lineage.**
- **PLIP remains the preferred post-validation independent witness.**

Changing the production docker now would introduce a new variable in the middle of validation.

### What changed

DOCK has earned stronger credibility than it had at the start of the session. It now has direct system-specific native-redocking evidence in A2A. Vina remains operationally attractive, but it does not yet have an equivalent Stage-5 native-redocking qualification in this exact comparison framework.

That is a **validation asymmetry**, not evidence that DOCK is globally better.

## 14. Future promotion path for DOCK

DOCK should be considered for a larger role only after a matched benchmark on the frozen experimental panel.

The planned Vina-versus-DOCK comparison will use the same:

- receptors;
- experimental ligands;
- crystallographic references.

It will compare:

- best-pose RMSD;
- top-ranked-pose RMSD;
- success rate at ≤2 Å;
- failure rate;
- pose diversity;
- runtime and operational burden;
- downstream ProLIF interaction conclusions.

The central question is not "Which docker wins?" It is:

> **Does the downstream Stage-5 interaction evidence materially depend on the pose generator?**

If both engines lead to concordant ProLIF conclusions, the Stage-5 claim becomes more robust. If they disagree, that disagreement maps a real sensitivity in the pipeline.

### Conditions for promotion

A future decision to promote DOCK to the primary production docking slot should require evidence that its scientific benefit justifies its added preparation and runtime complexity. A single excellent XAC redocking is not sufficient.

Possible future roles include:

1. primary production docker, if a matched benchmark materially favors it;
2. high-cost second-pass confirmation for important or ambiguous molecules;
3. permanent independent robustness/witness docking lane;
4. continued adversarial-decoy source only.

The interface should allow any of these without rewriting downstream evaluation logic.

## 15. Relationship to ProLIF proof-of-discrimination

Session 009 closes the prerequisite, not the final Stage-5 gate validation.

The next experiment asks whether frozen ProLIF can retain experimental positives while rejecting independently eligible, physically plausible adversarial negatives. DOCK now has the proof of life needed to contribute one such negative lineage.

The sequence is:

> **DOCK proof of life → qualify adversarial negatives → freeze panel → blind ProLIF POD → lock D-entry → qualify/run independent witness → later Vina-vs-DOCK robustness benchmark**

Until the ProLIF validation passes, A2A remains Level 1 with claims capped and no Stage-5 hard attrition.

## 16. Limitations

The DOCK qualification rests on one exceptionally controlled system: 3REY/XAC.

The result is strong within that system, but it does not establish performance across other A2A chemotypes, flexible ligands, alternative protonation states, generated molecules, or other targets. It also does not establish that DOCK is superior to Vina.

The correct claim is narrower:

> **The repaired and qualified DOCK implementation can recover the experimental XAC pose in 3REY under the frozen Stage-5 settings, with all three saved poses at 0.560-0.592 Å direct-frame heavy-atom RMSD.**

## 17. Glossary

**A2A (adenosine A2A receptor)** — The protein target used as the first Stage-5 Level-1 validation system.

**Adversarial negative** — A plausible but genuinely alternative pose deliberately used to challenge an interaction reader. It should be difficult enough that rejecting it is meaningful.

**AMSOL** — A legacy program used in the DOCK ligand-preparation lineage to calculate partial charges and solvation-related quantities.

**Antechamber** — A ligand-preparation tool from AmberTools used here to validate chemistry and assign SYBYL-style atom types.

**Atom type** — A label describing an atom's chemical environment, not merely its element. Docking programs use atom types to choose interaction parameters.

**CCD (Chemical Component Dictionary)** — The wwPDB reference definition for small molecules found in PDB structures, including atom names, bonds, bond orders, and formal charge.

**CM2 charge** — Charge Model 2 partial atomic charges produced by AMSOL. Partial charges describe how molecular charge is distributed over atoms.

**DB2** — A hierarchical ligand format used by DOCK. It stores atom information, coordinates/conformations, solvation terms, and strain metadata needed by the search/scoring machinery.

**Direct-frame RMSD** — RMSD calculated when prediction and reference already share the same receptor coordinate frame, without superimposing them afterward. It measures actual placement error.

**DOCK** — The Shoichet/Kuntz docking lineage used here as a qualified adversarial-decoy source and future candidate docking backend.

**Docker / docking engine** — Software that searches possible ligand placements and orientations in a receptor pocket and scores them.

**Frozen setting / frozen gate** — A parameter or decision rule fixed before the validation result is observed. It cannot be relaxed afterward simply to obtain a pass.

**Hard attrition** — Authority to remove/reject a molecule or pose from the evaluation cascade rather than merely describe it.

**Heavy atom** — Any non-hydrogen atom. Heavy-atom RMSD is commonly used to evaluate docking-pose recovery.

**INDOCK** — The DOCK configuration file containing search, scoring, output, and eligibility settings.

**Interaction fingerprint** — A structured representation of ligand-protein contacts such as hydrogen bonds, hydrophobic contacts, ionic interactions, and aromatic interactions.

**libg2c.so.0** — The obsolete GNU g77 Fortran runtime library required by the historical AMSOL 7.1 executable used here.

**MOL2** — A molecular file format that stores atoms, coordinates, bonds, atom types, and partial charges.

**Near-native pose** — In this Stage-5 protocol, a pose with RMSD ≤2.0 Å from the experimental reference.

**P1-P4** — The Stage-5 negative-eligibility doctrine: physical admissibility (P1), genuine alternative with native sampling (P2), independence from one generator's idiosyncrasy (P3), and Graves-style adversarial misranking strengthening (P4).

**PLIP** — Protein-Ligand Interaction Profiler, planned as the preferred independent witness after the primary ProLIF validation result is locked.

**Pose** — A particular three-dimensional placement and conformation of a ligand in a receptor binding site.

**PoseBusters-style plausibility** — An independent set of geometry/chemistry checks used to determine whether a pose is physically admissible before its interaction pattern is considered.

**ProLIF** — The frozen primary interaction reader for Stage 5. It converts a protein-ligand structure into defined interaction calls/fingerprints.

**Proof of discrimination (POD)** — The prospective validation experiment testing whether the frozen ProLIF reader retains all frozen experimental positives and rejects all frozen primary adversarial negatives under the project's predeclared rule.

**Proof of life** — A controlled demonstration that an implementation can perform its basic required task before its failures are interpreted scientifically.

**Protonation state** — The pattern of added/removed protons and resulting formal charge of a molecule. Different protonation states can change docking interactions and must not be silently mixed.

**RMSD (root-mean-square deviation)** — A measure of average coordinate difference between corresponding atoms in two structures. Lower values mean more similar poses.

**Solvation / desolvation** — Energetic effects associated with moving a ligand between solvent-like and binding-pocket environments.

**Strain / torsional strain** — Internal energetic penalty associated with a ligand conformation, especially unfavorable bond rotations. DOCK uses strain metadata as an eligibility/scoring component.

**SYBYL atom type** — A chemical atom-typing convention used by MOL2 and parts of the historical DOCK preparation toolchain.

**Vina** — The current pragmatic production docking default. It is easier to operationalize broadly but has not yet received the same matched Stage-5 native-redocking qualification as DOCK.

**wwPDB** — Worldwide Protein Data Bank, the organization maintaining PDB structural data and the Chemical Component Dictionary.

## 18. Final checkpoint

Session 009 establishes that the DOCK lineage required by the Stage-5 adversarial-negative doctrine is operational and scientifically credible in the exact 3REY/XAC A2A control.

It does **not** authorize ProLIF hard attrition and does **not** promote DOCK over Vina.

The project now moves to a clean ProLIF proof-of-discrimination session with the role allocation frozen prospectively. DOCK promotion remains a future evidence-driven decision.
