#!/usr/bin/env python3
"""P1=500 wrapper for the Session-016 DataSAIL scaling probe."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

try:
    from admet.qualification.datasail_scaling import probe
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from admet.qualification.datasail_scaling import probe


P1_AUTHORIZED_CHARACTERIZATION_SCENARIOS = (500,)
P1_SOLVER_OPTIMIZATION_LIMIT_SECONDS = 600
P1_SOLVE_EXTERNAL_PROCESS_CAP_SECONDS = 660


def apply_p1_configuration(target_probe: ModuleType = probe) -> None:
    """Apply the approved P1-only overrides to the qualified probe module."""
    target_probe.AUTHORIZED_CHARACTERIZATION_SCENARIOS = P1_AUTHORIZED_CHARACTERIZATION_SCENARIOS
    target_probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS = P1_SOLVER_OPTIMIZATION_LIMIT_SECONDS
    target_probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS = P1_SOLVE_EXTERNAL_PROCESS_CAP_SECONDS
    target_probe.PHASE_CAPS_SECONDS = {
        "construction": 600.0,
        "canonicalization": 600.0,
        "solve": float(P1_SOLVE_EXTERNAL_PROCESS_CAP_SECONDS),
    }
    target_probe.SCIP_PARAMS = dict(target_probe.SCIP_PARAMS)
    target_probe.SCIP_PARAMS["limits/time"] = P1_SOLVER_OPTIMIZATION_LIMIT_SECONDS


def main(argv: list[str] | None = None) -> int:
    apply_p1_configuration(probe)
    return probe.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
