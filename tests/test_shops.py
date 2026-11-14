"""Reading a shop's titles: the line and the three sizes a title states, or nothing. Every title below is one a
shop's public sitemap gives, as written."""

import re

import pytest

from wood_panels.shops import LINES, entries, materials, plain, problems, read, rows_of

READS = [
    ("panneau-osb-3-244-x-122-cm-ep-15-mm-vendu-au-panneau-", ("osb-3", 15, 2440, 1220)),
    ("tablette-melamine-blanc-30-x-120-cm-ep-1-8-cm", ("melamine", 18, 1200, 300)),
    ("panneau-medium-mdf-81-x-40-5-cm-ep-18-mm-vendu-au-panneau", ("mdf", 18, 810, 405)),
    ("tablette-chene-200-x-30-x-1-8-cm", ("massif-chene", 18, 2000, 300)),
    ("tablette-en-sapin-du-nord-2-m-l-60-cm-x-ep-1-8-cm", ("massif-sapin-du-nord", 18, 2000, 600)),
    ("tablette-melaminee-chene-gris-l-200-cm-x-ep-1-8-cm-x-l-60-cm", ("melamine", 18, 2000, 600)),
    ("panneau-bois-mdf-1-220-x-610-mm-ep-6-mm", ("mdf", 6, 1220, 610)),
    ("tablette-sapin-massif-250x40cm-ep-21mm", ("massif-sapin", 21, 2500, 400)),
    ("panneau-melamine-blanc-280x207x1.2cm", ("melamine", 12, 2800, 2070)),
    ("contreplaque-peuplier-interieur-2500x1220x5", ("contreplaque-peuplier", 5, 2500, 1220)),
    ("Panneau contreplaqué extérieur CTB-X OKOUPLEX tout Okoumé - 3,10x1,83m Ep.8mm",
     ("contreplaque-okoume", 8, 3100, 1830)),
    ("Panneau mélaminé 2 faces U190 black BS - 2800 x 2070 x 19 mm", ("melamine", 19, 2800, 2070)),
    ("Panneau MDF ponce ep.12mm larg.1,22m long.3,05m", ("mdf", 12, 3050, 1220)),
    ("Panneau OSB 3 ECOBOARD non poncé 2440 x 1220 ép.18 mm", ("osb-3", 18, 2440, 1220)),
    ("Panneau de particules brut standard 2800 x 2070 x 19 mm", ("agglomere", 19, 2800, 2070)),
    ("Tablette sapin lamellé 18mm 200x40cm", ("lamelle-colle-sapin", 18, 2000, 400)),
    ("panneau 3 plis pré découpé épicéa mil.humide 19mm 800x600mm - SUP BOIS", ("panneau-3-plis", 19, 800, 600)),
    ("Panneau contreplaqué prédécoupé Peuplier Intérieur 250x60x1,5cm", ("contreplaque-peuplier", 15, 2500, 600)),
    ("Panneau contreplaqué CTBX QUALIPLY Peuplier faces Okoumé - 3,10x1,53m Ep.5mm",
     ("contreplaque-peuplier", 5, 3100, 1530)),  # a poplar core faced with okoumé
    ("Panneau contreplaqué intérieur ECOPLUS S tout Peuplier faces sapelli - 3,10x1,53m Ep.5mm",
     ("contreplaque-peuplier", 5, 3100, 1530)),
]
NOT_BOARDS = [
    "contreplaque-pour-verrous-vega-diam-tre-23mm",       # a lock's plate
    "tablette-decor-chene-clair-204-x-50-cm",             # a décor, and no thickness
    "Tablette d'angle Schlüter-SHELF-E-S2 CURVE - 19,5x19,5cm",
    "dalle osb 3 205 x 67.5 cm epaisseur 16mm",           # a floor tile
    "Panneau contreplaqué intérieur cintrable POFLEX tout peuplier 2,50x1,12m Ep.7mm",  # bends: not a flat board
]


@pytest.mark.parametrize("title,expected", READS)
def test_a_title_reads_as_its_line_and_sizes(title, expected):
    assert read(title) == (expected[0], float(expected[1]), float(expected[2]), float(expected[3]))


@pytest.mark.parametrize("title", NOT_BOARDS)
def test_what_is_not_a_board_to_cut_from_reads_as_nothing(title):
    assert read(title) is None


def test_every_size_read_is_written_in_its_title():
    for title, _ in READS:
        line, *dims = read(title)
        said = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", plain(title))]
        for d in dims:  # in mm, cm or m, as the title gives it
            assert any(abs(n * k - d) < 1e-6 for n in said for k in (1, 10, 1000)), (title, d)


def test_every_line_is_described_once():
    ids = [line.id for line in LINES]
    assert len(ids) == len(set(ids))


SITEMAP = """<urlset><url><loc>https://shop.example/p/tablette-chene-200-x-30-x-1-8-cm/3663602885863</loc></url>
<url><loc>https://shop.example/p/papier-abrasif-silex-230x280-mm-grain-100/3505390038833</loc></url>
<url><loc>https://shop.example/p/x/1234567</loc><image:image><image:title><![CDATA[Panneau OSB 3 2440 x 1220 ép.18 mm]]>
</image:title></image:image></url></urlset>"""


def test_a_sitemaps_boards_become_rows_checked_against_the_entries_kept_and_materials():
    found = entries(SITEMAP, "sitemap-1.xml")
    rows, kept = rows_of(found)
    assert [(r["id"], r["line"]) for r in rows] == [("3663602885863", "massif-chene"), ("1234567", "osb-3")]
    captured = {"sitemaps": {"sitemap-1.xml": "0" * 64}, "entries": kept}
    assert problems(rows, captured) == []
    rows[0]["thickness_mm"] = 20.0
    assert problems(rows, captured) == ["3663602885863: 'tablette-chene-200-x-30-x-1-8-cm' does not read as its row"]
    rows[0]["thickness_mm"] = 18.0
    ms = {m.id: m for m in materials("shop", "A shop", "sources/shop-sitemap", rows)}
    assert set(ms) == {"shop-massif-chene-18", "shop-osb-3-18-major", "shop-osb-3-18-minor"}
    assert ms["shop-osb-3-18-major"].payload["shop"]["sheets_mm"] == [(2440.0, 1220.0)]
    assert ms["shop-massif-chene-18"].payload["shop"]["products"] == ["sources/shop-sitemap/p-3663602885863"]
