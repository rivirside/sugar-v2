"""KEGG REST API importer with rate limiting and local caching."""

import logging
import re
import time

import requests

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh

logger = logging.getLogger(__name__)

KEGG_BASE = "https://rest.kegg.jp"
RATE_LIMIT_DELAY = 0.15


def fetch_kegg_compound(kegg_id: str, cache_dir: str, refresh: bool = False) -> dict | None:
    cache_file = f"{kegg_id}.json"
    if not refresh and is_cache_fresh(cache_dir, "kegg", cache_file):
        cached = read_cache(cache_dir, "kegg", cache_file)
        if cached:
            return cached
    try:
        url = f"{KEGG_BASE}/get/{kegg_id}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            result = parse_kegg_compound_entry(resp.text)
            write_cache(cache_dir, "kegg", cache_file, result)
            return result
        elif resp.status_code == 404:
            return None
        else:
            logger.warning("KEGG returned %d for %s", resp.status_code, kegg_id)
            return None
    except Exception as e:
        logger.warning("KEGG fetch failed for %s: %s", kegg_id, e)
        return None


def fetch_kegg_compounds_batch(kegg_ids: list[str], cache_dir: str, refresh: bool = False) -> dict:
    results = {}
    for i, kegg_id in enumerate(kegg_ids):
        result = fetch_kegg_compound(kegg_id, cache_dir, refresh)
        if result:
            results[kegg_id] = result
        if i < len(kegg_ids) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    return results


def fetch_kegg_reaction_links(kegg_ids: list[str], cache_dir: str, refresh: bool = False) -> dict:
    cache_file = "reaction_links.json"
    if not refresh and is_cache_fresh(cache_dir, "kegg", cache_file):
        cached = read_cache(cache_dir, "kegg", cache_file)
        if cached:
            return cached
    all_links = {}
    for kegg_id in kegg_ids:
        try:
            url = f"{KEGG_BASE}/link/reaction/{kegg_id}"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200 and resp.text.strip():
                links = parse_kegg_link_response(resp.text)
                all_links.update(links)
            time.sleep(RATE_LIMIT_DELAY)
        except Exception as e:
            logger.warning("KEGG link fetch failed for %s: %s", kegg_id, e)
    write_cache(cache_dir, "kegg", cache_file, all_links)
    return all_links


def parse_kegg_compound_entry(text: str) -> dict:
    result = {"kegg_id": None, "names": [], "formula": None, "pathways": [], "chebi_id": None, "pubchem_id": None}
    current_field = None
    for line in text.strip().split("\n"):
        if line.startswith("///"):
            break
        if line[:12].strip():
            field = line[:12].strip()
            value = line[12:].strip()
            current_field = field
        else:
            value = line.strip()

        if current_field == "ENTRY":
            match = re.match(r"(\w+)", value)
            if match:
                result["kegg_id"] = match.group(1)
        elif current_field == "NAME":
            for name in value.rstrip(";").split(";"):
                name = name.strip()
                if name:
                    result["names"].append(name)
        elif current_field == "FORMULA":
            result["formula"] = value
        elif current_field == "PATHWAY":
            match = re.match(r"(map\d+)", value)
            if match:
                result["pathways"].append(match.group(1))
        elif current_field == "DBLINKS":
            if value.startswith("ChEBI:"):
                result["chebi_id"] = value.split(":")[1].strip()
            elif value.startswith("PubChem:"):
                result["pubchem_id"] = value.split(":")[1].strip()
    return result


def parse_kegg_link_response(text: str) -> dict:
    links: dict[str, list[str]] = {}
    for line in text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) == 2:
            compound_id = parts[0].replace("cpd:", "")
            reaction_id = parts[1].replace("rn:", "")
            links.setdefault(compound_id, []).append(reaction_id)
    return links
