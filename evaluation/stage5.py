import json
from copy import deepcopy
from pathlib import Path


GATE_VALIDATION_VALUES = {
    None,
    "ESTABLISHED",
    "NOT_ESTABLISHED",
}
GATE_VALIDATION_MESSAGE = (
    "None, ESTABLISHED, or NOT_ESTABLISHED"
)

AUTHORITY_FIELDS = [
    "molecule_level_claims",
    "hard_attrition",
    "pose_level_claims",
    "general_specificity",
]

OUT_OF_SCOPE_ROUTE = "STAGE5_OUT_OF_SCOPE"
LEVEL1_ROUTE = "LEVEL1_TARGET_SPECIFIC_INTERACTION"
LEVEL2_ROUTE = "LEVEL2_INTERACTION_CHARACTERIZATION"
LEVEL3_ROUTE = "LEVEL3_EVIDENCE_GAP"

INTERACTION_UNVERIFIED_FLAG = "INTERACTION-UNVERIFIED"
HOMOLOGY_INFERRED_LABEL = "HOMOLOGY-INFERRED"

D018_MIN_MAPPING_COVERAGE = 1.0
D018_MIN_MAPPED_POCKET_RESIDUES = 11
D018_MAX_POCKET_RMSD_ANGSTROM = 0.5370920576693073


def load_stage5_target_config(config_path):
    """Load a Stage-5 target evidence/router config from JSON."""

    config_path = Path(config_path)

    with config_path.open("r") as handle:
        config = json.load(handle)

    validate_stage5_target_config(config)

    return config


def validate_stage5_target_config(config):
    """Validate fields required by the generic Stage-5 router."""

    required_top_level = [
        "schema_version",
        "target_id",
        "evidence",
    ]

    for key in required_top_level:
        if key not in config:
            raise ValueError(
                f"Stage-5 config missing required key: {key}"
            )

    if config["schema_version"] != 1:
        raise ValueError(
            "Unsupported Stage-5 config schema_version: "
            f"{config['schema_version']!r}"
        )

    evidence = config["evidence"]

    if "structure_available" not in evidence:
        raise ValueError(
            "Stage-5 evidence missing required key: "
            "structure_available"
        )

    implementation = config.get(
        "interaction_implementation"
    )

    if implementation is None:
        return

    required_implementation = [
        "implementation_id",
    ]

    for key in required_implementation:
        if key not in implementation:
            raise ValueError(
                "Stage-5 interaction implementation missing "
                f"required key: {key}"
            )

    authority = implementation.get(
        "authority",
        {},
    )

    if (
        "gate_validation" in authority
        and authority["gate_validation"] not in GATE_VALIDATION_VALUES
    ):
        raise ValueError(
            "Stage-5 implementation authority gate_validation "
            f"must be {GATE_VALIDATION_MESSAGE}."
        )


def assign_target_evidence_level(target_evidence):
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

    elif apo_structure_available or (
        homolog_complex_available and pocket_conserved
    ):
        evidence_level = 2

    else:
        evidence_level = 3

    return {
        "evidence_level": evidence_level,
        "in_scope": structure_available,
    }


def validate_target_evidence(target_evidence):
    """Validate internal consistency of a Stage-5 evidence record."""

    errors = []
    structure_available = target_evidence["structure_available"]
    evidence_level = target_evidence.get(
        "evidence_level"
    )
    homology_inferred = target_evidence.get(
        "homology_inferred",
        False,
    )
    homolog_complex_available = target_evidence.get(
        "homolog_complex_available",
        False,
    )
    gate_validation = target_evidence.get(
        "gate_validation"
    )

    if structure_available and evidence_level not in {1, 2, 3}:
        errors.append(
            "Evidence level must be 1, 2, or 3 "
            "when a 3D target structure is available."
        )

    if not structure_available and evidence_level is not None:
        errors.append(
            "A target without a 3D structure cannot "
            "be assigned a Stage-5 evidence level."
        )

    if evidence_level == 1 and homology_inferred:
        errors.append(
            "Level 1 cannot be marked as homology-inferred."
        )

    if evidence_level == 3 and homology_inferred:
        errors.append(
            "Level 3 cannot be supported by homolog "
            "interaction evidence."
        )

    if evidence_level == 2 and homolog_complex_available:
        if target_evidence.get("pocket_conserved") is not True:
            errors.append(
                "Homolog-supported Level 2 requires "
                "pocket_conserved to be True."
            )

        if "mapping_coverage" not in target_evidence:
            errors.append(
                "Homolog-supported Level 2 requires documented "
                "D018 mapping coverage evidence."
            )

        if "mapped_pocket_residue_count" not in target_evidence:
            errors.append(
                "Homolog-supported Level 2 requires documented "
                "D018 mapped-pocket residue count evidence."
            )

        if "pocket_superposition_rmsd" not in target_evidence:
            errors.append(
                "Homolog-supported Level 2 requires documented "
                "D018 pocket superposition RMSD evidence."
            )

        if "level2_pocket_eligible" not in target_evidence:
            errors.append(
                "Homolog-supported Level 2 requires documented "
                "D018 pocket eligibility."
            )

        if target_evidence.get("level2_pocket_eligible") is not True:
            errors.append(
                "Homolog-supported Level 2 requires D018 "
                "pocket eligibility to be True."
            )

    if gate_validation not in GATE_VALIDATION_VALUES:
        errors.append(
            f"Gate validation must be {GATE_VALIDATION_MESSAGE}."
        )

    return {
        "valid": not errors,
        "errors": errors,
    }


def build_stage5_ruling(target_evidence, implementation=None):
    """Build the Stage-5 ruling from validated evidence and artifacts."""

    evidence_level = target_evidence.get(
        "evidence_level"
    )
    gate_validation = target_evidence.get(
        "gate_validation"
    )
    uses_homolog = target_evidence.get(
        "homolog_complex_available",
        False,
    )
    homology_inferred = uses_homolog or target_evidence.get(
        "homology_inferred",
        False,
    )

    ruling = {
        "in_scope": target_evidence["structure_available"],
        "evidence_level": evidence_level,
        "route": None,
        "verdict": None,
        "lane": None,
        "gate_validation": gate_validation,
        "claims_mode": None,
        "hard_attrition_permitted": False,
        "claims_cap": None,
        "labels": [],
        "flags": [],
        "interaction_unverified": False,
        "homology_inferred": False,
        "level3_verdict": None,
        "level3_lane": None,
        "stage3_stage5_separation": (
            "Stage 3 geometry evidence does not establish "
            "Stage 5 target-interaction evidence."
        ),
    }

    if not ruling["in_scope"]:
        ruling.update(
            {
                "route": OUT_OF_SCOPE_ROUTE,
                "verdict": OUT_OF_SCOPE_ROUTE,
                "claims_mode": "out_of_scope",
            }
        )
        return ruling

    if evidence_level == 1:
        apply_level1_ruling(
            ruling,
            implementation,
        )

    elif evidence_level == 2:
        ruling.update(
            {
                "route": LEVEL2_ROUTE,
                "verdict": "CHARACTERIZATION_ONLY",
                "lane": "interaction_characterization",
                "claims_mode": "interaction_characterization",
            }
        )

        if homology_inferred:
            ruling["homology_inferred"] = True
            ruling["labels"].append(
                HOMOLOGY_INFERRED_LABEL
            )

    elif evidence_level == 3:
        ruling.update(
            {
                "route": LEVEL3_ROUTE,
                "verdict": "INCONCLUSIVE",
                "lane": "evaluation_continues",
                "claims_mode": "inconclusive",
                "interaction_unverified": True,
                "level3_verdict": "INCONCLUSIVE",
                "level3_lane": "evaluation_continues",
            }
        )
        ruling["flags"].append(
            INTERACTION_UNVERIFIED_FLAG
        )

    return ruling


def apply_level1_ruling(ruling, implementation):
    """Route Level-1 targets to a configured implementation artifact."""

    ruling.update(
        {
            "route": LEVEL1_ROUTE,
            "verdict": "TARGET_SPECIFIC_IMPLEMENTATION",
            "lane": "target_specific_interaction",
            "claims_mode": "characterization",
        }
    )

    authority = normalize_level1_authority(
        implementation.get("authority", {})
        if implementation is not None
        else {}
    )

    if implementation is not None:
        ruling["target_specific_implementation"] = {
            "implementation_id": implementation[
                "implementation_id"
            ],
            "artifact_path": implementation.get(
                "artifact_path"
            ),
            "authority": deepcopy(authority),
        }
        gate_validation = authority.get(
            "gate_validation",
            ruling["gate_validation"],
        )
        ruling["gate_validation"] = gate_validation

    else:
        gate_validation = ruling["gate_validation"]

    ruling["level1_authority"] = deepcopy(
        authority
    )
    ruling["hard_attrition_permitted"] = authority[
        "hard_attrition"
    ]

    if authority["molecule_level_claims"]:
        ruling["claims_mode"] = "molecule_level_claims"

    if not any(
        authority[field] for field in AUTHORITY_FIELDS
    ):
        ruling["claims_cap"] = (
            "claims not authorized by frozen implementation authority"
        )
    elif authority.get("claims_status") is not None:
        ruling["claims_cap"] = authority["claims_status"]


def normalize_level1_authority(authority):
    """Default missing Level-1 authority conservatively."""

    normalized = {
        field: bool(authority.get(field, False))
        for field in AUTHORITY_FIELDS
    }

    for key, value in authority.items():
        if key not in normalized:
            normalized[key] = deepcopy(value)

    return normalized



D018_MIN_MAPPING_COVERAGE = 1.0
D018_MIN_MAPPED_POCKET_RESIDUES = 11
D018_MAX_POCKET_RMSD_ANGSTROM = 0.5370920576693073


def evaluate_level2_pocket_conservation(
    *,
    mapping_coverage: float,
    mapped_pocket_residue_count: int,
    pocket_superposition_rmsd: float,
) -> dict[str, object]:
    """Apply the frozen D018 Level-2 homolog-pocket conservation rule."""

    if not 0.0 <= mapping_coverage <= 1.0:
        raise ValueError(
            "mapping_coverage must be between 0.0 and 1.0"
        )

    if mapped_pocket_residue_count < 0:
        raise ValueError(
            "mapped_pocket_residue_count must be non-negative"
        )

    if pocket_superposition_rmsd < 0.0:
        raise ValueError(
            "pocket_superposition_rmsd must be non-negative"
        )

    eligible = (
        mapping_coverage == D018_MIN_MAPPING_COVERAGE
        and mapped_pocket_residue_count
        >= D018_MIN_MAPPED_POCKET_RESIDUES
    )

    pocket_conserved = (
        eligible
        and pocket_superposition_rmsd
        <= D018_MAX_POCKET_RMSD_ANGSTROM
    )

    return {
        "eligible": eligible,
        "pocket_conserved": pocket_conserved,
        "mapping_coverage": mapping_coverage,
        "mapped_pocket_residue_count": mapped_pocket_residue_count,
        "pocket_superposition_rmsd": pocket_superposition_rmsd,
        "sequence_identity_used": False,
        "minimum_mapping_coverage": D018_MIN_MAPPING_COVERAGE,
        "minimum_mapped_pocket_residues": D018_MIN_MAPPED_POCKET_RESIDUES,
        "maximum_pocket_rmsd_angstrom": D018_MAX_POCKET_RMSD_ANGSTROM,
    }


def load_d017_pocket_measurement_artifact(artifact_path):
    """Load a persisted D017 pocket-measurement artifact."""

    artifact_path = Path(artifact_path)

    if not artifact_path.exists():
        raise FileNotFoundError(
            f"D017 pocket-measurement artifact not found: "
            f"{artifact_path}"
        )

    with artifact_path.open("r") as handle:
        artifact = json.load(handle)

    measurement = artifact.get("measurement")
    if not isinstance(measurement, dict):
        raise ValueError(
            "D017 pocket-measurement artifact missing "
            "measurement object."
        )

    required = {
        "mapping_coverage",
        "mapped_pocket_residues",
        "pocket_superposition_rmsd",
    }

    missing = sorted(required - measurement.keys())
    if missing:
        raise ValueError(
            "D017 pocket-measurement artifact missing required "
            f"measurement fields: {missing}"
        )

    return artifact


def enrich_stage5_evidence_from_d017_artifact(target_evidence):
    """Populate Stage-5 homolog-pocket measurements from frozen D017 output."""

    artifact_reference = target_evidence.get(
        "d017_pocket_measurement_artifact"
    )

    if artifact_reference is None:
        return target_evidence

    artifact = load_d017_pocket_measurement_artifact(
        artifact_reference
    )
    measurement = artifact["measurement"]

    enriched = deepcopy(target_evidence)

    enriched["mapping_coverage"] = measurement[
        "mapping_coverage"
    ]
    enriched["mapped_pocket_residue_count"] = len(
        measurement["mapped_pocket_residues"]
    )
    enriched["pocket_superposition_rmsd"] = measurement[
        "pocket_superposition_rmsd"
    ]
    enriched["d017_pocket_measurement_artifact"] = (
        str(artifact_reference)
    )

    return enriched

def build_stage5_target_record(target_evidence, implementation=None):
    """Build the canonical Stage-5 target record."""

    target_evidence = enrich_stage5_evidence_from_d017_artifact(
        target_evidence
    )

    target_evidence = deepcopy(target_evidence)

    if (
        "mapping_coverage" in target_evidence
        and "mapped_pocket_residue_count" in target_evidence
        and "pocket_superposition_rmsd" in target_evidence
    ):
        conservation = evaluate_level2_pocket_conservation(
            mapping_coverage=target_evidence["mapping_coverage"],
            mapped_pocket_residue_count=target_evidence[
                "mapped_pocket_residue_count"
            ],
            pocket_superposition_rmsd=target_evidence[
                "pocket_superposition_rmsd"
            ],
        )

        target_evidence.update(
            {
                "level2_pocket_eligible": conservation["eligible"],
                "pocket_conserved": conservation["pocket_conserved"],
                "d018_conservation_rule": {
                    "minimum_mapping_coverage": (
                        conservation["minimum_mapping_coverage"]
                    ),
                    "minimum_mapped_pocket_residues": (
                        conservation["minimum_mapped_pocket_residues"]
                    ),
                    "maximum_pocket_rmsd_angstrom": (
                        conservation["maximum_pocket_rmsd_angstrom"]
                    ),
                    "sequence_identity_used": (
                        conservation["sequence_identity_used"]
                    ),
                },
            }
        )

    assigned_level = assign_target_evidence_level(
        target_evidence
    )
    evidence = {
        **target_evidence,
        **assigned_level,
    }

    if evidence["evidence_level"] == 2 and evidence.get(
        "homolog_complex_available",
        False,
    ):
        evidence["homology_inferred"] = True

    validation = validate_target_evidence(
        evidence
    )

    if not validation["valid"]:
        raise ValueError(
            "Invalid Stage-5 target evidence record: "
            f"{validation['errors']}"
        )

    ruling = build_stage5_ruling(
        evidence,
        implementation=implementation,
    )

    return {
        "target_id": evidence.get(
            "target_id"
        ),
        "evidence": evidence,
        "validation": validation,
        "ruling": ruling,
    }


def build_stage5_record_from_config(config):
    """Build a target record from a loaded Stage-5 config."""

    validate_stage5_target_config(config)

    target_evidence = {
        "target_id": config["target_id"],
        **config["evidence"],
    }

    implementation = config.get(
        "interaction_implementation"
    )

    return build_stage5_target_record(
        target_evidence,
        implementation=implementation,
    )


def build_stage5_report(config, molecule_records=None):
    """Build the generic Stage-5 reporting contract."""

    target_record = build_stage5_record_from_config(
        config
    )
    routed_molecules = propagate_stage5_flags(
        molecule_records or [],
        target_record["ruling"],
    )

    return {
        "schema_version": 1,
        "target_id": target_record["target_id"],
        "target_record": target_record,
        "molecules": routed_molecules,
        "headline_survival_policy": (
            "Level-3 interaction-unverified molecule counts are "
            "reported separately from headline pipeline survival rates."
        ),
    }


def propagate_stage5_flags(molecule_records, ruling):
    """Propagate Stage-5 reporting flags without changing prior results."""

    routed_records = []

    for molecule_record in molecule_records:
        routed_record = deepcopy(
            molecule_record
        )
        routed_record["stage5_route"] = ruling["route"]
        routed_record["stage5_verdict"] = ruling["verdict"]
        routed_record["stage5_lane"] = ruling["lane"]
        routed_record["stage5_flags"] = list(
            ruling["flags"]
        )
        routed_record["stage5_labels"] = list(
            ruling["labels"]
        )
        routed_record["interaction_unverified"] = ruling[
            "interaction_unverified"
        ]

        if ruling["interaction_unverified"]:
            routed_record[
                "stage5_reporting_bucket"
            ] = "interaction_unverified_separate_count"

        routed_records.append(
            routed_record
        )

    return routed_records


def run_stage5_ruling_checks():
    """Verify the generalized Stage-5 routing framework."""

    cases = {
        "out_of_scope": {
            "config": {
                "schema_version": 1,
                "target_id": "test_no_structure",
                "evidence": {
                    "structure_available": False,
                    "gate_validation": None,
                },
            },
            "expected": {
                "route": OUT_OF_SCOPE_ROUTE,
                "verdict": OUT_OF_SCOPE_ROUTE,
            },
        },
        "level1_claims_capped": {
            "config": {
                "schema_version": 1,
                "target_id": "test_level1",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": True,
                    "gate_validation": "NOT_ESTABLISHED",
                },
                "interaction_implementation": {
                    "implementation_id": "test_reader",
                    "artifact_path": "artifacts/test.csv",
                    "authority": {
                        "gate_validation": "NOT_ESTABLISHED",
                        "molecule_level_claims": True,
                        "hard_attrition": False,
                        "pose_level_claims": False,
                        "general_specificity": False,
                        "claims_status": (
                            "claims capped pending gate validation"
                        ),
                    },
                },
            },
            "expected": {
                "route": LEVEL1_ROUTE,
                "claims_mode": "molecule_level_claims",
                "hard_attrition_permitted": False,
                "claims_cap": (
                    "claims capped pending gate validation"
                ),
            },
        },
        "level2_homology": {
            "config": {
                "schema_version": 1,
                "target_id": "test_level2",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": False,
                    "apo_structure_available": False,
                    "homolog_complex_available": True,
                    "mapping_coverage": 1.0,
                    "mapped_pocket_residue_count": 14,
                    "pocket_superposition_rmsd": 0.4398073045565676,
                    "gate_validation": None,
                },
            },
            "expected": {
                "route": LEVEL2_ROUTE,
                "claims_mode": "interaction_characterization",
                "labels": [HOMOLOGY_INFERRED_LABEL],
            },
        },
        "level3": {
            "config": {
                "schema_version": 1,
                "target_id": "test_level3",
                "evidence": {
                    "structure_available": True,
                    "cognate_complex_available": False,
                    "apo_structure_available": False,
                    "homolog_complex_available": False,
                    "pocket_conserved": False,
                    "gate_validation": None,
                },
            },
            "expected": {
                "route": LEVEL3_ROUTE,
                "verdict": "INCONCLUSIVE",
                "lane": "evaluation_continues",
                "interaction_unverified": True,
                "flags": [INTERACTION_UNVERIFIED_FLAG],
            },
        },
    }

    for name, case in cases.items():
        report = build_stage5_report(
            case["config"]
        )
        ruling = report["target_record"]["ruling"]

        for key, expected_value in case["expected"].items():
            actual_value = ruling.get(
                key
            )
            if actual_value != expected_value:
                raise AssertionError(
                    f"{name}: {key} = {actual_value!r}, "
                    f"expected {expected_value!r}"
                )

    print(
        "PASS: Stage-5 routing framework verified."
    )


def main():
    """Run Stage-5 routing framework checks."""

    run_stage5_ruling_checks()


if __name__ == "__main__":
    main()
