"""Tests for the Ring 4 gap analysis orchestrator."""

from pipeline.analyze.gap_analysis import run_gap_analysis


def _compound(id, type, carbons, stereocenters, modifications=None):
    return {
        "id": id, "type": type, "carbons": carbons,
        "stereocenters": stereocenters, "modifications": modifications,
    }


def _reaction(id, rtype, substrates, products, ec=None, enzyme_name=None):
    r = {
        "id": id, "reaction_type": rtype, "substrates": substrates,
        "products": products, "evidence_tier": "hypothetical" if not ec else "validated",
        "evidence_criteria": [], "yield": None, "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
        r["enzyme_name"] = enzyme_name
    return r


def test_direct_coverage():
    """Reaction with ec_number gets enzyme_coverage='direct'."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"], ec="5.1.3.1")]
    enriched, meta = run_gap_analysis(compounds, reactions)
    assert enriched[0]["enzyme_coverage"] == "direct"
    assert enriched[0]["engineerability_score"] == 0.0


def test_no_coverage():
    """Reaction without enzyme data and no candidates gets coverage='none'."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"])]
    enriched, meta = run_gap_analysis(compounds, reactions)
    assert enriched[0]["enzyme_coverage"] == "none"
    assert enriched[0]["engineerability_score"] == 1.0


def test_cross_substrate_coverage():
    """Gap with a cross-substrate candidate gets coverage='cross_substrate'."""
    compounds = [
        _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        _compound("B", "aldose", 6, ["S", "S", "R", "R"]),
        _compound("C", "aldose", 6, ["R", "R", "R", "R"]),
        _compound("D", "aldose", 6, ["S", "R", "R", "R"]),
    ]
    reactions = [
        _reaction("GAP", "epimerization", ["A"], ["B"]),            # no enzyme
        _reaction("KNOWN", "epimerization", ["C"], ["D"], ec="5.1.3.1"),  # has enzyme
    ]
    enriched, meta = run_gap_analysis(compounds, reactions)
    gap_rxn = next(r for r in enriched if r["id"] == "GAP")
    assert gap_rxn["enzyme_coverage"] == "cross_substrate"
    assert len(gap_rxn["cross_substrate_candidates"]) >= 1
    assert 0.0 < gap_rxn["engineerability_score"] < 1.0


def test_all_reactions_get_ring4_fields():
    """Every reaction gets all Ring 4 fields after gap analysis."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"])]
    enriched, _ = run_gap_analysis(compounds, reactions)
    r = enriched[0]
    assert "enzyme_coverage" in r
    assert "cross_substrate_candidates" in r
    assert "ec_family_size" in r
    assert "engineerability_score" in r
    assert "engineerability_components" in r


def test_metadata_counts():
    """Metadata contains correct coverage counts."""
    compounds = [
        _compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"]),
        _compound("C", "aldose", 6, ["R", "S"]), _compound("D", "aldose", 6, ["S", "S"]),
    ]
    reactions = [
        _reaction("R1", "epimerization", ["A"], ["B"], ec="5.1.3.1"),
        _reaction("R2", "epimerization", ["C"], ["D"]),
    ]
    _, meta = run_gap_analysis(compounds, reactions)
    assert meta["reactions_analyzed"] == 2
    assert meta["coverage_direct"] == 1
    assert meta["coverage_none"] + meta["coverage_cross_substrate"] + meta["coverage_family_only"] == 1
