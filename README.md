# SBDD Drug Discovery Pipeline

An experimental, generator-agnostic pipeline for evaluating structure-based de novo molecular generation through progressively more development-relevant constraints.

## Project Goal

The long-term goal is an **end-to-end in silico drug discovery pipeline** that connects structure-based molecular generation to progressively deeper computational triage before any proposed wet-lab validation.

The central question is not simply whether a generative model produces chemically valid molecules, but:

> **Do generated molecules survive progressively more development-relevant constraints?**

## Architecture

```text
SBDD Generation
      ↓
Chemical Validity
      ↓
Drug-Likeness / Property Feasibility
      ↓
3D / Structural Plausibility
      ↓
Novelty / Chemical-Space Characterization
      ↓
Target Compatibility
      ↓
Synthetic Feasibility
      ↓
ADME / Disposition Characterization
      ↓
Safety-Risk Characterization
including DILI
      ↓
Virtual-Cell Simulation
      ↓
Final In Silico Validation Gate
      ↓
Potential Wet-Lab Validation
```

Generation and evaluation are intentionally separated.

Generators produce standardized molecular files such as SDFs. Downstream evaluation stages consume those files rather than model internals.

This allows different generators to be evaluated through the identical cascade.

## Generator Plan

### Phase 1 — DiffSBDD

Reproduce DiffSBDD using its released pretrained checkpoint and establish the complete baseline by carrying the surviving DiffSBDD cohort through the full evaluation cascade.

Each evaluation stage is developed, validated where required, and frozen before the baseline advances to the next stage.

### Phase 2 — FLOWR

After the complete DiffSBDD baseline cascade has been implemented and frozen, add FLOWR through the same generator interface and evaluate it through the identical frozen cascade.

The comparison will focus on **attrition and characterization across development-relevant stages**, rather than generator-native validity metrics alone.

Downstream evaluation methods must not be recalibrated using FLOWR outcomes.

## Current Baseline

DiffSBDD checkpoint inference has been successfully reproduced.

Initial test:

- Target: 3RFM / human A2A receptor
- Generated molecules: 20

---

## Stage 1 — Chemical Validity

Implemented in:

`evaluation/validity.py`

Initial DiffSBDD result:

```text
20 generated
    ↓
20 RDKit parsed
    ↓
19 RDKit sanitized
    ↓
95% Stage 1 survival
```

One molecule failed sanitization because of an explicit carbon valence of 5.

The evaluator also successfully handles deliberately malformed SDF records without silently dropping them.

---

## Stage 2 — Molecular Property Profiling and Rule-of-Five Classification

Implemented in:

`evaluation/properties.py`

Stage 2 consumes the machine-readable Stage 1 validity results and evaluates only molecules that passed chemical validity while preserving their original molecule IDs.

For each surviving molecule, it calculates:

- molecular weight
- cLogP
- TPSA
- hydrogen-bond donors
- hydrogen-bond acceptors
- rotatable bonds
- QED
- heavy atom count
- formal charge

Rule-of-Five criteria are also recorded individually, together with the total number of violations and a strict zero-violation classification.

Initial DiffSBDD result:

```text
19 Stage-1-valid molecules
    ↓
18 zero Rule-of-Five violations
 1 Rule-of-Five flagged
    ↓
94.74% Stage 2 zero-violation rate
```

The strict cascade therefore carries 18 molecules into Stage 3.

---

## Stage 3 — 3D / Structural Plausibility

Implemented in:

`evaluation/structure.py`

using PoseBusters `0.6.5`.

Stage 3 evaluates the generator's **original 3D coordinates** rather than regenerated conformers.

The evaluation is separated into:

- **Stage 3A — ligand-intrinsic structural plausibility**
- **Stage 3B — pocket-relative structural plausibility**

The predeclared hard gate evaluates:

- bond-length plausibility
- bond-angle plausibility
- internal ligand steric clashes
- protein–ligand steric clashes

Other PoseBusters outputs are retained as diagnostics rather than hard attrition criteria.

Stage 3B receives an explicitly prepared pocket artifact rather than invoking generator-specific preprocessing inside the evaluator.

For the 3RFM baseline, the evaluation pocket contains 36 standard amino-acid residues selected using a `< 8.0 Å` reference-ligand distance rule while preserving the deposited protein heavy-atom coordinates.

Results:

```text
Stage 3 entering: 18

Stage 3A passing:
16 / 18

Stage 3B protein-clash gate passing:
18 / 18

Combined Stage 3 passing:
16 / 18 = 88.89%
```

The two Stage 3 failures (`molecule_id=13` and `molecule_id=16`) resulted from ligand-intrinsic geometry rather than protein-pocket clashes.

Cumulative strict cascade survival after Stage 3:

```text
16 / 20 = 80%
```

---

## Stage 4 — Novelty / Chemical-Space Characterization

Implemented in:

`evaluation/novelty.py`

Stage 4 is intentionally **non-attritional**.

Rather than eliminating molecules according to an arbitrary structural-similarity cutoff, Stage 4 characterizes surviving molecules in three complementary chemical reference spaces while preserving all molecules for downstream evaluation.

All Stage 4 comparisons use the same molecular representation:

- Morgan fingerprints
- radius = 2
- 2048 bits
- chirality enabled
- Tanimoto similarity

The molecular representation remains fixed across Stage 4. Only the comparison population changes.

### Stage 4A — Internal Generated-Set Similarity

Stage 4A asks:

> How redundant is the surviving generated set?

The 16 Stage-3 survivors were compared against one another across all 120 unique unordered molecule pairs.

For each molecule, the most similar generated neighbor is also recorded.

Results:

```text
Number of unique pairs: 120

Pairwise mean similarity:   0.0892
Pairwise SD:                0.0306
Pairwise median similarity: 0.0872
Pairwise range:             0.0147–0.1961
```

Under the predefined fingerprint representation, the surviving generated set shows low internal fingerprint similarity and no obvious near-duplicate pairs.

No universal diversity threshold is imposed.

Artifacts:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4a_pairs.csv
experiments/phase1_diffsbdd/evaluation/novelty_4a.csv
```

### Stage 4B — Known Target-Ligand-Space Similarity

Stage 4B asks:

> How similar is each generated molecule to known ligand chemistry associated with the current target?

For the Phase 1 baseline, a frozen ChEMBL 37 reference set was constructed for the human A2A receptor.

Target:

```text
CHEMBL251
Adenosine receptor A2a
Homo sapiens
SINGLE PROTEIN
```

Qualifying ChEMBL activity records were restricted to:

- Ki
- Kd
- IC50
- EC50
- non-null standardized values
- standard relation `=`, `<`, or `<=`
- pChEMBL >= 6.0

Structures were parsed with RDKit, converted to canonical isomeric structures, and deduplicated by canonical structure while retaining ChEMBL activity and source provenance.

Final frozen A2A reference:

```text
5,344 unique known target-ligand structures
0 duplicate canonical structures
all retained pChEMBL values >= 6.0
```

Artifact:

```text
references/chembl37/ADORA2A_target_ligands.csv
```

Each of the 16 generated molecules was compared against all 5,344 reference structures.

Total comparisons:

```text
16 × 5,344 = 85,504
```

For each generated molecule, Stage 4B records:

- nearest known target ligand
- nearest-target Tanimoto similarity
- mean similarity to the five nearest target ligands
- target reference-set size

Results:

```text
Nearest-target similarity

Mean:    0.2252
SD:      0.0507
Median:  0.2144
Range:   0.1392–0.3043

Top-5 target-ligand similarity

Mean:    0.2061
SD:      0.0437
```

Stage 4B measures proximity to **known target-associated ligand chemistry**.

The reference ligands do not need to be approved drugs.

Artifact:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4b.csv
```

### Stage 4C — Approved-Drug-Space Similarity

Stage 4C asks:

> How similar is each generated molecule to established approved small-molecule chemistry?

Unlike Stage 4B, the Stage 4C reference is target-independent.

A frozen ChEMBL 37 approved-drug reference was constructed using:

- `max_phase = 4`
- `molecule_type = Small molecule`

Approved salts and alternative forms were normalized to their ChEMBL parent structures where possible.

For example:

```text
CARBACHOL
CHEMBL14
C[N+](C)(C)CCOC(N)=O.[Cl-]

        ↓ parent normalization

CARBAMOYLCHOLINE
CHEMBL965
C[N+](C)(C)CCOC(N)=O
```

The parent structure is used for chemical-space comparison while the approved-form identity is retained as provenance.

Approved records without any resolvable molecular structure cannot define a Morgan-fingerprint reference point and are explicitly excluded from the structural reference.

Final frozen approved-drug reference:

```text
2,198 unique parent-normalized approved-drug structures

158 approved records excluded because
no usable molecular structure could be resolved
```

Structural audit:

```text
2,198 / 2,198 structures parsed by RDKit
0 duplicate canonical structures
```

Withdrawal metadata:

```text
268 structures associated with at least one withdrawn approved record
1,930 without a withdrawn approved record
```

Withdrawal status and first-approval information are retained as descriptive provenance and do not affect reference inclusion or similarity calculations.

Artifact:

```text
references/chembl37/approved_drugs.csv
```

Each generated molecule was compared against all 2,198 approved-drug reference structures.

Total comparisons:

```text
16 × 2,198 = 35,168
```

For each molecule, Stage 4C records:

- nearest approved parent structure
- parent ChEMBL ID and name
- associated approved record IDs and names
- first-approval metadata where available
- withdrawal metadata
- nearest-approved Tanimoto similarity
- mean similarity to the five nearest approved structures
- approved reference-set size

Results:

```text
Nearest-approved similarity

Mean:    0.2461
SD:      0.0636
Median:  0.2290
Range:   0.1569–0.3824

Top-5 approved-drug similarity

Mean:    0.2184
SD:      0.0495
```

Stage 4C measures proximity to **established approved-drug chemistry across targets**, independently of target identity.

Artifact:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4c.csv
```

### Combined Stage 4 Output

Stage 4A, 4B, and 4C molecule-level outputs are combined strictly by original `molecule_id`.

The merge uses one-to-one molecule-ID validation and preserves mismatches rather than silently dropping molecules.

Final artifact:

```text
experiments/phase1_diffsbdd/evaluation/novelty.csv
```

The combined output contains exactly the same 16 molecule IDs that entered Stage 4:

```text
0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19
```

All core Stage 4 similarity measurements are populated.

Two nearest approved-drug neighbors lack first-approval metadata in ChEMBL. These remain missing reference metadata rather than evaluation failures.

### Stage 4 Interpretation

The three Stage 4 analyses answer distinct questions:

| Substage | Comparison space | Question |
|---|---|---|
| Stage 4A | Generated molecules | How redundant is the generated set? |
| Stage 4B | Known target ligands | How close is each molecule to known target-associated ligand chemistry? |
| Stage 4C | Approved drugs | How close is each molecule to established approved-drug chemistry? |

Summary:

```text
Stage 4A — generated vs generated

Pairwise mean: 0.0892
Pairwise max:  0.1961


Stage 4B — generated vs known A2A ligands

Mean nearest: 0.2252
Mean top-5:   0.2061


Stage 4C — generated vs approved drugs

Mean nearest: 0.2461
Mean top-5:   0.2184
```

Under the predefined fingerprint representation, the surviving DiffSBDD molecules show low internal redundancy while occupying measurable but generally modest similarity neighborhoods within both known A2A ligand space and approved-drug space.

Similarity values across Stage 4A, 4B, and 4C should not be interpreted as directly equivalent novelty thresholds because the comparison populations differ substantially in size and chemical composition.

Stage 4 similarity reading bands were predeclared before the FLOWR comparison using convention-anchored upper boundaries and reference-specific null-calibrated lower boundaries; see **D006** in `notes/Decisions.md` for the frozen bands, null calibration, and interpretation rules.

### Stage 4 Attrition

Stage 4 is intentionally non-attritional.

```text
Stage 4 entering: 16
Stage 4 leaving:  16

Stage 4 survival: 16 / 16 = 100%
Stage 4 attrition: 0
```

Cumulative strict cascade survival therefore remains:

```text
16 / 20 = 80%
```

---

## Stage 5 — Target–Ligand Interaction Evidence

Stage 5 evaluates whether surviving generator-provided poses reproduce experimentally grounded target–ligand recognition chemistry.

Stage 5 is **method-generalized but target-specific in implementation**. The generalized framework determines the available interaction-evidence level, permitted claims, validation requirements, and whether hard attrition is authorized. The biological interaction definition itself is target-specific.

### Interaction-Evidence Levels

Structurally defined targets are assigned one of three interaction-evidence levels:

- **Level 1 — validated compatibility testing:** direct experimental cognate target–ligand structural evidence is available.
- **Level 2 — interaction characterization:** direct cognate evidence is unavailable, but interaction characterization is supportable from an apo target structure or a demonstrably conserved ligand-bound homolog.
- **Level 3 — insufficient interaction evidence:** a target structure exists, but available target–ligand evidence is insufficient for a compatibility verdict.

Evidence level and gate validation are separate. Level 1 permits development of a target-specific compatibility gate but does not automatically authorize attrition.

For the Phase 1 A2A baseline:

```text
A2A interaction-evidence level: LEVEL 1
```

### Frozen A2A Recognition Criterion

The A2A interaction definition was derived from experimental cognate complexes before inspection of the DiffSBDD Stage-5 outcomes:

- 3REY / XAC
- 5OLH / Vipadenant
- 5OLO / Tozadenant

The frozen ProLIF recognition criterion is:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

`VdWContact` is retained as characterization evidence but does not satisfy the Phe168 arm.

**ProLIF 2.2.0** is the frozen Stage-5 verdict instrument.

**PLIP 3.0.1** is a separately qualified independent witness. PLIP provides concordance evidence but does not define or override the Stage-5 verdict.

### Gate Validation

Hard attrition requires validation of the target-specific implementation independently of generated-molecule outcomes.

For the finalized A2A gate, the frozen validation panel produced:

```text
Experimental positives retained: 3 / 3
Primary-panel negatives rejected: 6 / 6
```

The same frozen interaction-class criterion governs both arms.

The six-member primary-negative panel was frozen before the blind ProLIF read and contained physically qualified poses from two independent pose-generation lineages:

```text
DOCK:  1
rDock: 5
```

All six blind negatives were recognition-negative under the frozen criterion.

A predeclared receptor-artifact guard also checked every blind negative for any interaction involving residue 75. The guard remained clear for all six:

```text
Residue-75 guard clear: 6 / 6
```

Independent PLIP witness evaluation was concordant with ProLIF across the frozen 16-member DiffSBDD cohort:

```text
Complete-pattern concordance: 16 / 16
Discordant cases:              0
```

The validated authority is deliberately bounded to **molecule-level A2A interaction-pattern discrimination**. Stage 5 does not establish general pose sensitivity, universal specificity, experimental binding, or biological activity.

### DiffSBDD Stage-5 Evaluation

Stage 5 consumes the same 16 molecules that survived Stage 3 and were characterized in Stage 4.

The preserved Stage-5 measurements use:

- original molecule IDs;
- unmodified generator-provided coordinates;
- the interaction-ready 3RFM receptor in the generator's coordinate frame;
- the frozen ProLIF interaction reader;
- the frozen A2A recognition criterion.

Feature-level results were:

```text
Phe168 reference feature reproduced: 15 / 16
Asn253 reference feature reproduced:  4 / 16
Complete A2A pattern reproduced:       3 / 16
```

The complete pattern was reproduced by:

```text
molecule_id = 0
molecule_id = 3
molecule_id = 18
```

Following validation of the A2A gate and the D023 authority decision, the preserved measurements now exercise Stage-5 cascade attrition without being rerun or recalibrated:

```text
Stage 5 entering: 16

Retained through Stage 5:
3 / 16

Attrited from forward cascade progression:
13 / 16
```

The 13 attrited molecules remain permanently retained as characterization evidence. Their measurements are not deleted or hidden, and the feature-level pattern is preserved as evidence of the generator's Stage-5 failure mode.

In particular, Phe168 recognition was reproduced much more frequently than Asn253 recognition:

```text
Phe168:  15 / 16
Asn253:   4 / 16
Complete: 3 / 16
```

Stage-5 attrition means that a generator-provided pose did not reproduce the frozen A2A recognition criterion under the validated molecule-level gate. It does **not** establish that the molecule is experimentally inactive or incapable of binding A2A in another pose.

### Stage 5 Attrition

```text
Stage 5 entering: 16
Stage 5 leaving:   3

Stage 5 survival:  3 / 16 = 18.75%
Stage 5 attrition: 13 / 16 = 81.25%
```

Cumulative strict cascade survival after Stage 5:

```text
3 / 20 = 15%
```

The three Stage-5 survivors continue to Stage 6 — Synthetic Feasibility.

---

## Reference-Data Policy

Live ChEMBL access is separated from normal evaluation.

Reference construction is implemented in:

`scripts/build_chembl_reference.py`

Current frozen reference release:

```text
ChEMBL 37
```

Normal Stage 4 evaluation consumes local versioned reference files rather than querying ChEMBL live.

This ensures that:

- generator comparisons use identical reference populations
- database updates cannot silently change results
- network availability does not affect normal evaluation
- ChEMBL-specific retrieval logic remains outside the generator-independent evaluator

Future ChEMBL releases should produce new versioned reference artifacts rather than silently replacing the current reference sets.

---

## Target Selection Plan

The final project target will not be locked until the predefined target-selection rubric is completed.

A target selected by the Bivona lab supersedes the fallback target-selection process.

If no lab-selected target is available, fallback candidates will be compared using separate criteria for:

- generative tractability
- developability tractability
- biological / translational relevance
- pocket definition and structural evidence
- suitability for demonstrating the evaluation cascade

Current fallback framing:

- **SOS1** is a strong candidate for demonstrating that the overall pipeline can generate and advance plausible chemistry.
- **TEAD** is a strong candidate for demonstrating that the evaluation cascade provides useful discrimination under difficult developability conditions.

If TEAD is selected, high Stage 2 and later developability attrition is a **predeclared expectation** because the TEAD allosteric lipid pocket is deep and hydrophobic and may favor lipophilic generated chemistry.

A high developability flag rate for TEAD would therefore be interpreted as evidence that the cascade is identifying the expected liabilities of a difficult pocket rather than automatically as a pipeline failure.

Generative tractability and developability tractability should remain separate dimensions in the target-selection rubric so that the same pocket property is not penalized twice.

---

## Long-Term Developability Layer

Later stages are planned to include:

- target compatibility
- synthetic feasibility
- ADME / disposition characterization
- BCS / BDDCS-related prediction
- safety-risk characterization
- DILI risk characterization
- virtual-cell simulation

Disposition and DILI are intended as **late-stage characterization**, not early chemistry filters.

The proposed virtual-cell stage has a major unresolved limitation: mapping arbitrary generated molecular structures to credible cellular responses remains an open problem.

Therefore, the virtual-cell gate must first be validated on known drugs with real outcome labels before being applied to generated molecules.

A planned feasibility study will compare structure-only and virtual-cell-informed DILI prediction using known drugs with DILIrank labels, including analysis stratified by BDDCS class.

---

## Evaluation Environment

The generator-independent evaluation cascade uses the `sbdd-eval` Conda environment.

Create it with:

```bash
conda env create -f environment.yml
conda activate sbdd-eval
```

The environment includes the pinned dependencies required for the implemented evaluation and reference-construction stages, including RDKit, PoseBusters, ProLIF, and the ChEMBL web-resource client.

Stage-5 independent-witness work uses the separately qualified PLIP environment and remains distinct from the frozen ProLIF verdict pathway.

Generator environments remain separate from the evaluation environment.

---

## Repository Structure

```text
sbdd-project/
├── evaluation/              # generator-independent scientific evaluation
├── scripts/
│   ├── stage5/              # Stage-5 execution, qualification, and audit tooling
│   └── build_chembl_reference.py
├── references/
│   ├── chembl37/            # frozen Stage-4 reference populations
│   └── stage5/              # frozen Stage-5 configs, controls, validation, and evidence
├── experiments/
│   └── phase1_diffsbdd/
│       └── evaluation/      # DiffSBDD baseline evaluation artifacts
├── notes/
│   ├── Decisions.md
│   ├── Development.md
│   ├── Session_XXX.md
│   └── handoffs/
├── tests/
├── environment.yml
└── README.md
```

External generator repositories, model checkpoints, and generated molecular SDF files are intentionally excluded from Git where appropriate.

Frozen reference artifacts, validation evidence, machine-readable evaluation outputs, and characterization records are retained where required to preserve reproducibility and auditability.

---

## Current Development Principle

The evaluation cascade is the central reusable component of the project.

Each evaluation stage should:

- consume standardized molecular files or standardized upstream results
- preserve molecule-level provenance
- record explicit pass/fail outcomes where applicable
- preserve failure reasons
- produce machine-readable outputs
- avoid generator-specific assumptions

Reference-data construction should remain separate from evaluation.

Generators should produce standardized molecular artifacts, while evaluation stages consume those artifacts through generator-independent interfaces.

---

## Current Cascade

```text
20 DiffSBDD molecules generated
        ↓
Stage 1 — Chemical Validity
19 / 20
        ↓
Stage 2 — Rule-of-Five Strict Classification
18 / 19
        ↓
Stage 3 — 3D / Structural Plausibility
16 / 18
        ↓
Stage 4 — Novelty / Chemical-Space Characterization
16 / 16
        ↓
Stage 5 — Target–Ligand Interaction Evidence
3 / 16
        ↓
Stage 6 — Synthetic Feasibility
next
```

Current cumulative strict cascade survival:

```text
3 / 20 = 15%
```

The 13 molecules attrited at Stage 5 remain permanently preserved as characterization evidence even though they no longer progress through the strict cascade.

---

## Project Status

**Current phase:** Phase 1  
**Current generator:** DiffSBDD  
**Completed cascade stages:** Chemical validity; molecular property profiling / Rule-of-Five classification; 3D / structural plausibility; novelty / chemical-space characterization; target–ligand interaction evidence  
**Stage-5 status:** Validated and frozen for the A2A Level-1 implementation; DiffSBDD disposition complete  
**Current strict cascade survival:** 3/20 (15%)  
**Stage-5 characterization record:** Phe168 15/16; Asn253 4/16; complete A2A pattern 3/16  
**Next implementation:** Stage 6 — synthetic feasibility  
**FLOWR comparator arm:** Deferred until the complete DiffSBDD baseline cascade is implemented and frozen
