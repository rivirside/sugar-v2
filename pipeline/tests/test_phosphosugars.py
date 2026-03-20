"""Tests for phosphosugar enumeration and reactions."""

import re
from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.phosphosugars import generate_phosphosugars


def _get_all_compounds():
    """Helper: enumerate monosaccharides + phosphosugars."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    return mono, phospho


# --- Enumeration tests ---


def test_systematic_count():
    """136 systematic phosphosugars: 64 aldo-mono + 32 aldo-bis + 32 keto-mono + 8 keto-bis."""
    mono, phospho = _get_all_compounds()
    systematic = [p for p in phospho if not p["metadata"].get("curated")]
    assert len(systematic) == 136


def test_curated_count():
    """8 curated phosphosugars (G3P, DHAP, E4P, R5P, Ru5P, Xu5P, S7P, F26BP)."""
    mono, phospho = _get_all_compounds()
    curated = [p for p in phospho if p["metadata"].get("curated")]
    assert len(curated) == 8


def test_total_count():
    """144 total phosphosugars."""
    mono, phospho = _get_all_compounds()
    assert len(phospho) == 144


def test_all_type_phosphate():
    """Every phosphosugar has type='phosphate'."""
    mono, phospho = _get_all_compounds()
    assert all(p["type"] == "phosphate" for p in phospho)


def test_ids_unique():
    """All phosphosugar IDs are unique."""
    mono, phospho = _get_all_compounds()
    ids = [p["id"] for p in phospho]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"


def test_modifications_non_empty():
    """Every phosphosugar has a non-empty modifications list."""
    mono, phospho = _get_all_compounds()
    for p in phospho:
        assert isinstance(p["modifications"], list)
        assert len(p["modifications"]) > 0
        for mod in p["modifications"]:
            assert mod["type"] == "phosphate"
            assert isinstance(mod["position"], int)
            assert mod["position"] >= 1


def test_parent_exists():
    """Every parent_monosaccharide references an existing compound."""
    mono, phospho = _get_all_compounds()
    mono_ids = {c["id"] for c in mono}
    for p in phospho:
        assert p["parent_monosaccharide"] in mono_ids, (
            f"{p['id']} references missing parent {p['parent_monosaccharide']}"
        )


def test_stereocenters_inherited():
    """Stereocenters match the parent monosaccharide."""
    mono, phospho = _get_all_compounds()
    mono_map = {c["id"]: c for c in mono}
    for p in phospho:
        parent = mono_map[p["parent_monosaccharide"]]
        assert p["stereocenters"] == parent["stereocenters"], (
            f"{p['id']} stereocenters {p['stereocenters']} != parent {parent['stereocenters']}"
        )


def test_chirality_inherited():
    """Chirality matches the parent monosaccharide."""
    mono, phospho = _get_all_compounds()
    mono_map = {c["id"]: c for c in mono}
    for p in phospho:
        parent = mono_map[p["parent_monosaccharide"]]
        assert p["chirality"] == parent["chirality"]


def test_carbons_inherited():
    """Carbon count matches the parent monosaccharide."""
    mono, phospho = _get_all_compounds()
    mono_map = {c["id"]: c for c in mono}
    for p in phospho:
        parent = mono_map[p["parent_monosaccharide"]]
        assert p["carbons"] == parent["carbons"]


def _parse_formula(formula: str) -> dict[str, int]:
    """Parse molecular formula into element counts."""
    atoms: dict[str, int] = {}
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        if element:
            atoms[element] = atoms.get(element, 0) + count
    return atoms


def test_formula_correctness():
    """Phosphosugar formula = parent + n * PO3H (per phosphate group)."""
    mono, phospho = _get_all_compounds()
    mono_map = {c["id"]: c for c in mono}
    for p in phospho:
        parent = mono_map[p["parent_monosaccharide"]]
        parent_atoms = _parse_formula(parent["formula"])
        phospho_atoms = _parse_formula(p["formula"])
        n_phosphates = len(p["modifications"])

        expected = dict(parent_atoms)
        expected["P"] = expected.get("P", 0) + n_phosphates
        expected["O"] = expected.get("O", 0) + 3 * n_phosphates
        expected["H"] = expected.get("H", 0) + 1 * n_phosphates

        assert phospho_atoms == expected, (
            f"{p['id']}: formula {p['formula']} != expected from {parent['formula']} + {n_phosphates}xPO3H"
        )


def test_metadata_has_required_fields():
    """Metadata includes phosphate_positions, parent_type, curated."""
    mono, phospho = _get_all_compounds()
    for p in phospho:
        meta = p["metadata"]
        assert "phosphate_positions" in meta
        assert "parent_type" in meta
        assert meta["parent_type"] in ("aldose", "ketose")
        assert "curated" in meta


def test_c2_excluded_from_systematic():
    """No systematic phosphosugar has a phosphate at position 2."""
    mono, phospho = _get_all_compounds()
    systematic = [p for p in phospho if not p["metadata"].get("curated")]
    for p in systematic:
        positions = [m["position"] for m in p["modifications"]]
        assert 2 not in positions, f"{p['id']} has position 2 phosphate"


def test_known_compounds_present():
    """Key biologically important phosphosugars are generated."""
    mono, phospho = _get_all_compounds()
    ids = {p["id"] for p in phospho}
    expected = {"D-GLC-6P", "D-FRU-6P", "D-FRU-1,6BP", "D-GLYC-3P", "DHA-1P",
                "D-RIB-5P", "D-RBU-5P", "D-XLU-5P", "D-SED-7P", "D-FRU-2,6BP"}
    missing = expected - ids
    assert not missing, f"Missing expected compounds: {missing}"
