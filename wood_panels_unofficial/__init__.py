"""Wood panels as data on furniture-design's kinds (source, clause, material): the standard
classes a board's strength belongs to, and the makers' declared boards. Unofficial: neither the
makers nor the standards bodies wrote or endorsed it.

A particleboard, MDF, hardboard or OSB board's strength is its class's: a maker declares that its
board meets a class of EN 312, EN 622 or EN 300 and prints that class's figures (ledger: a-boards-
strength-is-its-classs). So there are two kinds of material:

- A class material, `<class>-<band>` (particleboard-p2-13-20, mdf-12-19, osb-3-10-18-major): the
  class's bending strength and modulus for one thickness band, as printed by a document that says
  it prints the standard. A class sets no density, so the density is a maker's board of that class
  and is never grounded.
- A product material, `<product>-<band>` (finsa-fimapan-ez-13-20, riga-wood-birch-plywood-18-
  along): a maker's board as its declaration states it. Plywood has no class with figures, so
  its values are always a product's.

A board bent two ways is two materials (`-along`/`-across` for plywood and 3-ply, `-major`/
`-minor` for OSB, same_panel_as). Every document is copyrighted, so a clause carries its locator
and values and no quote; the copies are kept private and tests/test_values.py checks every value
against them.

    from furniture_design.knowledge import knowledge as general, merge
    from wood_panels_unofficial import knowledge as wood_panels
    tree.root.children = merge(general(), wood_panels()) + [pieces]
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from furniture_design.knowledge import DESIGN_STRESS_CLAUSES, TROPIX_SHEETS, design_stress
from quern.provenance import Quantity
from quern.tree import Node

HERE = Path(__file__).parent
TROPIX = "sources/tropix-{}/properties"

# The classes whose figures a document prints: (id, name, form, the standard and table, the document
# that prints its strength and modulus, the document whose densities it borrows and whose board that is,
# connector_key)
CLASSES = [
    ("particleboard-p2", "Particleboard, EN 312 type P2 (interior fitments and furniture, dry)", "particleboard",
     "EN 312:2010, Table 3", "koskisen-chipboard-handbook", "swiss-krono-particleboard-technical-data",
     "Swiss Krono's P2 board", "particleboard"),
    ("particleboard-p3", "Particleboard, EN 312 type P3 (non load-bearing, humid)", "particleboard",
     "EN 312:2010, Tables 4 and 5", "kastamonu-particleboard-p3-datasheet", "swiss-krono-particleboard-technical-data",
     "Swiss Krono's P2 board, no P3 board's density being published here", "particleboard"),
    ("mdf", "MDF, EN 622-5 type MDF (general purpose, dry)", "MDF", "EN 622-5:2009, Table 3",
     "swiss-krono-mdf-technical-data", "swiss-krono-mdf-technical-data", "Swiss Krono's MDF board", "mdf"),
    ("osb-3", "OSB/3, EN 300 (load-bearing, humid), its EN 12369-1 characteristic values", "OSB/3",
     "EN 12369-1:2001, Tables 1 and 2", "kronospan-osb3-dop-18112013", "swiss-krono-osb3-dop-cpr-164",
     "Swiss Krono's OSB/3 board", "osb"),
]
# A maker's board: (id, name, form, its documents in the order their values are taken, the class it
# declares or None, connector_key)
PRODUCTS = [
    ("finsa-fimapan-ez", "Finsa FimaPan E-Z", "particleboard", ["finsa-fimapan-ez-dop-00067"], "particleboard-p2",
     "particleboard"),
    ("finsa-fimapan-h-ez", "Finsa FimaPan H E-Z", "particleboard", ["finsa-fimapan-h-ez-dop-00094"],
     "particleboard-p3", "particleboard"),
    ("finsa-fimaplast-ez", "Finsa FimaPlast E-Z (melamine-faced)", "melamine-faced particleboard",
     ["finsa-fimaplast-ez-dop-00267"], "particleboard-p2", "particleboard"),
    ("unilin-belspan", "Unilin Belspan", "particleboard", ["unilin-belspan-dop"], "particleboard-p2",
     "particleboard"),
    ("finsa-fibrapan-ez", "Finsa FibraPan E-Z", "MDF", ["finsa-fibrapan-ez-dop-00090", "finsa-fibrapan-ez-datasheet"],
     "mdf", "mdf"),
    ("valchromat", "Valchromat (MDF coloured through)", "MDF", ["valchromat-e05-dop-04-02"], None, "mdf"),
    ("betanzos-htp-premium", "Betanzos HB HTP Premium hardboard", "hardboard",
     ["betanzos-htp-premium-dop", "betanzos-hardboard-epd"], None, "hardboard"),
    ("kronospan-osb-3", "Kronospan OSB/3", "OSB/3", ["kronospan-osb3-dop-18112013"], "osb-3", "osb"),
    ("swiss-krono-osb-3", "Swiss Krono OSB/3", "OSB/3", ["swiss-krono-osb3-dop-cpr-164"], "osb-3", "osb"),
    ("riga-wood-birch-plywood", "Riga Wood birch plywood (Riga Ply)", "plywood", ["riga-wood-plywood-handbook"], None,
     "plywood"),
    ("garnica-poplar-plywood", "Garnica poplar plywood", "plywood", ["garnica-poplar-dop-gar-30"], None, "plywood"),
    ("toro-poplar-plywood", "Toro poplar plywood", "plywood", ["toro-poplar-datasheet"], None, "plywood"),
    ("thebault-teboply-okoume", "Thebault TeboPly okoumé (exterior)", "plywood", ["thebault-dop-01-teboply-okoume"],
     None, "plywood"),
    ("thebault-tebotwin", "Thebault TeboTwin", "plywood", ["thebault-dop-03-tebotwin"], None, "plywood"),
    ("thebault-tebopin", "Thebault TeboPin", "plywood", ["thebault-dop-12-tebopin"], None, "plywood"),
    ("binderholz-3-ply-spruce", "binderholz 3-layer solid wood panel, spruce", "solid wood panel",
     ["binderholz-swp-dop"], None, "plywood"),
    ("houtwerf-powerplex", "Houtwerf Powerplex Bio", "plywood", ["houtwerf-powerplex-bio-dop"], None, "plywood"),
]
# The two ways a board bends, and what its part's span_along must say
WAYS = {"plywood": [("parallel", "along", "face grain, flat"), ("perpendicular", "across", "across face grain, flat")],
        "solid wood panel": [("parallel", "along", "face grain, flat"),
                             ("perpendicular", "across", "across face grain, flat")],
        "OSB/3": [("major", "major", "major axis, flat"), ("minor", "minor", "minor axis, flat")]}
# The density a maker's document without one borrows: (document, from, why)
DENSITY_FROM = {
    "kronospan-osb3-dop-18112013": ("sources/swiss-krono-osb3-dop-cpr-164/10-18/density_low",
                                    "Kronospan's declaration states no density; Swiss Krono's OSB/3 mean"),
    "binderholz-swp-dop": (TROPIX.format("spruce-norway") + "/relative_density",
                           "binderholz states no density; Norway spruce's, the species of its layers"),
}


@lru_cache(maxsize=1)
def documents() -> dict[str, dict]:
    return {d["id"]: d for d in json.loads((HERE / "documents.json").read_text(encoding="utf-8"))["documents"]}


def _mm(t: float) -> str:
    return f"{t:g}".replace(".", "-")


def _published(value: float, unit: str, where: str, note: str) -> Quantity:
    return Quantity(value=float(value), unit=unit, provenance="published", grounded=True, source=where, note=note)


def _q(value: float, unit: str, refs: list[str], note: str, grounded: bool) -> Quantity:
    return Quantity(value=float(value), unit=unit, provenance="derived", grounded=grounded, derived_from=refs,
                    note=note)


def sources() -> list[Node]:
    """One source per document, one clause per thickness or band, its values as printed."""
    out = []
    for d in documents().values():
        clauses = [Node(id=c["id"], kind="clause",
                        payload={"locator": c["locator"], "thickness_mm": c["thickness"],
                                 "rows": {k: v["printed"] for k, v in c["params"].items()}},
                        params={k: _published(v["value"], v["unit"], c["locator"],
                                              f"{v['statistic']}{', ' + v['test'] if v.get('test') else ''}")
                                for k, v in c["params"].items()})
                   for c in d["clauses"]]
        payload = {"publisher": d["publisher"], "year": 2026, "url": d["url"], "fetched": d["fetched"],
                   "sha256": d["sha256"], "licence": "copyrighted",
                   "capture": "private copy, identified by its sha256"
                              + (", values transcribed from its scanned pages" if d["capture"] == "transcribed" else ""),
                   "statistic": d["statistic_note"]}
        if d.get("prints"):
            payload["prints"] = d["prints"]
        out.append(Node(id=d["id"], kind="source", name=f"{d['publisher']}: {d['title']}", payload=payload,
                        children=clauses))
    return out


def _covering(doc: str, t: float) -> dict | None:
    return next((c for c in documents()[doc]["clauses"] if c["thickness"][0] <= t <= c["thickness"][1]), None)


def _value(ref: str) -> float:
    """The value at a clause param path: a document's, or a Tropix sheet's relative density as kg/m3."""
    _, src, clause, param = ref.split("/")
    if src.startswith("tropix-"):
        return 1000.0 * next(s for s in TROPIX_SHEETS if f"tropix-{s[0]}" == src)[7]
    return next(c for c in documents()[src]["clauses"] if c["id"] == clause)["params"][param]["value"]


def _bands(docs: list[str]) -> list[tuple[str, dict]]:
    """Every band the documents state a strength for, the first document's where two cover the same
    thickness; a clause stating only a density lends it to a band and is not one."""
    out: list[tuple[str, dict]] = []
    for doc in docs:
        for c in documents()[doc]["clauses"]:
            lo, hi = c["thickness"]
            if any(k.startswith("bending_strength") for k in c["params"]) and not any(o["thickness"][0] <= (lo + hi) / 2 <= o["thickness"][1] for _, o in out):
                out.append((doc, c))
    return out


def _density(docs: list[str], doc: str, c: dict, grounded: bool) -> Quantity | None:
    """The middle of the density a band's clause states, or another document's for that band."""
    ref = f"sources/{doc}/{c['id']}"
    if "density_low" in c["params"]:
        lo, hi = c["params"]["density_low"]["value"], c["params"]["density_high"]["value"]
        return _q((lo + hi) / 2, "kg/m3", [f"{ref}/density_low", f"{ref}/density_high"],
                  "the middle of the stated density", grounded)
    if doc in DENSITY_FROM:
        src, why = DENSITY_FROM[doc]
        return _q(_value(src), "kg/m3", [src], why, False)
    mid = sum(c["thickness"]) / 2
    for other in docs:
        oc = _covering(other, mid)
        if other != doc and oc and "density_low" in oc["params"]:
            return _q(oc["params"]["density_low"]["value"], "kg/m3", [f"sources/{other}/{oc['id']}/density_low"],
                      "the maker's other document", grounded)
    return None


def _boards(base: str, name: str, form: str, key: str, ref: str, pr: dict, density: Quantity | None,
            grounded: bool, extra: dict, per: list[str], thickness: list[float]) -> list[Node]:
    """A board's materials from one clause's values: one per way it bends."""
    ways = WAYS.get(form, [("", "", "flat")])
    out = []
    for suffix, tag, along in ways:
        s_key, e_key = (f"bending_strength_{suffix}", f"bending_modulus_{suffix}") if suffix else (
            "bending_strength", "bending_modulus")
        params = {"density": density} if density else {}
        if s_key in pr:
            s = pr[s_key]
            characteristic = s["statistic"] == "characteristic"
            ds = design_stress(s["value"], f"{ref}/{s_key}", characteristic=characteristic)
            params["design_bending_stress"] = ds.model_copy(update={"grounded": grounded})
            if not characteristic:
                params["modulus_of_rupture"] = _q(s["value"], "MPa", [f"{ref}/{s_key}"], s["statistic"], grounded)
        modulus = "unstated"
        if e_key in pr:
            e = pr[e_key]
            params["modulus_of_elasticity"] = _q(e["value"], "MPa", [f"{ref}/{e_key}"],
                                                 f"{e['statistic']}, {e.get('test', 'test not printed')}", grounded)
            modulus = "apparent" if e.get("test") == "EN 310" else "true"
            if modulus == "true" and "shear_modulus_rolling" in pr:
                params["shear_modulus_rolling"] = _q(pr["shear_modulus_rolling"]["value"], "MPa",
                                                     [f"{ref}/shear_modulus_rolling"],
                                                     "rolling shear: the shear of a board bent flat", grounded)
        mid = f"{base}-{tag}" if tag else base
        payload = {"form": form, "measured_along": along, "modulus": modulus, "connector_key": key,
                   "thickness_mm": thickness, **extra}
        if tag and tag != ways[0][1]:
            payload["same_panel_as"] = f"{base}-{ways[0][1]}"
        out.append(Node(id=mid, kind="material", name=name + (f", bent {along}" if tag else ""),
                        payload=payload, params=params, links={"per": per}))
    return out


def _band_name(c: dict) -> str:
    lo, hi = c["thickness"]
    lo = round(lo) if abs(lo - round(lo) - 0.01) < 1e-9 else lo
    return f"{lo:g} mm" if lo == hi else f"{lo:g} to {hi:g} mm"


def class_materials() -> list[Node]:
    out = []
    for cid, name, form, standard, doc, density_doc, whose, key in CLASSES:
        for c in documents()[doc]["clauses"]:
            ref = f"sources/{doc}/{c['id']}"
            lo, hi = c["thickness"]
            # the lowest density the borrowed document states inside the band: a class sets none
            inside = [d for d in documents()[density_doc]["clauses"] if lo <= sum(d["thickness"]) / 2 <= hi
                      and "density_low" in d["params"]]
            if not inside:
                continue
            dc = min(inside, key=lambda d: d["params"]["density_low"]["value"])
            dref = f"sources/{density_doc}/{dc['id']}/density_low"
            density = _q(dc["params"]["density_low"]["value"], "kg/m3", [dref],
                         f"{standard} sets no density: {whose}, the lowest stated in this band", False)
            band = c["id"].split("-", 1)[1] if c["id"].startswith(("p2-", "p3-", "mdf-")) else c["id"]
            out.extend(_boards(f"{cid}-{band}", f"{name}, {_band_name(c)}", form, key, ref, c["params"], density,
                               True, {"class": cid, "standard": standard},
                               [ref, dref.rsplit("/", 1)[0], *DESIGN_STRESS_CLAUSES], c["thickness"]))
    return out


def product_materials() -> list[Node]:
    out = []
    for pid, name, form, docs, cls, key in PRODUCTS:
        for doc, c in _bands(docs):
            ref = f"sources/{doc}/{c['id']}"
            density = _density(docs, doc, c, True)
            extra_per = [density.derived_from[0].rsplit("/", 1)[0]] if density else []
            out.extend(_boards(f"{pid}-{c['id']}", f"{name}, {_band_name(c)}", form, key, ref, c["params"], density,
                               True, {"product": pid, "class": cls},
                               list(dict.fromkeys([ref, *extra_per, *DESIGN_STRESS_CLAUSES])), c["thickness"]))
    return out


def materials() -> list[Node]:
    return class_materials() + product_materials()


def knowledge() -> list[Node]:
    """The branches to merge beside furniture-design's: the sources and the materials."""
    return [Node(id="sources", kind="", children=sources()), Node(id="materials", kind="", children=materials())]
