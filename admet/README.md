# LigGate ADMET

## Overview

ADMET is an integrated stage of the LigGate evaluation cascade. It evaluates pharmacokinetic and developability properties of surviving candidate molecules before downstream MD/MM-GBSA and retrosynthetic/synthetic-feasibility evaluation.

Current cascade placement:

**upstream LigGate stages → ADMET → MD/MM-GBSA → retrosynthesis / synthetic feasibility**

The stage follows LigGate's generator-agnostic, artifact-first design. Predictions, uncertainty, molecular identity, model provenance, and relevant flags are preserved as explicit artifacts. ADMET outputs do not acquire attrition, routing, or ranking authority unless that authority is separately defined by the frozen methodology.

Tripwire remains a separate DDI-liability component and should not be conflated with the broader ADMET stage.

## Planned stage

The currently committed longer-term ADMET endpoints include:

- intrinsic clearance;
- fraction unbound; and
- CYP inhibition.

Additional endpoints require separate methodology and data review before entering scope.

The stage is intended to provide reusable molecular-property prediction with uncertainty for LigGate candidates. Its outputs may later provide inputs to mechanistic pharmacokinetic modeling, including the planned PK-Sim layer.

## Session 016 pilot

Session 016 is a bounded implementation pilot covering:

- human hepatocyte intrinsic clearance; and
- aqueous pKa, with a five-output base-side pKa model.

The pilot is establishing source preparation, alias-aware split construction, endpoint-specific metrics, masked multi-output behavior, Chemprop execution, learning curves, and measured runtime before the full ADMET model search.

The pilot does **not** authorize the full hyperparameter search, descriptor-arm training, final training-length selection, PK-Sim integration, or use of the held-out DataWarrior pKa dataset for training.

### Current status

Completed:

- source bundle v5 staged and its complete SHA-256 manifest verified;
- preparation runtime qualified with Python 3.12, NumPy 1.26.4, compatible pandas, and RDKit 2023.09.6;
- separate pilot Chemprop runtime qualified with Chemprop 2.3.1, `cuik-molmaker-pin` 2026.3.6, RDKit 2026.3.6, and GPU-capable PyTorch;
- pKa eligibility, temperature-selection, and numeric-aggregation logic implemented and tested;
- corrected pKa preparation checks reproduced exactly: **6,752 molecule-steps across 5,474 source-ID compounds**, with **523 compounds represented on both acid and base sides**.

Next:

- prepare the 408-record human hepatocyte clearance endpoint;
- construct and freeze alias groups, the development/test split, and development CV folds;
- implement and validate endpoint metrics and pKa masking behavior;
- run the gpu-dev1 smoke/timing benchmark;
- review the runtime projection before any CoreHPC GPU pilot execution.

The two-environment arrangement is specific to this bounded pilot and does not establish production environment pins for later ADMET work.

## Data

Canonical Session 016 source archive:

`admet/data/source/admet-source-bundle-v5.zip`

SHA-256:

`2384f1f0ce2e447f16841603c10bee6b0c00f52f35d4215b9a427d9a28ef0363`

Primary pilot sources:

- `pk/iupac_pka_v2.4a.csv`
- `pk/method_translation.csv`
- `pk/human_hepa_owner_408.csv`

Raw source files are preserved unchanged. Source-recorded molecular representations remain the model inputs; representations generated for alias grouping are used only for grouping and split assignment.

Detailed Session 016 preparation rules, corrections, qualification results, and attrition accounting are maintained in the corresponding methodology/session artifacts rather than duplicated here.

## Repository layout

- `admet/README.md` — stage overview
- `admet/data/source/` — immutable source bundle and extracted sources
- `admet/data/prepared/` — prepared endpoint datasets
- `admet/data/splits/` — frozen grouping, split, and fold artifacts
- `admet/scripts/` — preparation, training, and evaluation code
- `admet/artifacts/` — qualification and run artifacts
