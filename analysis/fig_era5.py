"""ERA5 weather at the study sites: (a) zone map with sites; (b-e) 2010 daily series of 100 m wind speed,
2 m temperature, GHI and diffuse share (the PV model inputs) for three zones, against each zone's 2000-2024 daily climatology."""
import sys, numpy as np, pandas as pd, geopandas as gpd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import Point
ERA, ZONES, SUMMARY, OUT = sys.argv[1:5]
YEAR = 2010
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
SEL = [('Z3', '', '', '', '#2c5fa8', 'Z3 Scotland (Pubil PV, Muir wind)'),
       ('Z10', '', '', '', '#5d6168', 'Z10 Midlands (Nottingham)'),
       ('Z14', '', '', '', '#c8553d', 'Z14 South (Minley)')]

def load(var):
    d = pd.read_csv(f'{ERA}/ERA5_{var}_2000_2025.csv', parse_dates=['Datetime']).set_index('Datetime')
    return d[d.index.year <= 2024]
ws, tt, dn = load('WindSpeed100m'), load('Temperature') - 273.15, load('InfluxDirect')
gh, df_ = load('GHI'), load('InfluxDiffuse')

fig = plt.figure(figsize=(177*MM, 140*MM))
mx = fig.add_axes([0.0, 0.02, 0.36, 0.94])
axs = [fig.add_axes([0.45, 0.735 - i*0.235, 0.54, 0.195]) for i in range(4)]

# ---- (a) map
g = gpd.read_file(ZONES).set_crs(4326, allow_override=True)
g = g[~g['Name_1'].isin(['DOGGER_BANK', 'HORNSEA', 'EAST_ANGLIA'])].to_crs(27700)
sel_ids = {s[0]: s[4] for s in SEL}
g.plot(ax=mx, color='#eceef1', edgecolor='#a3a7ad', linewidth=0.35)
for zid, c in sel_ids.items():
    g[g.Name_1 == zid].plot(ax=mx, color=c, alpha=0.22, edgecolor=c, linewidth=0.9)
s = pd.read_csv(SUMMARY)
def xy(lat, lon):
    p = gpd.GeoSeries([Point(lo, la) for la, lo in zip(lat, lon)], crs=4326).to_crs(27700); return p.x, p.y
sx, sy = xy(s.lat, s.lon); wx, wy = xy(s.wlat, s.wlon)
mx.scatter(sx, sy, s=14, marker='o', c='#f2a516', edgecolors='white', linewidths=0.5, zorder=4, label='solar site')
mx.scatter(wx, wy, s=16, marker='^', c='#3a3d42', edgecolors='white', linewidths=0.5, zorder=4, label='wind site')
for _, r in g.iterrows():
    p = max(list(r.geometry.geoms) if r.geometry.geom_type == 'MultiPolygon' else [r.geometry], key=lambda q: q.area).representative_point()
    mx.text(p.x, p.y, r.Name_1, fontsize=5.4, ha='center', va='center', color=sel_ids.get(r.Name_1, Q),
            fontweight='bold' if r.Name_1 in sel_ids else 'normal', zorder=5)
mx.set_xlim(-10000, 680000); mx.set_ylim(-10000, 1230000); mx.set_aspect('equal'); mx.axis('off')
mx.legend(loc='upper left', frameon=False, fontsize=6, bbox_to_anchor=(0.0, 0.42))
mx.plot([430000, 530000], [60000]*2, color=INK, lw=1.2); mx.text(480000, 72000, '100 km', ha='center', fontsize=6)
mx.text(0.02, 0.985, 'a', transform=mx.transAxes, fontsize=8.5, fontweight='bold', color=INK, va='top')
mx.text(0.10, 0.985, '20 study zones and their ERA5 sites', transform=mx.transAxes, fontsize=7, color=INK, va='top')

# ---- (b-d) series
spec = [(ws, 'wind', '100 m wind speed (m s$^{-1}$)', 'b', 'mean'),
        (tt, 'solar', '2 m temperature (°C)', 'c', 'mean'),
        (gh, 'solar', 'GHI (W m$^{-2}$)', 'd', 'mean'),
        (None, 'solar', 'Diffuse share of GHI', 'e', 'ratio')]
for ax, (df, kind, ylab, letter, how) in zip(axs, spec):
    notes = []
    for zid, name, sol, wnd, c, lab in SEL:
        col = next(k for k in (df if df is not None else gh).columns if k.startswith(f'{zid}_') and k.endswith(f'_{kind}'))
        if how == 'ratio':
            col = next(k for k in gh.columns if k.startswith(f'{zid}_') and k.endswith('_solar'))
            g_d = gh[col].resample('D').sum(); d = (df_[col].resample('D').sum() / g_d).where(g_d > 0)
        else:
            d = df[col].resample('D').mean()
        clim = d.groupby(d.index.dayofyear).mean().rolling(15, center=True, min_periods=1).mean()
        yr = d[str(YEAR)].rolling(7, center=True, min_periods=1).mean()
        cl = clim.reindex(yr.index.dayofyear).values
        if letter in ('b', 'd'):
            anom = (d[str(YEAR)].mean() / d.groupby(d.index.year).mean().drop(YEAR).mean() - 1)*100; unit = f'{anom:+.0f}%'
        elif letter == 'c':
            anom = d[str(YEAR)].mean() - d.groupby(d.index.year).mean().drop(YEAR).mean(); unit = f'{anom:+.1f} °C'
        else:
            anom = (d[str(YEAR)].mean() - d.groupby(d.index.year).mean().drop(YEAR).mean())*100; unit = f'{anom:+.0f} pp'
        unit = unit.replace('-', '−')
        ax.plot(yr.index, cl, color=c, lw=0.8, ls=(0, (3, 2)), alpha=0.9)
        ax.plot(yr.index, yr.values, color=c, lw=1.5, label=lab)
        notes.append((unit, c))
    ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    ax.set_ylabel(ylab, color=Q, fontsize=6.3)
    ax.set_xlim(pd.Timestamp(f'{YEAR}-01-01'), pd.Timestamp(f'{YEAR}-12-31'))
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator()); ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    ax.text(-0.13, 1.02, letter, transform=ax.transAxes, fontsize=8.5, fontweight='bold', color=INK)
    x0 = 0.995
    for txt, c in reversed(notes):
        t = ax.text(x0, 1.02, txt, transform=ax.transAxes, ha='right', va='bottom', fontsize=6, color=c, fontweight='bold'); x0 -= (0.105 if letter == 'c' else 0.085 if letter == 'e' else 0.075)
    ax.text(x0, 1.02, f'{YEAR} vs 2000–24:', transform=ax.transAxes, ha='right', va='bottom', fontsize=6, color=Q)
    if letter != 'e': ax.set_xticklabels([])
    if letter == 'e': ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
axs[0].legend(loc='lower left', frameon=False, fontsize=6, ncol=3, bbox_to_anchor=(0.0, 1.12), handlelength=1.4, columnspacing=1.2)
fig.text(0.45, 1.005, f'{YEAR} (the lowest-wind year): 7-day mean (solid) and 2000–2024 daily climatology (dashed)', fontsize=6.5, color=Q)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
