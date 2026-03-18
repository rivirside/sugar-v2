from pipeline.reactions.score import compute_cost_score

def test_validated_reaction_has_low_cost():
    rxn = {"evidence_tier": "validated", "cofactor_burden": 0}
    score = compute_cost_score(rxn)
    assert 0 < score <= 0.3

def test_hypothetical_reaction_has_high_cost():
    rxn = {"evidence_tier": "hypothetical", "cofactor_burden": 0}
    score = compute_cost_score(rxn)
    assert score >= 0.7

def test_cofactor_burden_increases_cost():
    base = {"evidence_tier": "validated", "cofactor_burden": 0}
    with_cofactors = {"evidence_tier": "validated", "cofactor_burden": 3}
    assert compute_cost_score(with_cofactors) > compute_cost_score(base)
