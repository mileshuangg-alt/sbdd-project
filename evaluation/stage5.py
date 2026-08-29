def assign_target_evidence_level(
    target_evidence,
):
    """Assign the Stage-5 target interaction evidence level."""

    structure_available = target_evidence.get(
        "structure_available",
        False,
    )

    cognate_complex_available = target_evidence.get(
        "cognate_complex_available",
        False,
    )

    apo_structure_available = target_evidence.get(
        "apo_structure_available",
        False,
    )

    homolog_complex_available = target_evidence.get(
        "homolog_complex_available",
        False,
    )

    pocket_conserved = target_evidence.get(
        "pocket_conserved",
        False,
    )

    if not structure_available:
        evidence_level = None

    elif cognate_complex_available:
        evidence_level = 1

    elif (
        apo_structure_available
        or (
            homolog_complex_available
            and pocket_conserved
        )
    ):
        evidence_level = 2

    else:
        evidence_level = 3

    result = {
        "evidence_level": evidence_level,
        "in_scope": structure_available,
    }

    return result


def validate_target_evidence(
    target_evidence,
):
    """Validate internal consistency of the Stage-5 target evidence record."""

    errors = []

    structure_available = target_evidence[
        "structure_available"
    ]

    evidence_level = target_evidence.get(
        "evidence_level"
    )

    homology_inferred = target_evidence.get(
        "homology_inferred",
        False,
    )

    gate_validation = target_evidence.get(
        "gate_validation"
    )

    if not structure_available:
        errors.append(
            "Stage 5 is out of scope because no "
            "3D target structure is available."
        )

    if structure_available and (
        evidence_level not in {1, 2, 3}
    ):
        errors.append(
            "Evidence level must be 1, 2, or 3 "
            "when a 3D target structure is available."
        )

    if not structure_available and (
        evidence_level is not None
    ):
        errors.append(
            "A target without a 3D structure cannot "
            "be assigned a Stage-5 evidence level."
        )

    if evidence_level == 1 and homology_inferred:
        errors.append(
            "Level 1 cannot be marked as "
            "homology-inferred."
        )

    if evidence_level == 3 and homology_inferred:
        errors.append(
            "Level 3 cannot be supported by "
            "homolog interaction evidence."
        )

    if evidence_level == 2 and (
        "pocket_sequence_identity"
        not in target_evidence
    ):
        errors.append(
            "Level 2 requires documented "
            "pocket sequence identity evidence."
        )

    if evidence_level == 2 and (
        "pocket_superposition_rmsd"
        not in target_evidence
    ):
        errors.append(
            "Level 2 requires documented "
            "pocket superposition RMSD evidence."
        )

    if gate_validation not in {
        None,
        "ESTABLISHED",
        "NOT_ESTABLISHED",
    }:
        errors.append(
            "Gate validation must be "
            "ESTABLISHED or NOT_ESTABLISHED."
        )

    result = {
        "valid": not errors,
        "errors": errors,
    }

    return result


def build_stage5_ruling(
    target_evidence,
):
    """Build the final Stage-5 ruling from a validated evidence record."""

    evidence_level = target_evidence.get(
        "evidence_level"
    )

    gate_validation = target_evidence.get(
        "gate_validation"
    )

    ruling = {
        "in_scope": target_evidence[
            "structure_available"
        ],
        "evidence_level": evidence_level,
        "gate_validation": gate_validation,
        "claims_mode": None,
        "hard_attrition_permitted": False,
        "claims_cap": None,
        "interaction_unverified": False,
        "homology_inferred": False,
        "level3_verdict": None,
        "level3_lane": None,
    }

    if not ruling["in_scope"]:
        ruling[
            "claims_mode"
        ] = "out_of_scope"

        return ruling

    if evidence_level == 1:
        if gate_validation == "ESTABLISHED":
            ruling[
                "claims_mode"
            ] = "validated_compatibility"

            ruling[
                "hard_attrition_permitted"
            ] = True

        else:
            ruling[
                "claims_mode"
            ] = "characterization"

            ruling[
                "claims_cap"
            ] = (
                "claims capped pending "
                "gate validation"
            )

    elif evidence_level == 2:
        ruling[
            "claims_mode"
        ] = "interaction_characterization"

        ruling[
            "homology_inferred"
        ] = True

    elif evidence_level == 3:
        ruling[
            "claims_mode"
        ] = "inconclusive"

        ruling[
            "interaction_unverified"
        ] = True

        ruling[
            "level3_verdict"
        ] = "INCONCLUSIVE"

        ruling[
            "level3_lane"
        ] = (
            "predicted_pocket_characterization"
        )

    return ruling


def build_stage5_target_record(
    target_evidence,
):
    """Build the canonical Stage-5 target record."""

    assigned_level = assign_target_evidence_level(
        target_evidence
    )

    evidence = {
        **target_evidence,
        **assigned_level,
    }

    validation = validate_target_evidence(
        evidence
    )

    if not validation["valid"]:
        raise ValueError(
            "Invalid Stage-5 target evidence record: "
            f"{validation['errors']}"
        )

    ruling = build_stage5_ruling(
        evidence
    )

    target_record = {
        "target_id": evidence.get(
            "target_id"
        ),
        "evidence": evidence,
        "validation": validation,
        "ruling": ruling,
    }

    return target_record


def run_stage5_ruling_checks():
    """Verify the generalized Stage-5 ruling framework."""

    cases = {
        "a2a_current": {
            "evidence": {
                "target_id": "A2A",
                "structure_available": True,
                "cognate_complex_available": True,
                "homology_inferred": False,
                "gate_validation":
                    "NOT_ESTABLISHED",
            },
            "expected": {
                "evidence_level": 1,
                "claims_mode":
                    "characterization",
                "hard_attrition_permitted":
                    False,
                "claims_cap":
                    "claims capped pending "
                    "gate validation",
            },
        },
        "level1_validated": {
            "evidence": {
                "target_id": "test_level1",
                "structure_available": True,
                "cognate_complex_available": True,
                "homology_inferred": False,
                "gate_validation":
                    "ESTABLISHED",
            },
            "expected": {
                "evidence_level": 1,
                "claims_mode":
                    "validated_compatibility",
                "hard_attrition_permitted":
                    True,
                "claims_cap": None,
            },
        },
        "level2": {
            "evidence": {
                "target_id": "test_level2",
                "structure_available": True,
                "cognate_complex_available": False,
                "apo_structure_available": False,
                "homolog_complex_available": True,
                "pocket_conserved": True,
                "pocket_sequence_identity": 0.90,
                "pocket_superposition_rmsd": 1.2,
                "homology_inferred": True,
                "gate_validation": None,
            },
            "expected": {
                "evidence_level": 2,
                "claims_mode":
                    "interaction_characterization",
                "hard_attrition_permitted":
                    False,
                "homology_inferred":
                    True,
            },
        },
        "level3": {
            "evidence": {
                "target_id": "test_level3",
                "structure_available": True,
                "cognate_complex_available": False,
                "apo_structure_available": False,
                "homolog_complex_available": False,
                "pocket_conserved": False,
                "homology_inferred": False,
                "gate_validation": None,
            },
            "expected": {
                "evidence_level": 3,
                "claims_mode":
                    "inconclusive",
                "hard_attrition_permitted":
                    False,
                "interaction_unverified":
                    True,
                "level3_verdict":
                    "INCONCLUSIVE",
                "level3_lane":
                    "predicted_pocket_characterization",
            },
        },
    }

    for name, case in cases.items():

        target_record = build_stage5_target_record(
            case["evidence"]
        )

        ruling = target_record[
            "ruling"
        ]

        expected = case[
            "expected"
        ]

        actual_evidence_level = (
            target_record[
                "evidence"
            ]["evidence_level"]
        )

        if (
            actual_evidence_level
            != expected["evidence_level"]
        ):
            raise AssertionError(
                f"{name}: evidence_level = "
                f"{actual_evidence_level!r}, "
                f"expected "
                f"{expected['evidence_level']!r}"
            )

        for key, expected_value in (
            expected.items()
        ):
            if key == "evidence_level":
                continue

            actual_value = ruling.get(
                key
            )

            if (
                actual_value
                != expected_value
            ):
                raise AssertionError(
                    f"{name}: {key} = "
                    f"{actual_value!r}, "
                    f"expected "
                    f"{expected_value!r}"
                )

    print(
        "PASS: Stage-5 ruling framework "
        "verified against test cases."
    )


def main():
    """Run Stage-5 ruling framework checks."""

    run_stage5_ruling_checks()


if __name__ == "__main__":
    main()
