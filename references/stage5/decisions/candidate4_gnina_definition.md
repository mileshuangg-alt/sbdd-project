# Stage 5 Docking-Protocol Candidate 4 --- GNINA CNN Rescoring

**Status:** FULLY LOCKED --- NOT YET EXECUTED\
**Lock date:** 2026-08-17\
**Results available at lock time:** NONE

Candidate 4 follows the accepted 2026-08-17 candidate-menu revision
memo. No Candidate-4 result existed when this protocol was locked.

## 1. Single Methodological Change

Candidate 4 changes exactly one named methodological lever:

``` text
Candidate 1:
AutoDock Vina 1.2.7 / Vina scoring

Candidate 3:
smina 2020.12.10 / Vinardo scoring

Candidate 4:
GNINA v1.3.3
Vina-family pose search
+
GNINA CNN final-pose rescoring / reranking
```

The CNN is used in **rescore mode only**. It does not refine or optimize
poses.

CNN refinement is excluded because refinement would change pose
coordinates and therefore change the search/optimization process.
Rescore mode isolates the predeclared question: **does better pose
judgment fix the registration failure?**

## 2. Frozen Candidate-1 Parameters

  -----------------------------------------------------------------------
  Parameter                           Candidate-4 frozen value
  ----------------------------------- -----------------------------------
  Receptor                            rigid

  Protein preparation                 PDB2PQR / PROPKA, pH 7.4;
                                      experimental protein heavy-atom
                                      coordinates preserved

  Ligand state preparation            Molscrub, pH 7.4, one protonation /
                                      tautomer state; tautomer
                                      enumeration disabled

  Exhaustiveness                      32

  Random seed                         20260816

  Maximum retained poses              20

  Energy range                        5 kcal/mol

  Search-box dimensions               20 Å × 20 Å × 20 Å

  3REY / XAC center                   49.535806, 23.214581, 34.764065

  5OLH / Vipadenant center            -21.614625, 6.759792, 16.878708

  5OLO / Tozadenant center            19.411107, 173.113429, 17.928714

  Receptor flexibility                none

  RMSD evaluation                     symmetry-aware heavy-atom RMSD to
                                      crystallographic cognate pose

  RMSD threshold                      \<= 2.0 Å

  Anchor recovery                     control-specific native chemistry:
                                      residue + interaction class +
                                      correct direction

  Pose success                        same pose must satisfy RMSD and
                                      both native anchors

  Scores                              descriptive/ranking only
  -----------------------------------------------------------------------

For 3REY/XAC:

``` text
Phe168:
Hydrophobic + VdWContact

Asn253:
HBAcceptor + VdWContact
```

## 3. A Priori Hypothesis

Candidate 1 produced a 1.826 Å near-native pose but recovered neither
native anchor. Candidate 3 produced a best RMSD of 4.642 Å, recovered
Phe168 chemistry in many poses, but recovered the native Asn253 acceptor
chemistry in 0/19 poses.

The accepted menu-revision memo established that the cognate 3REY
receptor already contains Asn253 in its experimentally observed
ligand-engaged conformation.

The predeclared hypothesis is therefore that the repeated Asn253
registration failure may arise from limitations of classical Vina-family
pose judgment rather than an incorrect cognate receptor rotamer. GNINA's
learned 3D pose scorer may rank local registrations that reproduce the
native Asn253 geometry more appropriately.

## 4. Predeclared Prediction

Candidate 4 is predicted to produce at least one retained 3REY/XAC pose
satisfying:

``` text
symmetry-aware heavy-atom RMSD <= 2.0 Å
AND
Phe168 Hydrophobic + VdWContact
AND
Asn253 HBAcceptor + VdWContact
with correct donor/acceptor direction
```

The same retained pose must satisfy all requirements. A favorable CNN or
Vina-family score cannot substitute.

## 5. Failure Acceptance

If Candidate 4 fails 3REY/XAC, it joins Candidates 1 and 3 as a
permanent documented failure, is not retuned, 5OLH/5OLO are not run, and
Layer 3 remains blocked.

> **One more selected candidate; if it fails Layer 2, Stage 5 concludes
> as a documented negative result on standard tools under the validated
> harness, and the project pivots to the reference-pose fallback gate.
> No further levers get invented after results.**

Candidate 4 is that one selected candidate.

## 6. Pre-Execution Lock

``` text
GNINA version:
v1.3.3

GNINA build:
master:6fe1ce2
Built Jun 30 2026

Container source:
docker://gnina/gnina:v1.3.3

Runtime:
Apptainer 1.4.5 with --nv

Container architecture:
amd64

Local SIF:
gnina_v1.3.3.sif

SIF SHA-256:
078bc25b6b8afcce0f2ab9a6c0a6353f37d4810d2922df3119e4670f1f473b1d

CNN ensemble alias:
all_default_to_default_1_3_3

Constituent models:
dense_1_3
dense_1_3_PT_KD_3
crossdock_default2018_KD_4

CNN mode:
--cnn_scoring rescore

Pose sorting:
--pose_sort_order CNNscore

CNN refinement:
DISALLOWED
```

The execution host exposes NVIDIA L40S GPUs to the container through
Apptainer `--nv`. GPU identity is an execution-environment detail and
must be recorded in the run report.

### Training provenance

> **CNN models derive from PDBbind/CrossDocked2020 family data,
> A2A-family overlap with our targets is unverified, so any result is
> interpreted as "an independently engineered tool can recover these
> complexes," not an untouched external validation of A2A
> generalization.**

## 7. Exact Frozen 3REY/XAC Command

`<PROJECT_ROOT>` is the repository location on the execution host.
`<GPU_ID>` is an available GPU selected at execution time and recorded
in the run report.

### Pre-execution implementation clarification

The first attempted Candidate-4 invocation did **not** dock. It failed
during command-line parsing because GNINA v1.3.3 rejected the Vina-specific
option:

``` text
Command line parse error:
unrecognised option '--energy_range'
```

No search, scoring, pose generation, or output interpretation occurred.
Candidate-4 run count therefore remains zero.

The compatibility audit found that GNINA v1.3.3 has no native
`--energy_range` option, including hidden or configuration-file options.
This is an implementation mismatch, not a scientific protocol revision.

The frozen Candidate-4 retained-pose policy remains:

``` text
5 kcal/mol retained-pose eligibility
```

Because GNINA cannot apply that window internally, the policy is
implemented deterministically after GNINA generation:

1. GNINA generates at most 20 poses.
2. `--num_modes` remains 20 and is **not** increased.
3. For each generated pose, read the empirical / Vina-family affinity
   reported by GNINA in PDBQT output as:

   ``` text
   REMARK minimizedAffinity <float>
   ```

   Example:

   ``` text
   MODEL 1
   REMARK minimizedAffinity -8.53218269
   ...
   ENDMDL
   ```

   GNINA v1.3.3 source `result_info::write` writes this field
   unconditionally for every normal output `MODEL`. It is the empirical /
   Vina-family affinity, not a CNN-derived quantity. CNN quantities are
   serialized separately as `REMARK CNNscore` and `REMARK CNNaffinity`.
4. Define the best empirical affinity as the minimum empirical affinity
   among generated poses.
5. A pose is eligible only if its empirical affinity is within 5.0
   kcal/mol of that best empirical affinity.
6. Only eligible poses enter the existing RMSD + ProLIF Layer-2
   evaluation.

Vina's `--energy_range` keeps poses within 5 kcal/mol of the best
empirical affinity; the Candidate-4 post-filter applies the identical
relative window to the identical affinity quantity, after generation
rather than during retention, so the retained-pose bar is unchanged.

CNNscore ordering is preserved as GNINA output ranking. CNNscore remains
descriptive / ranking evidence only and never determines Layer-2 pass/fail.

The implementation is also clarified to explicitly pin:

``` text
--min_rmsd_filter 1
--addH false
--device 0
```

Physical GPU selection is controlled by:

``` text
CUDA_VISIBLE_DEVICES=<GPU_ID>
```

and the physical GPU ID must be recorded in the execution report.

The CNN identifier `all_default_to_default_1_3_3` must be confirmed
verbatim against the installed GNINA binary's help text or startup banner
before execution. If the installed identifier differs, the observed string
must be recorded as a lock-field correction before any docking run. Nothing
is treated as pinned unless it has been observed on the actual install.

``` bash
CUDA_VISIBLE_DEVICES=<GPU_ID> \
apptainer exec --nv gnina_v1.3.3.sif \
gnina \
  --receptor <PROJECT_ROOT>/references/stage5/docking/3REY/3REY_receptor.pdbqt \
  --ligand <PROJECT_ROOT>/references/stage5/docking/3REY/3REY_XAC.pdbqt \
  --cnn all_default_to_default_1_3_3 \
  --cnn_scoring rescore \
  --pose_sort_order CNNscore \
  --center_x 49.535806 \
  --center_y 23.214581 \
  --center_z 34.764065 \
  --size_x 20.000 \
  --size_y 20.000 \
  --size_z 20.000 \
  --exhaustiveness 32 \
  --seed 20260816 \
  --num_modes 20 \
  --min_rmsd_filter 1 \
  --addH false \
  --device 0 \
  --out <PROJECT_ROOT>/references/stage5/docking/candidate4/3REY/3REY_XAC_poses.pdbqt \
  --log <PROJECT_ROOT>/references/stage5/docking/candidate4/3REY/3REY_XAC_gnina.log
```

Before interpreting the run, record/verify the GNINA version, SIF hash,
CNN ensemble, rescore mode, CNNscore sorting, frozen search arguments,
rigid receptor, explicit hydrogen handling, `--min_rmsd_filter`, the
empirical-affinity field used for the retained-pose post-filter, and GPU
used.

The evaluator must apply the deterministic 5 kcal/mol eligibility filter
before reporting Layer-2 pass/fail. The minimal evaluator change is to
parse exactly one `REMARK minimizedAffinity <float>` line from each generated
`MODEL`, compute the best empirical affinity as the minimum
`minimizedAffinity` among generated poses, and exclude poses outside
`best_empirical + 5.0` kcal/mol from RMSD + ProLIF pass/fail evaluation.
Do not use `REMARK CNNscore` or `REMARK CNNaffinity` for this eligibility
filter.

If the executable rejects a frozen option or changes its semantics,
execution stops for review rather than silently substituting another
setting.

## 8. Validation Sequence

First permitted experiment:

``` text
3REY / XAC
```

If it fails:

``` text
Candidate 4: PERMANENT FAIL
→ stop
→ no 5OLH / 5OLO
→ Layer 3 blocked
→ Stage 5 documented negative result
→ pivot to reference-pose fallback gate
```

If it passes, Candidate 4 proceeds under the identical frozen protocol
through:

``` text
3REY / XAC
5OLH / Vipadenant
5OLO / Tozadenant
```

Only **3/3 PASS** unblocks Layer 3.

## Candidate-4 Status at Lock

``` text
Candidate 1: Vina — EXECUTED, PERMANENT FAIL
Candidate 2: AM1-BCC — ELIMINATED BEFORE EXECUTION, 0 runs
Candidate 3: smina/Vinardo — EXECUTED, PERMANENT FAIL
Candidate 4: GNINA CNN rescore — FULLY LOCKED, NOT EXECUTED

GNINA: v1.3.3 master:6fe1ce2
SIF SHA-256: 078bc25b6b8afcce0f2ab9a6c0a6353f37d4810d2922df3119e4670f1f473b1d
CNN: all_default_to_default_1_3_3
CNN mode: rescore
Pose sorting: CNNscore
CNN refinement: DISALLOWED

Candidate-4 results: NONE
Layer 3: BLOCKED
Final Stage 5 hard gate: NOT FROZEN
DiffSBDD Stage 5 baseline: NOT PERMITTED
```

No Candidate-4 docking execution occurred before this lock was
completed.
