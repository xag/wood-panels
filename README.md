# wood-panels

Wood panels as data for [furniture-design](https://github.com/xag/furniture-design): the standard classes a board's strength belongs to, and the makers' declared boards. **Unofficial**: the makers and the standards bodies did not write or endorse it, and nothing here speaks for them.

## What is here

- **The classes**: a particleboard, MDF or OSB board's strength is its class's. A maker declares that its board meets a class and prints the class's figures: Finsa's FimaPan and Unilin's Belspan both declare 11 MPa and 1800 MPa from 6 to 13 mm, the P2 row of EN 312. So there is one material per class and thickness band: particleboard P2 and P3 (EN 312:2010), MDF (EN 622-5:2009, Table 3) and OSB/3 (EN 12369-1's characteristic values), as `materials/<class>-<band>` (`particleboard-p2-13-20`, `mdf-12-19`, `osb-3-10-18-major`). A class sets no density, so a class material borrows the lowest a maker's board of that class states in its band, ungrounded.
- **The makers' boards**: Declarations of Performance and data sheets from Finsa (FimaPan E-Z, FimaPan H E-Z, FimaPlast E-Z, FibraPan E-Z), Unilin (Belspan), Valchromat, Betanzos (hardboard), Kronospan and Swiss Krono (OSB/3), Riga Wood (birch plywood), Garnica and Toro (poplar), Thebault (okoumé, twin, pine), binderholz (3-ply spruce), Houtwerf (Powerplex) and ALLIN (all-poplar and all-okoumé plywood), and the documents the classes are read from (Koskisen's chipboard handbook, Kastamonu's P2 and P3 data sheets, Swiss Krono's particleboard and MDF pages). One material per board and thickness band as declared, `materials/<product>-<band>` (`finsa-fimapan-ez-13-20`, `riga-wood-birch-plywood-18-along`, `allin-poplar-plywood-18-along`). Plywood has no class with figures, so its values are always a maker's.
- A board that bends differently along and across is two materials: `-along`/`-across` for plywood and 3-ply, `-major`/`-minor` for OSB, linked by `same_panel_as`.
- **Creep**: every material carries `initial_share_of_longtime`, the share of its final deflection that the initial one is, 1/(1 + kdef) with EN 1995-1-1's deformation factor for service class 1 (a heated room): 0.80 for EN 636 plywood and 1.50 for OSB/3, from the code's table as Swedish Wood's *Design of timber structures, Volume 2* reprints it (furniture-design holds that book's source and its Table 9.1; this package reads it there), and 0.60 for EN 13353 solid wood panels, from the German national annex as FH Bielefeld's Leporello prints it. The code rates no P2 or P3 particleboard, no general-purpose MDF and no general-purpose hardboard, so those take P4's, MDF.LA's and HB.LA's 2.25, marked unverified. The Forest Products Laboratory's measured creep of plywood and OSB is recorded as clauses beside it, and the panel industry's shelf guidance (EWPAA's creep factor of 2, 3 or 4, the European Panel Federation's "up to 50 %") is in furniture-design's sources.
- **Screws, water and moisture**: where a document prints them, a material carries `screw_withdrawal_face` and `screw_withdrawal_edge` (N, EN 320), `thickness_swelling_24h` (%, EN 317) and `dimensional_change_in_plane` (the change in length per 1 % of moisture content, as a fraction: 0.02 % is 0.0002). A maker's board takes its own maker's values (Riga Wood's kg and Thebault's daN converted to N). A class takes a value from a document that prints the standard's requirement; otherwise it borrows a named maker's board's (Finsa SuperPan Star's face hold for P2, Medite Premier's for MDF, Swiss Krono's swelling and SmartPly's movement for OSB/3), the value is marked unverified and the material's payload `borrowed` says whose. Where nothing is printed the material carries nothing: no face hold for P3, no declared screw value for OSB/3, 3-ply spruce or hardboard, no 24 h swelling for P2.

No kinds and no rules of its own: a part that `uses` one of these materials is judged by furniture-design's rules. No shop either: a shop's package, such as [leroy-merlin-unofficial](https://github.com/xag/leroy-merlin-unofficial), says which class or maker board each of its lines is.

- **Reading a shop's range** (`wood_panels.shops`): a shop's public sitemap titles read as boards, the line (contreplaqué peuplier, médium, OSB 3, sapin lamellé-collé…) and the three sizes, however the title writes them, and the materials a shop's package lists, each line read as a class, a maker's board or a species, ungrounded unless the title names the class or the maker. It names no shop: a shop's package passes its rows. `tests/test_shops.py` holds it to titles shops actually write.

## Sources

The documents are copyrighted, so they are cited by locator and values and never quoted; the one exception is the Forest Products Laboratory's report, which is public domain and is quoted. The copies as fetched are kept in a private repo, and `tests/test_values.py` checks every value against them, a table's value against its row and column: clone that repo beside this one, or set `FURNITURE_REPO`, or that test fails and says why. Kronospan's and binderholz's declarations are scanned images; their values were read by eye and transcribed there, and the transcriptions say so. The standards themselves are not read: the class tables are taken from documents that say they print them, and a class figure is read as a mean, since none of them says whether it is a mean or a 5th percentile.

## Using it

```python
from furniture_design.knowledge import knowledge as general, merge
from wood_panels import knowledge as wood_panels

tree.root.children = merge(general(), wood_panels()) + [pieces]
```

A part then links `uses: ["materials/particleboard-p2-13-20"]` and states `span_along: "flat"`, or `uses: ["materials/riga-wood-birch-plywood-18-along"]` and `span_along: "face grain, flat"`.

## Design ledger

```sh
uv sync
uv run quern brief .
uv run quern check
```

The open debts: the standards are read at second hand, Thebault's data sheets disagree with its declaration, Thebault's moduli lack a shear modulus, and several boards have no screw-withdrawal value. There is no flight-recorder boundary: nothing here touches storage, the network, the clock or randomness at run time.

## Licence

- **The code** (`wood_panels/*.py`, `tests/`, `ledger/`) is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE), copyright 2026 Xavier Grehant.
- **The knowledge base**, the database `wood_panels.knowledge()` returns (documents.json and every value on its nodes), is licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0](LICENSE-DATA), database rights included, with one added permission: designing, building and selling furniture with it is allowed. An improvement is published here, through [CONTRIBUTING.md](CONTRIBUTING.md).
- **Authority**: every source says who stands behind it (furniture-design's `authority`): a board's own maker for its declarations, data sheets and handbooks, a distributor's copy included; research for the Forest Products Laboratory's paper and the University of Belgrade's; editorial for FH Bielefeld's Leporello. A shop's sitemap is the shop's own (maker).
- The makers' values and the standards' figures are cited from their documents, not licensed.

## Tests

`uv run pytest --testmon`, then `uv run pytest`. Both stop at the first failure.
