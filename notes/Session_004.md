# Session 4 — 2026-08-12

**Approximate session duration:** TBD

## Objective

Implement Stage 2 of the generator-agnostic evaluation cascade: molecular property profiling and Rule-of-Five feasibility classification.

Stage 2 will characterize the molecules surviving Stage 1 while preserving molecule-level provenance and separating descriptive molecular properties from explicit feasibility classifications.

---

## Starting Point

Session 3 completed Stage 1 — chemical validity.

Initial DiffSBDD result:

| Stage | Entering | Surviving | Failed |
| --- | ---: | ---: | ---: |
| Generated SDF records | 20 | 20 | 0 |
| RDKit parsing | 20 | 20 | 0 |
| RDKit sanitization | 20 | 19 | 1 |

Stage 1 survival: **19/20 (95%)**

One molecule (`molecule_id=15`, zero-based) failed RDKit sanitization because of an explicit carbon valence of 5.

Stage 1 implementation:

`evaluation/validity.py`

Stage 1 molecule-level results:

`experiments/phase1_diffsbdd/evaluation/validity.csv`

---

## Stage 2 Specification

For every molecule surviving Stage 1, calculate:

- molecular weight
- cLogP
- hydrogen-bond donors
- hydrogen-bond acceptors
- topological polar surface area (TPSA)
- rotatable bonds
- QED
- heavy atom count
- formal charge

Also calculate explicit Rule-of-Five outcomes:

- molecular-weight criterion
- cLogP criterion
- HBD criterion
- HBA criterion
- total Rule-of-Five violations
- overall Rule-of-Five classification

Raw property measurements must be retained regardless of Rule-of-Five classification.

Rule-of-Five failure represents a drug-likeness / oral-feasibility flag and must not be interpreted as proof that a molecule cannot become a drug.

---

## Architecture Rules

Stage 2 must:

- remain generator-agnostic
- contain no DiffSBDD-specific imports or paths
- operate from standardized molecular files/results
- evaluate only molecules that survived Stage 1
- preserve the original `molecule_id`
- never renumber surviving molecules
- retain raw property values
- retain individual Rule-of-Five criterion outcomes
- produce machine-readable output
- keep descriptive measurements separate from pass/fail classifications

The same implementation must later work unchanged on FLOWR output.

---

## Today's Question

What are the molecular-property profiles of the 19 Stage-1-valid DiffSBDD molecules, and how many satisfy the Rule-of-Five feasibility classification?

---

## Success Criteria

- [x] Confirm repository is clean and synchronized.
- [x] Confirm `sbdd-eval` environment is active.
- [x] Create `evaluation/properties.py`.
- [x] Load Stage 1 validity results.
- [x] Select only Stage-1-valid molecules.
- [x] Preserve original molecule IDs.
- [x] Calculate all specified molecular properties.
- [x] Calculate each Rule-of-Five criterion independently.
- [x] Calculate total Rule-of-Five violations.
- [x] Record overall Rule-of-Five classification.
- [x] Save molecule-level Stage 2 results.
- [x] Produce a Stage 2 summary.
- [x] Confirm Stage 2 contains no generator-specific assumptions.
- [x] Record Stage 2 results and attrition in this log.
- [ ] Commit and push the completed Stage 2 implementation.

---

## Results

### Stage 2 implementation

Created:

`evaluation/properties.py`

Stage 2:

- consumes the Stage 1 `validity.csv`
- selects only molecules with `sanitized=True`
- preserves original zero-based `molecule_id` values
- loads the corresponding molecules from the original SDF
- calculates molecular property profiles
- independently classifies each molecule using Rule-of-Five criteria
- exports molecule-level results to CSV
- produces a Stage 2 summary
- contains no DiffSBDD-specific imports or assumptions

### Molecular properties

For every Stage-1-valid molecule, Stage 2 calculates:

- molecular weight
- cLogP
- TPSA
- hydrogen-bond donors
- hydrogen-bond acceptors
- rotatable bonds
- QED
- heavy atom count
- formal charge

### Rule-of-Five classification

The following criteria were evaluated independently:

- molecular weight ≤ 500 Da
- cLogP ≤ 5
- HBD ≤ 5
- HBA ≤ 10

A molecule is recorded as `ro5_passes=True` when it has zero violations.

Individual criterion outcomes and the total number of violations are retained regardless of the aggregate classification.

### 3RFM DiffSBDD results

Stage 2 received the 19 molecules that survived Stage 1.

| Stage | Entering | Zero-violation / surviving | Flagged | Stage survival |
| --- | ---: | ---: | ---: | ---: |
| Generated molecules | 20 | 20 | 0 | 100% |
| Stage 1 — RDKit validity | 20 | 19 | 1 | 95% |
| Stage 2 — zero Ro5 violations | 19 | 18 | 1 | 94.74% |

Cumulative survival from generation through the strict zero-Ro5-violation classification:

**18/20 = 90%**

### Stage 2 flagged molecule

One molecule had Rule-of-Five violations:

- `molecule_id`: 4
- molecular weight: 607.64 Da
- cLogP: -0.681
- HBD: 4
- HBA: 14
- Rule-of-Five violations: 2

Failed criteria:

- molecular weight > 500 Da
- HBA > 10

Additional descriptive properties:

- TPSA: 205.87 Å²
- rotatable bonds: 16
- QED: 0.0604
- heavy atoms: 43
- formal charge: 0

This molecule is recorded as Rule-of-Five flagged rather than interpreted as categorically incapable of becoming a drug.

### Machine-readable output

Stage 2 results were saved to:

`experiments/phase1_diffsbdd/evaluation/properties.csv`

The file contains 19 molecule-level rows and preserves the original molecule identifiers.

`molecule_id=15`, which failed Stage 1, remains absent rather than causing downstream molecules to be renumbered.

### Robustness testing

The Rule-of-Five classifier was manually tested using controlled property dictionaries representing:

- zero violations
- one violation
- four violations
- values exactly at all four thresholds

Observed violation counts matched expectations.

The exact threshold case:

- MW = 500
- cLogP = 5
- HBD = 5
- HBA = 10

correctly produced zero violations because the implemented criteria use inclusive `<=` boundaries.

---

## Key Findings

- Stage 1 and Stage 2 now communicate through a machine-readable interface rather than model internals.
- Original molecule identifiers remain stable across cascade stages.
- All 19 Stage-1-valid molecules were successfully property-profiled.
- 18/19 Stage-1 survivors had zero Rule-of-Five violations.
- One molecule was flagged for two violations: molecular weight and hydrogen-bond acceptor count.
- Raw molecular properties provide substantially more information than a single aggregate Rule-of-Five classification.
- Rule-of-Five classification should be interpreted as an oral/drug-likeness feasibility heuristic rather than a universal definition of whether a molecule can become a drug.
- Cumulative survival through the first two cascade stages is 18/20 (90%).
- Stage 2 remains generator-agnostic and can later be applied unchanged to FLOWR outputs.

---

## Session 4 Milestone

The generator-independent evaluation cascade now contains two functioning stages:

```text
20 generated
    ↓
Stage 1 — Chemical validity
19 survive
    ↓
Stage 2 — Molecular properties / Rule-of-Five
18 have zero Rule-of-Five violations
```

Measured attrition:

- Stage 1 survival: **19/20 = 95%**
- Stage 2 zero-violation rate: **18/19 = 94.74%**
- Cumulative strict survival: **18/20 = 90%**

The cascade now preserves molecule-level provenance and failure modes across multiple evaluation stages.

---

## Next Step

Stage 3 will evaluate 3D / structural plausibility of surviving generated molecules.

Before implementation, define the exact structural checks, expected inputs, and whether PoseBusters or an equivalent framework should provide the primary Stage 3 evaluation.

The Stage 3 design must preserve the same generator-independent, molecule-level provenance and attrition bookkeeping established in Stages 1 and 2.