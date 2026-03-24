"""Tests for cross-substrate enzyme candidate matching."""

from pipeline.analyze.cross_substrate import find_candidates, extract_position


def _compound(id, type, carbons, stereocenters, modifications=None):
    """Helper: minimal compound dict."""
    return {
        "id": id,
        "type": type,
        "carbons": carbons,
        "stereocenters": stereocenters,
        "modifications": modifications,
    }


def _reaction(id, rtype, substrates, products, ec=None, enzyme_name=None, organism=None):
    """Helper: minimal reaction dict."""
    r = {
        "id": id,
        "reaction_type": rtype,
        "substrates": substrates,
        "products": products,
        "evidence_tier": "hypothetical" if not ec else "validated",
        "evidence_criteria": [],
        "yield": None,
        "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
        r["enzyme_name"] = enzyme_name or "test enzyme"
        r["organism"] = [organism] if organism else []
    return r


# --- Position extraction ---

def test_epi_position():
    """Epimerization: position is the index where stereocenters differ."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    rxn = _reaction("EPI-1", "epimerization", ["D-GLC"], ["D-MAN"])
    pos = extract_position(rxn, compounds)
    assert pos == (0,)  # index 0 differs (R vs S)


def test_mutase_position():
    """Mutase: position from modifications, not stereocenters."""
    compounds = {
        "D-GLC-1P": _compound("D-GLC-1P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 1}]),
        "D-GLC-6P": _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 6}]),
    }
    rxn = _reaction("MUT-1", "mutase", ["D-GLC-1P"], ["D-GLC-6P"])
    pos = extract_position(rxn, compounds)
    assert pos == (1, 6)  # phosphate positions


def test_phosphorylation_position():
    """Phosphorylation: position from phosphate site."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-GLC-6P": _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 6}]),
    }
    rxn = _reaction("PHOS-1", "phosphorylation", ["D-GLC"], ["D-GLC-6P"])
    pos = extract_position(rxn, compounds)
    assert pos == (6,)


def test_isomerization_no_position():
    """Isomerization: no position concept, returns None."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-FRU": _compound("D-FRU", "ketose", 6, ["S", "R", "R"]),
    }
    rxn = _reaction("ISO-1", "isomerization", ["D-GLC"], ["D-FRU"])
    pos = extract_position(rxn, compounds)
    assert pos is None


def test_reduction_no_position():
    """Reduction: no position concept, returns None."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-GLC-OL": _compound("D-GLC-OL", "polyol", 6, ["R", "S", "R", "R"]),
    }
    rxn = _reaction("RED-1", "reduction", ["D-GLC"], ["D-GLC-OL"])
    pos = extract_position(rxn, compounds)
    assert pos is None


# --- Cross-substrate matching ---

def test_no_enzyme_reactions_returns_empty():
    """When no reactions have enzyme data, candidates list is empty."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    gap = _reaction("GAP-1", "epimerization", ["D-GLC"], ["D-MAN"])
    all_rxns = [gap]
    result = find_candidates(gap, all_rxns, compounds)
    assert result == []


def test_layer1_match():
    """Layer 1: same type, same position, different substrate."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
        "D-GAL": _compound("D-GAL", "aldose", 6, ["R", "S", "S", "R"]),
        "D-TAL": _compound("D-TAL", "aldose", 6, ["S", "S", "S", "R"]),
    }
    # Gap: epimerize pos 0 on D-GAL (no enzyme)
    gap = _reaction("GAP", "epimerization", ["D-GAL"], ["D-TAL"])
    # Known: epimerize pos 0 on D-GLC (has enzyme)
    known = _reaction("KNOWN", "epimerization", ["D-GLC"], ["D-MAN"],
                       ec="5.1.3.18", enzyme_name="mannose-6P epimerase")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 1
    assert result[0]["ec_number"] == "5.1.3.18"


def test_layer2_match():
    """Layer 2: same type, different position."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-ALL": _compound("D-ALL", "aldose", 6, ["R", "S", "R", "S"]),  # pos 3 differs
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),  # pos 0 differs
    }
    # Gap: epimerize pos 3 on D-GLC
    gap = _reaction("GAP", "epimerization", ["D-GLC"], ["D-ALL"])
    # Known: epimerize pos 0 on D-GLC (different position)
    known = _reaction("KNOWN", "epimerization", ["D-GLC"], ["D-MAN"],
                       ec="5.1.3.18")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 2


def test_no_match_returns_none_coverage():
    """No matching candidates -> empty list."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    gap = _reaction("GAP", "epimerization", ["D-GLC"], ["D-MAN"])
    # Only a phosphorylation enzyme (wrong type)
    wrong_type = _reaction("PHOS", "phosphorylation", ["D-GLC"], ["D-GLC-6P"],
                            ec="2.7.1.1")
    compounds["D-GLC-6P"] = _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                                       [{"type": "phosphate", "position": 6}])
    result = find_candidates(gap, [gap, wrong_type], compounds)
    assert result == []


def test_candidates_sorted_by_layer_then_similarity():
    """Candidates sorted: layer ascending, then similarity descending."""
    compounds = {
        "A": _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        "B": _compound("B", "aldose", 6, ["S", "S", "R", "R"]),  # pos 0 flip
        "C": _compound("C", "aldose", 6, ["R", "R", "R", "R"]),  # pos 1 flip
        "D": _compound("D", "aldose", 6, ["S", "R", "R", "R"]),  # pos 0+1 flip
    }
    gap = _reaction("GAP", "epimerization", ["A"], ["B"])
    # Layer 1 candidate (same position 0)
    l1 = _reaction("L1", "epimerization", ["C"], ["D"], ec="5.1.3.1")
    # Layer 2 candidate (different position)
    l2 = _reaction("L2", "epimerization", ["A"], ["C"], ec="5.1.3.2")
    result = find_candidates(gap, [gap, l1, l2], compounds)
    assert len(result) == 2
    assert result[0]["matching_layer"] <= result[1]["matching_layer"]


def test_max_candidates_cap():
    """Results capped at max_candidates."""
    compounds = {f"C{i}": _compound(f"C{i}", "aldose", 6, ["R"]) for i in range(20)}
    compounds["GAP_S"] = _compound("GAP_S", "aldose", 6, ["S"])
    gap = _reaction("GAP", "epimerization", ["GAP_S"], ["C0"])
    # 10 known epimerases
    knowns = [
        _reaction(f"K{i}", "epimerization", [f"C{i}"], [f"C{i+1}"], ec=f"5.1.3.{i}")
        for i in range(0, 10)
    ]
    result = find_candidates(gap, [gap] + knowns, compounds, max_candidates=3)
    assert len(result) <= 3


def test_dedup_by_ec_keeps_best():
    """Deduplicate by EC: keep entry with best (layer, similarity)."""
    compounds = {
        "A": _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        "B": _compound("B", "aldose", 6, ["S", "S", "R", "R"]),
        "C": _compound("C", "aldose", 6, ["R", "R", "R", "R"]),
        "D": _compound("D", "aldose", 6, ["S", "R", "R", "R"]),
    }
    gap = _reaction("GAP", "epimerization", ["A"], ["B"])
    # Same EC at different layers
    l1 = _reaction("L1", "epimerization", ["C"], ["D"], ec="5.1.3.1")
    l2 = _reaction("L2", "epimerization", ["A"], ["C"], ec="5.1.3.1")  # same EC, different layer
    result = find_candidates(gap, [gap, l1, l2], compounds)
    ec_numbers = [c["ec_number"] for c in result]
    assert ec_numbers.count("5.1.3.1") == 1  # deduplicated


def test_isomerization_no_layer_split():
    """Isomerization: Layers 1+2 collapse (no position), all same-type matches are Layer 1."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-FRU": _compound("D-FRU", "ketose", 6, ["S", "R", "R"]),
        "D-GAL": _compound("D-GAL", "aldose", 6, ["R", "S", "S", "R"]),
        "D-TAG": _compound("D-TAG", "ketose", 6, ["S", "S", "R"]),
    }
    gap = _reaction("GAP", "isomerization", ["D-GLC"], ["D-FRU"])
    known = _reaction("K1", "isomerization", ["D-GAL"], ["D-TAG"], ec="5.3.1.9")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 1  # not 2, since no position concept
