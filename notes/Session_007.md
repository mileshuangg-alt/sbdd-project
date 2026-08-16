# Session 007 — Stage 5 Target Compatibility

**Date:** 2026-08-16

## Session Goal

Begin implementation and validation of Stage 5 target compatibility under the predeclared D007 methodology.

Stage 5 is distinct from Stage 3B:

- Stage 3B asks whether a generated pose is physically plausible relative to the pocket.
- Stage 5 asks whether that pose expresses credible, target-specific interactions consistent with recognition by the intended binding site.

The final Stage 5 hard gate is **not yet frozen**.

Before any DiffSBDD Stage 5 baseline molecules are evaluated, the methodology must pass the following validation sequence:

1. Interaction-reader proof of life on native experimental A2A complexes.
2. 3/3 cognate self-redocking validation.
3. Common 3RFM positive/negative control experiment.
4. Complete candidate gate-formulation ledger.
5. Freeze the final Stage 5 hard gate.
6. Only then evaluate the 16 DiffSBDD Stage 4 survivors.

## Starting Status

D007 status:

`PENDING VALIDATION`

Predeclared native interaction-reader controls:

- 3REY — XAC
- 5OLH — Vipadenant
- 5OLO — Tozadenant

Core published A2A interaction anchors:

- Phe168 — aromatic / hydrophobic core recognition
- Asn253 — polar hydrogen-bond anchoring

Primary interaction reader:

`ProLIF`

Frozen preparation policy:

- protein: PDB2PQR / PROPKA, pH 7.4
- ligand: Molscrub, pH 7.4, one state per molecule
- experimental protein heavy-atom coordinates preserved
- experimental ligand coordinates preserved during native reader validation
- His250 protonation state explicitly audited

## First Task

Validate the interaction-reader layer using the native 3REY/XAC experimental complex.

ProLIF must recover both Phe168 and Asn253 from the prepared native crystallographic pose before Stage 5 is allowed to proceed to docking validation.