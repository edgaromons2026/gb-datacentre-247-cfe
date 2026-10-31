# 24/7 carbon-free supply for data centres across Great Britain

Code for a techno-economic study of hourly-matched (24/7) carbon-free electricity for a 5 MW (IT) data centre in 20 GB zones, using PV, onshore wind, batteries and hydrogen storage, with and without a grid connection, over the ERA5 weather years 2000–2024.

The headline metric is the **levelised cost of 24/7 supply (LCO24/7)**, in £ per MWh of data-centre load.

## Contents

| Path | What it is |
|---|---|
| `gbtea/` | Model package: weather (ERA5, MIDAS), PV (pvlib), wind (windpowerlib), data-centre load and PUE, prices, technology costs, land screening, and the linear optimisation (`optimise.py`, linopy) |
| `run_corrected.py` | Builds the inputs: PV and wind profiles, load, sites, wholesale prices, costs, ERA5 vs MIDAS validation |
| `run_flagship.py` | Capacity-expansion runs: single-year designs, robust multi-year designs, grid adder and wind-loss cases |
| `run_stress.py` | Cross-year stress tests: each design operated with fixed capacities in every other weather year |
| `pick_critical_years.py` | Picks each zone's hardest weather years for the hourly robust design |
| `sens/` | Single-zone input sensitivities: `run_sens.py` (discount rate, ERA5 seasonal bias), `make_neso_g.py` (hourly carbon-free share of grid supply from NESO), monthly ERA5 bias factors |
| `run_chain/` | The Windows batch and PowerShell scripts that ran the steps in order on the author's PC |
| `analysis/` | Scripts that make the paper's tables and figures from the run outputs |
| `tests/` | Synthetic end-to-end and price-alignment tests |
| `CORRECTIONS.md` | Changes made to the original PV, wind, load and validation code |

## Installation

Python 3.11. A conda environment is easiest because of the geospatial packages:

```bash
conda create -n gbtea -c conda-forge python=3.11 geopandas rasterio pyproj cartopy glaes
conda activate gbtea
pip install -r requirements.txt
```

The linear programmes are solved with HiGHS through linopy. Gurobi can be used instead with `--solver gurobi` if a licence is available.

## Data

No data are included in this repository. The scripts read from a folder set with `--drive-root` (or the `GBTEA_DRIVE_ROOT` environment variable), laid out as in `gbtea/config.py`:

- `Energy_System_Modelling_GB/esm_GB_2025/`: ERA5 hourly single-level data for GB, 2000–2025 (one file per year), and the extracted site time series.
- `techno_econs_analysis_green_hydrogen_uk/`: MIDAS station observations (hourly radiation and weather), the station list, and GB market index prices (MIP) 2015–2025.
- Zone polygons (`zones_json.geojson`) and site lists.

Sources: ERA5 (Copernicus Climate Change Service), MIDAS (UK Met Office, via CEDA), Elexon market index prices, NESO historic generation mix and carbon intensity, and PyPSA technology-data v0.15.0 for costs. All outputs are written to `esm_GB_2025/corrected_v1/`.

## Run order

```bash
# 1. Inputs and validation
python run_corrected.py --drive-root "G:/My Drive"

# 2. Single-year designs, all zones and years (islanded 100% CFE; grid 90/95/99/100%)
python run_flagship.py --drive-root "G:/My Drive"

# 3. Cross-year stress tests
python run_stress.py --drive-root "G:/My Drive" --mode islanded
python run_stress.py --drive-root "G:/My Drive" --mode grid

# 4. Robust multi-year design (3 h steps), then its hourly check
python run_flagship.py --drive-root "G:/My Drive" --experiments robust --modes islanded --agg-hours 3 --tag main
python run_stress.py --drive-root "G:/My Drive" --mode islanded --from-designs robust_main.csv --tag main

# 5. Grid adder sensitivity (£30 and £70/MWh)
python run_flagship.py --drive-root "G:/My Drive" --modes grid --wind-loss 0.86 --grid-adder 30 --tag adder30
python run_flagship.py --drive-root "G:/My Drive" --modes grid --wind-loss 0.86 --grid-adder 70 --tag adder70

# 6. Hourly robust design on each zone's hardest years, then its hourly check
python pick_critical_years.py --drive-root "G:/My Drive" --n 5
python run_flagship.py --drive-root "G:/My Drive" --experiments robust --modes islanded --agg-hours 1 --years-file "<drive-root>/Energy_System_Modelling_GB/esm_GB_2025/corrected_v1/flagship/crit_years_5.csv" --tag crit5
python run_stress.py --drive-root "G:/My Drive" --mode islanded --from-designs robust_crit5.csv --tag crit5

# 7. Single-zone input sensitivities (see sens/sens_queue.ps1 for the full list)
python sens/run_sens.py flagship --rate 0.05 -- --drive-root "G:/My Drive" --zones Z10 --tag r05
```

The exact commands and arguments used for the paper are in `run_chain/` (steps 2 to 8) and `sens/sens_queue.ps1`. They contain the paths of the author's machine and need editing before reuse. A full 25-year design at 1 h steps (`run_chain/step7_robust1h.ps1`) was tried and stopped as too slow; step 8 replaces it.

Full runs take several days on a desktop PC. Runs are resumable: finished rows are skipped when a script is restarted.

## Licence

MIT, see `LICENSE`.
