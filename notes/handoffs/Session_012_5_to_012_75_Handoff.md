# Session 012.75 Handoff - Continue from D017/P1 completion into D018

**Date prepared:** 2026-09-13  
**Purpose:** Start Session 012.75 without repeating Session 012.5 setup, D017 implementation, P1 homolog-pocket measurement, visualization, artifact discovery, or validation work.

## 0. Standing rule
The handoff is the audit. Start at the first execution step. Never propose inventory, verification, or requirements-mapping phases for anything this handoff marks frozen. Retrieve an artifact only when execution exposes a specific gap, and name the artifact plus the decision it unblocks.

## 1. Critical boundary
Session 012.5 closed the first quantitative sub-arm of the Stage-5 Level-2 target arm: D017 P1 homolog-pocket characterization/correspondence measurement.

The bounded claim is:

> For D017 calibration row P1, the experimentally ligand-defined homolog pocket in 6D9H chain R contains 14 residues; all 14 map to target residues in 2YDV chain A under the frozen US-align correspondence; 13/14 mapped pairs are sequence-identical; mapping coverage is 1.0; pocket sequence identity is 13/14 = 0.9285714285714286; and the mapped-pocket local C-alpha RMSD after optimal proper rigid-body superposition is 0.4398073045565676 Å.

This does **not** establish `pocket_conserved` and does **not** establish the full Level-2 target-arm verdict. D018 remains the next methodology layer for interpreting these measurements. Do not reopen or tune D017 measurement definitions merely because D018 is now being discussed.

## 2. What Session 012.5 achieved

### D017 scientific core completed
Implemented and reviewed `evaluation/d017_homolog_pocket.py` function-by-function, with scientific tests after each major function:

- exact deposited ligand-instance selection (`ADN R 400`)
- heavy-atom selection
- homolog receptor heavy-atom selection
- Euclidean atom-atom distance measurement
- frozen 4.5 Å homolog-pocket residue definition
- minimum-distance atom-pair evidence per pocket residue
- mapping homolog-pocket residues through frozen US-align correspondence
- mapping coverage calculation
- pocket sequence identity calculation
- C-alpha coordinate lookup
- optimal proper rigid-body superposition (Kabsch-style)
- RMSD calculation
- integrated P1 pocket RMSD calculation
- assembly of the complete D017 measurement result
- provenance/artifact assembly for serialization

The scientific-core tests and integration tests were green; the full suite reached 47/47 after the homolog-pocket test file was added, and later full-suite runs remained green after visualization changes.

### P1 measured results
- Total homolog-pocket residues: 14
- Mapped homolog-pocket residues: 14
- Unmapped homolog-pocket residues: 0
- Mapping coverage: 1.0
- Identical mapped residue pairs: 13
- Pocket sequence identity: 0.9285714285714286
- Pocket superposition RMSD: 0.4398073045565676 Å
- Only non-identical mapped pocket pair: homolog R277 THR -> target A277 SER

### Pocket-distance evidence retained
Minimum qualifying heavy-atom distance evidence was retained for all 14 pocket residues. The largest retained qualifying minimum-distance contact was approximately 4.42871188947757 Å for R247 TRP, still inside the frozen 4.5 Å cutoff.

### D017 artifact completed
Persisted:
`references/stage5/d017/calibration_runs/P1/post_emitter_fix/pocket_measurement.json`

The artifact contains:
- target/homolog identities and SHA-256 hashes
- exact ligand identity (`ADN R 400`)
- frozen pocket definition (`4.5 Å`, heavy atoms, experimentally bound homolog ligand)
- US-align stdout/config paths and hashes
- total/mapped/unmapped residue counts
- explicit `unmapped_pocket_residues` (empty for P1)
- mapping coverage
- pocket sequence identity
- pocket RMSD
- explicit pocket residue list
- atom-level pocket-distance evidence
- mapped pocket residue correspondence
- local superposition rotation/translation and C-alpha coordinate sets

### Visualization completed
Required D017 human-review artifacts were retained, including:
- raw US-align superposition CIF/PML artifacts
- whole-structure review image/PML
- tighter pocket-focused review image/PML
- additional whole-protein-with-ligand-and-pocket-highlight review image/PML

Visualization is review-only and non-gating. It does not define residue correspondence, pocket membership, sequence identity, RMSD, or any conservation verdict.

### Refactor completed
The Session-012.5 consistency refactor standardized the shared `ResidueID` model so `number` is a string across the relevant code paths. Existing P2Rank code was continued through the refactor rather than reverted. The D017 scientific core and related shared residue model now use the established shared representation.

## 3. Frozen archive

D017 retained evidence is under:
`references/stage5/d017/`

Important P1 run directory:
`references/stage5/d017/calibration_runs/P1/post_emitter_fix/`

Important artifacts include:
- `pocket_measurement.json`
- `correspondence.json`
- `usalign_superposition.cif`
- `usalign_superposition.pml`
- `whole_structure_review.pml`
- `whole_structure_review.png`
- `pocket_review.pml`
- `pocket_review.png`
- `whole_protein_pocket_review.pml`
- `whole_protein_pocket_review.png`
- raw US-align stdout/matrix and related scripts

Preserve intermediate and failed validation artifacts; do not delete merely because they are not expected to be used in the final pipeline.

## 4. Documentation completed

- D017 methodology/decision documentation updated in `notes/Decisions.md`.
- D017 visualization requirements and raw-artifact retention were preserved.
- The function-by-function scientific-core workflow and script-level summary were completed in chat.

## 5. Git state

Local branch: `main`

D017 checkpoint commit:
`cb77507` — `Complete D017 homolog pocket characterization`

The commit contains the D017 implementation, shared residue-model/P2Rank refactor, P1 D017 artifacts, tests, and D017 visualization artifacts.

At the last confirmed status after the commit, the remaining unstaged/untracked work was separate from this D017 checkpoint:
- `evaluation/stage5.py`
- `evaluation/plip_witness.py`
- `local_dock_debug/`
- `notes/Development.md`
- `notes/handoffs/Session_012_Handoff.md`
- handoff-template files
- `references/stage5/dock385/...`
- `references/stage5/plip_witness/`
- `references/stage5/target_configs/`
- `scripts/stage5/run_plip_witness_concordance.py`
- `scripts/stage5/summarize_plip_witness.py`
- `tests/test_plip_witness.py`
- `tests/test_stage5_router.py`

The user then intended to push `main`, but no successful `git push` output was provided in-chat. **Do not claim the remote contains `cb77507` until a successful push is actually confirmed.**

## 6. Environments

Local repo:
`/Users/mileshuang/Desktop/sbdd-project`

Conda environment:
`sbdd-eval`

Current local workflow uses terminal commands for mechanical refactors/plumbing and collaborative function-by-function authoring for scientific core.

For UCSF gpu-dev1 access when needed:
`ssh mhuang8@facbastp9004.fac.ucsf.edu`
then
`ssh gpu-dev1.ic.fac.ucsf.edu`

Authentication remains interactive; never store passwords, MFA codes, or credentials.

## 7. Decisions now in force

### D017 — frozen quantitative homolog-pocket characterization
D017 uses the deposited homolog ligand to define the homolog pocket by heavy-atom distance at the frozen 4.5 Å cutoff. The quantitative outputs are:
- total homolog pocket residues
- mapped/unmapped pocket residues
- mapping coverage
- identical mapped residue pairs
- `pocket_sequence_identity`
- `pocket_superposition_rmsd`

Coverage must be reported jointly with sequence identity and RMSD.

D017 does not assign `pocket_conserved`.

### Review rendering
Frozen review renderer: PyMOL 3.1.0. Review artifacts are non-gating and downstream of the exact-coordinate alignment input.

### Shared model/refactor
Use the established shared `ResidueID` model. Do not reintroduce duplicate residue-identity classes when the shared model already fits the scientific role.

### Stage-5 target-side scope
P2Rank/fpocket remain target-side under the verdict arm. They are separate from the completed D017 ligand-defined homolog-pocket measurement arm.

## 8. Claim authority

Authorized:
- D017 P1 quantitative homolog-pocket characterization as measured above.
- Human review of the retained superposition/pocket images.

Prohibited:
- Saying D017/P1 alone proves the homolog pocket is conserved.
- Using rendered images to alter or rescue quantitative measurements.
- Treating D017 measurements as the final Level-2 target verdict.
- Replacing the frozen D017 measurement definition with a convenience visualization or an implementation-specific threshold.

Retention defects on record:
- None currently known for the completed P1 quantitative artifact.

## 9. Do NOT reopen

- Do not reopen the frozen D017 4.5 Å heavy-atom pocket definition.
- Do not retune P1 sequence identity or RMSD calculations.
- Do not reopen the validated Kabsch/superposition implementation.
- Do not replace the shared `ResidueID` model again.
- Do not treat PyMOL styling/camera as scientific methodology.
- Do not reopen the completed Graves/DOCK null ladder from Session 010.
- Do not reopen the frozen Stage-5 ProLIF reader decision.
- Do not introduce FLOWR into Stage-5 validation evidence before the frozen POD.

## 10. Session 012.75 starting point

**Start at D018 methodology work.**

The first authorized operation is to identify the already-frozen D018 decision/framework text that governs how D017's measurements become a conservation/verdict label. Do not remeasure P1 first.

The key question is:
> What exact frozen D018 rule determines whether the measured homolog pocket is `pocket_conserved`, given mapping coverage, pocket sequence identity, and local pocket C-alpha RMSD?

Before introducing any new threshold, test, or validation requirement, trace it to the frozen framework/session plan. If it is not already frozen, label it as a proposed new requirement and obtain user approval before making it mandatory.

## 11. Process rules in force

- Validation-requirement rule: trace to frozen framework, label anything new as proposed, user approval before mandatory.
- Alternatives-pass rule: whenever considering a new model/package/scoring function/reader/generator/software component, enumerate serious cited alternatives, assess what each enables, compute/dependency/scope cost, and trace rejection to an existing requirement; label alternatives unrejected if no specific rejection exists.
- Approval protocol: decisions and framework edits are drafted, shown, and approved by the user before being written.
- Scientific-core workflow: function-by-function; for each function provide pasteable implementation, explain scientific purpose and downstream role, state exact/qualitative test expectations and failure criteria, then give a complete terminal-wrapped runnable check. Reuse existing shared parsers/models.
- After each scientific-core script, provide a script-level summary covering each function, its contribution, its scientific context, and the script's role in the current frozen stage.
- Keep target-specific constants out of generic scripts; target-specific definitions belong in frozen config/artifact files.
- Implementation assistants are for plumbing/mechanical work only; scientifically consequential methodology remains authored/reviewed collaboratively in-chat.

## 12. Preservation rule

Retain all D017/P1 intermediate and validation artifacts, including failed rendering attempts and diagnostics, until the relevant Stage-5 work is formally finalized and frozen. Do not delete failed branches just because a later artifact is correct.

---

# Session 012.75 start prompt

Resume the SBDD project exactly from `cb77507`, which is the completed D017/P1 homolog-pocket characterization checkpoint. Do not redo D017 setup, artifact discovery, P1 measurement, visualization, or refactoring. D017/P1 is already complete and frozen as a quantitative measurement arm, not a conservation verdict.

Start with D018. Locate the frozen D018 framework/decision text already present in the project and determine the exact rule, thresholds, or logic governing how D017's three core measurements—mapping coverage, pocket sequence identity, and pocket superposition RMSD—are interpreted into the `pocket_conserved`/Level-2 target-arm verdict. Do not invent or make any new requirement mandatory unless it is already frozen; if a proposed addition is scientifically useful but not frozen, label it proposed and get my approval first.

Remember the current P1 measurements exactly: 14 total homolog-pocket residues; 14 mapped; 0 unmapped; coverage 1.0; 13 identical mapped pairs; pocket sequence identity 0.9285714285714286; pocket superposition RMSD 0.4398073045565676 Å; only R277 THR -> A277 SER is non-identical. The full measurement artifact is at `references/stage5/d017/calibration_runs/P1/post_emitter_fix/pocket_measurement.json` and the D017 implementation is in `evaluation/d017_homolog_pocket.py`.

Use the current scientific-core workflow if code is needed: function-by-function, pasteable implementation, scientific explanation, explicit test expectation/failure criteria, then a complete terminal-wrapped check. Reuse existing models/parsers and do not make me rediscover project details already present in this handoff.
