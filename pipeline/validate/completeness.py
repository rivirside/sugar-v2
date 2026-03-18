"""Validate that the compound set is complete (all expected stereoisomers present)."""

# Expected counts: (type, carbons) -> expected number of compounds
EXPECTED_COUNTS: dict[tuple[str, int], int] = {}

# Aldoses C2-C7: number of stereocenters = max(0, carbons - 2)
for _carbons in range(2, 8):
    _n_chiral = max(0, _carbons - 2)
    EXPECTED_COUNTS[("aldose", _carbons)] = 2 ** _n_chiral

# Ketoses C3-C7: number of stereocenters = max(0, carbons - 3)
for _carbons in range(3, 8):
    _n_chiral = max(0, _carbons - 3)
    EXPECTED_COUNTS[("ketose", _carbons)] = 2 ** _n_chiral


def check_completeness(compounds: list[dict]) -> list[str]:
    """Check that all expected monosaccharide stereoisomers are present.

    Returns a list of warning strings describing any missing compounds.
    An empty list means the set is complete.
    """
    # Count by (type, carbons)
    counts: dict[tuple[str, int], int] = {}
    for c in compounds:
        ctype = c.get("type")
        carbons = c.get("carbons")
        if ctype in ("aldose", "ketose") and carbons is not None:
            key = (ctype, carbons)
            counts[key] = counts.get(key, 0) + 1

    warnings = []
    for (ctype, carbons), expected in sorted(EXPECTED_COUNTS.items()):
        actual = counts.get((ctype, carbons), 0)
        if actual != expected:
            warnings.append(
                f"Expected {expected} {ctype}(s) with {carbons} carbons, found {actual}"
            )

    return warnings
