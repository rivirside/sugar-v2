"""Tests for RHEA importer."""

import pytest
from pipeline.import_.rhea import parse_sparql_results, classify_reaction_participants


SAMPLE_SPARQL_RESULT = {
    "results": {
        "bindings": [
            {
                "rheaId": {"value": "10001"},
                "equation": {"value": "D-glucose = D-fructose"},
                "ec": {"value": "5.3.1.9"},
                "substrateId": {"value": "http://purl.obolibrary.org/obo/CHEBI_17634"},
                "productId": {"value": "http://purl.obolibrary.org/obo/CHEBI_48095"},
            },
            {
                "rheaId": {"value": "10002"},
                "equation": {"value": "D-glucose + NAD+ = D-gluconate + NADH"},
                "ec": {"value": "1.1.1.47"},
                "substrateId": {"value": "http://purl.obolibrary.org/obo/CHEBI_17634"},
                "productId": {"value": "http://purl.obolibrary.org/obo/CHEBI_18391"},
            },
        ]
    }
}


def test_parse_sparql_results():
    reactions = parse_sparql_results(SAMPLE_SPARQL_RESULT)
    assert len(reactions) >= 2
    r1 = next(r for r in reactions if r["rhea_id"] == "RHEA:10001")
    assert "CHEBI:17634" in r1["substrate_chebi_ids"]
    assert "CHEBI:48095" in r1["product_chebi_ids"]
    assert r1["ec_number"] == "5.3.1.9"


def test_classify_participants():
    known_chebi_ids = {"CHEBI:17634", "CHEBI:48095"}
    reaction = {
        "substrate_chebi_ids": ["CHEBI:17634", "CHEBI:15846"],
        "product_chebi_ids": ["CHEBI:48095", "CHEBI:16908"],
    }
    result = classify_reaction_participants(reaction, known_chebi_ids)
    assert "CHEBI:17634" in result["known_substrates"]
    assert "CHEBI:15846" in result["unknown_substrates"]
    assert "CHEBI:48095" in result["known_products"]
    assert "CHEBI:16908" in result["unknown_products"]
