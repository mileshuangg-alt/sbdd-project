from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticFixture:
    family_ids: tuple[str, ...]
    partition_names: tuple[str, ...]
    molecular_weights: dict[str, int]
    pka_counts: dict[str, int]
    clearance_counts: dict[str, int]
    similarities: dict[tuple[str, str], float]


def build_synthetic_fixture(n_families: int) -> SyntheticFixture:
    """
    Build a deterministic synthetic family-level fixture for representation-cost
    qualification.

    Values are probe fixtures only. They have no scientific or production
    authority.
    """
    if n_families < 2:
        raise ValueError("n_families must be at least 2")

    family_ids = tuple(
        f"family_{index:06d}"
        for index in range(n_families)
    )

    partition_names = ("dev", "test")

    molecular_weights = {
        family_id: 1 + (index % 7)
        for index, family_id in enumerate(family_ids)
    }

    pka_counts = {
        family_id: index % 4
        for index, family_id in enumerate(family_ids)
    }

    clearance_counts = {
        family_id: (index * 3) % 5
        for index, family_id in enumerate(family_ids)
    }

    similarities: dict[tuple[str, str], float] = {}

    for left_index, left_id in enumerate(family_ids):
        for right_index in range(left_index + 1, n_families):
            right_id = family_ids[right_index]

            # Deterministic synthetic value in (0, 1].
            numerator = (
                ((left_index + 1) * 37)
                + ((right_index + 1) * 61)
            ) % 997

            similarity = (numerator + 1) / 997.0

            similarities[(left_id, right_id)] = similarity

    result = SyntheticFixture(
        family_ids=family_ids,
        partition_names=partition_names,
        molecular_weights=molecular_weights,
        pka_counts=pka_counts,
        clearance_counts=clearance_counts,
        similarities=similarities,
    )
    return result


def build_fixture_bounds(
    fixture: SyntheticFixture,
) -> tuple[
    dict[str, dict[str, int]],
    dict[str, dict[str, int]],
]:
    """
    Build deterministic fixture-only exact bounds from an alternating
    dev/test reference assignment.

    These bounds exist only to reproduce the numeric-constraint structure
    of the qualified formulation. They have no scientific or production
    authority.
    """
    reference_assignments = {
        family_id: fixture.partition_names[index % len(fixture.partition_names)]
        for index, family_id in enumerate(fixture.family_ids)
    }

    metric_counts = {
        "molecular_identities": fixture.molecular_weights,
        "pka_identities": fixture.pka_counts,
        "clearance_identities": fixture.clearance_counts,
    }

    totals = {
        partition_name: {
            metric_name: 0
            for metric_name in metric_counts
        }
        for partition_name in fixture.partition_names
    }

    for family_id in fixture.family_ids:
        partition_name = reference_assignments[family_id]

        for metric_name, counts in metric_counts.items():
            totals[partition_name][metric_name] += counts[family_id]

    lower_bounds = {
        partition_name: dict(metric_totals)
        for partition_name, metric_totals in totals.items()
    }

    upper_bounds = {
        partition_name: dict(metric_totals)
        for partition_name, metric_totals in totals.items()
    }

    result = (lower_bounds, upper_bounds)
    return result


def construct_native_model(n_families: int) -> dict[str, object]:
    """
    Construct and inspect the exact native quadratic Stage-A model.

    This function MUST NOT optimize the model.
    """
    from admet.qualification.native_quadratic.equivalence import (
        build_native_gurobi_model,
    )

    fixture = build_synthetic_fixture(n_families)
    lower_bounds, upper_bounds = build_fixture_bounds(fixture)

    built = build_native_gurobi_model(
        family_ids=fixture.family_ids,
        partition_names=fixture.partition_names,
        molecular_weights=fixture.molecular_weights,
        pka_counts=fixture.pka_counts,
        clearance_counts=fixture.clearance_counts,
        similarities=fixture.similarities,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
    )

    model = built["model"]
    objective = model.getObjective()

    expected_binary_variables = (
        n_families * len(fixture.partition_names)
    )

    expected_linear_constraints = (
        n_families
        + (
            3
            * 2
            * len(fixture.partition_names)
        )
    )

    expected_quadratic_terms = (
        (n_families * (n_families - 1) // 2)
        * len(fixture.partition_names)
    )

    if model.NumVars != expected_binary_variables:
        raise AssertionError(
            f"variable count mismatch: expected "
            f"{expected_binary_variables}, observed {model.NumVars}"
        )

    if model.NumBinVars != expected_binary_variables:
        raise AssertionError(
            f"binary-variable count mismatch: expected "
            f"{expected_binary_variables}, observed {model.NumBinVars}"
        )

    if model.NumConstrs != expected_linear_constraints:
        raise AssertionError(
            f"linear-constraint count mismatch: expected "
            f"{expected_linear_constraints}, observed {model.NumConstrs}"
        )

    if objective.size() != expected_quadratic_terms:
        raise AssertionError(
            f"quadratic-term count mismatch: expected "
            f"{expected_quadratic_terms}, observed {objective.size()}"
        )

    result = {
        "model": model,
        "fixture": fixture,
        "lower_bounds": lower_bounds,
        "upper_bounds": upper_bounds,
        "dimensions": {
            "binary_variables": model.NumBinVars,
            "linear_constraints": model.NumConstrs,
            "quadratic_terms": objective.size(),
        },
    }
    return result


def measure_native_construction(
    n_families: int,
    sample_interval_seconds: float = 0.05,
) -> dict[str, object]:
    """
    Measure wall time and current-process RSS while constructing the exact
    native quadratic model.

    This function MUST NOT optimize the model.
    """
    import os
    import threading
    import time

    import psutil

    if sample_interval_seconds <= 0:
        raise ValueError("sample_interval_seconds must be positive")

    process = psutil.Process(os.getpid())
    rss_samples: list[dict[str, float | int]] = []
    stop_event = threading.Event()

    start_time = time.perf_counter()
    rss_before = process.memory_info().rss

    def sample_rss() -> None:
        while not stop_event.is_set():
            rss_samples.append(
                {
                    "t_seconds": time.perf_counter() - start_time,
                    "rss_bytes": process.memory_info().rss,
                }
            )
            stop_event.wait(sample_interval_seconds)

    sampler = threading.Thread(
        target=sample_rss,
        name="native-construction-rss-sampler",
        daemon=True,
    )
    sampler.start()

    try:
        built = construct_native_model(n_families)
    finally:
        stop_event.set()
        sampler.join()

    elapsed_seconds = time.perf_counter() - start_time
    rss_after = process.memory_info().rss

    rss_samples.append(
        {
            "t_seconds": elapsed_seconds,
            "rss_bytes": rss_after,
        }
    )

    peak_rss = max(
        sample["rss_bytes"]
        for sample in rss_samples
    )

    model = built["model"]

    if model.SolCount != 0:
        raise AssertionError(
            "construction-only qualification unexpectedly produced a solution"
        )

    result = {
        "n_families": n_families,
        "elapsed_seconds": elapsed_seconds,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "peak_rss_bytes": peak_rss,
        "rss_samples": rss_samples,
        "dimensions": built["dimensions"],
        "solution_count": model.SolCount,
    }
    return result
