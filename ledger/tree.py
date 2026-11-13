"""The decisions wood-panels is bound by, as a ledger. Read it with
`uv run quern brief .`, never whole.

Vocabulary: ledger@0.8.0 and grounding@1.2.0, pinned in quern.lock.
"""

from __future__ import annotations

import os
from pathlib import Path

import quern.grounding  # noqa: F401
from quern import Node, Quern
from quern.library import consume

ASKED = "is the strength of a finsa particle board really linked to finsa or to the particle board?"
OWNER = "We need to keep the makers too but not necessarily as specific packages."


def _alt(id_: str, name: str, why: str) -> Node:
    return Node(id=id_, kind="alternative", name=name, payload={"why": why})


def entries() -> list[Node]:
    return [
        Node(
            id="a-boards-strength-is-its-classs", kind="decision",
            name="A particleboard, MDF or OSB board's bending strength and modulus are its class's (EN 312 P2 or "
                 "P3, EN 622-5 MDF, EN 300 OSB/3 with EN 12369-1's values): a class material per class and "
                 "thickness band carries them, and a board whose class is known but whose maker is not takes them. "
                 "Plywood and solid-wood panels have no class with figures, so their values are a maker's",
            payload={"decided_on": "2026-11-13", "the_owner": ASKED,
                     "why": "Makers declare that their board meets a class and print the class's figures: Finsa's "
                            "FimaPan and Unilin's Belspan both declare 11 MPa and 1800 MPa from 6 to 13 mm, the "
                            "P2 row of EN 312's table, and Finsa's declarations say they comply with that table. "
                            "Kronospan and Swiss Krono print the same EN 12369-1 strengths for OSB/3. Plywood's "
                            "strength depends on species and lay-up, and EN 636 sets none."},
            children=[
                _alt("maker-values-for-every-board", "Take every board's values from some maker's declaration",
                     "Calls a class's figures a maker's, so a board whose maker is unknown looked unverified when "
                     "only its class was."),
            ],
        ),
        Node(
            id="the-classes-and-the-makers-are-one-package", kind="decision",
            name="The classes and every panel maker's declared boards are one package, wood-panels, "
                 "which requires furniture-design and names no shop; a shop's package (leroy-merlin-unofficial) "
                 "says which class or maker board each of its lines is",
            payload={"decided_on": "2026-11-13", "the_owner": OWNER,
                     "why": "A maker's declaration holds wherever the board is sold, so it does not belong to a "
                            "shop; the makers of panels share the classes their boards declare, so one package "
                            "holds both. furniture-design names no maker (its ledger: "
                            "makers-products-are-outside-furniture-design)."},
            links={"rests_on": ["a-boards-strength-is-its-classs"]},
            meta={"amended": "0f8548b304e2 the package was renamed wood-panels; the claim is unchanged "
                             "(furniture-design: a-name-says-unofficial-only-when-it-names-a-maker-or-shop)"},
            children=[
                _alt("a-package-per-maker", "One unofficial package per panel maker, as for Lamello",
                     "Fourteen packages for a few declarations each, all needing the same classes."),
                _alt("in-the-shops-package", "Keep the makers in the shop's package",
                     "A second shop would copy them or depend on the first shop."),
                _alt("in-furniture-design", "Put the classes and makers in furniture-design",
                     "furniture-design names no maker."),
            ],
        ),
        Node(
            id="a-class-is-read-from-a-document-that-prints-it", kind="decision",
            name="A class's figures are read from a document that says it prints the standard's table (Koskisen's "
                 "handbook for EN 312 P2, Kastamonu's P3 data sheet, Swiss Krono's MDF page for EN 622-5, "
                 "Kronospan's OSB/3 declaration for EN 12369-1), each value checked against that row and column of "
                 "the copy; values unlabelled or printed as minimums are read as means",
            payload={"decided_on": "2026-11-13",
                     "why": "The standards are sold, not published; these documents print their tables and say "
                            "so, and two of them agree with the makers' declarations cell for cell. Reading a "
                            "class figure as a mean takes it down by the Handbook's coefficient of variation, "
                            "which is the safe side when a document does not say (furniture-design: "
                            "a-stated-strength-is-read-the-way-its-source-labels-it)."},
            links={"rests_on": ["a-boards-strength-is-its-classs"]},
            children=[
                _alt("buy-the-standards", "Buy EN 312, EN 622-5 and EN 12369-1 and cite them",
                     "Not done yet; recorded as the debt the-standards-are-read-at-second-hand."),
            ],
        ),
        Node(
            id="a-class-borrows-a-makers-density-ungrounded", kind="decision",
            name="A class sets no density, so a class material takes the lowest density a maker's board of that "
                 "class states in its band (Swiss Krono's P2 board for P2 and P3, its MDF for MDF, its OSB/3 for "
                 "OSB/3), never grounded",
            payload={"decided_on": "2026-11-13",
                     "why": "The rules need a density for a part's mass; the lowest in the band gives the "
                            "lightest part, and a lighter piece tips sooner."},
            links={"rests_on": ["a-boards-strength-is-its-classs"]},
            children=[
                _alt("no-density", "Give a class material no density", "Its parts would have no mass."),
            ],
        ),
        Node(
            id="the-values-are-checked-against-a-private-copy", kind="decision",
            name="Every value is checked by a test against the document as fetched, identified by its sha256 and "
                 "kept with its text in the private repo xag/furniture (sources/wood-panels); a scanned page is "
                 "transcribed there, and says so; the test fails, never skips, when the copy is not beside this repo",
            payload={"decided_on": "2026-11-13",
                     "why": "The documents are copyrighted (furniture-design: a-copyrighted-source-is-cited-by-"
                            "locator-and-values); a value with no copy to check it against is a number someone "
                            "typed. Kronospan's and binderholz's declarations are images with no text, read by eye."},
            children=[
                _alt("skip-without-the-copy", "Skip the check when the copy is absent",
                     "A skipped check reads as green on every machine that cannot run it."),
            ],
        ),
        Node(
            id="the-knowledge-is-shared-unchanged-and-improved-only-here", kind="decision",
            name="The knowledge base, the database knowledge() returns, is licensed CC BY-NC-ND 4.0 with one added "
                 "permission (designing, building and selling furniture with it); the code is AGPL-3.0-or-later, "
                 "as for furniture-design and lamello-unofficial",
            payload={"decided_on": "2026-11-13",
                     "why": "The same terms as the packages it extends, so a copy cannot grow elsewhere and an "
                            "improvement is published here."},
            children=[
                _alt("another-licence", "Another licence for this package",
                     "One base under two sets of terms would make the whole unusable under either."),
            ],
        ),
        Node(
            id="creep-is-ec5s-kdef-for-service-class-1", kind="decision",
            name="A panel's creep is EN 1995-1-1's deformation factor kdef for service class 1, carried as "
                 "initial_share_of_longtime = 1/(1 + kdef): EN 636 plywood 0.80 and OSB/3 1.50 from the code's Table "
                 "3.2 as Swedish Wood's Design of timber structures, Volume 2 reprints it, and EN 13353 solid wood "
                 "panels 0.60 from the German national annex as FH Bielefeld's Leporello prints it",
            payload={"decided_on": "2026-11-13",
                     "why": "furniture-design's rule a-beam-sags-within-its-limit holds a part's initial deflection "
                            "to initial_share_of_longtime times a longtime limit, and its species carry the Wood "
                            "Handbook's two-thirds for dry timber (a final deflection 1.5 times the initial). The "
                            "code's final deflection is the initial times (1 + kdef), so 1/(1 + kdef) is the same "
                            "quantity, defined the same way for every panel type it rates. Service class 1 is a "
                            "heated room, where furniture stands."},
            children=[
                _alt("the-wood-handbooks-two-thirds", "Give every panel the Wood Handbook's two-thirds",
                     "That is dry timber's creep; the code gives particleboard and MDF a kdef of 2.25 where solid "
                     "timber has 0.60, so a shelf would be judged to sag far less over time than it does."),
                _alt("measured-fractional-creep", "Use the Forest Products Laboratory's measured fractional creep "
                     "(RP-574: 1.4 for plywood, 1.7 for OSB at 50 % RH)",
                     "Six months on North American panels, not a service life; kept as clauses beside the code."),
                _alt("the-industrys-creep-factors", "Use the shelf guidance of the panel industry (EWPAA's factor "
                     "of 2, EPF's up to 50 %)",
                     "Shelf rules of thumb with no definition shared across panel types; kept as clauses."),
            ],
        ),
        Node(
            id="a-board-ec5-does-not-rate-borrows-the-nearest-rated-types-kdef", kind="decision",
            name="A board EN 1995-1-1 does not rate takes the kdef of the nearest type it does rate, never "
                 "grounded: P2 and P3 particleboard take P4's 2.25, general-purpose MDF takes MDF.LA's 2.25, "
                 "hardboard HB takes HB.LA's 2.25",
            payload={"decided_on": "2026-11-13",
                     "why": "The code rates only load-bearing grades; the nearest is the same make-up made to a "
                            "load-bearing grade, and whether the furniture grade creeps more is not known, so the "
                            "value is marked unverified. The German national annex's row for resin-bonded "
                            "particleboard, which names no type, gives the same 2.25 and is cited beside P4's."},
            links={"rests_on": ["creep-is-ec5s-kdef-for-service-class-1"]},
            children=[
                _alt("the-industrys-factor-for-unrated-boards", "Give unrated boards the industry's factor of 2 or "
                     "an increase of 50 %",
                     "Both are below the code's 3.25 for every particleboard and MDF it rates: a furniture board "
                     "would be judged to creep less than its load-bearing grade."),
                _alt("leave-unrated-boards-without", "Give unrated boards no creep share",
                     "The sag rule could not judge any part of particleboard, MDF or hardboard."),
                _alt("ground-the-german-annex", "Ground P2 and P3 on the German annex's resin-bonded "
                     "particleboard row",
                     "The annex rates boards approved for building in Germany and names no EN 312 type."),
            ],
        ),
        Node(
            id="a-value-a-board-lacks-is-a-named-boards-ungrounded", kind="decision",
            name="A screw-withdrawal, 24 h swelling or in-plane movement value is a board's own when its own "
                 "documents print it, and a class's when a document says it prints the standard's requirement, "
                 "both grounded; otherwise it is borrowed from a named maker's board, never grounded, the material's "
                 "payload `borrowed` naming whose. A borrowed value comes from that board's clause covering the "
                 "band's middle thickness, else from those inside the band, the least favourable of them",
            payload={"decided_on": "2026-11-13",
                     "why": "A maker's value for its own board is an example of the class, not its requirement, "
                            "and a reader must be able to tell the two apart (as for density: "
                            "a-class-borrows-a-makers-density-ungrounded). Taking a clause inside the band keeps an "
                            "18 mm P2 band answerable from Finsa SuperPan Star's 19 to 20 mm column; the least "
                            "favourable (the weakest hold, the most swelling) keeps a borrowed value on the safe "
                            "side. A product never takes a class's or another maker's screw value: its own maker "
                            "either prints one or it has none."},
            links={"rests_on": ["a-boards-strength-is-its-classs"]},
            children=[
                _alt("the-wood-handbooks-screw-equation", "Predict withdrawal from density with the Wood Handbook's "
                     "Equation (8-12)",
                     "Its constant is fitted to US particleboard and US screws, and it needs a density a class "
                     "does not set."),
                _alt("ansi-grades", "Take ANSI A208's grade requirements as the Wood Handbook prints them",
                     "US grades, not EN classes."),
                _alt("research-papers", "Take a paper's measured values (Miljkovic 2007's edge withdrawal in 18 mm "
                     "particleboard and OSB)",
                     "One laboratory's boards and screws, not a declared board; kept as clauses."),
                _alt("ground-a-makers-value-on-a-class", "Ground a maker's value on the class",
                     "Would present one board's declaration as the class's requirement."),
            ],
        ),
        Node(
            id="in-plane-movement-is-a-printed-per-percent-value", kind="decision",
            name="dimensional_change_in_plane is the change in length per 1 % of moisture content as a document "
                 "prints it, over 100 as furniture-design writes a species' dimensional_change_radial (Riga Wood "
                 "0.02 % is 0.0002); of a length and a width value the larger is taken; a movement over a humidity "
                 "step (SINTEF's approvals: 2 or 3 mm/m from 35 % to 85 % RH) is not converted",
            payload={"decided_on": "2026-11-13",
                     "why": "A per-% value multiplies a moisture change directly, as the species' coefficients "
                            "do. Converting a humidity step needs the board's moisture content at both ends, which "
                            "the approvals do not print, so OSB/3 borrows SmartPly's per-% values instead."},
            children=[
                _alt("convert-the-humidity-step", "Divide SINTEF's mm/m by an assumed moisture change",
                     "The moisture content at 35 % and 85 % RH is not printed; the result would be a guess."),
                _alt("one-movement-per-way", "Give the along and across materials their own movement",
                     "furniture-design's part names one dimensional_change property, and only SmartPly prints two "
                     "different values."),
            ],
        ),
        Node(
            id="the-standards-are-read-at-second-hand", kind="debt",
            name="EN 312, EN 622-5 and EN 12369-1 are read as other documents print them, not from the standards, "
                 "so whether a class figure is a mean or a 5th percentile is not known and it is read as a mean",
            payload={"decided_on": "2026-11-13",
                     "what": "A 5th percentile read as a mean is taken down twice, so a board is judged weaker "
                             "than it is; never stronger."},
            links={"rests_on": ["a-class-is-read-from-a-document-that-prints-it"]},
            children=[Node(id="read-the-standards", kind="discharge", name="Read the class tables and their statistic in the standards themselves",
                           payload={"who": "the owner, buying EN 312:2010, EN 622-5:2009 and EN 12369-1",
                                    "how": "Add each standard as a source and label each class figure with the statistic it states"})],
        ),
        Node(
            id="thebaults-sheets-disagree-with-its-declaration", kind="debt",
            name="Thebault's data sheets for TeboPly okoumé and TeboMarine give lower bending values than its "
                 "declaration of performance DOP 01 at 8 to 30 mm; the declaration's are used",
            payload={"decided_on": "2026-11-12",
                     "what": "At 15 mm the data sheet gives 18.7 MPa and 3464 MPa along the face grain where the "
                             "declaration gives 30.4 and 5456. A declaration is what the maker is bound by; "
                             "Thebault has not been asked which is right."},
            children=[Node(id="ask-thebault", kind="discharge", name="Ask Thebault which of its two tables is right",
                           payload={"who": "the owner, by mail to Thebault",
                                    "how": "Use the table Thebault confirms and record its answer as a source"})],
        ),
        Node(
            id="a-true-modulus-without-its-shear", kind="debt",
            name="Thebault declares its okoumé, twin and pine plywood moduli to NF EN 789 with no rolling-shear "
                 "modulus, so their sag is not judged; their strength is",
            payload={"decided_on": "2026-11-12",
                     "what": "A modulus measured in pure bending needs a shear term for a board's deflection "
                             "(furniture-design: a-panels-tested-modulus-takes-no-shear-term), and no Thebault "
                             "document gives the shear modulus; Kronospan and binderholz do, so theirs are judged."},
            children=[Node(id="find-a-rolling-shear-modulus", kind="discharge", name="Find the rolling-shear modulus Thebault's boards are designed with",
                           payload={"who": "anyone, from Thebault or a published table for okoumé and pine plywood",
                                    "how": "Add it to the clauses and the materials take a shear term, as Kronospan's and binderholz's do"})],
        ),
        Node(
            id="screw-values-are-missing-for-some-boards", kind="debt",
            name="No document here prints a face screw-withdrawal value for P3 particleboard, a declared one for "
                 "OSB/3, or any for 3-layer spruce panels or hardboard; most makers' boards print none, and "
                 "Thebault's only at 15 mm: those materials carry no screw value",
            payload={"decided_on": "2026-11-13",
                     "what": "A question about how a screw holds in those boards gets no answer from the "
                             "knowledge; for OSB only Miljkovic 2007's edge values on an interior OSB are recorded, "
                             "as clauses."},
            links={"rests_on": ["a-value-a-board-lacks-is-a-named-boards-ungrounded"]},
            children=[Node(id="find-en-320-values", kind="discharge", name="Find a maker's EN 320 values for each",
                           payload={"who": "anyone, from a maker's data sheet or declaration",
                                    "how": "Add the document and its clauses; the material takes them from its "
                                           "own documents, or through BORROW for a class"})],
        ),
    ]


def build() -> Quern:
    root = Path(__file__).resolve().parents[1]
    lib, refs = consume(root, os.environ.get("QUERN_REGISTRY", root.parent / "quern-registry"))
    quern = Quern(packages=list(refs))
    quern = lib.effective(quern)
    quern.root.children = entries()
    return quern
