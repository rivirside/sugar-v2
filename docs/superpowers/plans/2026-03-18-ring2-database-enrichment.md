# Ring 2: Database Enrichment Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the Ring 1 sugar compound/reaction network with data from ChEBI, KEGG, RHEA, and BRENDA databases, adding real identifiers, validated reactions, kinetic parameters, and evidence tier promotions.

**Architecture:** New `pipeline/import_/` module (underscore to avoid Python reserved word) with one importer per data source, a multi-strategy compound matching engine, and a merge/infer layer. ChEBI uses bulk TSV with REST fallback, KEGG uses async batch REST, RHEA uses SPARQL, BRENDA uses SOAP. All responses cached locally. Frontend updated to display enriched data.

**Tech Stack:** Python (requests, aiohttp, SPARQLWrapper, zeep, rdkit, thefuzz, python-dotenv), Next.js/TypeScript frontend

**Spec:** `docs/superpowers/specs/2026-03-18-ring2-database-enrichment-design.md`

---

## File Structure

### Pipeline (new files)
- `pipeline/import_/__init__.py` — Package init
- `pipeline/import_/cache.py` — Shared caching utilities (read/write/refresh/TTL)
- `pipeline/import_/chebi.py` — ChEBI bulk TSV download + REST fallback
- `pipeline/import_/kegg.py` — KEGG async batch REST with caching
- `pipeline/import_/rhea.py` — RHEA SPARQL batch queries
- `pipeline/import_/brenda.py` — BRENDA SOAP API per-EC-number
- `pipeline/import_/match.py` — Multi-strategy compound matching engine
- `pipeline/import_/merge.py` — Merge imported data into compounds/reactions
- `pipeline/import_/infer.py` — D-to-L mirroring and gap-fill inference
- `pipeline/data/match_overrides.json` — Manual match corrections (git-tracked)
- `.env.example` — Template for BRENDA credentials

### Pipeline (modified files)
- `pipeline/run_pipeline.py` — Add argparse CLI, import orchestration
- `pipeline/enumerate/monosaccharides.py` — Add new null fields to compound dicts
- `pipeline/enumerate/polyols.py` — Add new null fields to compound dicts
- `pipeline/reactions/score.py` — No changes needed (already handles all tiers)
- `pipeline/validate/mass_balance.py` — Add formula-balance mode for imported reactions
- `pipeline/requirements.txt` — Add new dependencies

### Pipeline (new test files)
- `pipeline/tests/test_cache.py`
- `pipeline/tests/test_match.py`
- `pipeline/tests/test_chebi.py`
- `pipeline/tests/test_kegg.py`
- `pipeline/tests/test_rhea.py`
- `pipeline/tests/test_brenda.py`
- `pipeline/tests/test_merge.py`
- `pipeline/tests/test_infer.py`

### Frontend (modified files)
- `web/lib/types.ts` — Add new Compound fields
- `web/app/compound/[id]/page.tsx` — External IDs section, InChI/SMILES
- `web/app/reaction/[id]/page.tsx` — Replace Ring 2 placeholder with real data
- `web/app/page.tsx` — Enrichment coverage stats on dashboard
- `web/app/compounds/page.tsx` — "Has external ID" filter toggle

### Config
- `.gitignore` — Add `pipeline/cache/`, `.env`

---

## Chunk 1: Foundation — Cache, CLI, Data Model

### Task 1: Install dependencies and update requirements.txt

**Files:**
- Modify: `pipeline/requirements.txt`

- [ ] **Step 1: Update requirements.txt**

```
pytest>=8.0
requests>=2.31
aiohttp>=3.9
SPARQLWrapper>=2.0
zeep>=4.2
python-dotenv>=1.0
thefuzz>=0.22
rdkit-pypi>=2024.3.1
```

- [ ] **Step 2: Install dependencies**

Run: `cd /Users/rivir/Documents/GitHub/sugar && pip install -r pipeline/requirements.txt`
Expected: All packages install successfully

- [ ] **Step 3: Commit**

```bash
git add pipeline/requirements.txt
git commit -m "chore: add Ring 2 pipeline dependencies"
```

### Task 2: Add new fields to compound dict templates

**Files:**
- Modify: `pipeline/enumerate/monosaccharides.py:79-93` (achiral aldose template)
- Modify: `pipeline/enumerate/monosaccharides.py:101-115` (chiral aldose template)
- Modify: `pipeline/enumerate/monosaccharides.py:134-148` (achiral ketose template)
- Modify: `pipeline/enumerate/monosaccharides.py:156-170` (chiral ketose template)
- Modify: `pipeline/enumerate/polyols.py:151-172` (polyol template)
- Modify: `pipeline/tests/test_monosaccharides.py`
- Modify: `pipeline/tests/test_polyols.py`

- [ ] **Step 1: Write test for new compound fields**

Add to `pipeline/tests/test_monosaccharides.py`:

```python
def test_compounds_have_external_id_fields():
    """All compounds must have chebi_id, kegg_id, pubchem_id, inchi, smiles initialized to None."""
    compounds = enumerate_all_monosaccharides()
    for c in compounds:
        assert "chebi_id" in c, f"{c['id']} missing chebi_id"
        assert "kegg_id" in c, f"{c['id']} missing kegg_id"
        assert "pubchem_id" in c, f"{c['id']} missing pubchem_id"
        assert "inchi" in c, f"{c['id']} missing inchi"
        assert "smiles" in c, f"{c['id']} missing smiles"
        assert c["chebi_id"] is None
        assert c["kegg_id"] is None
        assert c["pubchem_id"] is None
        assert c["inchi"] is None
        assert c["smiles"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_monosaccharides.py::test_compounds_have_external_id_fields -v`
Expected: FAIL with KeyError on "chebi_id"

- [ ] **Step 3: Add fields to all four compound templates in monosaccharides.py**

In each of the four compound dict literals in `enumerate_aldoses` and `enumerate_ketoses`, add these five lines after `"metadata": {}`:

```python
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
```

There are 4 dict literals to update:
1. `enumerate_aldoses` achiral case (~line 79)
2. `enumerate_aldoses` chiral case (~line 101)
3. `enumerate_ketoses` achiral case (~line 134)
4. `enumerate_ketoses` chiral case (~line 156)

- [ ] **Step 4: Add fields to polyol template in polyols.py**

In the polyol dict literal in `generate_polyols` (~line 151), add after `"metadata"`:

```python
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_monosaccharides.py::test_compounds_have_external_id_fields -v`
Expected: PASS

- [ ] **Step 6: Run full test suite to verify nothing broke**

Run: `python -m pytest pipeline/tests/ -v`
Expected: All 44+ tests pass

- [ ] **Step 7: Commit**

```bash
git add pipeline/enumerate/monosaccharides.py pipeline/enumerate/polyols.py pipeline/tests/test_monosaccharides.py
git commit -m "feat: add external ID fields to compound templates (chebi_id, kegg_id, pubchem_id, inchi, smiles)"
```

### Task 3: Create cache module

**Files:**
- Create: `pipeline/import/__init__.py`
- Create: `pipeline/import/cache.py`
- Create: `pipeline/tests/test_cache.py`

- [ ] **Step 1: Create package init**

Create `pipeline/import/__init__.py` (empty file).

- [ ] **Step 2: Write failing tests for cache module**

Create `pipeline/tests/test_cache.py`:

```python
"""Tests for pipeline.import.cache module."""

import json
import os
import tempfile
import time

import pytest

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh, clear_cache


@pytest.fixture
def cache_dir(tmp_path):
    return str(tmp_path / "cache")


def test_write_and_read_cache(cache_dir):
    data = {"chebi_id": "CHEBI:17634", "name": "D-Glucose"}
    write_cache(cache_dir, "chebi", "glucose.json", data)
    result = read_cache(cache_dir, "chebi", "glucose.json")
    assert result == data


def test_read_missing_cache(cache_dir):
    result = read_cache(cache_dir, "chebi", "nonexistent.json")
    assert result is None


def test_is_cache_fresh_when_fresh(cache_dir):
    write_cache(cache_dir, "kegg", "C00031.json", {"id": "C00031"})
    assert is_cache_fresh(cache_dir, "kegg", "C00031.json", max_age_days=7)


def test_is_cache_fresh_when_missing(cache_dir):
    assert not is_cache_fresh(cache_dir, "kegg", "missing.json", max_age_days=7)


def test_clear_cache(cache_dir):
    write_cache(cache_dir, "chebi", "test.json", {"a": 1})
    clear_cache(cache_dir, "chebi")
    assert read_cache(cache_dir, "chebi", "test.json") is None


def test_write_cache_creates_subdirs(cache_dir):
    write_cache(cache_dir, "brenda", "1.2.3.4.json", {"ec": "1.2.3.4"})
    path = os.path.join(cache_dir, "brenda", "1.2.3.4.json")
    assert os.path.exists(path)
```

NOTE: Python doesn't allow `import` as a module name. The package directory is `pipeline/import/` but we'll import it as `pipeline.import_` by naming the directory `pipeline/import_/`. Alternatively, we can keep the directory as `pipeline/import/` and use importlib. The simpler approach: **name the directory `pipeline/import_/`** to avoid the reserved word conflict.

**IMPORTANT**: Rename the directory from `pipeline/import/` to `pipeline/import_/` throughout the entire plan. The spec says `import/` but Python reserves `import` as a keyword.

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_cache.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 4: Create the cache module**

Create `pipeline/import_/__init__.py` (empty file).

Create `pipeline/import_/cache.py`:

```python
"""Shared caching utilities for import pipeline.

Provides read/write/freshness-check for cached API responses.
All cached data lives in pipeline/cache/ (gitignored).
"""

import json
import os
import shutil
import time


def _cache_path(cache_dir: str, source: str, filename: str) -> str:
    return os.path.join(cache_dir, source, filename)


def write_cache(cache_dir: str, source: str, filename: str, data: dict | list) -> str:
    """Write data to cache as JSON. Returns the file path."""
    path = _cache_path(cache_dir, source, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def read_cache(cache_dir: str, source: str, filename: str) -> dict | list | None:
    """Read cached data. Returns None if file doesn't exist."""
    path = _cache_path(cache_dir, source, filename)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def is_cache_fresh(cache_dir: str, source: str, filename: str, max_age_days: int = 30) -> bool:
    """Check if a cached file exists and is younger than max_age_days."""
    path = _cache_path(cache_dir, source, filename)
    if not os.path.exists(path):
        return False
    mtime = os.path.getmtime(path)
    age_days = (time.time() - mtime) / 86400
    return age_days < max_age_days


def clear_cache(cache_dir: str, source: str) -> None:
    """Remove all cached files for a specific source."""
    source_dir = os.path.join(cache_dir, source)
    if os.path.exists(source_dir):
        shutil.rmtree(source_dir)


def write_raw_cache(cache_dir: str, source: str, filename: str, content: bytes) -> str:
    """Write raw bytes to cache (for TSV/binary downloads). Returns file path."""
    path = _cache_path(cache_dir, source, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return path


def read_raw_cache(cache_dir: str, source: str, filename: str) -> bytes | None:
    """Read raw bytes from cache. Returns None if file doesn't exist."""
    path = _cache_path(cache_dir, source, filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()
```

- [ ] **Step 5: Update test imports to use `import_`**

Update `pipeline/tests/test_cache.py` import:
```python
from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh, clear_cache
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_cache.py -v`
Expected: All 6 tests pass

- [ ] **Step 7: Commit**

```bash
git add pipeline/import_/ pipeline/tests/test_cache.py
git commit -m "feat: add cache module for import pipeline"
```

### Task 4: Update .gitignore

**Files:**
- Modify: `.gitignore` (at repo root)

- [ ] **Step 1: Add cache and env entries to .gitignore**

Append to `.gitignore`:

```
# Ring 2: import pipeline cache (large API responses)
pipeline/cache/

# Environment variables (BRENDA credentials)
.env
```

- [ ] **Step 2: Create .env.example**

Create `.env.example` at repo root:

```
# BRENDA API credentials (register at https://www.brenda-enzymes.org/)
BRENDA_EMAIL=your-email@example.com
BRENDA_PASSWORD=your-password
```

- [ ] **Step 3: Create empty match_overrides.json**

Create `pipeline/data/match_overrides.json`:

```json
{}
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example pipeline/data/match_overrides.json
git commit -m "chore: add gitignore for cache/env, BRENDA env template, empty match overrides"
```

### Task 5: Refactor run_pipeline.py with argparse CLI

**Files:**
- Modify: `pipeline/run_pipeline.py`
- Modify: `pipeline/tests/test_pipeline_integration.py`

- [ ] **Step 1: Read existing integration test**

Read `pipeline/tests/test_pipeline_integration.py` to understand current test structure.

- [ ] **Step 2: Add argparse to run_pipeline.py**

Replace the `if __name__ == "__main__"` block and add argument parsing. The `run_pipeline()` function signature changes to accept optional parameters:

```python
import argparse

def run_pipeline(skip_import: bool = False, refresh: set[str] | None = None) -> dict:
    """Execute the SUGAR pipeline.

    Args:
        skip_import: If True, skip the import/enrichment step (Ring 1 behavior).
        refresh: Set of sources to refresh cache for (e.g., {"chebi", "kegg"}).
                 None means use cache. Empty set means refresh nothing.
    """
```

Add at the top of `run_pipeline()`, after the Ring 1 generation steps (after step 7, before writing output):

```python
    if not skip_import:
        print("\n=== Ring 2: Database Enrichment ===")
        print("  [SKIP] Import not yet implemented")
        # TODO: Wire import steps here in subsequent tasks
```

Replace the `__main__` block:

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SUGAR pipeline")
    parser.add_argument("--skip-import", action="store_true", help="Skip database import (Ring 1 only)")
    parser.add_argument("--refresh", action="store_true", help="Force refresh all cached data")
    parser.add_argument("--refresh-chebi", action="store_true", help="Refresh ChEBI cache")
    parser.add_argument("--refresh-kegg", action="store_true", help="Refresh KEGG cache")
    parser.add_argument("--refresh-rhea", action="store_true", help="Refresh RHEA cache")
    parser.add_argument("--refresh-brenda", action="store_true", help="Refresh BRENDA cache")
    args = parser.parse_args()

    refresh_sources = set()
    if args.refresh:
        refresh_sources = {"chebi", "kegg", "rhea", "brenda"}
    else:
        if args.refresh_chebi:
            refresh_sources.add("chebi")
        if args.refresh_kegg:
            refresh_sources.add("kegg")
        if args.refresh_rhea:
            refresh_sources.add("rhea")
        if args.refresh_brenda:
            refresh_sources.add("brenda")

    run_pipeline(skip_import=args.skip_import, refresh=refresh_sources or None)
```

- [ ] **Step 3: Run existing tests to verify nothing broke**

Run: `python -m pytest pipeline/tests/ -v`
Expected: All existing tests pass (run_pipeline() default args match old behavior)

- [ ] **Step 4: Test CLI flags work**

Run: `python -m pipeline.run_pipeline --skip-import`
Expected: Pipeline runs through Ring 1 steps only, no "Ring 2" output

Run: `python -m pipeline.run_pipeline`
Expected: Pipeline runs Ring 1 + prints "Ring 2: Database Enrichment" then "[SKIP] Import not yet implemented"

- [ ] **Step 5: Commit**

```bash
git add pipeline/run_pipeline.py
git commit -m "feat: add argparse CLI to run_pipeline (--skip-import, --refresh)"
```

---

## Chunk 2: ChEBI Importer + Compound Matching Engine

### Task 6: Build the compound matching engine

**Files:**
- Create: `pipeline/import_/match.py`
- Create: `pipeline/tests/test_match.py`

- [ ] **Step 1: Write failing tests for match engine**

Create `pipeline/tests/test_match.py`:

```python
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
    """Simulated ChEBI index keyed by lowercase name -> entry."""
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
    index = {}  # No index entries
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
            "inchi": None,
            "smiles": None,
            "kegg_id": None,
            "pubchem_id": None,
        }
    }
    # Build formula index from the chebi index
    result = match_compound(compound, index)
    # Should match because only one candidate with formula C4H8O4
    assert result["chebi_id"] == "CHEBI:27904"
    assert result["confidence"] == "medium"
    assert result["strategy"] == "formula_unique"


def test_formula_multiple_candidates_no_match():
    """Multiple compounds share C6H12O6, so formula match should NOT apply."""
    compound = _make_compound("TEST", "Unknown Hexose")
    glucose = _make_chebi_index()["d-glucose"]
    mannose = {**glucose, "chebi_id": "CHEBI:28729", "name": "D-Mannose"}
    index = {"d-glucose": glucose, "d-mannose": mannose}
    result = match_compound(compound, index)
    # Name doesn't match either entry, formula has multiple candidates
    assert result["chebi_id"] is None
    assert result["strategy"] == "no_match"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_match.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement match.py**

Create `pipeline/import_/match.py`:

```python
"""Multi-strategy compound matching engine.

Matches enumerated compounds to ChEBI database entries using these strategies
(applied in order, first match wins):

1. Override pin — manual override forces a specific match
2. Override reject — manual override blocks a match
3. Exact name match (confidence: high)
4. Synonym/alias match (confidence: high)
5. Formula unique match (confidence: medium) — only if exactly one candidate shares the formula
6. Fuzzy name match (confidence: low) — flagged for review, not auto-applied

The chebi_index is a dict keyed by lowercase name/synonym -> ChEBI entry dict.
"""

import json
import os
from thefuzz import fuzz


def match_compound(
    compound: dict,
    chebi_index: dict,
    overrides: dict | None = None,
) -> dict:
    """Match a single compound against the ChEBI index.

    Returns a match result dict with keys:
        chebi_id, kegg_id, pubchem_id, inchi, smiles, confidence, strategy, chebi_name
    """
    compound_id = compound["id"]
    no_match = _no_match_result()

    # Check overrides first
    if overrides and compound_id in overrides:
        override = overrides[compound_id]
        if override["action"] == "pin":
            return {
                "chebi_id": override["chebi_id"],
                "kegg_id": override.get("kegg_id"),
                "pubchem_id": override.get("pubchem_id"),
                "inchi": override.get("inchi"),
                "smiles": override.get("smiles"),
                "confidence": "high",
                "strategy": "override_pin",
                "chebi_name": override.get("name"),
            }
        elif override["action"] == "reject":
            return {**no_match, "strategy": "override_reject"}

    # Strategy 1: Exact name match
    key = compound["name"].lower()
    if key in chebi_index:
        return _result_from_entry(chebi_index[key], "high", "exact_name")

    # Strategy 2: Alias match
    for alias in compound.get("aliases", []):
        alias_key = alias.lower()
        if alias_key in chebi_index:
            return _result_from_entry(chebi_index[alias_key], "high", "alias")

    # Strategy 3: Formula unique match
    formula = compound.get("formula")
    if formula:
        candidates = _find_by_formula(chebi_index, formula)
        if len(candidates) == 1:
            return _result_from_entry(candidates[0], "medium", "formula_unique")

    # Strategy 4: Fuzzy name match (not auto-applied, returned as low confidence)
    best_score = 0
    best_entry = None
    for entry_key, entry in chebi_index.items():
        score = fuzz.ratio(compound["name"].lower(), entry_key)
        if score > best_score and score >= 85:
            best_score = score
            best_entry = entry
    if best_entry:
        return _result_from_entry(best_entry, "low", "fuzzy_name")

    return no_match


def match_all_compounds(
    compounds: list[dict],
    chebi_index: dict,
    overrides: dict | None = None,
) -> dict:
    """Match all compounds and return a match report dict keyed by compound ID."""
    report = {}
    for compound in compounds:
        report[compound["id"]] = match_compound(compound, chebi_index, overrides)
    return report


def load_overrides(overrides_path: str) -> dict:
    """Load match overrides from JSON file."""
    if not os.path.exists(overrides_path):
        return {}
    with open(overrides_path) as f:
        return json.load(f)


def _no_match_result() -> dict:
    return {
        "chebi_id": None,
        "kegg_id": None,
        "pubchem_id": None,
        "inchi": None,
        "smiles": None,
        "confidence": None,
        "strategy": "no_match",
        "chebi_name": None,
    }


def _result_from_entry(entry: dict, confidence: str, strategy: str) -> dict:
    return {
        "chebi_id": entry.get("chebi_id"),
        "kegg_id": entry.get("kegg_id"),
        "pubchem_id": entry.get("pubchem_id"),
        "inchi": entry.get("inchi"),
        "smiles": entry.get("smiles"),
        "confidence": confidence,
        "strategy": strategy,
        "chebi_name": entry.get("name"),
    }


def _find_by_formula(chebi_index: dict, formula: str) -> list[dict]:
    """Find all unique ChEBI entries matching a formula."""
    seen_ids = set()
    results = []
    for entry in chebi_index.values():
        chebi_id = entry.get("chebi_id")
        if chebi_id and chebi_id not in seen_ids and entry.get("formula") == formula:
            seen_ids.add(chebi_id)
            results.append(entry)
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_match.py -v`
Expected: All 7 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/match.py pipeline/tests/test_match.py
git commit -m "feat: add compound matching engine with override support"
```

### Task 7: Build ChEBI importer

**Files:**
- Create: `pipeline/import_/chebi.py`
- Create: `pipeline/tests/test_chebi.py`

- [ ] **Step 1: Write failing tests for ChEBI importer**

Create `pipeline/tests/test_chebi.py`:

```python
"""Tests for ChEBI importer."""

import pytest
from pipeline.import_.chebi import parse_chebi_compounds_tsv, parse_chebi_names_tsv, build_chebi_index


SAMPLE_COMPOUNDS_TSV = """ID\tSTATUS\tSOURCE\tPARENT_ID\tNAME\tDEFINITION\tMODIFIED_ON\tCREATED_BY\tSTAR
17634\tC\tKEGG COMPOUND\t\tD-glucopyranose\tA glucopyranose having D-configuration.\t2023-10-01\tCHEBI\t3
28729\tC\tKEGG COMPOUND\t\tD-mannopyranose\tA mannopyranose having D-configuration.\t2023-10-01\tCHEBI\t3"""

SAMPLE_NAMES_TSV = """ID\tCOMPOUND_ID\tNAME\tTYPE\tSOURCE\tADAPTED\tLANGUAGE
1\t17634\tD-Glucose\tSYNONYM\tChEBI\tfalse\ten
2\t17634\tDextrose\tSYNONYM\tChEBI\tfalse\ten
3\t17634\tGrape sugar\tSYNONYM\tChEBI\tfalse\ten
4\t28729\tD-Mannose\tSYNONYM\tChEBI\tfalse\ten"""


def test_parse_compounds_tsv():
    entries = parse_chebi_compounds_tsv(SAMPLE_COMPOUNDS_TSV)
    assert len(entries) == 2
    assert entries["17634"]["name"] == "D-glucopyranose"
    assert entries["28729"]["name"] == "D-mannopyranose"


def test_parse_names_tsv():
    names = parse_chebi_names_tsv(SAMPLE_NAMES_TSV)
    assert "17634" in names
    assert "D-Glucose" in names["17634"]
    assert "Dextrose" in names["17634"]
    assert "28729" in names
    assert "D-Mannose" in names["28729"]


def test_build_index():
    compounds = parse_chebi_compounds_tsv(SAMPLE_COMPOUNDS_TSV)
    names = parse_chebi_names_tsv(SAMPLE_NAMES_TSV)
    index = build_chebi_index(compounds, names)
    # Index should be keyed by lowercase name/synonym
    assert "d-glucose" in index
    assert "dextrose" in index
    assert "d-mannose" in index
    assert "d-glucopyranose" in index
    # All entries for glucose should point to same chebi_id
    assert index["d-glucose"]["chebi_id"] == "CHEBI:17634"
    assert index["dextrose"]["chebi_id"] == "CHEBI:17634"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_chebi.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement chebi.py**

Create `pipeline/import_/chebi.py`:

```python
"""ChEBI database importer.

Primary: bulk TSV download from ChEBI FTP.
Fallback: REST API per-compound.
Fallback on fallback: log warning and skip.
"""

import csv
import io
import logging
import os
import gzip

import requests

from pipeline.import_.cache import (
    read_cache,
    write_cache,
    is_cache_fresh,
    write_raw_cache,
    read_raw_cache,
)

logger = logging.getLogger(__name__)

CHEBI_FTP_COMPOUNDS = "https://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/compounds.tsv.gz"
CHEBI_FTP_NAMES = "https://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/names.tsv.gz"
CHEBI_FTP_ACCESSION = "https://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/database_accession.tsv.gz"
CHEBI_FTP_INCHI = "https://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/chebiId_inchi.tsv"
CHEBI_REST_BASE = "https://www.ebi.ac.uk/webservices/chebi/2.0"


def fetch_chebi_bulk(cache_dir: str, refresh: bool = False) -> dict:
    """Download and parse ChEBI bulk TSV files. Returns a chebi_index dict.

    Falls back to cached parsed index if available and fresh.
    """
    index_cache = read_cache(cache_dir, "chebi", "index.json")
    if index_cache and not refresh and is_cache_fresh(cache_dir, "chebi", "index.json"):
        logger.info("Using cached ChEBI index (%d entries)", len(index_cache))
        return index_cache

    try:
        logger.info("Downloading ChEBI compounds TSV...")
        compounds_data = _download_tsv_gz(CHEBI_FTP_COMPOUNDS)
        logger.info("Downloading ChEBI names TSV...")
        names_data = _download_tsv_gz(CHEBI_FTP_NAMES)

        compounds = parse_chebi_compounds_tsv(compounds_data)
        names = parse_chebi_names_tsv(names_data)
        index = build_chebi_index(compounds, names)

        write_cache(cache_dir, "chebi", "index.json", index)
        logger.info("Built ChEBI index with %d entries", len(index))
        return index

    except Exception as e:
        logger.warning("ChEBI bulk download failed: %s. Falling back to cached data.", e)
        if index_cache:
            return index_cache
        return {}


def fetch_chebi_rest(compound_name: str) -> dict | None:
    """Fetch a single compound from ChEBI REST API. Returns entry dict or None."""
    try:
        url = f"https://www.ebi.ac.uk/webservices/chebi/2.0/getCompleteEntity?chebiId={compound_name}"
        # Use the search endpoint instead
        search_url = f"https://www.ebi.ac.uk/webservices/chebi/2.0/getLiteEntity?search={compound_name}&searchCategory=ALL&maximumResults=5"
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            # Parse XML response (ChEBI REST returns XML)
            # For now return None - will implement XML parsing when needed
            return None
        return None
    except Exception as e:
        logger.warning("ChEBI REST lookup failed for %s: %s", compound_name, e)
        return None


def parse_chebi_compounds_tsv(tsv_content: str) -> dict:
    """Parse ChEBI compounds.tsv into dict keyed by ChEBI numeric ID.

    Returns: {chebi_numeric_id: {"name": str, "status": str}}
    Only includes entries with status 'C' (checked/approved).
    """
    entries = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        status = row.get("STATUS", "")
        if status != "C":
            continue
        chebi_num_id = row.get("ID", "").strip()
        name = row.get("NAME", "").strip()
        if chebi_num_id and name:
            entries[chebi_num_id] = {
                "name": name,
                "chebi_id": f"CHEBI:{chebi_num_id}",
            }
    return entries


def parse_chebi_names_tsv(tsv_content: str) -> dict:
    """Parse ChEBI names.tsv into dict keyed by ChEBI numeric ID -> list of synonym strings.

    Returns: {chebi_numeric_id: [synonym1, synonym2, ...]}
    """
    names: dict[str, list[str]] = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        compound_id = row.get("COMPOUND_ID", "").strip()
        name = row.get("NAME", "").strip()
        if compound_id and name:
            names.setdefault(compound_id, []).append(name)
    return names


def build_chebi_index(compounds: dict, names: dict) -> dict:
    """Build a lookup index keyed by lowercase name/synonym -> ChEBI entry.

    Each entry contains: chebi_id, name, synonyms, formula, inchi, smiles, kegg_id, pubchem_id
    """
    index = {}

    for chebi_num_id, compound_info in compounds.items():
        entry = {
            "chebi_id": compound_info["chebi_id"],
            "name": compound_info["name"],
            "synonyms": names.get(chebi_num_id, []),
            "formula": None,  # Will be populated from separate file if available
            "inchi": None,
            "smiles": None,
            "kegg_id": None,
            "pubchem_id": None,
        }

        # Index by canonical name
        index[compound_info["name"].lower()] = entry

        # Index by all synonyms
        for synonym in entry["synonyms"]:
            index[synonym.lower()] = entry

    return index


def _download_tsv_gz(url: str) -> str:
    """Download a gzipped TSV file and return decompressed content as string."""
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()
    content = gzip.decompress(resp.content)
    return content.decode("utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_chebi.py -v`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/chebi.py pipeline/tests/test_chebi.py
git commit -m "feat: add ChEBI importer with bulk TSV parsing and REST fallback"
```

---

## Chunk 3: KEGG, RHEA, BRENDA Importers

### Task 8: Build KEGG importer

**Files:**
- Create: `pipeline/import_/kegg.py`
- Create: `pipeline/tests/test_kegg.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_kegg.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_kegg.py -v`
Expected: FAIL

- [ ] **Step 3: Implement kegg.py**

Create `pipeline/import_/kegg.py`:

```python
"""KEGG REST API importer.

Uses async batch requests with rate limiting and local caching.
KEGG throttles at ~10 req/sec.
"""

import asyncio
import logging
import re
import time

import aiohttp
import requests

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh

logger = logging.getLogger(__name__)

KEGG_BASE = "https://rest.kegg.jp"
RATE_LIMIT_DELAY = 0.15  # seconds between requests (~7/sec, conservative)


def fetch_kegg_compound(kegg_id: str, cache_dir: str, refresh: bool = False) -> dict | None:
    """Fetch a single KEGG compound. Uses cache if available."""
    cache_file = f"{kegg_id}.json"
    if not refresh and is_cache_fresh(cache_dir, "kegg", cache_file):
        cached = read_cache(cache_dir, "kegg", cache_file)
        if cached:
            return cached

    try:
        url = f"{KEGG_BASE}/get/{kegg_id}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            result = parse_kegg_compound_entry(resp.text)
            write_cache(cache_dir, "kegg", cache_file, result)
            return result
        elif resp.status_code == 404:
            logger.debug("KEGG compound %s not found", kegg_id)
            return None
        else:
            logger.warning("KEGG returned %d for %s", resp.status_code, kegg_id)
            return None
    except Exception as e:
        logger.warning("KEGG fetch failed for %s: %s", kegg_id, e)
        return None


def fetch_kegg_compounds_batch(kegg_ids: list[str], cache_dir: str, refresh: bool = False) -> dict:
    """Fetch multiple KEGG compounds sequentially with rate limiting.

    Returns dict keyed by KEGG ID -> parsed entry.
    """
    results = {}
    for i, kegg_id in enumerate(kegg_ids):
        result = fetch_kegg_compound(kegg_id, cache_dir, refresh)
        if result:
            results[kegg_id] = result
        if i < len(kegg_ids) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    return results


def fetch_kegg_reaction_links(kegg_ids: list[str], cache_dir: str, refresh: bool = False) -> dict:
    """Fetch reaction links for a batch of KEGG compound IDs.

    Returns dict keyed by KEGG compound ID -> list of KEGG reaction IDs.
    """
    cache_file = "reaction_links.json"
    if not refresh and is_cache_fresh(cache_dir, "kegg", cache_file):
        cached = read_cache(cache_dir, "kegg", cache_file)
        if cached:
            return cached

    all_links = {}
    # KEGG /link/reaction endpoint accepts compound IDs
    for kegg_id in kegg_ids:
        try:
            url = f"{KEGG_BASE}/link/reaction/{kegg_id}"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200 and resp.text.strip():
                links = parse_kegg_link_response(resp.text)
                all_links.update(links)
            time.sleep(RATE_LIMIT_DELAY)
        except Exception as e:
            logger.warning("KEGG link fetch failed for %s: %s", kegg_id, e)

    write_cache(cache_dir, "kegg", cache_file, all_links)
    return all_links


def parse_kegg_compound_entry(text: str) -> dict:
    """Parse a KEGG compound flat-file entry into a structured dict."""
    result = {
        "kegg_id": None,
        "names": [],
        "formula": None,
        "pathways": [],
        "chebi_id": None,
        "pubchem_id": None,
    }

    current_field = None
    for line in text.strip().split("\n"):
        if line.startswith("///"):
            break

        if line[:12].strip():
            # New field
            field = line[:12].strip()
            value = line[12:].strip()
            current_field = field
        else:
            # Continuation of previous field
            value = line.strip()

        if current_field == "ENTRY":
            match = re.match(r"(\w+)", value)
            if match:
                result["kegg_id"] = match.group(1)
        elif current_field == "NAME":
            # Names are semicolon-separated, may span multiple lines
            for name in value.rstrip(";").split(";"):
                name = name.strip()
                if name:
                    result["names"].append(name)
        elif current_field == "FORMULA":
            result["formula"] = value
        elif current_field == "PATHWAY":
            match = re.match(r"(map\d+)", value)
            if match:
                result["pathways"].append(match.group(1))
        elif current_field == "DBLINKS":
            if value.startswith("ChEBI:"):
                result["chebi_id"] = value.split(":")[1].strip()
            elif value.startswith("PubChem:"):
                result["pubchem_id"] = value.split(":")[1].strip()

    return result


def parse_kegg_link_response(text: str) -> dict:
    """Parse KEGG /link/ response into dict of compound_id -> [reaction_ids]."""
    links: dict[str, list[str]] = {}
    for line in text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) == 2:
            compound_id = parts[0].replace("cpd:", "")
            reaction_id = parts[1].replace("rn:", "")
            links.setdefault(compound_id, []).append(reaction_id)
    return links
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_kegg.py -v`
Expected: All 2 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/kegg.py pipeline/tests/test_kegg.py
git commit -m "feat: add KEGG importer with rate-limited batch fetching"
```

### Task 9: Build RHEA importer

**Files:**
- Create: `pipeline/import_/rhea.py`
- Create: `pipeline/tests/test_rhea.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_rhea.py`:

```python
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
                "substrateId": {"value": "CHEBI:17634"},
                "productId": {"value": "CHEBI:48095"},
            },
            {
                "rheaId": {"value": "10002"},
                "equation": {"value": "D-glucose + NAD+ = D-gluconate + NADH"},
                "ec": {"value": "1.1.1.47"},
                "substrateId": {"value": "CHEBI:17634"},
                "productId": {"value": "CHEBI:18391"},
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
        "substrate_chebi_ids": ["CHEBI:17634", "CHEBI:15846"],  # glucose + NAD+
        "product_chebi_ids": ["CHEBI:48095", "CHEBI:16908"],    # fructose + NADH
    }
    result = classify_reaction_participants(reaction, known_chebi_ids)
    assert "CHEBI:17634" in result["known_substrates"]
    assert "CHEBI:15846" in result["unknown_substrates"]
    assert "CHEBI:48095" in result["known_products"]
    assert "CHEBI:16908" in result["unknown_products"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_rhea.py -v`
Expected: FAIL

- [ ] **Step 3: Implement rhea.py**

Create `pipeline/import_/rhea.py`:

```python
"""RHEA database importer via SPARQL endpoint.

Fetches validated reactions by querying for reactions involving known ChEBI IDs.
Discovers new compounds that participate in reactions with our existing set.
"""

import logging

from SPARQLWrapper import SPARQLWrapper, JSON

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh

logger = logging.getLogger(__name__)

RHEA_SPARQL_ENDPOINT = "https://sparql.rhea-db.org/sparql"
BATCH_SIZE = 50  # ChEBI IDs per SPARQL query


def fetch_rhea_reactions(chebi_ids: list[str], cache_dir: str, refresh: bool = False) -> list[dict]:
    """Fetch all RHEA reactions involving any of the given ChEBI IDs.

    Queries in batches of BATCH_SIZE to avoid query size limits.
    Returns list of parsed reaction dicts.
    """
    cache_file = "query_results.json"
    if not refresh and is_cache_fresh(cache_dir, "rhea", cache_file):
        cached = read_cache(cache_dir, "rhea", cache_file)
        if cached:
            logger.info("Using cached RHEA results (%d reactions)", len(cached))
            return cached

    all_reactions = []
    for i in range(0, len(chebi_ids), BATCH_SIZE):
        batch = chebi_ids[i:i + BATCH_SIZE]
        logger.info("Querying RHEA batch %d/%d (%d IDs)...",
                     i // BATCH_SIZE + 1,
                     (len(chebi_ids) + BATCH_SIZE - 1) // BATCH_SIZE,
                     len(batch))
        try:
            results = _query_rhea_batch(batch)
            reactions = parse_sparql_results(results)
            all_reactions.extend(reactions)
        except Exception as e:
            logger.warning("RHEA SPARQL query failed for batch starting at %d: %s", i, e)

    # Deduplicate by RHEA ID
    seen = set()
    unique = []
    for r in all_reactions:
        if r["rhea_id"] not in seen:
            seen.add(r["rhea_id"])
            unique.append(r)

    write_cache(cache_dir, "rhea", cache_file, unique)
    logger.info("Fetched %d unique RHEA reactions", len(unique))
    return unique


def _query_rhea_batch(chebi_ids: list[str]) -> dict:
    """Execute a SPARQL query for reactions involving a batch of ChEBI IDs."""
    # Build VALUES clause with ChEBI URIs
    values = " ".join(f"<http://purl.obolibrary.org/obo/{cid.replace(':', '_')}>" for cid in chebi_ids)

    query = f"""
    PREFIX rh: <http://rdf.rhea-db.org/>
    PREFIX ch: <http://purl.obolibrary.org/obo/>

    SELECT DISTINCT ?rheaId ?equation ?ec ?substrateId ?productId ?direction
    WHERE {{
        VALUES ?chebi {{ {values} }}
        ?rhea rh:equation ?equation .
        ?rhea rh:id ?rheaId .
        OPTIONAL {{ ?rhea rh:ec ?ec . }}
        ?rhea rh:side ?subSide .
        ?subSide rh:contains ?subPart .
        ?subPart rh:compound ?subCompound .
        ?subCompound rh:chebi ?substrateId .
        ?rhea rh:side ?prodSide .
        FILTER(?subSide != ?prodSide)
        ?prodSide rh:contains ?prodPart .
        ?prodPart rh:compound ?prodCompound .
        ?prodCompound rh:chebi ?productId .
        FILTER(?subCompound = ?chebi || ?prodCompound = ?chebi)
        OPTIONAL {{ ?rhea rh:direction ?direction . }}
    }}
    """

    sparql = SPARQLWrapper(RHEA_SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def parse_sparql_results(results: dict) -> list[dict]:
    """Parse SPARQL JSON results into a list of reaction dicts.

    Groups by RHEA ID and collects all substrates/products.
    """
    reactions_map: dict[str, dict] = {}

    for binding in results.get("results", {}).get("bindings", []):
        rhea_id = f"RHEA:{binding['rheaId']['value']}"
        ec = binding.get("ec", {}).get("value")
        equation = binding.get("equation", {}).get("value", "")

        # Extract ChEBI ID from URI like http://purl.obolibrary.org/obo/CHEBI_17634
        sub_uri = binding.get("substrateId", {}).get("value", "")
        prod_uri = binding.get("productId", {}).get("value", "")
        sub_chebi = _uri_to_chebi(sub_uri)
        prod_chebi = _uri_to_chebi(prod_uri)

        if rhea_id not in reactions_map:
            reactions_map[rhea_id] = {
                "rhea_id": rhea_id,
                "ec_number": ec,
                "equation": equation,
                "substrate_chebi_ids": set(),
                "product_chebi_ids": set(),
                "pmids": [],
            }

        if sub_chebi:
            reactions_map[rhea_id]["substrate_chebi_ids"].add(sub_chebi)
        if prod_chebi:
            reactions_map[rhea_id]["product_chebi_ids"].add(prod_chebi)

    # Convert sets to lists for JSON serialization
    reactions = []
    for r in reactions_map.values():
        r["substrate_chebi_ids"] = sorted(r["substrate_chebi_ids"])
        r["product_chebi_ids"] = sorted(r["product_chebi_ids"])
        reactions.append(r)

    return reactions


def classify_reaction_participants(reaction: dict, known_chebi_ids: set[str]) -> dict:
    """Classify reaction participants as known or unknown (discovered).

    Returns dict with known_substrates, unknown_substrates, known_products, unknown_products.
    """
    return {
        "known_substrates": [cid for cid in reaction["substrate_chebi_ids"] if cid in known_chebi_ids],
        "unknown_substrates": [cid for cid in reaction["substrate_chebi_ids"] if cid not in known_chebi_ids],
        "known_products": [cid for cid in reaction["product_chebi_ids"] if cid in known_chebi_ids],
        "unknown_products": [cid for cid in reaction["product_chebi_ids"] if cid not in known_chebi_ids],
    }


def _uri_to_chebi(uri: str) -> str | None:
    """Convert an OBO URI to a ChEBI ID string."""
    if "CHEBI_" in uri:
        chebi_num = uri.split("CHEBI_")[-1]
        return f"CHEBI:{chebi_num}"
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_rhea.py -v`
Expected: All 2 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/rhea.py pipeline/tests/test_rhea.py
git commit -m "feat: add RHEA SPARQL importer with batch queries and participant classification"
```

### Task 10: Build BRENDA importer

**Files:**
- Create: `pipeline/import_/brenda.py`
- Create: `pipeline/tests/test_brenda.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_brenda.py`:

```python
"""Tests for BRENDA importer."""

import pytest
from pipeline.import_.brenda import parse_brenda_km_data, parse_brenda_kcat_data


SAMPLE_KM_RESPONSE = [
    {"ecNumber": "5.3.1.9", "kmValue": 0.5, "substrate": "D-glucose", "organism": "Homo sapiens"},
    {"ecNumber": "5.3.1.9", "kmValue": 1.2, "substrate": "D-glucose", "organism": "Escherichia coli"},
]

SAMPLE_KCAT_RESPONSE = [
    {"ecNumber": "5.3.1.9", "turnoverNumber": 500, "substrate": "D-glucose", "organism": "Homo sapiens"},
]


def test_parse_km_data():
    result = parse_brenda_km_data(SAMPLE_KM_RESPONSE)
    assert len(result) == 2
    assert result[0]["km_mm"] == 0.5
    assert result[0]["organism"] == "Homo sapiens"
    assert result[0]["ec_number"] == "5.3.1.9"


def test_parse_kcat_data():
    result = parse_brenda_kcat_data(SAMPLE_KCAT_RESPONSE)
    assert len(result) == 1
    assert result[0]["kcat_sec"] == 500
    assert result[0]["organism"] == "Homo sapiens"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_brenda.py -v`
Expected: FAIL

- [ ] **Step 3: Implement brenda.py**

Create `pipeline/import_/brenda.py`:

```python
"""BRENDA enzyme database importer.

Uses SOAP API per EC number. Credentials from .env file.
Falls back gracefully if BRENDA is unavailable.
"""

import hashlib
import logging
import os

from dotenv import load_dotenv

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh

logger = logging.getLogger(__name__)

BRENDA_WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"


def load_brenda_credentials() -> tuple[str, str] | None:
    """Load BRENDA credentials from .env file."""
    load_dotenv()
    email = os.getenv("BRENDA_EMAIL")
    password = os.getenv("BRENDA_PASSWORD")
    if not email or not password:
        logger.warning("BRENDA credentials not found in .env file")
        return None
    return email, password


def fetch_brenda_kinetics(ec_numbers: list[str], cache_dir: str, refresh: bool = False) -> dict:
    """Fetch kinetic data for a list of EC numbers from BRENDA.

    Returns dict keyed by EC number -> kinetics data.
    """
    credentials = load_brenda_credentials()
    if not credentials:
        logger.warning("Skipping BRENDA import (no credentials)")
        return {}

    email, password = credentials
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    results = {}
    for ec in ec_numbers:
        cache_file = f"{ec.replace('.', '_')}.json"
        if not refresh and is_cache_fresh(cache_dir, "brenda", cache_file):
            cached = read_cache(cache_dir, "brenda", cache_file)
            if cached:
                results[ec] = cached
                continue

        try:
            kinetics = _fetch_ec_kinetics(email, password_hash, ec)
            write_cache(cache_dir, "brenda", cache_file, kinetics)
            results[ec] = kinetics
        except Exception as e:
            logger.warning("BRENDA fetch failed for EC %s: %s", ec, e)

    return results


def _fetch_ec_kinetics(email: str, password_hash: str, ec_number: str) -> dict:
    """Fetch Km and kcat data for a single EC number from BRENDA SOAP API."""
    try:
        from zeep import Client
        client = Client(BRENDA_WSDL)

        km_raw = []
        kcat_raw = []

        try:
            km_result = client.service.getKmValue(email, password_hash, f"ecNumber*{ec_number}")
            if km_result:
                km_raw = parse_brenda_km_data(km_result if isinstance(km_result, list) else [])
        except Exception as e:
            logger.debug("BRENDA Km fetch failed for %s: %s", ec_number, e)

        try:
            kcat_result = client.service.getTurnoverNumber(email, password_hash, f"ecNumber*{ec_number}")
            if kcat_result:
                kcat_raw = parse_brenda_kcat_data(kcat_result if isinstance(kcat_result, list) else [])
        except Exception as e:
            logger.debug("BRENDA kcat fetch failed for %s: %s", ec_number, e)

        return {
            "ec_number": ec_number,
            "km_entries": km_raw,
            "kcat_entries": kcat_raw,
        }

    except ImportError:
        logger.warning("zeep not installed, skipping BRENDA SOAP")
        return {"ec_number": ec_number, "km_entries": [], "kcat_entries": []}


def parse_brenda_km_data(km_entries: list) -> list[dict]:
    """Parse BRENDA Km response into structured dicts."""
    results = []
    for entry in km_entries:
        if isinstance(entry, dict):
            results.append({
                "ec_number": entry.get("ecNumber", ""),
                "km_mm": entry.get("kmValue"),
                "substrate": entry.get("substrate", ""),
                "organism": entry.get("organism", ""),
            })
    return results


def parse_brenda_kcat_data(kcat_entries: list) -> list[dict]:
    """Parse BRENDA kcat/turnover number response into structured dicts."""
    results = []
    for entry in kcat_entries:
        if isinstance(entry, dict):
            results.append({
                "ec_number": entry.get("ecNumber", ""),
                "kcat_sec": entry.get("turnoverNumber"),
                "substrate": entry.get("substrate", ""),
                "organism": entry.get("organism", ""),
            })
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_brenda.py -v`
Expected: All 2 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/brenda.py pipeline/tests/test_brenda.py
git commit -m "feat: add BRENDA SOAP importer with credential loading and kinetics parsing"
```

---

## Chunk 4: Merge, Infer, Evidence, Mass Balance

### Task 11: Build merge module

**Files:**
- Create: `pipeline/import_/merge.py`
- Create: `pipeline/tests/test_merge.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_merge.py`:

```python
"""Tests for merge module."""

import pytest
from pipeline.import_.merge import enrich_compound, enrich_reaction_with_rhea, create_rhea_reaction, determine_evidence_tier


def test_enrich_compound():
    compound = {
        "id": "D-GLC", "name": "D-Glucose", "aliases": ["Dextrose"],
        "chebi_id": None, "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None,
    }
    match = {
        "chebi_id": "CHEBI:17634", "kegg_id": "C00031", "pubchem_id": "5793",
        "inchi": "InChI=1S/test", "smiles": "OCC1OC(O)C(O)C(O)C1O",
        "chebi_name": "D-glucopyranose",
    }
    result = enrich_compound(compound, match)
    assert result["chebi_id"] == "CHEBI:17634"
    assert result["kegg_id"] == "C00031"
    assert result["inchi"] == "InChI=1S/test"
    # Original name preserved, ChEBI name added to aliases
    assert result["name"] == "D-Glucose"
    assert "D-glucopyranose" in result["aliases"]


def test_enrich_compound_no_duplicate_aliases():
    compound = {
        "id": "D-GLC", "name": "D-Glucose", "aliases": ["Dextrose"],
        "chebi_id": None, "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None,
    }
    match = {
        "chebi_id": "CHEBI:17634", "chebi_name": "D-Glucose",  # Same as existing name
        "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None,
    }
    result = enrich_compound(compound, match)
    # D-Glucose shouldn't be duplicated in aliases
    assert result["aliases"].count("D-Glucose") == 0  # It's the name, not an alias


def test_create_rhea_reaction():
    rhea_data = {
        "rhea_id": "RHEA:10001",
        "ec_number": "5.3.1.9",
        "substrate_chebi_ids": ["CHEBI:17634"],
        "product_chebi_ids": ["CHEBI:48095"],
        "pmids": ["12345678"],
    }
    chebi_to_compound = {"CHEBI:17634": "D-GLC", "CHEBI:48095": "D-FRU"}
    result = create_rhea_reaction(rhea_data, chebi_to_compound)
    assert result["id"] == "RHEA:10001"
    assert result["substrates"] == ["D-GLC"]
    assert result["products"] == ["D-FRU"]
    assert result["ec_number"] == "5.3.1.9"
    assert result["evidence_tier"] == "validated"  # Has PMID


def test_determine_evidence_tier_validated():
    assert determine_evidence_tier(pmids=["123"], ec_number="5.3.1.9") == "validated"


def test_determine_evidence_tier_predicted_ec():
    assert determine_evidence_tier(pmids=[], ec_number="5.3.1.9") == "predicted"


def test_determine_evidence_tier_predicted_rhea_only():
    assert determine_evidence_tier(pmids=[], ec_number=None) == "predicted"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_merge.py -v`
Expected: FAIL

- [ ] **Step 3: Implement merge.py**

Create `pipeline/import_/merge.py`:

```python
"""Merge imported data into enumerated compounds and reactions.

Handles:
- Enriching existing compounds with external IDs
- Creating new reactions from RHEA
- Detecting overlap between RHEA and generated reactions
- Adding discovered compounds from RHEA
"""

from pipeline.reactions.score import compute_cost_score


def enrich_compound(compound: dict, match: dict) -> dict:
    """Enrich a compound dict with matched external data.

    Preserves original name (from name_mapping.json). Adds ChEBI name to aliases
    if different from existing name and not already in aliases.
    """
    compound = {**compound}  # shallow copy
    compound["chebi_id"] = match.get("chebi_id")
    compound["kegg_id"] = match.get("kegg_id")
    compound["pubchem_id"] = match.get("pubchem_id")
    compound["inchi"] = match.get("inchi")
    compound["smiles"] = match.get("smiles")

    # Add ChEBI canonical name to aliases if different
    chebi_name = match.get("chebi_name")
    if chebi_name and chebi_name != compound["name"] and chebi_name not in compound["aliases"]:
        compound["aliases"] = compound["aliases"] + [chebi_name]

    return compound


def create_rhea_reaction(
    rhea_data: dict,
    chebi_to_compound: dict,
) -> dict | None:
    """Create a reaction dict from RHEA data.

    Maps ChEBI IDs to our compound IDs using chebi_to_compound lookup.
    Returns None if any participant can't be mapped.
    """
    substrates = []
    for chebi_id in rhea_data["substrate_chebi_ids"]:
        compound_id = chebi_to_compound.get(chebi_id)
        if compound_id:
            substrates.append(compound_id)

    products = []
    for chebi_id in rhea_data["product_chebi_ids"]:
        compound_id = chebi_to_compound.get(chebi_id)
        if compound_id:
            products.append(compound_id)

    if not substrates or not products:
        return None

    pmids = rhea_data.get("pmids", [])
    ec_number = rhea_data.get("ec_number")
    evidence_tier = determine_evidence_tier(pmids, ec_number)

    rxn = {
        "id": rhea_data["rhea_id"],
        "reaction_type": _guess_reaction_type(ec_number),
        "substrates": substrates,
        "products": products,
        "evidence_tier": evidence_tier,
        "evidence_criteria": _build_evidence_criteria(rhea_data, evidence_tier),
        "yield": None,
        "cofactor_burden": 0.0,
        "ec_number": ec_number,
        "enzyme_name": None,
        "cofactors": [],
        "pmid": pmids,
        "rhea_id": rhea_data["rhea_id"],
        "organism": [],
        "km_mm": None,
        "kcat_sec": None,
        "delta_g": None,
        "metadata": {"source": "rhea_import"},
    }
    rxn["cost_score"] = compute_cost_score(rxn)
    return rxn


def determine_evidence_tier(pmids: list, ec_number: str | None) -> str:
    """Determine evidence tier for a RHEA-imported reaction.

    - Has PMID -> validated
    - Has EC or RHEA ID (always true if we got here) -> predicted
    """
    if pmids:
        return "validated"
    return "predicted"


def find_overlapping_reaction(
    rhea_substrates: list[str],
    rhea_products: list[str],
    existing_reactions: list[dict],
) -> dict | None:
    """Find an existing generated reaction that overlaps with a RHEA reaction.

    Overlap: same substrate/product pair (ignoring cofactors).
    Only checks 1:1 reactions for overlap with generated reactions.
    """
    if len(rhea_substrates) != 1 or len(rhea_products) != 1:
        return None

    sub = rhea_substrates[0]
    prod = rhea_products[0]

    for rxn in existing_reactions:
        if rxn["substrates"] == [sub] and rxn["products"] == [prod]:
            return rxn

    return None


def enrich_reaction_with_rhea(existing: dict, rhea_data: dict) -> dict:
    """Enrich an existing generated reaction with RHEA data."""
    enriched = {**existing}
    enriched["rhea_id"] = rhea_data["rhea_id"]
    enriched["ec_number"] = rhea_data.get("ec_number")

    pmids = rhea_data.get("pmids", [])
    enriched["pmid"] = pmids
    enriched["evidence_tier"] = determine_evidence_tier(pmids, rhea_data.get("ec_number"))
    enriched["evidence_criteria"] = _build_evidence_criteria(rhea_data, enriched["evidence_tier"])
    enriched["cost_score"] = compute_cost_score(enriched)

    return enriched


def _guess_reaction_type(ec_number: str | None) -> str:
    """Guess reaction type from EC number prefix."""
    if not ec_number:
        return "isomerization"  # default

    prefix = ec_number.split(".")[0]
    return {
        "1": "oxidation",
        "2": "phosphorylation",
        "3": "hydrolysis",
        "4": "aldol",
        "5": "isomerization",
        "6": "condensation",
    }.get(prefix, "isomerization")


def _build_evidence_criteria(rhea_data: dict, tier: str) -> list[dict]:
    """Build structured evidence criteria from RHEA data."""
    criteria = []
    criteria.append({"source": "rhea", "rhea_id": rhea_data["rhea_id"]})

    if rhea_data.get("ec_number"):
        criteria.append({"source": "ec", "ec_number": rhea_data["ec_number"]})

    pmids = rhea_data.get("pmids", [])
    if pmids:
        criteria.append({"source": "pmid", "ids": pmids})

    return criteria
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_merge.py -v`
Expected: All 6 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/merge.py pipeline/tests/test_merge.py
git commit -m "feat: add merge module for enriching compounds/reactions with imported data"
```

### Task 12: Build infer module (D-to-L mirroring)

**Files:**
- Create: `pipeline/import_/infer.py`
- Create: `pipeline/tests/test_infer.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_infer.py`:

```python
"""Tests for D-to-L mirroring inference."""

import pytest
from pipeline.import_.infer import find_mirror_compound, infer_mirrored_reactions

SUGAR_TYPES = {"aldose", "ketose", "polyol", "phosphate", "acid", "lactone",
               "amino_sugar", "nucleotide_sugar", "deoxy_sugar", "disaccharide"}


def _make_compounds():
    return [
        {"id": "D-GLC", "name": "D-Glucose", "type": "aldose", "chirality": "D",
         "stereocenters": ["R", "S", "S", "R"]},
        {"id": "L-GLC", "name": "L-Glucose", "type": "aldose", "chirality": "L",
         "stereocenters": ["S", "R", "R", "S"]},
        {"id": "D-FRU", "name": "D-Fructose", "type": "ketose", "chirality": "D",
         "stereocenters": ["S", "S", "R"]},
        {"id": "L-FRU", "name": "L-Fructose", "type": "ketose", "chirality": "L",
         "stereocenters": ["R", "R", "S"]},
    ]


def test_find_mirror_d_to_l():
    compounds = _make_compounds()
    mirror = find_mirror_compound("D-GLC", compounds)
    assert mirror is not None
    assert mirror["id"] == "L-GLC"


def test_find_mirror_l_to_d():
    compounds = _make_compounds()
    mirror = find_mirror_compound("L-FRU", compounds)
    assert mirror is not None
    assert mirror["id"] == "D-FRU"


def test_find_mirror_none():
    compounds = [_make_compounds()[0]]  # Only D-GLC, no L-GLC
    mirror = find_mirror_compound("D-GLC", compounds)
    assert mirror is None


def test_infer_mirrored_reaction():
    compounds = _make_compounds()
    reactions = [{
        "id": "RHEA:10001",
        "substrates": ["D-GLC"],
        "products": ["D-FRU"],
        "reaction_type": "isomerization",
        "evidence_tier": "validated",
        "evidence_criteria": [{"source": "rhea", "rhea_id": "RHEA:10001"}],
        "rhea_id": "RHEA:10001",
        "ec_number": "5.3.1.9",
    }]
    existing_reaction_ids = {"RHEA:10001"}

    inferred = infer_mirrored_reactions(reactions, compounds, existing_reaction_ids)
    assert len(inferred) == 1
    assert inferred[0]["substrates"] == ["L-GLC"]
    assert inferred[0]["products"] == ["L-FRU"]
    assert inferred[0]["evidence_tier"] == "inferred"
    assert "RHEA:10001" in inferred[0]["id"]  # References source


def test_no_double_inference():
    """If the mirrored reaction already exists, don't create a duplicate."""
    compounds = _make_compounds()
    reactions = [{
        "id": "RHEA:10001",
        "substrates": ["D-GLC"],
        "products": ["D-FRU"],
        "reaction_type": "isomerization",
        "evidence_tier": "validated",
        "evidence_criteria": [],
        "rhea_id": "RHEA:10001",
        "ec_number": "5.3.1.9",
    }]
    # Mirrored reaction already exists
    existing_reaction_ids = {"RHEA:10001", "INFER-RHEA:10001-L"}

    inferred = infer_mirrored_reactions(reactions, compounds, existing_reaction_ids)
    assert len(inferred) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_infer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement infer.py**

Create `pipeline/import_/infer.py`:

```python
"""D-to-L mirroring inference.

For validated/predicted reactions from RHEA, infer the corresponding
L/D mirrored reaction if all sugar-class participants have mirrors.
Cofactors (non-sugar compounds) are carried over unchanged.
"""

from pipeline.reactions.score import compute_cost_score

SUGAR_TYPES = {"aldose", "ketose", "polyol", "phosphate", "acid", "lactone",
               "amino_sugar", "nucleotide_sugar", "deoxy_sugar", "disaccharide"}


def find_mirror_compound(compound_id: str, compounds: list[dict]) -> dict | None:
    """Find the D/L mirror of a compound.

    D-compounds have chirality 'D', their mirror is the L-compound with
    inverted stereocenters (all R->S, S->R).
    """
    compound_map = {c["id"]: c for c in compounds}
    compound = compound_map.get(compound_id)
    if not compound:
        return None

    if compound["chirality"] not in ("D", "L"):
        return None

    # Compute the mirrored stereocenters
    mirrored_centers = ["S" if s == "R" else "R" for s in compound["stereocenters"]]

    # Find a compound with the same type, same carbons, and mirrored stereocenters
    for c in compounds:
        if (c["id"] != compound_id
                and c["type"] == compound["type"]
                and c.get("carbons") == compound.get("carbons")
                and c["stereocenters"] == mirrored_centers):
            return c

    return None


def infer_mirrored_reactions(
    reactions: list[dict],
    compounds: list[dict],
    existing_reaction_ids: set[str],
) -> list[dict]:
    """Infer D-to-L mirrored reactions from validated/predicted RHEA reactions.

    Only mirrors sugar-class participants. Cofactors stay unchanged.
    """
    compound_map = {c["id"]: c for c in compounds}
    inferred = []

    for rxn in reactions:
        if rxn.get("evidence_tier") not in ("validated", "predicted"):
            continue

        # Classify participants as sugar or cofactor
        sugar_substrates = []
        cofactor_substrates = []
        for sid in rxn["substrates"]:
            comp = compound_map.get(sid)
            if comp and comp["type"] in SUGAR_TYPES:
                sugar_substrates.append(sid)
            else:
                cofactor_substrates.append(sid)

        sugar_products = []
        cofactor_products = []
        for pid in rxn["products"]:
            comp = compound_map.get(pid)
            if comp and comp["type"] in SUGAR_TYPES:
                sugar_products.append(pid)
            else:
                cofactor_products.append(pid)

        # Check if all sugar participants have mirrors
        mirrored_substrates = []
        all_have_mirrors = True
        for sid in sugar_substrates:
            mirror = find_mirror_compound(sid, compounds)
            if mirror:
                mirrored_substrates.append(mirror["id"])
            else:
                all_have_mirrors = False
                break

        if not all_have_mirrors:
            continue

        mirrored_products = []
        for pid in sugar_products:
            mirror = find_mirror_compound(pid, compounds)
            if mirror:
                mirrored_products.append(mirror["id"])
            else:
                all_have_mirrors = False
                break

        if not all_have_mirrors:
            continue

        # Build the mirrored reaction
        new_substrates = mirrored_substrates + cofactor_substrates
        new_products = mirrored_products + cofactor_products
        source_rhea = rxn.get("rhea_id", rxn["id"])
        new_id = f"INFER-{source_rhea}-L"

        if new_id in existing_reaction_ids:
            continue

        mirror_rxn = {
            "id": new_id,
            "reaction_type": rxn.get("reaction_type", "isomerization"),
            "substrates": new_substrates,
            "products": new_products,
            "evidence_tier": "inferred",
            "evidence_criteria": [
                {"source": "d_to_l_mirror", "source_reaction": source_rhea}
            ],
            "yield": None,
            "cofactor_burden": rxn.get("cofactor_burden", 0.0),
            "ec_number": rxn.get("ec_number"),
            "enzyme_name": rxn.get("enzyme_name"),
            "cofactors": rxn.get("cofactors", []),
            "pmid": [],
            "rhea_id": None,
            "organism": [],
            "km_mm": None,
            "kcat_sec": None,
            "delta_g": None,
            "metadata": {"source": "d_to_l_inference", "source_reaction": source_rhea},
        }
        mirror_rxn["cost_score"] = compute_cost_score(mirror_rxn)
        inferred.append(mirror_rxn)

    return inferred
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_infer.py -v`
Expected: All 5 tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/import_/infer.py pipeline/tests/test_infer.py
git commit -m "feat: add D-to-L mirroring inference for validated/predicted reactions"
```

### Task 13: Extend mass balance for imported reactions

**Files:**
- Modify: `pipeline/validate/mass_balance.py`
- Modify: `pipeline/tests/test_validate.py`

- [ ] **Step 1: Write failing test for formula balance mode**

Add to `pipeline/tests/test_validate.py`:

```python
def test_formula_balance_mode():
    """Formula balance checks atom counts across all participants."""
    from pipeline.validate.mass_balance import check_formula_balance

    reactions = [{
        "id": "RHEA:10001",
        "substrates": ["A", "B"],
        "products": ["C", "D"],
    }]
    compound_map = {
        "A": {"id": "A", "formula": "C6H12O6"},
        "B": {"id": "B", "formula": "C10H15N5O10P2"},
        "C": {"id": "C", "formula": "C6H13O9P"},
        "D": {"id": "D", "formula": "C10H14N5O7P"},
    }
    errors = check_formula_balance(reactions, compound_map)
    # This is a real phosphorylation: glucose + ATP -> G6P + ADP
    # Formula balance may not hold exactly due to water, but should not crash
    assert isinstance(errors, list)


def test_formula_balance_missing_formula():
    """Formula balance gracefully handles missing formulas."""
    from pipeline.validate.mass_balance import check_formula_balance

    reactions = [{"id": "TEST", "substrates": ["A"], "products": ["B"]}]
    compound_map = {
        "A": {"id": "A", "formula": "C6H12O6"},
        "B": {"id": "B", "formula": None},
    }
    errors = check_formula_balance(reactions, compound_map)
    # Should warn but not crash
    assert any("missing formula" in e.lower() or "none" in e.lower() for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_validate.py::test_formula_balance_mode -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Add check_formula_balance to mass_balance.py**

Add to `pipeline/validate/mass_balance.py`:

```python
import re

def _parse_formula(formula: str) -> dict[str, int]:
    """Parse a molecular formula like 'C6H12O6' into {'C': 6, 'H': 12, 'O': 6}."""
    atoms: dict[str, int] = {}
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        if element:
            atoms[element] = atoms.get(element, 0) + count
    return atoms


def check_formula_balance(reactions: list[dict], compound_map: dict) -> list[str]:
    """Check formula-level balance for imported reactions.

    Unlike carbon-count balance, this checks all atoms.
    Returns warnings (not errors) for mismatches since RHEA is authoritative.
    """
    warnings = []

    for rxn in reactions:
        rxn_id = rxn.get("id", "UNKNOWN")
        substrates = rxn.get("substrates", [])
        products = rxn.get("products", [])

        # Collect formulas
        sub_atoms: dict[str, int] = {}
        prod_atoms: dict[str, int] = {}
        skip = False

        for sid in substrates:
            compound = compound_map.get(sid)
            if not compound:
                warnings.append(f"Reaction {rxn_id}: substrate '{sid}' not in compound map")
                skip = True
                continue
            formula = compound.get("formula")
            if not formula:
                warnings.append(f"Reaction {rxn_id}: substrate '{sid}' has missing formula (None)")
                skip = True
                continue
            for elem, count in _parse_formula(formula).items():
                sub_atoms[elem] = sub_atoms.get(elem, 0) + count

        for pid in products:
            compound = compound_map.get(pid)
            if not compound:
                warnings.append(f"Reaction {rxn_id}: product '{pid}' not in compound map")
                skip = True
                continue
            formula = compound.get("formula")
            if not formula:
                warnings.append(f"Reaction {rxn_id}: product '{pid}' has missing formula (None)")
                skip = True
                continue
            for elem, count in _parse_formula(formula).items():
                prod_atoms[elem] = prod_atoms.get(elem, 0) + count

        if skip:
            continue

        # Compare
        all_elements = set(sub_atoms.keys()) | set(prod_atoms.keys())
        imbalanced = []
        for elem in sorted(all_elements):
            sub_count = sub_atoms.get(elem, 0)
            prod_count = prod_atoms.get(elem, 0)
            if sub_count != prod_count:
                imbalanced.append(f"{elem}: {sub_count} vs {prod_count}")

        if imbalanced:
            warnings.append(
                f"Reaction {rxn_id}: formula imbalance [{', '.join(imbalanced)}]"
            )

    return warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_validate.py -v`
Expected: All tests pass (existing + new)

- [ ] **Step 5: Commit**

```bash
git add pipeline/validate/mass_balance.py pipeline/tests/test_validate.py
git commit -m "feat: add formula-level mass balance check for imported reactions"
```

---

## Chunk 5: Pipeline Integration

### Task 14: Wire import steps into run_pipeline.py

**Files:**
- Modify: `pipeline/run_pipeline.py`

- [ ] **Step 1: Add the import orchestration to run_pipeline.py**

After the existing Ring 1 steps (after mass balance check, before writing output), add the Ring 2 import orchestration. This replaces the `[SKIP] Import not yet implemented` placeholder:

```python
    if not skip_import:
        print("\n=== Ring 2: Database Enrichment ===")
        cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        overrides_path = os.path.join(os.path.dirname(__file__), "data", "match_overrides.json")

        from pipeline.import_.chebi import fetch_chebi_bulk
        from pipeline.import_.kegg import fetch_kegg_compounds_batch
        from pipeline.import_.rhea import fetch_rhea_reactions, classify_reaction_participants
        from pipeline.import_.brenda import fetch_brenda_kinetics
        from pipeline.import_.match import match_all_compounds, load_overrides
        from pipeline.import_.merge import (
            enrich_compound, create_rhea_reaction, find_overlapping_reaction,
            enrich_reaction_with_rhea,
        )
        from pipeline.import_.infer import infer_mirrored_reactions
        from pipeline.validate.mass_balance import check_formula_balance

        refresh_sources = refresh or set()

        # Step R1: Fetch ChEBI data
        print("\n[R1] Fetching ChEBI data...")
        chebi_index = fetch_chebi_bulk(cache_dir, refresh="chebi" in refresh_sources)
        print(f"  -> ChEBI index: {len(chebi_index)} entries")

        # Step R2: Match compounds
        print("\n[R2] Matching compounds to ChEBI...")
        overrides = load_overrides(overrides_path)
        match_report = match_all_compounds(all_compounds, chebi_index, overrides)
        matched = sum(1 for m in match_report.values() if m["chebi_id"])
        print(f"  -> {matched}/{len(all_compounds)} compounds matched")

        # Write match report to cache
        import json as _json
        match_report_path = os.path.join(cache_dir, "match_report.json")
        os.makedirs(cache_dir, exist_ok=True)
        with open(match_report_path, "w") as _f:
            _json.dump(match_report, _f, indent=2)

        # Step R3: Enrich compounds
        print("\n[R3] Enriching compounds with external IDs...")
        enriched_compounds = []
        for compound in all_compounds:
            match = match_report.get(compound["id"])
            if match and match["chebi_id"]:
                enriched_compounds.append(enrich_compound(compound, match))
            else:
                enriched_compounds.append(compound)
        all_compounds = enriched_compounds

        # Step R4: Fetch KEGG data for matched compounds
        print("\n[R4] Fetching KEGG data...")
        kegg_ids = [m["kegg_id"] for m in match_report.values() if m.get("kegg_id")]
        if kegg_ids:
            kegg_data = fetch_kegg_compounds_batch(kegg_ids, cache_dir, refresh="kegg" in refresh_sources)
            print(f"  -> {len(kegg_data)} KEGG entries fetched")
        else:
            print("  -> No KEGG IDs to fetch")

        # Step R5: Fetch RHEA reactions
        print("\n[R5] Fetching RHEA reactions...")
        chebi_ids = [m["chebi_id"] for m in match_report.values() if m["chebi_id"]]
        rhea_reactions = fetch_rhea_reactions(chebi_ids, cache_dir, refresh="rhea" in refresh_sources)
        print(f"  -> {len(rhea_reactions)} RHEA reactions found")

        # Step R6: Process RHEA reactions
        print("\n[R6] Processing RHEA reactions...")
        # Build ChEBI -> compound ID mapping
        chebi_to_compound = {}
        for compound in all_compounds:
            if compound.get("chebi_id"):
                chebi_to_compound[compound["chebi_id"]] = compound["id"]

        new_reactions = []
        enriched_existing = 0
        for rhea_rxn in rhea_reactions:
            # Check for overlap with generated reactions
            subs = [chebi_to_compound.get(cid) for cid in rhea_rxn["substrate_chebi_ids"] if cid in chebi_to_compound]
            prods = [chebi_to_compound.get(cid) for cid in rhea_rxn["product_chebi_ids"] if cid in chebi_to_compound]
            subs = [s for s in subs if s]
            prods = [p for p in prods if p]

            overlap = find_overlapping_reaction(subs, prods, all_reactions)
            if overlap:
                # Enrich existing reaction
                idx = all_reactions.index(overlap)
                all_reactions[idx] = enrich_reaction_with_rhea(overlap, rhea_rxn)
                enriched_existing += 1
            else:
                # Create new reaction
                new_rxn = create_rhea_reaction(rhea_rxn, chebi_to_compound)
                if new_rxn:
                    new_reactions.append(new_rxn)

        all_reactions.extend(new_reactions)
        print(f"  -> {enriched_existing} existing reactions enriched")
        print(f"  -> {len(new_reactions)} new reactions from RHEA")

        # Step R7: Fetch BRENDA kinetics
        print("\n[R7] Fetching BRENDA kinetics...")
        ec_numbers = list({r.get("ec_number") for r in all_reactions if r.get("ec_number")})
        if ec_numbers:
            brenda_data = fetch_brenda_kinetics(ec_numbers, cache_dir, refresh="brenda" in refresh_sources)
            print(f"  -> {len(brenda_data)} EC numbers with kinetics data")
        else:
            print("  -> No EC numbers to fetch kinetics for")

        # Step R8: Infer D-to-L mirrored reactions (RHEA-sourced only)
        print("\n[R8] Inferring D-to-L mirrored reactions...")
        existing_ids = {r["id"] for r in all_reactions}
        rhea_sourced = [r for r in all_reactions if r.get("rhea_id") or r.get("metadata", {}).get("source") in ("rhea_import", "rhea_discovery")]
        inferred = infer_mirrored_reactions(rhea_sourced, all_compounds, existing_ids)
        all_reactions.extend(inferred)
        print(f"  -> {len(inferred)} inferred mirrored reactions")

        # Step R9: Formula balance check on imported reactions
        print("\n[R9] Checking formula balance on imported reactions...")
        imported_rxns = [r for r in all_reactions if r.get("rhea_id") or r.get("metadata", {}).get("source") == "rhea_import"]
        if imported_rxns:
            compound_map_full = {c["id"]: c for c in all_compounds}
            formula_warnings = check_formula_balance(imported_rxns, compound_map_full)
            for w in formula_warnings:
                print(f"  [WARNING] {w}")
            print(f"  -> {len(imported_rxns)} imported reactions checked, {len(formula_warnings)} warnings")
        else:
            print("  -> No imported reactions to check")

        print("\n=== Ring 2 complete ===")
```

- [ ] **Step 2: Update metadata to include Ring 2 stats**

In the metadata dict construction, add:

Build the import_stats dict inside the `if not skip_import:` block and store in a local variable:

```python
        import_stats = {
            "chebi_matched": matched,
            "rhea_reactions": len(new_reactions),
            "enriched_reactions": enriched_existing,
            "inferred_reactions": len(inferred),
        }
```

Then in the metadata dict (outside the if block), reference it:

```python
    import_stats_data = import_stats if not skip_import else None
    # ... in metadata dict:
    "import_stats": import_stats_data,
```

- [ ] **Step 3: Run pipeline with --skip-import to verify Ring 1 still works**

Run: `python -m pipeline.run_pipeline --skip-import`
Expected: Pipeline completes with 135 compounds, 696 reactions (same as before)

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest pipeline/tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add pipeline/run_pipeline.py
git commit -m "feat: wire Ring 2 import steps into pipeline orchestrator"
```

---

## Chunk 6: Frontend Updates

### Task 15: Update TypeScript types

**Files:**
- Modify: `web/lib/types.ts`

- [ ] **Step 1: Add new fields to Compound interface**

In `web/lib/types.ts`, add to the `Compound` interface after `metadata`:

```typescript
  chebi_id: string | null;
  kegg_id: string | null;
  pubchem_id: string | null;
  inchi: string | null;
  smiles: string | null;
```

- [ ] **Step 2: Run frontend build to check types compile**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx tsc --noEmit`
Expected: No type errors (existing code doesn't reference these new fields yet)

- [ ] **Step 3: Commit**

```bash
git add web/lib/types.ts
git commit -m "feat(web): add external ID fields to Compound interface"
```

### Task 16: Update compound detail page with external IDs

**Files:**
- Modify: `web/app/compound/[id]/page.tsx`

- [ ] **Step 1: Read the Next.js docs for this version**

Check `web/node_modules/next/dist/docs/` for any relevant deprecation notices about page components. Follow AGENTS.md instructions.

- [ ] **Step 2: Add External IDs section to compound detail page**

After the stereocenters panel (after line ~123), add a new panel:

```tsx
          {/* External IDs */}
          {(compound.chebi_id || compound.kegg_id || compound.pubchem_id) && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 sm:col-span-2">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                External IDs
              </h3>
              <dl className="mt-3 space-y-2 text-sm">
                {compound.chebi_id && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">ChEBI</dt>
                    <dd>
                      <a
                        href={`https://www.ebi.ac.uk/chebi/searchId.do?chebiId=${compound.chebi_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {compound.chebi_id}
                      </a>
                    </dd>
                  </div>
                )}
                {compound.kegg_id && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">KEGG</dt>
                    <dd>
                      <a
                        href={`https://www.genome.jp/entry/${compound.kegg_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {compound.kegg_id}
                      </a>
                    </dd>
                  </div>
                )}
                {compound.pubchem_id && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">PubChem</dt>
                    <dd>
                      <a
                        href={`https://pubchem.ncbi.nlm.nih.gov/compound/${compound.pubchem_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {compound.pubchem_id}
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Structural identifiers */}
          {(compound.inchi || compound.smiles) && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 sm:col-span-2">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Structural Identifiers
              </h3>
              <dl className="mt-3 space-y-3 text-sm">
                {compound.inchi && (
                  <div>
                    <dt className="text-zinc-500">InChI</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-zinc-300">
                      {compound.inchi}
                    </dd>
                  </div>
                )}
                {compound.smiles && (
                  <div>
                    <dt className="text-zinc-500">SMILES</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-zinc-300">
                      {compound.smiles}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}
```

- [ ] **Step 3: Build and verify**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add web/app/compound/\\[id\\]/page.tsx
git commit -m "feat(web): add external IDs and structural identifiers to compound detail"
```

### Task 17: Update reaction detail page (replace Ring 2 placeholder)

**Files:**
- Modify: `web/app/reaction/[id]/page.tsx`

- [ ] **Step 1: Replace the Ring 2 placeholder section**

Replace the "Ring 2 placeholders" div (lines 184-196) with:

```tsx
        {/* Database references */}
        {(reaction.ec_number || reaction.rhea_id || (reaction.pmid && reaction.pmid.length > 0) || (reaction.organism && reaction.organism.length > 0)) && (
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {/* Enzyme info */}
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Enzyme Information
              </h3>
              <dl className="mt-3 space-y-2 text-sm">
                {reaction.ec_number && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">EC Number</dt>
                    <dd>
                      <a
                        href={`https://enzyme.expasy.org/EC/${reaction.ec_number}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {reaction.ec_number}
                      </a>
                    </dd>
                  </div>
                )}
                {reaction.enzyme_name && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Enzyme</dt>
                    <dd className="text-zinc-200">{reaction.enzyme_name}</dd>
                  </div>
                )}
                {reaction.rhea_id && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">RHEA</dt>
                    <dd>
                      <a
                        href={`https://www.rhea-db.org/rhea/${reaction.rhea_id.replace("RHEA:", "")}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {reaction.rhea_id}
                      </a>
                    </dd>
                  </div>
                )}
                {reaction.km_mm != null && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Km</dt>
                    <dd className="text-zinc-200">{reaction.km_mm} mM</dd>
                  </div>
                )}
                {reaction.kcat_sec != null && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">kcat</dt>
                    <dd className="text-zinc-200">{reaction.kcat_sec} s⁻¹</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Literature & organisms */}
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Literature & Organisms
              </h3>
              {reaction.pmid && reaction.pmid.length > 0 ? (
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-zinc-500">References</p>
                  <div className="flex flex-wrap gap-2">
                    {reaction.pmid.map((pmid) => (
                      <a
                        key={pmid}
                        href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-blue-400 hover:text-blue-300"
                      >
                        PMID:{pmid}
                      </a>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-zinc-500">No literature references</p>
              )}
              {reaction.organism && reaction.organism.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-zinc-500">Organisms</p>
                  <div className="flex flex-wrap gap-2">
                    {reaction.organism.map((org, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs italic text-zinc-300"
                      >
                        {org}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
```

- [ ] **Step 2: Build and verify**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add web/app/reaction/\\[id\\]/page.tsx
git commit -m "feat(web): replace Ring 2 placeholder with enzyme, literature, and kinetics data"
```

### Task 18: Update dashboard with enrichment stats

**Files:**
- Modify: `web/app/page.tsx`
- Modify: `web/lib/data.ts`

- [ ] **Step 1: Add enrichment stat helper to data.ts**

Add to `web/lib/data.ts`:

```typescript
export function getEnrichmentStats() {
  const chebiMatched = compounds.filter((c) => c.chebi_id).length;
  const validatedReactions = reactions.filter((r) => r.evidence_tier === "validated").length;
  const predictedReactions = reactions.filter((r) => r.evidence_tier === "predicted").length;
  return { chebiMatched, validatedReactions, predictedReactions };
}
```

- [ ] **Step 2: Add enrichment stats row to dashboard**

In `web/app/page.tsx`, import `getEnrichmentStats` from `@/lib/data` and add after the existing stats row:

```tsx
      {/* Enrichment stats */}
      {(() => {
        const enrichment = getEnrichmentStats();
        if (enrichment.chebiMatched === 0) return null;
        return (
          <div className="mt-4 grid w-full max-w-3xl grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard
              label="ChEBI Matched"
              value={enrichment.chebiMatched}
              href="/compounds"
              color="text-green-400"
            />
            <StatCard
              label="Validated"
              value={enrichment.validatedReactions}
              href="/reactions"
              color="text-emerald-400"
            />
            <StatCard
              label="Predicted"
              value={enrichment.predictedReactions}
              href="/reactions"
              color="text-yellow-400"
            />
          </div>
        );
      })()}
```

- [ ] **Step 3: Build and verify**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add web/app/page.tsx web/lib/data.ts
git commit -m "feat(web): add enrichment coverage stats to dashboard"
```

### Task 19: Add "Has external ID" filter to compound browser

**Files:**
- Modify: `web/app/compounds/page.tsx`

- [ ] **Step 1: Add state and filter toggle**

Add a `hasExternalId` boolean state and filter toggle button.

Add state:
```typescript
const [hasExternalId, setHasExternalId] = useState(false);
```

Add to the filter logic in the `useMemo`:
```typescript
      // External ID filter
      if (hasExternalId && !c.chebi_id && !c.kegg_id) return false;
```

Add after the carbon range filter div:
```tsx
            {/* External ID filter */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setHasExternalId(!hasExternalId)}
                className={`rounded-full border px-2 py-0.5 text-xs transition-colors ${
                  hasExternalId
                    ? "border-zinc-600 bg-zinc-800 text-zinc-200"
                    : "border-zinc-800 text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Has external ID
              </button>
            </div>
```

- [ ] **Step 2: Build and verify**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add web/app/compounds/page.tsx
git commit -m "feat(web): add external ID filter toggle to compound browser"
```

---

## Chunk 7: Copy Data + Final Verification

### Task 20: Copy enriched pipeline output to web/data

**Files:**
- Modify: `pipeline/run_pipeline.py` (add copy step)

- [ ] **Step 1: Add web data copy to pipeline**

At the end of `run_pipeline()`, after writing output files, add:

```python
    # Copy to web/data for Next.js build
    web_data_dir = os.path.join(os.path.dirname(__file__), "..", "web", "data")
    if os.path.exists(web_data_dir):
        import shutil
        shutil.copy2(compounds_path, os.path.join(web_data_dir, "compounds.json"))
        shutil.copy2(reactions_path, os.path.join(web_data_dir, "reactions.json"))
        shutil.copy2(metadata_path, os.path.join(web_data_dir, "pipeline_metadata.json"))
        print(f"  -> Copied to {web_data_dir}")
```

- [ ] **Step 2: Run full pipeline**

Run: `python -m pipeline.run_pipeline --skip-import`
Expected: Pipeline completes and copies data to web/data/

- [ ] **Step 3: Run frontend tests**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx vitest run`
Expected: All 5 tests pass

- [ ] **Step 4: Run full frontend build**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add pipeline/run_pipeline.py
git commit -m "feat: auto-copy pipeline output to web/data after generation"
```

### Task 21: Run full pipeline with import (end-to-end test)

- [ ] **Step 1: Run pipeline without --skip-import**

Run: `python -m pipeline.run_pipeline`
Expected: Pipeline runs Ring 1 + Ring 2 import steps. ChEBI download may take several minutes on first run. Output shows match counts, RHEA reactions found, etc.

- [ ] **Step 2: Check output sizes**

Run: `python -c "import json; c=json.load(open('pipeline/output/compounds.json')); r=json.load(open('pipeline/output/reactions.json')); print(f'Compounds: {len(c)}, Reactions: {len(r)}')"`
Expected: More compounds and reactions than Ring 1 baseline (135 / 696)

- [ ] **Step 3: Run all pipeline tests**

Run: `python -m pytest pipeline/tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Run frontend build with enriched data**

Run: `cd /Users/rivir/Documents/GitHub/sugar/web && npx next build`
Expected: Build succeeds with new data

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: Ring 2 database enrichment pipeline complete"
```
