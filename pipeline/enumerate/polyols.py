"""Generate polyols by reduction of monosaccharides, with degeneracy detection."""

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


def _canonical_config(stereocenters: list[str]) -> str:
    """Compute canonical config string for degeneracy detection.

    A polyol with CH2OH on both ends can be read from either end.
    We take max(config, reversed(config)) as the canonical key so that
    aldoses whose stereocenters are reverse-complements of each other
    produce the same canonical key and are detected as degenerate.
    """
    config_str = "".join(stereocenters)
    reversed_str = config_str[::-1]
    return max(config_str, reversed_str)


def _polyol_formula(carbons: int) -> str:
    """Molecular formula for a polyol: CnH(2n+2)O(n)."""
    return f"C{carbons}H{2 * carbons + 2}O{carbons}"


def _resolve_polyol_name(carbons: int, canonical: str) -> tuple[str, str, list[str]]:
    """Look up human-readable name from name_mapping, fall back to systematic ID."""
    name_map = _load_name_map()
    key = f"polyol-C{carbons}-{canonical}" if canonical != "ACHIRAL" else f"polyol-C{carbons}-ACHIRAL"

    if key in name_map:
        entry = name_map[key]
        return entry["id"], entry["name"], entry.get("aliases", [])

    # Systematic fallback
    sys_id = f"POLYOL-C{carbons}-{canonical}"
    sys_name = f"C{carbons}-polyol-{canonical}"
    return sys_id, sys_name, []


def _polyol_from_aldose(aldose: dict) -> tuple[str, list[str], bool]:
    """Compute the canonical config key for the polyol produced by reducing an aldose.

    Reducing C1 (CHO -> CH2OH) leaves stereocenters unchanged.
    C2 aldoses and C3 aldoses both produce glycerol-like achiral polyols
    because the two terminal carbons become equivalent CH2OH groups.

    Returns (canonical_key, stereocenters, is_achiral).
    """
    carbons = aldose["carbons"]
    stereocenters = aldose["stereocenters"]

    # C2 aldose: no stereocenters -> achiral ethylene glycol
    # C3 aldose: one stereocenter but molecule is achiral (2 equivalent terminal CH2OH)
    if carbons <= 3:
        return "ACHIRAL", [], True

    canonical = _canonical_config(stereocenters)
    return canonical, stereocenters, False


def _polyol_from_ketose(ketose: dict) -> tuple[str, list[str], bool]:
    """Compute the canonical config key for the polyol produced by reducing a ketose.

    Reducing C2 (C=O -> CHOH) creates a new stereocenter at C2.
    We represent this new center as 'R' (then the normalization handles degeneracy).
    C3 ketoses produce achiral glycerol.

    Returns (canonical_key, stereocenters, is_achiral).
    """
    carbons = ketose["carbons"]
    stereocenters = ketose["stereocenters"]

    # C3 ketose (DHA): reducing C2 gives glycerol (achiral, 2 equivalent terminal CH2OH)
    if carbons == 3:
        return "ACHIRAL", [], True

    # Add new R stereocenter at C2, then remaining ketose centers follow
    new_stereocenters = ["R"] + stereocenters
    canonical = _canonical_config(new_stereocenters)
    return canonical, new_stereocenters, False


def generate_polyols(compounds: list[dict]) -> list[dict]:
    """Generate polyols by reduction of all monosaccharides, with degeneracy detection.

    Aldose reduction: remove C1 carbonyl (CHO -> CH2OH), stereocenters unchanged.
    Ketose reduction: reduce C2 carbonyl, add new 'R' stereocenter at C2.

    Degeneracy is detected by computing a canonical config key:
    canonical = max(config_str, reversed(config_str))

    Degenerate polyols (same canonical key) are merged into one compound,
    recording all parent monosaccharides in metadata.reduction_parents.

    C2 aldoses and C3 aldoses/ketoses produce achiral polyols.
    """
    # Group monosaccharides by (carbons, canonical_key) -> list of parent ids
    groups: dict[tuple, dict] = {}
    # group key -> (canonical, stereocenters, is_achiral, carbons)

    for compound in compounds:
        ctype = compound["type"]
        carbons = compound["carbons"]

        if ctype == "aldose":
            canonical, stereocenters, is_achiral = _polyol_from_aldose(compound)
        elif ctype == "ketose":
            canonical, stereocenters, is_achiral = _polyol_from_ketose(compound)
        else:
            # Skip non-monosaccharides (polyols, etc.)
            continue

        group_key = (carbons, canonical)
        if group_key not in groups:
            groups[group_key] = {
                "canonical": canonical,
                "stereocenters": stereocenters,
                "is_achiral": is_achiral,
                "carbons": carbons,
                "parents": [],
            }
        groups[group_key]["parents"].append(compound["id"])

    # Build polyol compounds from groups
    polyols = []
    for (carbons, canonical), group in groups.items():
        parents = group["parents"]
        primary_parent = parents[0]  # Use first parent as the canonical parent

        if group["is_achiral"]:
            display_canonical = "ACHIRAL"
            stereocenters = []
        else:
            display_canonical = canonical
            stereocenters = group["stereocenters"]

        compound_id, name, aliases = _resolve_polyol_name(carbons, display_canonical)

        polyol = {
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "polyol",
            "carbons": carbons,
            "chirality": "achiral" if group["is_achiral"] else (
                "D" if stereocenters and stereocenters[-1] == "R" else
                "L" if stereocenters else "achiral"
            ),
            "formula": _polyol_formula(carbons),
            "stereocenters": stereocenters,
            "modifications": None,
            "parent_monosaccharide": primary_parent,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {
                "reduction_parents": parents,
                "canonical_config": display_canonical,
            },
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        }
        polyols.append(polyol)

    return polyols
