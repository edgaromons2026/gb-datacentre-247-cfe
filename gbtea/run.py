"""Step functions that regenerate every corrected input. Each writes to config.OUT only."""
import json
import time

import numpy as np
import pandas as pd
import requests

from . import config as C
from . import costs, load, prices, pv, weather, wind

MOUNTS = ("fixed", "single_axis", "dual_axis")


def _out(sub=""):
    d = C.OUT / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


# 1. Prices ---------------------------------------------------------------------------------
def step_prices():
    h, rep = prices.load_mip()
    h.to_frame().to_csv(_out() / "mip_hourly_utc_gbp_per_mwh_2015_2025.csv")
    (_out() / "mip_report.json").write_text(json.dumps(rep, indent=2))
    print(rep)
    return h


# 2. Costs ----------------------------------------------------------------------------------
def step_costs():
    df = pd.concat([costs.load_costs(y) for y in C.COST_YEARS], ignore_index=True)
    df.to_csv(_out() / "costs_gbp2024_2025_2050.csv", index=False)
    return df


# 3. Sites with altitude --------------------------------------------------------------------
def _elevation(lat, lon):
    # LOCAL FIX: open-elevation times out intermittently; retry, then fall back to OpenTopoData
    for url, params in (("https://api.open-elevation.com/api/v1/lookup", {"locations": f"{lat},{lon}"}),
                        ("https://api.opentopodata.org/v1/eudem25m", {"locations": f"{lat},{lon}"}),
                        ("https://api.opentopodata.org/v1/srtm90m", {"locations": f"{lat},{lon}"})):
        for attempt in range(3):
            try:
                r = requests.get(url, params=params, timeout=30)
                r.raise_for_status()
                elev = r.json()["results"][0]["elevation"]
                if elev is not None:
                    return float(elev)
                break
            except Exception:
                time.sleep(2 * (attempt + 1))
    return np.nan


def step_sites():
    path = _out() / "sites_with_altitude.csv"
    if path.exists():  # FIX: altitudes are cached instead of lost after each session
        return pd.read_csv(path)
    s = pd.read_csv(C.OPTIMAL_SITES)
    rows = []
    for _, r in s.iterrows():
        for tech, pre in (("solar", "Solar"), ("wind", "Wind")):
            rows.append({"zone": r["Zone_ID"], "gsp": r["GSP_Name"], "tech": tech,
                         "site": f"{r['Zone_ID']}_{r[pre + '_Site_Name']}_{tech}".replace(" ", "_"),
                         "era5_col": f"{r['Zone_ID']}_{r[pre + '_Site_Name']}_{tech}",
                         "lat": r[f"{pre}_Latitude"], "lon": r[f"{pre}_Longitude"],
                         "dist_gsp_km": r[f"Distance_GSP_{pre}_km"]})
    df = pd.DataFrame(rows)
    elev = {}  # LOCAL FIX: one lookup per coordinate, so co-located sites share one altitude
    for a, b in zip(df.lat, df.lon):
        if (round(a, 4), round(b, 4)) not in elev:
            elev[(round(a, 4), round(b, 4))] = _elevation(a, b)
            time.sleep(1.1)  # OpenTopoData public limit: 1 request/s
    df["alt"] = [elev[(round(a, 4), round(b, 4))] for a, b in zip(df.lat, df.lon)]
    if df.alt.isna().any():
        print("WARNING: altitude lookup failed for", df.loc[df.alt.isna(), "site"].tolist(),
              "- set to 0 m; fill in from a DEM before publication")
        df["alt"] = df["alt"].fillna(0.0)
    # Sites sharing coordinates get identical weather; flag them so they are run once.
    df["coord_key"] = df.lat.round(4).astype(str) + "," + df.lon.round(4).astype(str)
    df["duplicate_of"] = df.groupby("coord_key")["site"].transform("first")
    df.to_csv(path, index=False)
    return df


# 4-6. ERA5 2000-2025: PV, wind, load -------------------------------------------------------
def step_era5_profiles(sites=None, mounts=MOUNTS):
    sites = step_sites() if sites is None else sites
    cache = {}
    done = {}
    for _, s in sites.iterrows():
        key = s["coord_key"]
        if key in done:  # same coordinates as an earlier site: copy, do not recompute
            pv_df, wd_df, ld = done[key]
        else:
            w = weather.era5_site_frame(s["era5_col"], cache=cache)
            w["wind10"] = pv.wind_at_10m(w["wind100"], w["roughness"])
            pv_df = pd.DataFrame({m: pv.simulate(w, s.lat, s.lon, s.alt, m)["cf"] for m in mounts})
            wd_df = pd.DataFrame({
                "e53_cluster": wind.simulate_e53_cluster(w, s.alt)["cf"],
                "v126_100m": wind.simulate_modern(w, s.alt)["cf"]})
            ld = load.facility_load(w["temp"])
            done[key] = (pv_df, wd_df, ld)
        pv_df.add_prefix("pv_cf_").to_csv(_out("pv") / f"{s.site}_pv_cf_2000_2025.csv")
        wd_df.add_prefix("wind_cf_").to_csv(_out("wind") / f"{s.site}_wind_cf_2000_2025.csv")
        ld.to_frame().to_csv(_out("load") / f"{s.site}_load_kw_2000_2025.csv")
        print(s.site, "PV CF", pv_df.mean().round(3).to_dict(),
              "wind CF", wd_df.mean().round(3).to_dict())


# 7. MIDAS vs ERA5 validation 2015-2025 -----------------------------------------------------
def _metrics(a, b):
    m = pd.concat([a, b], axis=1).dropna()
    if len(m) < 100:
        return {}
    x, y = m.iloc[:, 0], m.iloc[:, 1]
    return {"n": len(m), "r": x.corr(y), "rmse": float(np.sqrt(((y - x) ** 2).mean())),
            "mbe": float((y - x).mean()), "mean_midas": float(x.mean()), "mean_era5": float(y.mean())}


def step_validation(max_stations=None):
    st = weather.gb_midas_stations(pd.read_csv(C.MIDAS_STATIONS))
    ghi_m = weather.read_midas("ghi")
    wind_m = weather.read_midas("wind10")
    p_m = weather.read_midas("pressure")
    ghi_m, wind_m, p_m, notes = weather.check_midas_units(ghi_m, wind_m, p_m)
    t_m, rh_m = weather.read_midas("temp"), weather.read_midas("rh")
    cache = {}
    rows = []
    for _, s in st.head(max_stations).iterrows() if max_stations else st.iterrows():
        name = s["Name"]
        if name not in ghi_m.columns:
            continue
        years = weather.complete_years(ghi_m[name])
        if not years:
            continue
        e = weather.era5_site_frame(name, folder=C.ERA5_2015_2025, span="2015_2025", cache=cache)
        e["wind10"] = pv.wind_at_10m(e["wind100"], e["roughness"])
        m = pd.DataFrame({"ghi": ghi_m[name], "temp": t_m[name], "rh": rh_m[name],
                          "wind10": wind_m[name], "pressure": p_m[name]}).reindex(e.index)
        m["albedo"] = e["albedo"]  # same albedo for both datasets
        m = m[m.index.year.isin(years)].dropna()
        e = e.loc[m.index]
        row = {"station": name, "years": f"{min(years)}-{max(years)}"}
        row.update({f"ghi_{k}": v for k, v in _metrics(m["ghi"], e["ghi"]).items()})
        row.update({f"wind10_{k}": v for k, v in _metrics(m["wind10"], e["wind10"]).items()})
        alt = s.get("Altitude", 0.0) if pd.notna(s.get("Altitude", np.nan)) else 0.0
        for mount in MOUNTS:
            a = pv.simulate(m, s.Latitude, s.Longitude, alt, mount)["cf"]
            b = pv.simulate(e, s.Latitude, s.Longitude, alt, mount)["cf"]
            row.update({f"pv_{mount}_{k}": v for k, v in _metrics(a, b).items()})
        ww = e[["roughness", "temp"]].assign(wind10=m["wind10"])
        a = wind.simulate_modern(ww, alt, z_meas=10, wind_col="wind10")["cf"]
        b = wind.simulate_modern(e, alt)["cf"]
        row.update({f"wind_v126_{k}": v for k, v in _metrics(a, b).items()})
        rows.append(row)
        print(name, {k: round(v, 3) for k, v in row.items() if k.endswith("_r")})
    out = pd.DataFrame(rows)
    out.to_csv(_out("validation") / "midas_vs_era5_metrics_2015_2025.csv", index=False)
    (_out("validation") / "midas_unit_checks.txt").write_text("\n".join(notes))
    return out


# 8. Old vs corrected comparison ------------------------------------------------------------
def step_compare_old(sites=None):
    sites = step_sites() if sites is None else sites
    rows = []
    for _, s in sites.iterrows():
        old_pv = C.ERA5_2000_2025 / f"{s.era5_col}_ERA5_PV_Energy_2000_2025.csv"
        if not old_pv.exists():  # LOCAL FIX: old files use underscores where site names have spaces
            old_pv = C.ERA5_2000_2025 / f"{s.site}_ERA5_PV_Energy_2000_2025.csv"
        new_pv = C.OUT / "pv" / f"{s.site}_pv_cf_2000_2025.csv"
        if not (old_pv.exists() and new_pv.exists()):
            continue
        o = pd.read_csv(old_pv, index_col=0).clip(lower=0) / 5000.0  # old: one block / 5 MW
        n = pd.read_csv(new_pv, index_col=0)
        rows.append({"site": s.site,
                     "old_single_axis": o["ERA5_single_axis_kW"].mean(),
                     "new_single_axis": n["pv_cf_single_axis"].mean(),
                     "old_fixed": o["ERA5_fixed_tilt_kW"].mean(), "new_fixed": n["pv_cf_fixed"].mean(),
                     "old_dual": o["ERA5_dual_axis_kW"].mean(), "new_dual": n["pv_cf_dual_axis"].mean()})
    df = pd.DataFrame(rows)
    df.to_csv(_out("validation") / "pv_cf_old_vs_corrected.csv", index=False)
    return df


# 9. Corrected land eligibility and land caps per GSP zone ----------------------------------
def step_land(clc_tif, gb_boundary=C.ESM / "GB_boundary.shp", roads_shp=C.ESM / "GB_RoadLink.shp",
              radius_km=25.0):
    from . import land

    import subprocess
    import sys
    from pathlib import Path

    caps = []
    tifs = {}
    roads = land.major_roads(roads_shp, _out("land"))
    pkg = str(Path(__file__).resolve().parents[1])
    for tech in ("solar", "wind"):
        tif = _out("land") / f"GB_{tech}_eligible_corrected.tif"
        tifs[tech] = tif
        if tif.exists() and (_out("land") / f"{tech}_placements_corrected.csv").exists():
            print(f"{tech}: already done, skipped ({tif})")
            continue
        # Each technology in its own process: the full-GB calculator took ~9 GB and both were held at once.
        code = (f"import sys; sys.path.insert(0, {pkg!r}); from gbtea import land; "
                f"land.run_tech({tech!r}, {str(gb_boundary)!r}, {str(clc_tif)!r}, {str(roads)!r}, "
                f"include_agriculture={land.INCLUDE_AGRICULTURE})")
        subprocess.run([sys.executable, "-u", "-c", code], check=True)
    s = pd.read_csv(C.OPTIMAL_SITES)
    for _, r in s.iterrows():
        row = {"zone": r["Zone_ID"], "gsp": r["GSP_Name"], "lat": r["Latitude"], "lon": r["Longitude"]}
        for tech in ("solar", "wind"):
            km2, mw = land.land_cap_mw(tifs[tech], r["Latitude"], r["Longitude"], tech, radius_km)
            row[f"{tech}_eligible_km2"], row[f"{tech}_cap_mw"] = km2, mw
        caps.append(row)
    caps = pd.DataFrame(caps)
    caps.to_csv(_out("land") / f"land_caps_{int(radius_km)}km_by_gsp.csv", index=False)
    return caps
