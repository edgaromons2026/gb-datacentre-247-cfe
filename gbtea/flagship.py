"""Experiments for the flagship paper, built on optimise.py and the corrected_v1 inputs.

A. design_years   least-cost design for each weather year, per zone, CFE target and grid mode
B. stress_test    each design re-run (capacities fixed) on every other weather year:
                  how much load goes unserved (islanded) or how far CFE falls (grid)
C. robust_design  one design over all weather years together (optionally time-aggregated),
                  then checked hour by hour on each year
"""
import shutil
import time

import numpy as np
import pandas as pd

from . import config as C
from . import optimise as O

FULL_YEARS = list(range(2000, 2025))    # ERA5 runs to 2025-07-31, so 2025 is partial
PRICE_YEARS = list(range(2015, 2025))   # Market Index Price coverage with full years


def _read(path, col=None):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df if col is None else df[col]


def zone_sites(sites):
    """One row per zone with its solar and wind site names (site files are per technology)."""
    s = sites.pivot_table(index="zone", columns="tech", values="site", aggfunc="first")
    return s.rename(columns={"solar": "solar_site", "wind": "wind_site"}).reset_index()


def zone_series(zone_row, it_mw, out=None, pv_cols=("pv_cf_fixed", "pv_cf_single_axis"),
                wind_col="wind_cf_v126_100m", grid_cfe_path=None, wind_loss=None):
    """Hourly frame for one zone: load (MW), cf_fixed, cf_tracking, cf_wind, price, g.
    cf_wind is the gross V126 profile x wind_loss (default config.WIND_LOSS_FACTOR)."""
    out = C.OUT if out is None else out
    wind_loss = C.WIND_LOSS_FACTOR if wind_loss is None else wind_loss
    pv = _read(out / "pv" / f"{zone_row.solar_site}_pv_cf_2000_2025.csv")
    wd = _read(out / "wind" / f"{zone_row.wind_site}_wind_cf_2000_2025.csv", wind_col)
    ld = _read(out / "load" / f"{zone_row.solar_site}_load_kw_2000_2025.csv", "load_kw")
    ts = pd.DataFrame({"load": ld / C.IT_LOAD_KW * it_mw,  # scale the 5 MW IT profile to it_mw
                       "cf_fixed": pv[pv_cols[0]], "cf_tracking": pv[pv_cols[1]], "cf_wind": wd * wind_loss})
    ts = ts.clip(lower=0).dropna()
    mip_path = out / "mip_hourly_utc_gbp_per_mwh_2015_2025.csv"
    if mip_path.exists():
        mip = _read(mip_path).iloc[:, 0]
        ts["price"] = mip.reindex(ts.index).interpolate(limit=24)
    if grid_cfe_path is not None:
        # OPEN DECISION: hourly carbon-free share of grid supply (0-1), e.g. derived from NESO data.
        ts["g"] = _read(grid_cfe_path).iloc[:, 0].reindex(ts.index).clip(0, 1)
    else:
        ts["g"] = 0.0  # conservative default: grid imports count as fully fossil
    return ts


def land_caps(zone, out=None, radius_km=25):
    out = C.OUT if out is None else out
    f = out / "land" / f"land_caps_{radius_km}km_by_gsp.csv"
    if not f.exists():
        return np.inf, np.inf
    r = pd.read_csv(f).set_index("zone").loc[zone]
    return float(r["solar_cap_mw"]), float(r["wind_cap_mw"])


def years(ts, yrs):
    """Stack the given calendar years (UTC). Each year keeps its own hours; cyclic storage spans the stack."""
    part = ts[ts.index.year.isin(yrs)]
    if part.empty:
        raise ValueError(f"no data for {yrs}")
    return part


def _clean(ts, grid):
    cols = ["load", "cf_fixed", "cf_tracking", "cf_wind"] + (["price", "g"] if grid else [])
    t = ts[cols]
    if t.isna().any().any():
        t = t.dropna()
    return t.reset_index(drop=True)


DESIGN_COLS = ["pv_fixed", "pv_tracking", "wind", "bat_e", "bat_p", "electrolyser", "h2_store", "fuel_cell",
               "grid_conn", "objective_gbp", "load_mwh", "cost_gbp_per_mwh", "cfe", "unserved_mwh", "import_mwh",
               "export_mwh", "pv_mwh", "wind_mwh", "curtailment_frac", "hours", "design_year", "cfe_target", "grid",
               "label", "zone", "mode", "it_mw", "wind_loss", "weather_of", "grid_adder"]


def design_key(zone, mode, cfe_target, design_year, wind_loss, grid_adder=None):
    adder = C.GRID_ADDER_GBP_PER_MWH if grid_adder is None or pd.isna(grid_adder) else grid_adder
    return (str(zone), str(mode), round(float(cfe_target), 6), int(design_year), round(float(wind_loss), 4),
            round(float(adder), 4))


def weather_groups(sites, zones):
    """{first zone: [later zones with the same solar AND wind coordinates]} among `zones`.
    Those zones have identical weather, CF and load series, so only the first is solved."""
    s = sites[sites.zone.isin(zones)]
    k = s.assign(k=list(zip(s.lat.round(6), s.lon.round(6)))).set_index(["zone", "tech"])["k"].unstack()
    groups = {}
    for zone in zones:
        groups.setdefault((k.loc[zone, "solar"], k.loc[zone, "wind"]), []).append(zone)
    return {g[0]: g[1:] for g in groups.values()}


def copy_designs(path, src_zone, dst_zone):
    """Append src_zone's solved rows as dst_zone (weather_of = src_zone), skipping rows already there."""
    d = read_designs(path)
    have = {design_key(o.zone, o["mode"], o.cfe_target, o.design_year, o.wind_loss, o.get("grid_adder")) for _, o in d.iterrows()}
    new = d[d.zone == src_zone].copy()
    new["zone"], new["weather_of"] = dst_zone, src_zone
    new["label"] = new["label"].str.replace(f"{src_zone}|", f"{dst_zone}|", regex=False)
    keep = [design_key(o.zone, o["mode"], o.cfe_target, o.design_year, o.wind_loss, o.get("grid_adder")) not in have
            for _, o in new.iterrows()]
    new = new[keep]
    if len(new):
        _append_csv(path, new.reindex(columns=DESIGN_COLS))
    return len(new)


def _pending(path):
    return path.with_name(f"{path.stem}.pending.csv")


def read_designs(path):
    """Rows already solved, including any parked in <name>.pending.csv (empty frame if none)."""
    if path is None:
        return pd.DataFrame(columns=DESIGN_COLS)
    parts = [pd.read_csv(f) for f in (path, _pending(path)) if f.exists()]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=DESIGN_COLS)


def _append_csv(path, df):
    """Append df to path. If path is locked (e.g. open in Excel), park the rows in <name>.pending.csv
    instead and merge them into path on the next write that succeeds, so the run never stops on a lock.
    After each successful write, refresh <name>_view.csv, a copy that is safe to open."""
    pend = _pending(path)
    try:
        with open(path, "a", newline="", encoding="utf-8") as fh:
            if pend.exists():  # merge parked rows first
                parked = pd.read_csv(pend).reindex(columns=df.columns)
                parked.to_csv(fh, header=fh.tell() == 0, index=False)
                df.to_csv(fh, header=False, index=False)
            else:
                df.to_csv(fh, header=fh.tell() == 0, index=False)
        if pend.exists():
            pend.unlink()
            print(f"  merged parked rows from {pend.name}", flush=True)
    except PermissionError:
        print(f"  {path.name} is locked (open in Excel?); row parked in {pend.name}", flush=True)
        df.to_csv(pend, mode="a", header=not pend.exists(), index=False)
        return
    try:
        shutil.copyfile(path, path.with_name(f"{path.stem}_view.csv"))
    except OSError:
        pass  # the view copy itself is open; refreshed on the next row


def append_design(path, row):
    """Append one solved design to path straight away, so a crash loses at most the LP in progress."""
    _append_csv(path, pd.DataFrame([row]).reindex(columns=DESIGN_COLS))


def design_years(ts, unit, params, yrs, label=None, extra=None, out_csv=None):
    """extra: fields added to every row (zone, mode, it_mw). With out_csv, each row is appended to that
    file as soon as it is solved and years already in the file for this (zone, mode, target) are skipped.
    Returns all rows for this case, previously solved ones included."""
    ann, eff, vom = unit
    extra = extra or {}
    rows = []
    done = {}
    if out_csv is not None and extra:
        old = read_designs(out_csv)
        for _, o in old.iterrows():
            done[design_key(o.zone, o["mode"], o.cfe_target, o.design_year, o.wind_loss, o.get("grid_adder"))] = o.to_dict()
    for y in yrs:
        key = (design_key(extra.get("zone"), extra.get("mode"), params.cfe_target, y, extra.get("wind_loss", 1.0),
                          params.grid_adder_gbp_mwh)
               if extra else None)
        if key in done:
            print(f"  design {label} {y} target={params.cfe_target}: already solved, skipped")
            rows.append(done[key])
            continue
        r = O.design(_clean(years(ts, [y]), params.grid), ann, eff, vom, params)
        r.update(design_year=y, cfe_target=params.cfe_target, grid=params.grid, label=label,
                 grid_adder=params.grid_adder_gbp_mwh, **extra)
        if out_csv is not None:
            append_design(out_csv, r)
        rows.append(r)
        print(f"  design {label} {y} target={params.cfe_target} grid={params.grid}: "
              f"£{r['cost_gbp_per_mwh']:.0f}/MWh, PV {r['pv_fixed'] + r['pv_tracking']:.1f} MW, "
              f"wind {r['wind']:.1f} MW, bat {r['bat_e']:.0f} MWh, H2 store {r.get('h2_store', 0):.0f} MWh")
    return pd.DataFrame(rows).reindex(columns=DESIGN_COLS) if extra else pd.DataFrame(rows)


def stress_test(ts, unit, params, designs, test_years, label=None):
    """designs: rows from design_years or robust_design. Each is operated on every test year."""
    ann, eff, vom = unit
    rows = []
    for _, d in designs.iterrows():
        for y in test_years:
            r = O.operate(_clean(years(ts, [y]), params.grid), ann, eff, vom, params, d.to_dict())
            rows.append(dict(label=label, design_year=d.get("design_year"), test_year=y,
                             cfe_target=d.get("cfe_target"), grid=params.grid, cfe=r["cfe"],
                             unserved_mwh=r["unserved_mwh"], unserved_frac=r["unserved_mwh"] / r["load_mwh"],
                             import_mwh=r["import_mwh"]))
    return pd.DataFrame(rows)


def years_label(yrs):
    """'2000-2024' for a contiguous run of years, else '2001,2006,2021' (non-contiguous critical years)."""
    y = sorted(int(v) for v in yrs)
    return f"{y[0]}-{y[-1]}" if y == list(range(y[0], y[-1] + 1)) else ",".join(map(str, y))


ROBUST_COLS = DESIGN_COLS + ["years", "agg_hours", "unserved_hours", "unserved_max_mw"]


def robust_key(o):
    adder = C.GRID_ADDER_GBP_PER_MWH if pd.isna(o.get("grid_adder", float("nan"))) else o["grid_adder"]
    return (str(o["zone"]), str(o["mode"]), round(float(o["cfe_target"]), 6), round(float(o["wind_loss"]), 4),
            round(float(adder), 4), int(o["agg_hours"]), str(o["years"]))


def robust_saved(ts, unit, params, yrs, agg_hours, label, extra, out_csv):
    """robust_design, appended to out_csv as soon as it is solved; skipped if that case is already there."""
    row = dict(extra, cfe_target=params.cfe_target, grid_adder=params.grid_adder_gbp_mwh, agg_hours=agg_hours,
               years=years_label(yrs))
    old = read_designs(out_csv) if out_csv.exists() or _pending(out_csv).exists() else pd.DataFrame()
    for _, o in old.iterrows():
        if robust_key(o) == robust_key(row):
            print(f"  robust {label} {row['years']} ({agg_hours} h steps): already solved, skipped")
            return pd.DataFrame([o]).reindex(columns=ROBUST_COLS)
    r = robust_design(ts, unit, params, yrs, agg_hours, label).assign(**extra, grid_adder=params.grid_adder_gbp_mwh)
    r = r.reindex(columns=ROBUST_COLS)
    _append_csv(out_csv, r)
    return r


def copy_rows(path, src_zone, dst_zone, keyfn, cols):
    """Append src_zone's rows of path as dst_zone (weather_of = src_zone), skipping keys already present."""
    if not (path.exists() or _pending(path).exists()):
        return 0
    d = read_designs(path)
    have = {keyfn(o) for _, o in d.iterrows()}
    new = d[d.zone == src_zone].copy()
    new["zone"], new["weather_of"] = dst_zone, src_zone
    if "label" in new:
        new["label"] = new["label"].astype(str).str.replace(f"{src_zone}|", f"{dst_zone}|", regex=False)
    new = new[[keyfn(o) not in have for _, o in new.iterrows()]]
    if len(new):
        _append_csv(path, new.reindex(columns=cols))
    return len(new)


def robust_design(ts, unit, params, yrs, agg_hours=3, label=None):
    ann, eff, vom = unit
    t = O.aggregate(_clean(years(ts, yrs), params.grid), agg_hours)
    r = O.design(t, ann, eff, vom, params)
    r.update(design_year="all", years=years_label(yrs), agg_hours=agg_hours,
             cfe_target=params.cfe_target, grid=params.grid, label=label)
    print(f"  robust {label} {years_label(yrs)} ({agg_hours} h steps): £{r['cost_gbp_per_mwh']:.0f}/MWh")
    return pd.DataFrame([r])
