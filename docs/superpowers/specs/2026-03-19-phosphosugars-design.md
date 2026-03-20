# Phosphosugars Design Spec (Ring 3, Issue #18)

## Overview

Add phosphorylated sugar derivatives to the SUGAR pipeline. Phosphosugars are the first Ring 3 derivative class, extending the existing 135 compounds and 748 reactions with ~144 new compounds and ~1,240 new reactions.

## Scope

### Hybrid Enumeration Strategy

**Systematic enumeration** of C6 hexoses at biologically valid hydroxyl positions, plus **curated additions** of important phosphosugars from other carbon lengths.

### Systematic Compounds

Generate phosphorylated derivatives from existing C6 monosaccharides:

| Parent class | Count | Positions | Compounds |
|---|---|---|---|
| C6 aldohexoses (mono-P) | 16 stereoisomers | C1, C3, C4, C6 | 64 |
| C6 aldohexoses (bis-P) | 16 stereoisomers | (1,6), (3,6) | 32 |
| C6 ketohexoses (mono-P) | 8 stereoisomers | C1, C3, C4, C6 | 32 |
| C6 ketohexoses (bis-P) | 8 stereoisomers | (1,6) | 8 |

Note: ketohexoses get only (1,6) bisphosphate because (3,6) bisphosphates are not observed in known metabolism. Aldohexoses get both (1,6) and (3,6) because glucose-1,6-bisphosphate and fructose-3,6-bisphosphate-related intermediates exist.
| **Subtotal** | | | **136** |

**C2 is excluded** from phosphorylation — it's the carbonyl carbon in ketoses (chemically invalid) and extremely rare in aldoses. Fructose-2,6-bisphosphate is the sole biologically relevant C2 exception, added as a curated compound.

### Curated Compounds

Biologically important phosphosugars from non-C6 carbon lengths:

| Compound | ID | Parent ID | Carbon | Positions | Pathway |
|---|---|---|---|---|---|
| Glyceraldehyde 3-phosphate | D-GLYC-3P | D-GLYC | C3 | 3 | Glycolysis |
| Dihydroxyacetone phosphate | DHA-1P | DHA | C3 | 1 | Glycolysis |
| Erythrose 4-phosphate | D-ERY-4P | D-ERY | C4 | 4 | PPP |
| Ribose 5-phosphate | D-RIB-5P | D-RIB | C5 | 5 | PPP |
| Ribulose 5-phosphate | D-RBU-5P | D-RBU | C5 | 5 | PPP |
| Xylulose 5-phosphate | D-XLU-5P | D-XLU | C5 | 5 | PPP |
| Sedoheptulose 7-phosphate | D-SED-7P | D-SED | C7 | 7 | PPP |
| Fructose 2,6-bisphosphate | D-FRU-2,6BP | D-FRU | C6 | 2, 6 | Regulatory |

Note: Sedoheptulose (D-altro-2-heptulose, stereocenters SRRR, 4 chiral centers for C7 ketose) has no named entry in `name_mapping.json`. A named entry `"ketose-C7-SRRR": {"id": "D-SED", "name": "D-Sedoheptulose"}` must be added to the mapping so the parent compound gets a human-readable ID before phosphosugar derivation.

**Total: ~144 new compounds.**

## Compound Data Model

```python
{
    "id": "D-GLC-6P",                         # Parent ID + phosphate suffix
    "name": "D-Glucose 6-phosphate",
    "aliases": ["Glucose-6-phosphate", "G6P"],
    "type": "phosphate",
    "carbons": 6,
    "chirality": "D",                          # Inherited from parent
    "formula": "C6H13O9P",                     # Parent + phosphate group
    "stereocenters": ["R", "S", "S", "R"],     # Inherited from parent
    "modifications": [
        {"type": "phosphate", "position": 6}
    ],
    "parent_monosaccharide": "D-GLC",
    "commercial": False,
    "cost_usd_per_kg": None,
    "metadata": {
        "phosphate_positions": [6],
        "parent_type": "aldose",          # Parent's type, used for completeness grouping
        "curated": False
    },
    "chebi_id": None,
    "kegg_id": None,
    "pubchem_id": None,
    "inchi": None,
    "smiles": None
}
```

### ID Convention

**Suffix style** matching biochemistry shorthand:
- Mono-phosphate: `D-GLC-6P`
- Bisphosphate: `D-FRU-1,6BP`
- Curated compounds use the same suffix convention with their parent ID: `D-GLYC-3P` (not `G3P`). Common abbreviations like `G3P`, `DHAP`, `G6P` go in the `aliases` list for searchability.

### Formula Calculation

Phosphate ester bond: sugar-OH + H₃PO₄ → sugar-O-PO₃H₂ + H₂O

- **Mono-phosphate**: parent formula + PO₃H (net: +1P, +3O, +1H)
- **Bisphosphate**: parent formula + 2×PO₃H (net: +2P, +6O, +2H)

Example: D-Glucose (C₆H₁₂O₆) + PO₃H → C₆H₁₃O₉P

### Name Mapping

New entries in `pipeline/data/name_mapping.json` with keys:
- `"phosphate-C6-RSSR-6P"` → `{"id": "D-GLC-6P", "name": "D-Glucose 6-phosphate", "aliases": ["G6P"]}`
- Systematic fallback for unmapped: `"D-GLC-3P"` → `"D-Glucose 3-phosphate"`

~20 new named entries for well-known compounds (G6P, F6P, F16BP, G1P, M6P, G3P, DHAP, R5P, Ru5P, Xu5P, E4P, S7P, F26BP, etc.).

## Reaction Generation

### File: `pipeline/reactions/phosphorylation.py`

Five reaction types:

### 1. Phosphorylation (kinase)

```
Monosaccharide + ATP → Phosphosugar + ADP
```

- One reaction per phosphosugar, linking to its parent monosaccharide
- `reaction_type: "phosphorylation"`
- `cofactor_burden: 1.0` (ATP consumed)
- ID format: `PHOS-C6-D-GLC-6P`
- ~144 reactions

### 2. Dephosphorylation (phosphatase)

```
Phosphosugar → Monosaccharide + Pi
```

- Separate from phosphorylation (distinct enzyme class, not a simple reverse)
- `reaction_type: "dephosphorylation"`
- `cofactor_burden: 0.0`
- ID format: `DEPHOS-C6-D-GLC-6P`
- ~144 reactions

### 3. Mutase (phosphate migration)

```
D-GLC-1P ↔ D-GLC-6P
```

- Between mono-phosphosugars sharing same parent and stereocenters, differing only in phosphate position
- Bidirectional (forward + reverse with `-REV` suffix)
- `reaction_type: "mutase"`
- `cofactor_burden: 0.0`
- ID format: `MUT-C6-D-GLC-1P-6P`
- Count: each parent with 4 mono-P positions has C(4,2) = 6 undirected pairs = 12 directed reactions. 16 aldohexose parents × 12 + 8 ketohexose parents × 12 = **288 directed reactions**

### 4. Phospho-epimerization

```
D-GLC-6P → D-MAN-6P (differ at exactly one stereocenter)
```

- Same logic as existing epimerization, restricted to phosphosugars with matching modification patterns (same phosphate positions)
- Groups by `(parent_type, carbons, phosphate_positions)` — e.g., all aldohexose-6P compounds form one epimerization group
- `reaction_type: "epimerization"`
- `cofactor_burden: 0.0`
- ID format: `EPI-C6-D-GLC-6P-D-MAN-6P`
- Count: aldohexose groups (16 compounds, 4 stereocenters → 32 pairs × 2 directions = 64 per pattern × 6 patterns = 384) + ketohexose groups (8 compounds, 3 stereocenters → 12 pairs × 2 = 24 per pattern × 5 patterns = 120) = **~504 directed reactions**

### 5. Phospho-isomerization

```
D-GLC-6P ↔ D-FRU-6P (aldose-P ↔ ketose-P)
```

- Same stereocenter-dropping logic as existing isomerization, restricted to phosphosugars with matching modification patterns (same phosphate positions)
- `reaction_type: "isomerization"`
- `cofactor_burden: 0.0`
- ID format: `ISO-C6-D-GLC-6P-D-FRU-6P`
- Count: 16 aldohexose-P → 8 ketohexose-P per matching pattern, bidirectional. 4 shared mono-P patterns × 16 × 2 + 1 shared bis-P pattern × 16 × 2 = **~160 directed reactions**

**All reactions start at evidence tier `"hypothetical"`.** Ring 2 enrichment (RHEA/ChEBI) upgrades tiers when database matches are found.

### Reaction Count Summary

| Type | Count (directed) |
|---|---|
| Phosphorylation | ~144 |
| Dephosphorylation | ~144 |
| Mutase | ~288 |
| Phospho-epimerization | ~504 |
| Phospho-isomerization | ~160 |
| **Total** | **~1,240** |

### Reaction ID Helpers

`phosphorylation.py` defines its own ID generation and base-reaction helpers, independent of `pipeline/reactions/generate.py`. Phospho-epimerization and phospho-isomerization reuse the `"epimerization"` and `"isomerization"` reaction_type values but have distinct IDs because compound IDs differ (e.g., `D-GLC-6P` vs `D-GLC`), preventing collisions.

## Pipeline Integration

### `pipeline/run_pipeline.py` Changes

Insert phosphosugar generation after polyols, before validation. Step count increases from 7 to 8:

```
[1/8] Enumerate monosaccharides (94)
[2/8] Generate polyols (41)
[3/8] Generate phosphosugars (~144)              ← NEW
[4/8] Combine all compounds (~279)
[5/8] Validate completeness + duplicates
[6/8] Generate reactions
       - Existing: epimerization, isomerization, reduction (696)
       - New: phosphorylation, dephosphorylation, mutase,
              phospho-epimerization, phospho-isomerization (~1,240)
[7/8] Mass balance check (carbon count)
[8/8] Verify reaction ID uniqueness
[R1]-[R9] Ring 2 import steps unchanged
```

### Validation Updates

**Mass balance** (`check_mass_balance` — carbon count check):
- Phosphorylation/dephosphorylation: substrate and product have the same number of carbons (phosphate doesn't change carbon count). Passes naturally — **no changes needed** to `check_mass_balance`.
- Mutase, phospho-epi, phospho-iso: same carbon count on both sides. Passes naturally.

**Formula balance** (`check_formula_balance`):
- This function currently only runs on Ring 2 imported reactions, not on rule-generated reactions. Rule-generated phosphorylation/dephosphorylation reactions are **not** passed to `check_formula_balance`, so no changes needed.
- Formula correctness is verified in **tests** instead: assert that each phosphosugar's formula equals parent formula + n × PO₃H.

**Completeness** checks — add phosphosugar expected counts to `EXPECTED_COUNTS`:
- Key: `("phosphate", parent_type, carbons, phosphate_positions_tuple)` — must include parent type to distinguish aldose-derived from ketose-derived phosphosugars at the same carbon count
- Formula: same as parent type (aldose/ketose stereoisomer count for that carbon length)
- Example: `("phosphate", "aldose", 6, (6,))` → expected 16; `("phosphate", "ketose", 6, (6,))` → expected 8
- Curated compounds are exempt from completeness checks (they don't form systematic groups)
- The `parent_type` is stored in `metadata` for this purpose: `metadata.parent_type = "aldose"` or `"ketose"`

**Duplicate detection** (`check_duplicates`):
- Currently groups by `(type, carbons)` and checks stereocenter uniqueness. This will produce false positives: D-GLC-1P and D-GLC-6P share type, carbons, and stereocenters.
- **Fix**: extend grouping key to `(type, carbons, modifications_key)` where `modifications_key = tuple(sorted((m["type"], m["position"]) for m in modifications))` for phosphosugars, and `()` for unmodified compounds. This preserves existing behavior for Ring 1 compounds.

## New Files

| File | Purpose |
|---|---|
| `pipeline/enumerate/phosphosugars.py` | Compound enumeration (systematic + curated) |
| `pipeline/reactions/phosphorylation.py` | All 5 phosphosugar reaction types |
| `pipeline/tests/test_phosphosugars.py` | Tests for enumeration + reactions |

## Modified Files

| File | Change |
|---|---|
| `pipeline/run_pipeline.py` | Add phosphosugar generation step, reaction generation calls, update step numbering to `[1/8]`..`[8/8]`, add metadata keys (`phosphosugars`, `phosphorylations`, `dephosphorylations`, `mutases`) |
| `pipeline/data/name_mapping.json` | ~20 new entries for known phosphosugars + sedoheptulose parent entry (`ketose-C7-SRRR`) |
| `pipeline/validate/completeness.py` | Add phosphosugar expected counts with `(type, carbons, phosphate_positions)` grouping |
| `pipeline/validate/duplicates.py` | Extend grouping key to include modifications, preventing false positives |
| `pipeline/reactions/generate.py` | Filter out `type: "phosphate"` compounds from existing `generate_epimerizations`, `generate_isomerizations`, and `generate_reductions` to prevent spurious cross-position reactions (phosphosugars get their own reaction generators in `phosphorylation.py`) |
| `web/lib/types.ts` | Update `modifications` field type from `Record<string, unknown> \| null` to `Array<{type: string; position: number}> \| null` |

## Frontend

`web/lib/types.ts` needs one type change: the `modifications` field type must be updated to `Array<{type: string; position: number}> | null` to match the new data shape. All other frontend code (compound/reaction browsers, pathway finder, network graph) handles new data automatically — the `CompoundType` and `ReactionType` unions already include the needed values.

## Testing

### `pipeline/tests/test_phosphosugars.py`

**Enumeration tests:**
- Correct systematic count: 136 compounds
- Correct curated count: 8 compounds
- Total: 144
- No duplicate IDs
- All have `type: "phosphate"`
- All have non-empty `modifications` list
- All `modifications` entries have valid `type` and `position`
- Formula correctness: phosphate adds expected atoms vs parent
- Every `parent_monosaccharide` exists in the compound list
- Stereocenters inherited correctly from parent

**Reaction tests:**
- Phosphorylation: one per phosphosugar, links to correct parent
- Dephosphorylation: one per phosphosugar, distinct from phosphorylation
- Mutase: only between same-parent, same-stereo, different-position compounds
- Phospho-epimerization: only between phosphosugars differing at exactly one stereocenter with matching modifications
- Phospho-isomerization: only between aldose-P and ketose-P with matching modifications
- All reaction IDs unique
- Mass balance passes for all reactions
- All reactions have evidence tier "hypothetical"

## Ring 2 Enrichment Interaction

No changes to the import pipeline. The existing ChEBI/KEGG/RHEA matching runs on all compounds regardless of type. Phosphosugars like G6P, F6P, F16BP are well-represented in these databases and should match automatically via name/formula matching. This will upgrade evidence tiers on the hypothetical reactions that correspond to real enzymatic steps.

## Expected Final Numbers

| Metric | Before | After |
|---|---|---|
| Compounds | 135 | ~279 |
| Reactions | 748 | ~1,988 |
| Compound types | 3 | 4 |
| Reaction types | 3 (+RHEA) | 6 (+RHEA) |
