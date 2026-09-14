
---

## ProLIF/PLIP Interaction-Fingerprint Layer

### Purpose

Provide a future interaction-evidence layer that computes per-residue interaction fingerprints for generated molecules using ProLIF/PLIP.

The intended interaction types include:

- hydrogen bonds;
- hydrophobic contacts;
- related contact types supported by the selected interaction reader.

The purpose is to verify whether generated molecules reproduce key contacts of the experimentally bound ligand, providing interaction-level evidence beyond geometric fit.

### Inputs and scope

The layer consumes:

- frozen pocket/structure artifacts;
- experimentally defined reference-ligand interaction information;
- generated-molecule outputs.

Its results are an evidence layer downstream of the frozen structural measurements and must not alter those measurements.

### Scientific boundary

Interaction-fingerprint results must never feed back into a frozen verdict, threshold, eligibility rule, or routing decision without formal promotion through the decision/amendment process.

This implementation therefore remains a future evidence layer and introduces no new validation requirement for the currently frozen methodology.

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
