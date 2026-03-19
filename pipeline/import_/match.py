"""Multi-strategy compound matching engine.

Strategies (applied in order, first match wins):
1. Override pin — manual override forces a specific match
2. Override reject — manual override blocks a match
3. Exact name match (confidence: high)
4. Synonym/alias match (confidence: high)
5. Formula unique match (confidence: medium) — only if exactly one candidate shares the formula
6. Fuzzy name match (confidence: low) — flagged for review, not auto-applied
"""

import json
import os
from thefuzz import fuzz


def match_compound(compound: dict, chebi_index: dict, overrides: dict | None = None) -> dict:
    compound_id = compound["id"]
    no_match = _no_match_result()

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

    key = compound["name"].lower()
    if key in chebi_index:
        return _result_from_entry(chebi_index[key], "high", "exact_name")

    for alias in compound.get("aliases", []):
        alias_key = alias.lower()
        if alias_key in chebi_index:
            return _result_from_entry(chebi_index[alias_key], "high", "alias")

    formula = compound.get("formula")
    if formula:
        candidates = _find_by_formula(chebi_index, formula)
        if len(candidates) == 1:
            return _result_from_entry(candidates[0], "medium", "formula_unique")

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


def match_all_compounds(compounds: list[dict], chebi_index: dict, overrides: dict | None = None) -> dict:
    report = {}
    for compound in compounds:
        report[compound["id"]] = match_compound(compound, chebi_index, overrides)
    return report


def load_overrides(overrides_path: str) -> dict:
    if not os.path.exists(overrides_path):
        return {}
    with open(overrides_path) as f:
        return json.load(f)


def _no_match_result() -> dict:
    return {"chebi_id": None, "kegg_id": None, "pubchem_id": None, "inchi": None, "smiles": None, "confidence": None, "strategy": "no_match", "chebi_name": None}


def _result_from_entry(entry: dict, confidence: str, strategy: str) -> dict:
    return {"chebi_id": entry.get("chebi_id"), "kegg_id": entry.get("kegg_id"), "pubchem_id": entry.get("pubchem_id"), "inchi": entry.get("inchi"), "smiles": entry.get("smiles"), "confidence": confidence, "strategy": strategy, "chebi_name": entry.get("name")}


def _find_by_formula(chebi_index: dict, formula: str) -> list[dict]:
    seen_ids = set()
    results = []
    for entry in chebi_index.values():
        chebi_id = entry.get("chebi_id")
        if chebi_id and chebi_id not in seen_ids and entry.get("formula") == formula:
            seen_ids.add(chebi_id)
            results.append(entry)
    return results
