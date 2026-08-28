# Session 009 → Session 010 Handoff

**Date:** 2026-08-27  
**Next session objective:** ProLIF proof-of-discrimination for the A2A Stage-5 interaction gate

## Current Stage-5 state

A2A remains:

**LEVEL 1 — CLAIMS CAPPED PENDING GATE VALIDATION**

The frozen ProLIF interaction reader has established positive sensitivity on experimental A2A complexes, but plausible-negative discrimination has not yet been established. Therefore ProLIF interaction-pattern results remain characterization-only and do not yet have hard-attrition authority.

The next session begins the prospective proof-of-discrimination cycle defined by the Stage-5 validation doctrine.

## Frozen decisions

The following decisions are already established and must not be reopened merely because Session 010 begins in a new chat:

- ProLIF is the frozen primary Stage-5 interaction reader.
- The ProLIF version and interaction parameters must remain frozen through the validation cycle.
- A2A is a Level-1 target because experimental cognate target–ligand structures are available.
- A2A remains claims-capped until hard-gate discrimination is established.
- Negative-panel membership must be determined independently of ProLIF.
- Eligible primary negatives satisfy P1–P3; P4 is an adversarial strengthening criterion.
- The primary negative panel must contain at least two unrelated generation families, including one DOCK-lineage family.
- Near-native is RMSD <= 2.0 Å.
- Genuinely alternative is RMSD >= 3.0 Å.
- RMSD > 2.0 Å and < 3.0 Å is an intermediate zone and is ineligible for the primary panel.
- The hard-attrition authorization rule is prospectively 100% positive retention and 100% primary-negative rejection on the frozen panel.
- PLIP, or a qualified fallback witness, is post-validation only. Witness qualification occurs before its panel opinion is counted.
- Vina remains the production pose-generation default for the upcoming ProLIF proof-of-discrimination cycle.
- DOCK is a qualified independent adversarial-pose lineage and candidate future docking backend; it is not currently promoted to the production default.

## What Session 009 established

Session 009 qualified the DOCK lineage on the 3REY/XAC A2A control.

The earlier handcrafted XAC DB2 contained invalid strain metadata:

```text
total strain = +9999.990
max strain   = +9999.990
```

against frozen DOCK thresholds:

```text
total_strain = 8
max_strain   = 3
```

This caused deterministic rejection of the ligand set and explained the earlier zero-pose result. The zero-pose result was therefore not evidence that DOCK could not recover XAC.

The old XAC MOL2/DB2 lineage was abandoned. The qualified control was rebuilt from the wwPDB XAC Chemical Component Dictionary definition reconciled to deposited 3REY coordinates.

Qualified XAC control:

```text
formula: C21H28N6O4
formal/system charge: 0
heavy atoms: 31
hydrogens: 28
total atoms: 59
bonds: 61
```

Qualified preparation lineage:

```text
wwPDB XAC CCD
→ deposited 3REY coordinates
→ RDKit reconstruction
→ SDF
→ Antechamber SYBYL typing
→ AMSOL
→ canonical torsional strain
→ mol2db2_py3_strain
→ audited DB2
→ DOCK
```

Final DB2 coordinate preservation:

```text
all-atom RMSD:   0.000000 Å
heavy-atom RMSD: 0.000000 Å
maximum delta:   0.000000 Å
```

Canonical strain:

```text
total strain = 6.180
max strain   = 2.910
```

Both values pass the unchanged frozen thresholds.

DOCK then retained three XAC poses under the frozen settings. Direct receptor-frame heavy-atom RMSDs to the deposited 3REY XAC pose were:

| Rank | DOCK score | Heavy-atom RMSD |
| ---: | ---: | ---: |
| 1 | -26.623 | 0.592 Å |
| 2 | -26.586 | 0.563 Å |
| 3 | -26.553 | 0.560 Å |

Thus:

**DOCK A2A implementation proof of life: ESTABLISHED**

All three saved poses were native-like. This establishes that the qualified DOCK implementation can access the experimental XAC binding basin in this exact A2A system.

## DOCK compatibility work retained as provenance

AMSOL 7.1 required the legacy g77 runtime `libg2c.so.0`. The runtime was obtained from the archived CERN CentOS 7 `compat-libf2c-34-3.4.6-32.el7.x86_64.rpm` package, SHA-256:

```text
1667b0ba674f3c2b5ba2b3603cf49d661e32ce4eda35b6dad37c26b43173fef1
```

The RPM was extracted without installation and exposed through an isolated `LD_LIBRARY_PATH`.

The historical `make_amsol71_input.py3.py` helper also used an unavailable OpenEye `OENetCharge()` call only to determine molecular net charge. An isolated XAC-specific compatibility copy replaced that call with the independently validated XAC system charge of 0. The pinned DOCK/ZINC source was not modified.

These compatibility repairs are implementation provenance, not new scientific gate criteria.

## DOCK's current role

DOCK is currently:

- qualified as an independent Stage-5 adversarial-pose lineage;
- required as one of at least two unrelated negative-generation families for the planned panel;
- a candidate future production or second-pass docking backend;
- not the current production docking default.

A DOCK-generated alternative does not automatically become an eligible negative. It must independently satisfy P1–P3, with P4 recorded when applicable.

The successful XAC redocking is particularly important for P2 because it demonstrates that the same qualified docking implementation can access the native basin rather than merely generating wrong poses.

## ProLIF's current status

ProLIF remains the frozen primary interaction instrument.

Established:

- native experimental A2A positive recovery;
- same-coordinate-frame 3RFM/caffeine positive proof of life;
- frozen A2A reference-recognition definition.

Not yet established:

- plausible-negative discrimination;
- hard-attrition authority.

Therefore the current DiffSBDD Stage-5 statement remains characterization only:

**3/16 generator-provided DiffSBDD poses reproduced the predeclared A2A reference-recognition pattern.**

Do not describe this as 3/16 passing Stage 5.

## Immediate Session 010 objective

Begin the **ProLIF proof-of-discrimination** cycle.

The immediate work is to construct and prospectively freeze the experimental-positive / adversarial-negative A2A validation panel under the already established doctrine.

Primary tasks:

1. Confirm the frozen positive panel across A2A chemotypes.
2. Construct candidate negatives from at least two unrelated generation families, including DOCK.
3. Apply P1 physical-plausibility qualification independently of ProLIF.
4. Establish P2 using frozen RMSD definitions and same-search near-native evidence.
5. Establish and document P3 independently of ProLIF.
6. Record P4 where the alternative is scored/ranked at or above a sampled near-native solution.
7. Freeze panel membership, provenance, instrument settings, plausibility settings, RMSD classifications, and the 100%/100% decision rule before the blind ProLIF run.
8. Run frozen ProLIF blindly only after panel freeze.
9. Lock the result as the next D-entry before any independent-witness concordance work.

## Do not reopen

Unless new evidence requires a versioned decision, do not spend Session 010 re-litigating:

- whether A2A is Level 1;
- whether ProLIF is the primary reader;
- whether DOCK can recover XAC;
- the old `+9999.990` strain failure;
- the discarded old XAC MOL2/DB2 lineage;
- the earlier proposed +1 / 60-atom XAC branch for the DOCK proof-of-life control;
- whether PLIP should run before the ProLIF result is locked;
- whether Vina should be replaced by DOCK before the planned robustness benchmark.

## Future docking robustness work

After the ProLIF validation result is locked, perform the planned matched Vina-versus-DOCK robustness benchmark using the same receptors, experimental ligands, and crystallographic references.

Compare at minimum:

- best-pose RMSD;
- top-ranked-pose RMSD;
- success rate at RMSD <= 2.0 Å;
- failure rate;
- pose diversity;
- runtime / operational cost.

The primary question is whether downstream ProLIF interaction evidence is sensitive to the pose generator, not which docking engine wins.

## Session 010 starting principle

> **Session 009 qualified the adversarial DOCK lineage. Session 010 must now validate the frozen ProLIF reader against a prospectively frozen, independently eligible positive/negative panel without allowing ProLIF to define its own challenge set.**
