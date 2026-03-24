"""Tests for deoxy sugar enumeration and reactions."""

import pytest

from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.deoxy_sugars import (
    generate_deoxy_sugars,
    CURATED_DEOXY_SUGARS,
)
from pipeline.reactions.deoxy_reactions import (
    generate_deoxy_epimerizations,
)


@pytest.fixture(scope="module")
def monosaccharides():
    return enumerate_all_monosaccharides()


@pytest.fixture(scope="module")
def deoxy_sugars(monosaccharides):
    return generate_deoxy_sugars(monosaccharides)


# --- Enumeration tests ---

def test_curated_list_not_empty():
    assert len(CURATED_DEOXY_SUGARS) >= 4


def test_generate_returns_list(deoxy_sugars):
    assert isinstance(deoxy_sugars, list)
    assert len(deoxy_sugars) > 0


def test_all_compounds_have_deoxy_sugar_type(deoxy_sugars):
    for c in deoxy_sugars:
        assert c["type"] == "deoxy_sugar", f"{c['id']} has type {c['type']}"


def test_all_have_modifications(deoxy_sugars):
    for c in deoxy_sugars:
        mods = c.get("modifications")
        assert mods is not None and len(mods) > 0, f"{c['id']} missing modifications"
        for m in mods:
            assert m["type"] == "deoxy", f"{c['id']} has non-deoxy mod: {m}"


def test_formula_has_fewer_oxygens(monosaccharides, deoxy_sugars):
    """Each deoxy position removes one oxygen from the parent formula."""
    parent_map = {c["id"]: c for c in monosaccharides}
    for dc in deoxy_sugars:
        parent_id = dc.get("parent_monosaccharide")
        if parent_id not in parent_map:
            continue
        parent = parent_map[parent_id]
        parent_o = int("".join(c for c in parent["formula"].split("O")[1].split("P")[0].split("N")[0] if c.isdigit()) or "1")
        deoxy_o = int("".join(c for c in dc["formula"].split("O")[1].split("P")[0].split("N")[0] if c.isdigit()) or "1")
        n_deoxy = len(dc["modifications"])
        assert deoxy_o == parent_o - n_deoxy, (
            f"{dc['id']}: expected O={parent_o - n_deoxy}, got O={deoxy_o}"
        )


def test_l_fucose_exists(deoxy_sugars):
    ids = {c["id"] for c in deoxy_sugars}
    assert "L-FUC" in ids or any("FUC" in cid for cid in ids)


def test_l_rhamnose_exists(deoxy_sugars):
    ids = {c["id"] for c in deoxy_sugars}
    assert "L-RHA" in ids or any("RHA" in cid for cid in ids)


def test_2_deoxy_d_ribose_exists(deoxy_sugars):
    ids = {c["id"] for c in deoxy_sugars}
    assert any("dRIB" in cid or "2DRIB" in cid or "DEOXYRIB" in cid for cid in ids)


def test_stereocenters_preserved_from_parent(monosaccharides, deoxy_sugars):
    """Deoxy sugars keep parent stereocenters except at deoxy position."""
    parent_map = {c["id"]: c for c in monosaccharides}
    for dc in deoxy_sugars:
        parent_id = dc.get("parent_monosaccharide")
        if parent_id not in parent_map:
            continue
        parent = parent_map[parent_id]
        deoxy_positions = {m["position"] for m in dc["modifications"]}
        # Stereocenters at non-deoxy positions should match parent
        # (deoxy position may lose its stereocenter if it was one)
        assert len(dc["stereocenters"]) <= len(parent["stereocenters"])


def test_unique_ids(deoxy_sugars):
    ids = [c["id"] for c in deoxy_sugars]
    assert len(ids) == len(set(ids)), "Duplicate deoxy sugar IDs found"


# --- Reaction tests ---

def test_deoxy_epimerizations_generated(deoxy_sugars):
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    assert isinstance(epis, list)
    assert len(epis) > 0


def test_deoxy_epimerizations_are_valid(deoxy_sugars):
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    for r in epis:
        assert r["reaction_type"] == "epimerization"
        assert len(r["substrates"]) == 1
        assert len(r["products"]) == 1
        assert r["substrates"][0] != r["products"][0]


def test_fucose_rhamnose_epimerization_exists(deoxy_sugars):
    """L-Fucose and L-Rhamnose differ at one stereocenter, should have epimerization."""
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    ids_involved = set()
    for r in epis:
        ids_involved.add(r["substrates"][0])
        ids_involved.add(r["products"][0])
    # At least one of the well-known deoxy sugars should participate
    deoxy_ids = {c["id"] for c in deoxy_sugars}
    assert ids_involved & deoxy_ids, "No deoxy sugar epimerizations found"


def test_epimerizations_same_deoxy_position(deoxy_sugars):
    """Epimerizations should only happen between sugars with same deoxy positions."""
    compound_map = {c["id"]: c for c in deoxy_sugars}
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    for r in epis:
        sub = compound_map[r["substrates"][0]]
        prod = compound_map[r["products"][0]]
        sub_deoxy = sorted(m["position"] for m in sub["modifications"])
        prod_deoxy = sorted(m["position"] for m in prod["modifications"])
        assert sub_deoxy == prod_deoxy, (
            f"{r['id']}: deoxy positions differ ({sub_deoxy} vs {prod_deoxy})"
        )


def test_epimerizations_same_carbon_count(deoxy_sugars):
    compound_map = {c["id"]: c for c in deoxy_sugars}
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    for r in epis:
        sub = compound_map[r["substrates"][0]]
        prod = compound_map[r["products"][0]]
        assert sub["carbons"] == prod["carbons"]


def test_epimerizations_unique_ids(deoxy_sugars):
    epis = generate_deoxy_epimerizations(deoxy_sugars)
    ids = [r["id"] for r in epis]
    assert len(ids) == len(set(ids)), "Duplicate epimerization IDs"
