# SUGAR

Systematic Utilization of Glycans for Alternate Routes: a computational platform for discovering enzymatic synthesis pathways between sugar metabolites.

## What it does

SUGAR systematically enumerates all C2-C7 monosaccharide stereoisomers and their derivative classes (polyols, phosphosugars, deoxy sugars, amino sugars, sugar acids, lactones, NDP-sugars), generates rule-based enzymatic reactions between them, and scores each reaction's engineering feasibility. A web interface lets you find optimal multi-step synthesis pathways using Yen's K-shortest-paths algorithm and identify which enzymatic steps require protein engineering.

| Metric | Count |
|--------|-------|
| Compounds | 316 |
| Reactions | 2,096 |
| Compound types | 9 |
| Reaction types | 13 |
| Pipeline tests | 251 |
| Frontend tests | 5 |

## Quick start

### Generate data

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.run_pipeline
```

The pipeline writes `compounds.json`, `reactions.json`, and `pipeline_metadata.json` to `pipeline/output/` and copies them to `web/data/` for the frontend.

### Run the frontend

```bash
cd web
npm install
npm run dev
```

Opens at `http://localhost:3000`. The pathway finder, compound browser, reaction browser, and network graph are all client-side with no backend required.

### Run tests

```bash
# Pipeline (251 tests)
python -m pytest pipeline/tests/ -v

# Frontend (5 tests)
cd web && npm test
```

## Project structure

```
pipeline/                        Python data pipeline
  enumerate/                     Compound generation (monosaccharides, polyols, phosphosugars,
                                 deoxy sugars, amino sugars, sugar acids, lactones, NDP-sugars)
  reactions/                     Reaction generation and cost scoring (all reaction types)
  validate/                      Completeness, duplicate, and mass-balance checks
  import_/                       Ring 2 database enrichment (ChEBI, KEGG, RHEA, BRENDA)
  analyze/                       Ring 4 gap analysis (similarity, engineerability, cross-substrate)
  data/                          Name mappings, match overrides
  output/                        Generated JSON output
  tests/                         pytest suite (251 tests)

web/                             Next.js frontend
  app/                           Pages (dashboard, pathways, compounds, reactions, network, about)
  components/                    UI components (search, filters, pathway display)
  lib/                           Core logic (pathfinding, graph building, types, search)
  data/                          Copied pipeline output consumed at build time
```

## Architecture: the Ring model

SUGAR is built in concentric rings. Each ring adds a layer of data on top of the previous one.

**Ring 1 (complete)** generates all compounds and reactions from first principles:

- 94 monosaccharides (63 aldoses + 31 ketoses, C2-C7)
- 41 polyols (reduction products with degeneracy detection)
- 144 phosphosugars (systematic C6 + curated biologically important compounds)
- Core reaction types: epimerization, isomerization, reduction, phosphorylation, dephosphorylation, mutase, phospho-epimerization, phospho-isomerization
- All reactions start as "hypothetical" evidence tier

**Ring 2 (complete)** enriches Ring 1 data with external databases:

- ChEBI bulk matching (name, alias, formula, fuzzy) — 273 compounds matched
- KEGG compound cross-referencing
- RHEA reaction matching (upgrades evidence tier to "validated" or "predicted") — 31 reactions confirmed
- BRENDA enzyme kinetics (EC numbers, enzyme names, kinetic parameters)
- D-to-L reaction inference from validated D-form reactions

Run with database enrichment: `python -m pipeline.run_pipeline` (requires network access and BRENDA credentials in `.env`)

Run without: `python -m pipeline.run_pipeline --skip-import`

**Ring 3 (complete)** adds derivative compound classes and cross-class reactions:

- 8 deoxy sugars (L-Fucose, L-Rhamnose, and stereoisomers)
- 9 amino sugars (D-GlcNAc, D-GalNAc, D-ManNAc, and others)
- 8 sugar acids (D-Glucuronic acid, D-Galacturonic acid, and others)
- 4 sugar lactones
- 8 NDP-sugars (UDP-Glucose, GDP-Mannose, and others)
- Bridge reactions connecting all compound types via transamination, nucleotidyltransfer, oxidation, and hydrolysis

**Ring 4 (complete)** adds enzyme gap analysis for protein engineering:

- Multi-dimensional substrate similarity scoring (stereocenter, modification, carbon count, type distances)
- Engineerability scores (0.0-1.0 composite) for all 2,096 reactions
- Cross-substrate enzyme candidate matching (3-layer: direct, same-type cross-position, EC family)
- Enzyme index with 21 EC families, UniProt IDs, PDB structural data availability

## Documentation

- **[Architecture Guide](docs/architecture.md)** -- how the pipeline and frontend are built, how to extend them
- **[Data Guide](docs/data-guide.md)** -- compound/reaction data model, evidence tiers, data provenance, biochemistry rationale

## Pipeline version

Current output was generated by pipeline v2.0.0 on 2026-03-26. The pipeline is deterministic: same code produces the same output.

## Author

Built by the ReefBio / ReefPath Initiative team.
