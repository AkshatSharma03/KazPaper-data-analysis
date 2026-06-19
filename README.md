# Kazakhstan-China Trade Analysis, 2015-2024

Self-contained replication repository for the quantitative analysis and
publication figures supporting the Kazakhstan-China trade study.

## Contents

```
data/wits_raw/                vendored World Bank WITS / UN Comtrade extracts
analysis_v2/
  build_analysis.py           bilateral panel, TII, RCA-style, concentration,
                              sectoral, regression, and export-comparison outputs
  build_import_partners.py    China/Russia/EU+UK import-side comparison outputs
  dta/                        generated Stata panels
  numbers_report.txt          human-readable computed-output report
scripts/make_publication_figures.py
figures/pub_*.pdf             publication figures
run_all.sh                    end-to-end reproduction entrypoint
```

## Reproduce

Requires Python 3 with `pandas`, `numpy`, `statsmodels`, `scipy`, and
`matplotlib`.

```bash
./run_all.sh
```

The pipeline uses only the vendored extracts in `data/wits_raw/`. The
China-Russia-EU+UK comparison set retains the United Kingdom consistently over
2015-2024; generated files use the `eu_uk` name to make that definition
explicit.

## Data

Raw-input provenance and WITS job identifiers are documented in
`data/wits_raw/README.md`. Values are reported in thousands of US dollars in
the source extracts. The analysis converts them to US-dollar billions where
noted in the generated panels and figures.
