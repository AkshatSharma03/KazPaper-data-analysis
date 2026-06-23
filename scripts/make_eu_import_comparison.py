#!/usr/bin/env python3
"""Create a China--EU+UK sectoral-import comparison for the PCE manuscript."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "wits_raw")
FIG = os.path.join(REPO, "figures", "pub_china_eu_uk_sectoral_imports_2024.pdf")
DTA = os.path.join(REPO, "analysis_v2", "dta", "china_eu_uk_import_sector_comparison_2024.dta")
VALUE = "TradeValuein1000USD"
EU_PLUS_UK = {"AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC",
              "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK",
              "SVN", "ESP", "SWE", "GBR"}
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


def load(path):
    data = pd.read_stata(path)
    data.columns = [column.replace(" ", "") for column in data.columns]
    data["ProductCode"] = data.ProductCode.astype(str)
    return data


imports = pd.concat([
    load(os.path.join(RAW, "kazakhstan_imports_all_partners_hs_sections_01_49_2015_2024_wits.dta")),
    load(os.path.join(RAW, "kazakhstan_imports_all_partners_hs_sections_50_99_2015_2024_wits.dta")),
], ignore_index=True)
data = imports[imports.Year.eq(2024)].copy()
data["sector"] = data.ProductCode.map(SECMAP)
world = data[data.PartnerISO3.eq("WLD")].groupby("sector")[VALUE].sum()
china = data[data.PartnerISO3.eq("CHN")].groupby("sector")[VALUE].sum()
eu_uk = data[data.PartnerISO3.isin(EU_PLUS_UK)].groupby("sector")[VALUE].sum()
comparison = pd.DataFrame({
    "China": china.div(world).mul(100),
    "EU+UK": eu_uk.div(world).mul(100),
}).fillna(0)
comparison = comparison.sort_values("China", ascending=True)
comparison.reset_index(names="sector").melt(
    id_vars="sector", var_name="partner", value_name="share_pct"
).to_stata(DTA, write_index=False)

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 11, "axes.linewidth": 0.8, "savefig.dpi": 300, "savefig.bbox": "tight"})
figure, axis = plt.subplots(figsize=(7, 5))
y = np.arange(len(comparison))
axis.barh(y - 0.2, comparison["China"], height=0.38, color="#9e2b25", label="China")
axis.barh(y + 0.2, comparison["EU+UK"], height=0.38, color="#3c7a5a", label="EU+UK")
axis.set_yticks(y)
axis.set_yticklabels(comparison.index, fontsize=9)
axis.set_xlabel("Share of Kazakhstan's sectoral imports, 2024 (%)")
axis.spines["top"].set_visible(False)
axis.spines["right"].set_visible(False)
axis.grid(axis="x", color="#d9d9d9", linewidth=0.6)
axis.set_axisbelow(True)
axis.legend(frameon=False, loc="lower right")
figure.savefig(FIG)
print(f"Wrote {DTA}")
print(f"Wrote {FIG}")
