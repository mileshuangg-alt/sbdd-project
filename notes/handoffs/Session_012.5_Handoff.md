# Session 012.5 Handoff - Continue D017 Level-2 homolog correspondence execution

**Date prepared:** 2026-09-11
**Purpose:** Continue Session 012 in a fresh chat without repeating D015-D017 decisions, US-align qualification, calibration-structure selection, construct auditing, receptor preparation, provenance work, or the failed first P1 parse attempt.

## 0. Standing rule
The handoff is the audit. Start at the first execution step. Never propose inventory, verification, or requirements-mapping phases for anything this handoff marks frozen. Retrieve an artifact only when execution exposes a specific gap, and name the artifact plus the decision it unblocks.

Session 012 is NOT closed. Session 012.5 is the chat continuation.

## 1. Critical boundary
D016 binding labels are frozen. D017 structure selection, state/species handling, US-align method, construct handling, canonical position-only receptor extraction, exact-coordinate mmCIF input representation, mutation provenance, and the calibration structure manifest are frozen.

The first attempted P1 US-align execution DID NOT perform an alignment. US-align 20220227 failed while parsing `references/stage5/d017/receptor_inputs/2YDV_A.cif` because the derived mmCIF `_atom_site` schema was incomplete. US-align nevertheless returned shell exit code 0, so exit status alone MUST NOT be treated as evidence of success.

> Seven exact-coordinate receptor inputs have been deterministically derived using position-only canonical mapping, with engineered/noncanonical coordinates excluded and deposited mutations retained and provenance-flagged. The construct and mutation provenance has been audited before alignment. This establishes reproducible candidate receptor inputs for D017, but the emitted derived mmCIF schema is not yet US-align-compatible. No successful D017 calibration alignment has occurred, and no pocket sequence identity, mapping coverage, pocket RMSD, conservation threshold, or `pocket_conserved` classification has been established.

D018 remains unopened for threshold selection.

## 2. What Session 012 achieved

### D015
D015 freezes P2Rank as the Level-3 predicted-pocket characterization method. It does not establish target-ligand interaction evidence, compatibility, a Level-3 upgrade, or a Stage-5 interaction gate.

### D016
Frozen global Ki gates:
- `<50 nM` = POSITIVE
- `50-100 nM` = MIDDLE / probe-only
- `>100 nM` = NEGATIVE

N=50 nM; M=100 nM. The frozen affinity dataset has 13 adopted entries. Reference cell: 7 positive / 5 negative / 1 middle; 12/13 graded = 92.3%. The earlier reconstructed NECA 14/20/25 grid was caught and superseded.

### D017
Frozen Level-2 homolog-pocket measurement procedure:
- US-align 20220227.
- Homolog pocket = residues with any heavy atom within 4.5 A of any deposited homolog-ligand heavy atom.
- `pocket_sequence_identity = identical mapped pocket-residue pairs / total mapped pocket-residue pairs`.
- `mapping_coverage = mapped homolog pocket residues / total homolog pocket residues`.
- `pocket_superposition_rmsd` = C-alpha RMSD after optimal LOCAL superposition of mapped pocket C-alpha pairs.
- State and species provenance mandatory.
- `pocket_conserved = UNEVALUABLE` until D018.
- No executable defaults for sequence identity, RMSD, mapped-residue count, or coverage.

All D-number decisions must have Status near the top and end with `### Revisit when`; no redundant bottom Status section.

### US-align qualification
Executable:
`/Users/mileshuang/tools/usalign_20220227/USalign-master/USalign`

Version: `20220227`

Hashes:
- source archive: `3c6348e7d45105ade2f0fe80437a36b4e7bfdb92cdb6872a6f4912dcd24d0f8d`
- `USalign.cpp`: `4518d1e85bfccea3ff40de8fbf0b248faf8ebe4695d0d8b6f15f3625593c4427`
- executable: `26ba8b626cf2600321941f0a138ada60505626e858948b5285c66f33097ee55f`

Bundled smoke test succeeded: aligned length 119, global RMSD 2.20 A, aligned sequence identity 0.824, transformation matrix and `-o` artifacts produced. This was software qualification only.

### Visualization
PyMOL 3.1.0 is installed in `sbdd-eval`. Raw US-align rendering worked but occluded the structures. A better review-only recipe was visually qualified using blue ~55% transparent structure 1, red ~20% transparent structure 2, white background, shadows off, and ray-traced PNG. D017 requires raw visualization plus separate whole-structure and pocket-focused review images. Visualization is non-gating.

### D017 configs
Historical config:
`references/stage5/d017/usalign_20220227_config.json`
SHA-256: `c4420efec72ca257d5c13c786fa90bcd435c0aa2a410ea06438fc383df68fa23`

It used `single_chain_pdb` and is superseded.

Active config:
`references/stage5/d017/usalign_20220227_config_v2.json`
SHA-256: `6b98a09dcdc103a9c86aa640bc68a72e1685528ff7b5848df326048a99b2d6e6`

Active input contract: `single_chain_pdbx_mmcif`, because exact deposited coordinates must not be rounded into fixed-width PDB fields.

Materialization log:
`references/stage5/d017/materialization_20260910.txt`
SHA-256: `07e4e115d9fd81c4d4bdb520f87956edf000e3e8bbf342df24600750261c91b3`

### Structure selection
8YH0/8YH2 were excluded after verification as *Ovis aries*. Proxy rule permits same-pharmacological-class proxies when exact ligand-bound homolog structure is unavailable and state matching is provided.

Frozen manifest:
`references/stage5/d017/calibration_structure_manifest.json`
SHA-256: `f3b477b23c0505845367cb28383ca024e5692ec8a13f2696de3c04fef8b77b5d`

Rows:
- P1: 2YDV A -> 6D9H R; NECA A2A -> A1; active/active; human/human; homolog adenosine agonist proxy.
- P3: 2YDV A -> 9EBH R; NECA A2A -> A3; active/active; human/human; homolog adenosine agonist proxy.
- N1: 2YDV A -> 6D9H R; CCPA A2A -> A1; active/active; human/human; structural agonist proxies.
- N2: 4UG2 A -> 7XY7 R; CGS21680 A2A -> A2B; active/active; human/human; exact target ligand and NECA homolog proxy.
- N3: 3EML A -> 9EHS R; ZM241385 A2A -> A3; inactive/inactive; human/human; exact target ligand and LUF7602 antagonist proxy.

4UG2 A/B tie-break: lexicographically first author chain; chain A selected.

### Raw authoritative structures
`references/stage5/d017/structures/raw/`

Hashes:
- 2YDV `6957703aa88ede652c5e9d8850193c7ccd4348e7c54fe34f7f2867b1a8ec664f`
- 3EML `fc5e7cadd3951548025a382db1cd5e0b64aadfa2f160fe3436bf1f4ed840a888`
- 4UG2 `9ecdc696aad3d696fc0b07a289bd7e002749944530f2289a75a26aba3866900d`
- 6D9H `3dd17aedba2a046926ee911e06897ba03e21f64456e7b009dbed3ae49d506f22`
- 7XY7 `201b24bd4d51109567cb2f5e7052cd57f608d025bbaf41b7aa24ac44880d09f9`
- 9EBH `5c5395581e7de6af5a10b145d54494b90460e2f0300cce42c93b927040353844`
- 9EHS `70d760c7035663ef53c8d3c78801cb224db76d5ee89af40e8950bd114f7e1474`

### Canonical FASTAs
`references/stage5/d017/canonical_sequences/`

- ADORA1/P30542 `b737a73f9d6c134d0df89ce558deb1e72b84309df0967db13675b7205dfc2c89`
- ADORA2A/P29274 `fa327e00c2245b9aa5aa65816f078bdd5664de1531fb8404c2b5f60d8e96f239`
- ADORA2B/P29275 `4a6c391c07cdd34d0050367c9312638f37a74fa2215f1a01fb7dc63073c15b77`
- ADORA3/P0DMS8 `b117a029664c0025d6b833df72fef925dbd4f70936ee9a04ec09254edd59af92`

### Construct audit and receptor extraction
Audit code:
- `evaluation/d017_construct_audit.py`
- `scripts/stage5/audit_d017_construct_boundaries.py`
- `references/stage5/d017/construct_boundary_audit_selection.json`
- `references/stage5/d017/construct_boundary_audit.json`
- `tests/test_d017_construct_audit.py`

Initial construct results:
- 3EML A: 288 canonical-mapped / 160 noncanonical
- 7XY7 R: 283 / 0
- 9EHS R: 197 / 170

Frozen extraction rule: canonical mapping is POSITION-ONLY. Unique canonical position -> retain coordinate-bearing deposited residue. Identity mismatch -> retain and mutation-flag. No canonical position -> exclude from alignment input while preserving raw source.

Extraction implementation:
- `evaluation/d017_receptor_input.py`
- `scripts/stage5/materialize_d017_receptor_inputs.py`
- `references/stage5/d017/receptor_input_materialization.json`

Aggregate mapping:
`references/stage5/d017/receptor_inputs/position_only_mapping.json`
SHA-256: `f63dc90146de8e53346ad418644dcb615223fa1d883141ab50bdf48b17f9bdc8`

Current derived inputs and hashes:
- 2YDV_A.cif `dace42b649c00b273636a62337f26d3cfed0b48ce0d06255c00bb6ab9ea33a87` — 307 retained / 8 excluded / 5 mutations
- 3EML_A.cif `d1bac103e1b1f42ed821f8f094f3032131c99c1fcc838304d54304b07a27161f` — 288 / 160 / 0
- 4UG2_A.cif `083f3311262c8945870d40d8c13fb64875fec9d487327e3120d6d1f6d979b3dd` — 292 / 0 / 5
- 6D9H_R.cif `50f64239555e2fbc5cfe512c6076998e2539b385867002a0e4e9c6236399e96a` — 288 / 0 / 0
- 7XY7_R.cif `611b8ce6c91387f402aac1caf821bd4d466a19fcddaede18742ad244a8cc96cf` — 283 / 0 / 0
- 9EBH_R.cif `b51530d6873ef43cc83beb48626bad3976afa049d06245c3abaed88a5636aa8b` — 266 / 0 / 0
- 9EHS_R.cif `a2d7c6a874e158e36b1c89038d836218e51caeca66ebb42b55bbfca58b8800d3` — 197 / 170 / 2

IMPORTANT: these current derived mmCIF hashes are NOT final runnable-input hashes because the emitted schema is not US-align-compatible. Preserve them as diagnostic artifacts; regenerated hashes will change after the emitter fix.

The parser supports both loop and singleton `_struct_ref_seq` forms; this is parser compatibility only.

### Mutation-pocket audit
Implementation:
- `evaluation/d017_mutation_pocket_audit.py`
- `scripts/stage5/audit_d017_mutation_pockets.py`

Artifact:
`references/stage5/d017/receptor_inputs/mutation_pocket_audit.json`
SHA-256: `63a723e48b99231277a8402f428b1814888020b940570d4a8c3c0e1b6acb3bb0`

Pocket mutations:
- 2YDV A89 ALA -> GLN, 3.972587 A from NECA
- 4UG2 A89 ALA -> GLN, 3.879394 A from CGS21680

9EHS mutations are non-pocket:
- R97 ARG -> SER, 8.437770 A
- R160 ALA -> ASN, 20.480164 A

These are provenance annotations only.

Last tests:
- after materialization: focused 10 passed; full 44 passed
- after mutation audit: focused 11 passed; full 45 passed

### Implementation assistants
OpenCode is paused. Codex usage on the user's other account is currently exhausted. Do not suggest Codex until the user says usage is available again. Continue directly with user/assistant.

## 3. Frozen archive
Read-only/frozen evidence:
- raw mmCIFs under `references/stage5/d017/structures/raw/`
- canonical FASTAs under `references/stage5/d017/canonical_sequences/`
- manifest hash `f3b477b23c0505845367cb28383ca024e5692ec8a13f2696de3c04fef8b77b5d`
- historical config hash `c4420efec72ca257d5c13c786fa90bcd435c0aa2a410ea06438fc383df68fa23`
- active config v2 hash `6b98a09dcdc103a9c86aa640bc68a72e1685528ff7b5848df326048a99b2d6e6`
- materialization log hash `07e4e115d9fd81c4d4bdb520f87956edf000e3e8bbf342df24600750261c91b3`
- mapping hash `f63dc90146de8e53346ad418644dcb615223fa1d883141ab50bdf48b17f9bdc8`
- mutation-pocket audit hash `63a723e48b99231277a8402f428b1814888020b940570d4a8c3c0e1b6acb3bb0`

Known defect: current derived receptor mmCIFs are not yet valid US-align inputs. Preserve them as diagnostics until the emitter bug is fixed.

## 4. Documentation completed
D015, D016, and D017 are finalized/updated. D017 includes approved amendments for human A3 structures, same-class proxies, species provenance, chain tie-break, position-only extraction, mutation provenance, exact-coordinate mmCIF inputs, config supersession, and pocket-mutation provenance.

Decision records must end with `### Revisit when`.

This handoff continues Session 012 as Session 012.5.

## 5. Git state
Git state was not re-queried immediately before this handoff. Do not invent a clean/dirty claim. No commit/push of the current D017 work was confirmed in this portion of Session 012.

Known prior remote issue: SSH authentication to `git@git.ucsf.edu` was confirmed working. Do not reopen unless needed.

## 6. Environments
Local repo:
`/Users/mileshuang/Desktop/sbdd-project`

Conda env:
`sbdd-eval`

Before repo-relative writes, confirm:
`pwd`
must equal:
`/Users/mileshuang/Desktop/sbdd-project`

US-align:
`/Users/mileshuang/tools/usalign_20220227/USalign-master/USalign`

PyMOL: 3.1.0 in `sbdd-eval`.

Do not create project artifacts under the US-align tool directory.

Server is not currently required. Established SSH route if needed:
`ssh mhuang8@facbastp9004.fac.ucsf.edu`
then:
`ssh gpu-dev1.ic.fac.ucsf.edu`

## 7. Decisions now in force
D015: P2Rank Level-3 predicted-pocket characterization only; no interaction/compatibility claim.

D016: frozen known-answer binding labels with global 50/100 nM gates; no target-specific tuning.

D017: deterministic homolog-pocket measurement using US-align 20220227, frozen 4.5 A pocket rule, position-only receptor extraction, exact-coordinate single-chain PDBx/mmCIF, state/species provenance, coverage, local pocket C-alpha RMSD. No Boolean `pocket_conserved` yet.

D018: NOT DEFINED. Do not propose thresholds before frozen D017 calibration measurements exist.

## 8. Claim authority
Authorized:
> D016 provides frozen known-answer binding labels for calibration.

> D017 provides a frozen method for measuring local homolog-pocket correspondence once its exact-coordinate receptor inputs are valid and parseable.

> Seven selected structures and their canonical-position mappings were frozen and audited before calibration alignment.

Prohibited:
> “Level 2 is complete.”
> “The homolog pocket is conserved.”
> “D017 calibration passed.”
> “P1 aligned successfully.”
> “The current derived receptor mmCIFs are valid US-align inputs.”
> Any D018 threshold or Boolean `pocket_conserved`.
> Any claim that US-align exit code 0 alone indicates success.

Retention defect: current derived receptor mmCIF emitter output is not parseable by US-align 20220227 because required `_atom_site` schema fields are absent/misserialized.

## 9. Do NOT reopen
Do not reopen D015, D016 gates/table, US-align choice/version, 4.5 A pocket definition, local RMSD definition, position-only mapping, exact-coordinate requirement, PDBx/mmCIF switch, human A3 replacements, 4UG2 chain tie-break, mutation handling, construct audit, mutation-pocket audit, raw structures, canonical FASTAs, or US-align qualification.

Do not tune after seeing alignment outcomes. Do not begin D018 until D017 measurements are frozen.

## 10. Session 012.5 starting point
Start at the current emitter defect.

From `/Users/mileshuang/Desktop/sbdd-project`, inspect:

`head -80 references/stage5/d017/receptor_inputs/2YDV_A.cif`

and:

`grep '^_atom_site\.' references/stage5/d017/receptor_inputs/2YDV_A.cif`

US-align reported missing:
- `group_PDB`
- `label_atom_id`
- `label_comp_id`
- `auth_asym_id` or `label_asym_id`
- `auth_seq_id` or `label_seq_id`
- `Cartn_x`
- `Cartn_y`
- `Cartn_z`

Fix only the mechanical mmCIF emitter. Preserve exact coordinate tokens, atom identity/order/provenance, frozen mapping rules, and frozen US-align invocation.

Then:
1. regenerate all seven derived receptor mmCIFs through the same generic path;
2. rerun focused/full tests;
3. compute new derived-input hashes;
4. verify mapping/provenance is scientifically unchanged;
5. test US-align parsing on P1;
6. validate real alignment output/artifacts rather than exit code alone;
7. only after successful P1 raw correspondence proceed to pocket-specific D017 measurements.

Immediate done condition:
> P1's two exact-coordinate derived receptor mmCIFs are valid US-align 20220227 inputs, US-align produces a real alignment and expected artifacts, and the emitter fix does not change the frozen scientific mapping contract.

Do not compute D018 thresholds.

## 11. Process rules in force
- Validation-requirement rule: trace to frozen framework; new requirements are proposed until user-approved.
- Alternatives-pass rule: enumerate serious cited alternatives, cost/scope, rejection reasons, and unrejected options before adopting new scientific software.
- Approval protocol: decisions/framework edits are drafted and user-approved before writing; results reported as measured.
- Target-specific constants belong in frozen config/artifacts, not executable scripts.
- Scientific transformations/selection/claim semantics are authored and reviewed by user + assistant.
- OpenCode paused; Codex currently out of usage.
- Preserve all intermediate/validation artifacts.
- Never treat process exit code as scientific success when output reports failure.
- Before repo-relative writes, confirm the repo root.

## 12. Preservation rule
Preserve all Session 012 / Stage-5 artifacts until Stage 5 is finalized and frozen, including raw structures, canonical FASTAs, both D017 configs, materialization logs, manifest, construct audit, mapping artifacts and superseded hashes, current invalid derived mmCIFs, mutation audit, tests, failed P1 run directory, 33-byte failed stdout, US-align diagnostics, visualization qualification artifacts, and all future regenerated/successful/failed run artifacts.

Do not overwrite authoritative raw inputs. Do not silently replace frozen artifacts after regeneration; record supersession and hashes explicitly.

Session 012 remains open; Session 012.5 is the chat continuation.
