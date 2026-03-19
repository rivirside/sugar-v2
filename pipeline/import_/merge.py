"""Merge imported data into enumerated compounds and reactions."""

from pipeline.reactions.score import compute_cost_score


def enrich_compound(compound: dict, match: dict) -> dict:
    compound = {**compound}
    compound["chebi_id"] = match.get("chebi_id")
    compound["kegg_id"] = match.get("kegg_id")
    compound["pubchem_id"] = match.get("pubchem_id")
    compound["inchi"] = match.get("inchi")
    compound["smiles"] = match.get("smiles")
    chebi_name = match.get("chebi_name")
    if chebi_name and chebi_name != compound["name"] and chebi_name not in compound["aliases"]:
        compound["aliases"] = compound["aliases"] + [chebi_name]
    return compound


def create_rhea_reaction(rhea_data: dict, chebi_to_compound: dict) -> dict | None:
    substrates = [chebi_to_compound[cid] for cid in rhea_data["substrate_chebi_ids"] if cid in chebi_to_compound]
    products = [chebi_to_compound[cid] for cid in rhea_data["product_chebi_ids"] if cid in chebi_to_compound]
    if not substrates or not products:
        return None
    pmids = rhea_data.get("pmids", [])
    ec_number = rhea_data.get("ec_number")
    evidence_tier = determine_evidence_tier(pmids, ec_number)
    rxn = {
        "id": rhea_data["rhea_id"], "reaction_type": _guess_reaction_type(ec_number),
        "substrates": substrates, "products": products,
        "evidence_tier": evidence_tier, "evidence_criteria": _build_evidence_criteria(rhea_data, evidence_tier),
        "yield": None, "cofactor_burden": 0.0,
        "ec_number": ec_number, "enzyme_name": None, "cofactors": [],
        "pmid": pmids, "rhea_id": rhea_data["rhea_id"],
        "organism": [], "km_mm": None, "kcat_sec": None, "delta_g": None,
        "metadata": {"source": "rhea_import"},
    }
    rxn["cost_score"] = compute_cost_score(rxn)
    return rxn


def determine_evidence_tier(pmids: list, ec_number: str | None) -> str:
    if pmids:
        return "validated"
    return "predicted"


def find_overlapping_reaction(rhea_substrates: list[str], rhea_products: list[str], existing_reactions: list[dict]) -> dict | None:
    if len(rhea_substrates) != 1 or len(rhea_products) != 1:
        return None
    sub, prod = rhea_substrates[0], rhea_products[0]
    for rxn in existing_reactions:
        if rxn["substrates"] == [sub] and rxn["products"] == [prod]:
            return rxn
    return None


def enrich_reaction_with_rhea(existing: dict, rhea_data: dict) -> dict:
    enriched = {**existing}
    enriched["rhea_id"] = rhea_data["rhea_id"]
    enriched["ec_number"] = rhea_data.get("ec_number")
    pmids = rhea_data.get("pmids", [])
    enriched["pmid"] = pmids
    enriched["evidence_tier"] = determine_evidence_tier(pmids, rhea_data.get("ec_number"))
    enriched["evidence_criteria"] = _build_evidence_criteria(rhea_data, enriched["evidence_tier"])
    enriched["cost_score"] = compute_cost_score(enriched)
    return enriched


def _guess_reaction_type(ec_number: str | None) -> str:
    if not ec_number:
        return "isomerization"
    prefix = ec_number.split(".")[0]
    return {"1": "oxidation", "2": "phosphorylation", "3": "hydrolysis", "4": "aldol", "5": "isomerization", "6": "condensation"}.get(prefix, "isomerization")


def _build_evidence_criteria(rhea_data: dict, tier: str) -> list[dict]:
    criteria = [{"source": "rhea", "rhea_id": rhea_data["rhea_id"]}]
    if rhea_data.get("ec_number"):
        criteria.append({"source": "ec", "ec_number": rhea_data["ec_number"]})
    if rhea_data.get("pmids"):
        criteria.append({"source": "pmid", "ids": rhea_data["pmids"]})
    return criteria
