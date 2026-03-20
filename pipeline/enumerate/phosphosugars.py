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
