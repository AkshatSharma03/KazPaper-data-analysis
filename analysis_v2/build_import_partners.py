#!/usr/bin/env python3
"""
Import-side partner analysis, using the complete split all-partner import extracts
(data/wits_raw/kazakhstan_imports_all_partners_hs_sections_01_49_2015_2024_wits.dta and ..._hs50-99.dta),
pulled in two HS ranges to beat WITS's 100k-row cap. These are HS-section
granularity and complete: combined they reproduce China's true import totals
to 6 dp.

Adds to analysis_v2/dta/:
  * kazakhstan_partner_trade_china_russia_eu_uk_2015_2024.dta      China/Russia/EU+UK exports, imports, total, comparison-set shares
  * china_russia_import_sector_comparison_2024.dta  Russia & China import composition by section, 2024
"""
import os, glob
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "wits_raw")   # vendored WITS extracts (see data/wits_raw/README.md)
OUTD = os.path.join(REPO, "analysis_v2")
DTA = os.path.join(OUTD, "dta")
V = "TradeValuein1000USD"
YEARS = list(range(2015, 2025))
EU_PLUS_UK = {'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC',
              'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK',
              'SVN', 'ESP', 'SWE', 'GBR'}


def load(p):
    d = pd.read_stata(p) if p.endswith(".dta") else pd.read_csv(p)
    d.columns = [c.replace(" ", "") for c in d.columns]
    d["ProductCode"] = d.ProductCode.astype(str)
    return d


# imports: all-partner, split by HS range to beat WITS's 100k-row cap, then
# concatenated. (The original single-pull all-partner import extract was
# truncated at 100,000 rows; only these complete split files are vendored.)
imp = pd.concat([load(os.path.join(RAW, "kazakhstan_imports_all_partners_hs_sections_01_49_2015_2024_wits.dta")),
                 load(os.path.join(RAW, "kazakhstan_imports_all_partners_hs_sections_50_99_2015_2024_wits.dta"))],
                ignore_index=True)
assert abs(imp[(imp.Year == 2024) & (imp.PartnerISO3 == "CHN")][V].sum() / 1e6 - 15.153) < 0.02, \
    "split import files do not reproduce China 2024 = 15.15bn"
# exports: complete all-partner HS4 extract
exp = load(os.path.join(RAW, "kazakhstan_exports_all_partners_hs4_2015_2024_wits.csv"))


def grp(df):
    return np.where(df.PartnerISO3 == "CHN", "China",
           np.where(df.PartnerISO3 == "RUS", "Russia",
           np.where(df.PartnerISO3.isin(EU_PLUS_UK), "EU+UK", "Other")))


def partner_year(df):
    d = df.copy(); d["g"] = grp(d)
    return d.groupby(["Year", "g"])[V].sum().div(1e6).unstack().reindex(YEARS)[["China", "Russia", "EU+UK"]]


ex = partner_year(exp); im = partner_year(imp)
tot = ex + im
setsum = tot.sum(axis=1)
shares = tot.div(setsum, axis=0) * 100

print("=== Total-trade comparison-set shares (all-partner exports + split all-partner imports) ===")
out = pd.DataFrame(index=YEARS)
for p in ["China", "Russia", "EU+UK"]:
    out[p + "_total_bn"] = tot[p].round(2)
    out[p + "_setshare"] = shares[p].round(2)
print(out.to_string())

# save kazakhstan_partner_trade_china_russia_eu_uk_2015_2024.dta
pt = pd.DataFrame({"year": YEARS})
for p, stem in [("China", "china"), ("Russia", "russia"), ("EU+UK", "eu_uk")]:
    pt[stem + "_exp_bn"] = ex[p].values
    pt[stem + "_imp_bn"] = im[p].values
    pt[stem + "_total_bn"] = tot[p].values
    pt[stem + "_setshare_pct"] = shares[p].values
pt.to_stata(os.path.join(DTA, "kazakhstan_partner_trade_china_russia_eu_uk_2015_2024.dta"), write_index=False)

# ---- Russia & China import composition by section, 2024 -----------------
SECMAP = {
    "01-05_Animal": "Agriculture/food", "06-15_Vegetable": "Agriculture/food",
    "16-24_FoodProd": "Agriculture/food", "25-26_Minerals": "Metals/minerals",
    "27-27_Fuels": "Energy", "28-38_Chemicals": "Chemicals",
    "39-40_PlastiRub": "Plastics/rubber", "41-43_HidesSkin": "Other",
    "44-49_Wood": "Wood/paper", "50-63_TextCloth": "Textiles",
    "64-67_Footwear": "Other", "68-71_StoneGlas": "Stone/precious",
    "72-83_Metals": "Metals/minerals", "84-85_MachElec": "Machinery/electrical",
    "86-89_Transport": "Vehicles/transport", "90-99_Miscellan": "Miscellaneous",
}
rows = []
for code, lbl in [("CHN", "China"), ("RUS", "Russia")]:
    d = imp[(imp.Year == 2024) & (imp.PartnerISO3 == code)].copy()
    d["sec"] = d.ProductCode.map(SECMAP)
    s = d.groupby("sec")[V].sum()
    tot_p = s.sum()
    sh = (s / tot_p * 100).sort_values(ascending=False)
    hhi = ((s / tot_p) ** 2).sum()
    print(f"\n=== {lbl} 2024 imports = {tot_p/1e6:.2f}bn; section-HHI = {hhi:.3f} ===")
    print("; ".join(f"{k} {v:.1f}%" for k, v in sh.head(6).items()))
    for k, v in sh.items():
        rows.append({"partner": lbl, "sector": k, "share_pct": round(v, 2), "value_bn": round(s[k] / 1e6, 3)})
pd.DataFrame(rows).to_stata(os.path.join(DTA, "china_russia_import_sector_comparison_2024.dta"), write_index=False)
print("\nWROTE kazakhstan_partner_trade_china_russia_eu_uk_2015_2024.dta, china_russia_import_sector_comparison_2024.dta")

# ============================ FIGURES =======================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
FIG = os.path.join(REPO, "figures")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 11, "axes.linewidth": 0.8, "savefig.dpi": 300, "savefig.bbox": "tight"})
NAVY, RED, GREEN, GRAY = "#1f3b5c", "#9e2b25", "#3c7a5a", "#7a7a7a"


def finish(ax, ylabel):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_ylabel(ylabel); ax.set_xlabel("Year")
    ax.grid(axis="y", color="#d9d9d9", lw=0.6); ax.set_axisbelow(True)


def band(ax):
    ax.axvspan(2019.6, 2022.4, color="#000000", alpha=0.05)


def save(fig, n):
    fig.savefig(os.path.join(FIG, n + ".pdf")); plt.close(fig)
    print("fig", n)


# ii2a: multivector comparison-set shares
fig, ax = plt.subplots(figsize=(7, 4.2)); band(ax)
ax.plot(YEARS, shares["EU+UK"], color=GREEN, lw=2, marker="^", ms=4, label="EU+UK")
ax.plot(YEARS, shares["Russia"], color=NAVY, lw=2, marker="o", ms=4, label="Russia")
ax.plot(YEARS, shares["China"], color=RED, lw=2, marker="s", ms=4, label="China")
finish(ax, "Share of China--Russia--EU trade (\\%)"); ax.set_xticks(YEARS); ax.set_ylim(0, 60)
ax.legend(frameon=False, ncol=3, loc="lower center")
save(fig, "pub_multivector_shares")

# ii2b: China vs Russia total trade (value)
fig, ax = plt.subplots(figsize=(7, 4.2)); band(ax)
ax.plot(YEARS, tot["China"], color=RED, lw=2, marker="s", ms=4, label="China (total trade)")
ax.plot(YEARS, tot["Russia"], color=NAVY, lw=2, marker="o", ms=4, label="Russia (total trade)")
finish(ax, "Total bilateral trade (US\\$ billions)"); ax.set_xticks(YEARS); ax.set_ylim(0, None)
ax.legend(frameon=False, loc="upper left")
save(fig, "pub_china_russia_trade")

# iv2a: sectoral import penetration 2024 — China & Russia share of KAZ imports by sector.
# For sectors that combine multiple WITS section rows, use value-weighted shares:
# partner sector imports / Kazakhstan world imports in the same sector.
d2024 = imp[imp.Year == 2024].copy()
d2024["sector"] = d2024.ProductCode.map(SECMAP)
wld = d2024[d2024.PartnerISO3 == "WLD"].groupby("sector")[V].sum()
chn = d2024[d2024.PartnerISO3 == "CHN"].groupby("sector")[V].sum()
rus = d2024[d2024.PartnerISO3 == "RUS"].groupby("sector")[V].sum()
pen = pd.DataFrame({"China": chn / wld * 100, "Russia": rus / wld * 100}).dropna()
pen = pen.sort_values("China", ascending=True)
fig, ax = plt.subplots(figsize=(7, 5)); y = np.arange(len(pen))
ax.barh(y - 0.2, pen.China, height=0.38, color=RED, label="China")
ax.barh(y + 0.2, pen.Russia, height=0.38, color=NAVY, label="Russia")
ax.set_yticks(y); ax.set_yticklabels(pen.index, fontsize=9)
ax.set_xlabel("Share of Kazakhstan's sectoral imports, 2024 (\\%)")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", color="#d9d9d9", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right")
save(fig, "pub_sectoral_penetration")
print("done figures")
