from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.reactions.generate import generate_epimerizations, generate_isomerizations


def test_epimerization_between_d_glucose_and_d_mannose():
    """D-GLC and D-MAN differ at C2 only -> should generate an epimerization."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_epimerizations(compounds)
    pair = [r for r in reactions if
            (r["substrates"] == ["D-GLC"] and r["products"] == ["D-MAN"]) or
            (r["substrates"] == ["D-MAN"] and r["products"] == ["D-GLC"])]
    # Should have both forward and reverse
    assert len(pair) == 2


def test_no_epimerization_between_d_glucose_and_d_galactose_direct():
    """D-GLC and D-GAL differ at C4 only -> should have an epimerization."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_epimerizations(compounds)
    pair = [r for r in reactions if
            r["substrates"] == ["D-GLC"] and r["products"] == ["D-GAL"]]
    assert len(pair) == 1  # forward direction


def test_no_epimerization_across_types():
    """Aldoses should not epimerize with ketoses."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_epimerizations(compounds)
    for r in reactions:
        sub = next(c for c in compounds if c["id"] == r["substrates"][0])
        prod = next(c for c in compounds if c["id"] == r["products"][0])
        assert sub["type"] == prod["type"], f"Cross-type epimerization: {r['id']}"


def test_epimerization_only_single_center():
    """Each epimerization should differ at exactly one stereocenter."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_epimerizations(compounds)
    compound_map = {c["id"]: c for c in compounds}
    for r in reactions:
        sub = compound_map[r["substrates"][0]]
        prod = compound_map[r["products"][0]]
        diffs = sum(1 for a, b in zip(sub["stereocenters"], prod["stereocenters"]) if a != b)
        assert diffs == 1, f"Epimerization {r['id']} differs at {diffs} centers"


def test_epimerization_reaction_fields():
    """Each reaction should have required fields."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_epimerizations(compounds)
    r = reactions[0]
    assert r["reaction_type"] == "epimerization"
    assert r["evidence_tier"] == "hypothetical"
    assert "evidence_criteria" in r
    assert "cost_score" in r


def test_d_glucose_isomerizes_to_d_fructose():
    """D-Glucose (RSSR) -> D-Fructose (SSR): drop C2, remaining is SSR."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_isomerizations(compounds)
    fwd = [r for r in reactions if r["substrates"] == ["D-GLC"] and r["products"] == ["D-FRU"]]
    assert len(fwd) == 1


def test_d_mannose_also_isomerizes_to_d_fructose():
    """D-Mannose (SSSR) -> D-Fructose (SSR): drop C2 (S), remaining is SSR."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_isomerizations(compounds)
    fwd = [r for r in reactions if r["substrates"] == ["D-MAN"] and r["products"] == ["D-FRU"]]
    assert len(fwd) == 1


def test_isomerization_is_reversible():
    """Each isomerization should have a reverse reaction."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_isomerizations(compounds)
    fwd_count = len([r for r in reactions if not r["id"].endswith("-REV")])
    rev_count = len([r for r in reactions if r["id"].endswith("-REV")])
    assert fwd_count == rev_count


def test_no_isomerization_for_c2():
    """C2 aldose has no corresponding ketose."""
    compounds = enumerate_all_monosaccharides()
    reactions = generate_isomerizations(compounds)
    c2_rxns = [r for r in reactions if "C2" in r["id"]]
    assert len(c2_rxns) == 0
