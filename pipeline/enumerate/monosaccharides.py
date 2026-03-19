"""Enumerate all monosaccharide stereoisomers from C2-C7."""

from itertools import product as cartesian_product
import json
import os

# Load name mapping
_NAME_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "name_mapping.json")
_NAME_MAP: dict = {}


def _load_name_map() -> dict:
    global _NAME_MAP
    if not _NAME_MAP and os.path.exists(_NAME_MAP_PATH):
        with open(_NAME_MAP_PATH) as f:
            _NAME_MAP = json.load(f)
    return _NAME_MAP


def _chirality(stereocenters: list[str], sugar_type: str) -> str:
    """Determine D/L chirality from the highest-numbered stereocenter.

    D-series: last stereocenter is 'R'
    L-series: last stereocenter is 'S'
    Achiral: no stereocenters
    """
    if not stereocenters:
        return "achiral"
    return "D" if stereocenters[-1] == "R" else "L"


def _resolve_name(stereocenters: list[str], sugar_type: str, carbons: int) -> tuple[str, str, list[str]]:
    """Look up human-readable name from stereocenters, return (id, name, aliases).

    Falls back to systematic ID if not in name mapping.
    """
    name_map = _load_name_map()
    key = f"{sugar_type}-C{carbons}-{''.join(stereocenters)}" if stereocenters else f"{sugar_type}-C{carbons}"

    if key in name_map:
        entry = name_map[key]
        return entry["id"], entry["name"], entry.get("aliases", [])

    # Systematic fallback
    chirality = _chirality(stereocenters, sugar_type)
    prefix = "ALDO" if sugar_type == "aldose" else "KETO"
    config = "".join(stereocenters) if stereocenters else "ACHIRAL"
    sys_id = f"{prefix}-C{carbons}-{config}"
    carbon_name = {3: "tri", 4: "tetr", 5: "pent", 6: "hex", 7: "hept"}.get(carbons, f"C{carbons}")
    sys_name = f"{chirality}-{prefix.lower()}{carbon_name}ose"
    return sys_id, sys_name, []


def _molecular_formula(carbons: int, sugar_type: str) -> str:
    """Compute molecular formula for an open-chain monosaccharide.

    Aldose CnH(2n)On: e.g., C6H12O6
    Ketose CnH(2n)On: same formula
    """
    h = 2 * carbons
    o = carbons
    return f"C{carbons}H{h}O{o}"


def enumerate_aldoses(carbons: int) -> list[dict]:
    """Generate all aldose stereoisomers for a given carbon count.

    Aldoses have the carbonyl at C1. Chiral centers are C2 through C(n-1).
    Number of chiral centers = carbons - 2 (for C >= 3), 0 for C2.
    """
    if carbons < 2 or carbons > 7:
        raise ValueError(f"Carbon count must be 2-7, got {carbons}")

    n_chiral = max(0, carbons - 2)

    if n_chiral == 0:
        # C2: glycolaldehyde, no stereocenters
        compound_id, name, aliases = _resolve_name([], "aldose", carbons)
        return [{
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "aldose",
            "carbons": carbons,
            "chirality": "achiral",
            "formula": _molecular_formula(carbons, "aldose"),
            "stereocenters": [],
            "modifications": None,
            "parent_monosaccharide": None,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {},
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        }]

    compounds = []
    for config in cartesian_product("RS", repeat=n_chiral):
        stereocenters = list(config)
        chirality = _chirality(stereocenters, "aldose")
        compound_id, name, aliases = _resolve_name(stereocenters, "aldose", carbons)

        compounds.append({
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "aldose",
            "carbons": carbons,
            "chirality": chirality,
            "formula": _molecular_formula(carbons, "aldose"),
            "stereocenters": stereocenters,
            "modifications": None,
            "parent_monosaccharide": None,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {},
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        })

    return compounds


def enumerate_ketoses(carbons: int) -> list[dict]:
    """Generate all ketose stereoisomers for a given carbon count.

    Ketoses have the carbonyl at C2. Chiral centers are C3 through C(n-1).
    Number of chiral centers = carbons - 3 (for C >= 4), 0 for C3.
    """
    if carbons < 3 or carbons > 7:
        raise ValueError(f"Carbon count must be 3-7 for ketoses, got {carbons}")

    n_chiral = max(0, carbons - 3)

    if n_chiral == 0:
        # C3: dihydroxyacetone, no stereocenters
        compound_id, name, aliases = _resolve_name([], "ketose", carbons)
        return [{
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "ketose",
            "carbons": carbons,
            "chirality": "achiral",
            "formula": _molecular_formula(carbons, "ketose"),
            "stereocenters": [],
            "modifications": None,
            "parent_monosaccharide": None,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {},
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        }]

    compounds = []
    for config in cartesian_product("RS", repeat=n_chiral):
        stereocenters = list(config)
        chirality = _chirality(stereocenters, "ketose")
        compound_id, name, aliases = _resolve_name(stereocenters, "ketose", carbons)

        compounds.append({
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "ketose",
            "carbons": carbons,
            "chirality": chirality,
            "formula": _molecular_formula(carbons, "ketose"),
            "stereocenters": stereocenters,
            "modifications": None,
            "parent_monosaccharide": None,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {},
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        })

    return compounds


def enumerate_all_monosaccharides() -> list[dict]:
    """Generate all C2-C7 monosaccharides (aldoses + ketoses).

    Returns 63 aldoses + 31 ketoses = 94 total.
    """
    compounds = []
    for c in range(2, 8):
        compounds.extend(enumerate_aldoses(c))
    for c in range(3, 8):
        compounds.extend(enumerate_ketoses(c))
    return compounds
