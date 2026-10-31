"""Readers for the extracted ERA5 and MIDAS tables, with explicit time zones and unit checks."""
import numpy as np
import pandas as pd

from . import config as C

ERA5_FILES = {
    "direct": "ERA5_InfluxDirect",      # direct radiation on a HORIZONTAL surface (atlite 'fdir'), W/m2
    "diffuse": "ERA5_InfluxDiffuse",    # diffuse horizontal, W/m2
    "ghi": "ERA5_GHI",
    "toa": "ERA5_InfluxTOA",
    "wind100": "ERA5_WindSpeed100m",
    "roughness": "ERA5_WindRoughness",
    "albedo": "ERA5_Albedo",
    "temp": "ERA5_Temperature",          # K
    "dewpoint": "ERA5_Dew_Temperature",  # K
}


def _to_utc_index(df):
    """Find the time column, drop helper columns, return a UTC-indexed frame."""
    df = df.copy()
    for col in ("Datetime", "time", "DateTime"):
        if col in df.columns:
            df = df.set_index(col)
            break
    df = df.drop(columns=[c for c in df.columns if c == "Year" or str(c).startswith("Unnamed")],
                 errors="ignore")
    idx = pd.to_datetime(df.index)
    # FIX (DST alignment): ERA5 is UTC. Naive stamps are declared UTC, never local time.
    df.index = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df.index.name = "time_utc"
    df = df[~df.index.duplicated(keep="first")].sort_index()
    return df.apply(pd.to_numeric, errors="coerce")


def read_era5(var, folder=C.ERA5_2000_2025, span="2000_2025"):
    path = folder / f"{ERA5_FILES[var]}_{span}.csv"
    df = pd.read_csv(path)
    # The original extraction saved a 0..N integer index as the first column.
    if df.columns[0].startswith("Unnamed") and "Datetime" in df.columns:
        df = df.drop(columns=df.columns[0])
    df.columns = [str(c).strip() for c in df.columns]
    return _to_utc_index(df)


def _norm(name):
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def resolve_column(df, site):
    """Match a site name to a column even if spaces became underscores along the way."""
    if site in df.columns:
        return site
    lookup = {_norm(c): c for c in df.columns}
    if _norm(site) in lookup:
        return lookup[_norm(site)]
    raise KeyError(f"{site!r} not found; first columns: {list(df.columns[:5])}")


def era5_site_frame(site, folder=C.ERA5_2000_2025, span="2000_2025", cache=None):
    """One site's ERA5 variables in SI units (temperatures in deg C) on a UTC index."""
    cache = {} if cache is None else cache
    cols = {}
    for var in ("direct", "diffuse", "wind100", "roughness", "albedo", "temp", "dewpoint"):
        if var not in cache:
            cache[var] = read_era5(var, folder, span)
        cols[var] = cache[var][resolve_column(cache[var], site)]
    df = pd.DataFrame(cols)
    df["ghi"] = df["direct"] + df["diffuse"]
    for k in ("temp", "dewpoint"):
        if df[k].median() > 200:  # Kelvin
            df[k] = df[k] - 273.15
    return df.loc[:pd.Timestamp(C.ERA5_END, tz="UTC")]


# --- MIDAS ---------------------------------------------------------------------------------
MIDAS_FILES = {
    "ghi": "final_ghi_2015_2025.csv",
    "wind10": "final_wind_speed_2015_2025.csv",
    "temp": "final_air_temperature_2015_2025.csv",
    "rh": "final_relative_humidity_2015_2025.csv",
    "pressure": "final_station_pressure_2015_2025.csv",
}


def read_midas(var):
    df = pd.read_csv(C.MIDAS_DIR / MIDAS_FILES[var])
    df = df.rename(columns={df.columns[0]: "Datetime"})
    df.columns = [c.strip() for c in df.columns]  # station names carried leading/trailing spaces
    # MIDAS observation times are UTC (GMT), so the same UTC handling applies.
    return _to_utc_index(df)


def check_midas_units(ghi, wind, pressure, report=print):
    """FIX (MIDAS units): detect raw MIDAS units and convert. Returns converted frames and notes.

    Raw MIDAS hourly radiation is kJ/m2 per hour (W/m2 = kJ/m2 / 3.6); wind is knots;
    station pressure is hPa. The checks use physical ranges, and every decision is reported.
    """
    notes = []
    g99 = np.nanpercentile(ghi.values, 99.9)
    if g99 > 1300:
        ghi = ghi / 3.6
        notes.append(f"GHI 99.9th pct {g99:.0f} > 1300: treated as kJ/m2/h, divided by 3.6")
    else:
        notes.append(f"GHI 99.9th pct {g99:.0f} W/m2: already W/m2")
    w_mean = np.nanmean(wind.values)
    # GB 10 m mean wind is ~4-6 m/s (~8-12 kn). Above 7 the data are almost certainly knots.
    if w_mean > 7.0:
        wind = wind * 0.514444
        notes.append(f"wind mean {w_mean:.1f} > 7: treated as knots, converted to m/s")
    else:
        notes.append(f"wind mean {w_mean:.1f}: treated as m/s. CHECK the MIDAS metadata.")
    p_med = np.nanmedian(pressure.values)
    if p_med < 2000:
        pressure = pressure * 100.0
        notes.append(f"pressure median {p_med:.0f}: hPa, converted to Pa")
    for n in notes:
        report("MIDAS units: " + n)
    return ghi, wind, pressure, notes


def gb_midas_stations(stations_df):
    """FIX (non-GB stations): drop Northern Ireland and Isle of Man stations."""
    s = stations_df.copy()
    s["Name"] = s["Name"].str.strip()
    upper = s["Name"].str.upper()
    in_ni_box = s["Longitude"].between(-8.3, -5.3) & s["Latitude"].between(54.0, 55.4)
    keep = ~upper.apply(lambda n: any(x in n for x in C.NON_GB_STATIONS)) & ~in_ni_box
    return s[keep].reset_index(drop=True)


def complete_years(series, min_frac=C.MIN_COMPLETENESS):
    """FIX (closed stations): years with at least min_frac valid hours."""
    counts = series.notna().groupby(series.index.year).sum()
    hours = series.groupby(series.index.year).size()
    return list(counts.index[(counts / hours) >= min_frac])
