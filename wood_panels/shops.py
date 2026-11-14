"""A shop's wood panels, read from the titles its public sitemap gives, as materials furniture-design's
rules judge. The reader names no shop: a shop's package passes its own rows and names.

A row is one product: {id, url, title, line, thickness_mm, length_mm, width_mm, sitemap}. `read(title)`
gives the line and the three sizes a title states, or None when it states no line this module knows or
not all three sizes. A line is a kind of board in the shop's words (`LINES`): the wood-panels class or
maker's board its values are read from, or a species of furniture-design for solid wood. A title never
names the class or the maker, except in a line of its own (`named`), so a line's values are ungrounded
and its material says what settles them: the label on the panel.

    from wood_panels import shops
    rows = [r for r in (shops.row(e) for e in entries) if r]
    knowledge = shops.knowledge("castorama", "Castorama France", rows, sitemap={...})
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from quern.provenance import Quantity
from quern.tree import Node

from . import CLASSES, PRODUCTS
from . import materials as panel_materials


@dataclass(frozen=True)
class Line:
    id: str
    words: str          # how the documents name it, in French
    form: str           # the form of board
    values: tuple | str | None  # wood-panels classes or products tried in order, a species id, or None
    named: bool         # whether a title of this line names the class or maker its values are
    key: str | None     # the connector key its strengths are stored under


LINES = [
    Line("agglomere", "aggloméré", "particleboard", ("particleboard-p2",), False, "particleboard"),
    Line("agglomere-hydrofuge", "aggloméré hydrofuge", "particleboard", ("particleboard-p3",), False,
         "particleboard"),
    Line("melamine", "aggloméré mélaminé", "melamine-faced particleboard", ("particleboard-p2",), False,
         "particleboard"),
    Line("mdf", "médium (MDF)", "MDF", ("mdf", "finsa-fibrapan-ez"), False, "mdf"),
    Line("mdf-hydrofuge", "médium (MDF) hydrofuge", "MDF", None, False, "mdf"),
    Line("mdf-teinte", "médium teinté dans la masse", "MDF", ("mdf", "finsa-fibrapan-ez"), False, "mdf"),
    Line("mdf-valchromat", "médium teinté dans la masse Valchromat", "MDF", ("valchromat",), True, "mdf"),
    Line("panneau-fibres-dures", "panneau de fibres dures", "hardboard", ("betanzos-htp-premium",), False,
         "hardboard"),
    Line("osb-3", "OSB 3", "OSB/3", ("osb-3",), True, "osb"),
    Line("osb", "OSB", "OSB/3", ("osb-3",), False, "osb"),
    Line("contreplaque-peuplier", "contreplaqué peuplier", "plywood",
         ("garnica-poplar-plywood", "toro-poplar-plywood", "allin-poplar-plywood"), False, "plywood"),
    Line("contreplaque-okoume", "contreplaqué okoumé", "plywood", ("thebault-teboply-okoume",), False, "plywood"),
    Line("contreplaque-bouleau", "contreplaqué bouleau", "plywood", ("riga-wood-birch-plywood",), False, "plywood"),
    Line("contreplaque-bouleau-filme", "contreplaqué bouleau filmé", "plywood", ("riga-wood-birch-plywood",),
         False, "plywood"),
    Line("contreplaque-pin", "contreplaqué pin", "plywood", ("thebault-tebopin",), False, "plywood"),
    Line("contreplaque", "contreplaqué", "plywood", ("allin-poplar-plywood",), False, "plywood"),
    Line("panneau-3-plis", "panneau 3 plis", "solid wood panel", ("binderholz-3-ply-spruce",), False, "plywood"),
    Line("lamelle-colle-chene", "chêne lamellé-collé", "glued solid wood", "oak-european", True, None),
    Line("lamelle-colle-hetre", "hêtre lamellé-collé", "glued solid wood", "beech-european", True, None),
    Line("lamelle-colle-frene", "frêne lamellé-collé", "glued solid wood", "ash-european", True, None),
    Line("lamelle-colle-sapin", "sapin lamellé-collé", "glued solid wood", "spruce-norway", False, None),
    Line("lamelle-colle-epicea", "épicéa lamellé-collé", "glued solid wood", "spruce-norway", True, None),
    Line("lamelle-colle-pin", "pin lamellé-collé", "glued solid wood", "pine-maritime", False, None),
    Line("lamelle-colle-acacia", "acacia lamellé-collé", "glued solid wood", "acacia-mangium", False, None),
    Line("lamelle-colle-aulne", "aulne lamellé-collé", "glued solid wood", "alder-black", True, None),
    Line("lamelle-colle-teck", "teck lamellé-collé", "glued solid wood", "teak", True, None),
    Line("massif-chene", "chêne massif", "solid wood", "oak-european", True, None),
    Line("massif-hetre", "hêtre massif", "solid wood", "beech-european", True, None),
    Line("massif-sapin", "sapin massif", "solid wood", "spruce-norway", False, None),
    Line("massif-sapin-du-nord", "sapin du Nord (pin sylvestre)", "solid wood", "pine-scots", True, None),
    Line("massif-pin", "pin massif", "solid wood", "pine-maritime", False, None),
    Line("massif-teck", "teck massif", "solid wood", "teak", True, None),
    Line("massif-acacia", "acacia massif", "solid wood", "acacia-mangium", False, None),
    Line("massif-peuplier", "peuplier massif", "solid wood", "poplar", True, None),
]
BY_ID = {line.id: line for line in LINES}
# Why a line's values are borrowed or stand in, when they do
BORROWED = {
    "lamelle-colle-sapin": "'sapin' is sold for silver fir and for spruce alike; spruce is the weaker",
    "massif-sapin": "'sapin' is sold for silver fir and for spruce alike; spruce is the weaker",
    "lamelle-colle-pin": "the title names no pine; maritime pine is the weaker of the two sold in France",
    "massif-pin": "the title names no pine; maritime pine is the weaker of the two sold in France",
    "lamelle-colle-acacia": "'acacia' is sold for robinia and for Acacia mangium; mangium is the weaker",
    "massif-acacia": "'acacia' is sold for robinia and for Acacia mangium; mangium is the weaker",
}
STAND_IN = {
    "contreplaque": "the title names no species; ALLIN's all-poplar plywood is read, the less stiff of the two "
                    "French boards (poplar, okoumé) that cover these thicknesses. The label says what the board is.",
    "osb": "the title names no class; OSB/3, the class most OSB sold for building is, is read. The label states the "
           "class.",
}
TAGS = {"face grain, flat": "along", "across face grain, flat": "across", "major axis, flat": "major",
        "minor axis, flat": "minor"}
NOMINAL = {("riga-wood-birch-plywood", 6.0): 6.5}
CLASS_NAMES = {c[0]: c[1] for c in CLASSES}
PRODUCT_NAMES = {p[0]: p[1] for p in PRODUCTS}

# --- reading a title --------------------------------------------------------------------------------

# What is not a board to cut a part from, though its title names a panel's material
NOT_A_BOARD = re.compile(r"\b(verrou|grohe|schluter|appui|rabattable|angle|porte|plan de travail|credence|"
                         r"moulure|tasseau|plinthe|parquet|lame|etagere|kit|console|support|equerre|bandeau|"
                         r"chant|decorative|miroir|meuble|caisson|tiroir|facade|quart de rond|lambris|"
                         r"bardage|dalle|perfore|cintrable|isolant|patere|niche|jardin|cloture|occultant|"
                         r"claustra|brise vue|khoper|metal|verre|pierre|lavabo|tv)\b")
# Words that say a board only looks like a wood: a décor, a veneer, a laminate
LOOKS_LIKE = re.compile(r"\b(decor|effet|aspect|imitation|stratifie|placage|plaque)\b")
SPECIES = [("chene", "chene"), ("hetre", "hetre"), ("frene", "frene"), ("sapin du nord", "sapin-du-nord"),
           ("epicea", "epicea"), ("sapin", "sapin"), ("acacia", "acacia"), ("aulne", "aulne"), ("teck", "teck"),
           ("peuplier", "peuplier"), ("pin", "pin")]


CLASS_WORDS = {"osb", "classe", "cl", "type", "e", "p"}


def plain(text: str) -> str:
    """Lower case, no accents, hyphens and punctuation as spaces; a slug's '1-8-cm' is '1.8 cm'."""
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"(?<=\d)-(?=\d+-?(?:cm|mm|m)\b)", ".", t)
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)
    t = re.sub(r"[^a-z0-9.]+", " ", t).strip()
    # '1 220' is 1220, but 'osb 3 244' and 'classe 1 250' are a class and a size
    return re.sub(r"\b([a-z]+ )?(\d) (\d{3})\b",
                  lambda m: m.group(0) if (m.group(1) or "").strip() in CLASS_WORDS
                  else f"{m.group(1) or ''}{m.group(2)}{m.group(3)}", t)


def line_of(t: str) -> str | None:
    """The line a plain title names, or None."""
    if NOT_A_BOARD.search(t):
        return None
    if re.search(r"\bosb(?: ?3)?\b", t):
        return "osb-3" if re.search(r"\bosb ?3\b", t) else "osb"
    if "melamin" in t:
        return "melamine"
    if re.search(r"\bmedium\b|\bmdf\b", t):
        if "valchromat" in t:
            return "mdf-valchromat"
        if "hydrofuge" in t:
            return "mdf-hydrofuge"
        return "mdf-teinte" if re.search(r"teinte dans la masse|forescolor", t) else "mdf"
    if re.search(r"fibres? dures|isorel|\bhdf\b", t):
        return "panneau-fibres-dures"
    if "agglomere" in t or "particules" in t:
        return "agglomere-hydrofuge" if re.search(r"hydrofuge|\bctbh\b|\bp3\b", t) else "agglomere"
    if re.search(r"\b3 plis\b|\btrois plis\b", t):
        return "panneau-3-plis"
    if re.search(r"contre ?plaque|contrepalque|\bcp\b", t):
        if "bouleau" in t:
            return "contreplaque-bouleau-filme" if "filme" in t else "contreplaque-bouleau"
        for word, sp in (("okoume", "okoume"), ("peuplier", "peuplier"), ("pin", "pin")):
            if re.search(rf"\b{word}\b", t):
                return f"contreplaque-{sp}"
        return "contreplaque"
    species = next((sp for word, sp in SPECIES if re.search(rf"\b{word}\b", t)), None)
    if species is None or LOOKS_LIKE.search(t):
        return None
    glued = re.search(r"lamell|abou|\bcolle\b", t)
    line = f"lamelle-colle-{species}" if glued else f"massif-{species}"
    if line not in BY_ID and glued:
        line = f"massif-{species}"
    return line if line in BY_ID else None


NUM = r"(\d+(?:\.\d+)?)"
UNIT = {"mm": 1.0, "cm": 10.0, "m": 1000.0}


def sizes(t: str) -> tuple[float, float, float] | None:
    """(thickness, length, width) in mm that a plain title states, or None. It reads three sizes
    together ('2800 x 2070 x 19 mm', '120x50x1.8cm'), or two and a thickness ('250x125cm epaisseur 9mm',
    'l 200 x l 60 cm ep 18 mm', '15 mm 1200x400mm')."""
    m = re.search(rf"{NUM} ?(mm|cm|m)? ?x ?(?:l )?{NUM} ?(mm|cm|m)? ?x ?(?:ep )?{NUM} ?(mm|cm|m)\b", t)
    if m:
        a, ua, b, ub, c, uc = m.groups()
        dims = sorted([float(a) * UNIT[ua or ub or uc], float(b) * UNIT[ub or uc], float(c) * UNIT[uc]])
        return _checked(dims[0], dims[2], dims[1])
    m = re.search(rf"\b{NUM}x{NUM}x{NUM}\b(?! ?(?:mm|cm|m)\b)", t)
    if m and float(m.group(3)) <= 60:  # '2500x1220x5': three sizes and no unit, in mm
        dims = sorted(float(g) for g in m.groups())
        return _checked(dims[0], dims[2], dims[1])
    e = re.search(rf"\b(?:ep|epaisseur)\.? ?{NUM} ?(mm|cm)\b", t) or re.search(rf"\b{NUM} ?(mm)\b(?! ?x)", t)
    t2 = re.sub(r" +", " ", re.sub(rf"\bx ep\.? ?{NUM} ?(?:mm|cm)\b", " ", t))  # 'l 200 cm x ep 1.8 cm x l 50 cm'
    m = (re.search(rf"(?:l )?{NUM} ?(mm|cm|m)? ?x ?(?:l )?{NUM} ?(mm|cm|m)\b", t2)
         or re.search(rf"\b{NUM} ?(m|cm) l {NUM} ?(cm|mm)\b", t2))
    if not m:  # '2440 x 1220 ep 18 mm': two sizes with no unit, over a metre, in mm
        u = re.search(rf"\b{NUM} ?x ?{NUM}\b(?! ?(?:x|mm|cm|m)\b)", t2)
        if u and min(float(u.group(1)), float(u.group(2))) >= 1000:
            m = re.match(r"(\S+) (\S+) (\S+) (\S+)", f"{u.group(1)} mm {u.group(2)} mm")
    if not m:
        n = re.search(rf"\blong\.? ?{NUM} ?(m|cm|mm)?\b", t)
        w = re.search(rf"\blarg\.? ?{NUM} ?(m|cm|mm)?\b", t)
        if n and w and (n.group(2) or w.group(2)):
            m = re.match(r"(\S+) (\S+) (\S+) (\S+)", f"{n.group(1)} {n.group(2) or w.group(2)} "
                                                       f"{w.group(1)} {w.group(2) or n.group(2)}")
    if not (m and e):
        return None
    a, ua, b, ub = m.groups()
    length, width = sorted([float(a) * UNIT[ua or ub], float(b) * UNIT[ub]], reverse=True)
    return _checked(float(e.group(1)) * UNIT[e.group(2)], length, width)


def _checked(thickness: float, length: float, width: float):
    if not (2 <= thickness <= 60 and 100 <= width <= length <= 5600):
        return None
    return round(thickness, 1), round(length, 1), round(width, 1)


def text_of(entry: dict) -> str:
    """What a sitemap entry says of its product: its title or its image's, else the part of its address that
    carries words (a slug), not a number."""
    if entry.get("title") or entry.get("image_caption"):
        return entry.get("title") or entry["image_caption"]
    parts = [p for p in re.split(r"[/?]", entry["url"].split("://", 1)[-1])[1:] if re.search(r"[a-z]{3}", p)]
    return max(parts, key=lambda p: len(re.findall(r"[a-z]", p))) if parts else ""


def read(title: str) -> tuple[str, float, float, float] | None:
    """(line, thickness, length, width) a title states, or None."""
    t = plain(title)
    line, got = line_of(t), sizes(t)
    return (line, *got) if line and got else None


# --- the materials ----------------------------------------------------------------------------------

def _q(value: float, unit: str, where: str) -> Quantity:
    return Quantity(value=float(value), unit=unit, provenance="published", grounded=True, source=where,
                    note="as the title gives it")


def sitemap(source_id: str, name: str, publisher: str, url: str, fetched: str, rows: list[dict]) -> Node:
    """The shop's sitemap as a source, one clause per product it lists: its sizes as its title gives them."""
    clauses = [Node(id=f"p-{r['id']}", kind="clause",
                    payload={"locator": f"{r['sitemap']}, the <url> entry of {r['url']}",
                             "url": r["url"], "title": r["title"], "line": r["line"]},
                    params={"thickness": _q(r["thickness_mm"], "mm", "title"),
                            "length": _q(r["length_mm"], "mm", "title"),
                            "width": _q(r["width_mm"], "mm", "title")})
               for r in rows]
    return Node(id=source_id, kind="source", name=name,
                payload={"publisher": publisher, "year": int(fetched[:4]), "url": url, "fetched": fetched,
                         "licence": "copyrighted",
                         "capture": "private copy of every sitemap file read, identified by its sha256",
                         "in_our_words": "what the shop lists; not what a given store has in stock"},
                children=clauses)


@lru_cache(maxsize=1)
def _boards() -> dict[str, list[Node]]:
    out: dict[str, list[Node]] = {}
    for m in panel_materials():
        out.setdefault(m.payload.get("product") or m.payload["class"], []).append(m)
    return out


@lru_cache(maxsize=1)
def _species() -> dict[str, Node]:
    from furniture_design.knowledge import knowledge as general
    return {m.id: m for b in general() if b.id == "materials" for m in b.children}


def _mm(t: float) -> str:
    return f"{t:g}".replace(".", "-")


def _unverified(board: str) -> str:
    if board in CLASS_NAMES:
        return (f"The shop's listing states no class; these are the figures of {CLASS_NAMES[board]}, the class a "
                "board of this type is sold under. The label on the panel (its CE marking) states the class.")
    return (f"The shop's listing names no maker; these are the values of {PRODUCT_NAMES[board]}, a board of the "
            "same type. The label on the panel says who made it.")


def materials(prefix: str, shop: str, source: str, rows: list[dict]) -> list[Node]:
    """One material per line and thickness the rows list, `<prefix>-<line>-<thickness>`, two for a board bent
    two ways; its payload `shop` says what is sold (the products, their sheets) and where its values come from."""
    out = []
    for line in LINES:
        for t in sorted({r["thickness_mm"] for r in rows if r["line"] == line.id}):
            sold = [r for r in rows if r["line"] == line.id and r["thickness_mm"] == t]
            base = f"{prefix}-{line.id}-{_mm(t)}"
            shop_payload = {"shop": shop, "line": line.id, "thickness_mm": t,
                            "products": [f"{source}/p-{r['id']}" for r in sold],
                            "sheets_mm": sorted({(r["length_mm"], r["width_mm"]) for r in sold}),
                            "named": line.named}
            label = f"{line.words[:1].upper()}{line.words[1:]} {shop}"
            name = f"{shop}, {line.words}, {t:g} mm"
            if isinstance(line.values, str):
                src = _species()[line.values]
                payload = {**src.payload, "form": line.form, "label": label,
                           "shop": {**shop_payload, "values_from": f"materials/{line.values}"}}
                if not line.named:
                    payload["shop"]["unverified"] = BORROWED[line.id]
                params = {k: v.model_copy(update={"grounded": line.named}) for k, v in src.params.items()}
                out.append(Node(id=base, kind="material", name=f"{name}, read as {src.name}", payload=payload,
                                params=params, links={"per": list(src.links["per"])}))
                continue
            found = None
            for b in line.values or ():
                at = NOMINAL.get((b, t), t)
                band = [m for m in _boards()[b] if m.payload["thickness_mm"][0] <= at <= m.payload["thickness_mm"][1]]
                if band:
                    found = (b, band)
                    break
            if not found:
                out.append(Node(id=base, kind="material", name=name,
                                payload={"form": line.form, "measured_along": "unstated", "connector_key": line.key,
                                         "label": label,
                                         "shop": {**shop_payload, "values_from": None,
                                                  "missing": "no published values for this line and thickness"}},
                                links={"per": shop_payload["products"]}))
                continue
            board, band = found
            first = TAGS.get(band[0].payload["measured_along"], "")
            for m in band:
                tag = TAGS.get(m.payload["measured_along"], "")
                payload = {**m.payload, "form": line.form, "label": label,
                           "shop": {**shop_payload, "values_from": f"materials/{m.id}"}}
                if "same_panel_as" in payload:
                    payload["same_panel_as"] = f"{base}-{first}"
                if not line.named:
                    payload["shop"]["unverified"] = STAND_IN.get(line.id) or _unverified(board)
                params = {k: v if line.named else v.model_copy(update={"grounded": False}) for k, v in m.params.items()}
                out.append(Node(id=f"{base}-{tag}" if tag else base, kind="material",
                                name=name + (f", bent {m.payload['measured_along']}" if tag else ""),
                                payload=payload, params=params, links={"per": list(m.links["per"])}))
    return out


# --- the sitemap's entries ---------------------------------------------------------------------------

def entries(xml: str, sitemap: str) -> list[dict]:
    """Every <url> element of a sitemap file: its address, its first image title, the element as written."""
    out = []
    for m in re.finditer(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>\s*(.*?)\s*</loc>", m.group(1), re.S)
        if not loc:
            continue
        title = re.search(r"<image:title>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</image:title>", m.group(1), re.S)
        out.append({"url": loc.group(1).strip(), "title": (title.group(1).strip() if title else ""),
                    "element": m.group(0), "sitemap": sitemap})
    return out


def product_id(url: str) -> str:
    """The product's number in its address (its EAN or the shop's reference), else its slug."""
    runs = re.findall(r"\d{6,}", url.split("://", 1)[-1].split("/", 1)[-1])
    if runs:
        return max(runs, key=len)
    slug = url.rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9-]+", "-", slug.lower())[:80]


def rows_of(found: list[dict], skip=lambda url: False) -> tuple[list[dict], list[dict]]:
    """The rows (one per product a title states a board of) and the entries they come from, each product
    once, in the order the sitemaps give them."""
    rows, kept, seen = [], [], set()
    for e in found:
        if e["url"] in seen or skip(e["url"]):
            continue
        text = e["title"] or text_of({"url": e["url"]})
        got = read(text)
        if not got:
            continue
        seen.add(e["url"])
        line, t, length, width = got
        rows.append({"id": product_id(e["url"]), "url": e["url"], "title": text, "line": line, "thickness_mm": t,
                     "length_mm": length, "width_mm": width, "sitemap": e["sitemap"]})
        kept.append(e)
    ids = [r["id"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    for r in rows:  # two products with one number in their address: the slug tells them apart
        if r["id"] in dup:
            r["id"] = f"{r['id']}-{product_id(r['url'].rsplit('/', 1)[0] + '/' + r['url'].rsplit('/', 1)[-1].split('.')[0])}"[:90]
    return rows, kept


def problems(rows: list[dict], captured: dict) -> list[str]:
    """What does not hold between a shop's range and the entries kept privately ({sitemaps: {file: sha256},
    entries: [...]}): each row is an entry of a sitemap whose sha256 is recorded, its line and sizes are what
    its title or address states when read again, and no two rows share an id."""
    by_url = {e["url"]: e for e in captured["entries"]}
    out = []
    for r in rows:
        e = by_url.get(r["url"])
        if e is None:
            out.append(f"{r['id']}: no entry kept for {r['url']}")
            continue
        if e["sitemap"] not in captured["sitemaps"] or f"<loc>{r['url']}" not in re.sub(r"<loc>\s+", "<loc>", e["element"]):
            out.append(f"{r['id']}: its entry is not an element of a sitemap whose sha256 is kept")
        text = e["title"] or text_of({"url": e["url"]})
        if r["title"] != text or read(text) != (r["line"], r["thickness_mm"], r["length_mm"], r["width_mm"]):
            out.append(f"{r['id']}: '{text}' does not read as its row")
    ids = [r["id"] for r in rows]
    out += [f"{i}: two rows share this id" for i in sorted({i for i in ids if ids.count(i) > 1})]
    return out


def knowledge(prefix: str, shop: str, source_id: str, source_name: str, url: str, fetched: str,
              rows: list[dict]) -> list[Node]:
    """The branches a shop's package merges: its sitemap as a source, and its materials."""
    return [Node(id="sources", kind="", children=[sitemap(source_id, source_name, shop, url, fetched, rows)]),
            Node(id="materials", kind="", children=materials(prefix, shop, f"sources/{source_id}", rows))]
