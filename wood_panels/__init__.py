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

Every material also carries its creep share, 1/(1 + kdef) with EN 1995-1-1's kdef for service class 1, and,
where a document prints them, its screw-withdrawal, 24 h swelling and in-plane movement values; a value taken
from another maker's board is named in the payload's `borrowed` and is never grounded.

A board bent two ways is two materials (`-along`/`-across` for plywood and 3-ply, `-major`/
`-minor` for OSB, same_panel_as). Every document is copyrighted, so a clause carries its locator
and values and no quote; the copies are kept private and tests/test_values.py checks every value
against them.

    from furniture_design.knowledge import knowledge as general, merge
    from wood_panels import knowledge as wood_panels
    tree.root.children = merge(general(), wood_panels()) + [pieces]
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from furniture_design.knowledge import DESIGN_STRESS_CLAUSES, TROPIX_SHEETS, design_stress
from furniture_design.knowledge import knowledge as general_knowledge
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
    ("thebault-teboply-okoume", "Thebault TeboPly okoumé (exterior)", "plywood",
     ["thebault-dop-01-teboply-okoume", "thebault-teboply-okoume-exterieur-doc"], None, "plywood"),
    ("thebault-tebotwin", "Thebault TeboTwin", "plywood", ["thebault-dop-03-tebotwin"], None, "plywood"),
    ("thebault-tebopin", "Thebault TeboPin", "plywood", ["thebault-dop-12-tebopin", "thebault-tebopin-clear-doc"], None,
     "plywood"),
    ("binderholz-3-ply-spruce", "binderholz 3-layer solid wood panel, spruce", "solid wood panel",
     ["binderholz-swp-dop"], None, "plywood"),
    ("houtwerf-powerplex", "Houtwerf Powerplex Bio", "plywood", ["houtwerf-powerplex-bio-dop"], None, "plywood"),
    ("allin-poplar-plywood", "ALLIN PLY Tout Peuplier", "plywood", ["allin-ply-tout-peuplier"], None, "plywood"),
    ("allin-okoume-plywood", "ALLIN PLY Tout Okoumé", "plywood", ["allin-ply-tout-okoume"], None, "plywood"),
]
# The two ways a board bends, and what its part's span_along must say
WAYS = {"plywood": [("parallel", "along", "face grain, flat"), ("perpendicular", "across", "across face grain, flat")],
        "solid wood panel": [("parallel", "along", "face grain, flat"),
                             ("perpendicular", "across", "across face grain, flat")],
        "OSB/3": [("major", "major", "major axis, flat"), ("minor", "minor", "minor axis, flat")]}
# Creep: EN 1995-1-1's kdef for service class 1 that each form takes, as 1/(1 + kdef), the share of the final
# deflection the initial one is (ledger: creep-is-ec5s-kdef-for-service-class-1): (the clauses, grounded, note).
# A board the code does not rate borrows the nearest rated type's, ungrounded (a-board-ec5-does-not-rate-borrows-
# the-nearest-rated-types-kdef).
SWEDISH_WOOD = "sources/swedish-wood-design-vol-2-2022"  # furniture-design's source (ledger there: a-document-is-one-source-in-the-tree)
GERMAN_ANNEX = "sources/fh-bielefeld-leporello-ec5"
KDEF = "kdef_service_class_1"
_PARTICLEBOARD = ([f"{SWEDISH_WOOD}/table-9-1-p4/{KDEF}", f"{GERMAN_ANNEX}/kdef-kunstharzgebundene-spanplatten/{KDEF}"],
                  False, "1/(1 + kdef): EN 1995-1-1 rates no P2 or P3 particleboard, so P4's kdef for service class 1 "
                         "is borrowed; the German national annex gives resin-bonded particleboard the same 2.25")
CREEP = {
    "plywood": ([f"{SWEDISH_WOOD}/table-9-1-plywood/{KDEF}"], True,
                "1/(1 + kdef): EN 1995-1-1's kdef for EN 636 plywood in service class 1"),
    "OSB/3": ([f"{SWEDISH_WOOD}/table-9-1-osb-3/{KDEF}"], True,
              "1/(1 + kdef): EN 1995-1-1's kdef for OSB/3 in service class 1"),
    "solid wood panel": ([f"{GERMAN_ANNEX}/kdef-massivholzplatten/{KDEF}"], True,
                         "1/(1 + kdef): the German national annex's kdef for Massivholzplatten (EN 13353) in service "
                         "class 1"),
    "particleboard": _PARTICLEBOARD,
    "melamine-faced particleboard": _PARTICLEBOARD,
    "MDF": ([f"{SWEDISH_WOOD}/table-9-1-mdf-la/{KDEF}"], False,
            "1/(1 + kdef): EN 1995-1-1 rates no general-purpose MDF, so MDF.LA's kdef for service class 1 is "
            "borrowed"),
    "hardboard": ([f"{SWEDISH_WOOD}/table-9-1-hb-la/{KDEF}"], False,
                  "1/(1 + kdef): EN 1995-1-1 rates no general-purpose hardboard, so HB.LA's kdef for service class 1 "
                  "is borrowed"),
}
# Screws, water and moisture: each property's unit on a material, and which of several borrowed values is taken
# (the least favourable: the weakest hold, the most swelling or movement)
MORE = {"screw_withdrawal_face": ("N", min), "screw_withdrawal_edge": ("N", min),
        "thickness_swelling_24h": ("%", max), "dimensional_change_in_plane": ("1/%", max)}
# A clause's unit as printed: the factor that brings it to the material's, and what the note says of it
AS_PRINTED = {"N": (1.0, ""), "kg": (9.80665, ", printed in kg: times 9.80665"),
              "daN": (10.0, ", printed in daN: times 10"), "%": (1.0, ""), "%/%": (0.01, ", printed as % per %: over 100")}
# The documents a class reads beyond its strength table, each saying it prints the standard's requirements
CLASS_DOCS = {"particleboard-p2": ["kastamonu-particleboard-p2-datasheet"]}
# What a class or board takes from a named maker's board when its own documents do not print it, never grounded
# (ledger: a-value-a-board-lacks-is-a-named-boards-ungrounded): {(class or product, property): (document, whose)}
_SMARTPLY = ("smartply-osb3-datasheet", "SmartPly OSB/3 (Coillte), its change across the panel")
_SWISS_KRONO_OSB = ("swiss-krono-osb3-dop-cpr-164", "Swiss Krono's OSB/3 declaration")
_MEDITE = ("medite-premier-datasheet", "Medite Premier, an MDF board")
BORROW = {
    ("particleboard-p2", "screw_withdrawal_face"): ("finsa-superpan-star-datasheet", "Finsa SuperPan Star, a P2 board"),
    ("mdf", "screw_withdrawal_face"): _MEDITE,
    ("mdf", "screw_withdrawal_edge"): _MEDITE,
    ("osb-3", "thickness_swelling_24h"): _SWISS_KRONO_OSB,
    ("kronospan-osb-3", "thickness_swelling_24h"): _SWISS_KRONO_OSB,
    ("osb-3", "dimensional_change_in_plane"): _SMARTPLY,
    ("kronospan-osb-3", "dimensional_change_in_plane"): _SMARTPLY,
    ("swiss-krono-osb-3", "dimensional_change_in_plane"): _SMARTPLY,
    ("binderholz-3-ply-spruce", "dimensional_change_in_plane"): ("mayr-melnhof-k1-multiplan-datasheet",
                                                                 "Mayr-Melnhof's K1 multiplan 3-layer spruce panel"),
}
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
                                 "rows": {k: v["printed"] for k, v in c["params"].items()},
                                 **({"quote": c["quote"]} if "quote" in c else {})},
                        params={k: _published(v["value"], v["unit"], c["locator"],
                                              f"{v['statistic']}{', ' + v['test'] if v.get('test') else ''}")
                                for k, v in c["params"].items()})
                   for c in d["clauses"]]
        payload = {"publisher": d["publisher"], "year": 2026, "url": d["url"], "fetched": d["fetched"],
                   "sha256": d["sha256"], "licence": d.get("licence", "copyrighted"),
                   "capture": "private copy, identified by its sha256"
                              + (", values transcribed from its scanned pages" if d["capture"] == "transcribed" else ""),
                   "statistic": d["statistic_note"]}
        if d.get("prints"):
            payload["prints"] = d["prints"]
        out.append(Node(id=d["id"], kind="source", name=f"{d['publisher']}: {d['title']}", payload=payload,
                        children=clauses))
    return out


def _covering(doc: str, t: float) -> dict | None:
    return next((c for c in documents()[doc]["clauses"]
                 if c["thickness"] and c["thickness"][0] <= t <= c["thickness"][1]), None)


def _stating(doc: str, param: str, lo: float, hi: float, overlap: bool = False) -> list[dict]:
    """The clause of a document that states a property for a band's middle thickness, or for every thickness;
    else, when overlap, every clause that states it for some thickness inside the band."""
    mid, out = (lo + hi) / 2, []
    for c in documents()[doc]["clauses"]:
        if param not in c["params"]:
            continue
        t = c["thickness"]
        if t is None or t[0] <= mid <= t[1]:
            return [c]
        if overlap and t[0] <= hi and lo <= t[1]:
            out.append(c)
    return out


def _more(owner: str, own: list[str], form: str, thickness: list[float]) -> tuple[dict, dict, list[str]]:
    """A band's creep share and its screw, swelling and movement values: from its own documents, grounded (a
    class's own documents print the standard), or borrowed from a named board, never grounded. Returns the
    params, whose each borrowed one is, and the clauses they come from."""
    lo, hi = thickness
    refs, grounded, note = CREEP[form]
    params = {"initial_share_of_longtime": _q(1 / (1 + _value(refs[0])), "", refs, note, grounded)}
    per, borrowed = [r.rsplit("/", 1)[0] for r in refs], {}
    for param, (unit, worst) in MORE.items():
        found = next(((d, c) for d in own for c in _stating(d, param, lo, hi)), None)
        whose = None
        if not found and (owner, param) in BORROW:
            doc, whose = BORROW[(owner, param)]
            stated = _stating(doc, param, lo, hi, overlap=True)
            found = (doc, worst(stated, key=lambda c: c["params"][param]["value"])) if stated else None
        if not found:
            continue
        doc, c = found
        p = c["params"][param]
        factor, printed = AS_PRINTED[p["unit"]]
        ref = f"sources/{doc}/{c['id']}"
        note = f"{p['statistic']}{', ' + p['test'] if p.get('test') else ''}{printed}"
        if whose:
            t = c["thickness"]
            at = "" if t is None or t[0] <= (lo + hi) / 2 <= t[1] else f", which declares it from {t[0]:g} to {t[1]:g} mm"
            note = f"borrowed from {whose}{at}: {note}"
            borrowed[param] = whose
        params[param] = _q(p["value"] * factor, unit, [f"{ref}/{param}"], note, whose is None)
        per.append(ref)
    return params, borrowed, per


@lru_cache(maxsize=1)
def _general_sources() -> dict[str, Node]:
    """furniture-design's sources by id, for the clauses this package reads there."""
    return {s.id: s for b in general_knowledge() if b.id == "sources" for s in b.children}


def _value(ref: str) -> float:
    """The value at a clause param path: a document's, or a Tropix sheet's relative density as kg/m3."""
    _, src, clause, param = ref.split("/")
    if src.startswith("tropix-"):
        return 1000.0 * next(s for s in TROPIX_SHEETS if f"tropix-{s[0]}" == src)[7]
    if src not in documents():  # a source furniture-design holds
        return next(c for c in _general_sources()[src].children if c.id == clause).params[param].value
    return next(c for c in documents()[src]["clauses"] if c["id"] == clause)["params"][param]["value"]


def _bands(docs: list[str]) -> list[tuple[str, dict]]:
    """Every band the documents state a strength for, the first document's where two cover the same
    thickness; a clause stating only a density lends it to a band and is not one."""
    out: list[tuple[str, dict]] = []
    for doc in docs:
        for c in documents()[doc]["clauses"]:
            if not any(k.startswith("bending_strength") for k in c["params"]):
                continue
            lo, hi = c["thickness"]
            if not any(o["thickness"][0] <= (lo + hi) / 2 <= o["thickness"][1] for _, o in out):
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
            grounded: bool, extra: dict, per: list[str], thickness: list[float], more: tuple) -> list[Node]:
    """A board's materials from one clause's values, one per way it bends, each with the band's creep share and
    its screw, swelling and movement values (more: the params, whose the borrowed ones are, their clauses)."""
    more_params, borrowed, more_per = more
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
            g_key = next((k for k in (f"shear_modulus_rolling_{suffix}", "shear_modulus_rolling") if k in pr), None)
            if modulus == "true" and g_key:
                params["shear_modulus_rolling"] = _q(pr[g_key]["value"], "MPa", [f"{ref}/{g_key}"],
                                                     "rolling shear: the shear of a board bent flat", grounded)
        params.update(more_params)
        mid = f"{base}-{tag}" if tag else base
        payload = {"form": form, "measured_along": along, "modulus": modulus, "connector_key": key,
                   "thickness_mm": thickness, **extra}
        if borrowed:
            payload["borrowed"] = borrowed
        if tag and tag != ways[0][1]:
            payload["same_panel_as"] = f"{base}-{ways[0][1]}"
        out.append(Node(id=mid, kind="material", name=name + (f", bent {along}" if tag else ""),
                        payload=payload, params=params, links={"per": list(dict.fromkeys(per + more_per))}))
    return out


def _band_name(c: dict) -> str:
    lo, hi = c["thickness"]
    lo = round(lo) if abs(lo - round(lo) - 0.01) < 1e-9 else lo
    return f"{lo:g} mm" if lo == hi else f"{lo:g} to {hi:g} mm"


def class_materials() -> list[Node]:
    out = []
    for cid, name, form, standard, doc, density_doc, whose, key in CLASSES:
        for c in documents()[doc]["clauses"]:
            if not any(k.startswith("bending_strength") for k in c["params"]):
                continue
            ref = f"sources/{doc}/{c['id']}"
            lo, hi = c["thickness"]
            # the lowest density the borrowed document states inside the band: a class sets none
            inside = [d for d in documents()[density_doc]["clauses"] if d["thickness"]
                      and lo <= sum(d["thickness"]) / 2 <= hi and "density_low" in d["params"]]
            if not inside:
                continue
            dc = min(inside, key=lambda d: d["params"]["density_low"]["value"])
            dref = f"sources/{density_doc}/{dc['id']}/density_low"
            density = _q(dc["params"]["density_low"]["value"], "kg/m3", [dref],
                         f"{standard} sets no density: {whose}, the lowest stated in this band", False)
            band = c["id"].split("-", 1)[1] if c["id"].startswith(("p2-", "p3-", "mdf-")) else c["id"]
            out.extend(_boards(f"{cid}-{band}", f"{name}, {_band_name(c)}", form, key, ref, c["params"], density,
                               True, {"class": cid, "standard": standard},
                               [ref, dref.rsplit("/", 1)[0], *DESIGN_STRESS_CLAUSES], c["thickness"],
                               _more(cid, [doc, *CLASS_DOCS.get(cid, [])], form, c["thickness"])))
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
                               list(dict.fromkeys([ref, *extra_per, *DESIGN_STRESS_CLAUSES])), c["thickness"],
                               _more(pid, docs, form, c["thickness"])))
    return out


def materials() -> list[Node]:
    return class_materials() + product_materials()


def knowledge() -> list[Node]:
    """The branches to merge beside furniture-design's: the sources and the materials."""
    return [Node(id="sources", kind="", children=sources()), Node(id="materials", kind="", children=materials())]
