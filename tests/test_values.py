"""Every value against the copy it was read from, and the data against furniture-design's rules.

The copies are copyrighted and live in the private repo xag/furniture, checked out beside this
one (or at $FURNITURE_REPO), under sources/wood-panels/: makers/ holds the makers' declarations
and data sheets, classes/ the documents that print a standard's class table, each beside its
text (pdftotext, the page's text, or a transcription of a scanned page that says it is one).
Without them these tests fail, saying where they looked, and never skip.
"""

import hashlib
import os
import re
from pathlib import Path

from quern import Quern, run_rules

from furniture_design.knowledge import knowledge as general, merge
from furniture_design.package import PACKAGE
from wood_panels_unofficial import CLASSES, PRODUCTS, class_materials, documents, knowledge, product_materials

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = Path(os.environ.get("FURNITURE_REPO", ROOT.parent / "furniture")) / "sources" / "wood-panels"


def _here(path: Path) -> Path:
    assert path.exists(), (f"the private copy {path} is missing: clone xag/furniture beside this repo or "
                           "set FURNITURE_REPO")
    return path


def _numbers(printed: str) -> list[float]:
    """'13 300' is 13300, '18,0' is 18, '≥ 10,5' is 10.5, '450 ± 40' is 450 and 40."""
    return [float(n.replace(" ", "").replace(",", ".")) for n in re.findall(r"\d+(?: \d{3})*(?:[.,]\d+)?", printed)]


def _cells(printed: str) -> list[float]:
    """A table row's numbers, one per cell: '– 1800 2300' is 1800 and 2300."""
    return [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", printed)]


def test_every_value_is_printed_in_the_document_fetched():
    for doc in documents().values():
        copy = _here(CAPTURES / doc["file"])
        assert hashlib.sha256(copy.read_bytes()).hexdigest() == doc["sha256"], doc["id"]
        text = re.sub(r"\s+", " ", _here(copy.with_suffix(".txt")).read_text(encoding="utf-8"))
        if doc["capture"] == "transcribed":
            assert text.startswith("Transcribed by reading the scanned pages") and doc["sha256"] in text
        for clause in doc["clauses"]:
            for name, v in clause["params"].items():
                assert v["printed"] in text, (doc["id"], clause["id"], name, v["printed"])
                if "column" in v:  # a row of a table: the value is the cell its column names
                    assert abs(_cells(v["printed"])[v["column"]] - v["value"]) < 1e-9, (doc["id"], clause["id"], name)
                else:
                    assert any(abs(n - v["value"]) < 1e-9 for n in _numbers(v["printed"])), (doc["id"], name)


def test_a_class_is_read_from_a_document_that_says_it_prints_the_standard():
    for cid, _name, _form, standard, doc, *_ in CLASSES:
        assert documents()[doc].get("prints") or doc == "kronospan-osb3-dop-18112013", cid
        assert standard.split(",")[0].split(":")[0] in (documents()[doc].get("prints") or "EN 12369-1"), cid


def _tree() -> Quern:
    tree = Quern(vocabulary=PACKAGE.vocabulary, rules=PACKAGE.rules, solvers=PACKAGE.solvers)
    tree.root.children = merge(general(), knowledge())
    return tree


def test_the_data_passes_furniture_designs_rules():
    assert [(r.rule, r.node, r.verdict) for r in run_rules(_tree()) if not r.ok] == []


def test_no_copyrighted_clause_carries_a_quote():
    sources = knowledge()[0].children
    assert all(s.payload["licence"] == "copyrighted" for s in sources)
    assert all("quote" not in c.payload for s in sources for c in s.children)


def test_a_class_materials_strength_is_grounded_and_its_density_never_is():
    for m in class_materials():
        assert m.params["density"].grounded is False, m.id
        assert all(q.grounded for k, q in m.params.items() if k != "density"), m.id


def test_a_maker_declares_at_least_its_classs_strength():
    """A board's strength is its class's: every maker that declares a class prints at least the
    class's bending strength in each band. Not the modulus: Swiss Krono prints EN 300's required
    3500 MPa for its OSB/3 where EN 12369-1 gives the class a mean of 4930."""
    classes = {}
    for m in class_materials():
        classes.setdefault(m.payload["class"], []).append(m)
    seen = 0
    for m in product_materials():
        cls = m.payload["class"]
        if not cls or "design_bending_stress" not in m.params:
            continue
        mid = sum(m.payload["thickness_mm"]) / 2
        match = [c for c in classes[cls] if c.payload["thickness_mm"][0] <= mid <= c.payload["thickness_mm"][1]
                 and c.payload["measured_along"] == m.payload["measured_along"]]
        if not match:
            continue
        seen += 1
        assert m.params["design_bending_stress"].value >= match[0].params["design_bending_stress"].value - 1e-9, m.id
    assert seen >= 15


def test_a_plywood_board_is_two_materials_one_per_way_it_bends():
    ms = {m.id: m for m in product_materials()}
    along, across = ms["riga-wood-birch-plywood-18-along"], ms["riga-wood-birch-plywood-18-across"]
    assert along.payload["measured_along"] == "face grain, flat"
    assert across.payload["measured_along"] == "across face grain, flat"
    assert across.payload["same_panel_as"] == along.id and "same_panel_as" not in along.payload
    # Riga Wood's 18 mm, Table 3.17: EN 310 lower 5% strength 61.7 along, read as characteristic
    assert abs(along.params["design_bending_stress"].value - 61.7 / 2.1) < 1e-9


def test_every_product_has_a_material():
    ids = {m.payload["product"] for m in product_materials()}
    assert ids == {p for p, *_ in PRODUCTS}
