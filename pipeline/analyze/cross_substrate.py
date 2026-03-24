"""Cross-substrate enzyme candidate matching.

For reactions without a direct enzyme match, finds enzymes that catalyze
the same reaction type on structurally similar substrates. Candidates are
searched in three layers ordered by relevance.
"""

from pipeline.analyze.similarity import compute_similarity

# Reaction types where position is not a distinguishing factor.
# Layers 1 and 2 collapse into a single "same type" layer.
_POSITIONLESS_TYPES = {"isomerization", "reduction"}

# Reaction types where directionality matters for matching.
_DIRECTIONAL_TYPES = {"phosphorylation", "dephosphorylation"}


def extract_position(reaction: dict, compound_map: dict) -> tuple[int, ...] | None:
    """Extract the reaction position for cross-substrate matching.

    Returns:
        Tuple of position indices for position-aware types, or None for
        position-agnostic types (isomerization, reduction).

    Position extraction rules:
        - Epimerization: index where stereocenters differ
        - Mutase: (from_position, to_position) from modifications
        - Phosphorylation/Dephosphorylation: phosphate site from modifications
        - Isomerization/Reduction: None (no position concept)
    """
    rtype = reaction["reaction_type"]

    if rtype in _POSITIONLESS_TYPES:
        return None

    sub_id = reaction["substrates"][0] if reaction["substrates"] else None
    prod_id = reaction["products"][0] if reaction["products"] else None
    if not sub_id or not prod_id:
        return None

    sub = compound_map.get(sub_id)
    prod = compound_map.get(prod_id)
    if not sub or not prod:
        return None

    if rtype == "epimerization":
        stereo_a = sub.get("stereocenters", [])
        stereo_b = prod.get("stereocenters", [])
        diffs = [i for i in range(min(len(stereo_a), len(stereo_b)))
                 if stereo_a[i] != stereo_b[i]]
        if len(diffs) == 1:
            return (diffs[0],)
        return tuple(diffs) if diffs else None

    if rtype == "mutase":
        sub_mods = sub.get("modifications") or []
        prod_mods = prod.get("modifications") or []
        sub_positions = sorted(m["position"] for m in sub_mods if m["type"] == "phosphate")
        prod_positions = sorted(m["position"] for m in prod_mods if m["type"] == "phosphate")
        if sub_positions and prod_positions:
            return tuple(sorted(set(sub_positions + prod_positions)))
        return None

    if rtype in ("phosphorylation", "dephosphorylation"):
        # Find the phosphorylated compound
        phospho = prod if rtype == "phosphorylation" else sub
        mods = phospho.get("modifications") or []
        positions = sorted(m["position"] for m in mods if m["type"] == "phosphate")
        return tuple(positions) if positions else None

    return None


def find_candidates(
    gap_reaction: dict,
    all_reactions: list[dict],
    compound_map: dict,
    enzyme_index: dict | None = None,
    max_candidates: int = 5,
) -> list[dict]:
    """Find cross-substrate enzyme candidates for a gap reaction.

    Args:
        gap_reaction: The reaction lacking a direct enzyme match.
        all_reactions: All reactions in the dataset.
        compound_map: Dict mapping compound ID to compound dict.
        enzyme_index: Optional EC-keyed enzyme index for Layer 3 matching.
        max_candidates: Maximum candidates to return.

    Returns:
        List of candidate dicts sorted by (layer asc, similarity desc),
        capped at max_candidates. Each dict contains:
            ec_number, enzyme_name, organism, uniprot_id, pdb_ids,
            source_reaction_id, known_substrate_id, matching_layer,
            similarity (dict with overall + per-dimension scores)
    """
    gap_type = gap_reaction["reaction_type"]
    gap_position = extract_position(gap_reaction, compound_map)
    gap_sub_id = gap_reaction["substrates"][0] if gap_reaction["substrates"] else None
    gap_sub = compound_map.get(gap_sub_id) if gap_sub_id else None

    if not gap_sub:
        return []

    candidates = []

    for rxn in all_reactions:
        # Skip self
        if rxn["id"] == gap_reaction["id"]:
            continue

        # Must have enzyme data
        if not rxn.get("ec_number"):
            continue

        # Must be same reaction type
        if rxn["reaction_type"] != gap_type:
            continue

        # Determine layer
        rxn_position = extract_position(rxn, compound_map)

        if gap_position is None:
            # Positionless types: all same-type matches are Layer 1
            layer = 1
        elif rxn_position == gap_position:
            layer = 1
        elif rxn_position is not None:
            layer = 2
        else:
            layer = 2  # can't determine position -> treat as different

        # Get the known enzyme's substrate
        known_sub_id = rxn["substrates"][0] if rxn["substrates"] else None
        known_sub = compound_map.get(known_sub_id) if known_sub_id else None

        if not known_sub:
            continue

        # Compute substrate similarity
        sim = compute_similarity(gap_sub, known_sub)

        candidate = {
            "ec_number": rxn.get("ec_number"),
            "enzyme_name": rxn.get("enzyme_name", ""),
            "organism": rxn.get("organism", [None])[0] if rxn.get("organism") else None,
            "uniprot_id": None,  # Tier 2
            "pdb_ids": [],       # Tier 2
            "source_reaction_id": rxn["id"],
            "known_substrate_id": known_sub_id,
            "matching_layer": layer,
            "similarity": sim,
        }
        candidates.append(candidate)

    # Deduplicate by EC number: keep best (lowest layer, highest similarity)
    seen_ec: dict[str, dict] = {}
    for c in candidates:
        ec = c["ec_number"]
        if ec not in seen_ec:
            seen_ec[ec] = c
        else:
            existing = seen_ec[ec]
            if (c["matching_layer"], -c["similarity"]["overall"]) < \
               (existing["matching_layer"], -existing["similarity"]["overall"]):
                seen_ec[ec] = c

    deduped = list(seen_ec.values())

    # Sort: layer ascending, similarity descending
    deduped.sort(key=lambda c: (c["matching_layer"], -c["similarity"]["overall"]))

    return deduped[:max_candidates]
