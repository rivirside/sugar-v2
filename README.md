# SUGAR

Systematic Utilization of Glycans for Alternate Routes -- a computational platform for discovering synthesis pathways between sugars.

## What it does

SUGAR programmatically enumerates all C2-C7 monosaccharide stereoisomers (94 compounds + 41 polyols), generates rule-based reactions between them (epimerization, isomerization, reduction), and provides a web interface to find optimal synthesis pathways using Yen's K-shortest-paths algorithm.

## Structure

- `pipeline/` -- Python data pipeline (generates compound/reaction JSON from stereochemistry rules)
- `web/` -- Next.js frontend (dark theme, pathway finder, compound/reaction browsers, network graph)

## Quick Start

### Generate data
```bash
pip install -r pipeline/requirements.txt
python -m pipeline.run_pipeline
```

### Run frontend
```bash
cd web
npm install
npm run dev
```

### Run tests
```bash
# Pipeline tests (44 tests)
python -m pytest pipeline/tests/ -v

# Frontend tests (5 tests)
cd web && npm test
```

## Ring 1 (current)

- 135 compounds (94 monosaccharides + 41 polyols)
- 696 reactions (478 epimerizations, 124 isomerizations, 94 reductions)
- Client-side pathfinding with Yen's K-shortest-paths
- Deterministic pipeline: same input = same output

## Future Rings

- **Ring 2**: Database enrichment (ChEBI, KEGG, RHEA, BRENDA cross-referencing)
- **Ring 3**: Derivatives (phosphates, acids, lactones, amino sugars, nucleotide sugars, deoxy sugars)
- **Ring 4**: Disaccharides, hypothetical enzyme engineering targets, advanced scoring
