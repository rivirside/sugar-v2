# Phosphosugars Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ~144 phosphorylated sugar compounds and ~1,240 new reactions to the SUGAR pipeline.

**Architecture:** New enumeration module (`phosphosugars.py`) derives phosphosugars from existing monosaccharides. New reaction module (`phosphorylation.py`) generates 5 reaction types. Existing validation and pipeline orchestrator are updated to handle the new compound type. TDD throughout.

**Tech Stack:** Python 3, pytest, Next.js TypeScript types

**Spec:** `docs/superpowers/specs/2026-03-19-phosphosugars-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `pipeline/data/name_mapping.json` | Modify | Add sedoheptulose parent + ~20 phosphosugar name entries |
| `web/lib/types.ts` | Modify | Update `modifications` field type to array |
| `pipeline/enumerate/phosphosugars.py` | Create | Systematic + curated phosphosugar enumeration |
| `pipeline/reactions/phosphorylation.py` | Create | 5 reaction types: phos, dephos, mutase, epi, iso |
| `pipeline/tests/test_phosphosugars.py` | Create | All enumeration + reaction tests |
| `pipeline/validate/completeness.py` | Modify | Add phosphosugar expected counts |
| `pipeline/validate/duplicates.py` | Modify | Include modifications in grouping key |
| `pipeline/reactions/generate.py` | Modify | Filter out phosphosugars from existing generators |
| `pipeline/run_pipeline.py` | Modify | Wire in phosphosugar steps, update numbering + metadata |

---

## Chunk 1: Data Layer and Types

### Task 1: Name Mapping Updates

**Files:**
- Modify: `pipeline/data/name_mapping.json`

- [ ] **Step 1: Add sedoheptulose parent entry**

Add to `pipeline/data/name_mapping.json` (after the existing `ketose-C6-*` entries, before the `polyol-*` entries):

```json
"ketose-C7-SRRR": {"id": "D-SED", "name": "D-Sedoheptulose", "aliases": ["Sedoheptulose"]}
```

- [ ] **Step 2: Add phosphosugar name entries**

Add to `pipeline/data/name_mapping.json` (after all polyol entries, at the end before the closing `}`):

```json
"phosphate-C6-RSSR-1P": {"id": "D-GLC-1P", "name": "D-Glucose 1-phosphate", "aliases": ["G1P"]},
"phosphate-C6-RSSR-6P": {"id": "D-GLC-6P", "name": "D-Glucose 6-phosphate", "aliases": ["G6P"]},
"phosphate-C6-RSSR-1,6BP": {"id": "D-GLC-1,6BP", "name": "D-Glucose 1,6-bisphosphate", "aliases": []},
"phosphate-C6-SSSR-6P": {"id": "D-MAN-6P", "name": "D-Mannose 6-phosphate", "aliases": ["M6P"]},
"phosphate-C6-SSSR-1P": {"id": "D-MAN-1P", "name": "D-Mannose 1-phosphate", "aliases": []},
"phosphate-C6-RSRR-1P": {"id": "D-GAL-1P", "name": "D-Galactose 1-phosphate", "aliases": ["Gal-1-P"]},
"phosphate-C6-SSR-1P": {"id": "D-FRU-1P", "name": "D-Fructose 1-phosphate", "aliases": ["F1P"]},
"phosphate-C6-SSR-6P": {"id": "D-FRU-6P", "name": "D-Fructose 6-phosphate", "aliases": ["F6P"]},
"phosphate-C6-SSR-1,6BP": {"id": "D-FRU-1,6BP", "name": "D-Fructose 1,6-bisphosphate", "aliases": ["F16BP", "FBP"]},
"phosphate-C3-R-3P": {"id": "D-GLYC-3P", "name": "D-Glyceraldehyde 3-phosphate", "aliases": ["G3P", "GAP"]},
"phosphate-C3-1P": {"id": "DHA-1P", "name": "Dihydroxyacetone phosphate", "aliases": ["DHAP"]},
"phosphate-C4-RR-4P": {"id": "D-ERY-4P", "name": "D-Erythrose 4-phosphate", "aliases": ["E4P"]},
"phosphate-C5-RRR-5P": {"id": "D-RIB-5P", "name": "D-Ribose 5-phosphate", "aliases": ["R5P"]},
"phosphate-C5-RR-5P": {"id": "D-RBU-5P", "name": "D-Ribulose 5-phosphate", "aliases": ["Ru5P"]},
"phosphate-C5-SR-5P": {"id": "D-XLU-5P", "name": "D-Xylulose 5-phosphate", "aliases": ["Xu5P"]},
"phosphate-C7-SRRR-7P": {"id": "D-SED-7P", "name": "D-Sedoheptulose 7-phosphate", "aliases": ["S7P"]},
"phosphate-C6-SSR-2,6BP": {"id": "D-FRU-2,6BP", "name": "D-Fructose 2,6-bisphosphate", "aliases": ["F26BP"]}
```

- [ ] **Step 3: Verify JSON is valid**

Run: `python -c "import json; json.load(open('pipeline/data/name_mapping.json'))"`
Expected: no error

- [ ] **Step 4: Run existing tests to confirm nothing breaks**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/ -v`
Expected: all 80 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/data/name_mapping.json
git commit -m "feat: add phosphosugar name mappings and sedoheptulose parent entry"
```

---

### Task 2: TypeScript Type Update

**Files:**
- Modify: `web/lib/types.ts:39`

- [ ] **Step 1: Update modifications type**

In `web/lib/types.ts`, change line 39 from:

```typescript
modifications: Record<string, unknown> | null;
```

to:

```typescript
modifications: Array<{ type: string; position: number }> | null;
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx tsc --noEmit`
Expected: no errors (existing compounds all have `modifications: null`, which satisfies both types)

- [ ] **Step 3: Commit**

```bash
git add web/lib/types.ts
git commit -m "feat: update modifications type to support phosphosugar array format"
```

---

## Chunk 2: Phosphosugar Enumeration (TDD)

### Task 3: Write Enumeration Tests

**Files:**
- Create: `pipeline/tests/test_phosphosugars.py`

- [ ] **Step 1: Write enumeration test file**

Create `pipeline/tests/test_phosphosugars.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_phosphosugars.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.enumerate.phosphosugars'`

---

### Task 4: Implement Phosphosugar Enumeration

**Files:**
- Create: `pipeline/enumerate/phosphosugars.py`

- [ ] **Step 1: Create the enumeration module**

Create `pipeline/enumerate/phosphosugars.py`:

```python
"""Generate phosphorylated sugar derivatives from monosaccharides."""

import json
import os
import re

_NAME_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "name_mapping.json")
_NAME_MAP: dict = {}


def _load_name_map() -> dict:
    global _NAME_MAP
    if not _NAME_MAP and os.path.exists(_NAME_MAP_PATH):
        with open(_NAME_MAP_PATH) as f:
            _NAME_MAP = json.load(f)
    return _NAME_MAP


def _parse_formula(formula: str) -> dict[str, int]:
    """Parse 'C6H12O6' into {'C': 6, 'H': 12, 'O': 6}."""
    atoms: dict[str, int] = {}
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        if element:
            atoms[element] = atoms.get(element, 0) + count
    return atoms


def _format_formula(atoms: dict[str, int]) -> str:
    """Format {'C': 6, 'H': 13, 'O': 9, 'P': 1} into 'C6H13O9P'."""
    order = ["C", "H", "N", "O", "P", "S"]
    parts = []
    for elem in order:
        if elem in atoms and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    for elem in sorted(atoms):
        if elem not in order and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    return "".join(parts)


def _phospho_formula(parent_formula: str, n_phosphates: int) -> str:
    """Compute formula after adding n phosphate groups.

    Each phosphate ester: net +1P, +3O, +1H (sugar-OH + H3PO4 -> sugar-O-PO3H2 + H2O).
    """
    atoms = _parse_formula(parent_formula)
    atoms["P"] = atoms.get("P", 0) + n_phosphates
    atoms["O"] = atoms.get("O", 0) + 3 * n_phosphates
    atoms["H"] = atoms.get("H", 0) + 1 * n_phosphates
    return _format_formula(atoms)


def _phosphate_suffix(positions: list[int]) -> str:
    """Generate ID suffix: [6] -> '6P', [1,6] -> '1,6BP'."""
    if len(positions) == 1:
        return f"{positions[0]}P"
    elif len(positions) == 2:
        return f"{positions[0]},{positions[1]}BP"
    else:
        return f"{','.join(str(p) for p in positions)}{'T' if len(positions) == 3 else ''}P"


def _resolve_phospho_name(
    parent: dict, positions: list[int], stereo_key: str
) -> tuple[str, str, list[str]]:
    """Look up human-readable name for a phosphosugar, fall back to systematic."""
    name_map = _load_name_map()
    suffix = _phosphate_suffix(positions)
    lookup_key = f"phosphate-C{parent['carbons']}-{stereo_key}-{suffix}" if stereo_key else f"phosphate-C{parent['carbons']}-{suffix}"

    if lookup_key in name_map:
        entry = name_map[lookup_key]
        return entry["id"], entry["name"], entry.get("aliases", [])

    # Systematic fallback
    parent_id = parent["id"]
    compound_id = f"{parent_id}-{suffix}"
    pos_str = ", ".join(str(p) for p in positions)
    if len(positions) == 1:
        compound_name = f"{parent['name']} {pos_str}-phosphate"
    else:
        compound_name = f"{parent['name']} {pos_str}-bisphosphate"
    return compound_id, compound_name, []


def _make_phosphosugar(
    parent: dict, positions: list[int], curated: bool = False
) -> dict:
    """Create a phosphosugar compound dict from a parent monosaccharide."""
    stereo_key = "".join(parent["stereocenters"]) if parent["stereocenters"] else ""
    compound_id, name, aliases = _resolve_phospho_name(parent, positions, stereo_key)

    modifications = [{"type": "phosphate", "position": p} for p in positions]

    return {
        "id": compound_id,
        "name": name,
        "aliases": aliases,
        "type": "phosphate",
        "carbons": parent["carbons"],
        "chirality": parent["chirality"],
        "formula": _phospho_formula(parent["formula"], len(positions)),
        "stereocenters": list(parent["stereocenters"]),
        "modifications": modifications,
        "parent_monosaccharide": parent["id"],
        "commercial": False,
        "cost_usd_per_kg": None,
        "metadata": {
            "phosphate_positions": list(positions),
            "parent_type": parent["type"],
            "curated": curated,
        },
        "chebi_id": None,
        "kegg_id": None,
        "pubchem_id": None,
        "inchi": None,
        "smiles": None,
    }


# Systematic phosphorylation positions (C2 excluded)
ALDOHEXOSE_MONO_POSITIONS = [1, 3, 4, 6]
ALDOHEXOSE_BIS_POSITIONS = [(1, 6), (3, 6)]
KETOHEXOSE_MONO_POSITIONS = [1, 3, 4, 6]
KETOHEXOSE_BIS_POSITIONS = [(1, 6)]

# Curated phosphosugars: (parent_id, positions)
CURATED_PHOSPHOSUGARS = [
    ("D-GLYC", [3]),       # Glyceraldehyde 3-phosphate
    ("DHA", [1]),          # Dihydroxyacetone phosphate
    ("D-ERY", [4]),        # Erythrose 4-phosphate
    ("D-RIB", [5]),        # Ribose 5-phosphate
    ("D-RBU", [5]),        # Ribulose 5-phosphate
    ("D-XLU", [5]),        # Xylulose 5-phosphate
    ("D-SED", [7]),        # Sedoheptulose 7-phosphate
    ("D-FRU", [2, 6]),     # Fructose 2,6-bisphosphate
]


def generate_phosphosugars(compounds: list[dict]) -> list[dict]:
    """Generate phosphorylated derivatives from monosaccharides.

    Systematic: all C6 aldohexose and ketohexose stereoisomers at valid positions.
    Curated: biologically important phosphosugars from other carbon lengths.

    Args:
        compounds: list of monosaccharide compounds (from enumerate_all_monosaccharides)

    Returns:
        list of phosphosugar compound dicts
    """
    compound_map = {c["id"]: c for c in compounds}
    phosphosugars: list[dict] = []

    # --- Systematic enumeration ---
    c6_aldohexoses = [
        c for c in compounds
        if c["type"] == "aldose" and c["carbons"] == 6
    ]
    c6_ketohexoses = [
        c for c in compounds
        if c["type"] == "ketose" and c["carbons"] == 6
    ]

    # Aldohexose mono-phosphates
    for parent in c6_aldohexoses:
        for pos in ALDOHEXOSE_MONO_POSITIONS:
            phosphosugars.append(_make_phosphosugar(parent, [pos]))

    # Aldohexose bisphosphates
    for parent in c6_aldohexoses:
        for pos_pair in ALDOHEXOSE_BIS_POSITIONS:
            phosphosugars.append(_make_phosphosugar(parent, list(pos_pair)))

    # Ketohexose mono-phosphates
    for parent in c6_ketohexoses:
        for pos in KETOHEXOSE_MONO_POSITIONS:
            phosphosugars.append(_make_phosphosugar(parent, [pos]))

    # Ketohexose bisphosphates
    for parent in c6_ketohexoses:
        for pos_pair in KETOHEXOSE_BIS_POSITIONS:
            phosphosugars.append(_make_phosphosugar(parent, list(pos_pair)))

    # --- Curated additions ---
    for parent_id, positions in CURATED_PHOSPHOSUGARS:
        parent = compound_map.get(parent_id)
        if parent is None:
            raise ValueError(f"Curated phosphosugar parent '{parent_id}' not found in compounds")
        phosphosugars.append(_make_phosphosugar(parent, positions, curated=True))

    return phosphosugars
```

- [ ] **Step 2: Run enumeration tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_phosphosugars.py -v`
Expected: all enumeration tests pass

- [ ] **Step 3: Run ALL tests to ensure no regressions**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/ -v`
Expected: all tests pass (80 existing + new phosphosugar tests)

- [ ] **Step 4: Commit**

```bash
git add pipeline/enumerate/phosphosugars.py pipeline/tests/test_phosphosugars.py
git commit -m "feat: add phosphosugar enumeration with TDD tests (144 compounds)"
```

---

## Chunk 3: Reaction Generation (TDD)

### Task 5: Write Reaction Tests

**Files:**
- Modify: `pipeline/tests/test_phosphosugars.py`

- [ ] **Step 1: Add reaction tests**

Append to `pipeline/tests/test_phosphosugars.py`:

```python
from pipeline.enumerate.polyols import generate_polyols
from pipeline.reactions.phosphorylation import (
    generate_phosphorylations,
    generate_dephosphorylations,
    generate_mutases,
    generate_phospho_epimerizations,
    generate_phospho_isomerizations,
)


def _get_all_with_reactions():
    """Helper: get compounds + all phospho-reactions."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    all_compounds = mono + phospho
    phos = generate_phosphorylations(phospho)
    dephos = generate_dephosphorylations(phospho)
    mutases = generate_mutases(phospho)
    epi = generate_phospho_epimerizations(phospho)
    iso = generate_phospho_isomerizations(phospho)
    return all_compounds, phospho, phos, dephos, mutases, epi, iso


# --- Phosphorylation tests ---


def test_phosphorylation_count():
    """One phosphorylation per phosphosugar."""
    _, phospho, phos, _, _, _, _ = _get_all_with_reactions()
    assert len(phos) == len(phospho)


def test_phosphorylation_links_parent():
    """Each phosphorylation substrate is the parent monosaccharide."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    mono_map = {c["id"]: c for c in mono}
    phos = generate_phosphorylations(phospho)
    for r in phos:
        sub_id = r["substrates"][0]
        prod_id = r["products"][0]
        prod = next(p for p in phospho if p["id"] == prod_id)
        assert sub_id == prod["parent_monosaccharide"], (
            f"Reaction {r['id']}: substrate {sub_id} != parent {prod['parent_monosaccharide']}"
        )


def test_phosphorylation_fields():
    """Phosphorylation reactions have correct type, cofactor, and tier."""
    _, _, phos, _, _, _, _ = _get_all_with_reactions()
    for r in phos:
        assert r["reaction_type"] == "phosphorylation"
        assert r["cofactor_burden"] == 1.0
        assert r["evidence_tier"] == "hypothetical"


# --- Dephosphorylation tests ---


def test_dephosphorylation_count():
    """One dephosphorylation per phosphosugar."""
    _, phospho, _, dephos, _, _, _ = _get_all_with_reactions()
    assert len(dephos) == len(phospho)


def test_dephosphorylation_reverse_of_phos():
    """Each dephosphorylation is substrate=phosphosugar, product=parent."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    dephos = generate_dephosphorylations(phospho)
    for r in dephos:
        sub_id = r["substrates"][0]
        prod_id = r["products"][0]
        sub = next(p for p in phospho if p["id"] == sub_id)
        assert prod_id == sub["parent_monosaccharide"]


def test_dephosphorylation_fields():
    """Dephosphorylation has cofactor_burden=0.0."""
    _, _, _, dephos, _, _, _ = _get_all_with_reactions()
    for r in dephos:
        assert r["reaction_type"] == "dephosphorylation"
        assert r["cofactor_burden"] == 0.0


# --- Mutase tests ---


def test_mutase_between_same_parent():
    """Mutases connect mono-phosphosugars sharing the same parent."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    mutases = generate_mutases(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in mutases:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        assert sub["parent_monosaccharide"] == prod["parent_monosaccharide"]
        assert sub["stereocenters"] == prod["stereocenters"]


def test_mutase_different_positions():
    """Mutase substrate and product have different phosphate positions."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    mutases = generate_mutases(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in mutases:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        assert sub["metadata"]["phosphate_positions"] != prod["metadata"]["phosphate_positions"]


def test_mutase_only_mono_phosphates():
    """Mutases only involve mono-phosphosugars (not bisphosphates)."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    mutases = generate_mutases(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in mutases:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        assert len(sub["modifications"]) == 1
        assert len(prod["modifications"]) == 1


def test_mutase_count():
    """Expected: 24 parents x C(4,2) pairs x 2 directions = 288 directed."""
    _, _, _, _, mutases, _, _ = _get_all_with_reactions()
    assert len(mutases) == 288


def test_mutase_fields():
    """Mutase fields are correct."""
    _, _, _, _, mutases, _, _ = _get_all_with_reactions()
    for r in mutases:
        assert r["reaction_type"] == "mutase"
        assert r["cofactor_burden"] == 0.0


# --- Phospho-epimerization tests ---


def test_phospho_epi_single_stereocenter_diff():
    """Phospho-epimerizations differ at exactly one stereocenter."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    epi = generate_phospho_epimerizations(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in epi:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        diffs = sum(1 for a, b in zip(sub["stereocenters"], prod["stereocenters"]) if a != b)
        assert diffs == 1, f"Epimerization {r['id']} differs at {diffs} centers"


def test_phospho_epi_matching_modifications():
    """Phospho-epimerizations have matching phosphate patterns."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    epi = generate_phospho_epimerizations(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in epi:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        assert sub["metadata"]["phosphate_positions"] == prod["metadata"]["phosphate_positions"]


def test_phospho_epi_type():
    """Phospho-epimerization uses reaction_type='epimerization'."""
    _, _, _, _, _, epi, _ = _get_all_with_reactions()
    for r in epi:
        assert r["reaction_type"] == "epimerization"


# --- Phospho-isomerization tests ---


def test_phospho_iso_aldose_ketose_pairs():
    """Phospho-isomerizations connect aldose-P to ketose-P."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    iso = generate_phospho_isomerizations(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in iso:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        types = {sub["metadata"]["parent_type"], prod["metadata"]["parent_type"]}
        assert types == {"aldose", "ketose"}, f"Iso {r['id']} types: {types}"


def test_phospho_iso_matching_modifications():
    """Phospho-isomerizations have matching phosphate patterns."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    iso = generate_phospho_isomerizations(phospho)
    phospho_map = {p["id"]: p for p in phospho}
    for r in iso:
        sub = phospho_map[r["substrates"][0]]
        prod = phospho_map[r["products"][0]]
        assert sub["metadata"]["phosphate_positions"] == prod["metadata"]["phosphate_positions"]


def test_phospho_iso_type():
    """Phospho-isomerization uses reaction_type='isomerization'."""
    _, _, _, _, _, _, iso = _get_all_with_reactions()
    for r in iso:
        assert r["reaction_type"] == "isomerization"


def test_phospho_epi_count():
    """Expected: ~504 directed phospho-epimerization reactions.

    Aldohexose groups: 6 patterns x 32 pairs x 2 = 384
    Ketohexose groups: 5 patterns x 12 pairs x 2 = 120
    Total: 504
    """
    _, _, _, _, _, epi, _ = _get_all_with_reactions()
    assert len(epi) == 504


def test_phospho_iso_count():
    """Expected: ~160 directed phospho-isomerization reactions.

    4 shared mono-P patterns x 16 x 2 = 128
    1 shared bis-P pattern x 16 x 2 = 32
    Total: 160
    """
    _, _, _, _, _, _, iso = _get_all_with_reactions()
    assert len(iso) == 160


# --- Cross-cutting tests ---


def test_all_reaction_ids_unique():
    """All phosphosugar reaction IDs are unique."""
    _, _, phos, dephos, mutases, epi, iso = _get_all_with_reactions()
    all_rxns = phos + dephos + mutases + epi + iso
    ids = [r["id"] for r in all_rxns]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found"


def test_all_reactions_hypothetical():
    """All generated reactions have evidence_tier='hypothetical'."""
    _, _, phos, dephos, mutases, epi, iso = _get_all_with_reactions()
    all_rxns = phos + dephos + mutases + epi + iso
    for r in all_rxns:
        assert r["evidence_tier"] == "hypothetical"


def test_mass_balance_carbons():
    """All reactions conserve carbon count."""
    mono = enumerate_all_monosaccharides()
    phospho = generate_phosphosugars(mono)
    all_compounds = mono + phospho
    compound_map = {c["id"]: c for c in all_compounds}

    _, _, phos, dephos, mutases, epi, iso = _get_all_with_reactions()
    for r in phos + dephos + mutases + epi + iso:
        sub_carbons = sum(compound_map[s]["carbons"] for s in r["substrates"])
        prod_carbons = sum(compound_map[p]["carbons"] for p in r["products"])
        assert sub_carbons == prod_carbons, f"Reaction {r['id']}: {sub_carbons} != {prod_carbons}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_phosphosugars.py::test_phosphorylation_count -v`
Expected: FAIL — `ImportError: cannot import name 'generate_phosphorylations' from 'pipeline.reactions.phosphorylation'`

---

### Task 6: Implement Reaction Generation

**Files:**
- Create: `pipeline/reactions/phosphorylation.py`

- [ ] **Step 1: Create the reaction module**

Create `pipeline/reactions/phosphorylation.py`:

```python
"""Generate reactions involving phosphosugars."""

from itertools import combinations
from pipeline.reactions.score import compute_cost_score


def _base_reaction(reaction_id: str, substrate_id: str, product_id: str, reaction_type: str) -> dict:
    """Create a reaction dict with all required fields."""
    rxn = {
        "id": reaction_id,
        "reaction_type": reaction_type,
        "substrates": [substrate_id],
        "products": [product_id],
        "evidence_tier": "hypothetical",
        "evidence_criteria": [],
        "yield": None,
        "cofactor_burden": 0.0,
    }
    rxn["cost_score"] = compute_cost_score(rxn)
    return rxn


def generate_phosphorylations(phosphosugars: list[dict]) -> list[dict]:
    """Generate phosphorylation reactions: parent monosaccharide -> phosphosugar.

    One reaction per phosphosugar. Requires ATP (cofactor_burden=1.0).
    """
    reactions = []
    for ps in phosphosugars:
        parent_id = ps["parent_monosaccharide"]
        rxn_id = f"PHOS-C{ps['carbons']}-{ps['id']}"
        rxn = _base_reaction(rxn_id, parent_id, ps["id"], "phosphorylation")
        rxn["cofactor_burden"] = 1.0
        rxn["cost_score"] = compute_cost_score(rxn)
        reactions.append(rxn)
    return reactions


def generate_dephosphorylations(phosphosugars: list[dict]) -> list[dict]:
    """Generate dephosphorylation reactions: phosphosugar -> parent monosaccharide.

    Distinct enzyme class from kinases. No cofactor consumed.
    """
    reactions = []
    for ps in phosphosugars:
        parent_id = ps["parent_monosaccharide"]
        rxn_id = f"DEPHOS-C{ps['carbons']}-{ps['id']}"
        rxn = _base_reaction(rxn_id, ps["id"], parent_id, "dephosphorylation")
        reactions.append(rxn)
    return reactions


def generate_mutases(phosphosugars: list[dict]) -> list[dict]:
    """Generate mutase reactions: phosphate migration between positions on same sugar.

    Only between mono-phosphosugars sharing the same parent and stereocenters.
    Bidirectional (forward + reverse).
    """
    reactions = []

    # Group mono-phosphosugars by (parent_monosaccharide, stereocenters_tuple)
    groups: dict[tuple, list[dict]] = {}
    for ps in phosphosugars:
        if len(ps["modifications"]) != 1:
            continue  # Skip bisphosphates
        key = (ps["parent_monosaccharide"], tuple(ps["stereocenters"]))
        groups.setdefault(key, []).append(ps)

    for _key, group in groups.items():
        for sub, prod in combinations(group, 2):
            sub_pos = sub["metadata"]["phosphate_positions"][0]
            prod_pos = prod["metadata"]["phosphate_positions"][0]
            carbons = sub["carbons"]

            # Forward
            fwd_id = f"MUT-C{carbons}-{sub['id']}-{prod_pos}P"
            fwd = _base_reaction(fwd_id, sub["id"], prod["id"], "mutase")
            reactions.append(fwd)

            # Reverse
            rev_id = f"MUT-C{carbons}-{prod['id']}-{sub_pos}P"
            rev = _base_reaction(rev_id, prod["id"], sub["id"], "mutase")
            reactions.append(rev)

    return reactions


def generate_phospho_epimerizations(phosphosugars: list[dict]) -> list[dict]:
    """Generate epimerization reactions between phosphosugars with matching modifications.

    Same logic as standard epimerization: compounds must differ at exactly one
    stereocenter. Additionally, phosphate positions must match exactly.
    """
    reactions = []

    # Group by (parent_type, carbons, phosphate_positions_tuple)
    groups: dict[tuple, list[dict]] = {}
    for ps in phosphosugars:
        key = (
            ps["metadata"]["parent_type"],
            ps["carbons"],
            tuple(sorted(ps["metadata"]["phosphate_positions"])),
        )
        groups.setdefault(key, []).append(ps)

    for _key, group in groups.items():
        for sub, prod in combinations(group, 2):
            if len(sub["stereocenters"]) != len(prod["stereocenters"]):
                continue
            diffs = sum(
                1 for a, b in zip(sub["stereocenters"], prod["stereocenters"]) if a != b
            )
            if diffs != 1:
                continue

            carbons = sub["carbons"]

            # Forward
            fwd_id = f"EPI-C{carbons}-{sub['id']}-{prod['id']}"
            fwd = _base_reaction(fwd_id, sub["id"], prod["id"], "epimerization")
            reactions.append(fwd)

            # Reverse
            rev_id = f"EPI-C{carbons}-{prod['id']}-{sub['id']}"
            rev = _base_reaction(rev_id, prod["id"], sub["id"], "epimerization")
            reactions.append(rev)

    return reactions


def generate_phospho_isomerizations(phosphosugars: list[dict]) -> list[dict]:
    """Generate isomerization reactions between aldose-P and ketose-P.

    Same stereocenter-dropping logic as standard isomerization:
    ketose_stereocenters = aldose_stereocenters[1:]

    Only between phosphosugars with matching phosphate positions.
    """
    reactions = []

    # Separate aldose-derived and ketose-derived phosphosugars
    aldose_ps = [ps for ps in phosphosugars if ps["metadata"]["parent_type"] == "aldose"]
    ketose_ps = [ps for ps in phosphosugars if ps["metadata"]["parent_type"] == "ketose"]

    # Build ketose lookup: (carbons, stereocenters_tuple, phosphate_positions_tuple) -> compound
    ketose_map: dict[tuple, dict] = {}
    for kps in ketose_ps:
        key = (
            kps["carbons"],
            tuple(kps["stereocenters"]),
            tuple(sorted(kps["metadata"]["phosphate_positions"])),
        )
        ketose_map[key] = kps

    for aps in aldose_ps:
        if not aps["stereocenters"]:
            continue  # Skip achiral (C2)

        # Drop first stereocenter to get ketose config
        ketose_config = tuple(aps["stereocenters"][1:])
        phosphate_key = tuple(sorted(aps["metadata"]["phosphate_positions"]))
        lookup = (aps["carbons"], ketose_config, phosphate_key)
        kps = ketose_map.get(lookup)

        if kps is None:
            continue

        carbons = aps["carbons"]

        # Forward: aldose-P -> ketose-P
        fwd_id = f"ISO-C{carbons}-{aps['id']}-{kps['id']}"
        fwd = _base_reaction(fwd_id, aps["id"], kps["id"], "isomerization")
        reactions.append(fwd)

        # Reverse: ketose-P -> aldose-P
        rev_id = fwd_id + "-REV"
        rev = _base_reaction(rev_id, kps["id"], aps["id"], "isomerization")
        reactions.append(rev)

    return reactions
```

- [ ] **Step 2: Run reaction tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_phosphosugars.py -v`
Expected: all tests pass

- [ ] **Step 3: Run ALL tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/ -v`
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add pipeline/reactions/phosphorylation.py pipeline/tests/test_phosphosugars.py
git commit -m "feat: add phosphosugar reaction generation (5 types, ~1240 reactions)"
```

---

## Chunk 4: Validation, Filters, and Pipeline Integration

### Task 7: Update Validation Modules

**Files:**
- Modify: `pipeline/validate/duplicates.py`
- Modify: `pipeline/validate/completeness.py`

- [ ] **Step 1: Fix duplicate detection grouping key**

Replace the entire content of `pipeline/validate/duplicates.py`:

```python
"""Detect duplicate compounds based on stereocenters within the same group."""


def _modifications_key(compound: dict) -> tuple:
    """Build a hashable key from a compound's modifications list."""
    mods = compound.get("modifications")
    if not mods:
        return ()
    return tuple(sorted((m["type"], m["position"]) for m in mods))


def check_duplicates(compounds: list[dict]) -> list[dict]:
    """Check for duplicate compounds in the compound list.

    Duplicates are identified as compounds within the same (type, carbons, modifications)
    group that have identical stereocenters.

    Returns a list of dicts describing each duplicate found.
    An empty list means no duplicates exist.
    """
    # Group by (type, carbons, modifications_key)
    groups: dict[tuple, list[dict]] = {}
    for c in compounds:
        ctype = c.get("type")
        carbons = c.get("carbons")
        mod_key = _modifications_key(c)
        key = (ctype, carbons, mod_key)
        groups.setdefault(key, []).append(c)

    duplicates = []
    for (ctype, carbons, _mod_key), group in groups.items():
        # Track seen stereocenters within the group
        seen: dict[tuple, dict] = {}
        for c in group:
            stereocenters_key = tuple(c.get("stereocenters", []))
            if stereocenters_key in seen:
                duplicates.append({
                    "original": seen[stereocenters_key],
                    "duplicate": c,
                    "type": ctype,
                    "carbons": carbons,
                    "stereocenters": list(stereocenters_key),
                })
            else:
                seen[stereocenters_key] = c

    return duplicates
```

- [ ] **Step 2: Add phosphosugar completeness checks**

Replace the entire content of `pipeline/validate/completeness.py`:

```python
"""Validate that the compound set is complete (all expected stereoisomers present)."""

# Expected counts: key -> expected number of compounds
# Monosaccharides: (type, carbons)
# Phosphosugars: ("phosphate", parent_type, carbons, phosphate_positions_tuple)
EXPECTED_COUNTS: dict[tuple, int] = {}

# Aldoses C2-C7: number of stereocenters = max(0, carbons - 2)
for _carbons in range(2, 8):
    _n_chiral = max(0, _carbons - 2)
    EXPECTED_COUNTS[("aldose", _carbons)] = 2 ** _n_chiral

# Ketoses C3-C7: number of stereocenters = max(0, carbons - 3)
for _carbons in range(3, 8):
    _n_chiral = max(0, _carbons - 3)
    EXPECTED_COUNTS[("ketose", _carbons)] = 2 ** _n_chiral

# Phosphosugars: C6 aldohexoses (16 stereoisomers per position pattern)
for _pos in [(1,), (3,), (4,), (6,), (1, 6), (3, 6)]:
    EXPECTED_COUNTS[("phosphate", "aldose", 6, _pos)] = 16

# Phosphosugars: C6 ketohexoses (8 stereoisomers per position pattern)
for _pos in [(1,), (3,), (4,), (6,), (1, 6)]:
    EXPECTED_COUNTS[("phosphate", "ketose", 6, _pos)] = 8


def check_completeness(compounds: list[dict]) -> list[str]:
    """Check that all expected stereoisomers are present.

    Returns a list of warning strings describing any missing compounds.
    An empty list means the set is complete.
    """
    counts: dict[tuple, int] = {}
    for c in compounds:
        ctype = c.get("type")
        carbons = c.get("carbons")

        if ctype in ("aldose", "ketose") and carbons is not None:
            key = (ctype, carbons)
            counts[key] = counts.get(key, 0) + 1
        elif ctype == "phosphate" and not c.get("metadata", {}).get("curated"):
            parent_type = c.get("metadata", {}).get("parent_type")
            positions = tuple(sorted(c.get("metadata", {}).get("phosphate_positions", [])))
            if parent_type and carbons is not None and positions:
                key = ("phosphate", parent_type, carbons, positions)
                counts[key] = counts.get(key, 0) + 1

    warnings = []
    for key, expected in sorted(EXPECTED_COUNTS.items(), key=str):
        actual = counts.get(key, 0)
        if actual != expected:
            warnings.append(
                f"Expected {expected} compound(s) for group {key}, found {actual}"
            )

    return warnings
```

- [ ] **Step 3: Run existing validation tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_validate.py -v`
Expected: all validation tests pass

- [ ] **Step 4: Commit**

```bash
git add pipeline/validate/duplicates.py pipeline/validate/completeness.py
git commit -m "feat: update validation for phosphosugar support (completeness + dedup)"
```

---

### Task 8: Filter Existing Reaction Generators

**Files:**
- Modify: `pipeline/reactions/generate.py:33-46`

- [ ] **Step 1: Add phosphosugar filter to generate_epimerizations**

In `pipeline/reactions/generate.py`, change `generate_epimerizations` (line 33-69) to filter out phosphosugars at the start of the function. Replace lines 39-45:

```python
    # Group compounds by (type, carbons)
    groups: dict[tuple, list] = {}
    for c in compounds:
        key = (c["type"], c["carbons"])
        groups.setdefault(key, []).append(c)
```

with:

```python
    # Group compounds by (type, carbons) — skip phosphosugars (handled by phosphorylation.py)
    groups: dict[tuple, list] = {}
    for c in compounds:
        if c["type"] == "phosphate":
            continue
        key = (c["type"], c["carbons"])
        groups.setdefault(key, []).append(c)
```

- [ ] **Step 2: Add explicit phosphosugar filter to generate_isomerizations**

In `pipeline/reactions/generate.py`, change `generate_isomerizations` (line 72-108). Replace lines 85-86:

```python
    aldoses = [c for c in compounds if c["type"] == "aldose" and c["carbons"] >= 3]
    ketoses = [c for c in compounds if c["type"] == "ketose"]
```

with:

```python
    # Filter out phosphosugars explicitly (handled by phosphorylation.py)
    aldoses = [c for c in compounds if c["type"] == "aldose" and c["carbons"] >= 3]
    ketoses = [c for c in compounds if c["type"] == "ketose"]
```

Note: the existing type filters naturally exclude phosphosugars (`type == "phosphate"`), but this comment makes the exclusion explicit for maintainability. No functional change.

- [ ] **Step 3: Verify generate_reductions also safe**

`generate_reductions` takes `polyols` as a separate argument and iterates `polyol.metadata.reduction_parents`. It does not touch phosphosugars. No change needed.

- [ ] **Step 4: Run existing reaction tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/test_reactions.py -v`
Expected: all 9 reaction tests pass (no change in behavior for non-phosphosugar compounds)

- [ ] **Step 5: Commit**

```bash
git add pipeline/reactions/generate.py
git commit -m "fix: filter phosphosugars from existing reaction generators"
```

---

### Task 9: Pipeline Orchestrator Integration

**Files:**
- Modify: `pipeline/run_pipeline.py`

- [ ] **Step 1: Add imports**

In `pipeline/run_pipeline.py`, after line 10 (`from pipeline.enumerate.polyols import generate_polyols`), add:

```python
from pipeline.enumerate.phosphosugars import generate_phosphosugars
from pipeline.reactions.phosphorylation import (
    generate_phosphorylations,
    generate_dephosphorylations,
    generate_mutases,
    generate_phospho_epimerizations,
    generate_phospho_isomerizations,
)
```

- [ ] **Step 2: Update step numbering and add phosphosugar generation**

Replace the pipeline body from step 1 through step 7 (lines 48-115) with the updated version. Key changes:
- Step labels change from `[x/7]` to `[x/8]`
- New step 3: Generate phosphosugars
- Step 4 (was 3): Combine includes phosphosugars
- Step 6 (was 5): Generate reactions includes phosphosugar reactions
- All downstream step numbers increment by 1

Replace lines 48-115 with:

```python
    print("=== SUGAR v2 Pipeline ===")

    # Step 1: Enumerate monosaccharides
    print("\n[1/8] Enumerating monosaccharides...")
    monosaccharides = enumerate_all_monosaccharides()
    print(f"  -> {len(monosaccharides)} monosaccharides (aldoses + ketoses, C2-C7)")

    # Step 2: Generate polyols
    print("\n[2/8] Generating polyols...")
    polyols = generate_polyols(monosaccharides)
    print(f"  -> {len(polyols)} polyols (with degeneracy detection)")

    # Step 3: Generate phosphosugars
    print("\n[3/8] Generating phosphosugars...")
    phosphosugars = generate_phosphosugars(monosaccharides)
    print(f"  -> {len(phosphosugars)} phosphosugars")

    # Step 4: Combine all compounds
    print("\n[4/8] Combining compound sets...")
    all_compounds = monosaccharides + polyols + phosphosugars
    print(f"  -> {len(all_compounds)} total compounds")

    # Step 5: Validate
    print("\n[5/8] Validating compound set...")
    completeness_warnings = check_completeness(all_compounds)
    if completeness_warnings:
        for w in completeness_warnings:
            print(f"  [WARNING] {w}")
    else:
        print("  -> Completeness check passed")

    duplicates = check_duplicates(all_compounds)
    if duplicates:
        for d in duplicates:
            print(f"  [WARNING] Duplicate: {d['original']['id']} / {d['duplicate']['id']}")
    else:
        print("  -> Duplicate check passed")

    # Step 6: Generate reactions
    print("\n[6/8] Generating reactions...")
    epimerizations = generate_epimerizations(all_compounds)
    isomerizations = generate_isomerizations(all_compounds)
    reductions = generate_reductions(all_compounds, polyols)
    phosphorylations = generate_phosphorylations(phosphosugars)
    dephosphorylations = generate_dephosphorylations(phosphosugars)
    mutases = generate_mutases(phosphosugars)
    phospho_epimerizations = generate_phospho_epimerizations(phosphosugars)
    phospho_isomerizations = generate_phospho_isomerizations(phosphosugars)
    all_reactions = (
        epimerizations + isomerizations + reductions +
        phosphorylations + dephosphorylations + mutases +
        phospho_epimerizations + phospho_isomerizations
    )
    print(f"  -> {len(epimerizations)} epimerizations")
    print(f"  -> {len(isomerizations)} isomerizations")
    print(f"  -> {len(reductions)} reductions")
    print(f"  -> {len(phosphorylations)} phosphorylations")
    print(f"  -> {len(dephosphorylations)} dephosphorylations")
    print(f"  -> {len(mutases)} mutases")
    print(f"  -> {len(phospho_epimerizations)} phospho-epimerizations")
    print(f"  -> {len(phospho_isomerizations)} phospho-isomerizations")
    print(f"  -> {len(all_reactions)} total reactions")

    # Step 7: Mass balance check (ABORT on failure)
    print("\n[7/8] Checking mass balance...")
    compound_map = {c["id"]: c for c in all_compounds}
    mass_errors = check_mass_balance(all_reactions, compound_map)
    if mass_errors:
        for e in mass_errors:
            print(f"  [ERROR] {e}", file=sys.stderr)
        _abort(f"Mass balance check failed with {len(mass_errors)} error(s)")
    print("  -> Mass balance check passed")

    # Step 8: Verify reaction ID uniqueness (ABORT on duplicates)
    print("\n[8/8] Verifying reaction ID uniqueness...")
    reaction_ids = [r["id"] for r in all_reactions]
    seen_ids: set[str] = set()
    duplicate_ids = []
    for rid in reaction_ids:
        if rid in seen_ids:
            duplicate_ids.append(rid)
        seen_ids.add(rid)
    if duplicate_ids:
        for did in duplicate_ids:
            print(f"  [ERROR] Duplicate reaction ID: {did}", file=sys.stderr)
        _abort(f"Reaction ID uniqueness check failed: {len(duplicate_ids)} duplicate(s)")
    print("  -> Reaction ID uniqueness check passed")
```

- [ ] **Step 3: Update metadata counts**

In `pipeline/run_pipeline.py`, replace the metadata counts dict (lines 267-274) with:

```python
        "counts": {
            "monosaccharides": len(monosaccharides),
            "polyols": len(polyols),
            "phosphosugars": len(phosphosugars),
            "total_compounds": len(all_compounds),
            "epimerizations": len(epimerizations),
            "isomerizations": len(isomerizations),
            "reductions": len(reductions),
            "phosphorylations": len(phosphorylations),
            "dephosphorylations": len(dephosphorylations),
            "mutases": len(mutases),
            "phospho_epimerizations": len(phospho_epimerizations),
            "phospho_isomerizations": len(phospho_isomerizations),
            "total_reactions": len(all_reactions),
        },
```

- [ ] **Step 4: Update docstring**

Replace the docstring for `run_pipeline` (lines 29-47) to reflect the new step count:

```python
    """Execute the full SUGAR v2 pipeline.

    Args:
        skip_import: If True, skip Ring 2 database import steps.
        refresh: Set of source names to force-refresh cached data for
            (e.g. {"chebi", "kegg", "rhea", "brenda"}). None means use cache.

    Steps:
    1. Enumerate monosaccharides (94 compounds, C2-C7)
    2. Generate polyols with degeneracy detection
    3. Generate phosphosugars (systematic + curated)
    4. Combine all compounds
    5. Validate: completeness and duplicates
    6. Generate reactions (epi, iso, red, phos, dephos, mutase, phospho-epi, phospho-iso)
    7. Mass balance check (ABORT on failure)
    8. Verify reaction ID uniqueness (ABORT on duplicates)

    Returns a summary dict with counts and file paths.
    """
```

- [ ] **Step 5: Run ALL tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/ -v`
Expected: all tests pass

- [ ] **Step 6: Run the pipeline (skip import)**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pipeline.run_pipeline --skip-import`
Expected output includes:
- `[3/8] Generating phosphosugars...` → 144 phosphosugars
- `[6/8] Generating reactions...` → phosphorylation/dephosphorylation/mutase/epi/iso counts
- Mass balance check passed
- Reaction ID uniqueness check passed
- Total compounds ~279, total reactions ~1,936+

- [ ] **Step 7: Commit**

```bash
git add pipeline/run_pipeline.py
git commit -m "feat: wire phosphosugars into pipeline orchestrator (Ring 3 step 1)"
```

---

### Task 10: Final Integration Verification

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pytest pipeline/tests/ -v --tb=short`
Expected: all tests pass

- [ ] **Step 2: Run pipeline and inspect output**

Run: `cd /Users/rivir/Documents/GitHub/sugar && python -m pipeline.run_pipeline --skip-import`
Verify:
- Pipeline completes without errors
- compounds.json has ~279 entries
- reactions.json has ~1,936+ entries
- pipeline_metadata.json shows phosphosugar counts

- [ ] **Step 3: Spot-check output data**

Run: `python -c "import json; data=json.load(open('pipeline/output/compounds.json')); phospho=[c for c in data if c['type']=='phosphate']; print(f'{len(phospho)} phosphosugars'); g6p=[c for c in phospho if c['id']=='D-GLC-6P']; print(json.dumps(g6p[0], indent=2) if g6p else 'G6P not found')"`
Expected: 144 phosphosugars, D-GLC-6P has correct fields

- [ ] **Step 4: Final commit for any remaining adjustments**

If adjustments were needed:
```bash
git add -A
git commit -m "fix: final adjustments for phosphosugar integration"
```
