"""Validate that reactions satisfy mass balance (substrate and product carbon counts match)."""


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
