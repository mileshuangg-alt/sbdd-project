# Session 3 — 2026-08-12

## Objective

Build the first stage of the generator-agnostic evaluation cascade and determine how many of the 20 DiffSBDD-generated molecules pass independent RDKit sanitization.

---

## Starting Point

Phase 1 generation baseline was completed in Session 2.

Starting artifact:

`experiments/phase1_diffsbdd/3rfm_mol.sdf`

From Session 2:

- DiffSBDD successfully ran using the released CrossDocked conditional checkpoint.
- Target example: 3RFM.
- Pocket defined using reference ligand `A:330`.
- 20 molecules were generated.
- The output contained 20 SDF records.
- RDKit could parse 20/20 records with `sanitize=False`.
- Chemical validity had not yet been independently evaluated.

---

## Architecture Rule

Evaluation must remain independent of the generator.

The validity stage must:

- accept an SDF file as input
- contain no DiffSBDD imports
- process every input record
- explicitly record parse and sanitization outcomes
- preserve failure reasons
- report the number of molecules entering and surviving the stage

The same evaluation code should later work without modification on:

- DiffSBDD output
- FLOWR output
- known actives
- known decoys

---

## Today's Question

Of the 20 generated structures in `3rfm_mol.sdf`, how many pass independent RDKit sanitization?

---

## Success Criteria

- [x] Confirm the saved SDF is available locally.
- [x] Establish a local evaluation Python environment.
- [x] Create `evaluation/validity.py`.
- [x] Read all SDF records without silently dropping failures.
- [x] Attempt RDKit sanitization independently for every parsed molecule.
- [x] Record pass/fail status for every input record.
- [x] Record an interpretable failure reason where possible.
- [x] Save machine-readable molecule-level validity results.
- [x] Calculate Stage 1 attrition.
- [x] Confirm the evaluation code contains no DiffSBDD-specific dependencies.
- [x] Test explicit handling of a malformed SDF record.
- [x] Commit and push the Stage 1 implementation and results.

---

## Environment

A dedicated generator-independent evaluation environment was created locally.

- Environment: `sbdd-eval`
- Python: 3.12
- RDKit: 2026.03.5
- Development environment: VSCode on local Mac
- Environment manager: Miniforge / Conda

This environment is intentionally separate from the legacy DiffSBDD generation environment.

DiffSBDD generation therefore remains isolated from downstream evaluation dependencies.

---

## Implementation

Created:

`evaluation/validity.py`

The validity evaluator:

1. Accepts an arbitrary SDF path.
2. Confirms that the requested input file exists.
3. Loads SDF records using RDKit with:
   - `sanitize=False`
   - `removeHs=False`
4. Preserves every input record for evaluation.
5. Records whether RDKit successfully parsed each record.
6. Attempts `Chem.SanitizeMol()` on each successfully parsed molecule.
7. Records sanitization success or failure.
8. Preserves an explicit failure reason when possible.
9. Returns one result dictionary per input SDF record.
10. Exports molecule-level results to CSV.
11. Produces a summary of parsing, sanitization, failures, and survival rate.

The implementation contains no DiffSBDD imports and does not access model internals.

---

## Definition of Stage 1 Outcomes

Parsing and validity are treated as separate concepts.

### Parsed

`parsed=True` means RDKit successfully constructed a molecular graph from the SDF record.

This does not imply that the molecular graph is chemically valid.

### Sanitized

`sanitized=True` means the parsed molecule successfully passed RDKit's standard `Chem.SanitizeMol()` procedure.

For this evaluation cascade, a molecule is classified as **RDKit valid** only when it successfully parses and sanitizes.

Therefore:

`parseable != chemically valid`

---

## Results

### Input

`experiments/phase1_diffsbdd/3rfm_mol.sdf`

### Stage 1 Attrition

| Stage | Entering | Surviving | Failed | Survival |
|---|---:|---:|---:|---:|
| Generated SDF records | 20 | 20 | 0 | 100% |
| RDKit parsing | 20 | 20 | 0 | 100% |
| RDKit sanitization | 20 | 19 | 1 | 95% |

Final Stage 1 result:

- Total molecules evaluated: 20
- Successfully parsed: 20
- Failed parsing: 0
- Successfully sanitized: 19
- Failed sanitization after parsing: 1
- Total molecules failing Stage 1 validity: 1
- Stage 1 survival rate: 95%

---

## Failed Molecule

One DiffSBDD-generated molecule was parseable but failed RDKit sanitization.

Recorded result:

- `molecule_id`: 15
- Index convention: zero-based
- Corresponding SDF record: 16th record
- `parsed=True`
- `sanitized=False`

Failure reason:

`Explicit valence for atom # 1 C, 5, is greater than permitted`

This molecule was retained as a failed result.

It was not repaired, removed, or silently discarded.

---

## Machine-Readable Output

Molecule-level results were saved to:

`experiments/phase1_diffsbdd/evaluation/validity.csv`

The CSV contains one row for every generated molecule with:

- `molecule_id`
- `parsed`
- `sanitized`
- `failure_reason`

The output therefore preserves the complete Stage 1 audit trail.

---

## Robustness Test

A deliberately malformed SDF record was created at:

`tests/data/invalid_record.sdf`

This was used to test the parse-failure branch of the evaluator.

RDKit correctly failed to interpret the malformed mol block.

The evaluator did not crash and did not silently remove the record.

Result:

- Total molecules evaluated: 1
- Successfully parsed: 0
- Failed parsing: 1
- Successfully sanitized: 0
- Failed sanitization after parsing: 0
- Total molecules failing validity: 1
- Survival rate: 0%

The result record contained:

- `parsed=False`
- `sanitized=False`
- an explicit parsing failure reason

---

## Verified Stage 1 Paths

The evaluator has now demonstrated all three expected paths:

### Valid structure

`SDF record -> parse PASS -> sanitization PASS -> Stage 1 PASS`

### Chemically invalid structure

`SDF record -> parse PASS -> sanitization FAIL -> Stage 1 FAIL`

### Malformed structure

`SDF record -> parse FAIL -> Stage 1 FAIL`

In all cases, the input record remains represented in the evaluation results.

---

## Generator-Agnostic Boundary

The implemented architecture is now:

```text
Generator
   |
   v
SDF file
   |
   +----------------------+
   |                      |
DiffSBDD               FLOWR
(output today)      (future output)
   |                      |
   +----------+-----------+
              |
              v
     evaluation/validity.py
              |
              v
      molecule-level results
              |
              v
        attrition summary
```

The evaluator does not know which generator produced the SDF.

This establishes the first working generator-independent component of the evaluation cascade.

---

## Key Findings

- DiffSBDD produced 20 structurally readable SDF records.
- All 20 records were parseable by RDKit.
- One of the 20 generated molecular graphs failed independent RDKit sanitization.
- Stage 1 validity survival for the initial DiffSBDD sample was 19/20, or 95%.
- Parseability and chemical validity are meaningfully different outcomes and should remain separately recorded.
- Invalid molecules can be retained as explicit failures rather than repaired or silently removed.
- Malformed SDF records can also be preserved as explicit failures.
- Evaluation can operate entirely from generator output files without accessing DiffSBDD model internals.
- The first evaluation stage is therefore generator-agnostic and suitable for reuse with FLOWR later.

---

## Repository / Reproducibility Updates

The project now contains:

```text
evaluation/
├── __init__.py
└── validity.py

experiments/
└── phase1_diffsbdd/
    └── evaluation/
        └── validity.csv

tests/
└── data/
    └── invalid_record.sdf
```

Generated experiment SDF files remain excluded from Git.

Controlled SDF test fixtures under `tests/data/` are explicitly allowed so the robustness test can be reproduced.

Python cache files and local VSCode configuration are excluded from Git.

The Stage 1 implementation, results, test fixture, and session documentation were committed and pushed to the project repository.

---

## Session 3 Milestone

The project now has its first functioning evaluation-cascade stage.

For the initial DiffSBDD sample:

`20 generated -> 20 parsed -> 19 RDKit valid`

Stage 1 attrition:

**5%**

Stage 1 survival:

**95%**

This is the first measured attrition point in the generator-independent evaluation cascade.

---

## Planned Late-Stage Developability Extension

The intended endpoint of the evaluation cascade was expanded during Session 3.

After the core chemical, structural, target-compatibility, novelty, and synthetic-feasibility stages are established, the project will investigate adding a late-stage **developability characterization layer**.

This layer may include:

- predicted drug disposition
- predicted solubility
- predicted metabolism/disposition behavior
- BCS/BDDCS-style classification
- transporter and elimination considerations where supported
- DILI risk prediction
- potentially additional ADME and safety-related endpoints

The purpose of this extension is to ask a broader question than whether a generative model produces chemically valid or target-compatible molecules:

> Do generated molecules survive progressively more development-relevant constraints?

BDDCS class and DILI risk must be treated as **predicted outcomes**, not experimental determinations.

The exact implementation should be grounded in appropriate literature and validated predictive methods. If available, the Leslie Z. Benet lecture materials that motivated this addition should be reviewed when designing the disposition and DILI components.

This extension is intentionally deferred until the core generator-agnostic cascade is functioning. It should not delay the current Phase 1 work.

The longer-term cascade is therefore envisioned approximately as:

`generation -> chemical validity -> drug-likeness/property feasibility -> structural/3D plausibility -> novelty -> target compatibility -> synthetic feasibility -> disposition/developability characterization -> safety-risk characterization`

The final output should preserve individual measurements, classifications, failure reasons, model provenance, and uncertainty rather than collapsing developability into a single opaque score.

--- 

## Next Step

Define Stage 2 of the cascade before implementing it.

Candidate molecular properties include:

- molecular weight
- logP
- hydrogen-bond donors
- hydrogen-bond acceptors
- rotatable bonds
- QED
- possibly additional structural/property descriptors

Before implementing Stage 2, determine which properties are:

1. descriptive measurements only
2. actual pass/fail filters
3. scientifically justified for the intended SBDD evaluation

Avoid automatically treating conventional drug-likeness heuristics as universal hard filters without first defining their role in the cascade.

The Stage 2 implementation should continue the same architecture:

`SDF / molecule-level input -> standardized results -> explicit attrition bookkeeping`

No generator-specific assumptions should enter the evaluation code.