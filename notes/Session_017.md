# Session 017 — ADMET Split Construction: Duplicate-Tie Refinement, Similarity Freeze and Split-Input Builder

**Date:** Began after the 2026-11-11 Session 016 → Session 017 handoff (exact first active Session-017 date UNKNOWN); ongoing as of 2026-11-19  
**Status:** ONGOING — recovered history captured to 2026-11-14, then live entries to 2026-11-19; not closed, finalized or advanced

Condensed 2026-11-19 from notes/Session_017.md.pre_debloat (SHA-256 8a3d0af1…); full detail is in that file.

## 1. Session objective and record provenance

Session 017 continues the ADMET pilot at the first unfinished implementation-plan item: construct and freeze the real 80/20 development/test split and five-fold development CV (Session 016 §10 resume point; governing plan `admet-pilot-gpt-handoff-1.md`).

Recovered governing Task-2 plan wording (identical in both sources below):

> "Prepare both endpoint datasets with the approved filters, build the 80/20 development/test split and the 5-fold development CV with the approved alias grouping (decision 3), freeze them, and report: settled source-ID counts vs expectations, alias group counts recomputed on the pinned RDKit, any canonicalization failures or ambiguous fragments (held and reported, never guessed), and confirmation that the test side was never read."

"Task 2" is implementation-plan bookkeeping, not a scientific or architectural namespace.

This log was created 2026-11-14 as a recovered-history capture. Miles authorized it in chat: "I approve creating notes/Session_017.md as the first real bookkeeper write. Session 017 is ONGOING. This is recovered history capture, not session closure, advance, or permission to continue scientific work."

Source labels:

- **[Export]**: GPT export `LigGate_Session_017_Record_So_Far.md` (`/Users/mileshuang/Downloads/`, 1061 lines, SHA-256 `9b1f372ff198fb31497c20a46d2280c3f728ecb1facaca43882f9beb2740866a`), dated 2026-11-14, supplied by Miles. Historical context only.
- **[Handoff]**: `liggate-session-017-handoff.md` (`/Users/mileshuang/Downloads/`, 442 lines, SHA-256 `e39cfa56833b5f3aa241070facc0c52c11c1919d08ed8b3272f112e621085d32`), "Mid-Session Migration Handoff", 2026-11-14, "MID-SESSION TRANSFER — NOT A CLOSE-OUT". Identified by title by the main conversation.
- **[gpu-dev1, user-pasted]**: output Miles ran on gpu-dev1 (host `n4pu04`) and pasted or reported.
- **[Mac, user-reported]**: local Mac tests reported by Miles; mechanical smoke tests, not pinned-runtime qualification.
- **[Mac obs <date>]**: read-only local observations by the main Claude Code conversation; not remote-run evidence.
- **[Miles, chat]**: Miles's own statement.

The two source-file hashes were supplied by the main conversation; the bookkeeper did not recompute them. This log does not recover history beyond these sources.

---

## 2. Entering state: Session 016 pre-amendment baseline

Source: `notes/Session_016.md` §2 and §3 (committed), restated in [Export] §3.1 and [Handoff] §8.

- pKa: 6,752 molecule-steps / 5,474 source-ID compounds; clearance: 408 molecular identities; combined endpoint-qualified identities: 5,882
- grouped 5,881; failures 1; family keys 5,446; scaffold keys 893; MaxTransformsReached tautomer witnesses 5 of 5,881
- Held identity: `clearance:CHEMBL5315124`, `fragment_ambiguity_equal_largest_heavy_atom_count`

Valid historical pre-amendment evidence; not rewritten by the §8 rerun.

---

## 3. Recovered split formulation (carried forward, not reopened)

Source: [Export] §3.2, [Handoff] §1 and §6, reconciling the Session-016 record.

- Production units are immutable `family_key` families, not diagnostic scaffold-plus-family components.
- Per-family fields: family identifier; `w_i` = exact number of molecular identities; pKa count; clearance count; complete `S_ij` to every other family.
- Stage A: dev/test = 0.8/0.2, every family assigned once. `epsilon = delta = 0.05`, lower-bound semantics:
  - molecular count: `N_s >= int[p_s (1 - epsilon) N]`
  - endpoint count: `C_{s,e} >= p_s (1 - delta) C_e`
- Stage B: five development folds, nominally 0.2 each, same lower-bound semantics ([Handoff] §6). The historical synthetic 80/10/10 Stage-B probe settings are not production authority.
- Frozen leakage objective: `L_cross = sum_{i<j} w_i w_j S_ij 1[z_i != z_j]`; the native Gurobi formulation maximizes the equivalent within-partition weighted similarity.
- Not authorized: pair pruning, thresholding, sampling, coarsening, approximation, changed weighting, objective normalization or a replacement objective.
- Carried from Session 016 ([Handoff] §6): leakage of any returned assignment is recomputed independently; a time-limited incumbent is eligible only if it independently satisfies every frozen hard constraint; global optimality not required; no MIP-gap acceptance threshold authorized.

---

## 4. Similarity-method reconciliation and molecular-similarity specification

### 4.1 Reconciliation

[Export] §3.3, [Handoff] §2.1. The Session-016 record froze complete `S_ij` usage but not the exact structure → molecule similarity → family similarity mapping. An assistant proposed another alternatives pass and a grouping-only fingerprint input; the user corrected this (grouping, soft objective and family-mean/size weighting were already reasoned through) and the grouping-only proposal was withdrawn. No later decision supersedes the earlier prepared-source-SMILES recommendation.

### 4.2 Reported approval

[Export] §3.4 reports this user wording:

> "Approve the proposed Task-2 similarity mapping, incorporating the earlier input contract explicitly: pKa unique_ID and clearance molecule_chembl_id, preserving the same prepared-source SMILES string across steps; Environment A with RDKit 2023.09.6; direct sanitized MolFromSmiles parsing, no family-key normalization or representative substitution. A parse failure halts rather than skipping an identity.
>
> Freeze Morgan radius 2, 2048 bits, chirality enabled, Tanimoto, and the complete family-mean S_ij mapping as proposed. State explicitly that w_i = |F_i| is what makes w_iw_jS_ij equal the sum of the between-family molecular-pair similarities.
>
> Carry all other qualified choices forward unchanged. clearance:CHEMBL5315124 remains held and unresolved. This approval freezes the similarity specification only; it does not authorize fingerprint computation, pair-matrix generation, or split execution."

[Handoff] §1A reports the same as "explicitly approved by Miles in this chat" without quoting. Specification:

- pKa identity `unique_ID`; clearance identity `molecule_chembl_id`; same prepared-source SMILES string preserved across steps
- RDKit 2023.09.6; direct sanitized `Chem.MolFromSmiles(prepared_source_smiles)`; no family-key normalization or representative substitution; parse failure halts
- Morgan radius 2, 2048 bits, chirality enabled; Tanimoto
- `S_ij = (1 / (|F_i||F_j|)) * sum_{a in F_i} sum_{b in F_j} s(a,b)`; `w_i = |F_i|`, so `w_i w_j S_ij = sum_{a in F_i} sum_{b in F_j} s(a,b)`
- complete family-pair similarities retained; no thresholding, pruning, approximation or coarsening

The approval froze the specification only. Original approval date not recovered; later recorded as D033 (§17.5).

---

## 5. CHEMBL5315124 and the equal-largest duplicate-tie refinement

### 5.1 Source record recovered

[gpu-dev1, user-pasted] per [Export] §3.5 (host not named):

```text
MATCH_COUNT: 1
molecule_chembl_id: CHEMBL5315124
smiles: C[C@H]1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23.C[C@H]1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23.O
```

Two copies of the same large organic fragment plus water. The pre-amendment selector stopped on equal-largest heavy-atom ties, so Session 016 correctly held it.

### 5.2 Reported approval

[Export] §3.6 reports the user wording "yep approved lets move forward"; [Handoff] §1B says "approved in this chat" without wording. Rule:

1. Tied maximum-heavy-atom fragments are compared by canonical isomeric SMILES under RDKit 2023.09.6.
2. One distinct representation means duplicate multiplicity, not ambiguity; the downstream family-key computation continues.
3. Multiple distinct representations, or a parse/canonicalization failure, stay held. Nothing is guessed.
4. Grouping-only: the preserved prepared-source SMILES and similarity input are unchanged.
5. A successful resolution is not an ambiguity flag; audit label `duplicate_equal_largest_fragments_resolved`.

Rejected ([Export] §4): arbitrary first/second-fragment tie break; one-record-only CHEMBL5315124 exception. Later recorded as D032 (§17.1).

---

## 6. Alias-grouping amendment and Mac test chronology

- 6.1 Pre-amendment `admet/scripts/alias_grouping.py` (`AUTHORITATIVE_RDKIT_BEHAVIOR = "2023.09.6"`) returned `FRAGMENT_AMBIGUITY` whenever `len(largest) != 1`. Downstream family-key pipeline unchanged: copy fragment → remove stereochemistry → Uncharger → tautomer canonicalization → canonical non-isomeric SMILES ([Export] §3.7, [Handoff] §2.3).
- 6.2 Tie refinement implemented ([Export] §3.8, [Handoff] §2.3): added `resolution_note`, constant `DUPLICATE_EQUAL_LARGEST_RESOLVED = "duplicate_equal_largest_fragments_resolved"`, propagated into `AliasGroupingResult.notes`. Evidence type per [Handoff]: "code edits performed by Miles from commands supplied in this chat". Backup command `cp admet/scripts/alias_grouping.py admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement` (existence UNKNOWN in [Export]; observed on the Mac, §11).
- 6.3 First test attempt used the wrong environment ([Export] §3.9, host not named): `zsh: command not found: micromamba`, `RDKit: 2026.03.6`, `AssertionError` at the version check. Environment-selection failure, not scientific. Not in [Handoff].
- 6.4 [Mac, user-reported] Existing local alias suite: 19 passed (mechanical smoke).
- 6.5 First focused-test edit failed safely (`FAIL: alias_grouping import block not found`); file not modified; 19 tests still ran ([Export] §3.13).
- 6.6 Four focused tests added to `tests/test_admet_alias_grouping.py` (duplicate ties resolve with provenance; distinct ties stay ambiguous; order independence; actual CHEMBL5315124 resolves without source SMILES rewrite). [Mac, user-reported] first run `4 failed, 19 passed`, all `NameError: name 'build_alias_grouping_result' is not defined` (test import failure; grouping logic not reached).
- 6.7 Import fixed. [Mac, user-reported] [Export] §3.15: "all pass" (treated as 23/23); [Handoff] §2.4: "Miles reported: 23 passed". This 23-test pytest suite ran on the Mac runtime, not the pinned runtime ([Handoff] §2.5).

---

## 7. Pinned-runtime qualification on gpu-dev1

### 7.1 ADMET environment recovered and verified

[Export] §3.10, [Handoff] §2.5. Environment `/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot` (not to be conflated with the native-Gurobi environment under `CX900004_DS117`). [gpu-dev1, user-reported] pinned-runtime verification reported `pass`; contract per [Export]: Python 3.12.x, NumPy 1.26.4, RDKit 2023.09.6 ([Handoff] names only RDKit). pandas version from that check: UNKNOWN.

### 7.2 CHEMBL5315124 witness

[gpu-dev1, user-reported]. Direct witness (parse prepared-source SMILES, `Chem.GetMolFrags(..., sanitizeFrags=True)`, canonical isomeric `MolToSmiles` of tied-largest fragments) asserted 3 total fragments, 2 tied-largest, 1 distinct canonical representation. Result `pass` ([Export] §3.11, [Handoff] §2.5).

### 7.3 Implementation qualification with built-in assertions

[Export] §3.16, [Handoff] §3. Reviewed source and tests staged to `/mnt/nfs/CX900004_DS117/sbdd-project/session017_alias_tie_qualification` with SHA-256 transfer verification; literal hashes not preserved (old Session-016 manifest hashes must not be substituted). [gpu-dev1, user-reported] pytest is not in the conda environment (not changed); built-in assertions against the amended implementation under RDKit 2023.09.6 covered unique-largest, duplicate-tie resolution, order invariance, genuine ambiguity, actual CHEMBL5315124, source preservation, family-key presence, audit/failure state. Result `all pass`. The Mac pytest results (§6) are local smoke; the gpu-dev1 check used direct assertions, not pytest.

---

## 8. Full-population amended grouping rerun (post-amendment)

### 8.1 First attempt blocked by missing staged data

[gpu-dev1, user-pasted] [Export] §3.17: `NEED_PREPARED_DATA_TRANSFER` for `admet/data/prepared/pka_v2.4a_session016.csv` and `human_hepa_408_session016.csv`. Staging issue, not scientific.

### 8.2 Prepared data transferred

[Export] §3.18, [Handoff] §2.6: Mac staging `/tmp/session017_prepared_data(.tar.gz)` ([Export] only); gpu-dev1 `/mnt/nfs/CX900004_DS117/sbdd-project/session017_prepared_data`. Literal archive/file hashes not recoverable.

### 8.3 Rerun result

[gpu-dev1, user-pasted] host `n4pu04`, [Export] §3.19, [Handoff] §2.6. Many RDKit `Can't kekulize mol` warnings and several `max transforms reached` messages; none became grouping failures; no new exclusion. Final output:

```text
RDKit: 2023.09.6
endpoint_qualified_identities: 5882
successfully_grouped: 5882
grouping_failures: 0
distinct_family_keys: 5447
distinct_scaffold_keys: 894
resolved_duplicate_ties: [('clearance', 'CHEMBL5315124')]
CHEMBL5315124 family_key: CC1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23
CHEMBL5315124 notes: ('duplicate_equal_largest_fragments_resolved',)
PASS: amended full-population grouping
```

Post-amendment state: 5,882 / 5,882 / 0 failures / 5,447 family keys / 894 scaffold keys; CHEMBL5315124 is the only resolution. Kept separate from §2: the Session-016 pre-amendment result (5,881 grouped, 1 failure, 5,446, 893) remains historical. [Handoff] §8: the post-amendment state is the superseding production grouping state for continuation.

---

## 9. Stage-4 primitive reuse and naming

- 9.1 [Export] §3.20, [Handoff] §2.7: Stage-4 `novelty.py` (uploaded in the original chat) defines `MORGAN_RADIUS = 2`, `MORGAN_FP_SIZE = 2048`, `MORGAN_USE_CHIRALITY = True`, `make_morgan_generator()`, `calculate_tanimoto()`.
- 9.2 Reuse direction ([Export] §3.21 "accepted in conversation"; [Handoff] §2.7; no verbatim wording): reuse `make_morgan_generator()` and `calculate_tanimoto()`; do not duplicate the primitive in a new ADMET module; do not use Stage-4 collection/evaluation functions for family aggregation; a shared chemistry-module refactor is not authorized or required.
- 9.3 Naming ([Export] §3.22, [Handoff] §5): Task 2 is a plan step, not a scientific layer, so no `task2_*` scientific APIs/artifacts. Pipeline: prepared identities → alias families → molecular similarity → complete family-mean `S_ij` → family-level split input → 80/20 → five-fold CV. Builder name: `admet/scripts/build_split_input.py`.

---

## 10. Split-input builder: last recorded state in the sources

- [Handoff] §5: work stopped before the builder was implemented; next action was to determine the repo import path of Stage-4 `novelty.py` without guessing, then implement the builder.
- [Export] §3.23 (later): a command was *proposed* to locate `novelty.py` and create `build_split_input.py` (`SplitIdentity`, `fingerprint_split_identities()`, `family_mean_similarity()`); no user output confirms it ran, so the file's existence, content and the import path were UNKNOWN. §11 adds newer information.

---

## 11. Local Mac observations, 2026-11-14

[Mac obs 2026-11-14] Read-only, in `/Users/mileshuang/Desktop/sbdd-project`, branch `stage6-wip`, HEAD `f616babe10579b572e64d5175ca5682c63fc79ef`. `git status --short` showed modified `admet/scripts/alias_grouping.py` and `tests/test_admet_alias_grouping.py`; untracked `.claude/`, `CLAUDE.md`, `admet/scripts/build_split_input.py` and the two `.pre_*` backups. `notes/Session_017.md` did not exist.

| File | SHA-256 | Bytes | mtime |
| --- | --- | --- | --- |
| `admet/scripts/alias_grouping.py` | `dd604914ab88c9fd9e0475f0bbbecbef223b7dfd6667bfa9ebdb810f24dfe9c5` | 15989 | Nov 12 16:26 |
| `tests/test_admet_alias_grouping.py` | `2a11e59f0b672e3792172fd58d4de68da4194b47350c11eadcddfcd0a25b46a1` | 11284 | Nov 13 13:43 |
| `admet/scripts/build_split_input.py` (early draft) | `b1e96ba18b35391d19a54aa8c5054719642d8251be4054603be335f6de7905ff` | 2589 | Nov 13 14:36 |
| `evaluation/novelty.py` | `ba09443a67eae67ad08211299ea1f3484d9cfeda6676c047a7d159013eec9493` | 18359 | Aug 16 13:54 |
| `admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement` | `9f6be0038274c27c31527d2c45297ae8612b57c5397fdff92d325b686c4836e6` | 14450 | Nov 12 16:26 |
| `tests/test_admet_alias_grouping.py.pre_duplicate_tie_tests` | `3bdaad34c6e1ec186c822373f2d3500b3dba76d9b93a33eac0f594d1066cbd2e` | 9523 | Nov 6 14:20 |

The draft `build_split_input.py` (96 lines, untracked, not run) defined `SplitIdentity`, `fingerprint_split_identities()` (raises `ValueError` on parse failure or duplicate key) and `family_mean_similarity()`, imported `evaluation.novelty`, and had no data loading or `S_ij` matrix construction.

Newer information filling earlier UNKNOWNs (not contradictions):

- The builder draft exists locally; the sources do not establish whether [Export] §3.23's command created it.
- Stage-4 import path in the draft is `evaluation.novelty`; byte-identity with the uploaded `novelty.py` is not established (no upload hash).
- Both backups exist locally; neither source records how the test backup was created.
- The amended alias files were modified and uncommitted relative to `f616bab`.
- These Mac hashes describe only local bytes as of 2026-11-14; they do not establish what was staged to or ran on gpu-dev1 in the §7.3 qualification (staged hashes not recoverable).

---

## 12. Infrastructure and paths (as recorded in the sources)

Source: [Export] §7, [Handoff] §3.

- Mac remotes: `origin git@git.ucsf.edu:Miles-Huang/sbdd-project.git`; `github https://github.com/mileshuangg-alt/sbdd-project.git`
- gpu-dev1 route: `ssh mhuang8@facbastp9004.fac.ucsf.edu`, then `ssh gpu-dev1.ic.fac.ucsf.edu`. Observed host `n4pu04` is execution-state-specific, not a permanent identity.
- ADMET environment: `/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot`
- Gurobi environment: `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual` (Python 3.12.16, Gurobi 14.0.0, Academic WLS per [Handoff] §3)
- Session-017 qualification paths: `/mnt/nfs/CX900004_DS117/sbdd-project/session017_alias_tie_qualification`, `.../session017_prepared_data`; archive/commit/removal undecided, preserve for now.
- Transfer routes (Mac → gpu-dev1 via ProxyJump `mhuang8@facbastp9004.fac.ucsf.edu`; Mac → CoreHPC via ProxyJump `mhuang8@chpc-ucsf-bastion-vm1.corehpc.ucsf.edu` to `mhuang8@chpc-ucsf-login-vm1.corehpc.ucsf.edu:/scratch/user/mhuang8/`) are recorded verbatim in both sources; bundle workflow: one tar.gz plus `SHA256SUMS.txt`, `shasum -a 256` on the Mac, `sha256sum` remotely.

---

## 13. Running jobs

As of the 2026-11-14 sources ([Export] §10, [Handoff] §4): no known running Session-017 job (no fingerprint, family-pair matrix, production Gurobi, Stage-A or Stage-B job; no Slurm job or background process); live status not refreshed. Session-016 DataSAIL P1 and native N=100/N=500 measurements are engineering probes, not current jobs, and do not establish full-scale feasibility.

---

## 14. Differences between the sources

1. Local suite after the import fix: [Export] "all pass" (23/23) and [Handoff] "23 passed" are the same result in different words.
2. [Export]-only events (omissions, not contradictions): wrong-environment RDKit 2026.03.6 failure (§6.3), failed import-block edit (§6.5), `NEED_PREPARED_DATA_TRANSFER` (§8.1), Mac `/tmp` staging paths (§8.2), proposed builder-creation command (§10), withdrawn grouping-only fingerprint proposal (§4.1).
3. Runtime contract detail: [Export] lists Python 3.12.x / NumPy 1.26.4 / RDKit 2023.09.6; [Handoff] only RDKit.
4. Builder state: [Handoff] stops before implementation; [Export] records a later proposed command; consistent as successive states.

---

## 15. Gaps and UNKNOWNs (still open)

As recorded at 2026-11-14, with later resolutions noted:

- exact first active Session-017 date beyond the 2026-11-11 handoff
- production Gurobi seed / determinism: Seed 20261114 carried in the config under D034 ("keep the ongoing seed convention", §17.11); synthetic seeds not inherited
- production optimization time budget: OPEN (P0 1,800 s / P1 600 s were probe limits); W_A, W_B and TimeLimits to be set by Miles after calibration (D034 Amendment 1 A2)
- MIP-gap acceptance threshold: none approved
- constrained-random comparison protocol: covered by D034 and Amendment 1 (§17.11–§17.12); not run
- full-scale production optimization feasibility/performance: unmeasured (Stage-A construction only, §17.23)
- SHA-256 of bytes staged to and run in the §7.3 qualification: not recoverable
- pandas version from the pinned-runtime check: UNKNOWN
- whether local `evaluation/novelty.py` equals the uploaded `novelty.py`: not established
- how and when the early builder draft and test backup were created: not established
- Stage-A/Stage-B assignments, 80/20 production split, five-fold CV: not generated
- any unreported work after the last recoverable chat state

Resolved by later entries: Git commit of Session-017 edits (§17.13); production fingerprints, complete `S_ij` and family-level optimizer input (§17.9). Missing documentation is not evidence that something did not happen or was not approved.

---

## 16. Current state as of 2026-11-14 (historical snapshot; session ongoing)

From [Export] §9 and §14, [Handoff] §9, [Mac obs 2026-11-14]:

```text
Endpoint preparation:                    complete/frozen from Session 016
Alias-grouping base methodology:         qualified from Session 016
Equal-largest duplicate refinement:      reported approved, implemented, qualified (gpu-dev1 assertions)
Current grouping population:             5882/5882 grouped, 5447 families, 894 scaffold keys, 0 failures (gpu-dev1, user-pasted)
Similarity methodology:                  reported approved/frozen
Stage-4 Morgan/Tanimoto reuse:           reported selected
build_split_input.py:                    local untracked draft; incomplete; not run
Real fingerprints / S_ij / optimizer input: not established as generated
80/20 split / five-fold CV:              not run
Production Gurobi job:                   none known
```

Both sources and Miles's authorization give no permission to modify code, run jobs or advance the session. Later state is in §17.9, §17.23 and §17.25–§17.26. Session 017 remains ongoing.

---

## 17. Decision records, builder, and Stage-A calibration work

Entries to §17.24 are dated 2026-11-14 unless stated. Miles's chat authorization of 2026-11-14 for the first batch began: "Handle both rounds as one bookkeeping batch. I authorize the factual Session 017 additions and the D033 draft clarifications below, not code changes or execution." It does not amend D032. Session 017 remains ongoing.

### 17.1 Decisions recorded

- D031 — "ADMET Production Split Units, Constraints and Leakage Objective (Retrospective Consolidation)", `notes/Decisions.md` lines 8226–8374, 2026-11-14 on Miles's authorization. FROZEN DESIGN; recorded as retrospective consolidation; original approval date not recovered.
- D032 — "ADMET Alias Grouping: Equal-Largest Duplicate-Fragment Tie Resolution", lines 8376–8423. FROZEN; recorded retrospectively; original approval date not recovered; wording export-reported only.
- `notes/Decisions.md` SHA-256 after D032: `ee5c4b009df43e9bd9f3a74426b8ef478026e4ac2650702c6cff7d2fcb29fd6a` [Mac obs 2026-11-14].
- For items covered by D031 and D032, this subsection supersedes the "no `Decisions.md` entry" statements in §4.2, §5.2 and §9.3. Similarity specification: see §17.5.

### 17.2 Implementation review notes (for later code review; no code changed)

From `git diff -- admet/scripts/alias_grouping.py` against `f616bab` [Mac obs 2026-11-14]:

- **Failure-label discrepancy.** In amended `select_unique_largest_fragment()`, a canonicalization exception or empty canonical SMILES returns `FRAGMENT_AMBIGUITY` even when the largest fragment is unique. The record is still held (D032 rule 3 met); only the audit reason can be inaccurate. With 0 continuation failures, no current record is affected. D032 not amended; no code changed.
- **Stereo-only ties** have distinct canonical isomeric SMILES, so they are held under D032 rule 1 although the family key later removes stereochemistry. Follows from the rule; not newly tested.

### 17.3 Evidence status

- The continuation grouping counts (5,882 / 5,882 / 0 / 5,447 / 894; §8.3) were at this point console-reported only. First artifact-backed confirmation came with §17.9.
- `admet/scripts/session016_alias_edge_diagnostic.py` imports the amended module (line 27) and checks fixed Session-016 counts (`EXPECTED_AUDIT_COUNTS`, lines 38–50, checked at line 675); run with the amended module it would not reproduce them. The pre-amendment module survives at `f616bab` and in the `.pre_duplicate_tie_refinement` backup; that alone does not establish Session-016 reproducibility. Preserved for now.
- Hashes in this log and D032 §4 identify reference bytes on the Mac; they are not proof of review and do not establish what ran on gpu-dev1.

### 17.4 Gates carried forward for the split-input builder

- Existing approval gates remain in force.
- `admet/scripts/build_split_input.py` needs its own code review and identified bytes before any execution. Transfer verification (tar plus `SHA256SUMS.txt`) is not permission to run it.
- The builder must use D032's continuation counts, not the Session-016 diagnostic's `EXPECTED_AUDIT_COUNTS`.

### 17.5 D033 recorded

D033 — "ADMET Molecular-Similarity Specification for Split Construction", `notes/Decisions.md` lines 8425–8494, on Miles's authorization ("Yes, record D033"). FROZEN; recorded retrospectively; original approval date not recovered; wording export-reported only. Supersedes, for the similarity specification, the §17.1 "not yet recorded" statement.

### 17.6 Split-input builder code edits and Mac tests

[Mac obs 2026-11-14] Code edits by the main conversation on Miles's approval ([Miles, chat, 2026-11-14]: "I approve the builder proposal for code edits"). Covered code edits and Mac tests only; a real-data gpu-dev1 run still needed review, identified bytes and measured interactive runtime.

- `admet/scripts/build_split_input.py` completed (pinned-runtime check; prepared CSVs verified against `admet/data/prepared/MANIFEST.sha256`; halts on more than one SMILES per identity; D032 grouping halting on any failure; config-driven expected-count checks; D033 fingerprints; families ordered by `family_key`; complete upper-triangle `S_ij`; outputs `families.csv`, `memberships.csv`, `family_similarity_upper.npy` (float64), `run_metadata.json`, `SHA256SUMS.txt`; refuses to overwrite a non-empty output directory).
- New frozen config `admet/data/splits/split_input_config.json` (SHA-256 `4dd1c1aa2027fe3cbe8de988c2e3153ec5bd6111ad531ea0983e84658e70e9f2`): endpoint paths and columns, RDKit 2023.09.6, expected counts (pKa 5,474, clearance 408 from `notes/Session_016.md` §2; D032 counts 5,882 / 5,882 / 0 / 5,447 / 894), output directory `admet/data/splits/split_input_v1`.
- New tests `tests/test_admet_build_split_input.py` (12 tiny-fixture tests). Mac result 35 passed (12 + 23) under local RDKit 2026.03.6; mechanical only.
- Intermediate hashes of the builder (`35693c4c…`) and tests (`5aca2dd2…`) are superseded by §17.7.

### 17.7 Code review of the split-input builder and fixes

[Mac obs 2026-11-14] `/code-review` (high effort, single pass, no verify stage) on the builder, its config and tests, on Miles's instruction ("Run /code-review first"); 9 findings; on "Fix all findings" all were fixed:

1. Provenance code hashes come from the modules actually imported (`executed_code_sha256`).
2. Endpoint names and per-family endpoint-count columns come from the config (cf. `~/.claude/CLAUDE.md` rule 9).
3. Outputs are written to a temporary sibling directory and moved into place after `SHA256SUMS.txt`; no partial output on failure.
4. The complete `S_ij` loop precomputes one fingerprint tuple per family; each molecule pair still uses `calculate_tanimoto()`; no pair pruned.
5. End-to-end tiny-fixture test added.
6. Loader halts with file and line number on a short or blank CSV row.
7. Each input must sit in the manifest's directory.
8. Removed two checks that could never fail.
9. Removed a duplicate inner import.

Reference bytes after fixes [Mac obs; not proof of review]:

- `admet/scripts/build_split_input.py`: 631 lines, SHA-256 `970a2c424ea02375ea39915c40c84672e335c2985847e8709af17673b10f773e`
- `tests/test_admet_build_split_input.py`: 318 lines, SHA-256 `ca6ff4f55eccbb24f67b70d8b09a416d562f66e12865f08db58c7a3bf0f12675`
- `admet/data/splits/split_input_config.json`: unchanged, `4dd1c1aa…70e9f2`

Mac rerun: 39 passed (16 builder + 23 alias), RDKit 2026.03.6; mechanical only. No output directory created. The review was automated, not Miles's own; Miles's review is §17.10.

### 17.8 Split-input builder staged to gpu-dev1 (transfer verified; not run)

[Mac obs 2026-11-14] Bundle `session017_split_input_builder.tar.gz` (103,482 bytes, SHA-256 `442a649c4e2197e2653a7ac8034a26f3136ee9dfa7baa1736ec57636f14837d2`) plus `.SHA256SUMS.txt`, unpacking to `session017_split_input_builder/` with `FILES.sha256` and:

- empty `admet/__init__.py`, `admet/scripts/__init__.py`, `evaluation/__init__.py`
- `admet/scripts/build_split_input.py` `970a2c42…773e`; `admet/scripts/alias_grouping.py` `dd604914…e9c5`; `evaluation/novelty.py` `ba09443a…9493`
- `admet/data/splits/split_input_config.json` `4dd1c1aa…70e9f2`
- `admet/data/prepared/MANIFEST.sha256` `50284db691bea9de6fa8da720b58ea02693de97c304b7083b2a3608260f2a43b`
- `admet/data/prepared/pka_v2.4a_session016.csv` `572fad71dee4cf691f4c413be8295bfa86c0619bcf77ad8055d90df7228ffeba`
- `admet/data/prepared/human_hepa_408_session016.csv` `cb3885018ac3aab1c697ed8baa0501d001faae09aaa07cb724687e943d0083d3`

Tests not included (no pytest in the ADMET environment). Mac extraction check verified the tarball and all 10 file hashes.

[gpu-dev1, user-pasted] Miles transferred the bundle and reported "all okay" from `n4pu04` (`~/sbdd-project`): destination absent; `sha256sum -c` on the tarball `OK`; after `tar -xzf` (GNU tar warnings about macOS xattr headers `LIBARCHIVE.xattr.com.apple.provenance`/`.macl`, ignored), `sha256sum -c FILES.sha256` gave `OK` for all 10 files. The `cd /mnt/nfs/CX900004_DS117/sbdd-project` step was not shown; that `~/sbdd-project` resolves there is consistent with §8.3 but not independently verified. Transfer verification is not run permission (§17.4).

### 17.9 Real-data split-input build on gpu-dev1 (D031–D033 input; no split run)

[gpu-dev1, user-pasted] Miles ran the staged builder interactively (not Slurm) on `n4pu04` in `~/sbdd-project/session017_split_input_builder` with the ADMET environment active, and pasted this on 2026-11-14: `cd admet/data/splits/split_input_v1 && sha256sum -c SHA256SUMS.txt` gave `OK` for `families.csv`, `memberships.csv`, `family_similarity_upper.npy`, `run_metadata.json`. Sizes (Nov 14 22:31): `families.csv` 263,696; `family_similarity_upper.npy` 118,657,576; `memberships.csv` 522,846; `run_metadata.json` 2,804; `SHA256SUMS.txt` 339.

`run_metadata.json` (pasted excerpt):

- Counts: pKa 5,474; clearance 408; endpoint-qualified 5,882; grouped 5,882; failures 0; family keys 5,447; scaffold keys 894; family_count 5,447.
- Timings (s): load 0.0138; grouping 23.62; fingerprint 0.441; similarity 28.23; total before write 52.31.
- Executed code, resolved under `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/`: `build_split_input.py` `970a2c42…773e`; `alias_grouping.py` `dd604914…e9c5`; `evaluation/novelty.py` `ba09443a…9493`.
- Runtime: Python 3.12.15; NumPy 1.26.4; RDKit 2023.09.6; Linux-5.15.0-202-generic-x86_64-with-glibc2.35.

Checks by the main conversation [Mac obs, from the pasted text only]:

- All observed counts equal the frozen config's expected counts; first artifact-backed confirmation of the D032 continuation population (§17.3).
- Executed-code hashes equal the reference bytes of §17.7 and §17.8.
- `.npy` size 118,657,576 = 14,832,181 float64 values (5,447 × 5,446 / 2 × 8 = 118,657,448) plus a 128-byte header, consistent with a complete upper triangle.
- The run log (`split_input_v1_run.log`) was not pasted.

Scope: D031 optimizer input only. No Stage-A/Stage-B assignment, optimizer run or copy back to the Mac. Outputs remain on gpu-dev1 at `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/admet/data/splits/split_input_v1/`. Output hash values: §17.14.

### 17.10 Miles's review of the builder bytes

[Miles, chat, 2026-11-14] Asked whether he had reviewed the executed builder bytes, Miles stated: "I did review them". This records his review of the §17.7/§17.8 bytes (`build_split_input.py` `970a2c42…773e`, with `alias_grouping.py` and `evaluation/novelty.py` at the §17.8 hashes) and supersedes the "Miles's own review" not-done item in §17.7. When the review occurred relative to the §17.9 run is not stated; none is inferred.

### 17.11 D034 recorded

D034 — "ADMET Production Optimization Settings and Constrained-Random Comparison", `notes/Decisions.md` lines 8496–8557, on Miles's authorization ([Miles, chat, 2026-11-14]: "lets keep the ongoing seed convention, other than that lats authorize d034."). New decision (not retrospective); authorizes no run; numeric WorkLimit values (W_A, W_B) remain to be set by calibration (D034 §4 step 3).

### 17.12 D034 review and amendment

- [Miles, chat, 2026-11-14] After a structured review of D034: "yes to all six. let me commit changes to the rpeo before you propose code".
- D034 Amendment 1 recorded in `notes/Decisions.md` (lines 8559–8586): Stage-A freeze decision before Stage B; calibration reports only and Miles sets W_A, W_B and safety TimeLimits; Stage-B construction measurement; sampling cap of 100,000 attempts and percentile definition.
- Approved Q1 item: Miles to paste the `split_input_v1/SHA256SUMS.txt` values, to be recorded as D034's identified input and checked by each optimizer run (done, §17.14).
- Reproducibility scope: D034's claims cover only the same Gurobi version, parameters, `Threads` and host CPU; each run records the host CPU model; `n4pu04` is execution-state-specific (§12).
- Miles stated he would commit the repository changes himself before D034 code is proposed.

### 17.13 Commit, and Stage-A construction-measurement code

- [Mac obs 2026-11-14] On Miles's instruction ("Commit the working tree changes with a sensible message."), seven files were committed on `stage6-wip` as `9b0efa7e20e186f7ebf1a726f2c5a2cac540f42a` ("Session 017: record D031-D034 and add ADMET split-input builder"): `notes/Decisions.md`, `notes/Session_017.md`, `admet/scripts/alias_grouping.py`, `tests/test_admet_alias_grouping.py`, `admet/scripts/build_split_input.py`, `tests/test_admet_build_split_input.py`, `admet/data/splits/split_input_config.json`. Untracked: `CLAUDE.md`, `.claude/agents/bookkeeper.md`, the two `.pre_*` backups. Not pushed.
- [Miles, chat, 2026-11-14] Approval of the construction-measurement proposal, verbatim: "okay, I approve this proposal. I cannot find the shasums.txt file you referred to". `SHA256SUMS.txt` is on gpu-dev1 (outputs not copied to the Mac); the main conversation gave the command to print the five hashes.
- [Mac obs 2026-11-14] Code edits on that approval (D034 §4 step 2; reusable for Amendment 1 A3), untracked, not run on real data: `admet/data/splits/split_optimization_config.json` (split-input path, ε = δ = 0.05, Stage A dev 0.8 / test 0.2, Gurobi Seed 20261114, output root `admet/artifacts/split_optimization`; hashes and `rss_cap_bytes` initially null/PENDING); `admet/scripts/measure_split_model_construction.py` (builds the model with unchanged `equivalence.build_native_gurobi_model()`, samples RSS with abort at the cap, checks 10,894 binaries / 5,459 linear constraints / quadratic terms, never calls `optimize()`, writes `construction_report.json` and `SHA256SUMS.txt` atomically, refuses to overwrite); `tests/test_measure_split_model_construction.py`. Mac result 49 passed, 1 skipped (Gurobi build test; `gurobipy` not on the Mac); mechanical only. Intermediate hashes superseded by §17.16, §17.17, §17.21.

### 17.14 Split-input hashes recorded; gpu-dev1 pre-run checks

[gpu-dev1, user-pasted] Miles ran `sha256sum families.csv memberships.csv family_similarity_upper.npy run_metadata.json SHA256SUMS.txt` in `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/admet/data/splits/split_input_v1` on `n4pu04` (2026-11-14):

```text
286f5cbdcbd8af10ce845dda1a6a53d40feba93b0214a35300e18efc4d0e3abc  families.csv
95d8318413b9b89294e25ceaded99c251ce1a55fc3c2dd458afe9de1e45c9044  memberships.csv
478daa50f65111b673337805699b086be9451e21eb5caf61ce14d4b137051185  family_similarity_upper.npy
dd6cdcf373db6177844df3413d655a78b2a16219916b79d4c352aedbe347f53a  run_metadata.json
f6081b95fe808125f8f9f90068626541415f5dcb347f7bb20183020d0dee5276  SHA256SUMS.txt
```

Recorded as D034's identified split input (approved Q1, §17.12) and entered as `split_input.expected_sha256` in `split_optimization_config.json` [Mac obs]. Closes the §17.9 gap.

[gpu-dev1, user-pasted] Pre-run checks on `n4pu04`: `nproc` 128; `free -g` total 503, used 7, available 492, swap 507 (used 0). In `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual`, `import numpy, psutil, gurobipy` gave `ModuleNotFoundError: No module named 'numpy'`. Consequence: the construction script (imports numpy, and `probe.py` imports numpy) could not run there as written. No environment changed; fix pending Miles's choice.

### 17.15 numpy added to the Gurobi environment

- [Miles, chat, 2026-11-14] Offered (A) removing numpy from the script or (B) installing numpy into the qualified environment: "Option B, install numpy". He pasted `7.2.2 (14, 0, 0)` for `psutil` and `gurobipy`.
- [gpu-dev1, user-pasted] Environment: `python 3.12.16` conda-forge; `psutil 7.2.2` and `gurobipy 14.0.0` from PyPI (mixed conda/pip). A conda dry run failed with `LockError: Failed to acquire lock.` (nothing changed); the pip route was used: dry run `Would install numpy-1.26.4`.
- [gpu-dev1, user-pasted] Snapshots under `/mnt/nfs/CX900004_DS117/sbdd-project/`: `liggate-gurobi-qual.before_numpy.txt`, `.before_numpy.pip.txt`, `.after_numpy.txt`, `.after_numpy.pip.txt`. After install `import numpy, psutil, gurobipy` printed `1.26.4 7.2.2 (14, 0, 0)`; the pip-snapshot `diff` showed only `> numpy==1.26.4`. The install command output and conda-snapshot diff were not pasted.
- Consequence: the Session-016 Gurobi qualification (`notes/Session_016.md` §5; `session016_native_quadratic_qualification.json`) describes the environment before numpy was added. The D034 §1 environment path is unchanged. Further packages should not be added with conda.

### 17.16 Memory cap set; construction config complete

- [Miles, chat, 2026-11-14] Asked what memory cap to use (128 GiB proposed, about a quarter of the 503 GB on `n4pu04`, §17.14): "128 GiB".
- [Mac obs 2026-11-14] `split_optimization_config.json` now sets `construction_measurement.rss_cap_bytes` = `137438953472` (128 GiB) and carries the five split-input hashes; its test `test_measurement_refuses_pending_config` was changed to null the cap in its own copy. Mac result 49 passed, 1 skipped; mechanical only. Hashes superseded by §17.17 and §17.21.

### 17.17 Code review of the construction-measurement script and fixes

[Mac obs 2026-11-14] On "Run /code-review first" the main conversation ran `/code-review` (high effort, single pass) on the construction script, config and tests: 6 findings, none affecting the bounds, dimension checks or the no-`optimize()` rule; on "Fix all findings" all fixed:

1. The run refuses to start if `<stage>_construction_ABORTED.json` exists; the abort report records its sample interval and creation time.
2. The memory cap is documented as sample-based, not a hard limit (`rss_cap_enforcement`); config sample interval shortened from 0.5 s to 0.1 s.
3. Abort path, sampling and host description tested on the Mac with injected readers.
4. The live-config test locates the config relative to the test file.
5. The similarity mapping reuses the offset for `pair in mapping` then `mapping[pair]`.
6. `RssSampler` cross-references `construction_probe.measure_native_construction()` (qualified module unedited).

Mac result: 54 passed, 1 skipped (Gurobi build test); mechanical only. Reference bytes after fixes (superseded by §17.21): script `9e114432…87ee`, config `f20f1d187e90c0bd33576396cc25f78e98d9e3ceae6f12e17c34a577d37f4fd4` (final config of this phase), tests `109bef07…e6a8`.

### 17.18 Construction script reviewed; second staging bundle built

- [Miles, chat, 2026-11-14] Asked whether he had reviewed the fixed construction-script bytes: "Reviewed, stage it" (script `9e114432…87ee`, config `f20f1d18…4fd4`, tests `109bef07…e6a8`).
- [Mac obs 2026-11-14] Second bundle `session017_stage_a_construction.tar.gz` (17,742 bytes, SHA-256 `b73c3bb9d48b610ebce35d80e36c555efd54e0b7a0f69c05a1f5b4bcfef55c8c`), built with `--no-xattrs --no-mac-metadata`, unpacking under `session017_split_input_builder/` with `FILES_construction.sha256` listing 7 files: `admet/qualification/__init__.py` (empty), `admet/qualification/datasail_scaling/__init__.py`, `admet/qualification/datasail_scaling/probe.py` `cc5af684e4c99eb9eeba84e4dc53155402dda5dbff4280b178526bc347ae4410` (unmodified from HEAD; no separate qualified hash found), `admet/qualification/native_quadratic/__init__.py` (empty), `admet/qualification/native_quadratic/equivalence.py` `58c0df783e9222203e2be68ac28b28de5b803e40bae31689bfd8591a64aac133` (equals the Session-016 qualified hash in `admet/qualification/native_quadratic/artifacts/SHA256SUMS.txt`), the construction script and the config. Mac extraction check verified the tarball and all 7 file hashes.

### 17.19 Second bundle transferred to gpu-dev1 (verified; not run)

[gpu-dev1, user-pasted] Miles transferred the bundle and pasted from `n4pu04` (liggate-gurobi-qual active, 2026-11-14): `sha256sum -c FILES_construction.sha256 && sha256sum -c FILES.sha256` gave `OK` for all 7 second-bundle files and all 10 first-bundle files (first bundle not altered). The pasted output starts at the final command; earlier steps (path check, tarball check, `tar -xzkf`) were not pasted. Transfer verification is not run permission.

### 17.20 Stage-A construction run halted on the quadratic-term check; cause identified

[gpu-dev1, user-pasted] Miles ran `python -s -m admet.scripts.measure_split_model_construction --config admet/data/splits/split_optimization_config.json --stage stage_a` in `liggate-gurobi-qual` on `n4pu04` (2026-11-14). It printed `Restricted license - for non-production use only - expires 2028-11-29`, built the model, then halted: `AssertionError: quadratic_terms: observed 27815294, expected 29664362`, `exit=1`. No report written; `optimize()` not called; peak memory and build time not reported.

Diagnosis [gpu-dev1, user-pasted; analysis by the main conversation]:
- Missing terms 29,664,362 − 27,815,294 = 1,849,068 = 2 × 924,534; the array has `zero_pairs 924534`, `nonzero_pairs 13907647`, `min_nonzero 0.0028169014084507044`.
- Minimal Gurobi check (terms 0.0·x·y and 0.5·x·y): `expr_terms 2`, `objective_terms 1` after `setObjective`/`update()`.
- Root cause (confirmed): Gurobi keeps a zero-coefficient term in a `QuadExpr` but drops it when set as the objective; the script counts `model.getObjective().size()` while its expected count assumed one term per pair per partition. Session-016 synthetic fixtures had no zero similarities.
- A pair with S_ij = 0 contributes nothing to L_cross, so the stored objective is mathematically identical; the artifact still holds complete S_ij for all 14,832,181 pairs.

Separate finding: this shell used the size-limited restricted licence bundled with pip `gurobipy`, not the Academic WLS licence recorded for Session 016 (resolved in §17.24). No code changed at this point.

### 17.21 Zero-similarity term-count fix

- [Miles, chat, 2026-11-14] Shown the root cause and planned fix: "Approve the fix".
- [Mac obs 2026-11-14] The script's expected quadratic-term count is now partitions × non-zero similarity pairs (Stage A on `split_input_v1`: 2 × 13,907,647 = 27,815,294), measured from the array at run time; the report records `similarity_pairs` (total, nonzero, zero) with an explanatory note and expected dimensions beside observed. The test dimension test uses the real counts; the tiny fixture contains one zero pair, so the Gurobi build test expects 10 stored terms. That test is skipped on the Mac, and pytest is not in the gpu-dev1 Gurobi environment, so the gpu-dev1 re-run is the check.
- Reference bytes after the fix [Mac obs; not proof of review]: `measure_split_model_construction.py` 564 lines, SHA-256 `cfb6d08facb9e31d0652e665e4720705dd18cd1ff36653b2cff6a1182377d2e6`; `tests/test_measure_split_model_construction.py` 303 lines, SHA-256 `61bad0eb85179a3dd92dae3715e45b5d2956f5d09b884ed086f9f7e3026f3226`; config unchanged `f20f1d18…4fd4`. Mac result 54 passed, 1 skipped; mechanical only.
- D031 handling: recorded as a fact with no amendment to D031 (solver omits only exactly-zero terms; objective mathematically unchanged; complete S_ij retained).

### 17.22 Fixed construction script reviewed; third staging bundle built

- [Miles, chat, 2026-11-15] Asked whether he had reviewed the fixed script: "Reviewed, stage it" (`cfb6d08f…d2e6`).
- [Mac obs 2026-11-15] Third bundle `session017_zero_fix.tar.gz` (6,361 bytes, SHA-256 `8b78cf97775fbcea502489b2c4088820817ffff074e7a138f97725eea5e58c41`), built with `--no-xattrs --no-mac-metadata`, unpacking to `session017_zero_fix/` with only the fixed script and `FILES_zero_fix.sha256`; Mac extraction check verified the file hash.
- Planned replacement on gpu-dev1 (given to Miles): verify, extract, keep the pre-fix script as `measure_split_model_construction.py.pre_zero_fix`, copy in the fixed script and verify in place.

### 17.23 Stage-A construction measurement completed (D034 §4 step 2)

[gpu-dev1, user-pasted] On 2026-11-15 Miles reported the destination check passed and that before the swap `admet/artifacts/split_optimization` did not exist and the staged script hash was `9e114432…87ee`. He swapped in the fixed script (swap output not pasted; the executed-code hash below confirms the fixed script ran) and re-ran the Stage-A measurement in `liggate-gurobi-qual` on `n4pu04`:

- `exit=0`. Report `admet/artifacts/split_optimization/stage_a_construction/construction_report.json`, SHA-256 `5701bc34512232dcf278e9a887423aefe7f8c2249e5f3ffd5f948bbdc8459fe0`; `sha256sum -c SHA256SUMS.txt` → `construction_report.json: OK`.
- Dimensions (observed = expected): binary variables 10,894; linear constraints 5,459; quadratic terms 27,815,294. Similarity pairs: total 14,832,181; non-zero 13,907,647; zero 924,534.
- Construction time 109.53128896607086 s; peak RSS 2,272,206,848 bytes (about 2.12 GiB; cap 128 GiB, sample-based). `optimize_called: false`; `solution_count: 0`.
- Host `n4pu04`, CPU INTEL(R) XEON(R) GOLD 6548Y+, 128 logical CPUs, memory 540,498,747,392 bytes, Linux-5.15.0-202-generic-x86_64-with-glibc2.35. Runtime Gurobi 14.0.0; NumPy 1.26.4; Python 3.12.16.
- Executed code under `.../session017_split_input_builder/`: `measure_split_model_construction.py` `cfb6d08f…d2e6`; `equivalence.py` `58c0df78…c133`; `probe.py` `cc5af684…4410`.

Notes (main conversation): completes D034 §4 step 2 for Stage A; the model fits easily (about 2.1 GiB peak vs 503 GB); the earlier ~10 GB extrapolation was an overestimate. The run log tail was not pasted (restricted-licence line not shown here; see §17.24). Whether `.pre_zero_fix` was kept: resolved in §17.26.

### 17.24 Gurobi Academic WLS licence located and confirmed on gpu-dev1

[gpu-dev1, user-pasted] Earlier on 2026-11-15 Miles reported from `n4pu04`: the Stage-A construction runs printed `Restricted license - for non-production use only - expires 2028-11-29` (adds to §17.23); `GRB_LICENSE_FILE` empty; neither `/mnt/nfs/CX900004_DS117/gurobi.lic` nor `/opt/gurobi/gurobi.lic` exists; `find /mnt/nfs/CX900004_DS117 -maxdepth 3 -name 'gurobi*.lic'` → `/mnt/nfs/CX900004_DS117/private/gurobi/gurobi.lic`.

[gpu-dev1, user-pasted] Miles then ran (2026-11-15): `ls -l` showed `-rw-------+ 1 mhuang8 sec_fac_cx900004_ds117 308 Nov 10 21:07` for the file; `export GRB_LICENSE_FILE=/mnt/nfs/CX900004_DS117/private/gurobi/gurobi.lic`; then `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual/bin/python -s -c "import gurobipy as gp; m=gp.Model(); m.addVars(3000); m.optimize(); print('status', m.Status)"`. Output (licence ID and registration redacted; WLS credentials not recorded): `Academic license <REDACTED> - for non-commercial use only`, Gurobi Optimizer 14.0.0, CPU Xeon Gold 6548Y+, "Thread count: 64 physical cores, 128 logical processors, using up to 32 threads", 3,000 columns solved, `status 2`. An earlier attempt from `(base)` failed with `ModuleNotFoundError: No module named 'gurobipy'` (wrong interpreter, not a licence problem). `getfacl`: owner `mhuang8`, `user::rw-`, `group:sec_fac_cx900004_ds117:rwx #effective:---`, `mask::---`, `other::---`.

Observations (main conversation):
- The Academic WLS licence is at a non-default location; without `GRB_LICENSE_FILE`, gurobipy 14.0.0 falls back to the restricted licence. The §17.23 construction measurement ran under the restricted licence, called no `optimize()`, and is unaffected.
- With `GRB_LICENSE_FILE` set, a 3,000-variable model (above the restricted size limit) optimized to status 2 in `liggate-gurobi-qual`.
- Gurobi's default is "up to 32 threads" on `n4pu04`; relevant to the D034 fixed-Threads setting (set in §17.25).
- File mode 600; ACL mask `---` leaves only the owner effective access. No change made.

Records discrepancy (unresolved; not a decision): `notes/Session_016.md` line 171 states "Gurobi 14.0.0 with Academic WLS was qualified on gpu-dev1 under Python 3.12.16", but no other line there matches "WLS", "Academic" or "licen", so no recovered record shows how the licence was configured. The recorded Session-016 runs would also have fit within the restricted licence. `Session_016.md` not edited.

Pending at that time (not approved): recording the licence path in `split_optimization_config.json` and setting `GRB_LICENSE_FILE` explicitly in calibration commands (the config later carries licence fields, §17.25).

### 17.25 Stage-A calibration design approved (Threads 32); Mac smoke test; gurobipy introspection

Session 017 remains ongoing (entries dated 2026-11-19).

**Approval.** [Miles, chat, 2026-11-19] answering the main conversation's Stage-A calibration-design proposal, verbatim: "Approve, Threads 32".
- Proposal (approved by that statement): new `admet/scripts/calibrate_split_solve.py`; tests `tests/test_calibrate_split_solve.py`; a `calibration` block in `split_optimization_config.json`. `Threads = 32` recommended because Gurobi's default on `n4pu04` is up to 32 threads (§17.24) and a shared 64-physical-core node needs headroom; no measurement compares 32 vs 64. `Seed = 20261114` from the config. `WorkLimit` and `TimeLimit` caps are required CLI arguments with no defaults, supplied by Miles. Calibration reports only (D034 Amendment 1 A2) and does not choose W_A.
- Effect on D034: D034 §1 says `Threads` is "fixed to a single recorded value for both stages, set from the gpu-dev1 core count observed before the run"; Miles's approval supplies 32. Whether it is also entered in `notes/Decisions.md` is not decided in this entry (the main conversation was asked to take it to Miles).

**gpu-dev1 introspection (read-only).** [gpu-dev1, pasted by Miles 2026-11-19] with `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual/bin/python -s`: `gurobipy.gurobi.version()` = `(14, 0, 0)`; `GRB.Callback` has `WORK`, `RUNTIME`, `MIPSOL`, `MIPSOL_OBJ`, `MIPSOL_OBJBND`, `MIPSOL_NODCNT`, `MIPSOL_SOLCNT` (among others); `GRB.Attr` has `Work`, `Runtime`, `ObjPassNWork`, `ObjPassNRuntime`; `GRB.Param` has `WorkLimit`, `TimeLimit`, `Seed`, `Threads`. Not verified: that `cbGet(WORK)` returns correctly inside a live MIP solve.

**Files written (uncommitted)** [Mac obs], SHA-256 (the first two and the `575b6bd2…` config are superseded or carried in §17.26): `calibrate_split_solve.py` `64786648b362f499bec2ff72084f18b5cdb2724d60a7c19cbc2434b289c947a6`; `tests/test_calibrate_split_solve.py` `e4f72f7c0801b7e4d394747c376336b4b1adb9683067aa3efa0f7470155a884c`; `split_optimization_config.json` `575b6bd2ad7e8797622aa270ad390a07987fae2623acf221accc512981dca804` (adds `calibration` {`threads`: 32, `threads_source`, `output_root`}; licence-field version `b1644603…05e9`); `measure_split_model_construction.py` unchanged (`cfb6d08f…d2e6`). Not reviewed line by line by Miles; not staged; nothing run on gpu-dev1.

**Design notes** (main conversation). No licence-type check exists: the `GRB_LICENSE_FILE` guard equals `gurobi.license_file`; a restricted licence would raise at `optimize` on this model; the Gurobi log is saved with the report. The trajectory records each new incumbent (MIPSOL callback) with work units, runtime, within-partition objective, L_cross = total pair weight minus within objective, bound and node count.

**Mac test** [Mac obs, pasted by Miles 2026-11-19]. `/opt/homebrew/Caskroom/miniforge/base/bin/python3 -m pytest tests/test_calibrate_split_solve.py tests/test_measure_split_model_construction.py -q -rs` (Python 3.13.13, pytest 9.1.1, numpy 2.5.3, rdkit 2026.03.6; `psutil`, `gurobipy` missing) → `30 passed, 2 skipped in 2.14s`; skipped: `test_calibrate_split_solve.py:176` and `test_measure_split_model_construction.py:266` (no `gurobipy`). Mechanical only; the Gurobi solve path and callback are untested.

### 17.26 First calibration run attempt failed before optimize(); one-line fix on the Mac

Session 017 remains ongoing (entries dated 2026-11-19).

**gpu-dev1 read-only check** [gpu-dev1, pasted by Miles 2026-11-19, `n4pu04`, in `.../session017_split_input_builder`]: `measure_split_model_construction.py` `cfb6d08f…d2e6` (equals committed `4433d75`); `equivalence.py` `58c0df78…c133`; `probe.py` `cc5af684…4410`; `split_optimization_config.json` `f20f1d18…4fd4` (old config, no licence or calibration fields). `admet/scripts/measure_split_model_construction.py.pre_zero_fix` still exists (18761 bytes, Nov 14 23:17); `admet/artifacts/split_optimization/` contains only `stage_a_construction`. New information: resolves the handoff's open item 3 (the `.pre_zero_fix` copy is kept).

**Run instruction.** [Miles, chat, 2026-11-19] verbatim: "For the run, lets do a benchmark run to establish the work and time limit caps". Proposal (Claude Code's guesses, no solve-cost data; Miles had not stated caps): provisional `--time-limit-cap 900`, `--work-limit-cap 100000`. Per D034 Amendment 1 A2 the run only reports; Miles sets W_A and the safety TimeLimit afterwards. Bundle/staging steps were given to Miles; the pasted output starts at the run command, so extraction/verification output is not recorded as verified.

**First calibration run attempt: FAILED before optimize().** [gpu-dev1, pasted by Miles 2026-11-19] Command: `cd /mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder && GRB_LICENSE_FILE=/mnt/nfs/CX900004_DS117/private/gurobi/gurobi.lic /mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual/bin/python -s -m admet.scripts.calibrate_split_solve --config admet/data/splits/split_optimization_config.json --stage stage_a --work-limit-cap 100000 --time-limit-cap 900`. Output: Academic licence loaded; parameters set (Seed 20261114, Threads 32, WorkLimit 100000, TimeLimit 900); traceback at `calibrate_split_solve.py` line 133 in `gurobi_codes`: `"MIPSOL": grb.MIPSOL,` → `AttributeError: type object 'GRB' has no attribute 'MIPSOL'`.

Findings (Claude Code's reading, not a measurement): the licence guard passed and model build and parameter setting completed; the failure is a bug in unreviewed code (`MIPSOL` belongs to `GRB.Callback`, per §17.25); no solve ran; no calibration report written (expected, not confirmed by listing); the tiny fake-model tests did not catch it and the real-Gurobi Mac test is skipped; staging of the buggy script and new config is evidenced only by the run having loaded them.

**Fix on the Mac (uncommitted)** [Mac obs, Claude Code 2026-11-19]. One-line fix `"MIPSOL": grb.Callback.MIPSOL`, plus new test `test_gurobi_codes_read_callback_constants_from_grb_callback`. SHA-256: `calibrate_split_solve.py` `f72ec9a1b40adbbe17fadfa6f00268947f3ddb0af8f315f1828af85406942edf` (supersedes `64786648…`); `tests/test_calibrate_split_solve.py` `2e27d31842d771bb6bffb4b6078f5e74fdaab16e60595968860a250dbd5b4c3f` (supersedes `e4f72f7c…`); `split_optimization_config.json` unchanged, `575b6bd2ad7e8797622aa270ad390a07987fae2623acf221accc512981dca804`.

Status: not yet re-tested on the Mac, not reviewed by Miles, not re-staged to gpu-dev1.
