"""Hourly ERA5 vs MIDAS validation that keeps MIDAS gaps as gaps.

The final_*_2015_2025.csv MIDAS files fill every missing hour with 0 (checked against the raw
hourly_ghi / wind_speed files), which run.step_validation then scores as a real observation.
Here those hours are set to NaN using the raw files, both datasets are run through the same
gbtea PV and wind models as in run.step_validation, and the hourly pairs are saved per station.

Usage: GBTEA_DRIVE_ROOT=<root holding Energy_System_Modelling_GB and techno_econs_...> \
       python validation_hourly.py GBTEA_PARENT OUT_DIR [N_STATIONS]"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
from gbtea import config as C, weather, pv, wind
OUT = sys.argv[2]; os.makedirs(f'{OUT}/pairs', exist_ok=True)
NMAX = int(sys.argv[3]) if len(sys.argv) > 3 else None
MOUNTS = ('fixed', 'single_axis', 'dual_axis')


def raw(name):
    d = pd.read_csv(C.MIDAS_DIR / name, index_col=0)
    d.columns = [c.strip() for c in d.columns]
    d.index = pd.to_datetime(d.index).tz_localize('UTC')
    return d


st = weather.gb_midas_stations(pd.read_csv(C.MIDAS_STATIONS))
ghi_m, wind_m, p_m = weather.read_midas('ghi'), weather.read_midas('wind10'), weather.read_midas('pressure')
ghi_m, wind_m, p_m, _ = weather.check_midas_units(ghi_m, wind_m, p_m, report=lambda s: None)
t_m, rh_m = weather.read_midas('temp'), weather.read_midas('rh')
ghi_raw, wind_raw = raw('hourly_ghi_2015_2025.csv'), raw('wind_speed_2015_2025.csv')

cache, rows = {}, []
stations = [s for _, s in st.iterrows() if s['Name'] in ghi_m.columns and s['Name'] != 'FILTON']
for s in stations[:NMAX]:
    name = s['Name']
    e = weather.era5_site_frame(name, folder=C.ERA5_2015_2025, span='2015_2025', cache=cache)
    e['wind10'] = pv.wind_at_10m(e['wind100'], e['roughness'])
    m = pd.DataFrame({'ghi': ghi_m[name], 'temp': t_m[name], 'rh': rh_m[name],
                      'wind10': wind_m[name], 'pressure': p_m[name]}).reindex(e.index)
    gap_g = ghi_raw[name].reindex(e.index).isna()
    gap_w = wind_raw[name].reindex(e.index).isna()
    m.loc[m['pressure'] <= 0, 'pressure'] = np.nan
    m.loc[m['rh'] <= 0, 'rh'] = np.nan
    m['albedo'] = e['albedo']
    alt = s.get('Altitude', 0.0) if pd.notna(s.get('Altitude', np.nan)) else 0.0
    # zero-filled run, exactly as step_validation, for the before/after comparison
    mz = m.ffill().bfill()
    out = pd.DataFrame(index=e.index)
    out['ghi_midas'], out['ghi_era5'] = m['ghi'].where(~gap_g), e['ghi']
    out['wind10_midas'], out['wind10_era5'] = m['wind10'].where(~gap_w), e['wind10']
    out['ghi_midas_zf'], out['wind10_midas_zf'] = m['ghi'], m['wind10']
    for mount in MOUNTS:
        a = pv.simulate(mz, s.Latitude, s.Longitude, alt, mount)['cf']
        out[f'pv_{mount}_midas'] = a.where(~gap_g)
        out[f'pv_{mount}_midas_zf'] = a
        out[f'pv_{mount}_era5'] = pv.simulate(e, s.Latitude, s.Longitude, alt, mount)['cf']
    ww = e[['roughness', 'temp']].assign(wind10=m['wind10'])
    a = wind.simulate_modern(ww, alt, z_meas=10, wind_col='wind10')['cf']
    out['v126_midas'], out['v126_midas_zf'] = a.where(~gap_w), a
    out['v126_era5'] = wind.simulate_modern(e, alt)['cf']
    out['zenith'] = pv.pvlib.solarposition.get_solarposition(e.index - pv.HALF_HOUR, s.Latitude, s.Longitude)['apparent_zenith'].values
    out.astype('float32').to_pickle(f'{OUT}/pairs/{name.replace(":", "").replace(" ", "_")}.pkl')
    rows.append({'station': name, 'lat': s.Latitude, 'lon': s.Longitude, 'alt': alt,
                 'gap_ghi': gap_g.mean(), 'gap_wind': gap_w.mean()})
    print(name, f"gaps ghi {gap_g.mean():.3f} wind {gap_w.mean():.3f}", flush=True)
pd.DataFrame(rows).to_csv(f'{OUT}/stations.csv', index=False)
