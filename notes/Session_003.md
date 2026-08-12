## Results

### Evaluation environment

Created a generator-independent local evaluation environment:

- Environment: `sbdd-eval`
- Python 3.12
- RDKit 2026.03.5
- Development environment: VSCode on local Mac

This environment is separate from the legacy DiffSBDD generation environment.

### Stage 1 — RDKit validity

Implemented `evaluation/validity.py`.

The evaluator:

- accepts an arbitrary SDF path
- reads records with `sanitize=False`
- preserves explicit hydrogens during initial loading
- records parse success/failure independently from sanitization
- attempts RDKit sanitization on every successfully parsed molecule
- preserves failure reasons
- returns one result for every input record
- exports molecule-level results to CSV
- produces a validity/attrition summary
- contains no DiffSBDD-specific imports or assumptions

### 3RFM DiffSBDD results

Input:

`experiments/phase1_diffsbdd/3rfm_mol.sdf`

Results:

| Stage | Entering | Surviving | Failed | Survival |
|---|---:|---:|---:|---:|
| SDF records | 20 | 20 | 0 | 100% |
| RDKit parsing | 20 | 20 | 0 | 100% |
| RDKit sanitization | 20 | 19 | 1 | 95% |

One molecule failed sanitization.

- `molecule_id`: 15 (zero-based index; 16th SDF record)
- Parsing: passed
- Sanitization: failed
- Failure reason: `Explicit valence for atom # 1 C, 5, is greater than permitted`

The molecule was retained as a failed result rather than repaired or silently removed.

Molecule-level results were saved to:

`experiments/phase1_diffsbdd/evaluation/validity.csv`

### Robustness test

Created an intentionally malformed SDF record under `tests/data/`.

The evaluator correctly reported:

- input records: 1
- parsed: 0
- parse failures: 1
- sanitized: 0
- total validity failures: 1
- survival rate: 0%

The malformed record remained represented in the results with:

- `parsed=False`
- `sanitized=False`
- an explicit parsing failure reason

The evaluator therefore successfully handles all three tested paths:

1. parse pass → sanitization pass
2. parse pass → sanitization fail
3. parse fail

## Key Findings

- DiffSBDD produced 20 structurally readable SDF records, but RDKit sanitization identified one chemically invalid molecular graph.
- Parseability and chemical validity must remain separate evaluation outcomes.
- Stage 1 validity survival for this initial DiffSBDD sample is 19/20 (95%).
- Evaluation can operate entirely from the generated SDF without access to DiffSBDD model internals.
- Invalid and malformed molecules can be retained as explicit failures rather than silently discarded.
- The Stage 1 implementation is generator-agnostic and can be applied unchanged to future generator outputs.