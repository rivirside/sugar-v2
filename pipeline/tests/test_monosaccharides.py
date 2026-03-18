from pipeline.enumerate.monosaccharides import enumerate_aldoses, enumerate_ketoses


def test_c3_aldoses_count():
    """C3 aldoses have 1 chiral center -> 2 stereoisomers (D and L)."""
    result = enumerate_aldoses(3)
    assert len(result) == 2


def test_c4_aldoses_count():
    """C4 aldoses have 2 chiral centers -> 4 stereoisomers."""
    result = enumerate_aldoses(4)
    assert len(result) == 4


def test_c5_aldoses_count():
    """C5 aldoses have 3 chiral centers -> 8 stereoisomers."""
    result = enumerate_aldoses(5)
    assert len(result) == 8


def test_c6_aldoses_count():
    """C6 aldoses have 4 chiral centers -> 16 stereoisomers."""
    result = enumerate_aldoses(6)
    assert len(result) == 16


def test_c7_aldoses_count():
    """C7 aldoses have 5 chiral centers -> 32 stereoisomers."""
    result = enumerate_aldoses(7)
    assert len(result) == 32


def test_aldose_total_c2_to_c7():
    """Total aldoses C2-C7 = 1 + 2 + 4 + 8 + 16 + 32 = 63."""
    all_aldoses = []
    for c in range(2, 8):
        all_aldoses.extend(enumerate_aldoses(c))
    assert len(all_aldoses) == 63


def test_aldose_has_required_fields():
    """Each aldose must have id, name, type, carbons, chirality, stereocenters."""
    result = enumerate_aldoses(6)
    compound = result[0]
    assert "id" in compound
    assert "name" in compound
    assert compound["type"] == "aldose"
    assert compound["carbons"] == 6
    assert compound["chirality"] in ("D", "L")
    assert "stereocenters" in compound
    assert isinstance(compound["stereocenters"], list)
    assert len(compound["stereocenters"]) == 4  # C6 aldose: C2,C3,C4,C5


def test_aldose_stereocenters_are_unique():
    """No two aldoses at the same carbon count should have identical stereocenters."""
    result = enumerate_aldoses(6)
    configs = [tuple(c["stereocenters"]) for c in result]
    assert len(configs) == len(set(configs))


def test_c2_aldose_is_glycolaldehyde():
    """C2 has no chiral centers -> 1 achiral compound."""
    result = enumerate_aldoses(2)
    assert len(result) == 1
    assert result[0]["chirality"] == "achiral"
    assert result[0]["stereocenters"] == []


# Ketose tests
def test_c3_ketoses_count():
    """C3 ketose (DHA) has 0 chiral centers -> 1 achiral compound."""
    result = enumerate_ketoses(3)
    assert len(result) == 1
    assert result[0]["chirality"] == "achiral"


def test_c4_ketoses_count():
    result = enumerate_ketoses(4)
    assert len(result) == 2


def test_c5_ketoses_count():
    result = enumerate_ketoses(5)
    assert len(result) == 4


def test_c6_ketoses_count():
    result = enumerate_ketoses(6)
    assert len(result) == 8


def test_c7_ketoses_count():
    result = enumerate_ketoses(7)
    assert len(result) == 16


def test_ketose_total():
    """Total ketoses C3-C7 = 1 + 2 + 4 + 8 + 16 = 31."""
    all_ketoses = []
    for c in range(3, 8):
        all_ketoses.extend(enumerate_ketoses(c))
    assert len(all_ketoses) == 31


def test_all_monosaccharides_total():
    """63 aldoses + 31 ketoses = 94."""
    from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
    result = enumerate_all_monosaccharides()
    assert len(result) == 94


def test_all_ids_unique():
    """Every compound must have a unique ID."""
    from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
    result = enumerate_all_monosaccharides()
    ids = [c["id"] for c in result]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"


# Name mapping tests (Task 4)
def test_d_glucose_has_correct_name():
    """D-Glucose (C6 aldose, RSSR) should be named D-GLC."""
    result = enumerate_aldoses(6)
    d_glucose = [c for c in result if c["stereocenters"] == ["R", "S", "S", "R"]]
    assert len(d_glucose) == 1
    assert d_glucose[0]["id"] == "D-GLC"
    assert d_glucose[0]["name"] == "D-Glucose"


def test_d_fructose_has_correct_name():
    """D-Fructose (C6 ketose, SSR) should be named D-FRU."""
    result = enumerate_ketoses(6)
    d_fructose = [c for c in result if c["stereocenters"] == ["S", "S", "R"]]
    assert len(d_fructose) == 1
    assert d_fructose[0]["id"] == "D-FRU"
    assert d_fructose[0]["name"] == "D-Fructose"


def test_unnamed_compound_gets_systematic_id():
    """C7 heptoses without common names get systematic IDs."""
    result = enumerate_aldoses(7)
    systematic = [c for c in result if c["id"].startswith("ALDO-")]
    assert len(systematic) > 0
