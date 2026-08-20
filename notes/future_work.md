# Future Work

This document records scientifically relevant questions and implementation extensions that are intentionally outside the current frozen baseline.

Items here must not be used to retroactively tune the completed DiffSBDD evaluation.

---

## 1. Receptor flexibility in docking validation

Determine when rigid-receptor docking is an adequate approximation and when limited receptor flexibility is required.

Questions:

- How should flexible residues be selected prospectively?
- Can selection be based on apo/holo ensembles, alternate conformations, B-factors, MD, or other structural evidence?
- Can a general rule be defined without choosing residues retrospectively because a docking control failed?
- Would limited receptor flexibility materially alter the documented negative result from the current independent docking-validation arm?

---

## 2. Target-specific side-chain flexibility

Characterize which binding-site residues undergo meaningful conformational adaptation during ligand recognition.

Questions:

- How much target-specific structural precedent is required before introducing side-chain flexibility?
- Can conformational ensembles define permissible receptor states?
- How should receptor-state uncertainty propagate into pose-validation claims?

---

## 3. Improved independent pose validation

Revisit whether future docking or pose-prediction methods can provide an independent confirmation layer that the current standard docking candidates could not establish.

Questions:

- Which newer docking or scoring approaches warrant validation?
- What evidence would justify reopening the independent docking arm?
- Can independent confirmation be achieved without allowing the confirmation method to redefine the target-recognition rule?

The current docking arm remains closed until a formally justified future experiment reopens it.

---

## 4. Plausible-but-wrong Stage-5 negative controls

Develop a general method for constructing poses that are:

1. physically plausible;
2. chemically unchanged;
3. meaningfully wrong with respect to target recognition.

The principal-axis rotation strategy did not achieve this for A2A.

Observed A2A behavior:

- 10° axis 1 — physically plausible; native recognition retained;
- 15° axis 1 — physically plausible; native recognition retained;
- 20° axis 1 — universal physical plausibility lost before universal interaction disruption was established.

Questions:

- Can plausible negatives be constructed without tuning against the interaction reader?
- Can negative-pose construction be generalized across targets?
- Can experimental alternate poses, decoy poses, homolog-derived incompatible orientations, or other evidence provide stronger negatives?
- What number and diversity of plausible negatives are sufficient for hard-gate discrimination?

---

## 5. Stage-5 gate-validation requirements

Formalize how much validation is sufficient to promote a characterization rule to a hard attrition gate.

Questions:

- How many cognate positives are required?
- How many plausible-but-wrong negatives are required?
- How should chemotype diversity be represented?
- What sensitivity and discrimination criteria should be predeclared?
- What material implementation changes require revalidation?
- How should validation be handled when only a small number of experimental complexes exist?

Gate validation remains target-specific and implementation-specific.

---

## 6. Level-2 homolog sufficiency

Operationalize the Level-2 evidence requirements.

Questions:

- What pocket sequence-identity threshold is sufficient?
- What pocket-superposition RMSD threshold is sufficient?
- Which residues define the pocket comparison?
- How should insertions, deletions, alternate conformations, and protonation differences be handled?
- How should conflicting sequence and structural similarity be resolved?

Overall fold homology alone remains insufficient.

---

## 7. Level-3 target handling

Characterize uncertainty for structurally defined targets with insufficient target–ligand interaction evidence.

Questions:

- How reliable are P2Rank and fpocket for defining candidate pockets in this setting?
- How should disagreement between pocket predictors be represented?
- How should predicted-pocket uncertainty propagate through Stage 3B?
- What evidence is sufficient to upgrade Level 3 to Level 2?
- How should Level-3 molecules be compared across generators without implying target compatibility?

Level-3 target compatibility remains INCONCLUSIVE until qualifying evidence appears.

---

## 8. Interaction-guided generator comparator

Consider adding an interaction-aware generator such as DiffInt after the core DiffSBDD-versus-FLOWR comparison is complete.

Motivation:

The DiffSBDD A2A baseline reproduced:

- Phe168 reference recognition in 15/16 poses;
- Asn253 HBAcceptor recognition in 4/16 poses;
- the complete A2A reference pattern in 3/16 poses.

This motivates a future hypothesis:

**Does explicit interaction-guided generation improve experimentally grounded target-recognition reproduction under the same frozen evaluation cascade?**

Any future DiffInt or other interaction-aware comparator must:

- use the identical frozen Stage-1 through Stage-5 evaluation pathway;
- receive no generator-specific Stage-5 threshold tuning;
- preserve generator-provided poses;
- be treated as an extension rather than a replacement for the current core comparison.

---

## 9. Broader interaction-aware generator comparison

Survey whether a future extension should compare multiple interaction-aware approaches rather than adding a single third generator.

Questions:

- Do interaction-conditioned models improve hydrogen-bond reconstruction?
- Are improvements target-specific or general?
- Do interaction gains trade off against chemical validity, diversity, novelty, or physical plausibility?
- Does explicit interaction conditioning improve complete recognition patterns or only individual interaction counts?

---

## 10. Stage-5 ruling framework implementation

Implement the generalized Stage-5 ruling layer before implementing target-specific Level-2 or Level-3 arms.

The ruling layer should:

- determine whether a target is structurally in scope;
- record Level 1, Level 2, or Level 3 evidence status;
- represent gate-validation status separately from evidence level;
- determine the permitted Stage-5 claim mode;
- apply claims-cap status where required;
- propagate `interaction-unverified`, `homology-inferred`, and related provenance flags;
- remain independent of generator identity and target-specific interaction definitions.

A2A should serve as the first Level-1 / claims-capped test case.

The ruling framework should be implemented before the Level-3 predicted-pocket lane.

---

## 11. Level-3 predicted-pocket lane implementation

After the generalized ruling framework exists, implement the Level-3 LANE arm when a qualifying Level-3 target is encountered.

The lane may use an established pocket-prediction method such as P2Rank or fpocket to:

- nominate candidate binding sites;
- characterize predicted-pocket geometry;
- preserve prediction confidence/provenance;
- provide predicted-pocket coordinates to Stage 3B.

Requirements:

- every nominated site remains labeled `PREDICTED POCKET`;
- prediction does not establish target compatibility;
- prediction does not upgrade the target evidence level;
- Stage-3B outputs remain geometry-only;
- all downstream molecules retain the `interaction-unverified` flag.

Do not implement this arm speculatively before the ruling framework and an appropriate target exist.

---

## 12. Evidence-level automation

Standardize the Stage-5 target evidence pull.

Potential evidence sources include:

- PDB;
- ChEMBL;
- cognate ligand records;
- homolog ligand-bound structures.

Future automation should assist evidence collection without automatically assigning scientific authority.

The evidence record should preserve:

- source;
- date;
- target;
- ligand;
- structure;
- pocket comparison;
- evidence-level rationale.

---

## 13. Pipeline automation and HPC scaling

After the evaluation cascade and generator comparison are fully validated and frozen, automate large-scale execution.

Potential scope:

- generator execution;
- artifact transfer;
- Stage-1 through Stage-5 evaluation;
- provenance tracking;
- evidence-level metadata;
- claims-cap metadata;
- aggregate reports;
- HPC / GPU scheduling.

Automation must preserve the generator/evaluator boundary.

All evaluators should remain independently runnable and interpretable beneath the orchestration layer.

The current implementation workflow remains intentionally manual while methodology is still being developed.

---


