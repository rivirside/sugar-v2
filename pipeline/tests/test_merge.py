"""Tests for merge module."""

import pytest
from pipeline.import_.merge import enrich_compound, enrich_reaction_with_rhea, create_rhea_reaction, determine_evidence_tier


def test_enrich_compound():
    compound = {"id": "D-GLC", "name": "D-Glucose", "aliases": ["Dextrose"], "chebi_id": None, "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None}
    match = {"chebi_id": "CHEBI:17634", "kegg_id": "C00031", "pubchem_id": "5793", "inchi": "InChI=1S/test", "smiles": "OCC1OC(O)C(O)C(O)C1O", "chebi_name": "D-glucopyranose"}
    result = enrich_compound(compound, match)
    assert result["chebi_id"] == "CHEBI:17634"
    assert result["kegg_id"] == "C00031"
    assert result["inchi"] == "InChI=1S/test"
    assert result["name"] == "D-Glucose"
    assert "D-glucopyranose" in result["aliases"]


def test_enrich_compound_no_duplicate_aliases():
    compound = {"id": "D-GLC", "name": "D-Glucose", "aliases": ["Dextrose"], "chebi_id": None, "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None}
    match = {"chebi_id": "CHEBI:17634", "chebi_name": "D-Glucose", "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None}
    result = enrich_compound(compound, match)
    assert result["aliases"].count("D-Glucose") == 0


def test_create_rhea_reaction():
    rhea_data = {"rhea_id": "RHEA:10001", "ec_number": "5.3.1.9", "substrate_chebi_ids": ["CHEBI:17634"], "product_chebi_ids": ["CHEBI:48095"], "pmids": ["12345678"]}
    chebi_to_compound = {"CHEBI:17634": "D-GLC", "CHEBI:48095": "D-FRU"}
    result = create_rhea_reaction(rhea_data, chebi_to_compound)
    assert result["id"] == "RHEA:10001"
    assert result["substrates"] == ["D-GLC"]
    assert result["products"] == ["D-FRU"]
    assert result["ec_number"] == "5.3.1.9"
    assert result["evidence_tier"] == "validated"


def test_determine_evidence_tier_validated():
    assert determine_evidence_tier(pmids=["123"], ec_number="5.3.1.9") == "validated"

def test_determine_evidence_tier_predicted_ec():
    assert determine_evidence_tier(pmids=[], ec_number="5.3.1.9") == "predicted"

def test_determine_evidence_tier_predicted_rhea_only():
    assert determine_evidence_tier(pmids=[], ec_number=None) == "predicted"
