"""Corrected Elexon Market Index Price (MIP) processing.

Fixes against the original notebook:
- DST: each settlement day has 46, 48 or 50 half-hours. Periods are numbered within the day
  and placed from local (Europe/London) midnight, then converted to UTC, so clock-change days
  line up with the UTC weather data.
- No IQR cap: price spikes and negative prices are kept; they are the hours that drive
  storage and grid-backup value. Outliers are only reported.
- Units: one column, always GBP/MWh, with the name saying so.
- Naming: this is the Market Index Price (a wholesale reference), not the System Price.
"""
import pandas as pd

from . import config as C


def load_mip(path=C.PRICE_RAW, zero_as_missing=True):
    raw = pd.read_csv(path)
    raw["Date"] = pd.to_datetime(raw["Date"], format="%d-%b-%y", errors="coerce")
    raw = raw.dropna(subset=["Date"])
    # Settlement period within each day, in file order (the file is in period order).
    raw["sp"] = raw.groupby("Date").cumcount() + 1
    n_per_day = raw.groupby("Date")["sp"].transform("max")
    odd = raw.loc[~n_per_day.isin([46, 48, 50]), "Date"].dt.date.unique()
    local_midnight = raw["Date"].dt.tz_localize("Europe/London", ambiguous=False,
                                                nonexistent="shift_forward")
    # Period k starts (k-1) half-hours after local midnight in ELAPSED time, so DST days work.
    start_utc = local_midnight.dt.tz_convert("UTC") + pd.to_timedelta((raw["sp"] - 1) * 30, "min")
    price = pd.Series(raw["Market_Index_Price_GBP_MWh"].astype(float).values,
                      index=pd.DatetimeIndex(start_utc), name="mip_gbp_per_mwh").sort_index()
    if zero_as_missing:
        # Elexon publishes MIP = 0 for periods with no traded volume; these are gaps, not prices.
        price = price.mask(price == 0.0)
    price = price[~price.index.duplicated(keep="first")]
    # Hour-ending UTC stamps to match ERA5: mean of the two half-hours in (t-1h, t].
    hourly = price.resample("1h", label="right", closed="left").mean()
    # Bridge gaps of up to 3 hours only; longer gaps stay missing.
    gap_id = hourly.notna().cumsum()
    gap_len = hourly.isna().groupby(gap_id).transform("sum")
    hourly = hourly.where(hourly.notna() | (gap_len > 3), hourly.interpolate(limit_area="inside"))
    report = {
        "days_with_unusual_period_count": len(odd),
        "negative_hours": int((hourly < 0).sum()),
        "hours_above_300": int((hourly > 300).sum()),
        "missing_hours_after_fill": int(hourly.isna().sum()),
    }
    return hourly.rename("mip_gbp_per_mwh"), report
