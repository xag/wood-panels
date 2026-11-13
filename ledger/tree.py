"""The decisions wood-panels-unofficial is bound by, as a ledger. Read it with
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
            name="The classes and every panel maker's declared boards are one package, wood-panels-unofficial, "
                 "which requires furniture-design and names no shop; a shop's package (leroy-merlin-unofficial) "
                 "says which class or maker board each of its lines is",
            payload={"decided_on": "2026-11-13", "the_owner": OWNER,
                     "why": "A maker's declaration holds wherever the board is sold, so it does not belong to a "
                            "shop; the makers of panels share the classes their boards declare, so one package "
                            "holds both. furniture-design names no maker (its ledger: "
                            "makers-products-are-outside-furniture-design)."},
            links={"rests_on": ["a-boards-strength-is-its-classs"]},
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
    ]


def build() -> Quern:
    root = Path(__file__).resolve().parents[1]
    lib, refs = consume(root, os.environ.get("QUERN_REGISTRY", root.parent / "quern-registry"))
    quern = Quern(packages=list(refs))
    quern = lib.effective(quern)
    quern.root.children = entries()
    return quern
