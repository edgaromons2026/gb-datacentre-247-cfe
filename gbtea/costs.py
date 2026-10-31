"""Corrected technology costs from the PyPSA technology-data tables (costs_YYYY.xlsx).

Fixes against the original notebook:
- Each row is inflated from its own currency year to 2024 euros (euro-area HICP), then
  converted at the 2024 EUR->GBP rate. Before, one 0.8544 factor mixed 2015 and 2020 euros.
- Battery energy (per kWh) and battery inverter (per kW, with its FOM) are kept apart.
- VOM is kept, not dropped.
- Gas carbon cost uses a fuel-based factor divided by efficiency once (was counted twice).
- Fuel and carbon prices after 2025 are no longer silently flat; pass a path explicitly.
"""
import numpy as np
import pandas as pd

from . import config as C

TECHS = ["onwind", "solar-utility", "solar-utility single-axis tracking", "battery storage",
         "battery inverter", "electrolysis", "fuel cell", "hydrogen storage tank type 1 including compressor",
         "hydrogen storage underground", "CCGT"]


def _inflator(currency_year):
    cy = int(currency_year) if pd.notna(currency_year) else 2020
    cy = min(max(cy, min(C.EUR_HICP)), max(C.EUR_HICP))
    return C.EUR_HICP[C.TARGET_PRICE_YEAR] / C.EUR_HICP[cy]


def load_costs(year, folder=C.ESM_2025):
    # Prefer the full PyPSA technology-data CSV; the Drive xlsx files only carry 9 technologies.
    csv = folder / f"costs_{year}.csv"
    df = pd.read_csv(csv, index_col=0) if csv.exists() else pd.read_excel(folder / f"costs_{year}.xlsx", index_col=0)
    df.index = df.index.str.strip()
    missing = sorted(set(TECHS) - set(df.index))
    if missing:
        print(f"costs_{year}: missing technologies {missing}")
    df = df[df.index.isin(TECHS)].copy()
    if "currency_year" not in df.columns:
        df["currency_year"] = np.nan
    money = df["unit"].astype(str).str.contains("EUR", case=False)
    factor = df["currency_year"].apply(_inflator) * C.EUR_TO_GBP_2024
    df["value_gbp2024"] = np.where(money, df["value"] * factor, df["value"])
    df["unit_gbp"] = df["unit"].astype(str).str.replace("EUR", "GBP2024", case=False)
    df["year"] = year
    df.index.name = "technology"
    return df.reset_index()


def tidy(df):
    """technology x parameter table of values in GBP2024 (money) or native units."""
    return df.pivot_table(index="technology", columns="parameter", values="value_gbp2024",
                          aggfunc="first")


def annuity(rate, lifetime):
    return rate / (1 - (1 + rate) ** -lifetime)


def annualised_capex(t, rate=C.DISCOUNT_RATE):
    """GBP2024 per unit-year: investment x annuity + FOM (% of investment)."""
    inv, life = t["investment"], t["lifetime"]
    fom = t.get("FOM", pd.Series(0.0, index=t.index)).fillna(0)
    return inv * annuity(rate, life) + inv * fom / 100.0


def gas_marginal_cost(gas_price_gbp_per_mwh_fuel, carbon_price_gbp_per_t,
                      efficiency=C.CCGT_EFFICIENCY, vom_gbp_per_mwh=0.0):
    """GBP per MWh of electricity. Emission factor is per MWh of FUEL, divided by efficiency once."""
    fuel = gas_price_gbp_per_mwh_fuel / efficiency
    carbon = C.GAS_EF_T_PER_MWH_FUEL * carbon_price_gbp_per_t / efficiency
    return {"fuel": fuel, "carbon": carbon, "vom": vom_gbp_per_mwh,
            "total": fuel + carbon + vom_gbp_per_mwh}
