
---

## Interaction-Fingerprint Review View

### Purpose

Provide a future reporting and GUI view for displaying the existing interaction-fingerprint infrastructure established under D019.

The interaction-fingerprint infrastructure is no longer a future implementation item:

- **ProLIF** is the frozen Stage-5 verdict instrument;
- **PLIP** is the qualified independent witness.

The future implementation is therefore limited to presentation and exploration of those existing results.

### Desired capabilities

A future GUI/reporting layer could display:

- per-residue interaction fingerprints;
- configured interaction roles;
- ProLIF observations;
- PLIP witness observations;
- concordance/disagreement status;
- links to the underlying frozen audit artifacts.

### Scientific boundary

This is a presentation layer over existing frozen interaction-evidence outputs.

It must not:

- redefine the ProLIF interaction pattern;
- change the ProLIF verdict instrument;
- promote PLIP to verdict authority;
- introduce new interaction thresholds;
- create new validation requirements.

Any change to the instrument/witness allocation or any attempt to use these results in a new scientific verdict requires formal promotion through the decision/amendment process.
---

## Dock-Back Forensics Harness

### Purpose

Provide a future analysis layer that docks generated molecules back into the target pocket with a standard docking engine and inspects the resulting poses.

The purpose is to reality-check generative output in three dimensions and, when an output appears incorrect, distinguish a problematic generated molecule from a problematic evaluation result.

### Inputs and scope

The harness consumes:

- frozen pocket/structure artifacts;
- generated-molecule outputs.

Docking is used as a forensic analysis tool rather than as an additional generator or a replacement for the frozen evaluation cascade.

### Scientific boundary

Dock-back results must never feed back into frozen verdicts, thresholds, eligibility criteria, or routing decisions without formal promotion through the decision/amendment process.

The harness therefore remains a future diagnostic layer and introduces no new validation requirement for the currently frozen methodology.

---

## Failure-Mode Decomposition View

### Purpose

Provide a future reporting and GUI view that classifies generation failures by the pipeline layer that owns the appropriate fix:

- **invalid chemistry** — filter;
- **pocket conditioning** — inputs;
- **pocket-directed sampling** — sampling guidance;
- **model fit** — fine-tuning.

The purpose is to route debugging to the correct layer instead of defaulting to retraining.

### Scope

This is a classification and presentation layer over existing pipeline outputs.

It does not create a new scientific measurement, alter existing measurements, or replace the existing evaluation cascade.

### Scientific boundary

The failure-mode decomposition introduces no new validation requirements.

Its classifications must not feed back into frozen verdicts, thresholds, eligibility criteria, routing rules, or other scientific decisions without formal promotion through the decision/amendment process.

---
