"""Tests for KEGG importer."""

import pytest
from pipeline.import_.kegg import parse_kegg_compound_entry, parse_kegg_link_response


SAMPLE_COMPOUND = """ENTRY       C00031                      Compound
NAME        D-Glucose;
            Grape sugar;
            Dextrose
FORMULA     C6H12O6
EXACT_MASS  180.0634
MOL_WEIGHT  180.0634
PATHWAY     map00010  Glycolysis / Gluconeogenesis
            map00500  Starch and sucrose metabolism
DBLINKS     CAS: 50-99-7
            PubChem: 3333
            ChEBI: 17634
///"""

SAMPLE_LINK = """C00031\trn:R00299
C00031\trn:R00300
C00031\trn:R01070"""


def test_parse_compound_entry():
    result = parse_kegg_compound_entry(SAMPLE_COMPOUND)
    assert result["kegg_id"] == "C00031"
    assert "D-Glucose" in result["names"]
    assert "Dextrose" in result["names"]
    assert result["formula"] == "C6H12O6"
    assert result["chebi_id"] == "17634"
    assert "map00010" in result["pathways"]


def test_parse_link_response():
    links = parse_kegg_link_response(SAMPLE_LINK)
    assert "C00031" in links
    assert len(links["C00031"]) == 3
    assert "R00299" in links["C00031"]
