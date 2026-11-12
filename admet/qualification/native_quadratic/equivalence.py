from __future__ import annotations

from collections.abc import Mapping, Sequence


def reference_cross_partition_leakage(
    family_ids: Sequence[str],
    molecular_weights: Mapping[str, int],
    similarities: Mapping[tuple[str, str], float],
    assignments: Mapping[str, str],
) -> float:
    """
    Compute the approved family-compressed cross-partition leakage objective.

    Each unordered family pair contributes w_i * w_j * S_ij exactly when
    the two immutable families are assigned to different partitions.
    """
    leakage = 0.0

    for left_index, left_id in enumerate(family_ids):
        for right_id in family_ids[left_index + 1 :]:
            pair = (left_id, right_id)

            if pair not in similarities:
                raise KeyError(f"missing similarity for unordered pair {pair!r}")

            if left_id not in molecular_weights:
                raise KeyError(f"missing molecular weight for {left_id!r}")
            if right_id not in molecular_weights:
                raise KeyError(f"missing molecular weight for {right_id!r}")

            if left_id not in assignments:
                raise KeyError(f"missing assignment for {left_id!r}")
            if right_id not in assignments:
                raise KeyError(f"missing assignment for {right_id!r}")

            if assignments[left_id] != assignments[right_id]:
                leakage += (
                    molecular_weights[left_id]
                    * molecular_weights[right_id]
                    * similarities[pair]
                )

    result = float(leakage)
    return result


def quadratic_cross_partition_leakage(
    family_ids: Sequence[str],
    molecular_weights: Mapping[str, int],
    similarities: Mapping[tuple[str, str], float],
    assignments: Mapping[str, str],
) -> float:
    """
    Compute cross-partition leakage as total pair weight minus
    within-partition pair weight.

    For a complete assignment of immutable families,

        total_pair_weight - within_partition_weight

    is exactly equal to the approved cross-partition leakage objective.
    """
    total_pair_weight = 0.0
    within_partition_weight = 0.0

    for left_index, left_id in enumerate(family_ids):
        for right_id in family_ids[left_index + 1 :]:
            pair = (left_id, right_id)

            if pair not in similarities:
                raise KeyError(f"missing similarity for unordered pair {pair!r}")

            if left_id not in molecular_weights:
                raise KeyError(f"missing molecular weight for {left_id!r}")
            if right_id not in molecular_weights:
                raise KeyError(f"missing molecular weight for {right_id!r}")

            if left_id not in assignments:
                raise KeyError(f"missing assignment for {left_id!r}")
            if right_id not in assignments:
                raise KeyError(f"missing assignment for {right_id!r}")

            pair_weight = (
                molecular_weights[left_id]
                * molecular_weights[right_id]
                * similarities[pair]
            )

            total_pair_weight += pair_weight

            if assignments[left_id] == assignments[right_id]:
                within_partition_weight += pair_weight

    result = float(total_pair_weight - within_partition_weight)
    return result


def partition_numeric_totals(
    family_ids: Sequence[str],
    molecular_weights: Mapping[str, int],
    pka_counts: Mapping[str, int],
    clearance_counts: Mapping[str, int],
    assignments: Mapping[str, str],
    partition_names: Sequence[str],
) -> dict[str, dict[str, int]]:
    """
    Measure molecular-identity and endpoint-count totals in each partition.

    These are measurements only. This function does not decide whether
    any partition satisfies a size or endpoint-coverage constraint.
    """
    result = {
        partition_name: {
            "molecular_identities": 0,
            "pka_identities": 0,
            "clearance_identities": 0,
        }
        for partition_name in partition_names
    }

    for family_id in family_ids:
        if family_id not in molecular_weights:
            raise KeyError(f"missing molecular weight for {family_id!r}")
        if family_id not in pka_counts:
            raise KeyError(f"missing pKa count for {family_id!r}")
        if family_id not in clearance_counts:
            raise KeyError(f"missing clearance count for {family_id!r}")
        if family_id not in assignments:
            raise KeyError(f"missing assignment for {family_id!r}")

        partition_name = assignments[family_id]

        if partition_name not in result:
            raise ValueError(
                f"assignment for {family_id!r} uses undeclared partition "
                f"{partition_name!r}"
            )

        result[partition_name]["molecular_identities"] += molecular_weights[family_id]
        result[partition_name]["pka_identities"] += pka_counts[family_id]
        result[partition_name]["clearance_identities"] += clearance_counts[family_id]

    return result


def satisfies_numeric_constraints(
    partition_totals: Mapping[str, Mapping[str, int]],
    lower_bounds: Mapping[str, Mapping[str, int]],
    upper_bounds: Mapping[str, Mapping[str, int]],
) -> bool:
    """
    Independently classify whether measured partition totals satisfy
    explicitly supplied numeric lower and upper bounds.

    Bounds are inputs to this function. This function defines no scientific
    tolerances and performs no relaxation or repair.
    """
    metric_names = (
        "molecular_identities",
        "pka_identities",
        "clearance_identities",
    )

    for partition_name, totals in partition_totals.items():
        if partition_name not in lower_bounds:
            raise KeyError(f"missing lower bounds for {partition_name!r}")
        if partition_name not in upper_bounds:
            raise KeyError(f"missing upper bounds for {partition_name!r}")

        for metric_name in metric_names:
            if metric_name not in totals:
                raise KeyError(
                    f"missing measured {metric_name!r} for {partition_name!r}"
                )
            if metric_name not in lower_bounds[partition_name]:
                raise KeyError(
                    f"missing lower bound for {partition_name!r} "
                    f"{metric_name!r}"
                )
            if metric_name not in upper_bounds[partition_name]:
                raise KeyError(
                    f"missing upper bound for {partition_name!r} "
                    f"{metric_name!r}"
                )

            value = totals[metric_name]
            lower = lower_bounds[partition_name][metric_name]
            upper = upper_bounds[partition_name][metric_name]

            if lower > upper:
                raise ValueError(
                    f"lower bound exceeds upper bound for "
                    f"{partition_name!r} {metric_name!r}"
                )

            if value < lower or value > upper:
                return False

    return True


def build_native_gurobi_model(
    family_ids: Sequence[str],
    partition_names: Sequence[str],
    molecular_weights: Mapping[str, int],
    pka_counts: Mapping[str, int],
    clearance_counts: Mapping[str, int],
    similarities: Mapping[tuple[str, str], float],
    lower_bounds: Mapping[str, Mapping[str, int]],
    upper_bounds: Mapping[str, Mapping[str, int]],
):
    """
    Construct, but do not optimize, the exact native Gurobi binary-quadratic
    representation of the approved family-level splitting problem.
    """
    import gurobipy as gp

    model = gp.Model("native_quadratic_equivalence")
    model.Params.OutputFlag = 0

    assignment_variables = {
        (family_id, partition_name): model.addVar(
            vtype=gp.GRB.BINARY,
            name=f"x[{family_id},{partition_name}]",
        )
        for family_id in family_ids
        for partition_name in partition_names
    }

    for family_id in family_ids:
        model.addConstr(
            gp.quicksum(
                assignment_variables[(family_id, partition_name)]
                for partition_name in partition_names
            )
            == 1,
            name=f"assign_once[{family_id}]",
        )

    metric_counts = {
        "molecular_identities": molecular_weights,
        "pka_identities": pka_counts,
        "clearance_identities": clearance_counts,
    }

    for partition_name in partition_names:
        if partition_name not in lower_bounds:
            raise KeyError(f"missing lower bounds for {partition_name!r}")
        if partition_name not in upper_bounds:
            raise KeyError(f"missing upper bounds for {partition_name!r}")

        for metric_name, counts in metric_counts.items():
            if metric_name not in lower_bounds[partition_name]:
                raise KeyError(
                    f"missing lower bound for {partition_name!r} "
                    f"{metric_name!r}"
                )
            if metric_name not in upper_bounds[partition_name]:
                raise KeyError(
                    f"missing upper bound for {partition_name!r} "
                    f"{metric_name!r}"
                )

            lower = lower_bounds[partition_name][metric_name]
            upper = upper_bounds[partition_name][metric_name]

            if lower > upper:
                raise ValueError(
                    f"lower bound exceeds upper bound for "
                    f"{partition_name!r} {metric_name!r}"
                )

            expression = gp.quicksum(
                counts[family_id]
                * assignment_variables[(family_id, partition_name)]
                for family_id in family_ids
            )

            model.addConstr(
                expression >= lower,
                name=f"{metric_name}_lower[{partition_name}]",
            )
            model.addConstr(
                expression <= upper,
                name=f"{metric_name}_upper[{partition_name}]",
            )

    within_partition_similarity = gp.QuadExpr()

    for left_index, left_id in enumerate(family_ids):
        for right_id in family_ids[left_index + 1 :]:
            pair = (left_id, right_id)

            if pair not in similarities:
                raise KeyError(f"missing similarity for unordered pair {pair!r}")

            coefficient = (
                molecular_weights[left_id]
                * molecular_weights[right_id]
                * similarities[pair]
            )

            for partition_name in partition_names:
                within_partition_similarity += (
                    coefficient
                    * assignment_variables[(left_id, partition_name)]
                    * assignment_variables[(right_id, partition_name)]
                )

    model.setObjective(
        within_partition_similarity,
        gp.GRB.MAXIMIZE,
    )

    model.update()

    result = {
        "model": model,
        "assignment_variables": assignment_variables,
    }
    return result
