"""Tests for amino sugar enumeration and reactions."""

import pytest

from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.amino_sugars import (
    generate_amino_sugars,
    CURATED_AMINO_SUGARS,
)
from pipeline.reactions.amino_reactions import (
    generate_amino_epimerizations,
    generate_nacetylations,
)


@pytest.fixture(scope="module")
def monosaccharides():
    return enumerate_all_monosaccharides()


@pytest.fixture(scope="module")
def amino_sugars(monosaccharides):
    return generate_amino_sugars(monosaccharides)


# --- Enumeration tests ---

def test_curated_list_not_empty():
    assert len(CURATED_AMINO_SUGARS) >= 6


def test_generate_returns_list(amino_sugars):
    assert isinstance(amino_sugars, list)
    assert len(amino_sugars) == len(CURATED_AMINO_SUGARS)


def test_all_have_amino_sugar_type(amino_sugars):
    for c in amino_sugars:
        assert c["type"] == "amino_sugar"


def test_all_have_modifications(amino_sugars):
    for c in amino_sugars:
        mods = c.get("modifications")
        assert mods and len(mods) > 0
        for m in mods:
            assert m["type"] in ("amino", "nacetyl")


def test_glucosamine_exists(amino_sugars):
    ids = {c["id"] for c in amino_sugars}
    assert "D-GlcN" in ids


def test_glcnac_exists(amino_sugars):
    ids = {c["id"] for c in amino_sugars}
    assert "D-GlcNAc" in ids


def test_amino_formula_correct(amino_sugars):
    """Amino sugar: parent -1O +1N +1H."""
    glcn = next(c for c in amino_sugars if c["id"] == "D-GlcN")
    # D-Glucose is C6H12O6, D-GlcN should be C6H13NO5
    assert glcn["formula"] == "C6H13NO5"


def test_nacetyl_formula_correct(amino_sugars):
    """N-acetyl amino sugar: parent +1N +2C +3H."""
    glcnac = next(c for c in amino_sugars if c["id"] == "D-GlcNAc")
    # D-Glucose is C6H12O6, D-GlcNAc should be C8H15NO6
    assert glcnac["formula"] == "C8H15NO6"


def test_unique_ids(amino_sugars):
    ids = [c["id"] for c in amino_sugars]
    assert len(ids) == len(set(ids))


# --- Reaction tests ---

def test_amino_epimerizations_generated(amino_sugars):
    epis = generate_amino_epimerizations(amino_sugars)
    assert isinstance(epis, list)
    assert len(epis) > 0


def test_glcn_mann_epimerization(amino_sugars):
    """D-GlcN and D-ManN should epimerize (differ at C2 stereocenter... wait,
    amino is at C2, but they still have different stereocenters at other positions)."""
    epis = generate_amino_epimerizations(amino_sugars)
    pairs = {(r["substrates"][0], r["products"][0]) for r in epis}
    # D-GlcN and D-ManN both have amino at position 2, same carbons
    # They should epimerize if they differ at exactly one stereocenter
    assert ("D-GlcN", "D-ManN") in pairs or ("D-ManN", "D-GlcN") in pairs


def test_nacetylations_generated(amino_sugars):
    nacs = generate_nacetylations(amino_sugars)
    assert isinstance(nacs, list)
    assert len(nacs) > 0


def test_nacetylation_pairs_correct(amino_sugars):
    """Each amino sugar should pair with its N-acetyl form."""
    nacs = generate_nacetylations(amino_sugars)
    # D-GlcN -> D-GlcNAc should exist
    fwd_pairs = {(r["substrates"][0], r["products"][0]) for r in nacs}
    assert ("D-GlcN", "D-GlcNAc") in fwd_pairs


def test_nacetylation_has_cofactor(amino_sugars):
    nacs = generate_nacetylations(amino_sugars)
    fwd = [r for r in nacs if r["id"].startswith("NACETYL")]
    for r in fwd:
        assert "acetyl-CoA" in r.get("cofactors", [])


def test_epimerization_unique_ids(amino_sugars):
    epis = generate_amino_epimerizations(amino_sugars)
    ids = [r["id"] for r in epis]
    assert len(ids) == len(set(ids))


def test_nacetylation_unique_ids(amino_sugars):
    nacs = generate_nacetylations(amino_sugars)
    ids = [r["id"] for r in nacs]
    assert len(ids) == len(set(ids))
