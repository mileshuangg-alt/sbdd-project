import json
from pathlib import Path
import xml.etree.ElementTree as ET


PLIP_INTERACTION_CLASSES = {
    "hydrophobic_interaction": "Hydrophobic",
    "hydrogen_bond": "HydrogenBond",
    "water_bridge": "WaterBridge",
    "salt_bridge": "SaltBridge",
    "pi_stack": "PiStacking",
    "pi_cation_interaction": "PiCation",
    "halogen_bond": "HalogenBond",
    "metal_complex": "MetalComplex",
}


def load_plip_witness_config(config_path):
    """Load a PLIP witness definition from JSON."""

    config_path = Path(config_path)

    with config_path.open("r") as handle:
        config = json.load(handle)

    validate_plip_witness_config(
        config
    )

    return config


def validate_plip_witness_config(config):
    """Validate the fields needed by the generic PLIP summarizer."""

    required_top_level = [
        "witness_id",
        "target_id",
        "qualification_panel",
        "configured_residues",
        "configured_roles",
    ]

    for key in required_top_level:
        if key not in config:
            raise ValueError(
                f"PLIP witness config missing required key: {key}"
            )

    residue_ids = set()

    for residue in config["configured_residues"]:
        for key in ["residue_id", "name", "chain", "number"]:
            if key not in residue:
                raise ValueError(
                    "Configured residue missing required key: "
                    f"{key}"
                )

        residue_ids.add(
            residue["residue_id"]
        )

    for role in config["configured_roles"]:
        for key in ["role_id", "residue_id", "requires_any"]:
            if key not in role:
                raise ValueError(
                    f"Configured role missing required key: {key}"
                )

        if role["residue_id"] not in residue_ids:
            raise ValueError(
                "Configured role references unknown residue_id: "
                f"{role['residue_id']}"
            )

        if not role["requires_any"]:
            raise ValueError(
                "Configured role requires at least one interaction "
                f"criterion: {role['role_id']}"
            )


def summarize_plip_xml(xml_path, config, panel_id=None, case=None):
    """Summarize configured PLIP interactions for one XML report."""

    xml_path = Path(xml_path)

    tree = ET.parse(
        xml_path
    )

    root = tree.getroot()

    if case is None:
        case = select_qualification_case(
            root,
            config,
            panel_id=panel_id,
        )

    selected_site = select_binding_site(
        root,
        case["ligand"],
    )

    observed_interactions = extract_configured_interactions(
        selected_site,
        config["configured_residues"],
    )

    observed_counts = count_observed_interactions(
        observed_interactions,
        config["configured_residues"],
    )

    role_results = evaluate_configured_roles(
        observed_interactions,
        config,
    )


    selected_ligand = ligand_summary_from_site(
        selected_site
    )


    summary = {
        "witness_id": config["witness_id"],
        "target_id": config["target_id"],
        "panel_id": case.get("panel_id"),
        "case_id": case.get("case_id"),
        "pdb_id": root.findtext("pdbid"),
        "source_xml": str(xml_path),
        "selected_ligand": selected_ligand,
        "ignored_ligands": ignored_ligands(
            root,
            selected_ligand,
        ),
        "observed_interactions": observed_interactions,
        "observed_counts": observed_counts,
        "configured_role_reproduction": role_results,
        "witness_reproduced": all(
            role["reproduced"] for role in role_results
        ),
        "stage5_verdict_instrument": config.get(
            "stage5_verdict_instrument"
        ),
        "instrument_role": config.get(
            "instrument_role"
        ),
    }

    return summary


def summarize_plip_xml_for_case(xml_path, config, case):
    """Summarize one PLIP XML report with explicitly supplied case metadata."""

    return summarize_plip_xml(
        xml_path,
        config,
        case=case,
    )


def summarize_qualification_panel(config, base_path=None):
    """Summarize every configured PLIP qualification-panel XML report."""

    base_path = Path(base_path or ".")
    summaries = []

    for case in config["qualification_panel"]["cases"]:
        xml_path = base_path / case["xml_path"]
        summary = summarize_plip_xml(
            xml_path,
            config,
            panel_id=case["panel_id"],
        )

        summaries.append(
            summary
        )

    reproduced_count = sum(
        summary["witness_reproduced"] for summary in summaries
    )

    return {
        "witness_id": config["witness_id"],
        "target_id": config["target_id"],
        "qualification_panel": config["qualification_panel"],
        "summary_count": len(summaries),
        "witness_reproduced_count": reproduced_count,
        "witness_reproduced": reproduced_count == len(summaries),
        "case_summaries": summaries,
    }


def select_qualification_case(root, config, panel_id=None):
    """Select fixture metadata without embedding target-specific values."""

    cases = config["qualification_panel"]["cases"]

    if panel_id is not None:
        for case in cases:
            if case["panel_id"] == panel_id:
                return case

        raise ValueError(
            f"No qualification-panel case configured for {panel_id}"
        )

    pdb_id = root.findtext("pdbid")
    matches = [
        case
        for case in cases
        if case.get("pdb_id") == pdb_id
    ]

    if len(matches) != 1:
        raise ValueError(
            "Could not infer a unique qualification-panel case "
            f"for pdb_id={pdb_id!r}."
        )

    return matches[0]


def select_binding_site(root, ligand):
    """Return the PLIP binding site matching the configured ligand."""

    matches = []

    for site in root.findall("bindingsite"):
        identifiers = site.find("identifiers")

        if identifiers is None:
            continue

        site_ligand = {
            "hetid": identifiers.findtext("hetid"),
            "chain": identifiers.findtext("chain"),
            "position": text_to_int(
                identifiers.findtext("position")
            ),
        }

        if site_ligand == ligand:
            matches.append(
                site
            )

    if len(matches) != 1:
        raise ValueError(
            "Configured PLIP ligand matched "
            f"{len(matches)} binding sites; expected exactly one."
        )

    return matches[0]


def ligand_summary_from_site(site):
    """Extract compact ligand metadata from a PLIP binding site."""

    identifiers = site.find("identifiers")

    return {
        "hetid": identifiers.findtext("hetid"),
        "chain": identifiers.findtext("chain"),
        "position": text_to_int(
            identifiers.findtext("position")
        ),
        "longname": identifiers.findtext("longname"),
        "binding_site_id": site.get("id"),
        "has_interactions": site.get("has_interactions"),
    }


def ignored_ligands(root, selected_ligand):
    """List non-selected binding-site ligands present in the PLIP report."""

    ignored = []

    selected_key = ligand_key(
        selected_ligand
    )

    for site in root.findall("bindingsite"):
        site_ligand = ligand_summary_from_site(
            site
        )

        if ligand_key(site_ligand) != selected_key:
            ignored.append(
                site_ligand
            )

    return ignored


def extract_configured_interactions(site, configured_residues):
    """Extract PLIP interactions touching configured residues only."""

    residue_lookup = {
        residue_key(residue): residue
        for residue in configured_residues
    }

    interactions_root = site.find("interactions")


    if interactions_root is None:
        return []

    observed = []

    for interaction_group in list(interactions_root):
        for interaction in list(interaction_group):
            interaction_class = PLIP_INTERACTION_CLASSES.get(
                interaction.tag,
                normalize_plip_class_name(interaction.tag),
            )

            residue = residue_from_interaction(
                interaction
            )

            residue_config = residue_lookup.get(
                residue_key(residue)
            )

            if residue_config is None:
                continue

            observed.append(
                build_interaction_record(
                    interaction,
                    interaction_class,
                    residue_config,
                )
            )

    observed.sort(
        key=lambda item: (
            item["residue_id"],
            item["interaction_class"],
            item["plip_id"],
        )
    )

    return observed


def build_interaction_record(interaction, interaction_class, residue_config):
    """Build the compact machine-readable interaction record."""

    record = {
        "plip_id": interaction.get("id"),
        "residue_id": residue_config["residue_id"],
        "residue": {
            "name": interaction.findtext("restype"),
            "chain": interaction.findtext("reschain"),
            "number": text_to_int(
                interaction.findtext("resnr")
            ),
        },
        "interaction_class": interaction_class,
        "direction": interaction_direction(
            interaction,
            interaction_class,
        ),
        "atom_indices": atom_indices(
            interaction
        ),
    }

    return record


def residue_from_interaction(interaction):
    """Extract a normalized residue identity from a PLIP interaction."""

    return {
        "name": interaction.findtext("restype"),
        "chain": interaction.findtext("reschain"),
        "number": text_to_int(
            interaction.findtext("resnr")
        ),
    }


def residue_key(residue):
    """Return a comparable residue key."""

    return (
        residue["name"],
        residue["chain"],
        int(residue["number"]),
    )


def ligand_key(ligand):
    """Return a comparable ligand key."""


    return (
        ligand["hetid"],
        ligand["chain"],
        int(ligand["position"]),
    )


def interaction_direction(interaction, interaction_class):
    """Return the direction for PLIP interaction classes that carry one."""

    if interaction_class != "HydrogenBond":
        return None

    protisdon = interaction.findtext("protisdon")

    if protisdon == "True":
        return "protein_donor"

    if protisdon == "False":
        return "ligand_donor"

    return None


def atom_indices(interaction):
    """Extract scalar and list-valued atom indices from a PLIP interaction."""

    indices = {}

    scalar_tags = [
        "ligcarbonidx",
        "protcarbonidx",
        "donoridx",
        "acceptoridx",
        "donor_idx",
        "acceptor_idx",
        "water_idx",
    ]


    for tag in scalar_tags:
        value = interaction.findtext(tag)
        if value is not None:
            indices[tag] = text_to_int(
                value
            )

    for list_tag in ["prot_idx_list", "lig_idx_list"]:
        values = [
            text_to_int(idx.text)
            for idx in interaction.findall(f"{list_tag}/idx")
        ]

        if values:
            indices[list_tag] = values

    return indices


def count_observed_interactions(observed_interactions, configured_residues):
    """Count observed configured-residue interactions by class and direction."""

    counts = {}


    for residue in configured_residues:
        counts[residue["residue_id"]] = {
            "total": 0,
            "by_class": {},
            "by_class_and_direction": {},
        }

    for interaction in observed_interactions:
        residue_counts = counts[
            interaction["residue_id"]
        ]
        interaction_class = interaction[
            "interaction_class"
        ]
        direction = interaction[
            "direction"
        ]
        class_direction = (
            f"{interaction_class}:{direction}"
            if direction is not None
            else interaction_class
        )

        residue_counts["total"] += 1
        residue_counts["by_class"][interaction_class] = (
            residue_counts["by_class"].get(
                interaction_class,
                0,
            )
            + 1
        )
        residue_counts["by_class_and_direction"][class_direction] = (
            residue_counts["by_class_and_direction"].get(
                class_direction,
                0,
            )
            + 1
        )

    return counts


def evaluate_configured_roles(observed_interactions, config):
    """Evaluate configured role reproduction from observed interactions."""

    role_results = []


    for role in config["configured_roles"]:
        observations = [
            interaction
            for interaction in observed_interactions
            if interaction["residue_id"] == role["residue_id"]
        ]
        matching = [
            interaction
            for interaction in observations
            if interaction_matches_any_requirement(
                interaction,
                role["requires_any"],
            )
        ]

        role_results.append(
            {
                "role_id": role["role_id"],
                "residue_id": role["residue_id"],
                "reproduced": len(matching) > 0,
                "matched_count": len(matching),
                "observed_count": len(observations),
                "matched_observation_indices": [
                    observed_interactions.index(interaction)
                    for interaction in matching
                ],
            }
        )

    return role_results


def interaction_matches_any_requirement(interaction, requirements):
    """Return whether an observed interaction satisfies a role requirement."""

    for requirement in requirements:
        if interaction["interaction_class"] != requirement["interaction_class"]:
            continue

        required_direction = requirement.get("direction")
        if (
            required_direction is not None
            and interaction["direction"] != required_direction
        ):
            continue

        return True

    return False


def normalize_plip_class_name(tag):
    """Convert an unknown PLIP interaction tag into a stable class label."""

    parts = tag.split("_")

    return "".join(
        part.capitalize() for part in parts
    )


def text_to_int(value):
    """Convert PLIP numeric text to int while preserving missing values."""

    if value is None:
        return None

    return int(
        value.strip()
    )
