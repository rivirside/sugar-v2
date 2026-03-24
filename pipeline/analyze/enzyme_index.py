"""Build lightweight enzyme family index from Ring 2 reaction data.

Tier 1 (always available): Built from Ring 2 reaction annotations.
Tier 2 (optional): Extended with BRENDA/UniProt API data when available.

Phase 1 implements Tier 1 only. Tier 2 fields are present but set to None.
"""


def build_enzyme_index(reactions: list[dict]) -> dict:
    """Build EC-number-keyed enzyme index from reactions.

    Scans all reactions for ec_number fields (populated by Ring 2).
    Aggregates enzyme names, organisms, and known substrates per EC number.

    Args:
        reactions: List of reaction dicts, some with Ring 2 annotations.

    Returns:
        Dict keyed by EC number, each value containing:
            name: str | None
            organisms: list[str]
            known_substrates: list[str]
            reaction_count: int
            family_size: None (Tier 2, not yet implemented)
            pdb_count: None (Tier 2, not yet implemented)
            uniprot_ids: None (Tier 2, not yet implemented)
    """
    index: dict[str, dict] = {}

    for rxn in reactions:
        ec = rxn.get("ec_number")
        if not ec:
            continue

        if ec not in index:
            index[ec] = {
                "name": rxn.get("enzyme_name"),
                "organisms": [],
                "known_substrates": [],
                "reaction_count": 0,
                # Tier 2 placeholders
                "family_size": None,
                "pdb_count": None,
                "uniprot_ids": None,
            }

        entry = index[ec]
        entry["reaction_count"] += 1

        # Use first non-None enzyme name
        if entry["name"] is None and rxn.get("enzyme_name"):
            entry["name"] = rxn["enzyme_name"]

        # Collect organisms (deduplicated)
        for org in rxn.get("organism", []):
            if org not in entry["organisms"]:
                entry["organisms"].append(org)

        # Collect substrates (deduplicated)
        for sub_id in rxn.get("substrates", []):
            if sub_id not in entry["known_substrates"]:
                entry["known_substrates"].append(sub_id)

    return index
