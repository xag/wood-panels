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
from wood_panels import (AS_PRINTED, CLASS_DOCS, CLASSES, MORE, PRODUCTS, class_materials, documents, knowledge,
                         product_materials)

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = Path(os.environ.get("FURNITURE_REPO", ROOT.parent / "furniture")) / "sources" / "wood-panels"


def _here(path: Path) -> Path:
    assert path.exists(), (f"the private copy {path} is missing: clone xag/furniture beside this repo or "
                           "set FURNITURE_REPO")
    return path


WORDS = {"two": 2.0, "three": 3.0, "four": 4.0}


def _numbers(printed: str) -> list[float]:
    """'13 300' is 13300, '18,0' is 18, '≥ 10,5' is 10.5, '450 ± 40' is 450 and 40, 'four' is 4."""
    return ([float(n.replace(" ", "").replace(",", ".")) for n in re.findall(r"\d+(?: \d{3})*(?:[.,]\d+)?", printed)]
            + [WORDS[w] for w in re.findall(r"[a-z]+", printed.lower()) if w in WORDS])


def _cells(printed: str, thousands: str | None = None) -> list[float]:
    """A table row's numbers, one per cell: '– 1800 2300' is 1800 and 2300. A row that groups thousands says
    with what: with ' ', '610 1 050 980' is 610, 1050 and 980; with ',', '2,105 2,182' is 2105 and 2182."""
    if thousands == ",":
        printed = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", printed)
    pattern = r"\d{1,2} \d{3}(?!\d)|\d+(?:[.,]\d+)?" if thousands == " " else r"\d+(?:[.,]\d+)?"
    return [float(n.replace(" ", "").replace(",", ".")) for n in re.findall(pattern, printed)]


def test_every_value_is_printed_in_the_document_fetched():
    for doc in documents().values():
        copy = _here(CAPTURES / doc["file"])
        assert hashlib.sha256(copy.read_bytes()).hexdigest() == doc["sha256"], doc["id"]
        text = re.sub(r"\s+", " ", _here(copy.with_suffix(".txt")).read_text(encoding="utf-8"))
        if doc["capture"] == "transcribed":
            assert text.startswith("Transcribed by reading the scanned pages") and doc["sha256"] in text
        for clause in doc["clauses"]:
            assert clause.get("quote", "") in text, (doc["id"], clause["id"], "quote")
            for name, v in clause["params"].items():
                assert v["printed"] in text, (doc["id"], clause["id"], name, v["printed"])
                if "column" in v:  # a row of a table: the value is the cell its column names
                    cells = _cells(v["printed"], v.get("thousands"))
                    assert abs(cells[v["column"]] - v["value"]) < 1e-9, (doc["id"], clause["id"], name)
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


def test_only_a_public_domain_clause_carries_a_quote():
    """Every document is copyrighted but the Forest Products Laboratory's, whose clauses quote it."""
    sources = knowledge()[0].children
    assert {s.id for s in sources if s.payload["licence"] != "copyrighted"} == {"fpl-rp-574-creep-of-panels"}
    for s in sources:
        assert all(("quote" in c.payload) == (s.payload["licence"] == "public domain") for c in s.children), s.id


def test_a_class_materials_strength_is_grounded_and_its_density_never_is():
    for m in class_materials():
        assert m.params["density"].grounded is False, m.id
        assert all(q.grounded for k, q in m.params.items() if k not in ("density", "initial_share_of_longtime", *MORE)
                   ), m.id


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


def test_every_material_has_its_creep_share():
    """The rule a-beam-sags-within-its-limit reads initial_share_of_longtime: 1/(1 + kdef), from the clause it
    names, so every board can be judged for sag over time."""
    for m in class_materials() + product_materials():
        q = m.params["initial_share_of_longtime"]
        _, doc, clause, param = q.derived_from[0].split("/")
        kdef = next(c for c in documents()[doc]["clauses"] if c["id"] == clause)["params"][param]["value"]
        assert abs(q.value - 1 / (1 + kdef)) < 1e-12, m.id
    plywood = {m.id: m for m in product_materials()}["riga-wood-birch-plywood-18-along"]
    assert plywood.params["initial_share_of_longtime"].grounded and abs(
        plywood.params["initial_share_of_longtime"].value - 1 / 1.8) < 1e-12
    particleboard = {m.id: m for m in class_materials()}["particleboard-p2-13-20"]
    assert particleboard.params["initial_share_of_longtime"].grounded is False


def _own(m) -> list[str]:
    """The documents a material's values are its own in: a product's, or a class's that print its standard."""
    if "product" in m.payload:
        return next(docs for pid, _n, _f, docs, *_ in PRODUCTS if pid == m.payload["product"])
    doc = next(c[4] for c in CLASSES if c[0] == m.payload["class"])
    return [doc, *CLASS_DOCS.get(m.payload["class"], [])]


def test_a_borrowed_value_is_never_grounded():
    """A screw, swelling or movement value from a document that is not the board's own is borrowed: named in
    the material's payload and never grounded; one from its own documents is grounded, and a class's own
    documents say they print its standard."""
    seen = 0
    for m in class_materials() + product_materials():
        borrowed = m.payload.get("borrowed", {})
        for param in MORE:
            if param not in m.params:
                assert param not in borrowed, (m.id, param)
                continue
            doc = m.params[param].derived_from[0].split("/")[1]
            if param in borrowed:
                seen += 1
                assert m.params[param].grounded is False and doc not in _own(m), (m.id, param)
                assert m.params[param].note.startswith("borrowed from " + borrowed[param]), (m.id, param)
            else:
                assert m.params[param].grounded and doc in _own(m), (m.id, param)
                assert "product" in m.payload or documents()[doc].get("prints"), (m.id, param)
    assert seen >= 20


def test_a_materials_screw_swelling_and_movement_values_are_its_clauses():
    """Each equals the value its clause prints, brought to the material's unit: kg times 9.80665, daN times 10,
    % per % over 100."""
    for m in class_materials() + product_materials():
        for param, (unit, _) in MORE.items():
            if param not in m.params:
                continue
            q = m.params[param]
            _, doc, clause, name = q.derived_from[0].split("/")
            printed = next(c for c in documents()[doc]["clauses"] if c["id"] == clause)["params"][name]
            assert name == param and q.unit == unit, (m.id, param)
            assert abs(q.value - printed["value"] * AS_PRINTED[printed["unit"]][0]) < 1e-9, (m.id, param)
    ms = {m.id: m for m in product_materials()}
    # Riga Wood's Table 4.22: 285 kg on the face from 15 mm; Thebault's TeboPin: 180 daN on the face
    assert abs(ms["riga-wood-birch-plywood-18-along"].params["screw_withdrawal_face"].value - 285 * 9.80665) < 1e-9
    assert ms["thebault-tebopin-15-along"].params["screw_withdrawal_face"].value == 1800
    assert abs(ms["riga-wood-birch-plywood-18-along"].params["dimensional_change_in_plane"].value - 0.0002) < 1e-12


def test_the_bench_is_answerable_in_every_18_mm_class():
    """An 18 mm board of each class says how it creeps, holds a screw in its edge and swells in water."""
    classes = {m.id: m for m in class_materials()}
    for mid in ("particleboard-p2-13-20", "particleboard-p3-13-20", "mdf-12-19", "osb-3-10-18-major"):
        assert "initial_share_of_longtime" in classes[mid].params, mid
    for mid in ("particleboard-p2-13-20", "particleboard-p3-13-20", "mdf-12-19"):
        assert "screw_withdrawal_edge" in classes[mid].params, mid
    for mid in ("particleboard-p3-13-20", "mdf-12-19", "osb-3-10-18-major"):
        assert "thickness_swelling_24h" in classes[mid].params, mid
