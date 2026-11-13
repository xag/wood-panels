# wood-panels

Wood panels as data for [furniture-design](https://github.com/xag/furniture-design): the standard classes a board's strength belongs to, and the makers' declared boards. **Unofficial**: the makers and the standards bodies did not write or endorse it, and nothing here speaks for them.

## What is here

- **The classes**: a particleboard, MDF or OSB board's strength is its class's. A maker declares that its board meets a class and prints the class's figures: Finsa's FimaPan and Unilin's Belspan both declare 11 MPa and 1800 MPa from 6 to 13 mm, the P2 row of EN 312. So there is one material per class and thickness band: particleboard P2 and P3 (EN 312:2010), MDF (EN 622-5:2009, Table 3) and OSB/3 (EN 12369-1's characteristic values), as `materials/<class>-<band>` (`particleboard-p2-13-20`, `mdf-12-19`, `osb-3-10-18-major`). A class sets no density, so a class material borrows the lowest a maker's board of that class states in its band, ungrounded.
- **The makers' boards**: twenty-three documents, mostly Declarations of Performance: Finsa (FimaPan E-Z, FimaPan H E-Z, FimaPlast E-Z, FibraPan E-Z), Unilin (Belspan), Valchromat, Betanzos (hardboard), Kronospan and Swiss Krono (OSB/3), Riga Wood (birch plywood), Garnica and Toro (poplar), Thebault (okoumé, twin, pine), binderholz (3-ply spruce) and Houtwerf (Powerplex), and the documents the classes are read from (Koskisen's chipboard handbook, Kastamonu's P3 data sheet, Swiss Krono's particleboard and MDF pages). One material per board and thickness band as declared, `materials/<product>-<band>` (`finsa-fimapan-ez-13-20`, `riga-wood-birch-plywood-18-along`). Plywood has no class with figures, so its values are always a maker's.
- A board that bends differently along and across is two materials: `-along`/`-across` for plywood and 3-ply, `-major`/`-minor` for OSB, linked by `same_panel_as`.

No kinds and no rules of its own: a part that `uses` one of these materials is judged by furniture-design's rules. No shop either: a shop's package, such as [leroy-merlin-unofficial](https://github.com/xag/leroy-merlin-unofficial), says which class or maker board each of its lines is.

## Sources

The documents are copyrighted, so they are cited by locator and values and never quoted. The copies as fetched are kept in a private repo, and `tests/test_values.py` checks every value against them, a table's value against its row and column: clone that repo beside this one, or set `FURNITURE_REPO`, or that test fails and says why. Kronospan's and binderholz's declarations are scanned images; their values were read by eye and transcribed there, and the transcriptions say so. The standards themselves are not read: the class tables are taken from documents that say they print them, and a class figure is read as a mean, since none of them says whether it is a mean or a 5th percentile.

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

The open debts: the standards are read at second hand, Thebault's data sheets disagree with its declaration, and Thebault's moduli lack a shear modulus. There is no flight-recorder boundary: nothing here touches storage, the network, the clock or randomness at run time.

## Licence

- **The code** (`wood_panels/*.py`, `tests/`, `ledger/`) is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE), copyright 2026 Xavier Grehant.
- **The knowledge base**, the database `wood_panels.knowledge()` returns (documents.json and every value on its nodes), is licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0](LICENSE-DATA), database rights included, with one added permission: designing, building and selling furniture with it is allowed. An improvement is published here, through [CONTRIBUTING.md](CONTRIBUTING.md).
- The makers' values and the standards' figures are cited from their documents, not licensed.

## Tests

`uv run pytest --testmon`, then `uv run pytest`. Both stop at the first failure.
