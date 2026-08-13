## Success Criteria

- [x] Write D003 before inspecting Stage 3 results.
- [x] Verify the PoseBusters release/API to use.
- [x] Pin PoseBusters in `sbdd-eval`.
- [x] Confirm the installed PoseBusters version.
- [x] Map actual PoseBusters output names to the predeclared gate.
- [x] Define the Stage 3A interface.
- [x] Define the Stage 3B interface with explicit prepared-pocket input.
- [x] Create `evaluation/structure.py`.
- [x] Select the 18 Stage-2 survivors without renumbering them.
- [x] Evaluate original generated coordinates.
- [x] Preserve the full PoseBusters output.
- [x] Apply only the predeclared hard gate.
- [x] Produce molecule-level Stage 3 results.
- [x] Calculate the third 3RFM attrition number.
- [x] Document results and failure modes.
- [ ] Commit and push the completed Stage 3 implementation.

---

## Results

### Reproducible Stage 3 environment

Stage 3 was implemented using:

- PoseBusters `0.6.5`
- BioPython `1.88`
- the existing `sbdd-eval` environment

The PoseBusters version was pinned before structural results were interpreted.

The PoseBusters 0.6.5 configuration and returned output schema were inspected directly so that the evaluation code uses the field names and semantics of the installed version rather than assumptions from another release.

A reproducible evaluation environment specification is now stored in:

`environment.yml`

The file pins the Python, RDKit, pandas, NumPy, PoseBusters, and BioPython versions used for the current cascade baseline.

### Stage 3 input

Stage 3 consumed the 18 molecules that passed the Stage 2 zero-Rule-of-Five-violation gate.

Original zero-based molecule identifiers were preserved:

`0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19`

The previously removed molecules remained absent:

- `molecule_id=4` — Stage 2 Rule-of-Five flag
- `molecule_id=15` — Stage 1 validity failure

A Stage 3 input SDF containing only the 18 eligible molecules was written without generating new conformers or optimizing the structures.

The coordinates were checked against the original DiffSBDD SDF to confirm that the generated coordinates were preserved.

### Stage 3A — ligand-intrinsic structural plausibility

PoseBusters was run using the ligand-intrinsic `mol` configuration with the full report enabled.

The installed PoseBusters version returned 44 metrics before project-specific provenance and gate fields were added.

The predeclared Stage 3A hard gate used only:

- `bond_lengths`
- `bond_angles`
- `internal_steric_clash`

All three criteria were required to pass.

Other PoseBusters outputs were preserved as diagnostics and did not affect attrition.

Stage 3A results:

| Entering | Passing | Failing | Survival |
| ---: | ---: | ---: | ---: |
| 18 | 16 | 2 | 88.89% |

Two molecules failed the Stage 3A gate.

#### Molecule 13

- bond lengths: fail
- bond angles: pass
- internal steric clash: pass
- short bond outliers: 1
- long bond outliers: 0
- angle outliers: 0
- internal clashes: 0

The molecule therefore failed Stage 3A because of one implausibly short bond.

#### Molecule 16

- bond lengths: fail
- bond angles: fail
- internal steric clash: fail
- short bond outliers: 0
- long bond outliers: 1
- angle outliers: 1
- internal clashes: 1

This molecule failed all three predeclared Stage 3A criteria.

### Stage 3A diagnostics

The complete PoseBusters output was retained rather than reducing evaluation to the hard-gate fields.

The PoseBusters energy-ratio module failed to generate the comparison conformer ensemble for one structure and therefore could not calculate that diagnostic successfully.

Energy was predeclared as diagnostic-only. This failure therefore caused no attrition and did not change the Stage 3 gate.

The structure was not regenerated or optimized to force the energy diagnostic to succeed.

Full Stage 3A results were saved to:

`experiments/phase1_diffsbdd/evaluation/structure_3a.csv`

### Stage 3B — explicit pocket construction

Stage 3B was designed so that pocket preparation is an explicit upstream input rather than an implicit DiffSBDD operation.

Inspection of the DiffSBDD implementation showed that its reference-ligand pocket definition selects standard amino-acid residues when the minimum distance between any residue atom and any reference-ligand atom is less than 8.0 Å.

The shared evaluation code independently implemented the same geometric pocket-definition rule without importing DiffSBDD.

Inputs:

- source protein: `repos/DiffSBDD/example/3rfm.pdb`
- reference ligand: `repos/DiffSBDD/example/3rfm_B_CFF.sdf`
- distance cutoff: `< 8.0 Å`
- standard amino acids only

This selected 36 residues.

The resulting explicit evaluation artifact was written to:

`experiments/phase1_diffsbdd/evaluation/prepared_3rfm_pocket.pdb`

The written artifact was independently reloaded and confirmed to contain the same 36 residues.

For this Phase 1 baseline, pocket preparation preserves the deposited protein heavy-atom coordinates and does not add hydrogens, alter protonation, or optimize receptor geometry.

### Stage 3B — pocket-relative structural plausibility

PoseBusters was run using the `dock` configuration with:

- the original generated ligand coordinates
- the explicit prepared pocket artifact

The Stage 3B evaluator accepts the prepared pocket path directly and contains no DiffSBDD-specific pocket-preparation logic.

Before inspecting Stage 3B outcomes, D003 was clarified so that the predeclared steric-clash criterion maps to:

- Stage 3A: `internal_steric_clash`
- Stage 3B: PoseBusters protein-ligand clash result, returned as `minimum_distance_to_protein`

Protein maximum-distance and volume-overlap checks remain diagnostic-only.

Stage 3B results:

| Evaluated | Passing protein-clash gate | Failing | Survival |
| ---: | ---: | ---: | ---: |
| 18 | 18 | 0 | 100% |

All 18 molecules passed the protein-ligand steric-clash gate.

No molecule contained a PoseBusters pairwise protein clash under the pinned configuration.

The smallest reported ligand-protein distances across the evaluated molecules were approximately 2.69–3.48 Å.

Full Stage 3B results were saved to:

`experiments/phase1_diffsbdd/evaluation/structure_3b.csv`

### Combined Stage 3 gate

Stage 3A and Stage 3B results were joined using the original `molecule_id`.

The final gate is:

`stage3_passes = stage3a_passes AND stage3b_passes`

Final Stage 3 results:

| Stage | Entering | Surviving | Flagged | Stage survival |
| --- | ---: | ---: | ---: | ---: |
| Generated molecules | 20 | 20 | 0 | 100% |
| Stage 1 — RDKit validity | 20 | 19 | 1 | 95% |
| Stage 2 — zero Ro5 violations | 19 | 18 | 1 | 94.74% |
| Stage 3 — 3D structural plausibility | 18 | 16 | 2 | 88.89% |

Cumulative strict survival from generation through Stage 3:

**16/20 = 80%**

The two final Stage 3 failures were:

- `molecule_id=13`
- `molecule_id=16`

Both passed Stage 3B and therefore failed solely because of ligand-intrinsic structural problems identified in Stage 3A.

### Machine-readable outputs

Stage 3 produces three machine-readable result files:

`experiments/phase1_diffsbdd/evaluation/structure_3a.csv`

Full ligand-intrinsic PoseBusters diagnostics and Stage 3A gate outcome.

`experiments/phase1_diffsbdd/evaluation/structure_3b.csv`

Full pocket-relative PoseBusters diagnostics and Stage 3B gate outcome.

`experiments/phase1_diffsbdd/evaluation/structure.csv`

Compact combined Stage 3 result containing:

- original molecule ID
- bond-length gate
- bond-angle gate
- internal steric-clash gate
- Stage 3A outcome
- protein-ligand clash gate
- Stage 3B outcome
- final Stage 3 outcome

The final file contains 18 unique molecule IDs, with 16 passing and 2 failing.

---

## Key Findings

- Stage 3 now provides a generator-independent 3D structural-plausibility evaluation interface.
- The generator's original coordinates are evaluated directly rather than replaced with RDKit-generated conformers.
- PoseBusters `0.6.5` is pinned so future comparisons use the same structural definitions and thresholds.
- The full PoseBusters output is preserved independently of the project's hard attrition gate.
- 16/18 Stage-2 survivors passed the Stage 3 ligand-intrinsic gate.
- Molecule 13 failed because of one short bond outlier.
- Molecule 16 failed bond-length, bond-angle, and internal steric-clash criteria.
- All 18 molecules passed the Stage 3B protein-ligand clash gate.
- The two final Stage 3 failures therefore reflect ligand-intrinsic geometry rather than protein-pocket clashes.
- The energy-ratio diagnostic failed for one structure, but this had no effect on attrition because energy was predeclared as diagnostic-only.
- Stage 3B receives an explicit prepared-pocket artifact rather than silently invoking DiffSBDD preprocessing.
- The 3RFM evaluation pocket contains 36 standard amino-acid residues selected using the documented `< 8.0 Å` reference-ligand rule.
- DiffSBDD-specific neural-network pocket representation remains outside the shared evaluator.
- Original molecule identifiers remain stable through all three cascade stages.
- Cumulative strict survival is now 16/20 (80%).

---

## Next Step

Stage 4 will evaluate novelty / chemical-space redundancy of the 16 molecules surviving Stage 3.

Before implementation, define:

- the reference chemical set against which novelty will be measured
- molecular representation / fingerprint choice
- similarity metric
- whether novelty is a hard attrition gate or primarily a ranked diagnostic
- thresholds, if any, before inspecting the 3RFM Stage 4 results

Stage 4 must continue to consume machine-readable outputs from the previous stage, preserve original molecule identifiers, and remain generator-independent so the identical analysis can later be applied to FLOWR.