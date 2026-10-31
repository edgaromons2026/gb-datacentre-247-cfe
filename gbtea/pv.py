"""Corrected pvlib model of the 5 MWp CdTe plant (fixed tilt, single-axis, dual-axis).

Fixes against the original notebook (review items in brackets):
- [1] Beam and diffuse come from the weather data, never from clear-sky values. ERA5 supplies
  direct and diffuse horizontal; MIDAS GHI is split with the Erbs model.
- [2] Fixed tilt is a real 35 deg south-facing plane, not a horizontal plane following the sun.
- [3] The dual-axis run uses a dual-axis mount for BOTH irradiance and angle of incidence.
- [4] Output covers both inverter blocks and capacity factor uses the DC capacity modelled.
- [5] Site pressure is computed per site inside the loop.
- [7] GCR comes from geometry (1.2 m / 3.0 m = 0.40), not from a station latitude.
- [9] Cell temperature uses 10 m wind for both datasets, and both use the ERA5 albedo series.
- ERA5 and MIDAS hourly values are means over the hour ENDING at the stamp, so the sun
  position is taken at the middle of the hour (stamp - 30 min), as atlite does.
- Night-time inverter tare is clipped to zero, and the clip is actually assigned.
"""
import numpy as np
import pandas as pd
import pvlib
from pvlib.pvsystem import AbstractMount

from . import config as C

HALF_HOUR = pd.Timedelta("30min")


class DualAxisTrackerMount(AbstractMount):
    """Ideal two-axis tracker: plane normal points at the sun."""

    def get_orientation(self, solar_zenith, solar_azimuth):
        return {"surface_tilt": np.clip(solar_zenith, 0, 90), "surface_azimuth": solar_azimuth}


def _components():
    mods = pvlib.pvsystem.retrieve_sam("cecmod")
    invs = pvlib.pvsystem.retrieve_sam("cecinverter")
    module = mods[C.MODULE].copy()
    module["Technology"] = "CdTe"
    return module, invs[C.INVERTER]


MODULE, INVERTER = _components()
DC_KW_PER_BLOCK = MODULE["STC"] * C.MODULES_PER_STRING * C.STRINGS_PER_INVERTER / 1000.0
PLANT_DC_KW = DC_KW_PER_BLOCK * C.N_INVERTER_BLOCKS  # ~5,000 kWp


def make_mount(kind):
    if kind == "fixed":
        return pvlib.pvsystem.FixedMount(surface_tilt=C.FIXED_TILT_DEG,
                                         surface_azimuth=C.FIXED_AZIMUTH_DEG,
                                         racking_model="open_rack")
    if kind == "single_axis":
        return pvlib.pvsystem.SingleAxisTrackerMount(
            axis_azimuth=180, max_angle=C.TRACKER_MAX_ANGLE, backtrack=C.TRACKER_BACKTRACK,
            gcr=C.GCR, racking_model="open_rack")
    if kind == "dual_axis":
        return DualAxisTrackerMount()
    raise ValueError(kind)


def wind_at_10m(wind100, roughness):
    """Log-law transfer of ERA5 100 m wind to 10 m for the cell-temperature model."""
    z0 = roughness.clip(*C.ROUGHNESS_CLIP_M)
    return wind100 * np.log(10 / z0) / np.log(100 / z0)


def split_irradiance(w, solpos, dni_extra):
    """Return dni, dhi on the mid-hour index. Uses ERA5 components when present, else Erbs."""
    cosz = np.cos(np.radians(solpos["zenith"]))
    if {"direct", "diffuse"} <= set(w.columns):
        up = solpos["zenith"] < 87
        dni = (w["direct"] / cosz.where(up)).where(up, 0.0).clip(lower=0)
        dni = np.minimum(dni, dni_extra)
        dhi = (w["ghi"] - dni * cosz).clip(lower=0)
        return dni.fillna(0.0), dhi.fillna(0.0)
    out = pvlib.irradiance.erbs(w["ghi"], solpos["zenith"], w.index)
    return out["dni"].fillna(0.0), out["dhi"].fillna(0.0)


def simulate(w, lat, lon, alt, kind):
    """Simulate the plant for one site and one mount.

    w: UTC hour-ending frame with ghi [W/m2], temp [C], wind10 [m/s], albedo [-], and
       either rh [%] or dewpoint [C]; optional direct/diffuse (horizontal), pressure [Pa].
    Returns a hour-ending UTC frame: ac_kw for the whole plant and cf per kWp DC.
    """
    w = w.copy()
    w.index = w.index - HALF_HOUR  # mid-hour timing for every solar-geometry step
    pressure = w["pressure"] if "pressure" in w else pvlib.atmosphere.alt2pres(alt)  # [5]
    solpos = pvlib.solarposition.get_solarposition(w.index, lat, lon, altitude=alt,
                                                   pressure=pressure, temperature=w["temp"])
    dni_extra = pvlib.irradiance.get_extra_radiation(w.index, method="nrel", solar_constant=1361)
    dni, dhi = split_irradiance(w, solpos, dni_extra)  # [1]

    mount = make_mount(kind)
    orient = mount.get_orientation(solpos["apparent_zenith"], solpos["azimuth"])
    tilt = pd.Series(orient["surface_tilt"], index=w.index).fillna(0)
    azim = pd.Series(orient["surface_azimuth"], index=w.index).fillna(180)
    albedo = w["albedo"] if "albedo" in w else C.MIDAS_ALBEDO

    if kind in ("fixed", "single_axis"):
        poa = pvlib.bifacial.infinite_sheds.get_irradiance_poa(
            tilt, azim, solpos["apparent_zenith"], solpos["azimuth"], C.GCR, C.AXIS_HEIGHT_M,
            C.PITCH_M, w["ghi"], dhi, dni, albedo, model="haydavies", dni_extra=dni_extra)
    else:  # dual-axis pedestals are widely spaced, so no row-to-row shading model
        poa = pvlib.irradiance.get_total_irradiance(
            tilt, azim, solpos["apparent_zenith"], solpos["azimuth"], dni, w["ghi"], dhi,
            dni_extra=dni_extra, albedo=albedo, model="haydavies")

    # Prilliman smoothing is dropped: pvlib applies it only below 20-minute data, so at hourly
    # resolution it returned the input unchanged in the original notebook too.
    t_cell = pvlib.temperature.faiman(poa["poa_global"], w["temp"], w["wind10"], **C.FAIMAN)
    if "rh" in w:
        rh = w["rh"]
    else:
        rh = pvlib.atmosphere.rh_from_tdew(w["temp"], w["dewpoint"])
    pw = pvlib.atmosphere.gueymard94_pw(w["temp"], rh.clip(1, 100))

    array = pvlib.pvsystem.Array(mount, module_parameters=MODULE,
                                 modules_per_string=C.MODULES_PER_STRING,
                                 strings=C.STRINGS_PER_INVERTER,
                                 temperature_model_parameters=C.FAIMAN, module_type="glass_glass")
    system = pvlib.pvsystem.PVSystem(array, inverter_parameters=INVERTER,
                                     losses_parameters=C.PVWATTS_LOSSES)
    site = pvlib.location.Location(lat, lon, tz="UTC", altitude=alt)
    mc = pvlib.modelchain.ModelChain(system, site, spectral_model="first_solar",
                                     aoi_model="physical", temperature_model="faiman",
                                     airmass_model="youngirvine1967", losses_model="pvwatts")
    mc.run_model_from_poa(pd.DataFrame({
        "poa_global": poa["poa_global"], "poa_direct": poa["poa_direct"],
        "poa_diffuse": poa["poa_diffuse"], "cell_temperature": t_cell,
        "precipitable_water": pw}))
    ac_kw = (mc.results.ac.clip(lower=0) / 1000.0) * C.N_INVERTER_BLOCKS  # [4]
    out = pd.DataFrame({"ac_kw": ac_kw, "cf": ac_kw / PLANT_DC_KW,
                        "poa_global": poa["poa_global"], "dni": dni, "dhi": dhi})
    out.index = out.index + HALF_HOUR  # back to hour-ending stamps
    return out
