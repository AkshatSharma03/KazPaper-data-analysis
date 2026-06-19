#!/usr/bin/env python3
"""
Master analysis for "FinalVersion.tex", built from the corrected WITS
extracts (2015-2024) vendored in data/wits_raw/ (see that folder's README
for provenance and WITS query IDs).

Produces:
  * clean Stata .dta files            -> analysis_v2/dta/
  * a human-readable numbers report   -> analysis_v2/numbers_report.txt
  * (figures are produced by make_publication_figures.py, which imports the
     panels written here)

Validated: the Kazakhstan-China and Kazakhstan-world export/import extracts
reproduce the corrected Table 8 bilateral series to 6 dp.
Data-quality note: WITS's original single-pull all-partner import extract is
truncated at 100,000 rows (China 2024 imports read 2.17bn vs the true
15.15bn), so import-side partner shares are computed only from the complete
split all-partner import extracts in build_import_partners.py. The all-partner
export extract is complete and is used here.
"""
import os, glob
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "wits_raw")   # vendored WITS extracts (see data/wits_raw/README.md)
OUTD = os.path.join(REPO, "analysis_v2")
DTA = os.path.join(OUTD, "dta")
os.makedirs(DTA, exist_ok=True)
V = "TradeValuein1000USD"
REPORT = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    REPORT.append(s)


def norm(df):
    df.columns = [c.replace(" ", "") for c in df.columns]
    return df


def load_wits(fname):
    f = os.path.join(RAW, fname)
    d = pd.read_stata(f) if f.endswith(".dta") else pd.read_csv(f)
    return norm(d)


def chap(code):
    s = str(code).strip()
    s = "".join(ch for ch in s if ch.isdigit())
    if not s:
        return None
    if len(s) % 2 == 1:
        s = "0" + s
    return int(s[:2])


SECTOR = {}
for c in range(1, 25):
    SECTOR[c] = "Agriculture"
SECTOR[27] = "Energy"
for c in range(28, 39):
    SECTOR[c] = "Chemicals"
for c in (39, 40):
    SECTOR[c] = "Plastics_Rubber"
for c in range(44, 50):
    SECTOR[c] = "Wood_Paper"
for c in range(50, 64):
    SECTOR[c] = "Textiles"
for c in (68, 69, 70):
    SECTOR[c] = "Stone_Ceramics"
SECTOR[26] = "Metals_Minerals"
for c in range(71, 84):
    SECTOR[c] = "Metals_Minerals"
for c in (84, 85):
    SECTOR[c] = "Machinery_Electrical"
SECTOR[87] = "Vehicles"


def sector_of(code):
    return SECTOR.get(chap(code), "Other")


# ---------------------------------------------------------------- load
e1 = load_wits("kazakhstan_exports_to_china_hs4_2015_2024_wits.dta")      # KAZ exports to China, HS4
e2 = load_wits("kazakhstan_exports_to_world_hs4_2015_2024_wits.dta")      # KAZ exports to world, HS4
i1 = load_wits("kazakhstan_imports_from_china_hs4_2015_2024_wits.dta")    # KAZ imports from China, HS4
i2 = load_wits("kazakhstan_imports_from_world_hs4_2015_2024_wits.dta")    # KAZ imports from world, HS4
e3 = load_wits("kazakhstan_exports_all_partners_hs4_2015_2024_wits.csv")  # KAZ exports, all partners, HS4 (reliable)

YEARS = list(range(2015, 2025))


def by_year(df):
    return df.groupby("Year")[V].sum().div(1e6).reindex(YEARS)


exp = by_year(e1); imp = by_year(i1)
expW = by_year(e2); impW = by_year(i2)

# ---------------------------------------------------------------- panel
panel = pd.DataFrame({
    "year": YEARS,
    "exports_bn": exp.values,
    "imports_bn": imp.values,
}).assign(
    total_trade_bn=lambda d: d.exports_bn + d.imports_bn,
    trade_balance=lambda d: d.exports_bn - d.imports_bn,
)
panel["balance_ratio"] = (panel.exports_bn - panel.imports_bn) / (panel.exports_bn + panel.imports_bn)
panel["kaz_world_exports_bn"] = expW.values
panel["kaz_world_imports_bn"] = impW.values
panel["chn_exp_share_pct"] = panel.exports_bn / panel.kaz_world_exports_bn * 100
panel["chn_imp_share_pct"] = panel.imports_bn / panel.kaz_world_imports_bn * 100
panel["t"] = panel.year - 2015
panel["post2020"] = (panel.year >= 2020).astype(int)
panel.to_stata(os.path.join(DTA, "kazakhstan_china_annual_trade_panel_2015_2024.dta"), write_index=False)
log("=== PANEL (corrected, new data) ===")
log(panel.round(3).to_string(index=False))

# ---------------------------------------------------------------- TII
tii_raw = norm(pd.read_csv(os.path.join(RAW, "china_imports_from_world_reference_2015_2024_wits.csv")))
world = norm(pd.read_csv(os.path.join(RAW, "world_imports_by_hs4_2015_2024_wits.csv")))
chn_world_imp = tii_raw.groupby("Year")[V].sum().div(1e6).reindex(YEARS)
world_imp = world.groupby("Year")[V].sum().div(1e6).reindex(YEARS)
chn_world_imp_share = chn_world_imp / world_imp * 100
tii = panel.chn_exp_share_pct.values / chn_world_imp_share.values
tii_df = pd.DataFrame({"year": YEARS,
                       "kaz_exp_share_to_chn_pct": panel.chn_exp_share_pct.values,
                       "chn_world_import_share_pct": chn_world_imp_share.values,
                       "tii": tii})
tii_df.to_stata(os.path.join(DTA, "kazakhstan_china_trade_intensity_index_2015_2024.dta"), write_index=False)
log("\n=== TII ===")
log(tii_df.round(3).to_string(index=False))

# ---------------------------------------------------------------- RCA-style specialization index (2015 & 2024)
# KAZ world exports by sector / KAZ total world exports, against WITS world
# imports by sector. This uses world import demand as the reference distribution
# because the vendored WITS reference extract is world_imports_by_hs4_2015_2024_wits.csv.
e2c = e2.copy(); e2c["sector"] = e2c.ProductCode.map(sector_of)
worldc = world.copy(); worldc["sector"] = worldc.ProductCode.map(sector_of)


def rca_year(yr):
    k = e2c[e2c.Year == yr].groupby("sector")[V].sum()
    kt = k.sum()
    w = worldc[worldc.Year == yr].groupby("sector")[V].sum()
    wt = w.sum()
    return (k / kt) / (w / wt)


rca = pd.DataFrame({"rca_2015": rca_year(2015), "rca_2024": rca_year(2024)})
order = ["Metals_Minerals", "Chemicals", "Agriculture", "Textiles",
         "Machinery_Electrical", "Plastics_Rubber", "Energy", "Vehicles", "Wood_Paper"]
rca = rca.reindex(order)
rca.reset_index().rename(columns={"index": "sector"}).to_stata(
    os.path.join(DTA, "kazakhstan_rca_style_export_specialization_by_sector.dta"), write_index=False)
log("\n=== RCA (world reference = world imports by sector) ===")
log(rca.round(3).to_string())

# ---------------------------------------------------------------- concentration / HHI
def conc(df, yr):
    s = df[df.Year == yr].groupby("ProductCode")[V].sum().sort_values(ascending=False)
    tot = s.sum()
    sh = s / tot
    return dict(top5=sh.head(5).sum() * 100, top10=sh.head(10).sum() * 100, hhi=(sh ** 2).sum())


conc_rows = []
for yr in YEARS:
    ce = conc(e1, yr); ci = conc(i1, yr)
    conc_rows.append({"year": yr, "exp_top5_pct": ce["top5"], "exp_top10_pct": ce["top10"],
                      "exp_hhi": ce["hhi"], "imp_top5_pct": ci["top5"], "imp_top10_pct": ci["top10"],
                      "imp_hhi": ci["hhi"]})
conc_df = pd.DataFrame(conc_rows)
conc_df.to_stata(os.path.join(DTA, "kazakhstan_china_hs4_concentration_2015_2024.dta"), write_index=False)
log("\n=== CONCENTRATION / HHI (bilateral, HS4) ===")
log(conc_df.round(3).to_string(index=False))
# world-reference HHI 2024 (export & import baskets vs world)
we = e2[e2.Year == 2024].groupby("ProductCode")[V].sum(); we = (we / we.sum())
wi = i2[i2.Year == 2024].groupby("ProductCode")[V].sum(); wi = (wi / wi.sum())
log(f"world-export HHI 2024 = {(we**2).sum():.3f}; world-import HHI 2024 = {(wi**2).sum():.3f}")

# ---------------------------------------------------------------- sectoral composition (China)
def sect(df, flow):
    d = df.copy(); d["sector"] = d.ProductCode.map(sector_of)
    return d.groupby(["Year", "sector"])[V].sum().div(1e6).reset_index().rename(columns={V: flow})


se = sect(e1, "exports_bn"); si = sect(i1, "imports_bn")
sectoral = pd.merge(se, si, on=["Year", "sector"], how="outer").fillna(0)
sectoral.rename(columns={"Year": "year"}).to_stata(os.path.join(DTA, "kazakhstan_china_sectoral_trade_2015_2024.dta"), write_index=False)

# ---------------------------------------------------------------- export partner shares (complete all-partner export extract)
EU_PLUS_UK = {'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC',
              'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK',
              'SVN', 'ESP', 'SWE', 'GBR'}
e3c = e3.copy()
e3c["grp"] = np.where(e3c.PartnerISO3 == "CHN", "China",
              np.where(e3c.PartnerISO3 == "RUS", "Russia",
              np.where(e3c.PartnerISO3.isin(EU_PLUS_UK), "EU+UK", "Other")))
pe = e3c.groupby(["Year", "grp"])[V].sum().div(1e6).unstack().reindex(YEARS)
# comparison-set shares (export side) among China/Russia/EU+UK
partners = ["China", "Russia", "EU+UK"]
stems = {"China": "china", "Russia": "russia", "EU+UK": "eu_uk"}
cmp_tot = pe[partners].sum(axis=1)
pe_share = pe[partners].div(cmp_tot, axis=0) * 100
part = pe[["China", "Russia", "EU+UK"]].copy()
part.columns = ["exp_china_bn", "exp_russia_bn", "exp_eu_uk_bn"]
pe_share.columns = [f"{stems[c]}_setshare_pct" for c in pe_share.columns]
part = part.join(pe_share)
part.reset_index().rename(columns={"Year": "year"}).to_stata(
    os.path.join(DTA, "kazakhstan_partner_exports_china_russia_eu_uk_2015_2024.dta"), write_index=False)
log("\n=== EXPORT-SIDE partner values (bn) and comparison-set shares (%) ===")
log(part.round(2).to_string())

# Russia export sectoral composition 2024 + KAZ export-line count to CHN vs RUS
e3c["sector"] = e3c.ProductCode.map(sector_of)
log("\n=== Russia vs China KAZ EXPORT sectoral shares 2024 (%) ===")
for grp in ["China", "Russia"]:
    d = e3c[(e3c.grp == grp) & (e3c.Year == 2024)]
    sh = d.groupby("sector")[V].sum().sort_values(ascending=False)
    sh = (sh / sh.sum() * 100).round(1)
    log(f"  {grp}: " + "; ".join(f"{k} {v}" for k, v in sh.head(4).items()))
for grp, code in [("China", "CHN"), ("Russia", "RUS")]:
    d = e3[(e3.PartnerISO3 == code) & (e3.Year == 2024)]
    n = (d.groupby("ProductCode")[V].sum() >= 1000).sum()  # >=1m USD lines
    log(f"  KAZ 2024 export lines >=US$1m to {grp}: {n}")

# ---------------------------------------------------------------- regression
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from scipy.stats import t as tdist
tb = panel.trade_balance.values; tt = panel.t.values.astype(float); post = panel.post2020.values.astype(float)
m1 = sm.OLS(tb, sm.add_constant(tt)).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
m2 = sm.OLS(tb, sm.add_constant(np.column_stack([tt, post]))).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
log("\n=== REGRESSION (corrected trade balance) ===")
log(f"M1 trend {m1.params[1]:+.3f} (se {m1.bse[1]:.3f}, p {2*(1-tdist.cdf(abs(m1.tvalues[1]),8)):.3f}), R2 {m1.rsquared:.3f}")
log(f"M2 trend {m2.params[1]:+.3f} (se {m2.bse[1]:.3f}); post2020 {m2.params[2]:+.3f} (se {m2.bse[2]:.3f}, p {2*(1-tdist.cdf(abs(m2.tvalues[2]),7)):.3f}); adjR2 {m2.rsquared_adj:.3f}")
for nm, col in [("trade_balance", "trade_balance"), ("balance_ratio", "balance_ratio"), ("total", "total_trade_bn")]:
    r = adfuller(panel[col].values, maxlag=1, autolag=None)
    log(f"ADF {nm}: stat {r[0]:+.3f} p {r[1]:.3f}")

# China import penetration note
log("\n=== China import penetration (share of KAZ world imports, %) ===")
log(panel[["year", "chn_imp_share_pct"]].round(1).to_string(index=False))

# ---------------------------------------------------------------- write report
with open(os.path.join(OUTD, "numbers_report.txt"), "w") as f:
    f.write("\n".join(REPORT))
log("\nWROTE dta ->", DTA)
log("WROTE report ->", os.path.join(OUTD, "numbers_report.txt"))
