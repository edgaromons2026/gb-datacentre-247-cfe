"""Corrected windpowerlib model (original E-53 cluster plus a modern utility turbine).

Fixes against the original notebook:
- Hub-height wind uses the site's own ERA5 roughness series (clipped, because ERA5 roughness
  includes orography), not one CORINE pixel that gave towns 0.5-1.2 m and cut hub wind sharply.
  The same roughness is used for MIDAS and ERA5, so the comparison is like-for-like.
- Hub temperature uses a standard lapse rate from 2 m; pressure is per site at hub height.
- MIDAS wind and pressure units are converted in weather.check_midas_units before use.
- Output is labelled in kW, and capacity factor is per kW of nameplate actually modelled.
- A modern turbine (V126/3450 at 100 m) is added, because the 800 kW E-53 is not utility scale.
- Negative or missing values are clipped and the clip is assigned.
"""
import numpy as np
import pandas as pd
import pvlib
from windpowerlib import WindTurbine
from windpowerlib.power_curves import smooth_power_curve
from windpowerlib.power_output import power_curve as pc_output

from . import config as C

R_DRY = 287.058


def hub_wind(wind, z_meas, hub, roughness):
    if abs(hub - z_meas) < 1e-6:
        return wind
    z0 = roughness.clip(*C.ROUGHNESS_CLIP_M) if hasattr(roughness, "clip") else roughness
    return wind * np.log(hub / z0) / np.log(z_meas / z0)


def _turbine(spec):
    return WindTurbine(turbine_type=spec["turbine"], hub_height=spec["hub_height"])


def simulate(w, alt, spec, z_meas=100, wind_col="wind100", n_turbines=1, efficiency=1.0,
             smoothing=True):
    """w: UTC frame with wind_col [m/s at z_meas], roughness [m], temp [C at 2 m].

    Returns frame with power_kw (whole farm) and cf (per kW nameplate).
    """
    t = _turbine(spec)
    hub = spec["hub_height"]
    v = hub_wind(w[wind_col], z_meas, hub, w["roughness"]).clip(lower=0)
    temp_k = w["temp"] + 273.15 + C.LAPSE_RATE_K_PER_M * (hub - 2)
    pressure = pvlib.atmosphere.alt2pres(alt + hub)
    rho = pressure / (R_DRY * temp_k)

    curve = t.power_curve
    if smoothing:  # Staffell-Pfenninger smoothing for spatial spread within a farm
        curve = smooth_power_curve(curve["wind_speed"], curve["value"],
                                   standard_deviation_method="Staffell_Pfenninger",
                                   mean_gauss=0, block_width=0.5)
    p_w = pc_output(v, curve["wind_speed"], curve["value"], density=rho, density_correction=True)
    p_w = pd.Series(np.asarray(p_w, dtype=float), index=w.index).fillna(0).clip(lower=0)
    nameplate_kw = t.nominal_power / 1000.0 * n_turbines
    power_kw = p_w / 1000.0 * n_turbines * efficiency
    return pd.DataFrame({"power_kw": power_kw, "cf": power_kw / nameplate_kw, "hub_wind": v})


def simulate_e53_cluster(w, alt, **kw):
    s = C.E53_CLUSTER
    n = s["n_farms"] * s["n_per_farm"]  # 12 x 800 kW = 9.6 MW
    return simulate(w, alt, s, n_turbines=n, efficiency=s["efficiency"], **kw)


def simulate_modern(w, alt, **kw):
    return simulate(w, alt, C.MODERN_TURBINE, **kw)
