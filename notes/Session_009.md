# Session 009 — Generalized Stage-5 ruling framework

**Date:** 2026-08-21  
**Status:** CLOSED — DOCK PROOF-OF-LIFE COMPLETE; PROLIF POD NEXT

## Session objective

Implement the generalized Stage-5 ruling framework established by D008.

The framework will separate:

- target–ligand interaction evidence level;
- target-specific gate-validation status;
- permitted Stage-5 claims;
- attrition authority;
- claims-cap and provenance flags.

The framework is target-independent and generator-independent.

A2A will serve as the first Level-1, claims-capped implementation test.

## Starting state

Session 8 completed the A2A Stage-5 characterization baseline.

A2A target–ligand evidence is Level 1.

The A2A interaction reader has established positive sensitivity, including an independent 3RFM/caffeine proof of life.

Plausible-negative discrimination is not established.

Therefore A2A remains:

**LEVEL 1 — CLAIMS CAPPED PENDING GATE VALIDATION**

The current DiffSBDD Stage-5 result is characterization only:

**3/16 generator-provided poses reproduced the predeclared A2A reference-recognition pattern.**

No Stage-5 attrition was applied.

## Stage 5 — Target-Specific Interaction Gate Validation Protocol

### Purpose and scope

This protocol governs validation of the **target-specific interaction gate** before that gate may exercise hard attrition within the Level 1 molecular arm. It does not modify the existing **Level 1–3 verdict definitions**, the **verdict/lane fork**, or the evidentiary roles assigned elsewhere in the cascade.

The frozen interaction reader is **ProLIF**, cited as Bouysset & Fiorucci, *Journal of Cheminformatics* (2021). The fingerprint definition is treated as the measurement instrument. Accordingly, the ProLIF version and all interaction parameters are frozen before validation and may not be tuned, swapped, or modified in response to panel performance.

Until this protocol is passed, interaction-pattern evidence is **characterization-only**. It may inform the appropriate lane but may not exercise hard attrition or rescue a target verdict. Claims remain capped pending validation or revision.

---

## 1. Validation principle

Hard-gate validation tests whether the frozen reader can distinguish:

1. **experimental positives** representing experimentally supported target-recognition states; from
2. **independently eligible, physically plausible adversarial negatives** representing genuinely alternative poses.

Negative-set membership must be established independently of ProLIF.

**No ProLIF output, fingerprint, interaction count, similarity value, or failure to reproduce a reference interaction may be used to select, exclude, promote, or otherwise determine membership in the negative panel.**

The methodological foundation is the Shoichet/Kuntz DOCK lineage, particularly the geometric-decoy framework of Graves, Brenk & Shoichet (2005): informative decoys are reasonable but incorrect alternatives for which native-like sampling has been demonstrated, rather than artificial structures made wrong by destroying physical plausibility.

---

## 2. Negative eligibility doctrine

A candidate becomes an **eligible negative** only when **P1–P3** are satisfied.

### P1 — Physically admissible

The candidate must pass an independent, pinned **PoseBusters-style physical-plausibility suite**.

The freeze record must identify:

* plausibility-suite implementation;
* exact version;
* checks applied;
* any prespecified handling of warnings, failures, or non-applicable tests.

Physical plausibility is determined independently of ProLIF and independently of the generator's score.

**A favorable docking or generator score never counts as evidence for P1.**

A pose that becomes interaction-negative only after physical plausibility fails is not an informative negative and is ineligible for the primary panel.

### P2 — Genuine alternative with demonstrated native sampling

Pose status is determined relative to the applicable experimental reference using the RMSD definitions frozen below.

For every candidate negative, the record must contain:

**(a)** evidence that the **same generator search** also sampled at least one near-native solution; and
**(b)** the candidate's rank/score under that generator relative to the sampled near-native solution.

This distinguishes a genuine alternative from a search that simply failed to find the reference-like state.

The candidate must satisfy the **genuinely alternative** RMSD definition. A search that produces an alternative pose but never samples a near-native solution does not establish P2 for primary-panel purposes.

### P3 — Negative status not attributable to the generating model

The candidate's status as an informative alternative must not depend solely on an idiosyncrasy of the model that generated it.

Evidence supporting P3 must be established independently of ProLIF and documented before panel freeze. Generator provenance is retained so that model-family dependence can be examined explicitly.

The negative panel must contain candidates from **at least two unrelated generation families**, including one from the **DOCK lineage**.

No single generation family may define the negative challenge by itself.

### P4 — Graves adversarial strengthening

P4 is a strengthening criterion, not a minimum eligibility requirement.

A P1–P3 negative receives the **P4 flag** when the generating method ranks/scores the genuinely alternative pose **at or above the sampled near-native pose** under its own scoring procedure.

Thus:

> **P1–P3 = eligible negative.**
> **P1–P4 = preferred adversarial negative.**

The **primary validation panel preferentially consists of P1–P4 negatives**. Eligible P1–P3 candidates that do not satisfy P4 may supplement the panel or enter the characterization lane as specified at freeze time.

P4 does not establish physical plausibility and cannot substitute for P1.

---

## 3. Frozen RMSD definitions

The following definitions are predeclared in the panel freeze document and may not be changed after reader results are observed:

**Near-native:** RMSD **≤ 2.0 Å** from the applicable experimental reference.

This follows the conventional docking-success definition used in pose-prediction benchmarking.

**Genuinely alternative:** RMSD **≥ 3.0 Å** from the applicable experimental reference, following the geometric-decoy treatment of Graves et al. (2005).

**Intermediate zone:** RMSD **> 2.0 Å and < 3.0 Å**.

Intermediate poses are **ineligible for the primary validation panel**. They may be retained in a separate characterization lane, but their ProLIF behavior cannot contribute to the hard-attrition authorization decision.

The two cutoffs deliberately create a buffer between demonstrated near-native and genuinely alternative states.

---

## 4. Positive panel

Experimental positives consist of experimentally determined A2A complexes representing the target-recognition state the gate is intended to preserve.

The panel is expanded across **chemotypes** rather than by generating multiple trivial variants of a single complex.

For every positive, provenance and experimental structure identity are recorded before freeze.

Experimental positives are not required to reproduce one geometrically identical global pose or one identical whole-fingerprint representation across chemotypes. They are evaluated according to the **predeclared target-specific recognition definition** encoded by the frozen ProLIF instrument.

The positive panel is frozen before the blind reader run.

---

## 5. Negative-panel composition and provenance

The primary negative panel must contain eligible negatives generated from **at least two unrelated generation families**.

One family must belong to the **Shoichet/Kuntz DOCK lineage**.

For every candidate, the freeze record contains at minimum:

* candidate identifier;
* parent ligand/complex;
* generation family and implementation;
* generator/search settings necessary for provenance;
* RMSD to experimental reference;
* P1 result and plausibility-instrument record;
* evidence of a near-native solution from the same search;
* near-native RMSD;
* candidate generator score/rank;
* near-native generator score/rank;
* P2 determination;
* P3 determination and supporting evidence;
* P4 flag;
* final panel assignment.

At freeze time, report the number and proportion of primary-panel negatives contributed by each generation family.

Family identity remains attached to each candidate after blinding so that post-run results can be stratified by generation family without changing membership or the decision rule.

---

## 6. Panel freeze

Before any validation reader run, create a dated **panel freeze record** containing:

### Instrument freeze

* pinned ProLIF version;
* exact interaction-parameter table;
* target-specific recognition rule derived from that frozen definition.

The parameter table is part of the instrument specification. Changing it constitutes changing the instrument and therefore invalidates the existing validation run.

### Plausibility freeze

* pinned PoseBusters-style suite and version;
* exact prespecified plausibility criteria.

### Panel freeze

* all experimental positives;
* all primary negatives;
* characterization-only controls;
* P1–P4 status;
* RMSD classification;
* generation-family provenance;
* panel family distribution.

### Decision-rule freeze

The hard-attrition decision rule below is written into the freeze document before ProLIF sees the panel.

---

## 7. Predeclared hard-attrition decision rule

For this frozen panel:

> **Hard attrition is authorized if and only if frozen ProLIF rejects 100% of the frozen primary-panel negatives and retains 100% of the frozen experimental positives.**

Therefore:

**PASS:**
all experimental positives retained **AND** all primary-panel negatives rejected.

**FAIL:**
one or more experimental positives rejected **OR** one or more primary-panel negatives retained.

There is no post hoc tolerance threshold.

Any retained primary-panel negative or any rejected experimental positive keeps the interaction gate at **characterization-only authority pending revision**.

A failed validation is recorded as a **D-entry**. The failure may be investigated, but panel membership, interaction parameters, RMSD boundaries, or eligibility rules may not be retrospectively changed to convert that run into a pass.

Any subsequent revised instrument or revised validation design constitutes a new prospective validation cycle and receives its own freeze record and D-entry.

The 100%/100% criterion is **our preregistered decision rule for this panel**. It must never be described as a literature-standard sensitivity or specificity threshold.

---

## 8. Reporting

After the blind run, report exact counts rather than percentages alone:

* positives retained / positives tested;
* positives rejected / positives tested;
* primary negatives rejected / primary negatives tested;
* primary negatives retained / primary negatives tested.

Report corresponding observed sensitivity/retention and discrimination proportions with **Wilson confidence intervals**.

Results are additionally stratified descriptively by:

* chemotype/positive family;
* negative generation family;
* P4 status;
* other prespecified control classes.

Confidence intervals characterize uncertainty in the observed panel performance. They **do not replace or modify the preregistered 100%/100% authorization rule**.

---

## 9. Blind reader sequence and D-entry

After panel freeze:

**Step 1 — Frozen ProLIF run.**
ProLIF receives the blind frozen panel and is run without tuning or parameter modification.

**Step 2 — Result lock.**
All ProLIF results, exact counts, confidence intervals, panel-stratified results, and the PASS/FAIL determination are locked and recorded as the next **D-entry**.

**Step 3 — No retrospective repair.**
Nothing learned from the ProLIF run may alter membership in the panel used to judge that run.

Only after the ProLIF D-entry is locked may instrument concordance begin.

---

## 10. Independent witness

Instrument concordance is explicitly **post-validation** and separate from gate authorization.

The first-choice witness is **PLIP**, run in an isolated environment. PLIP does not need to become part of the production pipeline environment.

Before its opinion on the validation panel counts, the witness must first be **qualified independently** by demonstrating that, on its own interaction definitions, it reproduces the known A2A contacts in the experimental qualification complexes.

The sequence is therefore:

> **qualification → witness opinion**

never:

> **opinion → retrospective qualification**

Once qualified, the witness runs the **identical frozen panel** previously read by ProLIF.

Agreement and disagreement are reported as instrument-concordance evidence.

The witness has **no authority to demote, relabel, remove, or replace a panel member**, and witness disagreement cannot retrospectively alter the locked ProLIF validation result.

If PLIP cannot be qualified or deployed reliably because of its environment, the prespecified fallback witness is:

1. **ODDT fingerprint module**, or
2. a **minimal RDKit contact scorer**.

Any fallback is subject to the same qualification-before-opinion rule.

---

## 11. Lineage allocation and independence doctrine

Roles remain deliberately separated:

**ProLIF — instrument**
Measures the target-specific interaction pattern and is the only reader whose prospective validation determines whether the proposed gate earns hard-attrition authority.

**PLIP / qualified equivalent — independent witness**
Assesses post-validation concordance after ProLIF results are locked.

**DOCK lineage — adversarial-decoy source**
Supplies one independent lineage of challenging pose alternatives grounded in the Shoichet/Kuntz decoy methodology.

**DOCK footprint-similarity scoring — optional historical third perspective**
May be reported for methodological depth but does **not** define the gate, determine P1–P3 eligibility, or determine panel membership.

These roles must not collapse into one another.

---

## 12. Verdict/lane integration

This validation protocol does not alter the existing **Level 1–3 verdict definitions** or the **verdict/lane fork**.

Before successful validation, ProLIF interaction-pattern results belong to the **characterization/evidence lane** and cannot exercise Level-1 hard attrition.

Following a PASS under the prospective rule, the frozen interaction gate may exercise the hard-attrition authority assigned to it within the Level-1 molecular arm, subject to the scope of the validated target, instrument definition, and control domain.

A validation failure leaves that authority disabled.

At Level 3, the existing separation remains intact:

* **P2Rank/fpocket pocket characterization** remains target-side evidence under the **verdict arm**.
* **SEA-style or equivalent ligand-based target hints** belong to the **lane arm** for generated molecules.

Ligand-based target hints remain **claims-capped** and cannot rescue or override the target's verdict.

---

## 13. Claims discipline

### Before validation or after FAIL

Permitted claims are limited to characterization, for example:

> “The frozen ProLIF reader reproduces the specified recognition pattern in the tested experimental complexes.”

> “Interaction-pattern behavior is reported as characterization evidence.”

Not permitted:

> “Failure of the interaction pattern establishes an invalid pose.”

> “The interaction gate discriminates valid from invalid poses.”

> “ProLIF rejection authorizes molecular attrition.”

Claims remain **capped pending revision**.

### After PASS

Within the frozen validation domain, it becomes permissible to state:

> “The frozen target-specific interaction gate retained all experimental positives and rejected all independently eligible primary-panel adversarial negatives under the preregistered Stage 5 validation rule.”

And:

> “The gate therefore earned hard-attrition authority within the prespecified Level-1 scope.”

Exact counts and Wilson confidence intervals accompany the claim.

The 100%/100% decision rule is identified explicitly as the project's **prospectively declared authorization criterion for the frozen panel**, not as a universal or literature-derived performance standard.

---

## 14. Locked Stage 5 doctrine

The governing doctrine is:

> **A negative becomes eligible when P1–P3 hold. A negative is especially strong when P4 also holds. The primary validation panel preferentially uses P1–P4 negatives. No ProLIF result is allowed to determine negative-set membership.**

Physical plausibility and interaction correctness remain separate questions.

A generator score never establishes physical plausibility.

A genuinely alternative pose must be evaluated in a search context in which a near-native solution was also sampled.

The Graves misranking condition identifies especially informative adversarial negatives but does not replace independent eligibility.

Multiple unrelated generation families prevent the validation challenge from collapsing onto one generator's error distribution.

The panel, reader, plausibility instrument, RMSD definitions, and decision rule are all frozen **before the blind ProLIF run**.

The resulting PASS or FAIL is immutable for that validation cycle and is recorded as a **D-entry**.

### Methodological foundation

Primary lineage:

* Kuntz and colleagues, original DOCK geometric-matching lineage.
* Meng, Shoichet & Kuntz, DOCK 3.0/grid-based energy evaluation.
* Graves, Brenk & Shoichet (2005), *Decoys for Docking* — geometric decoys, demonstrated near-native sampling, misranking/scoring failures, cross-scoring, and experimentally tested hit-list false positives.
* Huang, Shoichet & Irwin (2006), DUD — property-matched, topologically distinct decoy design. **This is cited once; PMC3383317 and PMID 17154509 refer to the same DUD paper and are not treated as independent evidence.**
* Mysinger et al. (2012), DUD-E — expanded property-matched decoy framework and chemotype diversity.
* Later Shoichet/Irwin decoy-artifact work — benchmark-distribution dependence and the danger of optimizing against a single decoy population.

Interaction instrument:

* Bouysset & Fiorucci (2021), ProLIF, *Journal of Cheminformatics*.

These sources establish the methodological lineage and precedent. The project's **100% positive-retention / 100% primary-negative-rejection authorization rule is a prospective project decision**, not a threshold attributed to those publications.


## Planned work

1. Implement the target-independent Stage-5 ruling layer.
2. Validate internally coherent evidence records.
3. Map evidence level and gate-validation status to permitted claims.
4. Represent Level-3 VERDICT and LANE behavior.
5. Test the framework using A2A as the first Level-1 claims-capped case.
6. Freeze Stage 5 once the generalized framework is validated.
7. Write the Stage-5 completion checkpoint.

---

## Session 009 close-out — DOCK implementation qualification

**Close-out date:** 2026-08-27

### Why the DOCK detour was required

The Stage-5 doctrine above requires one negative-generation family from the **Shoichet/Kuntz DOCK lineage** and requires demonstrated near-native sampling before a DOCK-generated alternative can satisfy P2. Session 009 therefore could not proceed directly from the literature doctrine to adversarial-negative construction. The DOCK implementation first needed a system-specific proof of life on the exact A2A control system.

The qualification target was **3REY/XAC**. The purpose was not to promote DOCK to the production docking slot. The purpose was to establish that the DOCK lineage used to challenge ProLIF is itself capable of recovering the known experimental state when the receptor and ligand are prepared correctly.

### Failure diagnosis

The initial XAC search sampled thousands of orientations but returned no viable poses. This initially resembled a search, grid, or physical-placement failure.

The repaired 3REY receptor was independently challenged with the canonical DOCK compound **313**. That control produced viable poses and therefore showed that the receptor grids, search machinery, and DOCK executable were operational.

Source-level inspection then identified the decisive ligand-side failure. The handcrafted XAC DB2 contained placeholder strain metadata:

```text
+9999.990  +9999.990
```

The frozen INDOCK limits were:

```text
total_strain = 8
max_strain   = 3
```

DOCK evaluates these fields when determining whether a ligand set is viable. The placeholder values therefore caused deterministic rejection of every set as above strain. The apparent zero-pose result was **not evidence that DOCK could not geometrically recover XAC**. It was an invalid ligand-preparation record tripping the frozen gate before a pose could qualify.

### Canonical XAC rebuild

The earlier MOL2 lineage was abandoned rather than incrementally repaired.

The successful reconstruction used the **wwPDB Chemical Component Dictionary (CCD) XAC definition** reconciled against the deposited 3REY ligand coordinates. The qualified species was the CCD-neutral XAC form:

```text
C21H28N6O4
formal charge = 0
31 heavy atoms + 28 hydrogens = 59 atoms
61 bonds
```

The 31 CCD heavy-atom names matched the 31 deposited 3REY heavy atoms exactly, and their coordinates agreed at **0.000000 Å heavy-atom RMSD**.

The qualified ligand lineage was:

> **wwPDB CCD → RDKit reconstruction → lossless SDF → Antechamber/SYBYL typing → AMSOL → canonical torsional strain → mol2db2_py3_strain → DB2 audit → DOCK**

The final DB2 retained all 59 atoms and 61 bonds and preserved the complete crystallographic geometry at **0.000000 Å all-atom and heavy-atom RMSD**.

### Legacy dependency qualification

The historical AMSOL 7.1 executable required the obsolete GNU g77 runtime `libg2c.so.0`. The compatible runtime was sourced from the archived CERN CentOS 7 package:

```text
compat-libf2c-34-3.4.6-32.el7.x86_64.rpm
SHA256 1667b0ba674f3c2b5ba2b3603cf49d661e32ce4eda35b6dad37c26b43173fef1
```

The RPM was extracted without system installation. The library was exposed only through an isolated `LD_LIBRARY_PATH` on gpu-dev1. The frozen environments and pinned DOCK/ZINC checkout were not modified.

The historical `make_amsol71_input.py3.py` helper also made an OpenEye `OENetCharge()` call. The available OpenEye installation was unlicensed. Inspection showed that this was the helper's only functional use of OEChem. An isolated compatibility copy replaced that call with the independently established XAC system charge, **0**, while leaving the pinned source unchanged.

AMSOL then completed both water and hexadecane SM5.42R calculations. The postprocessed structure retained the complete crystal geometry and connectivity. The serialized CM2 atomic charges sum to -0.02 e because of finite output precision; AMSOL itself reports system charge 0. No manual charge renormalization was applied.

### Real torsional strain and DB2 qualification

The canonical strain path produced:

```text
total strain = 6.180
max strain   = 2.910
```

Both values pass the frozen limits without changing the gate:

```text
6.180 < 8    PASS
2.910 < 3    PASS
```

The qualified DB2 therefore contains real strain metadata rather than the placeholder `+9999.990` values. The maximum strain is close to the frozen cutoff and is retained as an audit observation; the threshold was not relaxed.

### DOCK proof-of-life result

The qualified XAC DB2 was docked against the repaired 3REY receptor under the frozen search and strain settings.

DOCK sampled **4,070 orientations** and saved **3 viable poses**. Direct crystallographic-frame heavy-atom RMSDs, without post-hoc superposition, were:

| Rank | DOCK score | Heavy-atom RMSD |
|---:|---:|---:|
| 1 | -26.623 | 0.592 Å |
| 2 | -26.586 | 0.563 Å |
| 3 | -26.553 | **0.560 Å** |

All **3/3 saved poses were native-like** under the predeclared ≤2.0 Å near-native definition. The entire saved ensemble occupied the experimental binding basin.

This closes the original implementation failure. The earlier zero-pose result was caused by invalid ligand-preparation metadata, not by an inability of DOCK to recover XAC.

### Architectural ruling

The role allocation established earlier in Session 009 remains in force:

**ProLIF — frozen interaction instrument.**

**PLIP / qualified equivalent — post-validation independent witness.**

**DOCK lineage — qualified adversarial-decoy source.**

**Vina — pragmatic production pose-generation default for the upcoming ProLIF proof-of-discrimination cycle.**

The DOCK result exposes a validation asymmetry: DOCK now has a direct native-redocking qualification in this exact A2A system, whereas Vina has not yet received an equivalent matched qualification in Stage 5. This does not justify replacing Vina during the current validation cycle. It motivates a later matched robustness benchmark.

The architecture remains implementation-agnostic. Reader, generator, docker, and fingerprinter slots are treated as swappable interfaces. One qualified default occupies each production slot, while alternative implementations may be promoted only after an explicit proof-of-life and comparative validation exercise.

### Amended decisions from Session 009

1. **Superseded XAC protonation/rebuild branch.** Earlier debugging considered a +1, 60-atom XAC docking protomer. That branch did not become the qualified lineage. The successful proof-of-life used the wwPDB CCD-neutral **59-atom XAC** with system charge 0. Future documentation must distinguish the superseded branch from the qualified control.
2. **Zero poses reinterpreted.** The original XAC zero-pose result is no longer treated as evidence against DOCK search performance. It is classified as a ligand-preparation/DB2 bookkeeping failure.
3. **DOCK role strengthened, not promoted.** DOCK is now qualified for its Stage-5 adversarial-decoy role. It is not yet the primary production docker.
4. **Vina remains production default prospectively.** Its production role is retained for the ProLIF POD cycle to avoid changing the architecture mid-validation. Comparative scientific claims between Vina and DOCK are deferred.
5. **Future promotion requires evidence.** A docking implementation may be promoted to the primary slot only after a matched proof-of-life/robustness exercise on the frozen experimental panel, not because of convenience, reputation, or one successful case.

## Session 009 final status

Session 009 is **CLOSED**.

The generalized Stage-5 validation doctrine is defined, the DOCK lineage required by that doctrine has passed a system-specific 3REY/XAC proof of life, and the project is ready to begin the **ProLIF proof-of-discrimination (POD)** cycle from a clean session.

A2A remains:

**LEVEL 1 — CLAIMS CAPPED PENDING GATE VALIDATION**

No Stage-5 hard attrition is authorized yet.

## Next-session roadmap

1. Freeze the experimental A2A positive panel and the ProLIF instrument specification.
2. Construct and qualify adversarial negatives under P1-P4, including the now-qualified DOCK lineage and at least one unrelated generation family.
3. Freeze panel membership and the 100%/100% prospective authorization rule before ProLIF sees the panel.
4. Run the blind frozen ProLIF proof-of-discrimination experiment and lock the result as the next D-entry.
5. Only after the ProLIF result is locked, qualify and run PLIP or the prespecified fallback witness.
6. After the primary POD cycle, perform the planned **Vina-versus-DOCK robustness benchmark** on the same experimental receptors, ligands, and crystallographic references. Compare best-pose RMSD, top-ranked RMSD, ≤2 Å success rate, failure rate, pose diversity, runtime, and downstream ProLIF interaction evidence.

The purpose of the Vina-versus-DOCK benchmark is not to declare a universal winner. It is to determine whether the Stage-5 interaction conclusion is sensitive to the pose generator and whether DOCK has earned consideration for future promotion to the primary docking slot.
