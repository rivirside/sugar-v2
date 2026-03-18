"""Pipeline orchestrator: enumerate, validate, generate reactions, and write output."""

import json
import os
import sys
from datetime import datetime, timezone

from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.polyols import generate_polyols
from pipeline.reactions.generate import (
    generate_epimerizations,
    generate_isomerizations,
    generate_reductions,
)
from pipeline.validate.completeness import check_completeness
from pipeline.validate.duplicates import check_duplicates
from pipeline.validate.mass_balance import check_mass_balance

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def _abort(message: str) -> None:
    print(f"[ABORT] {message}", file=sys.stderr)
    sys.exit(1)


def run_pipeline() -> dict:
    """Execute the full SUGAR v2 Ring 1 pipeline.

    Steps:
    1. Enumerate monosaccharides (94 compounds, C2-C7)
    2. Generate polyols with degeneracy detection
    3. Combine all compounds
    4. Validate: completeness and duplicates
    5. Generate reactions: epimerizations, isomerizations, reductions
    6. Mass balance check (ABORT on failure)
    7. Verify reaction ID uniqueness (ABORT on duplicates)
    8. Write output JSON files

    Returns a summary dict with counts and file paths.
    """
    print("=== SUGAR v2 Ring 1 Pipeline ===")

    # Step 1: Enumerate monosaccharides
    print("\n[1/7] Enumerating monosaccharides...")
    monosaccharides = enumerate_all_monosaccharides()
    print(f"  -> {len(monosaccharides)} monosaccharides (aldoses + ketoses, C2-C7)")

    # Step 2: Generate polyols
    print("\n[2/7] Generating polyols...")
    polyols = generate_polyols(monosaccharides)
    print(f"  -> {len(polyols)} polyols (with degeneracy detection)")

    # Step 3: Combine all compounds
    print("\n[3/7] Combining compound sets...")
    all_compounds = monosaccharides + polyols
    print(f"  -> {len(all_compounds)} total compounds")

    # Step 4: Validate
    print("\n[4/7] Validating compound set...")
    completeness_warnings = check_completeness(monosaccharides)
    if completeness_warnings:
        for w in completeness_warnings:
            print(f"  [WARNING] {w}")
    else:
        print("  -> Completeness check passed")

    duplicates = check_duplicates(all_compounds)
    if duplicates:
        for d in duplicates:
            print(f"  [WARNING] Duplicate: {d['original']['id']} / {d['duplicate']['id']}")
    else:
        print("  -> Duplicate check passed")

    # Step 5: Generate reactions
    print("\n[5/7] Generating reactions...")
    epimerizations = generate_epimerizations(all_compounds)
    isomerizations = generate_isomerizations(all_compounds)
    reductions = generate_reductions(all_compounds, polyols)
    all_reactions = epimerizations + isomerizations + reductions
    print(f"  -> {len(epimerizations)} epimerizations")
    print(f"  -> {len(isomerizations)} isomerizations")
    print(f"  -> {len(reductions)} reductions")
    print(f"  -> {len(all_reactions)} total reactions")

    # Step 6: Mass balance check (ABORT on failure)
    print("\n[6/7] Checking mass balance...")
    compound_map = {c["id"]: c for c in all_compounds}
    mass_errors = check_mass_balance(all_reactions, compound_map)
    if mass_errors:
        for e in mass_errors:
            print(f"  [ERROR] {e}", file=sys.stderr)
        _abort(f"Mass balance check failed with {len(mass_errors)} error(s)")
    print("  -> Mass balance check passed")

    # Step 7: Verify reaction ID uniqueness (ABORT on duplicates)
    print("\n[7/7] Verifying reaction ID uniqueness...")
    reaction_ids = [r["id"] for r in all_reactions]
    seen_ids: set[str] = set()
    duplicate_ids = []
    for rid in reaction_ids:
        if rid in seen_ids:
            duplicate_ids.append(rid)
        seen_ids.add(rid)
    if duplicate_ids:
        for did in duplicate_ids:
            print(f"  [ERROR] Duplicate reaction ID: {did}", file=sys.stderr)
        _abort(f"Reaction ID uniqueness check failed: {len(duplicate_ids)} duplicate(s)")
    print("  -> Reaction ID uniqueness check passed")

    # Write output files
    print("\n=== Writing output files ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    compounds_path = os.path.join(OUTPUT_DIR, "compounds.json")
    reactions_path = os.path.join(OUTPUT_DIR, "reactions.json")
    metadata_path = os.path.join(OUTPUT_DIR, "pipeline_metadata.json")

    with open(compounds_path, "w") as f:
        json.dump(all_compounds, f, indent=2)
    print(f"  -> {compounds_path}")

    with open(reactions_path, "w") as f:
        json.dump(all_reactions, f, indent=2)
    print(f"  -> {reactions_path}")

    metadata = {
        "pipeline_version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "monosaccharides": len(monosaccharides),
            "polyols": len(polyols),
            "total_compounds": len(all_compounds),
            "epimerizations": len(epimerizations),
            "isomerizations": len(isomerizations),
            "reductions": len(reductions),
            "total_reactions": len(all_reactions),
        },
        "completeness_warnings": completeness_warnings,
        "duplicate_warnings": len(duplicates),
        "output_files": {
            "compounds": compounds_path,
            "reactions": reactions_path,
        },
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  -> {metadata_path}")

    print("\n=== Pipeline complete ===")
    print(f"  {len(all_compounds)} compounds, {len(all_reactions)} reactions")

    return metadata


if __name__ == "__main__":
    run_pipeline()
