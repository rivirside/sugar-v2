"""Detect duplicate compounds based on stereocenters within the same (type, carbons) group."""


def check_duplicates(compounds: list[dict]) -> list[dict]:
    """Check for duplicate compounds in the compound list.

    Duplicates are identified as compounds within the same (type, carbons) group
    that have identical stereocenters.

    Returns a list of (compound, duplicate) pairs describing each duplicate found.
    An empty list means no duplicates exist.
    """
    # Group by (type, carbons)
    groups: dict[tuple, list[dict]] = {}
    for c in compounds:
        ctype = c.get("type")
        carbons = c.get("carbons")
        key = (ctype, carbons)
        groups.setdefault(key, []).append(c)

    duplicates = []
    for (ctype, carbons), group in groups.items():
        # Track seen stereocenters within the group
        seen: dict[tuple, dict] = {}
        for c in group:
            stereocenters_key = tuple(c.get("stereocenters", []))
            if stereocenters_key in seen:
                duplicates.append({
                    "original": seen[stereocenters_key],
                    "duplicate": c,
                    "type": ctype,
                    "carbons": carbons,
                    "stereocenters": list(stereocenters_key),
                })
            else:
                seen[stereocenters_key] = c

    return duplicates
