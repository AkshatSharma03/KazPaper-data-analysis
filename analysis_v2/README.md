# analysis_v2 — rebuilt analysis on the updated WITS extracts (2015–2024)

Built from the vendored WITS extracts in `../data/wits_raw/` (see that folder's
README for provenance/query IDs), which reproduce the corrected
Kazakhstan-reported bilateral series to 6 dp. The pipeline is self-contained:
run `../run_all.sh` from the repo root.

## Scripts
- `build_analysis.py` — loads the queries, validates against the corrected
  series, computes every index, writes the Stata files below and
  `numbers_report.txt`.
- `../scripts/make_publication_figures.py` — generates the publication figures
  (`figures/pub_*.pdf`) from these panels.

## Stata files (`dta/`)
| file | contents |
|------|----------|
| `kazakhstan_china_annual_trade_panel_2015_2024.dta` | annual exports/imports/total/balance, balance ratio, KAZ world exports/imports, China shares of KAZ world trade, t, post2020 |
| `kazakhstan_china_trade_intensity_index_2015_2024.dta` | Trade Intensity Index inputs and values, 2015–2024 |
| `kazakhstan_rca_style_export_specialization_by_sector.dta` | Revealed Comparative Advantage by sector, 2015 & 2024 |
| `kazakhstan_china_hs4_concentration_2015_2024.dta` | export/import top-5, top-10, HHI (HS4), all years |
| `kazakhstan_china_sectoral_trade_2015_2024.dta` | bilateral exports/imports by sector, all years |
| `kazakhstan_partner_exports_china_russia_eu_uk_2015_2024.dta` | China/Russia/EU+UK **export** values and comparison-set shares from the complete all-partner export extract |

## Import-side partner data — split all-partner extract
WITS caps a query at 100,000 rows, which truncated the original single-pull
all-partner import extract (dropping machinery/vehicles/metals; China 2024 read
US$2.17bn vs the true US$15.15bn). It was re-pulled in two HS ranges —
`kazakhstan_imports_all_partners_hs_sections_01_49_2015_2024_wits.dta` and `..._hs50-99.dta` in
`../data/wits_raw/` — at HS-**section** granularity. Combined they are complete
and reproduce China's true import totals to 6 dp (16.772bn 2023, 15.153bn 2024).
`build_import_partners.py` uses these (with a hard assert on the China total)
and writes `kazakhstan_partner_trade_china_russia_eu_uk_2015_2024.dta` and `china_russia_import_sector_comparison_2024.dta`, plus the three
import-side figures. The extract contains a `WLD` aggregate row (≈59.8bn in
2024) alongside countries — it is excluded; individual partners (CHN/RUS/EU) are clean.

All four previously-flagged components are now re-based and the `[TODO]` flags
are cleared:
1. §5.1 total-trade comparison-set shares, using EU+UK for consistency across 2015--2024 (2015 China 19.0/Russia 27.1/EU+UK 53.8; 2024 28.7/26.6/44.7)
2. §7.1 Russia import value (18.25bn), sectoral shares, import HHI (0.122)
3. Figures ii2a (`pub_multivector_shares`), ii2b (`pub_china_russia_trade`), iv2a (`pub_sectoral_penetration`)

The whole paper is now re-based on the corrected data with 10 publication figures.
