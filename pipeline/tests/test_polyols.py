from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.polyols import generate_polyols


def test_polyol_from_aldose():
    """Reducing an aldose removes C1 carbonyl, creating a polyol."""
    compounds = enumerate_all_monosaccharides()
    polyols = generate_polyols(compounds)
    assert len(polyols) > 0
    assert all(p["type"] == "polyol" for p in polyols)


def test_polyol_degeneracy_detected():
    """D-Galactose and D-Allose should reduce to the same polyol (Galactitol/Allitol).

    D-GAL has config RSRR; reversed is RRSR which is D-ALL's config.
    max('RSRR', 'RRSR') == max('RRSR', 'RSRR') == 'RSRR', so they collide.
    """
    compounds = enumerate_all_monosaccharides()
    polyols = generate_polyols(compounds)
    gal_polyol = [p for p in polyols if "D-GAL" in p.get("metadata", {}).get("reduction_parents", [])]
    assert len(gal_polyol) == 1
    all_parents = gal_polyol[0]["metadata"]["reduction_parents"]
    assert "D-ALL" in all_parents


def test_polyol_ids_unique():
    """All polyol IDs should be unique."""
    compounds = enumerate_all_monosaccharides()
    polyols = generate_polyols(compounds)
    ids = [p["id"] for p in polyols]
    assert len(ids) == len(set(ids))


def test_polyol_has_parent():
    """Every polyol should reference at least one parent monosaccharide."""
    compounds = enumerate_all_monosaccharides()
    polyols = generate_polyols(compounds)
    for p in polyols:
        assert p["parent_monosaccharide"] is not None
