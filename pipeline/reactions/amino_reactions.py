"""Generate reactions for amino sugars.

Supports:
- Epimerization between amino sugars with same modification pattern
- N-acetylation (amino sugar + acetyl-CoA -> N-acetyl amino sugar)
"""

from itertools import combinations


def _base_reaction(
    reaction_id: str,
    substrate_id: str,
    product_id: str,
    reaction_type: str,
    carbons: int,
    cofactor_burden: float = 0.0,
    cofactors: list[str] | None = None,
) -> dict:
    return {
        "id": reaction_id,
        "substrates": [substrate_id],
        "products": [product_id],
        "reaction_type": reaction_type,
        "evidence_tier": "hypothetical",
        "evidence_criteria": [
            {"type": "rule_generated", "rule": f"amino_{reaction_type}"}
        ],
        "yield": None,
        "cofactor_burden": cofactor_burden,
        "cost_score": 0.94,
        "cofactors": cofactors or [],
        "metadata": {
            "source": "amino_rule_generation",
            "carbon_count": carbons,
        },
    }


def generate_amino_epimerizations(amino_sugars: list[dict]) -> list[dict]:
    """Generate epimerization reactions between amino sugars.

    Two amino sugars can epimerize if they:
    - Have the same carbon count
    - Have the same modification pattern (same type and position)
    - Differ at exactly one stereocenter
    """
    reactions = []

    # Group by (carbons, modification_key)
    groups: dict[tuple, list[dict]] = {}
    for c in amino_sugars:
        mod_key = tuple(
            (m["type"], m["position"]) for m in sorted(
                c["modifications"], key=lambda m: (m["type"], m["position"])
            )
        )
        key = (c["carbons"], mod_key)
        if key not in groups:
            groups[key] = []
        groups[key].append(c)

    for (carbons, mod_key), members in groups.items():
        if len(members) < 2:
            continue

        for a, b in combinations(members, 2):
            stereo_a = a["stereocenters"]
            stereo_b = b["stereocenters"]

            if len(stereo_a) != len(stereo_b):
                continue

            diffs = sum(1 for sa, sb in zip(stereo_a, stereo_b) if sa != sb)
            if diffs != 1:
                continue

            fwd_id = f"EPI-AMINO-C{carbons}-{a['id']}-{b['id']}"
            rev_id = f"EPI-AMINO-C{carbons}-{b['id']}-{a['id']}"

            reactions.append(
                _base_reaction(fwd_id, a["id"], b["id"], "epimerization", carbons)
            )
            reactions.append(
                _base_reaction(rev_id, b["id"], a["id"], "epimerization", carbons)
            )

    return reactions


def generate_nacetylations(amino_sugars: list[dict]) -> list[dict]:
    """Generate N-acetylation reactions: amino sugar + acetyl-CoA -> N-acetyl sugar.

    Pairs each amino sugar with its N-acetyl counterpart if both exist.
    """
    reactions = []

    # Build lookup: (parent_id, position) -> compound
    amino_map: dict[tuple, dict] = {}
    nacetyl_map: dict[tuple, dict] = {}

    for c in amino_sugars:
        for mod in c["modifications"]:
            key = (c.get("parent_monosaccharide"), mod["position"])
            if mod["type"] == "amino":
                amino_map[key] = c
            elif mod["type"] == "nacetyl":
                nacetyl_map[key] = c

    for key, amino in amino_map.items():
        nacetyl = nacetyl_map.get(key)
        if nacetyl is None:
            continue

        carbons = amino["carbons"]

        # Forward: amino -> N-acetyl (N-acetyltransferase, requires acetyl-CoA)
        fwd_id = f"NACETYL-C{carbons}-{amino['id']}-{nacetyl['id']}"
        reactions.append(
            _base_reaction(
                fwd_id, amino["id"], nacetyl["id"],
                "transamination", carbons,
                cofactor_burden=1.0,
                cofactors=["acetyl-CoA"],
            )
        )

        # Reverse: N-acetyl -> amino (deacetylase)
        rev_id = f"DEACETYL-C{carbons}-{nacetyl['id']}-{amino['id']}"
        reactions.append(
            _base_reaction(
                rev_id, nacetyl["id"], amino["id"],
                "hydrolysis", carbons,
            )
        )

    return reactions
