"""Generate amino sugar derivatives from monosaccharides.

Amino sugars have a hydroxyl group replaced by an amino (-NH2) or
N-acetyl (-NHAc) group. Each amino substitution changes the formula:
  -OH -> -NH2: net +1N, -1O, +1H
  -OH -> -NHAc (NHCOCH3): net +1N, +1C, +1H (replace O with NHCOCH3, lose H2O)
"""

import re


def _parse_formula(formula: str) -> dict[str, int]:
    atoms: dict[str, int] = {}
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        if element:
            atoms[element] = atoms.get(element, 0) + count
    return atoms


def _format_formula(atoms: dict[str, int]) -> str:
    order = ["C", "H", "N", "O", "P", "S"]
    parts = []
    for elem in order:
        if elem in atoms and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    for elem in sorted(atoms):
        if elem not in order and atoms[elem] > 0:
            parts.append(f"{elem}{atoms[elem]}" if atoms[elem] > 1 else elem)
    return "".join(parts)


def _amino_formula(parent_formula: str) -> str:
    """Formula for amino sugar: -OH replaced by -NH2 (net +1N, -1O, +1H)."""
    atoms = _parse_formula(parent_formula)
    atoms["N"] = atoms.get("N", 0) + 1
    atoms["O"] = atoms.get("O", 0) - 1
    atoms["H"] = atoms.get("H", 0) + 1
    return _format_formula(atoms)


def _nacetyl_formula(parent_formula: str) -> str:
    """Formula for N-acetyl amino sugar: -OH replaced by -NHCOCH3.

    Net change from parent: +1N, +2C, +3H, keeping same O count.
    (Replace -OH with -NH-CO-CH3: lose 1O+1H, gain 1N+2C+4H+1O = net +1N+2C+3H)
    """
    atoms = _parse_formula(parent_formula)
    atoms["N"] = atoms.get("N", 0) + 1
    atoms["C"] = atoms.get("C", 0) + 2
    atoms["H"] = atoms.get("H", 0) + 3
    return _format_formula(atoms)


# Curated amino sugars: (parent_id, amino_position, is_nacetyl, id, name, aliases)
CURATED_AMINO_SUGARS = [
    ("D-GLC", 2, False, "D-GlcN", "D-Glucosamine", []),
    ("D-GLC", 2, True, "D-GlcNAc", "N-Acetyl-D-glucosamine", ["GlcNAc"]),
    ("D-GAL", 2, False, "D-GalN", "D-Galactosamine", []),
    ("D-GAL", 2, True, "D-GalNAc", "N-Acetyl-D-galactosamine", ["GalNAc"]),
    ("D-MAN", 2, False, "D-ManN", "D-Mannosamine", []),
    ("D-MAN", 2, True, "D-ManNAc", "N-Acetyl-D-mannosamine", ["ManNAc"]),
    ("L-GLC", 2, False, "L-GlcN", "L-Glucosamine", []),
    ("L-GAL", 2, False, "L-GalN", "L-Galactosamine", []),
    ("L-MAN", 2, False, "L-ManN", "L-Mannosamine", []),
]


def generate_amino_sugars(compounds: list[dict]) -> list[dict]:
    """Generate amino sugar derivatives from monosaccharides.

    Uses a curated list of biologically important amino sugars.
    Each compound is derived from a parent monosaccharide by replacing
    a hydroxyl group with an amino or N-acetyl group.

    Args:
        compounds: list of monosaccharide compounds

    Returns:
        list of amino sugar compound dicts
    """
    compound_map = {c["id"]: c for c in compounds}
    amino_sugars: list[dict] = []

    for parent_id, position, is_nacetyl, compound_id, name, aliases in CURATED_AMINO_SUGARS:
        parent = compound_map.get(parent_id)
        if parent is None:
            raise ValueError(
                f"Amino sugar parent '{parent_id}' not found in compounds"
            )

        mod_type = "nacetyl" if is_nacetyl else "amino"
        formula = _nacetyl_formula(parent["formula"]) if is_nacetyl else _amino_formula(parent["formula"])
        modifications = [{"type": mod_type, "position": position}]

        compound = {
            "id": compound_id,
            "name": name,
            "aliases": aliases,
            "type": "amino_sugar",
            "carbons": parent["carbons"],
            "chirality": parent["chirality"],
            "formula": formula,
            "stereocenters": list(parent["stereocenters"]),
            "modifications": modifications,
            "parent_monosaccharide": parent_id,
            "commercial": False,
            "cost_usd_per_kg": None,
            "metadata": {
                "amino_position": position,
                "is_nacetyl": is_nacetyl,
                "parent_type": parent["type"],
            },
            "chebi_id": None,
            "kegg_id": None,
            "pubchem_id": None,
            "inchi": None,
            "smiles": None,
        }
        amino_sugars.append(compound)

    return amino_sugars
