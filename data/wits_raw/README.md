# data/wits_raw — raw trade inputs (World Bank WITS)

Self-contained raw inputs for the whole analysis pipeline. Every number in
`FinalVersion.tex` traces back to these files. All are direct World Bank
**WITS** (World Integrated Trade Solution) downloads, UN Comtrade reporting,
HS nomenclature, values in **1000 USD** (`TradeValuein1000USD`).

| File | Reporter | Flow / partner | Detail | WITS job |
|------|----------|----------------|--------|----------|
| `kazakhstan_exports_to_china_hs4_2015_2024_wits.dta`        | Kazakhstan | Exports → China        | HS-4 | 3100908 |
| `kazakhstan_exports_to_world_hs4_2015_2024_wits.dta`        | Kazakhstan | Exports → World         | HS-4 | 3100910 |
| `kazakhstan_exports_all_partners_hs4_2015_2024_wits.csv`    | Kazakhstan | Exports, all partners   | HS-4 | 3100911 |
| `kazakhstan_imports_from_china_hs4_2015_2024_wits.dta`      | Kazakhstan | Imports ← China         | HS-4 | 3100914 |
| `kazakhstan_imports_from_world_hs4_2015_2024_wits.dta`      | Kazakhstan | Imports ← World         | HS-4 | 3100916 |
| `kazakhstan_imports_china_world_hs4_2015_2024_wits_crosscheck.dta`     | Kazakhstan | Imports ← China and World | HS-4 cross-check extract | 3100919 |
| `kazakhstan_imports_all_partners_hs_sections_01_49_2015_2024_wits.dta`| Kazakhstan | Imports, all partners   | HS-section, chapters 01–49 | 3100965 |
| `kazakhstan_imports_all_partners_hs_sections_50_99_2015_2024_wits.dta`| Kazakhstan | Imports, all partners   | HS-section, chapters 50–99 | 3100966 |
| `china_imports_from_world_reference_2015_2024_wits.csv`          | China      | Imports ← World (TII denominator) | — | 3082405 |
| `world_imports_by_hs4_2015_2024_wits.csv`                | World      | Total world imports (TII denominator) | — | 3082411 |

Period: **2015–2024** (china/world reference series start 2012).

The current raw WITS files match the updated WITS download folder
`/Users/akshatsharma/Downloads/wits new data` byte-for-byte. The combined
China/world import cross-check extract from that same download is vendored as
an additional audit input: it is not needed to compute the published tables
because the standalone China and world import extracts already provide those
annual series separately.

## Why the all-partner import file is split in two
WITS caps a single query at **100,000 rows**. The original single-pull
all-partner import extract was silently truncated at that cap (sorted by HS
code, cut off mid-textiles), which dropped machinery/vehicles/metals and made
China's 2024 imports read ≈US$2.2bn instead of the true US$15.15bn. It was
re-pulled in two HS ranges (01–49 and 50–99); concatenated they are complete.
`build_import_partners.py` asserts the concatenation reproduces
China 2024 imports = 15.15bn, so the truncated file can never silently
re-enter the pipeline.

## Data correction (why this is the *corrected* series)
An earlier vintage of the bilateral series double-counted HS-2 chapter totals
together with HS-4 product rows, roughly doubling every bilateral figure
(e.g. 2024 total US$60bn vs the true ~US$30bn). These extracts use HS-4
product rows only (and de-duplicated HS-section for the all-partner imports),
reproducing Kazakhstan's official ~US$30bn 2024 total. Cross-checks are in
the replication pipeline.
