"""Ring 4 orchestrator: classify enzyme coverage and compute engineerability.

Main entry point for the enzyme gap analysis pipeline stage.
Reads all compounds and reactions, enriches each reaction with:
- enzyme_coverage classification
- cross_substrate_candidates list
- engineerability_score and components
"""

from pipeline.analyze.cross_substrate import find_candidates
from pipeline.analyze.engineerability import compute_score
from pipeline.analyze.enzyme_index import build_enzyme_index


def run_gap_analysis(
    compounds: list[dict],
    reactions: list[dict],
    enzyme_index: dict | None = None,
) -> tuple[list[dict], dict]:
    """Run Ring 4 gap analysis on all reactions.

    Args:
        compounds: All compound dicts from the pipeline.
        reactions: All reaction dicts (may include Ring 2 annotations).
        enzyme_index: Pre-built enzyme index. If None, builds from reactions.

    Returns:
        Tuple of (enriched_reactions, metadata_dict).
        enriched_reactions: Copy of reactions with Ring 4 fields added.
        metadata_dict: Summary statistics for pipeline_metadata.json.
    """
    compound_map = {c["id"]: c for c in compounds}

    if enzyme_index is None:
        enzyme_index = build_enzyme_index(reactions)

    # Counters for metadata
    counts = {
        "reactions_analyzed": 0,
        "coverage_direct": 0,
        "coverage_cross_substrate": 0,
        "coverage_family_only": 0,
        "coverage_none": 0,
    }
    total_score = 0.0

    enriched = []
    for rxn in reactions:
        counts["reactions_analyzed"] += 1
        rxn = dict(rxn)  # shallow copy to avoid mutating original

        # Classify coverage
        if rxn.get("ec_number"):
            # Direct enzyme match from Ring 2: trivially engineerable
            rxn["enzyme_coverage"] = "direct"
            rxn["cross_substrate_candidates"] = []
            rxn["ec_family_size"] = None
            score = 0.0
            components = {
                "coverage_level": 0.0,
                "best_similarity": 0.0,
                "family_richness": 0.0,
                "structural_data": 0.0,
            }
            counts["coverage_direct"] += 1
        else:
            # Find cross-substrate candidates
            candidates = find_candidates(
                rxn, reactions, compound_map,
                enzyme_index=enzyme_index,
            )

            if candidates:
                best = candidates[0]
                best_layer = best["matching_layer"]

                if best_layer <= 2:
                    rxn["enzyme_coverage"] = "cross_substrate"
                    coverage_level = f"cross_substrate_l{best_layer}"
                    counts["coverage_cross_substrate"] += 1
                else:
                    rxn["enzyme_coverage"] = "family_only"
                    coverage_level = "family_only"
                    counts["coverage_family_only"] += 1

                # Look up EC family size
                best_ec = best.get("ec_number", "")
                ec_entry = enzyme_index.get(best_ec, {})
                ec_family_size = ec_entry.get("family_size")
                has_pdb = (ec_entry.get("pdb_count") or 0) > 0

                rxn["cross_substrate_candidates"] = candidates
                rxn["ec_family_size"] = ec_family_size

                score, components = compute_score(
                    coverage_level,
                    best["similarity"]["overall"],
                    ec_family_size,
                    has_pdb,
                    num_candidates=len(candidates),
                )
            else:
                rxn["enzyme_coverage"] = "none"
                rxn["cross_substrate_candidates"] = []
                rxn["ec_family_size"] = None
                score, components = compute_score(
                    "none", 0.0, None, False, num_candidates=0
                )
                counts["coverage_none"] += 1

        rxn["engineerability_score"] = score
        rxn["engineerability_components"] = components
        total_score += score
        enriched.append(rxn)

    n = counts["reactions_analyzed"]
    metadata = {
        **counts,
        "avg_engineerability_score": round(total_score / n, 4) if n > 0 else 0.0,
        "ec_families_indexed": len(enzyme_index),
    }

    return enriched, metadata
