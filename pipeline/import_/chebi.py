"""ChEBI database importer.

Primary: bulk TSV download from ChEBI FTP.
Fallback: REST API per-compound.
Fallback on fallback: log warning and skip.
"""

import csv
import io
import logging
import os
import gzip

import requests

from pipeline.import_.cache import read_cache, write_cache, is_cache_fresh, write_raw_cache, read_raw_cache

logger = logging.getLogger(__name__)

CHEBI_FTP_COMPOUNDS = "https://ftp.ebi.ac.uk/pub/databases/chebi/flat_files/compounds.tsv.gz"
CHEBI_FTP_NAMES = "https://ftp.ebi.ac.uk/pub/databases/chebi/flat_files/names.tsv.gz"
CHEBI_FTP_ACCESSIONS = "https://ftp.ebi.ac.uk/pub/databases/chebi/flat_files/database_accession.tsv.gz"
CHEBI_FTP_STRUCTURES = "https://ftp.ebi.ac.uk/pub/databases/chebi/flat_files/structures.tsv.gz"
CHEBI_REST_BASE = "https://www.ebi.ac.uk/webservices/chebi/2.0"


def fetch_chebi_bulk(cache_dir: str, refresh: bool = False) -> dict:
    """Download and parse ChEBI bulk TSV files. Returns a chebi_index dict."""
    index_cache = read_cache(cache_dir, "chebi", "index.json")
    if index_cache and not refresh and is_cache_fresh(cache_dir, "chebi", "index.json"):
        logger.info("Using cached ChEBI index (%d entries)", len(index_cache))
        return index_cache

    try:
        logger.info("Downloading ChEBI compounds TSV...")
        compounds_data = _download_tsv_gz(CHEBI_FTP_COMPOUNDS)
        logger.info("Downloading ChEBI names TSV...")
        names_data = _download_tsv_gz(CHEBI_FTP_NAMES)
        logger.info("Downloading ChEBI accessions TSV...")
        accessions_data = _download_tsv_gz(CHEBI_FTP_ACCESSIONS)
        logger.info("Downloading ChEBI structures TSV...")
        structures_data = _download_tsv_gz(CHEBI_FTP_STRUCTURES)

        compounds = parse_chebi_compounds_tsv(compounds_data)
        names = parse_chebi_names_tsv(names_data)
        xrefs = parse_chebi_accessions_tsv(accessions_data)
        structures = parse_chebi_structures_tsv(structures_data)
        index = build_chebi_index(compounds, names, xrefs, structures)

        write_cache(cache_dir, "chebi", "index.json", index)
        logger.info("Built ChEBI index with %d entries", len(index))
        return index
    except Exception as e:
        logger.warning("ChEBI bulk download failed: %s. Falling back to cached data.", e)
        if index_cache:
            return index_cache
        return {}


def fetch_chebi_rest(compound_name: str) -> dict | None:
    """Fetch a single compound from ChEBI REST API. Returns entry dict or None."""
    try:
        search_url = f"{CHEBI_REST_BASE}/getLiteEntity?search={compound_name}&searchCategory=ALL&maximumResults=5"
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            return None  # XML parsing not implemented yet
        return None
    except Exception as e:
        logger.warning("ChEBI REST lookup failed for %s: %s", compound_name, e)
        return None


def parse_chebi_compounds_tsv(tsv_content: str) -> dict:
    """Parse ChEBI compounds.tsv. Returns {chebi_numeric_id: {"name": str, "chebi_id": str}}."""
    entries = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        status = row.get("STATUS") or row.get("status_id", "")
        if status not in ("C", "1"):
            continue
        chebi_num_id = (row.get("ID") or row.get("id", "")).strip()
        name = (row.get("NAME") or row.get("name", "")).strip()
        if chebi_num_id and name:
            entries[chebi_num_id] = {"name": name, "chebi_id": f"CHEBI:{chebi_num_id}"}
    return entries


def parse_chebi_names_tsv(tsv_content: str) -> dict:
    """Parse ChEBI names.tsv. Returns {chebi_numeric_id: [synonym1, synonym2, ...]}."""
    names: dict[str, list[str]] = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        compound_id = (row.get("COMPOUND_ID") or row.get("compound_id", "")).strip()
        name = (row.get("NAME") or row.get("name", "")).strip()
        if compound_id and name:
            names.setdefault(compound_id, []).append(name)
    return names


def parse_chebi_accessions_tsv(tsv_content: str) -> dict:
    """Parse ChEBI database_accession.tsv. Returns {chebi_numeric_id: {"kegg_id": str, "pubchem_id": str}}."""
    xrefs: dict[str, dict] = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        compound_id = (row.get("COMPOUND_ID") or row.get("compound_id", "")).strip()
        accession = (row.get("ACCESSION_NUMBER") or row.get("accession_number", "")).strip()
        if not compound_id or not accession:
            continue
        if compound_id not in xrefs:
            xrefs[compound_id] = {"kegg_id": None, "pubchem_id": None}
        # KEGG compound IDs: C followed by 5 digits
        if accession.startswith("C") and len(accession) == 6 and accession[1:].isdigit():
            xrefs[compound_id]["kegg_id"] = accession
        # PubChem CIDs are numeric
        elif accession.isdigit() and len(accession) >= 3:
            xrefs[compound_id]["pubchem_id"] = accession
    return xrefs


def parse_chebi_structures_tsv(tsv_content: str) -> dict:
    """Parse ChEBI structures.tsv. Returns {chebi_numeric_id: {"smiles": str, "inchi": str}}."""
    structs: dict[str, dict] = {}
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    for row in reader:
        compound_id = (row.get("COMPOUND_ID") or row.get("compound_id", "")).strip()
        smiles = (row.get("SMILES") or row.get("smiles", "")).strip()
        inchi = (row.get("STANDARD_INCHI") or row.get("standard_inchi", "")).strip()
        if not compound_id:
            continue
        if compound_id not in structs:
            structs[compound_id] = {"smiles": None, "inchi": None}
        if smiles:
            structs[compound_id]["smiles"] = smiles
        if inchi:
            structs[compound_id]["inchi"] = inchi
    return structs


def build_chebi_index(compounds: dict, names: dict, xrefs: dict = None, structures: dict = None) -> dict:
    """Build lookup index keyed by lowercase name/synonym -> ChEBI entry."""
    xrefs = xrefs or {}
    structures = structures or {}
    index = {}
    for chebi_num_id, compound_info in compounds.items():
        xref = xrefs.get(chebi_num_id, {})
        struct = structures.get(chebi_num_id, {})
        entry = {
            "chebi_id": compound_info["chebi_id"],
            "name": compound_info["name"],
            "synonyms": names.get(chebi_num_id, []),
            "formula": None,
            "inchi": struct.get("inchi"),
            "smiles": struct.get("smiles"),
            "kegg_id": xref.get("kegg_id"),
            "pubchem_id": xref.get("pubchem_id"),
        }
        index[compound_info["name"].lower()] = entry
        for synonym in entry["synonyms"]:
            index[synonym.lower()] = entry
    return index


def _download_tsv_gz(url: str) -> str:
    """Download a gzipped TSV file and return decompressed content as string."""
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()
    content = gzip.decompress(resp.content)
    return content.decode("utf-8")
