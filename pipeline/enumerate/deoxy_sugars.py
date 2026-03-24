"""Generate deoxy sugar derivatives from monosaccharides.

Deoxy sugars have one or more hydroxyl groups replaced by hydrogen.
Each deoxy position removes one oxygen from the parent formula.
"""

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
    """Format atom dict back to formula string."""
    order = ["C", "H", "N", "O", "P", "S"]
    parts = []
    for elem in order:
        if elem in atoms and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    for elem in sorted(atoms):
        if elem not in order and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    return "".join(parts)


def _deoxy_formula(parent_formula: str, n_deoxy: int) -> str:
    """Compute formula after removing n hydroxyl groups (replacing -OH with -H).

    Each deoxy position: net -1O (hydroxyl replaced by hydrogen).
    """
    atoms = _parse_formula(parent_formula)
    atoms["O"] = atoms.get("O", 0) - n_deoxy
    return _format_formula(atoms)


def _deoxy_stereocenters(parent: dict, deoxy_positions: list[int]) -> list[str]:
    """Compute stereocenters for a deoxy sugar.

    If a deoxy position was a stereocenter, it may be lost (carbon
    with two H's is not a stereocenter). For simplicity, we keep
    the parent's stereocenters list and note that the deoxy position's
    stereocenter is no longer meaningful in metadata.
    """
    # Stereocenters in our model are indexed differently than carbon positions.
    # For aldoses: stereocenters start at C2. So stereocenter index i corresponds
    # to carbon position i+2. For ketoses: stereocenters start at C3, so index i
    # corresponds to carbon position i+3.
    #
    # A deoxy at position p removes the stereocenter at that carbon if it was one.
    parent_stereo = list(parent["stereocenters"])
    parent_type = parent["type"]

    stereo_offset = 2 if parent_type == "aldose" else 3

    result = []
    for i, sc in enumerate(parent_stereo):
        carbon_pos = i + stereo_offset
        if carbon_pos not in deoxy_positions:
            result.append(sc)
        # If deoxy position was a stereocenter, we skip it (no longer chiral)

    return result


# Curated deoxy sugars: (parent_id, deoxy_positions, id, name, aliases)
CURATED_DEOXY_SUGARS = [
    ("L-GAL", [6], "L-FUC", "L-Fucose", ["6-deoxy-L-galactose"]),
    ("L-MAN", [6], "L-RHA", "L-Rhamnose", ["6-deoxy-L-mannose"]),
    ("D-RIB", [2], "D-dRIB", "2-Deoxy-D-ribose", ["deoxyribose"]),
    ("D-GLC", [2], "D-2dGLC", "2-Deoxy-D-glucose", []),
    ("D-GAL", [6], "D-FUC", "D-Fucose", ["6-deoxy-D-galactose"]),
    ("D-MAN", [6], "D-RHA", "D-Rhamnose", ["6-deoxy-D-mannose"]),
    ("L-GLC", [2], "L-2dGLC", "2-Deoxy-L-glucose", []),
    ("D-GLC", [6], "D-QUI", "D-Quinovose", ["6-deoxy-D-glucose"]),
]


def generate_deoxy_sugars(compounds: list[dict]) -> list[dict]:
    """Generate deoxy sugar derivatives from monosaccharides.

    Uses a curated list of biologically important deoxy sugars.
    Each compound is derived from a parent monosaccharide by replacing
    one or more hydroxyl groups with hydrogen.

    Args:
        compounds: list of monosaccharide compounds

    Returns:
        list of deoxy sugar compound dicts
    """
    compound_map = {c["id"]: c for c in compounds}
    deoxy_sugars: list[dict] = []

    for parent_id, deoxy_positions, compound_id, name, aliases in CURATED_DEOXY_SUGARS:
        parent = compound_map.get(parent_id)
        if parent is None:
            raise ValueError(
                f"Deoxy sugar parent '{parent_id}' not found in compounds"
            )

        modifications = [{"type": "deoxy", "position": p} for p in deoxy_positions]
        stereocenters = _deoxy_stereocenters(parent, deoxy_positions)

        compound = {
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "deoxy_sugar",
            "carbons": parent["carbons"],
            "chirality": parent["chirality"],
            "formula": _deoxy_formula(parent["formula"], len(deoxy_positions)),
            "stereocenters": stereocenters,
            "modifications": modifications,
            "parent_monosaccharide": parent_id,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {
                "deoxy_positions": list(deoxy_positions),
                "parent_type": parent["type"],
            },
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        }
        deoxy_sugars.append(compound)

    return deoxy_sugars
