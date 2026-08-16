# Session 6 — 2026-08-15

**Approximate session duration:** TBD

## Objective

Implement Stage 4 of the generator-agnostic evaluation cascade: novelty and chemical-space redundancy characterization.

Stage 4 will characterize the 16 molecules that survived Stage 3 using molecular similarity metrics without removing molecules from the cascade.

The stage will distinguish between:

- internal similarity / redundancy among generated molecules
- external similarity / novelty relative to a predefined reference chemical set

Stage 4 is explicitly non-attritional.

All 16 Stage-3 survivors will proceed to subsequent stages regardless of their Stage 4 similarity scores.

---

## Starting Point

The current strict cascade is:

| Stage | Entering | Surviving | Stage survival |
| --- | ---: | ---: | ---: |
| Generated | 20 | 20 | 100% |
| Stage 1 — chemical validity | 20 | 19 | 95% |
| Stage 2 — zero Rule-of-Five violations | 19 | 18 | 94.74% |
| Stage 3 — 3D structural plausibility | 18 | 16 | 88.89% |

Cumulative strict survival through Stage 3:

**16/20 = 80%**

Stage 4 will characterize these 16 surviving molecules.

Because Stage 4 is non-attritional, cumulative strict survival will remain **16/20 = 80%** after Stage 4.

---

## Stage 4 Architecture

Stage 4 is separated into two complementary analyses.

### Stage 4A — Internal similarity / redundancy

Evaluate structural similarity among the 16 generated Stage-3 survivors.

For each molecule, retain information such as:

- nearest generated neighbor
- nearest-neighbor similarity
- pairwise similarity information
- internal redundancy / diversity diagnostics

This analysis asks whether the generator produced chemically diverse molecules or multiple closely related variants of the same chemistry.

### Stage 4B — External similarity / novelty

Evaluate each Stage-3 survivor against a predefined external reference chemical set.

For each generated molecule, retain:

- nearest reference molecule
- nearest-reference similarity
- reference molecule identity / provenance
- additional similarity diagnostics where useful

This analysis asks how similar the generated chemistry is to already-known chemistry represented by the selected reference set.

---

## Stage 4 Interpretation

Stage 4 will not use a hard novelty gate.

No molecule will be removed solely because it is highly similar or dissimilar to another molecule.

Novelty is not assumed to be monotonically beneficial.

High similarity to known chemistry may indicate:

- redundancy
- limited chemical novelty
- similarity to established medicinal-chemistry space
- potentially useful similarity to known active chemistry

Low similarity may indicate:

- greater chemical novelty
- exploration of new chemical space
- greater uncertainty because the molecule lies farther from established chemistry

Similarity will therefore be retained as a continuous characterization and ranking feature rather than converted into a binary pass/fail decision.

---

## Initial Similarity Method

The initial molecular-similarity baseline will use:

- RDKit molecular fingerprints
- Morgan fingerprints
- Tanimoto similarity

The exact fingerprint parameters must be declared before Stage 4 results are inspected.

The implementation must preserve the fingerprint definition and similarity metric explicitly so that DiffSBDD and FLOWR can later be compared using the identical method.

---

## External Reference Set

The Stage 4B external reference set must be defined before external similarity results are inspected.

Possible reference-set interpretations answer different scientific questions:

- similarity to approved / known drugs
- similarity to broader known bioactive chemistry
- similarity to known ligands for a specific target
- similarity to the generator's training distribution

The reference set used for the Phase 1 3RFM baseline must therefore be selected based on the scientific claim Stage 4 is intended to support.

Target-specific ligand similarity should remain distinguishable from general chemical novelty.

---

## Non-Attritional Rule

Stage 4 is a characterization stage rather than an attrition stage.

Therefore:

`stage4_entering = 16`

and:

`stage4_leaving = 16`

There will be no `stage4_passes` filter in the current implementation.

Similarity scores may later contribute to candidate ranking or multi-objective prioritization, but they will not independently determine cascade survival.

Any future conversion of Stage 4 into an attrition gate would require a new versioned project decision declared before inspecting affected results.

---

## Reproducibility Requirements

- Consume the machine-readable Stage 3 output.
- Select only molecules with `stage3_passes=True`.
- Preserve original zero-based `molecule_id` values.
- Do not renumber surviving molecules.
- Use a predefined fingerprint representation.
- Use a predefined similarity metric.
- Record fingerprint parameters explicitly.
- Define the external reference set before inspecting external similarity outcomes.
- Preserve nearest-neighbor identities and similarity values.
- Keep internal redundancy and external novelty conceptually separate.
- Produce machine-readable Stage 4 outputs.
- Contain no DiffSBDD-specific assumptions inside the shared novelty evaluator.
- Ensure the identical Stage 4 implementation can later be applied to FLOWR.

---

## Today's Questions

### Stage 4A

How structurally redundant or diverse are the 16 molecules that survived Stage 3?

### Stage 4B

How similar are those molecules to chemistry in the predefined external reference set?

### Overall

What additional ranking information does Stage 4 provide without changing the current strict cascade survival of 16/20?

---

## Success Criteria

- [ ] Predeclare Stage 4 as non-attritional before inspecting similarity results.
- [ ] Define the Morgan fingerprint parameters.
- [ ] Define Tanimoto similarity as the baseline similarity metric.
- [ ] Define the Stage 4B external reference set and its scientific interpretation.
- [ ] Define the Stage 4A internal-similarity interface.
- [ ] Define the Stage 4B external-similarity interface.
- [ ] Create `evaluation/novelty.py`.
- [ ] Select the 16 Stage-3 survivors without renumbering them.
- [ ] Calculate internal pairwise similarity.
- [ ] Preserve nearest generated-neighbor identity and similarity.
- [ ] Calculate external-reference similarity.
- [ ] Preserve nearest external-reference identity and similarity.
- [ ] Produce machine-readable Stage 4 results.
- [ ] Confirm that Stage 4 causes zero cascade attrition.
- [ ] Document similarity distributions and notable redundancy / novelty patterns.
- [ ] Update project documentation.
- [ ] Commit and push the completed Stage 4 implementation.

---

## Results

_To be completed during the session._

## Key Findings

_To be completed during the session._

## Next Step

_To be completed at the end of the session._