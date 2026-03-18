from pipeline.enumerate.monosaccharides import enumerate_all_monosaccharides
from pipeline.enumerate.polyols import generate_polyols
from pipeline.reactions.generate import generate_epimerizations, generate_isomerizations, generate_reductions

def test_full_pipeline_produces_expected_counts():
    monosaccharides = enumerate_all_monosaccharides()
    assert len(monosaccharides) == 94
    polyols = generate_polyols(monosaccharides)
    assert len(polyols) > 0
    all_compounds = monosaccharides + polyols
    epi = generate_epimerizations(all_compounds)
    iso = generate_isomerizations(all_compounds)
    red = generate_reductions(all_compounds, polyols)
    all_reactions = epi + iso + red
    assert len(epi) > 100
    assert len(iso) > 50
    assert len(red) > 50
    ids = [r["id"] for r in all_reactions]
    assert len(ids) == len(set(ids))
    compound_ids = {c["id"] for c in all_compounds}
    for r in all_reactions:
        for s in r["substrates"]:
            assert s in compound_ids
        for p in r["products"]:
            assert p in compound_ids

def test_d_glucose_to_l_glucose_path_exists():
    monosaccharides = enumerate_all_monosaccharides()
    epi = generate_epimerizations(monosaccharides)
    adj = {}
    for r in epi:
        s = r["substrates"][0]
        p = r["products"][0]
        adj.setdefault(s, set()).add(p)
    visited = set()
    queue = ["D-GLC"]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    assert "L-GLC" in visited
