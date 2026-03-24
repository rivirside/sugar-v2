# Enzyme Gap Analysis (Ring 4) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an enzyme gap analysis stage (Ring 4) that classifies every reaction's enzyme coverage, finds cross-substrate engineering candidates, and computes engineerability scores for route ranking.

**Architecture:** Four pure-function modules under `pipeline/analyze/` (similarity, engineerability, cross-substrate matching, enzyme index), plus an orchestrator that wires them into the pipeline. The pathfinder gains a scoring_mode parameter to rank routes by engineerability instead of (or combined with) biochemical cost.

**Tech Stack:** Python 3.12, pytest, TypeScript (Next.js frontend types)

**Spec:** `docs/superpowers/specs/2026-03-23-enzyme-gap-analysis-design.md`

---

## Chunk 1: Core Scoring Modules (similarity.py + engineerability.py)

These are pure functions with no dependencies on the rest of the pipeline. Build and test them first.

### Task 1: Substrate Similarity Scoring

**Files:**
- Create: `pipeline/analyze/__init__.py`
- Create: `pipeline/analyze/similarity.py`
- Create: `pipeline/tests/test_similarity.py`

- [ ] **Step 1: Create the `pipeline/analyze/` package**

```bash
mkdir -p pipeline/analyze
touch pipeline/analyze/__init__.py
```

- [ ] **Step 2: Write failing tests for `similarity.py`**

Create `pipeline/tests/test_similarity.py`:

```python
"""Tests for multi-dimensional substrate similarity scoring."""

from pipeline.analyze.similarity import compute_similarity


def _compound(id, type, carbons, stereocenters, modifications=None):
    """Helper: minimal compound dict for similarity tests."""
    return {
        "id": id,
        "type": type,
        "carbons": carbons,
        "stereocenters": stereocenters,
        "modifications": modifications,
    }


# --- Identical compounds ---

def test_identical_compounds():
    """Identical compounds have similarity 1.0 and all distances 0."""
    a = _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"])
    result = compute_similarity(a, a)
    assert result["overall"] == 1.0
    assert result["stereocenter_distance"] == 0
    assert result["modification_distance"] == 0.0
    assert result["carbon_count_distance"] == 0
    assert result["type_distance"] == 0.0


# --- Stereocenter distance ---

def test_one_stereocenter_different():
    """One stereocenter flip produces stereocenter_distance=1, high overall."""
    a = _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"])
    b = _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"])
    result = compute_similarity(a, b)
    assert result["stereocenter_distance"] == 1
    assert result["overall"] > 0.85  # small penalty

def test_all_stereocenters_different():
    """All 4 stereocenters different -> stereocenter_distance=4."""
    a = _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"])
    b = _compound("L-GLC", "aldose", 6, ["S", "R", "S", "S"])
    result = compute_similarity(a, b)
    assert result["stereocenter_distance"] == 4

def test_zero_stereocenters_no_division_error():
    """Both compounds with empty stereocenters: stereo_norm=0.0, no crash."""
    a = _compound("GLYCO", "aldose", 2, [])
    b = _compound("GLYCO2", "aldose", 2, [])
    result = compute_similarity(a, b)
    assert result["stereocenter_distance"] == 0
    assert result["overall"] == 1.0

def test_different_length_stereocenters():
    """Different stereocenter array lengths (C5 vs C6)."""
    a = _compound("C5", "aldose", 5, ["R", "S", "R"])
    b = _compound("C6", "aldose", 6, ["R", "S", "R", "R"])
    result = compute_similarity(a, b)
    # stereo_distance = at least 1 (length diff), carbon_count_distance = 1
    assert result["stereocenter_distance"] >= 1
    assert result["carbon_count_distance"] == 1


# --- Modification distance ---

def test_same_modifications():
    """Same phosphate at same position: modification_distance=0."""
    mods = [{"type": "phosphate", "position": 6}]
    a = _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"], mods)
    b = _compound("D-MAN-6P", "phosphate", 6, ["S", "S", "R", "R"], mods)
    result = compute_similarity(a, b)
    assert result["modification_distance"] == 0.0

def test_different_phosphate_position():
    """Same type, different position: modification_distance=0.4."""
    a = _compound("X-1P", "phosphate", 6, ["R"], [{"type": "phosphate", "position": 1}])
    b = _compound("X-6P", "phosphate", 6, ["R"], [{"type": "phosphate", "position": 6}])
    result = compute_similarity(a, b)
    assert result["modification_distance"] == 0.4

def test_has_vs_no_modifications():
    """One has phosphate, other has none: modification_distance=0.7."""
    a = _compound("D-GLC-6P", "phosphate", 6, ["R"], [{"type": "phosphate", "position": 6}])
    b = _compound("D-GLC", "aldose", 6, ["R"], None)
    result = compute_similarity(a, b)
    assert result["modification_distance"] == 0.7


# --- Carbon count distance ---

def test_same_carbon_count():
    """Same carbons: carbon_count_distance=0."""
    a = _compound("A", "aldose", 6, ["R"])
    b = _compound("B", "aldose", 6, ["S"])
    result = compute_similarity(a, b)
    assert result["carbon_count_distance"] == 0

def test_different_carbon_count():
    """C3 vs C6: carbon_count_distance=3."""
    a = _compound("A", "aldose", 3, ["R"])
    b = _compound("B", "aldose", 6, ["R", "R", "R", "R"])
    result = compute_similarity(a, b)
    assert result["carbon_count_distance"] == 3


# --- Type distance ---

def test_same_type():
    """Same type: type_distance=0."""
    a = _compound("A", "aldose", 6, ["R"])
    b = _compound("B", "aldose", 6, ["S"])
    result = compute_similarity(a, b)
    assert result["type_distance"] == 0.0

def test_aldose_ketose():
    """Aldose vs ketose: type_distance=0.5."""
    a = _compound("A", "aldose", 6, ["R"])
    b = _compound("B", "ketose", 6, ["R"])
    result = compute_similarity(a, b)
    assert result["type_distance"] == 0.5

def test_aldose_polyol():
    """Aldose vs polyol: type_distance=0.7."""
    a = _compound("A", "aldose", 6, ["R"])
    b = _compound("B", "polyol", 6, ["R"])
    result = compute_similarity(a, b)
    assert result["type_distance"] == 0.7

def test_phosphate_type_uses_parent_logic():
    """Phosphate type: similarity should look at parent_type or treat as its parent type.
    Two phosphate compounds with same underlying structure are similar."""
    a = _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                  [{"type": "phosphate", "position": 6}])
    b = _compound("D-MAN-6P", "phosphate", 6, ["S", "S", "R", "R"],
                  [{"type": "phosphate", "position": 6}])
    result = compute_similarity(a, b)
    assert result["type_distance"] == 0.0  # both phosphate -> same type


# --- Composite score ---

def test_maximally_different():
    """Maximally different compounds: low overall score."""
    a = _compound("A", "aldose", 6, ["R", "S", "R", "R"])
    b = _compound("B", "polyol", 3, [], [{"type": "phosphate", "position": 1}])
    result = compute_similarity(a, b)
    assert result["overall"] < 0.3  # very different

def test_overall_range():
    """Overall score is always between 0.0 and 1.0."""
    pairs = [
        (_compound("A", "aldose", 6, ["R", "S"]), _compound("B", "polyol", 2, [])),
        (_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["R"])),
    ]
    for a, b in pairs:
        result = compute_similarity(a, b)
        assert 0.0 <= result["overall"] <= 1.0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_similarity.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement `similarity.py`**

Create `pipeline/analyze/similarity.py`:

```python
"""Multi-dimensional substrate similarity scoring.

Compares two compound dicts across four dimensions:
1. Stereocenter distance (number of differing positions)
2. Modification distance (phosphate pattern differences)
3. Carbon count distance (chain length difference)
4. Type distance (aldose/ketose/polyol/phosphate)

Returns a dict with per-dimension raw values and a weighted composite score.
"""

# Weights for composite score (sum = 1.0)
W_STEREO = 0.35
W_MOD = 0.25
W_CARBON = 0.25
W_TYPE = 0.15

# Type distance lookup: (type_a, type_b) -> distance
# Symmetric: order doesn't matter.
_TYPE_DISTANCES = {
    ("aldose", "ketose"): 0.5,
    ("aldose", "polyol"): 0.7,
    ("ketose", "polyol"): 0.7,
}


def _stereo_distance(stereo_a: list[str], stereo_b: list[str]) -> int:
    """Count differing stereocenters. Length difference adds to distance."""
    min_len = min(len(stereo_a), len(stereo_b))
    diff = sum(1 for i in range(min_len) if stereo_a[i] != stereo_b[i])
    diff += abs(len(stereo_a) - len(stereo_b))
    return diff


def _modification_distance(mods_a: list[dict] | None, mods_b: list[dict] | None) -> float:
    """Score modification differences.

    Returns:
        0.0: same modifications (identical positions and types)
        0.4: same type, different position
        0.7: different number of modifications (has vs doesn't)
        0.9: different modification types
    """
    a_set = set()
    b_set = set()
    a_types = set()
    b_types = set()

    if mods_a:
        for m in mods_a:
            a_set.add((m["type"], m["position"]))
            a_types.add(m["type"])
    if mods_b:
        for m in mods_b:
            b_set.add((m["type"], m["position"]))
            b_types.add(m["type"])

    # No modifications on either side
    if not a_set and not b_set:
        return 0.0

    # Identical modifications
    if a_set == b_set:
        return 0.0

    # One has mods, other doesn't
    if (not a_set) != (not b_set):
        return 0.7

    # Both have mods but different types
    if a_types != b_types:
        return 0.9

    # Same types, different positions
    return 0.4


def _type_distance(type_a: str, type_b: str) -> float:
    """Score compound type differences."""
    # Normalize: treat "phosphate" as its own type for comparison.
    # Two phosphate compounds = same type (0.0).
    if type_a == type_b:
        return 0.0

    pair = tuple(sorted([type_a, type_b]))
    return _TYPE_DISTANCES.get(pair, 0.5)  # default 0.5 for unknown pairs


def compute_similarity(compound_a: dict, compound_b: dict) -> dict:
    """Compute multi-dimensional substrate similarity between two compounds.

    Args:
        compound_a: First compound dict (must have id, type, carbons,
                     stereocenters, modifications).
        compound_b: Second compound dict.

    Returns:
        Dict with keys:
            overall: float (0.0 = maximally different, 1.0 = identical)
            stereocenter_distance: int (raw count of differing positions)
            modification_distance: float (0.0-1.0)
            carbon_count_distance: int (absolute difference)
            type_distance: float (0.0-1.0)
    """
    stereo_a = compound_a.get("stereocenters", [])
    stereo_b = compound_b.get("stereocenters", [])
    stereo_dist = _stereo_distance(stereo_a, stereo_b)

    max_stereo = max(len(stereo_a), len(stereo_b))
    stereo_norm = stereo_dist / max_stereo if max_stereo > 0 else 0.0

    mod_dist = _modification_distance(
        compound_a.get("modifications"),
        compound_b.get("modifications"),
    )

    carbons_a = compound_a.get("carbons", 0)
    carbons_b = compound_b.get("carbons", 0)
    carbon_dist = abs(carbons_a - carbons_b)
    max_carbons = max(carbons_a, carbons_b)
    carbon_norm = carbon_dist / max_carbons if max_carbons > 0 else 0.0

    type_dist = _type_distance(
        compound_a.get("type", ""),
        compound_b.get("type", ""),
    )

    overall = 1.0 - (
        W_STEREO * stereo_norm
        + W_MOD * mod_dist
        + W_CARBON * carbon_norm
        + W_TYPE * type_dist
    )
    # Clamp to [0.0, 1.0]
    overall = max(0.0, min(1.0, overall))

    return {
        "overall": overall,
        "stereocenter_distance": stereo_dist,
        "modification_distance": mod_dist,
        "carbon_count_distance": carbon_dist,
        "type_distance": type_dist,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_similarity.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline/analyze/__init__.py pipeline/analyze/similarity.py pipeline/tests/test_similarity.py
git commit -m "feat: add substrate similarity scoring module (Ring 4)"
```

---

### Task 2: Engineerability Score

**Files:**
- Create: `pipeline/analyze/engineerability.py`
- Create: `pipeline/tests/test_engineerability.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_engineerability.py`:

```python
"""Tests for engineerability score computation."""

from pipeline.analyze.engineerability import compute_score


def test_direct_enzyme_score_zero():
    """Direct enzyme match: engineerability = 0.0."""
    score, components = compute_score(
        coverage_level="direct",
        best_similarity=1.0,
        ec_family_size=50,
        has_pdb=True,
        num_candidates=1,
    )
    assert score == 0.0
    assert components["coverage_level"] == 0.0


def test_no_candidates_score_one():
    """No candidates at all: engineerability = 1.0."""
    score, components = compute_score(
        coverage_level="none",
        best_similarity=0.0,
        ec_family_size=None,
        has_pdb=False,
        num_candidates=0,
    )
    assert score == 1.0
    assert components["coverage_level"] == 1.0
    assert components["best_similarity"] == 1.0
    assert components["family_richness"] == 0.8  # None default
    assert components["structural_data"] == 1.0


def test_layer1_high_similarity_low_score():
    """Layer 1 + high similarity + large family + PDB = low score."""
    score, components = compute_score(
        coverage_level="cross_substrate_l1",
        best_similarity=0.95,
        ec_family_size=60,
        has_pdb=True,
        num_candidates=3,
    )
    assert score < 0.2
    assert components["structural_data"] == 0.0


def test_layer2_medium_score():
    """Layer 2 + medium similarity = medium score."""
    score, components = compute_score(
        coverage_level="cross_substrate_l2",
        best_similarity=0.6,
        ec_family_size=10,
        has_pdb=False,
        num_candidates=1,
    )
    assert 0.3 < score < 0.7


def test_family_only_high_score():
    """Family only (Layer 3): high but not maximum score."""
    score, components = compute_score(
        coverage_level="family_only",
        best_similarity=0.0,
        ec_family_size=5,
        has_pdb=False,
        num_candidates=1,
    )
    assert score > 0.6
    assert score < 1.0


def test_candidate_count_modulates_penalty():
    """More candidates reduce the coverage penalty."""
    score_1, _ = compute_score("cross_substrate_l1", 0.8, 20, True, num_candidates=1)
    score_5, _ = compute_score("cross_substrate_l1", 0.8, 20, True, num_candidates=5)
    assert score_5 < score_1  # more candidates = easier


def test_ec_family_none_defaults():
    """When ec_family_size is None, family_richness defaults to 0.8."""
    _, components = compute_score("cross_substrate_l1", 0.8, None, False, 1)
    assert components["family_richness"] == 0.8


def test_large_family_low_penalty():
    """Family of 50+ enzymes: family_richness = 0.0."""
    _, components = compute_score("cross_substrate_l1", 0.8, 100, True, 1)
    assert components["family_richness"] == 0.0


def test_score_always_in_range():
    """Engineerability score is always between 0.0 and 1.0."""
    test_cases = [
        ("direct", 1.0, 100, True, 10),
        ("none", 0.0, None, False, 0),
        ("cross_substrate_l1", 0.5, 25, True, 3),
        ("cross_substrate_l2", 0.3, 1, False, 1),
        ("family_only", 0.0, 5, False, 1),
    ]
    for level, sim, fam, pdb, count in test_cases:
        score, _ = compute_score(level, sim, fam, pdb, count)
        assert 0.0 <= score <= 1.0, f"Out of range for {level}: {score}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_engineerability.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `engineerability.py`**

Create `pipeline/analyze/engineerability.py`:

```python
"""Compute engineerability score for reactions.

Combines four components:
1. Coverage level (0.4 weight) - direct, cross-substrate, family, none
2. Best candidate similarity (0.3 weight) - inverted similarity score
3. EC family richness (0.15 weight) - normalized family size
4. Structural data availability (0.15 weight) - PDB crystal structure exists
"""

# Coverage level base penalties
_COVERAGE_PENALTIES = {
    "direct": 0.0,
    "cross_substrate_l1": 0.3,
    "cross_substrate_l2": 0.6,
    "family_only": 0.8,
    "none": 1.0,
}

# Component weights (sum = 1.0)
W_COVERAGE = 0.4
W_SIMILARITY = 0.3
W_FAMILY = 0.15
W_STRUCTURAL = 0.15

# Default family richness penalty when BRENDA data unavailable
DEFAULT_FAMILY_PENALTY = 0.8

# Family size normalization ceiling
FAMILY_SIZE_CEILING = 50


def compute_score(
    coverage_level: str,
    best_similarity: float,
    ec_family_size: int | None,
    has_pdb: bool,
    num_candidates: int = 0,
) -> tuple[float, dict]:
    """Compute the engineerability score for a reaction.

    Args:
        coverage_level: One of "direct", "cross_substrate_l1",
            "cross_substrate_l2", "family_only", "none".
        best_similarity: Overall similarity score of the best candidate
            (0.0 to 1.0). Set to 0.0 when no candidates exist.
        ec_family_size: Number of distinct enzymes in the EC subclass.
            None when BRENDA data is unavailable.
        has_pdb: Whether the best candidate has a PDB crystal structure.
        num_candidates: Number of cross-substrate candidates found.

    Returns:
        Tuple of (engineerability_score, components_dict).
        Score range: 0.0 (trivially engineerable) to 1.0 (no leads).
    """
    # Component 1: Coverage level with candidate count modulation
    base_penalty = _COVERAGE_PENALTIES.get(coverage_level, 1.0)
    if coverage_level != "direct" and coverage_level != "none" and num_candidates > 0:
        modulation = 1.0 - min(num_candidates / 5, 1.0) * 0.3
        coverage_component = base_penalty * modulation
    else:
        coverage_component = base_penalty

    # Component 2: Best candidate similarity (inverted: higher = harder)
    if coverage_level == "direct":
        similarity_component = 0.0
    elif coverage_level == "none":
        similarity_component = 1.0
    else:
        similarity_component = 1.0 - best_similarity

    # Component 3: EC family richness
    if ec_family_size is None:
        family_component = DEFAULT_FAMILY_PENALTY
    else:
        family_component = 1.0 - min(ec_family_size / FAMILY_SIZE_CEILING, 1.0)

    # Component 4: Structural data availability (binary in phase 1)
    structural_component = 0.0 if has_pdb else 1.0

    # Composite score
    score = (
        W_COVERAGE * coverage_component
        + W_SIMILARITY * similarity_component
        + W_FAMILY * family_component
        + W_STRUCTURAL * structural_component
    )
    score = max(0.0, min(1.0, score))

    components = {
        "coverage_level": coverage_component,
        "best_similarity": similarity_component,
        "family_richness": family_component,
        "structural_data": structural_component,
    }

    return score, components
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_engineerability.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/analyze/engineerability.py pipeline/tests/test_engineerability.py
git commit -m "feat: add engineerability score computation (Ring 4)"
```

---

## Chunk 2: Enzyme Index + Cross-Substrate Matching

### Task 3: Enzyme Index Builder

**Files:**
- Create: `pipeline/analyze/enzyme_index.py`
- Create: `pipeline/tests/test_enzyme_index.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_enzyme_index.py`:

```python
"""Tests for enzyme index builder."""

from pipeline.analyze.enzyme_index import build_enzyme_index


def _reaction(id, ec=None, enzyme_name=None, substrates=None, organisms=None):
    """Helper: minimal reaction dict for enzyme index tests."""
    r = {
        "id": id,
        "reaction_type": "epimerization",
        "substrates": substrates or ["D-GLC"],
        "products": ["D-MAN"],
        "evidence_tier": "hypothetical",
        "evidence_criteria": [],
        "yield": None,
        "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
    if enzyme_name:
        r["enzyme_name"] = enzyme_name
    if organisms:
        r["organism"] = organisms
    return r


def test_empty_reactions():
    """No reactions -> empty index."""
    index = build_enzyme_index([])
    assert index == {}


def test_no_ec_numbers():
    """Reactions without ec_number are skipped."""
    rxns = [_reaction("R1"), _reaction("R2")]
    index = build_enzyme_index(rxns)
    assert index == {}


def test_single_ec_entry():
    """One reaction with EC -> one entry in index."""
    rxns = [_reaction("R1", ec="5.1.3.2", enzyme_name="epimerase",
                       substrates=["D-GLC"], organisms=["E. coli"])]
    index = build_enzyme_index(rxns)
    assert "5.1.3.2" in index
    assert index["5.1.3.2"]["name"] == "epimerase"
    assert "E. coli" in index["5.1.3.2"]["organisms"]
    assert "D-GLC" in index["5.1.3.2"]["known_substrates"]
    assert index["5.1.3.2"]["reaction_count"] == 1


def test_multiple_reactions_same_ec():
    """Multiple reactions with same EC -> merged entry."""
    rxns = [
        _reaction("R1", ec="5.1.3.2", substrates=["D-GLC"], organisms=["E. coli"]),
        _reaction("R2", ec="5.1.3.2", substrates=["D-GAL"], organisms=["H. sapiens"]),
    ]
    index = build_enzyme_index(rxns)
    assert index["5.1.3.2"]["reaction_count"] == 2
    assert "D-GLC" in index["5.1.3.2"]["known_substrates"]
    assert "D-GAL" in index["5.1.3.2"]["known_substrates"]
    assert "E. coli" in index["5.1.3.2"]["organisms"]
    assert "H. sapiens" in index["5.1.3.2"]["organisms"]


def test_tier2_fields_default_none():
    """Tier 2 fields (family_size, pdb_count, uniprot_ids) default to None."""
    rxns = [_reaction("R1", ec="5.1.3.2")]
    index = build_enzyme_index(rxns)
    assert index["5.1.3.2"]["family_size"] is None
    assert index["5.1.3.2"]["pdb_count"] is None
    assert index["5.1.3.2"]["uniprot_ids"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_enzyme_index.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `enzyme_index.py`**

Create `pipeline/analyze/enzyme_index.py`:

```python
"""Build lightweight enzyme family index from Ring 2 reaction data.

Tier 1 (always available): Built from Ring 2 reaction annotations.
Tier 2 (optional): Extended with BRENDA/UniProt API data when available.

Phase 1 implements Tier 1 only. Tier 2 fields are present but set to None.
"""


def build_enzyme_index(reactions: list[dict]) -> dict:
    """Build EC-number-keyed enzyme index from reactions.

    Scans all reactions for ec_number fields (populated by Ring 2).
    Aggregates enzyme names, organisms, and known substrates per EC number.

    Args:
        reactions: List of reaction dicts, some with Ring 2 annotations.

    Returns:
        Dict keyed by EC number, each value containing:
            name: str | None
            organisms: list[str]
            known_substrates: list[str]
            reaction_count: int
            family_size: None (Tier 2, not yet implemented)
            pdb_count: None (Tier 2, not yet implemented)
            uniprot_ids: None (Tier 2, not yet implemented)
    """
    index: dict[str, dict] = {}

    for rxn in reactions:
        ec = rxn.get("ec_number")
        if not ec:
            continue

        if ec not in index:
            index[ec] = {
                "name": rxn.get("enzyme_name"),
                "organisms": [],
                "known_substrates": [],
                "reaction_count": 0,
                # Tier 2 placeholders
                "family_size": None,
                "pdb_count": None,
                "uniprot_ids": None,
            }

        entry = index[ec]
        entry["reaction_count"] += 1

        # Use first non-None enzyme name
        if entry["name"] is None and rxn.get("enzyme_name"):
            entry["name"] = rxn["enzyme_name"]

        # Collect organisms (deduplicated)
        for org in rxn.get("organism", []):
            if org not in entry["organisms"]:
                entry["organisms"].append(org)

        # Collect substrates (deduplicated)
        for sub_id in rxn.get("substrates", []):
            if sub_id not in entry["known_substrates"]:
                entry["known_substrates"].append(sub_id)

    return index
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_enzyme_index.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/analyze/enzyme_index.py pipeline/tests/test_enzyme_index.py
git commit -m "feat: add enzyme index builder (Ring 4, Tier 1)"
```

---

### Task 4: Cross-Substrate Matching

**Files:**
- Create: `pipeline/analyze/cross_substrate.py`
- Create: `pipeline/tests/test_cross_substrate.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_cross_substrate.py`:

```python
"""Tests for cross-substrate enzyme candidate matching."""

from pipeline.analyze.cross_substrate import find_candidates, extract_position


def _compound(id, type, carbons, stereocenters, modifications=None):
    """Helper: minimal compound dict."""
    return {
        "id": id,
        "type": type,
        "carbons": carbons,
        "stereocenters": stereocenters,
        "modifications": modifications,
    }


def _reaction(id, rtype, substrates, products, ec=None, enzyme_name=None, organism=None):
    """Helper: minimal reaction dict."""
    r = {
        "id": id,
        "reaction_type": rtype,
        "substrates": substrates,
        "products": products,
        "evidence_tier": "hypothetical" if not ec else "validated",
        "evidence_criteria": [],
        "yield": None,
        "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
        r["enzyme_name"] = enzyme_name or "test enzyme"
        r["organism"] = [organism] if organism else []
    return r


# --- Position extraction ---

def test_epi_position():
    """Epimerization: position is the index where stereocenters differ."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    rxn = _reaction("EPI-1", "epimerization", ["D-GLC"], ["D-MAN"])
    pos = extract_position(rxn, compounds)
    assert pos == (0,)  # index 0 differs (R vs S)


def test_mutase_position():
    """Mutase: position from modifications, not stereocenters."""
    compounds = {
        "D-GLC-1P": _compound("D-GLC-1P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 1}]),
        "D-GLC-6P": _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 6}]),
    }
    rxn = _reaction("MUT-1", "mutase", ["D-GLC-1P"], ["D-GLC-6P"])
    pos = extract_position(rxn, compounds)
    assert pos == (1, 6)  # phosphate positions


def test_phosphorylation_position():
    """Phosphorylation: position from phosphate site."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-GLC-6P": _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                               [{"type": "phosphate", "position": 6}]),
    }
    rxn = _reaction("PHOS-1", "phosphorylation", ["D-GLC"], ["D-GLC-6P"])
    pos = extract_position(rxn, compounds)
    assert pos == (6,)


def test_isomerization_no_position():
    """Isomerization: no position concept, returns None."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-FRU": _compound("D-FRU", "ketose", 6, ["S", "R", "R"]),
    }
    rxn = _reaction("ISO-1", "isomerization", ["D-GLC"], ["D-FRU"])
    pos = extract_position(rxn, compounds)
    assert pos is None


def test_reduction_no_position():
    """Reduction: no position concept, returns None."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-GLC-OL": _compound("D-GLC-OL", "polyol", 6, ["R", "S", "R", "R"]),
    }
    rxn = _reaction("RED-1", "reduction", ["D-GLC"], ["D-GLC-OL"])
    pos = extract_position(rxn, compounds)
    assert pos is None


# --- Cross-substrate matching ---

def test_no_enzyme_reactions_returns_empty():
    """When no reactions have enzyme data, candidates list is empty."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    gap = _reaction("GAP-1", "epimerization", ["D-GLC"], ["D-MAN"])
    all_rxns = [gap]
    result = find_candidates(gap, all_rxns, compounds)
    assert result == []


def test_layer1_match():
    """Layer 1: same type, same position, different substrate."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
        "D-GAL": _compound("D-GAL", "aldose", 6, ["R", "S", "S", "R"]),
        "D-TAL": _compound("D-TAL", "aldose", 6, ["S", "S", "S", "R"]),
    }
    # Gap: epimerize pos 0 on D-GAL (no enzyme)
    gap = _reaction("GAP", "epimerization", ["D-GAL"], ["D-TAL"])
    # Known: epimerize pos 0 on D-GLC (has enzyme)
    known = _reaction("KNOWN", "epimerization", ["D-GLC"], ["D-MAN"],
                       ec="5.1.3.18", enzyme_name="mannose-6P epimerase")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 1
    assert result[0]["ec_number"] == "5.1.3.18"


def test_layer2_match():
    """Layer 2: same type, different position."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-ALL": _compound("D-ALL", "aldose", 6, ["R", "S", "R", "S"]),  # pos 3 differs
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),  # pos 0 differs
    }
    # Gap: epimerize pos 3 on D-GLC
    gap = _reaction("GAP", "epimerization", ["D-GLC"], ["D-ALL"])
    # Known: epimerize pos 0 on D-GLC (different position)
    known = _reaction("KNOWN", "epimerization", ["D-GLC"], ["D-MAN"],
                       ec="5.1.3.18")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 2


def test_no_match_returns_none_coverage():
    """No matching candidates -> empty list."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-MAN": _compound("D-MAN", "aldose", 6, ["S", "S", "R", "R"]),
    }
    gap = _reaction("GAP", "epimerization", ["D-GLC"], ["D-MAN"])
    # Only a phosphorylation enzyme (wrong type)
    wrong_type = _reaction("PHOS", "phosphorylation", ["D-GLC"], ["D-GLC-6P"],
                            ec="2.7.1.1")
    compounds["D-GLC-6P"] = _compound("D-GLC-6P", "phosphate", 6, ["R", "S", "R", "R"],
                                       [{"type": "phosphate", "position": 6}])
    result = find_candidates(gap, [gap, wrong_type], compounds)
    assert result == []


def test_candidates_sorted_by_layer_then_similarity():
    """Candidates sorted: layer ascending, then similarity descending."""
    compounds = {
        "A": _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        "B": _compound("B", "aldose", 6, ["S", "S", "R", "R"]),  # pos 0 flip
        "C": _compound("C", "aldose", 6, ["R", "R", "R", "R"]),  # pos 1 flip
        "D": _compound("D", "aldose", 6, ["S", "R", "R", "R"]),  # pos 0+1 flip
    }
    gap = _reaction("GAP", "epimerization", ["A"], ["B"])
    # Layer 1 candidate (same position 0)
    l1 = _reaction("L1", "epimerization", ["C"], ["D"], ec="5.1.3.1")
    # Layer 2 candidate (different position)
    l2 = _reaction("L2", "epimerization", ["A"], ["C"], ec="5.1.3.2")
    result = find_candidates(gap, [gap, l1, l2], compounds)
    assert len(result) == 2
    assert result[0]["matching_layer"] <= result[1]["matching_layer"]


def test_max_candidates_cap():
    """Results capped at max_candidates."""
    compounds = {f"C{i}": _compound(f"C{i}", "aldose", 6, ["R"]) for i in range(20)}
    compounds["GAP_S"] = _compound("GAP_S", "aldose", 6, ["S"])
    gap = _reaction("GAP", "epimerization", ["GAP_S"], ["C0"])
    # 10 known epimerases
    knowns = [
        _reaction(f"K{i}", "epimerization", [f"C{i}"], [f"C{i+1}"], ec=f"5.1.3.{i}")
        for i in range(0, 10)
    ]
    result = find_candidates(gap, [gap] + knowns, compounds, max_candidates=3)
    assert len(result) <= 3


def test_dedup_by_ec_keeps_best():
    """Deduplicate by EC: keep entry with best (layer, similarity)."""
    compounds = {
        "A": _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        "B": _compound("B", "aldose", 6, ["S", "S", "R", "R"]),
        "C": _compound("C", "aldose", 6, ["R", "R", "R", "R"]),
        "D": _compound("D", "aldose", 6, ["S", "R", "R", "R"]),
    }
    gap = _reaction("GAP", "epimerization", ["A"], ["B"])
    # Same EC at different layers
    l1 = _reaction("L1", "epimerization", ["C"], ["D"], ec="5.1.3.1")
    l2 = _reaction("L2", "epimerization", ["A"], ["C"], ec="5.1.3.1")  # same EC, different layer
    result = find_candidates(gap, [gap, l1, l2], compounds)
    ec_numbers = [c["ec_number"] for c in result]
    assert ec_numbers.count("5.1.3.1") == 1  # deduplicated


def test_isomerization_no_layer_split():
    """Isomerization: Layers 1+2 collapse (no position), all same-type matches are Layer 1."""
    compounds = {
        "D-GLC": _compound("D-GLC", "aldose", 6, ["R", "S", "R", "R"]),
        "D-FRU": _compound("D-FRU", "ketose", 6, ["S", "R", "R"]),
        "D-GAL": _compound("D-GAL", "aldose", 6, ["R", "S", "S", "R"]),
        "D-TAG": _compound("D-TAG", "ketose", 6, ["S", "S", "R"]),
    }
    gap = _reaction("GAP", "isomerization", ["D-GLC"], ["D-FRU"])
    known = _reaction("K1", "isomerization", ["D-GAL"], ["D-TAG"], ec="5.3.1.9")
    result = find_candidates(gap, [gap, known], compounds)
    assert len(result) >= 1
    assert result[0]["matching_layer"] == 1  # not 2, since no position concept
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_cross_substrate.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `cross_substrate.py`**

Create `pipeline/analyze/cross_substrate.py`:

```python
"""Cross-substrate enzyme candidate matching.

For reactions without a direct enzyme match, finds enzymes that catalyze
the same reaction type on structurally similar substrates. Candidates are
searched in three layers ordered by relevance.
"""

from pipeline.analyze.similarity import compute_similarity

# Reaction types where position is not a distinguishing factor.
# Layers 1 and 2 collapse into a single "same type" layer.
_POSITIONLESS_TYPES = {"isomerization", "reduction"}

# Reaction types where directionality matters for matching.
_DIRECTIONAL_TYPES = {"phosphorylation", "dephosphorylation"}


def extract_position(reaction: dict, compound_map: dict) -> tuple[int, ...] | None:
    """Extract the reaction position for cross-substrate matching.

    Returns:
        Tuple of position indices for position-aware types, or None for
        position-agnostic types (isomerization, reduction).

    Position extraction rules:
        - Epimerization: index where stereocenters differ
        - Mutase: (from_position, to_position) from modifications
        - Phosphorylation/Dephosphorylation: phosphate site from modifications
        - Isomerization/Reduction: None (no position concept)
    """
    rtype = reaction["reaction_type"]

    if rtype in _POSITIONLESS_TYPES:
        return None

    sub_id = reaction["substrates"][0] if reaction["substrates"] else None
    prod_id = reaction["products"][0] if reaction["products"] else None
    if not sub_id or not prod_id:
        return None

    sub = compound_map.get(sub_id)
    prod = compound_map.get(prod_id)
    if not sub or not prod:
        return None

    if rtype == "epimerization":
        stereo_a = sub.get("stereocenters", [])
        stereo_b = prod.get("stereocenters", [])
        diffs = [i for i in range(min(len(stereo_a), len(stereo_b)))
                 if stereo_a[i] != stereo_b[i]]
        if len(diffs) == 1:
            return (diffs[0],)
        return tuple(diffs) if diffs else None

    if rtype == "mutase":
        sub_mods = sub.get("modifications") or []
        prod_mods = prod.get("modifications") or []
        sub_positions = sorted(m["position"] for m in sub_mods if m["type"] == "phosphate")
        prod_positions = sorted(m["position"] for m in prod_mods if m["type"] == "phosphate")
        if sub_positions and prod_positions:
            return tuple(sorted(set(sub_positions + prod_positions)))
        return None

    if rtype in ("phosphorylation", "dephosphorylation"):
        # Find the phosphorylated compound
        phospho = prod if rtype == "phosphorylation" else sub
        mods = phospho.get("modifications") or []
        positions = sorted(m["position"] for m in mods if m["type"] == "phosphate")
        return tuple(positions) if positions else None

    return None


def find_candidates(
    gap_reaction: dict,
    all_reactions: list[dict],
    compound_map: dict,
    enzyme_index: dict | None = None,
    max_candidates: int = 5,
) -> list[dict]:
    """Find cross-substrate enzyme candidates for a gap reaction.

    Args:
        gap_reaction: The reaction lacking a direct enzyme match.
        all_reactions: All reactions in the dataset.
        compound_map: Dict mapping compound ID to compound dict.
        enzyme_index: Optional EC-keyed enzyme index for Layer 3 matching.
        max_candidates: Maximum candidates to return.

    Returns:
        List of candidate dicts sorted by (layer asc, similarity desc),
        capped at max_candidates. Each dict contains:
            ec_number, enzyme_name, organism, uniprot_id, pdb_ids,
            source_reaction_id, known_substrate_id, matching_layer,
            similarity (dict with overall + per-dimension scores)
    """
    gap_type = gap_reaction["reaction_type"]
    gap_position = extract_position(gap_reaction, compound_map)
    gap_sub_id = gap_reaction["substrates"][0] if gap_reaction["substrates"] else None
    gap_sub = compound_map.get(gap_sub_id) if gap_sub_id else None

    if not gap_sub:
        return []

    candidates = []

    for rxn in all_reactions:
        # Skip self
        if rxn["id"] == gap_reaction["id"]:
            continue

        # Must have enzyme data
        if not rxn.get("ec_number"):
            continue

        # Must be same reaction type
        if rxn["reaction_type"] != gap_type:
            continue

        # Determine layer
        rxn_position = extract_position(rxn, compound_map)

        if gap_position is None:
            # Positionless types: all same-type matches are Layer 1
            layer = 1
        elif rxn_position == gap_position:
            layer = 1
        elif rxn_position is not None:
            layer = 2
        else:
            layer = 2  # can't determine position -> treat as different

        # Get the known enzyme's substrate
        known_sub_id = rxn["substrates"][0] if rxn["substrates"] else None
        known_sub = compound_map.get(known_sub_id) if known_sub_id else None

        if not known_sub:
            continue

        # Compute substrate similarity
        sim = compute_similarity(gap_sub, known_sub)

        candidate = {
            "ec_number": rxn.get("ec_number"),
            "enzyme_name": rxn.get("enzyme_name", ""),
            "organism": rxn.get("organism", [None])[0] if rxn.get("organism") else None,
            "uniprot_id": None,  # Tier 2
            "pdb_ids": [],       # Tier 2
            "source_reaction_id": rxn["id"],
            "known_substrate_id": known_sub_id,
            "matching_layer": layer,
            "similarity": sim,
        }
        candidates.append(candidate)

    # Deduplicate by EC number: keep best (lowest layer, highest similarity)
    seen_ec: dict[str, dict] = {}
    for c in candidates:
        ec = c["ec_number"]
        if ec not in seen_ec:
            seen_ec[ec] = c
        else:
            existing = seen_ec[ec]
            if (c["matching_layer"], -c["similarity"]["overall"]) < \
               (existing["matching_layer"], -existing["similarity"]["overall"]):
                seen_ec[ec] = c

    deduped = list(seen_ec.values())

    # Sort: layer ascending, similarity descending
    deduped.sort(key=lambda c: (c["matching_layer"], -c["similarity"]["overall"]))

    return deduped[:max_candidates]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_cross_substrate.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/analyze/cross_substrate.py pipeline/tests/test_cross_substrate.py
git commit -m "feat: add cross-substrate enzyme matching (Ring 4)"
```

---

## Chunk 3: Gap Analysis Orchestrator + Pipeline Integration

### Task 5: Gap Analysis Orchestrator

**Files:**
- Create: `pipeline/analyze/gap_analysis.py`
- Create: `pipeline/tests/test_gap_analysis.py`

- [ ] **Step 1: Write failing tests**

Create `pipeline/tests/test_gap_analysis.py`:

```python
"""Tests for the Ring 4 gap analysis orchestrator."""

from pipeline.analyze.gap_analysis import run_gap_analysis


def _compound(id, type, carbons, stereocenters, modifications=None):
    return {
        "id": id, "type": type, "carbons": carbons,
        "stereocenters": stereocenters, "modifications": modifications,
    }


def _reaction(id, rtype, substrates, products, ec=None, enzyme_name=None):
    r = {
        "id": id, "reaction_type": rtype, "substrates": substrates,
        "products": products, "evidence_tier": "hypothetical" if not ec else "validated",
        "evidence_criteria": [], "yield": None, "cofactor_burden": 0.0,
        "cost_score": 0.5,
    }
    if ec:
        r["ec_number"] = ec
        r["enzyme_name"] = enzyme_name
    return r


def test_direct_coverage():
    """Reaction with ec_number gets enzyme_coverage='direct'."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"], ec="5.1.3.1")]
    enriched, meta = run_gap_analysis(compounds, reactions)
    assert enriched[0]["enzyme_coverage"] == "direct"
    assert enriched[0]["engineerability_score"] == 0.0


def test_no_coverage():
    """Reaction without enzyme data and no candidates gets coverage='none'."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"])]
    enriched, meta = run_gap_analysis(compounds, reactions)
    assert enriched[0]["enzyme_coverage"] == "none"
    assert enriched[0]["engineerability_score"] == 1.0


def test_cross_substrate_coverage():
    """Gap with a cross-substrate candidate gets coverage='cross_substrate'."""
    compounds = [
        _compound("A", "aldose", 6, ["R", "S", "R", "R"]),
        _compound("B", "aldose", 6, ["S", "S", "R", "R"]),
        _compound("C", "aldose", 6, ["R", "R", "R", "R"]),
        _compound("D", "aldose", 6, ["S", "R", "R", "R"]),
    ]
    reactions = [
        _reaction("GAP", "epimerization", ["A"], ["B"]),            # no enzyme
        _reaction("KNOWN", "epimerization", ["C"], ["D"], ec="5.1.3.1"),  # has enzyme
    ]
    enriched, meta = run_gap_analysis(compounds, reactions)
    gap_rxn = next(r for r in enriched if r["id"] == "GAP")
    assert gap_rxn["enzyme_coverage"] == "cross_substrate"
    assert len(gap_rxn["cross_substrate_candidates"]) >= 1
    assert 0.0 < gap_rxn["engineerability_score"] < 1.0


def test_all_reactions_get_ring4_fields():
    """Every reaction gets all Ring 4 fields after gap analysis."""
    compounds = [_compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"])]
    reactions = [_reaction("R1", "epimerization", ["A"], ["B"])]
    enriched, _ = run_gap_analysis(compounds, reactions)
    r = enriched[0]
    assert "enzyme_coverage" in r
    assert "cross_substrate_candidates" in r
    assert "ec_family_size" in r
    assert "engineerability_score" in r
    assert "engineerability_components" in r


def test_metadata_counts():
    """Metadata contains correct coverage counts."""
    compounds = [
        _compound("A", "aldose", 6, ["R"]), _compound("B", "aldose", 6, ["S"]),
        _compound("C", "aldose", 6, ["R", "S"]), _compound("D", "aldose", 6, ["S", "S"]),
    ]
    reactions = [
        _reaction("R1", "epimerization", ["A"], ["B"], ec="5.1.3.1"),
        _reaction("R2", "epimerization", ["C"], ["D"]),
    ]
    _, meta = run_gap_analysis(compounds, reactions)
    assert meta["reactions_analyzed"] == 2
    assert meta["coverage_direct"] == 1
    assert meta["coverage_none"] + meta["coverage_cross_substrate"] + meta["coverage_family_only"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pipeline/tests/test_gap_analysis.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `gap_analysis.py`**

Create `pipeline/analyze/gap_analysis.py`:

```python
"""Ring 4 orchestrator: classify enzyme coverage and compute engineerability.

Main entry point for the enzyme gap analysis pipeline stage.
Reads all compounds and reactions, enriches each reaction with:
- enzyme_coverage classification
- cross_substrate_candidates list
- engineerability_score and components
"""

from pipeline.analyze.cross_substrate import find_candidates
from pipeline.analyze.engineerability import compute_score
from pipeline.analyze.enzyme_index import build_enzyme_index


def run_gap_analysis(
    compounds: list[dict],
    reactions: list[dict],
    enzyme_index: dict | None = None,
) -> tuple[list[dict], dict]:
    """Run Ring 4 gap analysis on all reactions.

    Args:
        compounds: All compound dicts from the pipeline.
        reactions: All reaction dicts (may include Ring 2 annotations).
        enzyme_index: Pre-built enzyme index. If None, builds from reactions.

    Returns:
        Tuple of (enriched_reactions, metadata_dict).
        enriched_reactions: Copy of reactions with Ring 4 fields added.
        metadata_dict: Summary statistics for pipeline_metadata.json.
    """
    compound_map = {c["id"]: c for c in compounds}

    if enzyme_index is None:
        enzyme_index = build_enzyme_index(reactions)

    # Counters for metadata
    counts = {
        "reactions_analyzed": 0,
        "coverage_direct": 0,
        "coverage_cross_substrate": 0,
        "coverage_family_only": 0,
        "coverage_none": 0,
    }
    total_score = 0.0

    enriched = []
    for rxn in reactions:
        counts["reactions_analyzed"] += 1
        rxn = dict(rxn)  # shallow copy to avoid mutating original

        # Classify coverage
        if rxn.get("ec_number"):
            # Direct enzyme match from Ring 2
            rxn["enzyme_coverage"] = "direct"
            rxn["cross_substrate_candidates"] = []
            rxn["ec_family_size"] = None
            score, components = compute_score(
                "direct", 1.0, None, False, num_candidates=0
            )
            counts["coverage_direct"] += 1
        else:
            # Find cross-substrate candidates
            candidates = find_candidates(
                rxn, reactions, compound_map,
                enzyme_index=enzyme_index,
            )

            if candidates:
                best = candidates[0]
                best_layer = best["matching_layer"]

                if best_layer <= 2:
                    rxn["enzyme_coverage"] = "cross_substrate"
                    coverage_level = f"cross_substrate_l{best_layer}"
                    counts["coverage_cross_substrate"] += 1
                else:
                    rxn["enzyme_coverage"] = "family_only"
                    coverage_level = "family_only"
                    counts["coverage_family_only"] += 1

                # Look up EC family size
                best_ec = best.get("ec_number", "")
                ec_entry = enzyme_index.get(best_ec, {})
                ec_family_size = ec_entry.get("family_size")
                has_pdb = (ec_entry.get("pdb_count") or 0) > 0

                rxn["cross_substrate_candidates"] = candidates
                rxn["ec_family_size"] = ec_family_size

                score, components = compute_score(
                    coverage_level,
                    best["similarity"]["overall"],
                    ec_family_size,
                    has_pdb,
                    num_candidates=len(candidates),
                )
            else:
                rxn["enzyme_coverage"] = "none"
                rxn["cross_substrate_candidates"] = []
                rxn["ec_family_size"] = None
                score, components = compute_score(
                    "none", 0.0, None, False, num_candidates=0
                )
                counts["coverage_none"] += 1

        rxn["engineerability_score"] = score
        rxn["engineerability_components"] = components
        total_score += score
        enriched.append(rxn)

    n = counts["reactions_analyzed"]
    metadata = {
        **counts,
        "avg_engineerability_score": round(total_score / n, 4) if n > 0 else 0.0,
        "ec_families_indexed": len(enzyme_index),
    }

    return enriched, metadata
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_gap_analysis.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/analyze/gap_analysis.py pipeline/tests/test_gap_analysis.py
git commit -m "feat: add gap analysis orchestrator (Ring 4)"
```

---

### Task 6: Pipeline Integration

**Files:**
- Modify: `pipeline/run_pipeline.py`
- Modify: `pipeline/reactions/score.py`

- [ ] **Step 1: Add `compute_combined_score` to `score.py`**

Add to the end of `pipeline/reactions/score.py`:

```python
def compute_combined_score(
    cost_score: float,
    engineerability_score: float,
    alpha: float = 0.5,
) -> float:
    """Compute combined cost + engineerability score.

    Args:
        cost_score: Biochemical cost score (0.0-1.6 range).
        engineerability_score: Engineering feasibility (0.0-1.0 range).
        alpha: Weight for cost_score. 1.0 = cost only, 0.0 = engineerability only.

    Returns:
        Weighted blend of both scores.
    """
    return alpha * cost_score + (1.0 - alpha) * engineerability_score
```

- [ ] **Step 2: Wire Ring 4 into `run_pipeline.py`**

Add the import near the top of `run_pipeline.py` (after existing imports):

```python
from pipeline.analyze.gap_analysis import run_gap_analysis
from pipeline.analyze.enzyme_index import build_enzyme_index
```

Add Ring 4 steps after the Ring 2 block (after line 273 `print("\n=== Ring 2 complete ===")`) and before `# Write output files`:

```python
    # === Ring 4: Enzyme Gap Analysis ===
    print("\n=== Ring 4: Enzyme Gap Analysis ===")

    # Step G1: Build enzyme index
    print("\n[G1] Building enzyme index...")
    enzyme_index = build_enzyme_index(all_reactions)
    print(f"  -> {len(enzyme_index)} EC families indexed")

    # Step G2: Run gap analysis
    print("\n[G2] Running gap analysis...")
    all_reactions, gap_metadata = run_gap_analysis(
        all_compounds, all_reactions, enzyme_index=enzyme_index
    )
    print(f"  -> {gap_metadata['reactions_analyzed']} reactions analyzed")
    print(f"  -> {gap_metadata['coverage_direct']} direct enzyme matches")
    print(f"  -> {gap_metadata['coverage_cross_substrate']} cross-substrate candidates")
    print(f"  -> {gap_metadata['coverage_family_only']} EC family only")
    print(f"  -> {gap_metadata['coverage_none']} no coverage")
    print(f"  -> avg engineerability: {gap_metadata['avg_engineerability_score']:.4f}")

    print("\n=== Ring 4 complete ===")
```

Add enzyme_index.json export in the `# Write output files` block:

```python
    # Export enzyme index
    enzyme_index_path = os.path.join(OUTPUT_DIR, "enzyme_index.json")
    with open(enzyme_index_path, "w") as f:
        json.dump(enzyme_index, f, indent=2)
    print(f"  -> {enzyme_index_path}")
```

Add `gap_analysis` to the metadata dict:

```python
        "gap_analysis": gap_metadata,
```

Copy enzyme_index.json to web/data alongside the other files:

```python
        shutil.copy2(enzyme_index_path, os.path.join(web_data_dir, "enzyme_index.json"))
```

- [ ] **Step 3: Run the pipeline to verify integration**

Run: `python -m pipeline.run_pipeline --skip-import`
Expected: Pipeline completes with Ring 4 output. All reactions have engineerability_score.

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest pipeline/tests/ -v`
Expected: ALL PASS (existing 116 tests + new Ring 4 tests)

- [ ] **Step 5: Commit**

```bash
git add pipeline/run_pipeline.py pipeline/reactions/score.py
git commit -m "feat: wire Ring 4 gap analysis into pipeline orchestrator"
```

---

## Chunk 4: TypeScript Types + Pathfinder Integration

### Task 7: TypeScript Type Updates

**Files:**
- Modify: `web/lib/types.ts`
- Modify: `web/lib/graph.ts`

- [ ] **Step 1: Add Ring 4 fields to `Reaction` interface**

In `web/lib/types.ts`, add after the existing optional fields (after line 73 `metadata?: Record<string, unknown>;`):

```typescript
  // Ring 4: Enzyme Gap Analysis (optional, present when Ring 4 has run)
  enzyme_coverage?: "direct" | "cross_substrate" | "family_only" | "none";
  cross_substrate_candidates?: Array<{
    ec_number: string;
    enzyme_name: string;
    organism: string | null;
    uniprot_id: string | null;
    pdb_ids: string[];
    source_reaction_id: string;
    known_substrate_id: string;
    matching_layer: 1 | 2 | 3;
    similarity: {
      overall: number;
      stereocenter_distance: number;
      modification_distance: number;
      carbon_count_distance: number;
      type_distance: number;
    };
  }>;
  ec_family_size?: number | null;
  engineerability_score?: number;
  engineerability_components?: {
    coverage_level: number;
    best_similarity: number;
    family_richness: number;
    structural_data: number;
  };
```

Add new type after `ReactionType`:

```typescript
export type ScoringMode = "cost" | "engineerability" | "combined";
```

- [ ] **Step 2: Update `buildGraph` to support scoring modes**

Replace `web/lib/graph.ts` content:

```typescript
import type { Reaction, ScoringMode } from "./types";

export interface Edge {
  reactionId: string;
  target: string;
  weight: number;
}

export type AdjacencyList = Map<string, Edge[]>;

function getWeight(r: Reaction, mode: ScoringMode, alpha: number): number {
  if (mode === "cost") return r.cost_score;
  if (mode === "engineerability") return r.engineerability_score ?? r.cost_score;
  // combined
  const eng = r.engineerability_score ?? r.cost_score;
  return alpha * r.cost_score + (1 - alpha) * eng;
}

export function buildGraph(
  reactions: Reaction[],
  scoringMode: ScoringMode = "cost",
  alpha: number = 0.5,
): AdjacencyList {
  const adj: AdjacencyList = new Map();
  for (const r of reactions) {
    if (r.substrates.length !== 1 || r.products.length !== 1) continue;
    const source = r.substrates[0];
    const target = r.products[0];
    const weight = getWeight(r, scoringMode, alpha);
    if (!adj.has(source)) adj.set(source, []);
    adj.get(source)!.push({ reactionId: r.id, target, weight });
  }
  return adj;
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd web && npx tsc --noEmit` (or whatever the project's type-check command is)
Expected: No type errors

- [ ] **Step 4: Commit**

```bash
git add web/lib/types.ts web/lib/graph.ts
git commit -m "feat: add Ring 4 types and scoring mode to pathfinder"
```

---

### Task 8: Final Integration Verification

**Files:** None new. This is a verification task.

- [ ] **Step 1: Run full pipeline with --skip-import**

Run: `python -m pipeline.run_pipeline --skip-import`
Expected: Pipeline completes. Ring 4 output shows all reactions analyzed, all classified as "none" (since Ring 2 was skipped), avg engineerability near 1.0.

- [ ] **Step 2: Verify output files**

Run: `python -c "import json; d=json.load(open('pipeline/output/reactions.json')); r=d[0]; print(r.get('enzyme_coverage'), r.get('engineerability_score'))"`
Expected: `none 1.0`

Run: `python -c "import json; d=json.load(open('pipeline/output/enzyme_index.json')); print(len(d))"`
Expected: `0` (no Ring 2 data)

Run: `python -c "import json; d=json.load(open('pipeline/output/pipeline_metadata.json')); print(d.get('gap_analysis'))"`
Expected: Dict with reactions_analyzed, coverage counts, avg score

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest pipeline/tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Spot-check a specific reaction**

Run:
```python
python -c "
import json
rxns = json.load(open('pipeline/output/reactions.json'))
r = next(r for r in rxns if r['id'].startswith('EPI-C6'))
print(f'ID: {r[\"id\"]}')
print(f'Coverage: {r[\"enzyme_coverage\"]}')
print(f'Score: {r[\"engineerability_score\"]}')
print(f'Candidates: {len(r[\"cross_substrate_candidates\"])}')
print(f'Components: {r[\"engineerability_components\"]}')
"
```
Expected: All Ring 4 fields present and populated.

- [ ] **Step 5: Final commit (regenerated output)**

```bash
git add pipeline/output/
git commit -m "chore: regenerate pipeline output with Ring 4 gap analysis"
```
