# Stage 5 Target–Ligand Interaction Evidence Levels

## Purpose

Stage 5 is the **target–ligand interaction evidence layer** of the evaluation cascade.

Following the documented negative result from the independent docking-validation arm, Stage 5 uses a reference-pose fallback framework. This document defines how targets are assigned interaction-evidence levels, how an implemented target-specific gate earns authority, and what scientific claims are permitted.

Two questions are deliberately separated:

1. **Target evidence:** What target–ligand interaction knowledge exists?
2. **Gate validation:** Has the implemented computational gate demonstrated that it can operationalize that knowledge?

Evidence level is assigned **before generator outcomes are inspected**. Gate-validation criteria are likewise predeclared before validation results are seen.

---

## 1. Scope exclusion

A target with **no available three-dimensional structure is out of scope for Stage 5 entirely**.

Stage 5 requires a structural representation of the target because interaction assessment and predicted-pocket characterization depend on spatial protein geometry.

This exclusion is distinct from Level 3.

A Level 3 target **has a well-defined structure** but lacks sufficient target–ligand interaction evidence. A target without a structure cannot be assigned Level 1, Level 2, or Level 3 for Stage 5.

---

## 2. Canonical evidence-level definitions

Level 1 - sufficient for validated compatibility testing
Level 2 - sufficient for interaction characterization
Level 3 - insufficient for target-compatibility assessment

These definitions are **permissions statements about scientific claims**. They are canonical and do not change.

The criteria below determine whether the available target–ligand evidence is sufficient to earn each permission level. Gate validation is a separate requirement applied above these levels.

---

## 3. Sufficiency criteria

### Level 1

Level 1 requires an **experimental target–ligand complex containing a cognate ligand**.

The experimental complex provides direct structural evidence of how a ligand interacts with the target binding site.

Level 1 therefore provides sufficient target evidence to develop and attempt validation of a target-specific compatibility definition.

Where multiple experimental complexes or chemotypes are available, they should be used to distinguish recurring target-recognition features from interactions specific to a single ligand.

Level 1 evidence alone does **not** authorize hard attrition. The implemented compatibility gate must independently earn that authority under the gate-validation requirements below.

### Level 2

Level 2 applies when direct cognate target–ligand structural evidence is unavailable, but interaction characterization can be supported by either:

* an experimental apo structure of the target with sufficient binding-site information; or
* an experimental ligand-bound complex from a homologous protein.

Homolog evidence is admissible only when the **binding site itself is demonstrably conserved**.

The target record must document:

* pocket sequence identity; and
* pocket structural superposition RMSD.

Overall fold homology alone is insufficient.

A homolog with a similar global structure but materially different pocket residues does **not** establish Level 2 interaction evidence.

All Level 2 outputs are explicitly labeled **homology-inferred** when homolog evidence is used.

Level 2 supports interaction characterization only and never validated compatibility.

### Level 3

Level 3 requires a **well-defined target structure** but no recorded target–ligand interaction evidence sufficient for Level 1 or Level 2 anywhere in the relevant protein family.

The Level 3 verdict is strictly an **evidence-absence statement**.

It does not mean:

* the target does not exist;
* the binding pocket does not exist;
* the target is biologically unimportant;
* the target is undruggable; or
* generated molecules cannot bind the target.

It means only that the available evidence cannot support a defensible target-specific interaction assessment.

---

## 4. Gate-validation layer

The gate-validation requirement is applied **above the evidence levels**.

Target evidence and tool validity are separate questions. A hard target-compatibility claim requires both sufficient evidence **and** a validated implementation.

Conceptually:

```text
Target–ligand evidence
        +
Implemented gate validity
        ↓
Permitted claim
```

A strong evidence level cannot compensate for an inadequately validated gate, and successful software execution cannot compensate for insufficient target–ligand evidence.

### Predeclaration

The validation criterion must be written down **before validation results are inspected**.

The criterion must specify what constitutes successful recovery of known-positive behavior and what constitutes successful discrimination of plausible-but-wrong poses.

The criterion must not be retroactively modified to accommodate observed validation outcomes.

### Validation is implementation-specific and target-specific

Gate validation applies **per implementation and per target**.

A gate validated on one target earns no hard-claim authority on another target.

Each target-specific hard gate must earn its authority using that target's own:

* cognate positive controls; and
* plausible-but-wrong negative pose controls.

Likewise, materially changing the implemented interaction logic requires reassessment of the relevant validation evidence.

### Sensitivity versus discrimination

Successful recovery of known positive complexes demonstrates **sensitivity only**.

Positive recovery establishes that the implemented reader can detect the intended interaction pattern when that pattern is known to be present.

Hard attrition requires more.

Because attrition is a **rejection act**, the implemented gate must additionally establish discrimination using plausible-but-wrong negative poses.

Negative controls are **pose conditions, not molecule conditions**.

A useful negative therefore preserves sufficient physical plausibility while disrupting the target-recognition condition the gate is intended to detect.

A synthetic negative that becomes physically implausible does not test Stage 5 discrimination. It tests a condition that should already be detectable by the geometry-focused stages of the cascade.

Gate-validation outcomes are recorded as:

* **established**; or
* **not established**.

They are never recorded as a failed target, failed evidence level, or failed molecule.

### Claims cap pending validation

If the implemented gate has not fully validated, the target **retains its assigned evidence level**.

The evidence level is not demoted because the computational implementation has not earned hard-gate authority.

Instead, the target record states:

> **claims capped pending gate validation**

Under the cap, Stage 5 may produce characterization appropriate to the target's evidence level, but hard compatibility claims and attrition are not permitted.

If the gate subsequently validates, the cap is lifted.

Previously archived characterization readouts may then be **re-scored attritionally under the newly validated gate without regenerating molecules**, provided the underlying generator-provided poses and required provenance were preserved.

### Language under a capped gate

Results generated under a claims-capped gate must be phrased as **pattern reproduction**, not as Stage 5 PASS/FAIL outcomes.

For example:

> **Reproduced the predeclared reference-recognition pattern.**

or:

> **Did not reproduce the predeclared reference-recognition pattern.**

These statements are explicitly conditional on the **generator-provided pose**.

They do not constitute independent confirmation that the supplied pose is the experimentally preferred or physically correct binding mode.

---

## 5. Level 3 procedure

Level 3 produces two parallel outputs: a **VERDICT arm** and a **LANE arm**.

### VERDICT arm

The target record receives an explicit **interaction-evidence gap**.

Stage 5 target compatibility is reported as **INCONCLUSIVE**.

No target-specific feasibility claim may be produced.

Absence of evidence must not be converted into either compatibility or incompatibility.

### LANE arm

Generated molecules are **not failed because their target is Level 3**.

They continue through every evaluation stage whose claims do not require target–ligand interaction evidence.

The sole target-side analysis permitted within the Level 3 lane is **predicted-pocket characterization**, using an established pocket-prediction method such as P2Rank or fpocket.

Any nominated binding site derived in this manner must be labeled:

> **Predicted pocket**

and never presented as an experimentally observed target–ligand binding site.

A predicted pocket does not upgrade the target's evidence level and does not establish a target-specific interaction model.

---

## 6. Provenance and reporting rules

Every molecule evaluated against a Level 3 target carries an **interaction-unverified** flag through every downstream stage and aggregate claim.

The flag cannot be removed because the molecule performs well on target-independent evaluations.

Level 3 molecule counts are reported **separately from headline pipeline survival rates** so unresolved target compatibility is not obscured by success on chemistry, drug-likeness, physical plausibility, or other downstream measurements.

Any target-specific downstream claim requiring interaction evidence is blocked while the target remains Level 3. This includes claims concerning:

* selectivity;
* off-target risk; and
* efficacy proxies dependent on target engagement.

Level 2 outputs are always labeled according to their evidentiary basis.

When homolog evidence is used, outputs must be labeled:

> **homology-inferred**

Level 2 supports interaction characterization only and **never validated compatibility**.

Every evidence-level assignment must remain traceable to the evidence used to make it. The target record should identify, where applicable:

* experimental structures;
* cognate ligand identities;
* relevant PDB depositions;
* ligand activity evidence;
* homolog structures;
* pocket sequence comparisons;
* pocket structural superpositions; and
* the date of the evidence pull.

Gate-validation provenance must separately identify:

* the implemented gate version;
* the target;
* the predeclared validation criterion;
* cognate positive controls;
* plausible-but-wrong negative controls;
* validation outcome; and
* whether hard-claim authority is established.

---

## 7. Level reassignment

Evidence levels are re-evaluated during **each session's evidence pull**.

New evidence that may trigger reassessment includes:

* a new PDB deposition;
* a new ChEMBL activity record;
* a newly identified cognate ligand;
* a newly available homolog complex; or
* other qualifying experimental target–ligand evidence.

Targets upgrade when new evidence satisfies the criteria for a higher level.

For example:

**Level 3 → Level 2** may occur when a qualifying conserved homolog complex becomes available.

**Level 2 → Level 1** may occur when an experimental cognate target–ligand complex becomes available.

Evidence levels must **never downgrade silently**.

Any downgrade requires a documented reason identifying the evidence or methodological assumption that was withdrawn, invalidated, reinterpreted, or found insufficient.

Evidence-level reassignment and gate validation remain separate processes. New evidence may change the target's level without automatically validating an implementation, while successful gate validation may lift a claims cap without changing the target's evidence level.

---

## 8. Claims separation with Stage 3

Stage 3 and Stage 5 make fundamentally different claims.

Stage 3 evaluates **physical and geometric plausibility**.

Stage 5 evaluates **target–ligand interaction evidence**.

For a Level 3 target, the LANE arm may provide predicted-pocket coordinates to Stage 3B as the pocket artifact.

Stage 3B may then ask whether a generator-provided ligand pose is physically compatible with that predicted pocket.

A Stage 3B PASS remains strictly **geometry-only evidence**.

It does not establish:

* productive target recognition;
* binding affinity;
* target engagement;
* selectivity; or
* biological efficacy.

Interaction-adjacent claims are written only through the Level 3 LANE arm with the **interaction-unverified** flag attached.

The evidence gap established by the VERDICT arm therefore remains visible even when a molecule successfully progresses through target-independent portions of the evaluation cascade.

Likewise, physical plausibility cannot substitute for a plausible-but-wrong Stage 5 negative control. A pose that fails Stage 3B does not establish Stage 5 discrimination.

---

## Governing principle

**The verdict keeps the science honest, the lane keeps the pipeline fair.**
