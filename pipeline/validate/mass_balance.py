"""Validate that reactions satisfy mass balance (substrate and product carbon counts match)."""

import re


def check_mass_balance(reactions: list[dict], compound_map: dict) -> list[str]:
    """Check that each reaction's substrates and products have matching carbon counts.

    For epimerization and isomerization reactions, the total carbons in substrates
    must equal the total carbons in products. Reduction reactions are also checked
    for carbon count consistency.

    Args:
        reactions: list of reaction dicts with 'substrates', 'products', 'reaction_type'
        compound_map: dict mapping compound ID -> compound dict with 'carbons' field

    Returns a list of error strings for reactions that fail mass balance.
    An empty list means all reactions pass.
    """
    errors = []

    for rxn in reactions:
        rxn_id = rxn.get("id", "UNKNOWN")
        substrates = rxn.get("substrates", [])
        products = rxn.get("products", [])

        # Compute total carbons for substrates and products
        substrate_carbons = []
        for sid in substrates:
            compound = compound_map.get(sid)
            if compound is None:
                errors.append(
                    f"Reaction {rxn_id}: substrate '{sid}' not found in compound map"
                )
                substrate_carbons.append(None)
            else:
                substrate_carbons.append(compound.get("carbons"))

        product_carbons = []
        for pid in products:
            compound = compound_map.get(pid)
            if compound is None:
                errors.append(
                    f"Reaction {rxn_id}: product '{pid}' not found in compound map"
                )
                product_carbons.append(None)
            else:
                product_carbons.append(compound.get("carbons"))

        # Skip if any compound is missing (already logged as error)
        if None in substrate_carbons or None in product_carbons:
            continue

        total_substrate = sum(substrate_carbons)
        total_product = sum(product_carbons)

        if total_substrate != total_product:
            errors.append(
                f"Reaction {rxn_id}: carbon mismatch "
                f"(substrates={total_substrate}, products={total_product})"
            )

    return errors


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
    """Check formula-level balance for imported reactions. Returns warnings list."""
    warnings = []
    for rxn in reactions:
        rxn_id = rxn.get("id", "UNKNOWN")
        sub_atoms: dict[str, int] = {}
        prod_atoms: dict[str, int] = {}
        skip = False

        for sid in rxn.get("substrates", []):
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

        for pid in rxn.get("products", []):
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

        all_elements = set(sub_atoms.keys()) | set(prod_atoms.keys())
        imbalanced = []
        for elem in sorted(all_elements):
            sub_count = sub_atoms.get(elem, 0)
            prod_count = prod_atoms.get(elem, 0)
            if sub_count != prod_count:
                imbalanced.append(f"{elem}: {sub_count} vs {prod_count}")

        if imbalanced:
            warnings.append(f"Reaction {rxn_id}: formula imbalance [{', '.join(imbalanced)}]")

    return warnings
