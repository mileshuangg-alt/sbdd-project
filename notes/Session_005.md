 # Session 5 — 2026-08-13

**Approximate session duration:** TBD

## Objective

Implement Stage 3 of the generator-agnostic evaluation cascade: 3D / structural plausibility evaluation using PoseBusters.

Evaluate the original generated coordinates of the 18 Stage-2 survivors, preserve the full PoseBusters output, apply a predeclared structural-plausibility gate, and obtain the third attrition number for the 3RFM DiffSBDD baseline.

---

## Starting Point

The current cascade is:

| Stage | Entering | Surviving | Stage survival |
| --- | ---: | ---: | ---: |
| Generated | 20 | 20 | 100% |
| Stage 1 — chemical validity | 20 | 19 | 95% |
| Stage 2 — zero Rule-of-Five violations | 19 | 18 | 94.74% |

Cumulative strict survival through Stage 2:

**18/20 = 90%**

Stage 3 will evaluate these 18 surviving molecules.

---

## Stage 3 Architecture

Stage 3 is separated into two interfaces.

### Stage 3A — Ligand-intrinsic structural plausibility

Evaluate the generated ligand's original 3D geometry independently of the protein pocket.

### Stage 3B — Pocket-relative structural plausibility

Evaluate the generated ligand pose relative to an explicitly prepared protein pocket.

Pocket preparation must be represented as an explicit evaluation input rather than silently inheriting DiffSBDD-specific preprocessing assumptions.

Both stages must preserve the original generated coordinates.

No RDKit conformer regeneration or geometry optimization will be performed before evaluation.

---

## Predeclared Attrition Gate

The full PoseBusters suite will be run and preserved.

Stage 3 hard attrition will be determined only from:

- bond-length plausibility
- bond-angle plausibility
- steric-clash checks

The following will initially be retained as diagnostics rather than hard gate criteria:

- ring planarity
- double-bond geometry
- chirality
- energy-related checks
- other PoseBusters metrics not explicitly included in the hard gate

The hard gate is declared before examining the Stage 3 results.

Any future change to the Stage 3 attrition rule must be documented through a new versioned project decision.

---

## Reproducibility Requirements

- Pin the exact PoseBusters version.
- Verify API, check names, thresholds, and semantics against documentation for the pinned version.
- Record the PoseBusters version in project documentation.
- Preserve full raw PoseBusters results.
- Preserve original molecule IDs.
- Preserve original generated coordinates.
- Keep Stage 3A and Stage 3B results distinguishable.
- Make prepared-pocket provenance explicit.
- Contain no DiffSBDD-specific assumptions inside the shared structural evaluator.

---

## Today's Question

Of the 18 molecules surviving Stages 1 and 2, how many pass the predeclared Stage 3 structural-plausibility gate when evaluated using their original generated coordinates?

---

## Success Criteria

- [ ] Write D003 before inspecting Stage 3 results.
- [ ] Verify the PoseBusters release/API to use.
- [ ] Pin PoseBusters in `sbdd-eval`.
- [ ] Confirm the installed PoseBusters version.
- [ ] Map actual PoseBusters output names to the predeclared gate.
- [ ] Define the Stage 3A interface.
- [ ] Define the Stage 3B interface with explicit prepared-pocket input.
- [ ] Create `evaluation/structure.py`.
- [ ] Select the 18 Stage-2 survivors without renumbering them.
- [ ] Evaluate original generated coordinates.
- [ ] Preserve the full PoseBusters output.
- [ ] Apply only the predeclared hard gate.
- [ ] Produce molecule-level Stage 3 results.
- [ ] Calculate the third 3RFM attrition number.
- [ ] Document results and failure modes.
- [ ] Commit and push the completed Stage 3 implementation.

---

## Results

_To be completed during the session._

## Key Findings

_To be completed during the session._

## Next Step

_To be completed at the end of the session._