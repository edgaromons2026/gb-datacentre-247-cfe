"""Hourly validation diagnostics from validation_hourly.py output (MIDAS gaps kept as gaps):
metrics per station (all hours and daylight only, plus the zero-filled version for comparison) and
Fig. V3: (a) hourly GHI, (b) hourly 10 m wind, (c) diurnal GHI bias by season, (d) monthly output bias,
(e) wind-speed distributions, (f) diffuse fraction: ERA5 against Erbs.
Usage: python fig_validation_hourly.py PAIRS_DIR ERA5_DIR OUT_FIG OUT_METRICS.csv"""
import sys, glob, os, numpy as np, pandas as pd, pvlib
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
PAIRS, ERA5, OUT, MET = sys.argv[1:5]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
COOL, WARM, DARK, AMBER = '#2c5fa8', '#c8553d', '#5d6168', '#d08c00'
st = pd.read_csv(f'{PAIRS}/stations.csv')
P = {r.station: pd.read_pickle(f"{PAIRS}/pairs/{r.station.replace(':', '').replace(' ', '_')}.pkl") for r in st.itertuples()}
VARS = ('ghi', 'wind10', 'pv_fixed', 'pv_single_axis', 'pv_dual_axis', 'v126')


def metrics(x, y):
    m = pd.concat([x, y], axis=1).dropna(); a, b = m.iloc[:, 0], m.iloc[:, 1]
    return dict(n=len(m), r=a.corr(b), rmse=float(np.sqrt(((b - a)**2).mean())), mbe=float((b - a).mean()),
                mean_midas=float(a.mean()), mean_era5=float(b.mean()))


rows = []
for name, d in P.items():
    day = d['zenith'] < 85
    row = dict(station=name)
    for v in VARS:
        for tag, x in (('', d[f'{v}_midas']), ('zf_', d[f'{v}_midas_zf'])):
            row.update({f'{tag}{v}_{k}': val for k, val in metrics(x, d[f'{v}_era5']).items()})
        if v in ('ghi', 'pv_fixed', 'pv_single_axis', 'pv_dual_axis'):
            row.update({f'day_{v}_{k}': val for k, val in metrics(d[f'{v}_midas'][day], d[f'{v}_era5'][day]).items()})
    yrs = d.index.year
    for v in ('pv_fixed', 'v126'):                                 # annual relative bias, full years only
        g = d[[f'{v}_midas', f'{v}_era5']].dropna().groupby(yrs[d[[f'{v}_midas', f'{v}_era5']].notna().all(axis=1)]).mean()
        g = g[g.index <= 2024]; row[f'{v}_annual_bias_sd'] = float((g[f'{v}_era5']/g[f'{v}_midas'] - 1).std())
    rows.append(row)
M = pd.DataFrame(rows).merge(st, on='station'); M.to_csv(MET, index=False)

fig = plt.figure(figsize=(177*MM, 118*MM))
W, H = 0.25, 0.30
pos = [[0.07, 0.60], [0.40, 0.60], [0.73, 0.60], [0.07, 0.10], [0.40, 0.10], [0.73, 0.10]]
ax = [fig.add_axes([x, y, W, H]) for x, y in pos]
def tidy(a, grid='y'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    if grid: (a.yaxis if grid == 'y' else a.xaxis).grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
def tag(a, t): a.text(-0.2, 1.06, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)
lab = dict(color=Q, fontsize=6.3)
allp = pd.concat(P.values())

# (a, b) pooled hourly density
for a, v, lim, unit, cm, t in ((ax[0], 'ghi', 1000, 'W/m²', 'YlOrBr', 'a'), (ax[1], 'wind10', 20, 'm/s', 'Blues', 'b')):
    sel = (allp['zenith'].values < 85) if v == 'ghi' else np.ones(len(allp), bool)
    m = allp.loc[sel, [f'{v}_midas', f'{v}_era5']].dropna()
    h = a.hexbin(m[f'{v}_midas'], m[f'{v}_era5'], gridsize=60, extent=(0, lim, 0, lim), bins='log', cmap=cm, mincnt=1, lw=0)
    a.plot([0, lim], [0, lim], color=DARK, lw=0.6, ls=(0, (3, 2)))
    a.set_xlim(0, lim); a.set_ylim(0, lim); a.set_aspect('equal', adjustable='box')
    a.set_xlabel(f'MIDAS ({unit})', **lab); a.set_ylabel(f'ERA5 ({unit})', **lab)
    r = M[f'{v}_r'].median()
    a.text(0.04, 0.96, f"{'GHI, daylight' if v == 'ghi' else '10 m wind'}\nmedian station r = {r:.2f}", transform=a.transAxes, va='top', fontsize=6, color=INK)
    tidy(a, None); tag(a, t)

# (c) diurnal GHI bias by season (UTC hour, mean ERA5 - MIDAS over stations)
for mon, c, nm in (((12, 1, 2), COOL, 'Dec–Feb'), ((3, 4, 5), '#6a9a5b', 'Mar–May'), ((6, 7, 8), WARM, 'Jun–Aug'), ((9, 10, 11), AMBER, 'Sep–Nov')):
    s = allp[allp.index.month.isin(mon)]
    b = (s['ghi_era5'] - s['ghi_midas']).groupby(s.index.hour).mean()
    ax[2].plot(b.index, b.values, color=c, lw=1.3, label=nm)
ax[2].axhline(0, color=DARK, lw=0.6); ax[2].set_xlim(3, 21); ax[2].set_xticks(range(3, 22, 3))
ax[2].set_xlabel('Hour (UTC, hour ending)', **lab); ax[2].set_ylabel('Mean GHI bias, ERA5 − MIDAS (W/m²)', **lab)
ax[2].legend(frameon=False, fontsize=5.6, loc='upper right', ncol=1, handlelength=1.4, columnspacing=0.8); tidy(ax[2]); tag(ax[2], 'c')

# (d) monthly relative bias of output, median and IQR across stations
for v, c, nm in (('pv_fixed', AMBER, 'PV fixed 35°'), ('v126', COOL, 'V126')):
    rb = pd.DataFrame({n: (lambda g: g[f'{v}_era5']/g[f'{v}_midas'] - 1)(d[[f'{v}_midas', f'{v}_era5']].dropna().groupby(d[[f'{v}_midas', f'{v}_era5']].dropna().index.month).mean())
                       for n, d in P.items()})
    ax[3].fill_between(rb.index, rb.quantile(0.25, axis=1), rb.quantile(0.75, axis=1), color=c, alpha=0.18, lw=0)
    ax[3].plot(rb.index, rb.median(axis=1), color=c, lw=1.5, label=nm)
ax[3].axhline(0, color=DARK, lw=0.6); ax[3].set_xticks(range(1, 13)); ax[3].set_xticklabels(list('JFMAMJJASOND'))
ax[3].yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); ax[3].set_ylabel('Output bias, ERA5 vs MIDAS', **lab)
ax[3].legend(frameon=False, fontsize=6, loc='upper center'); tidy(ax[3]); tag(ax[3], 'd')

# (e) pooled 10 m wind-speed distribution
bins = np.arange(0, 20.5, 0.5)
for v, c, nm in (('wind10_midas', DARK, 'MIDAS'), ('wind10_era5', COOL, 'ERA5')):
    x = allp[['wind10_midas', 'wind10_era5']].dropna()[v]
    ax[4].hist(x, bins=bins, density=True, histtype='step', color=c, lw=1.3, label=nm)
calm_m = (allp['wind10_midas'].dropna() < 1.0).mean(); calm_e = (allp.loc[allp['wind10_midas'].notna(), 'wind10_era5'] < 1.0).mean()
ax[4].text(0.97, 0.6, f'hours below 1 m/s\nMIDAS {calm_m:.1%}\nERA5 {calm_e:.1%}', transform=ax[4].transAxes, ha='right', fontsize=5.8, color=Q)
ax[4].set_xlim(0, 18); ax[4].set_xlabel('10 m wind speed (m/s)', **lab); ax[4].set_ylabel('Share of hours (density)', **lab)
ax[4].legend(frameon=False, fontsize=6); tidy(ax[4]); tag(ax[4], 'e')

# (f) diffuse fraction by month: ERA5's own split, Erbs on ERA5 GHI, Erbs on MIDAS GHI
def era5(var):
    d = pd.read_csv(f'{ERA5}/ERA5_{var}_2015_2025.csv'); d.columns = [c.strip() for c in d.columns]
    if d.columns[0].startswith('Unnamed'): d = d.drop(columns=d.columns[0])
    d = d.set_index('Datetime'); d.index = pd.to_datetime(d.index).tz_localize('UTC'); return d
dif, dirh = era5('InfluxDiffuse'), era5('InfluxDirect')
fr = {k: [] for k in ('era5', 'erbs_era5', 'erbs_midas')}
for r in st.itertuples():
    col = [c for c in dif.columns if c.replace(':', '').replace(' ', '') == r.station.replace(':', '').replace(' ', '')][0]
    d = P[r.station]; idx = d.index
    sp = pvlib.solarposition.get_solarposition(idx - pd.Timedelta('30min'), r.lat, r.lon)
    zen = pd.Series(sp['zenith'].values, idx); ok = (zen < 80) & d['ghi_midas'].notna() & (d['ghi_era5'] > 20) & (d['ghi_midas'] > 20)
    ge = (dif[col] + dirh[col]).reindex(idx)
    e_dhi = pd.Series(pvlib.irradiance.erbs(ge.values, zen.values, idx.dayofyear.values)['dhi'], idx)
    m_dhi = pd.Series(pvlib.irradiance.erbs(d['ghi_midas'].values, zen.values, idx.dayofyear.values)['dhi'], idx)
    for k, num, den in (('era5', dif[col].reindex(idx), ge), ('erbs_era5', e_dhi, ge), ('erbs_midas', m_dhi, d['ghi_midas'])):
        g = pd.DataFrame({'n': num[ok], 'd': den[ok]}).groupby(idx[ok].month).sum(); fr[k].append(g['n'] / g['d'])
for k, c, ls, nm in (('era5', COOL, '-', 'ERA5 diffuse / GHI'), ('erbs_era5', COOL, (0, (3, 1.6)), 'Erbs split of ERA5 GHI'),
                     ('erbs_midas', DARK, '-', 'Erbs split of MIDAS GHI')):
    f = pd.concat(fr[k], axis=1).mean(axis=1); ax[5].plot(f.index, f.values, color=c, ls=ls, lw=1.3, label=nm)
ax[5].set_xticks(range(1, 13)); ax[5].set_xticklabels(list('JFMAMJJASOND')); ax[5].set_ylim(0.3, 1.0)
ax[5].yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); ax[5].set_ylabel('Diffuse share of daylight GHI', **lab)
ax[5].legend(frameon=False, fontsize=5.6, loc='upper center'); tidy(ax[5]); tag(ax[5], 'f')
pd.DataFrame({k: pd.concat(v, axis=1).mean(axis=1) for k, v in fr.items()}).to_csv(MET.replace('.csv', '_diffuse_fraction.csv'))

for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
