# Session 016 — ADMET Preparation and Split-Representation Qualification

**Date:** 2026-11-05 to 2026-11-11  
**Status:** CLOSED FOR HANDOFF — preparation and split-representation qualification complete; production split not yet built

## 1. Session objective

Session 016 began the ADMET workstream after Stage 6 was intentionally paused at D030 Test D.

The governing pilot plan requires, in order: environment qualification; pKa and human-hepatocyte-clearance preparation; construction and freezing of the shared 80/20 development/test split and five-fold development CV; then metric qualification, masked-output checks, smoke timing, runtime projection, and the bounded CoreHPC pilot.

This session completed the endpoint-preparation and split-representation work needed to proceed toward the real split. It did **not** complete Task 2 because no production split assignment has yet been generated or frozen.

---

## 2. Prepared ADMET endpoints

The pKa endpoint was prepared from IUPAC Dissociation Constants v2.4a under the settled Session-016 eligibility rules.

The corrected prepared population is:

- 6,752 molecule-steps
- 5,474 source-ID compounds
- 523 compounds with both acid and base labels
- base steps 1–5: 3,153 / 265 / 34 / 8 / 2
- acid steps 1–6: 2,641 / 501 / 100 / 38 / 8 / 2

Prepared artifact:

`admet/data/prepared/pka_v2.4a_session016.csv`

The human-hepatocyte clearance endpoint uses the owner-verified ChEMBL assay-record population rather than the mixed-species TDC hepatocyte file.

Prepared population:

- 408 molecular identities

Prepared artifact:

`admet/data/prepared/human_hepa_408_session016.csv`

Model inputs remain the source-recorded SMILES. Grouping representations do not replace or rewrite model inputs.

---

## 3. Alias-grouping qualification

The approved grouping implementation is:

`admet/scripts/alias_grouping.py`

Grouping behavior is pinned to RDKit 2023.09.6.

The combined prepared population contains:

- pKa identities: 5,474
- clearance identities: 408
- combined endpoint-qualified identities: 5,882

The authoritative alias-edge diagnostic reproduced exactly:

- 5,881 successfully grouped identities
- 1 explicit grouping failure
- 5,446 distinct family keys
- 893 distinct scaffold keys
- 4,885 identities with scaffold keys
- 996 ring-free/no-scaffold notes
- 20 cross-endpoint components
- 1,740 diagnostic scaffold-plus-family connected components
- largest diagnostic component: 1,315 identities

The single explicit failure is `clearance:CHEMBL5315124`, caused by `fragment_ambiguity_equal_largest_heavy_atom_count`. The source record is preserved and no fragment/group is guessed.

Tautomer witness status across the 5,881 successfully keyed identities was:

- Completed: 5,876
- MaxTransformsReached: 5

`MaxTransformsReached` remains diagnostic evidence and is not automatically an exclusion or grouping failure.

The diagnostic produced and hash-verified:

- `identities.csv`
- `components.csv`
- `component_summary.csv`
- `key_memberships.csv`
- `grouping_failures.csv`
- `tautomer_status.csv`
- `run_metadata.json`
- `run.log`
- `SHA256SUMS.txt`

The very large transitive scaffold-plus-family components motivated further split-representation investigation; they are not themselves a frozen production split.

---

## 4. Literal DataSAIL/CVXPY scaling investigation

DataSAIL v1.2.4 was audited at commit:

`a212606c4ad9d847ff94365545392958c2aab7f5`

The investigated implementation used CVXPY 1.5.3 with SCIP/PySCIPOpt.

A bounded synthetic probe preserved the approved uncoarsened scientific problem while avoiding real molecular similarities and real split assignments.

### P0 — 100 synthetic families

The original 300-second P0 reached the SCIP time limit and was preserved unchanged.

A corrected-instrumentation follow-up used:

- SCIP optimization allowance: 1,800 seconds
- external process cap: 1,860 seconds

These were engineering allowances, not scientific thresholds. No further P0 timeout escalation was authorized.

### P1 — 500 synthetic families

P1 used:

- SCIP optimization allowance: 600 seconds
- external process cap: 660 seconds

Measured representation costs were:

- construction: 79.994 s; peak RSS 737,771,520 bytes
- canonicalization: 256.713 s; peak RSS 6,795,390,976 bytes
- solve: 629.266 s; peak RSS 7,993,204,736 bytes

Native SCIP returned:

- status: `timelimit`
- incumbent present: yes
- solution count: 2
- node count: 2
- primal bound: 53,588.79441039555
- dual bound: 11.209536550548242
- gap: 4,779.643175455332

The incumbent remains solver-reported feasible; independent frozen hard-constraint validation is pending. The large gap is a weak optimality certificate, not evidence that the assignment itself is poor.

P0/P1 timing comparisons are cross-host observations, not controlled size-only scaling measurements.

The bounded DataSAIL scaling probe was closed at P1. No P2 was run.

**Conclusion:** the literal uncoarsened CVXPY representation remained executable at 500 synthetic families, but its measured representation costs justified investigating a more direct formulation. This does not establish that larger instances are impossible or infeasible.

---

## 5. Native binary-quadratic representation

The approved leakage objective was rewritten exactly, without coarsening or approximation.

For each unordered family pair:

`c_ij = w_i × w_j × S_ij`

Minimizing total cross-partition leakage is algebraically equivalent to maximizing the corresponding within-partition weighted similarity because total pair weight is constant.

The native formulation preserves:

- immutable families
- exact molecular-count weights
- numeric pKa and clearance counts
- complete pairwise similarities
- the approved Stage-A and Stage-B hard constraints

It introduces no pair pruning, additional coarsening, similarity approximation, overflow rule, or silent tolerance change.

Gurobi 14.0.0 with Academic WLS was qualified on gpu-dev1 under Python 3.12.16. SCIP remains the fallback backend.

---

## 6. Exact equivalence qualification

### Stage A

A four-family/two-partition fixture was exhaustively evaluated over all 16 assignments before optimizer use.

The native model contained exactly:

- 8 binary variables
- 16 linear constraints
- 12 quadratic objective terms

Every quadratic coefficient was independently verified as `w_i × w_j × S_ij`, and every linear constraint was checked against the independent specification.

Gurobi subsequently returned an independently feasible assignment matching the exhaustive optimum.

### Stage B

A five-family/five-fold fixture was exhaustively evaluated over all 3,125 assignments.

Observed:

- feasible assignments: 1,140
- infeasible assignments: 1,985
- best reference leakage: 119.20999999999998
- tied minimizing assignments: 60

The native model contained exactly:

- 25 binary variables
- 35 linear constraints
- 50 quadratic terms

All coefficients and constraints matched the independent specification. Gurobi returned an independently feasible member of the exhaustive minimizing set.

The toy fixture bounds have no production authority.

---

## 7. Native construction-cost qualification

A construction-only harness was built around the qualified formulation. It does not call `optimize()`.

At N=100:

- 200 binary variables
- 112 linear constraints
- 9,900 quadratic terms
- elapsed: 0.344884 s
- peak RSS: 35,098,624 bytes
- solution count: 0

At N=500:

- 1,000 binary variables
- 512 linear constraints
- 249,500 quadratic terms
- elapsed: 1.077300 s
- peak RSS: 83,038,208 bytes
- solution count: 0

These measurements were made on gpu-dev1. The DataSAIL measurements were made on different hardware, so no controlled numerical speedup or memory-reduction ratio is claimed.

The supported engineering conclusion is that the native representation removed the measured front-end representation bottleneck at the qualified N=100 and N=500 synthetic sizes.

This does **not** establish production optimization performance or full-scale feasibility.

Qualification artifacts:

- `admet/qualification/native_quadratic/equivalence.py`
- `admet/qualification/native_quadratic/construction_probe.py`
- `admet/qualification/native_quadratic/artifacts/session016_native_quadratic_qualification.json`
- `admet/qualification/native_quadratic/artifacts/SHA256SUMS.txt`

The closed DataSAIL investigation is preserved under:

`admet/qualification/datasail_scaling/`

---

## 8. Session claim boundary

Session 016 establishes:

- prepared pKa and human-hepatocyte-clearance endpoint artifacts
- RDKit-pinned alias-grouping implementation and diagnostic evidence
- explicit preservation of grouping failures and tautomer-status flags
- bounded characterization and closure of the literal DataSAIL/CVXPY scaling route
- exact native binary-quadratic reformulation
- exhaustive tiny Stage-A and Stage-B equivalence
- Gurobi backend qualification
- N=100 and N=500 native construction qualification

Session 016 does **not** establish:

- a frozen production 80/20 development/test split
- a frozen five-fold development CV
- production Gurobi optimization performance
- global optimality of a production assignment
- constrained-random leakage quality
- custom clearance metric qualification
- pKa masked-output qualification
- Chemprop timing or the 16-fit CoreHPC pilot
- model selection or test-set performance

---

## 9. Do not reopen

Unless an explicit revisit condition is triggered, do not reopen:

- source-recorded SMILES as model inputs
- RDKit 2023.09.6 grouping behavior
- approved alias failure handling
- Session-016 pKa preparation policy
- owner-verified human-hepatocyte endpoint selection
- authoritative alias diagnostic counts
- bounded DataSAIL scaling probe through P1
- decision not to run P2 merely for another timeout
- native binary-quadratic objective identity
- Stage-A and Stage-B tiny equivalence qualification
- Gurobi 14.0.0 qualification on gpu-dev1
- N=100/N=500 native construction qualification

The constrained-random comparison protocol remains open.

---

## 10. Session close and resume point

**Status:** CLOSED FOR HANDOFF

The original implementation plan remains authoritative.

Task 2 is **not complete** because the real production split has not yet been generated and frozen.

Session 017 therefore resumes at:

> **Task 2 — build and freeze the shared 80/20 development/test split and five-fold development CV under the approved grouping and split methodology.**

The immediate work is to construct the real family-level split inputs, preserve the explicit grouping failure and diagnostic flags, construct the real complete similarity objective and numeric endpoint constraints, run the qualified formulation, independently validate any returned assignment, and freeze the resulting split/CV.

Do not advance to Task 3 until Task 2 is frozen.

Stage 6 remains separately paused at D030 Test D.
