"""Tests for enzyme index builder."""

from pipeline.analyze.enzyme_index import build_enzyme_index


def _reaction(id, ec=None, enzyme_name=None, substrates=None, organisms=None):
    """Helper: minimal reaction dict for enzyme index tests."""
    r = {
        "id": id,
        "reaction_type": "epimerization",
        "substrates": substrates or ["D-GLC"],
        "products": ["D-MAN"],
        "evidence_tier": "hypothetical",
        "evidence_criteria": [],
        "yield": None,
        "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
    if enzyme_name:
        r["enzyme_name"] = enzyme_name
    if organisms:
        r["organism"] = organisms
    return r


def test_empty_reactions():
    """No reactions -> empty index."""
    index = build_enzyme_index([])
    assert index == {}


def test_no_ec_numbers():
    """Reactions without ec_number are skipped."""
    rxns = [_reaction("R1"), _reaction("R2")]
    index = build_enzyme_index(rxns)
    assert index == {}


def test_single_ec_entry():
    """One reaction with EC -> one entry in index."""
    rxns = [_reaction("R1", ec="5.1.3.2", enzyme_name="epimerase",
                       substrates=["D-GLC"], organisms=["E. coli"])]
    index = build_enzyme_index(rxns)
    assert "5.1.3.2" in index
    assert index["5.1.3.2"]["name"] == "epimerase"
    assert "E. coli" in index["5.1.3.2"]["organisms"]
    assert "D-GLC" in index["5.1.3.2"]["known_substrates"]
    assert index["5.1.3.2"]["reaction_count"] == 1


def test_multiple_reactions_same_ec():
    """Multiple reactions with same EC -> merged entry."""
    rxns = [
        _reaction("R1", ec="5.1.3.2", substrates=["D-GLC"], organisms=["E. coli"]),
        _reaction("R2", ec="5.1.3.2", substrates=["D-GAL"], organisms=["H. sapiens"]),
    ]
    index = build_enzyme_index(rxns)
    assert index["5.1.3.2"]["reaction_count"] == 2
    assert "D-GLC" in index["5.1.3.2"]["known_substrates"]
    assert "D-GAL" in index["5.1.3.2"]["known_substrates"]
    assert "E. coli" in index["5.1.3.2"]["organisms"]
    assert "H. sapiens" in index["5.1.3.2"]["organisms"]


def test_tier2_fields_default_none():
    """Tier 2 fields (family_size, pdb_count, uniprot_ids) default to None."""
    rxns = [_reaction("R1", ec="5.1.3.2")]
    index = build_enzyme_index(rxns)
    assert index["5.1.3.2"]["family_size"] is None
    assert index["5.1.3.2"]["pdb_count"] is None
    assert index["5.1.3.2"]["uniprot_ids"] is None
