# SUGAR — Systematic Utilization of Glycans for Alternate Routes

## Commands

```bash
# Run full pipeline (requires BRENDA credentials in .env)
python -m pipeline.run_pipeline

# Run pipeline without external database imports (faster, offline)
python -m pipeline.run_pipeline --skip-import

# Run all pipeline tests
pytest pipeline/tests/ -q

# Frontend dev server
cd web && npm run dev

# Frontend tests
cd web && npm test
```

## Current Phase: Publication Preparation

Target journal: **Journal of Cheminformatics** (Springer, Software article type, APC waiver available for students)

Full publication roadmap: `docs/superpowers/plans/2026-03-31-publication-roadmap.md`

### Priority tasks in order (start here):
1. Wire gap analysis engineerability results into `reactions.json` output — `pipeline/analyze/gap_analysis.py` and `pipeline/run_pipeline.py`
2. Build `/workbench` frontend page with per-step engineerability visualization — `web/app/workbench/`
3. Fix duplicate checker false positives — `pipeline/validate/duplicates.py` (issue #27)
4. D-Glucose → L-Glucose case study — `docs/case-study/` (issue #29)
5. Benchmarking against 15 known pathways — `docs/benchmarking/` (issue #30)

## Project Stats (2026-03-31)

| Metric | Value |
|--------|-------|
| Compounds | 316 |
| Reactions | 2,096 |
| Pipeline tests | 251 (all passing) |
| Frontend tests | 5 |

Compound types: aldoses (63), ketoses (31), polyols (41), phosphosugars (144), deoxy sugars (8), amino sugars (9), sugar acids (8), lactones (4), NDP-sugars (8)

Gap analysis: 35 direct coverage, 1,485 cross-substrate coverage, 576 no coverage, avg score 0.56

## Key Files

| File | Purpose |
|------|---------|
| `pipeline/run_pipeline.py` | Main orchestrator — runs all rings in sequence |
| `pipeline/output/compounds.json` | 316 compounds |
| `pipeline/output/reactions.json` | 2,096 reactions |
| `pipeline/output/enzyme_index.json` | 21 EC families indexed |
| `pipeline/analyze/gap_analysis.py` | Ring 4 orchestrator |
| `pipeline/analyze/engineerability.py` | Composite engineerability score (0.0-1.0) |
| `pipeline/analyze/similarity.py` | Multi-dimensional substrate similarity |
| `pipeline/analyze/cross_substrate.py` | 3-layer enzyme candidate matching |
| `pipeline/reactions/bridge_reactions.py` | Cross-class bridge reactions |
| `web/app/` | Next.js pages |
| `docs/superpowers/plans/` | Implementation plans |

## Conventions

- **Compound IDs**: human-readable (`D-GLC`, `L-GLC`) with systematic fallback (`ALDO-C7-RSSRS`)
- **Cofactors**: stored as metadata on reactions, NOT as graph nodes
- **Evidence tiers**: `validated` > `predicted` > `inferred` > `hypothetical`
- **Bridge reactions**: connect isolated compound islands; use `transamination`, `nucleotidyltransfer`, `oxidation`, `hydrolysis` reaction types
- **Reversible reactions**: two directed edges (A→B and B→A as separate rows)
- **Engineerability scores**: `coverage_level` is the key field; `none` = needs de novo engineering

## Open GitHub Issues

| # | Title | Priority |
|---|-------|----------|
| #25 | Frontend engineering workbench | CRITICAL (publication) |
| #27 | Fix duplicate checker false positives | Medium |
| #29 | Case study: D-Glucose → L-Glucose | High (publication) |
| #30 | Benchmarking: validate against 15 known pathways | High (publication) |
| #31 | Comparison table vs KEGG/MetaCyc | Medium (publication) |
| #32 | Manuscript writing | High (publication) |
| #24 | Dashboard enrichment statistics | Low |
| #28 | Expand curated compound lists | Low |

## Architecture: Concentric Rings

```
Ring 4 (complete): enzyme gap analysis, engineerability scoring
Ring 3 (complete): deoxy/amino/acid/lactone/NDP-sugar + bridge reactions
Ring 2 (complete): ChEBI, KEGG, RHEA, BRENDA enrichment
Ring 1 (complete): monosaccharides, polyols, phosphosugars + core reactions
```

See `docs/architecture.md` for full details and extension guides.
See `docs/data-guide.md` for compound/reaction data model and field reference.
