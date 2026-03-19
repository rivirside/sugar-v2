"""RHEA database importer via SPARQL endpoint."""

import logging
from SPARQLWrapper import SPARQLWrapper, JSON
from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh

logger = logging.getLogger(__name__)
RHEA_SPARQL_ENDPOINT = "https://sparql.rhea-db.org/sparql"
BATCH_SIZE = 50


def fetch_rhea_reactions(chebi_ids: list[str], cache_dir: str, refresh: bool = False) -> list[dict]:
    cache_file = "query_results.json"
    if not refresh and is_cache_fresh(cache_dir, "rhea", cache_file):
        cached = read_cache(cache_dir, "rhea", cache_file)
        if cached:
            logger.info("Using cached RHEA results (%d reactions)", len(cached))
            return cached

    all_reactions = []
    for i in range(0, len(chebi_ids), BATCH_SIZE):
        batch = chebi_ids[i:i + BATCH_SIZE]
        logger.info("Querying RHEA batch %d/%d (%d IDs)...", i // BATCH_SIZE + 1, (len(chebi_ids) + BATCH_SIZE - 1) // BATCH_SIZE, len(batch))
        try:
            results = _query_rhea_batch(batch)
            reactions = parse_sparql_results(results)
            all_reactions.extend(reactions)
        except Exception as e:
            logger.warning("RHEA SPARQL query failed for batch starting at %d: %s", i, e)

    seen = set()
    unique = []
    for r in all_reactions:
        if r["rhea_id"] not in seen:
            seen.add(r["rhea_id"])
            unique.append(r)

    write_cache(cache_dir, "rhea", cache_file, unique)
    logger.info("Fetched %d unique RHEA reactions", len(unique))
    return unique


def _query_rhea_batch(chebi_ids: list[str]) -> dict:
    values = " ".join(f"<http://purl.obolibrary.org/obo/{cid.replace(':', '_')}>" for cid in chebi_ids)
    query = f"""
    PREFIX rh: <http://rdf.rhea-db.org/>
    SELECT DISTINCT ?rheaId ?equation ?ec ?substrateId ?productId ?direction
    WHERE {{
        VALUES ?chebi {{ {values} }}
        ?rhea rh:equation ?equation .
        ?rhea rh:id ?rheaId .
        OPTIONAL {{ ?rhea rh:ec ?ec . }}
        ?rhea rh:side ?subSide .
        ?subSide rh:contains ?subPart .
        ?subPart rh:compound ?subCompound .
        ?subCompound rh:chebi ?substrateId .
        ?rhea rh:side ?prodSide .
        FILTER(?subSide != ?prodSide)
        ?prodSide rh:contains ?prodPart .
        ?prodPart rh:compound ?prodCompound .
        ?prodCompound rh:chebi ?productId .
        FILTER(?subCompound = ?chebi || ?prodCompound = ?chebi)
        OPTIONAL {{ ?rhea rh:direction ?direction . }}
    }}
    """
    sparql = SPARQLWrapper(RHEA_SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def parse_sparql_results(results: dict) -> list[dict]:
    reactions_map: dict[str, dict] = {}
    for binding in results.get("results", {}).get("bindings", []):
        rhea_id = f"RHEA:{binding['rheaId']['value']}"
        ec = binding.get("ec", {}).get("value")
        equation = binding.get("equation", {}).get("value", "")
        sub_chebi = _uri_to_chebi(binding.get("substrateId", {}).get("value", ""))
        prod_chebi = _uri_to_chebi(binding.get("productId", {}).get("value", ""))

        if rhea_id not in reactions_map:
            reactions_map[rhea_id] = {"rhea_id": rhea_id, "ec_number": ec, "equation": equation, "substrate_chebi_ids": set(), "product_chebi_ids": set(), "pmids": []}
        if sub_chebi:
            reactions_map[rhea_id]["substrate_chebi_ids"].add(sub_chebi)
        if prod_chebi:
            reactions_map[rhea_id]["product_chebi_ids"].add(prod_chebi)

    reactions = []
    for r in reactions_map.values():
        r["substrate_chebi_ids"] = sorted(r["substrate_chebi_ids"])
        r["product_chebi_ids"] = sorted(r["product_chebi_ids"])
        reactions.append(r)
    return reactions


def classify_reaction_participants(reaction: dict, known_chebi_ids: set[str]) -> dict:
    return {
        "known_substrates": [cid for cid in reaction["substrate_chebi_ids"] if cid in known_chebi_ids],
        "unknown_substrates": [cid for cid in reaction["substrate_chebi_ids"] if cid not in known_chebi_ids],
        "known_products": [cid for cid in reaction["product_chebi_ids"] if cid in known_chebi_ids],
        "unknown_products": [cid for cid in reaction["product_chebi_ids"] if cid not in known_chebi_ids],
    }


def _uri_to_chebi(uri: str) -> str | None:
    if "CHEBI_" in uri:
        return f"CHEBI:{uri.split('CHEBI_')[-1]}"
    return None
