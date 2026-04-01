# Publication Roadmap: SUGAR Platform

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get the SUGAR platform to a state ready for submission to Journal of Cheminformatics (primary target) or PLOS ONE (backup).

**Architecture:** Four phases — (1) finish the software, (2) run and document the D-Glucose→L-Glucose case study, (3) benchmarking against known literature pathways, (4) manuscript writing. Phases 1 and 3 can partially overlap; Phase 4 starts after Phase 2.

**Tech Stack:** Python pipeline, Next.js 14 frontend, pytest, Journal of Cheminformatics (Springer Open Access, APC waiver available for students)

---

## Current State

- **Pipeline**: 316 compounds, 2096 reactions, 251 tests passing ✓
- **Compound types**: aldoses, ketoses, polyols, phosphosugars, deoxy sugars, amino sugars, sugar acids, lactones, NDP-sugars ✓
- **Bridge reactions**: cross-class connections (transamination, nucleotidyltransfer, etc.) ✓
- **Ring 4 backend**: similarity scoring, engineerability scores, cross-substrate matching, enzyme index ✓
- **Gap analysis NOT in reactions.json**: engineerability scores computed but not embedded in pipeline output — frontend can't use them yet
- **No engineering workbench page** in frontend
- **D-GLC and L-GLC both in graph** with 28 reactions involving L-GLC ✓

---

## Chunk 1: Software — Wire Gap Analysis + Workbench

### Task 1: Embed gap analysis results into reactions.json

The `pipeline/analyze/gap_analysis.py` module computes per-reaction engineerability scores and candidates, but they aren't stored in `reactions.json`. The frontend needs them there.

**Files:**
- Modify: `pipeline/run_pipeline.py` (wire gap analysis results into reaction output)
- Modify: `pipeline/analyze/gap_analysis.py` (return per-reaction annotations)
- Test: `pipeline/tests/test_gap_analysis.py`

- [ ] **Step 1: Read current gap_analysis.py to understand what it returns**

Read `pipeline/analyze/gap_analysis.py` and `pipeline/run_pipeline.py`.

- [ ] **Step 2: Write a failing test confirming gap data appears in reaction output**

```python
# pipeline/tests/test_gap_analysis.py
def test_gap_analysis_annotates_reactions():
    """Gap analysis results should be embedded in each reaction dict."""
    from pipeline.analyze.gap_analysis import run_gap_analysis
    reactions = [{"id": "TEST-1", "reaction_type": "epimerization", ...}]
    compounds = [...]
    enzyme_index = {}
    result = run_gap_analysis(reactions, compounds, enzyme_index)
    r = next(r for r in result["annotated_reactions"] if r["id"] == "TEST-1")
    assert "engineerability" in r
    assert "coverage_level" in r["engineerability"]
    assert "score" in r["engineerability"]
```

Run: `pytest pipeline/tests/test_gap_analysis.py::test_gap_analysis_annotates_reactions -v`
Expected: FAIL (no `annotated_reactions` key yet)

- [ ] **Step 3: Modify gap_analysis.py to return annotated reactions**

Add a return key `annotated_reactions` — each reaction gets an `engineerability` field:
```python
{
  "coverage_level": "cross_substrate",   # direct | cross_substrate | family_only | none
  "score": 0.72,
  "top_candidates": [
    {"ec_number": "5.1.3.2", "enzyme_name": "...", "similarity": 0.85}
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest pipeline/tests/test_gap_analysis.py -v`
Expected: PASS

- [ ] **Step 5: Wire into run_pipeline.py**

After gap analysis runs, merge `annotated_reactions` back into the output reactions list before writing `reactions.json`.

- [ ] **Step 6: Regenerate pipeline**

```bash
python -m pipeline.run_pipeline
```

Verify `reactions.json` has `engineerability` field on spot-checked reactions.

- [ ] **Step 7: Run all tests**

```bash
pytest pipeline/tests/ -q
```
Expected: 251+ passing.

- [ ] **Step 8: Commit**

```bash
git add pipeline/analyze/gap_analysis.py pipeline/run_pipeline.py pipeline/output/reactions.json pipeline/tests/test_gap_analysis.py
git commit -m "feat: embed gap analysis engineerability scores into reactions.json output"
```

---

### Task 2: Engineering Workbench frontend page

A new page at `/workbench` (or extend `/pathways`) that shows, for a given route:
1. Each reaction step with its engineerability score (colored: green ≥ 0.8, yellow 0.5–0.8, red < 0.5)
2. Top candidate enzymes for each step
3. The overall route engineering score (minimum score along path, or average)

**Files:**
- Create: `web/app/workbench/page.tsx`
- Create: `web/components/EngineerabilityBadge.tsx`
- Create: `web/components/WorkbenchRoute.tsx`
- Modify: `web/lib/types.ts` (add Engineerability type)
- Modify: `web/lib/data.ts` (load engineerability from reactions)

- [ ] **Step 1: Add Engineerability types to types.ts**

```typescript
export interface EngineerabilityScore {
  coverage_level: "direct" | "cross_substrate" | "family_only" | "none";
  score: number;
  top_candidates: Array<{
    ec_number: string;
    enzyme_name: string;
    similarity: number;
  }>;
}
// Add to Reaction interface:
// engineerability?: EngineerabilityScore;
```

- [ ] **Step 2: Create EngineerabilityBadge component**

Simple colored badge component: green/yellow/red based on score, shows the score and coverage level as a tooltip.

- [ ] **Step 3: Create WorkbenchRoute component**

Shows a pathway (array of reactions) as a vertical stepper:
- Each step: compound → [reaction type, engineerability badge, top candidates] → compound
- Route summary: overall score, bottleneck step identified

- [ ] **Step 4: Create the /workbench page**

Uses the same pathway search as `/pathways` but renders WorkbenchRoute instead of the simple route list. Allows the user to select a route and see the full engineering analysis.

- [ ] **Step 5: Add export button**

"Export as JSON" button for each route — downloads the full route with engineerability scores. This is what you'll use to generate paper figures.

- [ ] **Step 6: Verify locally**

Start dev server. Navigate to /workbench. Enter "D-GLC" → "L-GLC". Verify routes render with colored badges and candidate lists.

- [ ] **Step 7: Commit**

```bash
git add web/app/workbench/ web/components/EngineerabilityBadge.tsx web/components/WorkbenchRoute.tsx web/lib/types.ts web/lib/data.ts
git commit -m "feat: add engineering workbench page with per-step engineerability visualization"
```

---

### Task 3: Close stale issues + fix duplicate checker

- [ ] **Step 1: Close issue #18 (phosphosugars done)**

```bash
gh issue close 18 --comment "144 phosphosugars implemented in pipeline/enumerate/phosphosugars.py. 144 phosphorylation + 144 dephosphorylation + 288 mutase reactions generated."
```

- [ ] **Step 2: Fix duplicate checker false positives (#27)**

Read `pipeline/validate/duplicates.py`. The grouping key currently doesn't account for modification differences. Fix: include modification type in the key (e.g., `nacetyl`, `amino`, `deoxy` should all produce different fingerprints from the base compound).

- [ ] **Step 3: Verify no false positives after fix**

```bash
python -m pipeline.run_pipeline --skip-import
```

Check `pipeline_metadata.json` `duplicate_warnings` — should be 0.

- [ ] **Step 4: Update docs (#26)**

Update `docs/architecture.md` and `docs/data-guide.md` to reflect current stats (316 compounds, 2096 reactions, Ring 4 gap analysis).

Update `README.md` stats table.

- [ ] **Step 5: Commit + close issues**

```bash
git add pipeline/validate/duplicates.py docs/ README.md
git commit -m "fix: duplicate checker false positives; update docs for current state"
gh issue close 27 --comment "Fixed: modification type now included in grouping key"
gh issue close 26 --comment "Docs updated for 316 compounds, 2096 reactions, Ring 4 gap analysis"
```

---

## Chunk 2: Case Study — D-Glucose to L-Glucose

This is the scientific centerpiece of the paper. L-Glucose is a non-metabolizable enantiomer of D-Glucose with potential therapeutic applications (low-calorie sweetener, diagnostic tracer). There is no known natural enzyme that directly interconverts D-Glucose and L-Glucose. Your tool is uniquely positioned to find and rank engineering candidates.

**Important**: This is partly literature work, not just running the tool. You need to cross-reference candidates against published papers.

### Task 4: Generate and document all D-GLC → L-GLC routes

- [ ] **Step 1: Run pathway analysis in the deployed tool**

Navigate to `/workbench`. Enter "D-GLC" as source, "L-GLC" as target. Run K-shortest-paths (try K=10 or K=20).

Export all routes as JSON.

Save the export to `docs/case-study/routes-D-GLC-to-L-GLC.json`.

- [ ] **Step 2: Analyze routes programmatically**

Write `docs/case-study/analyze_routes.py`:

```python
"""Analyze D-GLC to L-GLC routes from exported workbench data."""
import json

with open("routes-D-GLC-to-L-GLC.json") as f:
    routes = json.load(f)

for i, route in enumerate(routes):
    steps = route["steps"]
    scores = [s["engineerability"]["score"] for s in steps]
    bottleneck = min(scores)
    avg = sum(scores) / len(scores)
    print(f"Route {i+1}: {len(steps)} steps, bottleneck={bottleneck:.2f}, avg={avg:.2f}")
    for step in steps:
        eng = step["engineerability"]
        print(f"  {step['id']}: {eng['coverage_level']} ({eng['score']:.2f})")
        for c in eng.get("top_candidates", [])[:2]:
            print(f"    -> {c['ec_number']} {c['enzyme_name']} sim={c['similarity']:.2f}")
```

- [ ] **Step 3: Identify the top 3 routes**

Pick the 3 routes with the highest bottleneck engineerability scores. Document them in `docs/case-study/top-routes.md` with:
- Full reaction sequence (compound IDs and reaction types)
- For each reaction: coverage level, top 2 enzyme candidates
- Why this route is promising

- [ ] **Step 4: Literature validation of top candidates**

For each unique enzyme candidate identified (typically 5-15 unique EC numbers across all top routes), do a PubMed search:
- Search: `"{enzyme_name}" AND "sugar" AND ("stereoisomer" OR "epimer" OR "engineering")`
- Note: has anyone engineered this enzyme for a related substrate? What's the nearest known reaction?
- Save notes to `docs/case-study/candidate-literature.md`

This is manual literature work. Budget 3-5 hours for 10-15 enzymes.

- [ ] **Step 5: Draft the case study summary**

Write `docs/case-study/summary.md`:
- Biological motivation (L-glucose therapeutic relevance, no natural pathway)
- Tool approach (systematic route enumeration + engineerability scoring)
- Top routes found (table: route length, bottleneck score, key intermediates)
- Top engineering candidates (table: EC, enzyme name, similarity score, literature precedent)
- Key finding: what is the most promising route and why?

This draft will become the Results section of the paper.

---

## Chunk 3: Benchmarking

Benchmarking validates that the tool correctly predicts known biology. This is what reviewers will ask for. You need to show that for reactions with known enzymes, the tool assigns them to the `direct` or `cross_substrate` coverage category.

### Task 5: Select and document the validation set

- [ ] **Step 1: Build a validation set of 15 known sugar reactions**

These should be reactions where the enzyme is known, well-characterized, and in BRENDA/KEGG. Suggested list:

| Reaction | Enzyme | EC | Source |
|----------|--------|-----|--------|
| D-Glucose → D-Fructose | Glucose isomerase | 5.3.1.5 | KEGG R00760 |
| D-Glucose → D-Mannose | Glucose-6-phosphate isomerase | 5.3.1.9 | KEGG |
| UDP-Glucose synthesis | UTP:Glc-1P uridylyltransferase | 2.7.7.9 | KEGG R00289 |
| GDP-Mannose synthesis | GTP:Man-1P guanylyltransferase | 2.7.7.22 | KEGG |
| D-Galactose → D-Glucose (epimerization at C4) | UDP-galactose 4-epimerase | 5.1.3.2 | KEGG |
| L-Fucose synthesis from GDP-Mannose | GDP-mannose 4,6-dehydratase | 4.2.1.47 | KEGG |
| D-Glucuronate synthesis | Glucose-1-P 1-dehydrogenase | 1.1.1.22 | KEGG |
| D-Xylose → D-Xylitol | Xylose reductase | 1.1.1.307 | BRENDA |
| D-Sorbitol synthesis from D-Glucose | Aldose reductase | 1.1.1.21 | KEGG |
| L-Rhamnose synthesis from dTDP-Glucose | dTDP-glucose 4,6-dehydratase | 4.2.1.46 | KEGG |
| N-Acetylglucosamine synthesis | Glucosamine N-acetyltransferase | 2.3.1.3 | KEGG |
| D-Glucosamine synthesis | D-Fructose-6P aminotransferase | 2.6.1.16 | KEGG |
| Myo-inositol synthesis | Inositol-3-phosphate synthase | 5.5.1.4 | KEGG |
| D-Glucose-6P ↔ D-Glucose-1P (mutase) | Phosphoglucomutase | 5.4.2.2 | KEGG |
| Lactose synthesis from UDP-Galactose | Lactose synthase | 2.4.1.22 | KEGG |

Save as `docs/benchmarking/validation-set.md`

- [ ] **Step 2: For each reaction, check what the tool assigns**

Write `docs/benchmarking/run_benchmark.py`:

```python
"""Check tool coverage for each validation set reaction."""
import json

with open("../../pipeline/output/reactions.json") as f:
    reactions = json.load(f)

# For each validation reaction, find it in the output
# Check: does it exist? what is its coverage_level? what is its engineerability score?
# A "pass" is: reaction exists AND coverage_level in ("direct", "cross_substrate")
```

For reactions that don't have the exact EC number in the tool, look for the substrate/product pair in reactions.json and check what the gap analysis says about it.

- [ ] **Step 3: Calculate benchmark statistics**

For the validation set:
- **Sensitivity** = reactions the tool correctly assigns coverage / total validation reactions
- **False negatives** = known reactions the tool says "none" coverage
- **Note any systematic gaps** (e.g., "lactose synthesis is missing because disaccharides not yet implemented")

Document in `docs/benchmarking/results.md`:
- Table with each validation reaction, what the tool found, pass/fail
- Overall sensitivity (target: ≥ 70%)
- Explanation of any failures (data gap, out of scope, etc.)

- [ ] **Step 4: Add 5 "true negative" checks**

Pick 5 reactions that should NOT be in the tool (e.g., reactions involving 8+ carbon sugars, reactions with compounds not in scope). Verify the tool says "none" or doesn't find a path. This shows the tool isn't just assigning high scores to everything.

---

## Chunk 4: Database Comparison

### Task 6: Compare to existing tools

- [ ] **Step 1: Compare compound coverage**

For the 316 compounds in SUGAR, check how many are in:
- KEGG Compound database (search each ChEBI ID)
- MetaCyc (manual spot-check of representative compounds)

Focus on the "exotic" compounds: L-sugars, rare stereoisomers, phosphosugars beyond the common 5-10. These are where SUGAR has unique coverage.

Document in `docs/comparison/coverage.md`:
- Count: how many SUGAR compounds have a KEGG entry?
- Count: how many SUGAR compounds appear to be absent from KEGG?
- Specific examples of compounds unique to SUGAR

- [ ] **Step 2: Feature comparison table**

Create `docs/comparison/feature-table.md`:

| Feature | KEGG | MetaCyc | SugarBase | **SUGAR** |
|---------|------|---------|-----------|-----------|
| Systematic enumeration of all stereoisomers | No | No | Partial | **Yes** |
| Pathway finding | Yes | Yes | No | **Yes** |
| Engineering gap analysis | No | No | No | **Yes** |
| Engineerability scoring | No | No | No | **Yes** |
| Cross-substrate enzyme candidates | No | No | No | **Yes** |
| Evidence tiers (hypothetical → validated) | No | Yes | No | **Yes** |
| Open source + reproducible pipeline | No | No | No | **Yes** |
| Free access, no account required | No | Partial | Yes | **Yes** |

Note limitations honestly:
- KEGG and MetaCyc have far more experimentally validated reactions
- SUGAR does not include disaccharides or oligosaccharides (yet)
- SUGAR's engineering predictions are computational, not experimentally validated

---

## Chunk 5: Manuscript

**Target journal: Journal of Cheminformatics** (Springer Open Access)
- Article type: "Software" or "Database"
- Length: typically 6-10 pages
- APC: €1,490 — request fee waiver at submission (student status + no institutional funding)
- Deadline: rolling

**Backup: PLOS ONE** (if J. Cheminformatics rejects)
- Article type: Software / Methods
- APC: $1,350 — fee waiver available

### Task 7: Find a faculty mentor

Before writing, do this:

- [ ] **Step 1: Identify 2-3 potential mentors at your medical school**

Options:
- Biochemistry department faculty who work on carbohydrate metabolism
- Systems biology / computational biology faculty
- Anyone who has published in J. Cheminformatics or similar

- [ ] **Step 2: Send a brief email**

Template:
> "I'm a second-year medical student who has been building a computational platform for systematically mapping sugar metabolism and enzyme engineering opportunities. The project is at a stage where I'm considering submission to Journal of Cheminformatics. I'm looking for someone willing to review the manuscript before submission and potentially advise on the case study interpretation. Would you be open to a 20-minute conversation about this?"

Having even one faculty reviewer on the acknowledgments (or as corresponding author if they contribute) significantly helps with peer review.

- [ ] **Step 3: Share the GitHub repo and deployed tool**

Once the workbench page is live, you have a real thing to show them.

---

### Task 8: Write the manuscript

Write sections in this order (easiest → hardest):

- [ ] **Step 1: Methods (~1,500 words)**

Subsections:
1. **Compound enumeration** — how are the 316 compounds generated? (stereo rules, C2-C7 range, derivative classes)
2. **Reaction generation** — how are the 2096 reactions generated? (rule-based + database import + inference)
3. **Database integration** — ChEBI, KEGG, RHEA, BRENDA (what each contributes)
4. **Evidence tiers** — validated / predicted / inferred / hypothetical
5. **Similarity scoring** — multi-dimensional substrate similarity (stereocenter distance, modification distance, carbon count)
6. **Engineerability scoring** — composite score, coverage levels
7. **Pathway analysis** — Yen's K-shortest-paths, cost function

- [ ] **Step 2: Results (~2,500 words)**

Subsections:
1. **Tool overview** — compound coverage statistics, reaction statistics, database enrichment (table)
2. **D-Glucose to L-Glucose case study** — (from Task 4 + Task 5 in Chunk 2/3)
3. **Benchmarking** — validation set results table, sensitivity statistics
4. **Comparison** — comparison table vs KEGG/MetaCyc

- [ ] **Step 3: Discussion (~1,000 words)**

- What the results mean for enzyme engineering workflows
- Limitations (no wet lab validation, disaccharides not included, BRENDA coverage gaps)
- Future directions (expanding to disaccharides, integrating structural data from PDB, adding cost optimization)
- How a researcher would actually use this tool

- [ ] **Step 4: Introduction (~800 words)**

Write this last, after you know what the paper actually says.
- Open with: the L-glucose therapeutic problem (why does L-glucose matter?)
- Describe the gap: no systematic tool exists for rare sugar engineering pathway analysis
- Existing tools (KEGG, MetaCyc) and why they fall short for this use case
- One sentence describing what you built and your main finding

- [ ] **Step 5: Abstract (250 words)**

Structure: background (2 sentences), gap (1 sentence), what you built (2 sentences), main results (3 sentences — case study finding + benchmark result + comparison result), conclusion (1 sentence).

- [ ] **Step 6: Figures**

Minimum set of figures for the paper:
1. **Fig 1**: Overview diagram — the 4 compound categories, pipeline stages, ring model (make this a clean schematic, not a screenshot)
2. **Fig 2**: Network graph — screenshot of the full compound network from the tool (use the /network page)
3. **Fig 3**: D-Glucose → L-Glucose case study — the workbench visualization of the top route with engineerability scores at each step
4. **Fig 4**: Benchmarking results — bar chart or table showing coverage by reaction type

- [ ] **Step 7: Share with mentor for review**

Send the draft. Give them 2-3 weeks to respond. Incorporate feedback.

- [ ] **Step 8: Submit**

Journal of Cheminformatics submission:
1. Create account at https://jcheminf.biomedcentral.com/
2. Select article type: Software
3. Request APC waiver in the cover letter (state student status, no institutional funding)
4. Cover letter should mention: the specific problem being solved, why J. Cheminformatics is appropriate, and that you're requesting a fee waiver

---

## Timeline (realistic)

| Phase | Work | Calendar time |
|-------|------|--------------|
| Chunk 1 (software) | ~3-5 days coding | 2–3 weeks (around medical school) |
| Chunk 2 (case study) | ~8 hours literature + analysis | 2–3 weeks |
| Chunk 3 (benchmarking) | ~6 hours literature lookup | 2–3 weeks (can overlap Chunk 2) |
| Chunk 4 (comparison) | ~3 hours | 1 week |
| Task 7 (find mentor) | ~1 hour email + meeting | 2-4 weeks depending on response |
| Task 8 (writing) | ~15-20 hours writing | 4–6 weeks |
| **Total to submission** | | **3–4 months** |

Realistic given medical school: **aim for submission by end of July 2026**.

---

## Things that would strengthen the paper (optional, not blocking)

- **One additional case study**: pick a second rare sugar with therapeutic interest (e.g., L-Fucose, D-Psicose, N-acetylneuraminic acid) and run the same analysis. This shows the tool is general, not purpose-built for one use case.
- **Wet lab collaborator**: if you can find a biochemist at your school willing to test even one predicted reaction, that's a genuinely strong paper upgrade. Not required for J. Cheminformatics Software article.
- **Interactive tutorial**: a 3-minute screen recording or interactive demo notebook showing the workflow. Journals increasingly appreciate this.
