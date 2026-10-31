"""Weather-driven data-centre load for multi-year runs.

The original notebook tiles one simulated Simulink week to a year, so cooling does not respond
to weather and every year is identical. For the 26-year analysis the facility load is
IT load x PUE(T_air), with PUE rising above a free-cooling threshold. The IT profile can be
the normalised weekly shape from the Simulink run (optional), so the original work is reused.
Calibrate PUE_* in config so the mean PUE matches the Simulink cooling model.
"""
import numpy as np
import pandas as pd

from . import config as C


def pue(temp_c):
    return np.clip(C.PUE_BASE + C.PUE_SLOPE_PER_K * np.maximum(temp_c - C.PUE_T_THRESHOLD_C, 0),
                   C.PUE_BASE, C.PUE_MAX)


def it_profile(index, weekly_shape=None):
    """IT load in kW. weekly_shape: optional Series of 168 hourly values (any scale), Monday 00 UTC first."""
    if weekly_shape is None:
        return pd.Series(C.IT_LOAD_KW, index=index)
    shape = np.asarray(weekly_shape, dtype=float)
    shape = shape / shape.mean()
    how = index.dayofweek * 24 + index.hour
    return pd.Series(C.IT_LOAD_KW * shape[how], index=index)


def facility_load(temp_c, weekly_shape=None):
    """Hourly facility load in kW on the same UTC index as temp_c (deg C at 2 m)."""
    it = it_profile(temp_c.index, weekly_shape)
    return (it * pue(temp_c)).rename("load_kw")
