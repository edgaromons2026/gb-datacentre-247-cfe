# Corrections log (v1, 23 Oct 2026)

The original notebook (`03_Models/Simulating_And_Valiadting_PV_And_Wind_...ipynb`) is unchanged. The corrected code is the `gbtea` package plus `Corrected_inputs_v1.ipynb`, which writes only to `esm_GB_2025/corrected_v1/`. Each item below is tested on synthetic data in this container; none has been run on your Drive data yet.

## PV (`gbtea/pv.py`)
| # | Original | Corrected |
|---|---|---|
| 1 | Clear-sky DNI and DHI fed to the irradiance model | ERA5 direct and diffuse horizontal → DNI = direct / cos(zenith); MIDAS GHI split with Erbs |
| 2 | "Fixed tilt" was horizontal with azimuth following the sun | 35° tilt, 180° azimuth |
| 3 | Dual-axis irradiance used the leftover fixed mount | A dual-axis mount for both irradiance and angle of incidence |
| 4 | One 2.5 MWp block divided by 5 MW (CF about halved) | Both blocks modelled; CF per kWp DC (5.01 MWp) |
| 5 | Pressure carried over from the previous station | Pressure per site inside the loop |
| 7 | GCR from the last station's latitude | GCR = 1.2 m / 3.0 m = 0.40 |
| 9 | 100 m ERA5 wind vs 10 m MIDAS wind in cell temperature; 0.25 vs ERA5 albedo | 10 m wind for both (ERA5 via log law); ERA5 albedo for both |
| new | Sun position at the hour stamp | Sun position at mid-hour (stamp − 30 min), as atlite does for ERA5 |
| new | `infinite_sheds` called with `model='king'`, which it does not support | Hay–Davies for all three mounts |
| new | Prilliman smoothing | Removed: pvlib skips it for hourly data, so it did nothing |
| new | `.clip(lower=0)` not assigned | Clip assigned |

## Wind (`gbtea/wind.py`)
- Roughness from one CORINE pixel (0.5–1.2 m in towns) → the site's ERA5 roughness series, clipped to 0.0002–0.5 m, used for both datasets.
- Added a modern turbine (V126/3450, 100 m hub, so no height extrapolation from ERA5 100 m). E-53 cluster kept for continuity.
- Hub temperature from a −6.5 K/km lapse rate; pressure per site at hub height. ERA5 surface pressure was never extracted, so pressure is still altitude-based (no weather variation).
- Output named `cf` per kW nameplate; power in kW.

## MIDAS (`gbtea/weather.py`)
- Unit check with printed decisions: GHI kJ/m²/h → W/m² (÷3.6) if the 99.9th percentile is above 1,300; wind knots → m/s if the mean is above 7; pressure hPa → Pa.
- Northern Ireland and Isle of Man stations dropped (Aldergrove, Ballypatrick, Magilligan, Thomastown, Ronaldsway, plus an NI bounding box).
- Station-years kept only with ≥ 80 % valid hours, which handles stations that closed.
- Validation now covers all GB stations, all three mounts, GHI, 10 m wind and wind power.

## Prices (`gbtea/prices.py`)
- Settlement periods placed from local midnight in elapsed time and converted to UTC, so 46- and 50-period days line up (tested on both 2024 clock changes).
- IQR cap removed; negatives and spikes kept and counted.
- One unit (£/MWh) and an honest name: Market Index Price, not System Price.
- MIP = 0 treated as no-trade gaps; gaps of up to 3 hours interpolated, longer gaps left missing.

## Costs (`gbtea/costs.py`)
- Each row inflated from its own currency year (2015 or 2020 euros) to 2024 euros, then × 0.8466 £/€.
- Battery storage (£/kWh) and battery inverter (£/kW, with FOM) kept separate; VOM kept.
- Gas carbon cost: 0.1829 t/MWh fuel ÷ efficiency once (was 488 kg/MWh electricity ÷ efficiency again). At 2025 prices: £25.3/MWh instead of £78.8/MWh.
- CCGT efficiency taken from the same cost file (0.57) rather than mixing in 0.489.
- Fuel and carbon prices after 2025 are no longer silently flat. A projection source is still needed (open item).

## Land (`gbtea/land.py`)
- 1 km buffer applied around settlements (CORINE 1–2) as its own step, not around every eligible patch.
- Class lists as GLAES strings (sets, not ranges); heterogeneous agriculture is 19–22.
- Roads: motorways and A roads, 200 m.
- Placements distributed on the solar and wind calculators.
- New: eligible km² and MW cap within 25 km of each GSP (50 MW/km² solar, 5 MW/km² wind).

- Memory (local run, 23 Oct): the land step reached 8.7 GB of 16 GB RAM while the flagship ran, leaving 0.3 GB free. That is a likely cause of the unclean reboot, so it was stopped (`logs/land_stopped_mem_2.log`) and will rerun alone after the main flagship run. Changes, with the exclusion rules unchanged:
  - `step_land` runs each technology in its own Python process (`land.run_tech`), so the solar calculator is freed before wind starts (before, both were held at once). A technology whose tif and placements already exist is skipped.
  - `land.major_roads` pre-filters `GB_RoadLink.shp` (782 MB geometry + 5.5 GB dbf) to motorways and A roads once, giving `land/GB_RoadLink_major.gpkg` (299,332 links: 7,278 motorway, 292,054 A road; 86 MB). GLAES then reads that file with no `where`. The features are the same as `ROAD_WHERE` on the full file.

  - The flagship main run has priority. Land was stopped again (`logs/land_stopped_priority_3.log`) and now runs at **250 m** (`land.PIXEL_RES_M`, was 100 m): about 6x fewer pixels, which is ample for 25 km caps that are only a check at 5 MW. `logs/land_after_main.ps1` starts it automatically once the main run exits, one technology per subprocess.

## Load (`gbtea/load.py`)
- New for the 26-year runs: IT load × PUE(T), so cooling responds to weather. Calibrate the PUE constants to the Simulink model.

## Open decisions
1. Agriculture rule: include (default) or exclude arable and pasture.
2. Fuel and carbon price projections for 2026–2050.
3. Hourly grid carbon intensity source for the grid-connected case (NESO Carbon Intensity API covers 2018 onwards).
4. Whether sites sharing coordinates (Minley ×3, Dundreggan ×3) should be re-placed with a tighter separation after the corrected land run.

## Local run fixes
- `tests/test_prices_dst.py`, `tests/test_end_to_end_synthetic.py` (first line plus the temp paths): the tests had a hardcoded Colab path (`/mnt/project-files/gb_tea_corrected`) and hardcoded `/tmp` paths, which don't work on Windows. They now add this folder to `sys.path` and write their scratch files to `tempfile.gettempdir()`. The `gbtea` package is unchanged. Both tests pass in the `gbtea` conda env (Python 3.11, pandas 3.1, pvlib 0.16.1, windpowerlib 0.2.2).
- `gbtea/run.py` `_elevation` / `step_sites` (sites step): open-elevation timed out for 30 of 40 sites, which were silently set to 0 m and cached, and co-located sites got different altitudes (Minley 87.6 m vs 0 m). The lookup now retries 3 times and falls back to OpenTopoData (EU-DEM 25 m, then SRTM 90 m). Each unique coordinate is looked up once, with a 1.1 s pause for the public rate limit. The bad cache was kept as `sites_with_altitude_zero_alt_failed.csv.bak` in the output folder. All 40 sites now have altitudes (35–531 m).
- `gbtea/run.py` `step_compare_old` (compare step): 5 sites were skipped (Z13/Z17 Whitbourne Springs, Z15 Bishop's Stortford, Z4/Z5 East Croft). Their `era5_col` has spaces, but the old PV files on Drive use underscores. The step now falls back to the underscored `site` name.
- MIDAS wind units (validation step): the unit check printed "wind mean 4.5: treated as m/s. CHECK the MIDAS metadata." I kept m/s with no code change. `final_wind_speed_2015_2025.csv` is preprocessed, and the 10 m wind MBE of ERA5 against MIDAS is −0.2 m/s at Aberdaron and +0.1 m/s at Altnaharra. If the data were in knots, ERA5 would read about 45% low.
- Wind old-vs-new is not part of `step_compare_old` (PV only). It was computed separately into `logs/cf_old_vs_new_pv_wind.csv`, taking the old E-53 cluster `feedin_power_plant` (kW) ÷ 9,600 kW (2 × 6 × 800 kW) as the old CF.

## Flagship (`gbtea/optimise.py`, `gbtea/flagship.py`, `run_flagship.py`)
- Copied from `gb_tea_corrected` on Drive. MD5 checked on copy (optimise 29dff3f0…, flagship 67a1d97b…, run_flagship a0b0c206…). `optimise.py` was then changed (see below), so its MD5 no longer matches.
- `config.py`: added `GRID_ADDER_GBP_PER_MWH = 50.0` (OPEN DECISION, placeholder) and `GRID_CONNECTION_GBP_PER_KW_YR = 0.0`.
- Cost source: `esm_GB_2025/costs_YYYY.xlsx` only has 9 technologies. It has no single-axis PV, battery inverter, electrolysis, fuel cell or H2 tank, so the first smoke test stopped with KeyError. I downloaded PyPSA technology-data **v0.15.0** `outputs/costs_{2025..2050}.csv` into `esm_GB_2025/technology_data_v0.15.0/` (README there; sizes checked against GitHub). The xlsx files are untouched. All names in `costs.TECHS` exist in v0.15.0, so no name mapping was needed.
- `costs.load_costs` now prefers `costs_YYYY.csv` and falls back to the xlsx. It prints any `TECHS` missing from the file. `costs_gbp2024_2025_2050.csv` was regenerated from v0.15.0; the old one is kept as `.bak`.
- `config.EUR_HICP`: added 2025 = 128.6 (approx. 2024 × 1.021). v0.15.0 investment rows have currency_year 2025, which `_inflator` would otherwise clamp to 2024 and leave un-deflated (about 2% high). VERIFY against Eurostat.
- 2025 costs (GBP2024): onwind 1,194 £/kW; PV fixed 493, single-axis 576 £/kW; battery 207 £/kWh + inverter 238 £/kW (η 0.955 one way); electrolysis 1,877 £/kW_e (η 0.587); fuel cell 1,330 £/kW_e (η 0.50); H2 tank incl. compressor 56.5 £/kWh.
- `optimise.unit_costs`: VOM NaN (no VOM row) gave `float(nan or 0.0) = nan`. linopy's legacy mode silently zeroed these NaN coefficients, so the results were unaffected, but the log was flooded with warnings and linopy v1 semantics would raise. These are now `np.nan_to_num` → 0.
- Smoke test (Z10, years 2010/2015, targets 0.9/1.0, design+stress, HiGHS, gurobipy not installed): 10 LPs in 9.9 min (≈ 60 s per 8,760-h LP). Islanded: £179/MWh (2010), £195/MWh (2015). Grid (2015): £59/MWh at CFE 0.9, £184/MWh at CFE 1.0. Islanded stress: 2010 design run on 2015 leaves 0.29% of load unserved; 2015 design run on 2010 leaves 1.35% unserved.
- Main design run launched with `-W ignore`. It started before the land step finished, so zones solved before `land/land_caps_25km_by_gsp.csv` exists have no land caps (the per-zone log line shows "land caps inf/inf"). Re-run those zones once land is done if caps should apply.
- Resumable at LP level (after the 23 Oct crash, which lost a whole unsaved zone): `flagship.design_years` now appends each solved design to `flagship/design_<tag>.csv` straight away, with the fixed column order `flagship.DESIGN_COLS`. On a rerun it skips any (zone, mode, cfe_target, design_year) already in the file. `run_flagship.py` no longer rewrites the design file at the end of each zone, so rows are not duplicated; stress and robust are still saved per zone. The stress test uses the previously solved rows read back from the file. Tested on Z10 (`--tag resumetest`): killed after the first LP, the rerun skipped 2010, solved only 2011, and wrote no duplicates. Restarted `--tag main` with this version. The 5 Z10 LPs from the old-code run were only in the log (old log: `logs/flagship_main_old_code.log`) and are re-solved. Pre-change copies are in `logs/*.pre_resume`.
- To resume after any interruption, rerun the same command (same `--tag`).
- Gurobi: gurobipy 13.0.3 is installed in gbtea. The licence activated on 23 Oct (ID 2877751) is TYPE=TRIAL, which is size-limited, and the test LP (Z10 2010 islanded, ~100k variables) failed with "Model too large for size-limited license". Runs stay on HiGHS until a Named-User Academic licence is activated.
- 23 Oct 13:23: the main run was stopped by a console Ctrl+C after 22 Z10 islanded rows (2000–2021), probably from a foreground test run. The land step then ran alone (solar subprocess peaked at ~11 GB, so filtering the roads did not remove the main memory load). `logs/main_after_land.ps1` restarts `--tag main` when land exits, and it resumes from the saved rows.
- Wind losses (23 Oct): the gross V126 CFs (0.39–0.43 at lowland sites) had no losses applied. Added `config.WIND_LOSS_FACTOR = 0.86` (wakes, availability, electrical; OPEN: GB calibration as a sensitivity). `flagship.zone_series` multiplies `cf_wind` by it, `run_flagship.py --wind-loss` overrides it, and every design, stress and robust row records `wind_loss`. The resume key includes `wind_loss`, so a different factor is never skipped as done. Effect, Z10 2010 islanded: £179 → £187/MWh (PV 15.9 → 17.4 MW, wind 22.0 → 22.2 MW, H2 store 389 → 462 MWh). The 22 loss-free rows are kept in `flagship/design_main_noloss.csv` (log `logs/flagship_main_noloss.log`).
- Zones with identical weather: zones whose solar AND wind coordinates match (rounded 1e-6) share PV, wind and load series. `flagship.weather_groups` finds them; only the first zone of each group is solved and the others get copied rows (`weather_of` = the zone solved; `label` renamed). That gives 14 distinct of 20 zones: Z13→Z17, Z14→Z16, Z8→Z9, Z1_2→Z1_3, Z1_4, Z1_1→Z2. Land caps are per zone, so if caps ever bind, the copies would need their own solves. At 5 MW they are only a check. Tested on Z8/Z9/Z10 for 2010 (`--tag windlosstest`).
- Main run restarted (`--tag main`, new `design_main.csv`, HiGHS): 14 × 65 = 910 LPs, about 25 h at ~100 s per LP. Land (250 m) is queued after it (`logs/land_after_main.ps1`).
- 23 Oct 15:24: main run stopped by a second console Ctrl+C after 36 rows. The cmd launched via Win32_Process.Create had a visible console window, which could be closed or interrupted. It was relaunched at 22:23 with ShowWindow=0 (hidden) and resumed from the saved rows. The land step (250 m) started at 15:24 by the watcher ran 7 h with only 52 min CPU, peaked at 11.2 GB as at 100 m, and wrote nothing. It was stopped (`logs/land_250m_stalled_4.log`) and NOT re-queued. Resolution is not the memory driver. Suspect the 1 km settlement buffer in `excludeRasterType`, which makes GLAES vectorise every matching CORINE pixel across GB. Needs a raster-distance buffer instead before land is rerun.
- 24 Oct 09:56: main run crashed with PermissionError because `design_main.csv` was open in Excel, which locks it. About 6.7 h lost (log `logs/flagship_main_locked_5.log`). `flagship._append_csv` now retries every 30 s for up to 2 h while the file is locked. After each write it refreshes `design_main_view.csv`, a copy that is safe to open. Restarted 24 Oct 16:4x (windowless, resumes).
- 24 Oct 16:4x-18:4x: design_main.csv stayed open in Excel, so the 2 h retry ran out and the run stopped again (log `logs/flagship_main_locked_6.log`). `_append_csv` no longer waits: while the file is locked, rows go to `design_main.pending.csv`. `read_designs` (the resume check) reads both files, and the parked rows are merged into the main file on the next write that succeeds. Tested with a simulated exclusive lock. Restarted 24 Oct ~19:15.
- 24 Oct 22:08: second unclean shutdown (Kernel-Power 41; no land step running, so not memory). Run restarted 25 Oct ~01:05 from 419 solved LPs (log `logs/flagship_main_reboot_7.log`).
- Main design run COMPLETE, 25 Oct 21:59 GMT. `design_main.csv`: 1,300 rows = 910 solved + 390 copied (20 zones × 65), no duplicates, no parked rows, wind_loss 0.86 throughout. All islanded rows have CFE = 1 and no grid row falls short of its target. The per-zone summary is in `flagship/summary_main.csv` (islanded median/min/max, worst/best year, median PV/wind/battery/H2, H2-year count, curtailment, grid medians per CFE target). The land step is parked (not run).
- Cross-year stress test (`run_stress.py`, 25 Oct): operates the saved islanded designs from `design_main.csv` on every test year 2000-2024 (no design re-solve) for Z10, Z14, Z5 and Z1_2. Rows go to `flagship/stress_main.csv` (lock-safe, resumable, with a view copy) and record unserved MWh/fraction, shortfall hours and peak shortfall MW (new `unserved_hours`/`unserved_max_mw` in `optimise._results`). `flagship._append_csv` parked-row merge now uses the frame's own columns.
- `run_stress.py` generalised: `--mode islanded|grid`; zones default to every distinct zone (duplicates copied with `weather_of`). Grid mode operates each grid design (per CFE target, 2015–24) on every price year and records achieved CFE, the shortfall vs target, imports/exports and £/MWh in `flagship/stress_grid_<tag>.csv`. Tested on Z10 at 0.9 (design 2015 run on 2015 gives CFE 0.899).
- `run_flagship.py --grid-adder` (default config £50/MWh) is recorded per row (`grid_adder`, new last column of `DESIGN_COLS`) and is part of the skip key. Rows without the column count as the config default. Use the new column layout only with new tags; don't append to `design_main.csv`. Tested: Z10 2015 at CFE 0.9 with adder £30 gives £62/MWh.
- Detached chain (`logs/chain.cmd`, started once the 4-zone stress run exits; progress in `logs/chain.log`): [1] islanded stress for all 14 distinct zones (resumes) → [2] grid stress for all zones → [3] grid design run, adder £30 (`--tag adder30`) → [4] adder £70 (`--tag adder70`).
- Robust step result (27 Oct): the 3 h-step multi-year designs (`robust_main.csv`) show 2–10 years with hourly shortfalls when re-run hour by hour (worst 0.006–1.9%), so 3 h averaging under-sizes them slightly. PROVISIONAL step 7 (`logs/step7_robust1h.ps1`, started by the watcher `logs/step7_after_chain2.ps1` after chain2 exits; cancel by stopping that watcher): 1 h robust designs (`--agg-hours 1 --tag 1h` → `robust_1h.csv`), worst-shortfall zones first, killed if RAM > 12 GB; then the hourly check → `stress_robust1h.csv`. `run_flagship.py` now keeps the `--zones` order as given.
- 29 Oct 05:24: third unclean shutdown (Kernel-Power 41), during the �70 run (529 rows saved). Google Drive restarted. `logs/chain3.ps1` resumes the �70 run, then runs step 7 (1 h robust). To cancel step 7 only, stop it after `[step6_adder70] exit` appears in `logs/chain.log`, or stop chain3 and rerun step6 by hand.
- 29 Oct 07:3x: solver threads 4 ? 2 (`config.SOLVER_THREADS`, used for HiGHS and Gurobi) to cut heat and power draw after the repeated power-cut shutdowns. The �70 run was stopped at an LP boundary and resumed via `logs/chain3.ps1` (then step 7). Expect about 1.5x longer LPs.
- 29 Oct: at Dr Edgar's request, added the scheduled task **GBTEA auto-resume** (current user only, at logon + 2 min, not elevated). It runs `logs/autoresume.ps1`, which does nothing if the chain is finished or already running. Otherwise it starts Google Drive, waits up to 15 min for G:, then resumes `logs/chain3.ps1`. Log: `logs/autoresume.log`. Tested by running it by hand while the chain was running; it correctly did nothing. **Remove with:** `schtasks /Delete /TN "GBTEA auto-resume" /F`. It runs only after someone logs in to Windows; it does not log in automatically.
- 30 Oct 10:34: fifth unclean shutdown. Auto-resume fired correctly at logon (12:12). Step 7 (1 h robust over 25 years) is PAUSED: the Z10 LP ran 16+ h on HiGHS (2 threads) without finishing, so it is not practical as specified. `logs/PAUSE` stops auto-resume from relaunching it; delete the file to allow it.
- 30 Oct: step 8 (provisional, replaces paused step 7): critical-years robust design. `pick_critical_years.py` ranks each zone's years by (own single-year design cost) + (mean unserved when used as a test year) and writes `flagship/crit_years_5.csv` and `crit_years_4.csv`. `run_flagship.py --years-file` gives per-zone design years; non-contiguous years are labelled '2002,2006,...' (`flagship.years_label`). Each zone's 5 years are stacked at 1 h steps (`--tag crit5` ? `robust_crit5.csv`), then checked hourly on all 25 years (`stress_crit5.csv`). It drops to 4 years if Z10 takes > 4 h, and has a 12 GB RAM guard. Auto-resume now runs `logs/current_chain.ps1` and stops when `logs/CHAIN_DONE` or `logs/PAUSE` exists.
- 30 Oct: the Z10 input-sensitivity queue (`sens/sens_queue.ps1`, set up 28 Oct) had been waiting for step 7. Its watcher died in the crashes. It no longer waits on step 7; `logs/current_chain.ps1` runs it after step 8 (live hand-off: `logs/sens_after_step8.ps1`), then writes `logs/CHAIN_DONE`. Auto-resume treats it as part of the chain. Fix: `optimise.operate` drops NaN capacities, and `run_stress.py` sets `allow_h2` from the design, so the `--no-h2` case's stress test works (checked on one LP).
