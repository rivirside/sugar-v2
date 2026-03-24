"""Compute cost_score for reactions."""

W1 = 1.0  # yield loss
W2 = 0.5  # cofactor burden
W3 = 0.3  # evidence penalty
W4 = 0.2  # step penalty

EVIDENCE_PENALTY = {
    "validated": 0.0,
    "predicted": 0.1,
    "inferred": 0.3,
    "hypothetical": 0.8,
}

# Default yield when not explicitly specified, scaled by evidence tier.
# Well-validated reactions are assumed to have high/perfect yield;
# hypothetical reactions default to uncertain (50%) yield.
DEFAULT_YIELD_BY_TIER = {
    "validated": 1.0,
    "predicted": 0.8,
    "inferred": 0.6,
    "hypothetical": 0.5,
}


def compute_cost_score(reaction: dict) -> float:
    """Compute the weighted cost score for a reaction.

    cost_score = w1*(1-yield) + w2*cofactor_burden + w3*evidence_penalty + w4*step_penalty
    Null yield defaults to a tier-dependent estimate:
      validated=1.0, predicted=0.8, inferred=0.6, hypothetical=0.5
    """
    evidence = reaction.get("evidence_tier", "hypothetical")

    rxn_yield = reaction.get("yield")
    if rxn_yield is None:
        rxn_yield = DEFAULT_YIELD_BY_TIER.get(evidence, 0.5)

    cofactor_burden = reaction.get("cofactor_burden", 0.0)
    evidence_pen = EVIDENCE_PENALTY.get(evidence, 0.8)

    return (
        W1 * (1.0 - rxn_yield) +
        W2 * cofactor_burden +
        W3 * evidence_pen +
        W4
    )


def compute_combined_score(
    cost_score: float,
    engineerability_score: float,
    alpha: float = 0.5,
) -> float:
    """Compute combined cost + engineerability score.

    Args:
        cost_score: Biochemical cost score (0.0-1.6 range).
        engineerability_score: Engineering feasibility (0.0-1.0 range).
        alpha: Weight for cost_score. 1.0 = cost only, 0.0 = engineerability only.

    Returns:
        Weighted blend of both scores.
    """
    return alpha * cost_score + (1.0 - alpha) * engineerability_score
