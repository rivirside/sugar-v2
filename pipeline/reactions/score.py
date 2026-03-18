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


def compute_cost_score(reaction: dict) -> float:
    """Compute the weighted cost score for a reaction.

    cost_score = w1*(1-yield) + w2*cofactor_burden + w3*evidence_penalty + w4*step_penalty
    Null yield is treated as 0.5 (unknown).
    """
    rxn_yield = reaction.get("yield")
    if rxn_yield is None:
        rxn_yield = 0.5

    cofactor_burden = reaction.get("cofactor_burden", 0.0)
    evidence = reaction.get("evidence_tier", "hypothetical")
    evidence_pen = EVIDENCE_PENALTY.get(evidence, 0.8)

    return (
        W1 * (1.0 - rxn_yield) +
        W2 * cofactor_burden +
        W3 * evidence_pen +
        W4
    )
