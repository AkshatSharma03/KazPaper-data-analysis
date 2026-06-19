#!/usr/bin/env bash
# Reproduce the full analysis from raw WITS data (data/wits_raw/).
# Requires: python3 with pandas numpy statsmodels scipy matplotlib.
set -euo pipefail
cd "$(dirname "$0")"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/kazpaper-matplotlib}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${TMPDIR:-/tmp}/kazpaper-cache}"
mkdir -p "$MPLCONFIGDIR"
mkdir -p "$XDG_CACHE_HOME"
echo "[1/3] build_analysis.py";        python3 analysis_v2/build_analysis.py
echo "[2/3] build_import_partners.py"; python3 analysis_v2/build_import_partners.py
echo "[3/3] make_publication_figures.py"; python3 scripts/make_publication_figures.py
echo "Done. Outputs: analysis_v2/dta/, analysis_v2/numbers_report.txt, figures/pub_*"
