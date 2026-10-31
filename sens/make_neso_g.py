"""Hourly carbon-free share of GB grid supply, g_t, from the NESO historic generation mix (half-hourly).

g = (nuclear + wind + embedded wind + hydro + solar) / total generation including imports and storage.
Biomass, imports and storage count as not carbon-free (conservative). Half-hours are averaged to
UTC hour-ending stamps to match the model series. Writes <OUT>/sens/neso_g_hourly_2009_2025.csv.
    python sens/make_neso_g.py --drive-root "G:/My Drive" [--csv df_fuel_ckan.csv]"""
import argparse
import os
import sys
from pathlib import Path

URL = ("https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/"
       "f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv")
CV1 = Path(__file__).resolve().parent.parent
CLEAN = ["NUCLEAR", "WIND", "WIND_EMB", "HYDRO", "SOLAR"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--csv", default=None, help="local copy of df_fuel_ckan.csv (default: download)")
    args = ap.parse_args()
    os.environ["GBTEA_DRIVE_ROOT"] = str(Path(args.drive_root))
    sys.path.insert(0, str(CV1))
    import pandas as pd
    from gbtea import config as C
    dst = C.OUT / "sens"
    dst.mkdir(parents=True, exist_ok=True)
    raw = Path(args.csv) if args.csv else dst / "neso_df_fuel_ckan.csv"
    if not raw.exists():
        import requests
        r = requests.get(URL, timeout=300)
        r.raise_for_status()
        raw.write_bytes(r.content)
    d = pd.read_csv(raw)
    d.columns = [c.upper() for c in d.columns]
    t = pd.to_datetime(d["DATETIME"], utc=True)
    missing = [c for c in CLEAN + ["GENERATION"] if c not in d]
    if missing:
        sys.exit(f"columns missing from NESO file: {missing}")
    g = (d[CLEAN].sum(axis=1) / d["GENERATION"]).clip(0, 1)
    g.index = t
    hourly = g.groupby(g.index.floor("h") + pd.Timedelta(hours=1)).mean()  # hour-ending
    full = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h")
    gaps = int(hourly.reindex(full).isna().sum())
    hourly = hourly.reindex(full).interpolate(limit=24)  # short gaps filled so the grid LP keeps those hours
    print(f"{gaps} missing hours filled or left empty (gaps > 24 h)", flush=True)
    hourly.index.name = "time"
    hourly.rename("g").to_frame().to_csv(dst / "neso_g_hourly_2009_2025.csv")
    y = hourly.groupby(hourly.index.year).mean().round(3)
    print("mean g by year:", y.loc[2015:2024].to_dict(), flush=True)


if __name__ == "__main__":
    main()
