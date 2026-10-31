"""Paths and modelling constants for the corrected GB solar/wind/data-centre pipeline.

Every value that changed from the original notebook is marked FIX, with the review item it answers.
The data root is read from the GBTEA_DRIVE_ROOT environment variable (run_corrected.py sets it),
so the same code runs on Windows, Linux or Colab.
"""
import os
from pathlib import Path

# --- Paths ------------------------------------------------------------------------------
# Folder that holds Energy_System_Modelling_GB and techno_econs_analysis_green_hydrogen_uk,
# e.g. "G:/My Drive" with Google Drive for desktop. Defaults to the Colab mount.
DRIVE_ROOT = Path(os.environ.get("GBTEA_DRIVE_ROOT", "/content/gdrive/MyDrive"))
ESM = DRIVE_ROOT / "Energy_System_Modelling_GB"
ESM_2025 = ESM / "esm_GB_2025"
ERA5_2000_2025 = ESM_2025 / "ERA5_Extracted_2000_2025"
ERA5_2015_2025 = ESM_2025 / "ERA5_Extracted_2015_2025"
MIDAS_DIR = DRIVE_ROOT / "techno_econs_analysis_green_hydrogen_uk"
OPTIMAL_SITES = ERA5_2000_2025 / "optimal_sites.csv"
MIDAS_STATIONS = MIDAS_DIR / "df_midas_stations_updated.csv"
PRICE_RAW = MIDAS_DIR / "electricity_price_data_2015_2025.csv"

# All corrected outputs go to a new folder; nothing existing is overwritten.
OUT = ESM_2025 / "corrected_v1"

# --- Time ------------------------------------------------------------------------------
# FIX (DST alignment): every series is held on a UTC hourly index labelled at hour END,
# which is how ERA5 accumulations and MIDAS hourly totals are stamped.
TZ = "UTC"
ERA5_END = "2025-07-31 23:00"

# --- PV system (5 MWp CdTe, First Solar FS-4117-3) ---------------------------------------
MODULE = "First_Solar__Inc__FS_4117_3"
INVERTER = "Power_Electronics__FS1901CU__420V_"
MODULES_PER_STRING = 15
STRINGS_PER_INVERTER = 1419
N_INVERTER_BLOCKS = 2  # FIX (capacity factor): the plant is two identical blocks
MODULE_LENGTH_M = 1.2  # collector width, portrait, one module high
PITCH_M = 3.0
GCR = MODULE_LENGTH_M / PITCH_M  # FIX (GCR from one station's latitude): 0.40 from geometry
AXIS_HEIGHT_M = 1.5
FIXED_TILT_DEG = 35.0  # FIX (horizontal "fixed tilt"): real tilt, south-facing
FIXED_AZIMUTH_DEG = 180.0
TRACKER_MAX_ANGLE = 60.0
TRACKER_BACKTRACK = False  # kept as in the original design
FAIMAN = dict(u0=25.0, u1=6.84)
MODULE_UNIT_MASS = 12 / 0.72  # kg/m2
PVWATTS_LOSSES = dict(shading=0, availability=0)
MIDAS_ALBEDO = 0.20  # FIX (unequal comparison): see pv.py, used only when no ERA5 albedo given
DECOMPOSITION = "erbs"  # FIX (clear-sky DNI/DHI): measured GHI is split, never clear-sky

# --- Wind ------------------------------------------------------------------------------
# Original cluster kept for continuity, plus a modern utility turbine.
E53_CLUSTER = dict(turbine="E-53/800", hub_height=60, n_farms=2, n_per_farm=6, efficiency=0.9)
MODERN_TURBINE = dict(turbine="V126/3450", hub_height=100)
ROUGHNESS_CLIP_M = (0.0002, 0.5)  # ERA5 forecast roughness is clipped; it includes orography
LAPSE_RATE_K_PER_M = -0.0065

# --- Costs -----------------------------------------------------------------------------
COST_YEARS = [2025, 2030, 2035, 2040, 2045, 2050]
TARGET_PRICE_YEAR = 2024  # all costs expressed in 2024 GBP
# FIX (currency years mixed): euro-area HICP annual averages, 2015 = 100 (Eurostat prc_hicp_aind).
# Check against the latest Eurostat release before publication.
EUR_HICP = {2015: 100.0, 2016: 100.2, 2017: 101.8, 2018: 103.6, 2019: 104.8, 2020: 105.1,
            2021: 107.8, 2022: 116.8, 2023: 123.1, 2024: 126.0,
            2025: 128.6}  # 2025: approx. (2024 x 1.021); technology-data v0.15 rows are in 2025 EUR. VERIFY
EUR_TO_GBP_2024 = 0.8466  # 2024 average ECB reference rate; verify before publication
DISCOUNT_RATE = 0.07

# FIX (doubled carbon cost): fuel-based emission factor for natural gas, t CO2 per MWh of fuel
# (DESNZ GHG conversion factors, gross CV). Divided by efficiency once.
GAS_EF_T_PER_MWH_FUEL = 0.1829
CCGT_EFFICIENCY = 0.57  # from the PyPSA cost file, so cost and efficiency come from one source

# --- Data-centre load ------------------------------------------------------------------
IT_LOAD_KW = 5000.0
PUE_BASE = 1.12  # free-cooling floor
PUE_SLOPE_PER_K = 0.010  # rise per K above the free-cooling threshold
PUE_T_THRESHOLD_C = 15.0
PUE_MAX = 1.45

# --- MIDAS station filter --------------------------------------------------------------
# FIX (non-GB stations): Northern Ireland and Isle of Man stations are dropped.
NON_GB_STATIONS = {"ALDERGROVE", "BALLYPATRICK", "MAGILLIGAN", "THOMASTOWN", "RONALDSWAY"}
MIN_COMPLETENESS = 0.8  # FIX (closed stations): keep station-years with >= 80 % valid hours

# --- Solver ---
# 2 (was 4) after repeated power-cut shutdowns under full CPU load (29 Oct); fewer threads, less heat/power.
SOLVER_THREADS = 2

# --- Wind losses (flagship) ---
# FIX (optimistic wind): V126 CFs of 0.39-0.43 at lowland sites had no losses applied.
WIND_LOSS_FACTOR = 0.86  # wakes, availability, electrical losses; OPEN: GB calibration as sensitivity

# --- Grid (flagship, grid-connected case) ---
# OPEN DECISION: non-energy charges on imports (network, policy, levies), GBP/MWh on top of MIP. Placeholder.
GRID_ADDER_GBP_PER_MWH = 50.0
# Connection capacity cost (TNUoS-like), GBP per kW-yr. Placeholder.
GRID_CONNECTION_GBP_PER_KW_YR = 0.0
