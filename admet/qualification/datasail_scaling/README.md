# DataSAIL S1 Scaling Probe

Synthetic-only Session 016 probe for the uncoarsened DataSAIL `solve_c1()` formulation pinned to DataSAIL `1.2.4` commit `a212606c4ad9d847ff94365545392958c2aab7f5`, CVXPY `1.5.3`, Python `3.12`, PySCIPOpt `5.1.1`, and SCIP `<=9.1`.

The probe builds deterministic synthetic family weights, similarities, and two numeric endpoint-count columns in fixed class order: `pKa`, `clearance`. It does not read `admet/data/`, molecular files, fingerprints, real families, DataSAIL clustering, split generation, coarsening, overflow recovery, ratio renormalization, or tolerance relaxation.

Default ladder: `100 500 1000 2000 3000 5446`, modeled as Stage A with `dev,test` splits `0.8,0.2`. The explicit Stage-B scenario is `4357`, modeled as five `0.2` CV folds, and is only included with `--include-stage-b`.

Measured phases are construction, SCIP canonicalization without solve, and SCIP solve. Construction and canonicalization caps are 600 s. For the single P0 characterization, Phase C keeps SCIP `limits/time=1800` and uses a 1860 s external process cap for cleanup/status-return grace. The 204.8 GB RSS watchdog remains active throughout. Any failure or solver timeout stops escalation.

`probe_p1.py` is a minimal wrapper over the same qualified probe implementation for the separate P1 characterization only: authorized scenario `500`, SCIP `limits/time=600`, and external solve cap `660`.

CoreHPC request in `run_corehpc.sbatch`: CPU partition, 1 node, 16 CPUs, 256 GB RAM, 1 hour.

Do not run from this repository unless intentionally launching the qualification probe. A non-empty output directory is refused.
