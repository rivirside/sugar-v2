"""Tests for the compound matching engine."""

import pytest
from pipeline.import_.match import match_compound


def _make_compound(id, name, aliases=None, formula="C6H12O6"):
    return {
        "id": id,
        "name": name,
        "aliases": aliases or [],
        "formula": formula,
        "stereocenters": ["R", "S", "S", "R"],
    }


def _make_chebi_index():
    return {
        "d-glucose": {
            "chebi_id": "CHEBI:17634",
            "name": "D-glucopyranose",
            "synonyms": ["D-Glucose", "Dextrose", "Grape sugar"],
            "formula": "C6H12O6",
            "inchi": "InChI=1S/C6H12O6/test",
            "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
            "kegg_id": "C00031",
            "pubchem_id": "5793",
        },
        "dextrose": {
            "chebi_id": "CHEBI:17634",
            "name": "D-glucopyranose",
            "synonyms": ["D-Glucose", "Dextrose"],
            "formula": "C6H12O6",
            "inchi": "InChI=1S/C6H12O6/test",
            "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
            "kegg_id": "C00031",
            "pubchem_id": "5793",
        },
    }


def test_exact_name_match():
    compound = _make_compound("D-GLC", "D-Glucose")
    index = _make_chebi_index()
    result = match_compound(compound, index)
    assert result["chebi_id"] == "CHEBI:17634"
    assert result["confidence"] == "high"
    assert result["strategy"] == "exact_name"


def test_alias_match():
    compound = _make_compound("D-GLC", "D-Glucose", aliases=["Dextrose"])
    index = {"dextrose": _make_chebi_index()["dextrose"]}
    result = match_compound(compound, index)
    assert result["chebi_id"] == "CHEBI:17634"
    assert result["confidence"] == "high"
    assert result["strategy"] == "alias"


def test_no_match():
    compound = _make_compound("ALDO-C7-RRSRS", "D-aldoheptose-RRSRS", formula="C7H14O7")
    index = _make_chebi_index()
    result = match_compound(compound, index)
    assert result["chebi_id"] is None
    assert result["strategy"] == "no_match"


def test_override_pin():
    compound = _make_compound("D-GLC", "D-Glucose")
    index = {}
    overrides = {"D-GLC": {"chebi_id": "CHEBI:17634", "action": "pin"}}
    result = match_compound(compound, index, overrides=overrides)
    assert result["chebi_id"] == "CHEBI:17634"
    assert result["strategy"] == "override_pin"


def test_override_reject():
    compound = _make_compound("D-GLC", "D-Glucose")
    index = _make_chebi_index()
    overrides = {"D-GLC": {"chebi_id": "CHEBI:17634", "action": "reject"}}
    result = match_compound(compound, index, overrides=overrides)
    assert result["chebi_id"] is None
    assert result["strategy"] == "override_reject"


def test_formula_single_candidate():
    compound = _make_compound("TEST", "Unknown Sugar", formula="C4H8O4")
    index = {
        "erythrose": {
            "chebi_id": "CHEBI:27904",
            "name": "D-Erythrose",
            "synonyms": ["erythrose"],
            "formula": "C4H8O4",
            "inchi": None, "smiles": None, "kegg_id": None, "pubchem_id": None,
        }
    }
    result = match_compound(compound, index)
    assert result["chebi_id"] == "CHEBI:27904"
    assert result["confidence"] == "medium"
    assert result["strategy"] == "formula_unique"


def test_formula_multiple_candidates_no_match():
    compound = _make_compound("TEST", "Unknown Hexose")
    glucose = _make_chebi_index()["d-glucose"]
    mannose = {**glucose, "chebi_id": "CHEBI:28729", "name": "D-Mannose"}
    index = {"d-glucose": glucose, "d-mannose": mannose}
    result = match_compound(compound, index)
    assert result["chebi_id"] is None
    assert result["strategy"] == "no_match"
