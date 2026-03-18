from pipeline.validate.completeness import check_completeness
from pipeline.validate.duplicates import check_duplicates
from pipeline.validate.mass_balance import check_mass_balance
from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides


def test_completeness_passes_for_full_set():
    compounds = enumerate_all_monosaccharides()
    warnings = check_completeness(compounds)
    assert len(warnings) == 0

def test_completeness_warns_on_missing():
    compounds = enumerate_all_monosaccharides()
    compounds = compounds[:-1]
    warnings = check_completeness(compounds)
    assert len(warnings) > 0

def test_no_duplicates_in_full_set():
    compounds = enumerate_all_monosaccharides()
    duplicates = check_duplicates(compounds)
    assert len(duplicates) == 0

def test_detects_duplicate():
    compounds = enumerate_all_monosaccharides()
    compounds.append(compounds[0].copy())
    compounds[-1]["id"] = "DUPLICATE"
    duplicates = check_duplicates(compounds)
    assert len(duplicates) > 0

def test_mass_balance_passes_for_epimerization():
    compounds = [{"id": "D-GLC", "carbons": 6, "type": "aldose"}, {"id": "D-MAN", "carbons": 6, "type": "aldose"}]
    reactions = [{"id": "EPI-001", "substrates": ["D-GLC"], "products": ["D-MAN"], "reaction_type": "epimerization"}]
    errors = check_mass_balance(reactions, {c["id"]: c for c in compounds})
    assert len(errors) == 0

def test_mass_balance_fails_on_carbon_mismatch():
    compounds = [{"id": "D-GLC", "carbons": 6, "type": "aldose"}, {"id": "D-ERY", "carbons": 4, "type": "aldose"}]
    reactions = [{"id": "BAD-001", "substrates": ["D-GLC"], "products": ["D-ERY"], "reaction_type": "epimerization"}]
    errors = check_mass_balance(reactions, {c["id"]: c for c in compounds})
    assert len(errors) > 0
