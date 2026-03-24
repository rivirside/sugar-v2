"""Generate reactions for deoxy sugars.

Currently supports epimerization between deoxy sugars that share
the same deoxy positions, carbon count, and differ at exactly one
stereocenter.
"""

from itertools import combinations


def _base_reaction(
    reaction_id: str,
    substrate_id: str,
    product_id: str,
    reaction_type: str,
    carbons: int,
) -> dict:
    """Create a base reaction dict for deoxy sugar reactions."""
    return {
        "id": reaction_id,
        "substrates": [substrate_id],
        "products": [product_id],
        "reaction_type": reaction_type,
        "evidence_tier": "hypothetical",
        "evidence_criteria": [
            {"type": "rule_generated", "rule": f"deoxy_{reaction_type}"}
        ],
        "yield": None,
        "cofactor_burden": 0.0,
        "cost_score": 0.94,
        "cofactors": [],
        "metadata": {
            "source": "deoxy_rule_generation",
            "carbon_count": carbons,
        },
    }


def generate_deoxy_epimerizations(deoxy_sugars: list[dict]) -> list[dict]:
    """Generate epimerization reactions between deoxy sugars.

    Two deoxy sugars can epimerize if they:
    - Have the same carbon count
    - Have the same deoxy positions (same modification pattern)
    - Differ at exactly one stereocenter

    Args:
        deoxy_sugars: list of deoxy sugar compound dicts

    Returns:
        list of epimerization reaction dicts (directed, both directions)
    """
    reactions = []

    # Group by (carbons, deoxy_positions_tuple) for efficient matching
    groups: dict[tuple, list[dict]] = {}
    for c in deoxy_sugars:
        deoxy_pos = tuple(sorted(m["position"] for m in c["modifications"]))
        key = (c["carbons"], deoxy_pos)
        if key not in groups:
            groups[key] = []
        groups[key].append(c)

    for (carbons, deoxy_pos), members in groups.items():
        if len(members) < 2:
            continue

        for a, b in combinations(members, 2):
            stereo_a = a["stereocenters"]
            stereo_b = b["stereocenters"]

            if len(stereo_a) != len(stereo_b):
                continue

            # Count stereocenter differences
            diffs = sum(
                1 for sa, sb in zip(stereo_a, stereo_b) if sa != sb
            )
            if diffs != 1:
                continue

            # Generate both directions
            deoxy_label = ",".join(str(p) for p in deoxy_pos)
            fwd_id = f"EPI-DEOXY-C{carbons}-{a['id']}-{b['id']}"
            rev_id = f"EPI-DEOXY-C{carbons}-{b['id']}-{a['id']}"

            reactions.append(
                _base_reaction(fwd_id, a["id"], b["id"], "epimerization", carbons)
            )
            reactions.append(
                _base_reaction(rev_id, b["id"], a["id"], "epimerization", carbons)
            )

    return reactions
