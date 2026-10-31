"""Validation maps: relative bias of ERA5 against MIDAS at 47 GB stations, 2015-2025 (hourly pairs).
(a) GHI, (b) fixed-tilt PV CF, (c) 10 m wind speed, (d) V126 CF. Bias = (ERA5 - MIDAS) / MIDAS mean.
Filton is left out (its MIDAS record averages 44 W/m2 and 1.5 m/s, a faulty or filled series).
Usage: python fig_validation_maps.py METRICS.csv STATION_COORDS.csv ZONES.geojson SITES.csv OUT"""
import sys, numpy as np, pandas as pd, geopandas as gpd
import matplotlib.patheffects
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
MET, CO, ZON, SITES, OUT = sys.argv[1:6]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7})
MM = 1/25.4; INK, Q = '#1d1d1f', '#55565a'
COOL, WARM = '#2c5fa8', '#c8553d'
d = pd.read_csv(MET).merge(pd.read_csv(CO), on='station')
d = d[d.station != 'FILTON']
gb = gpd.read_file(ZON); gb = gb[gb.Name_1.str.startswith('Z')].dissolve()
sites = pd.read_csv(SITES).drop_duplicates('coord_key')
cm = LinearSegmentedColormap.from_list('b', [COOL, '#9dbbe3', '#f7f7f5', '#efb3a3', WARM])
LIM = 0.50
norm = TwoSlopeNorm(0, -LIM, LIM)
PANELS = (('ghi', 'a', 'Global horizontal irradiance'), ('pv_fixed', 'b', 'PV output, fixed 35°'),
          ('wind10', 'c', 'Wind speed at 10 m'), ('wind_v126', 'd', 'V126 output at 100 m'))
fig, axs = plt.subplots(1, 4, figsize=(177*MM, 82*MM))
plt.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.20, wspace=0.04)
for ax, (v, tag, title) in zip(axs, PANELS):
    rel = (d[f'{v}_mbe'] / d[f'{v}_mean_midas']).values
    gb.plot(ax=ax, color='#f1f2f3', edgecolor='#b0b3b8', lw=0.4)
    tech = 'solar' if v in ('ghi', 'pv_fixed') else 'wind'
    s = sites[sites.tech == tech]
    ax.scatter(s.lon, s.lat, marker='^', s=11, facecolors='none', edgecolors=INK, linewidths=0.6, zorder=4)
    o = np.argsort(np.abs(rel))
    ax.scatter(d.lon.values[o], d.lat.values[o], c=np.clip(rel[o], -LIM, LIM), cmap=cm, norm=norm, s=17,
               edgecolors='#55565a', linewidths=0.35, zorder=5)
    big = np.abs(rel) > LIM                                     # beyond the colour range: thick ring
    ax.scatter(d.lon[big], d.lat[big], s=34, facecolors='none', edgecolors=WARM, linewidths=0.8, zorder=6)
    ax.set_xlim(-7.9, 2.0); ax.set_ylim(49.8, 60.9); ax.set_aspect(1/np.cos(np.radians(55))); ax.axis('off')
    ax.set_title(title, fontsize=6.8, color=INK, pad=2)
    ax.text(0.02, 1.05, tag, transform=ax.transAxes, fontsize=8.5, fontweight='bold', color=INK)
    ax.text(0.5, -0.02, f'median {np.median(rel):+.1%};  IQR {np.percentile(rel, 25):+.0%} to {np.percentile(rel, 75):+.0%}',
            transform=ax.transAxes, ha='center', va='top', fontsize=5.8, color=Q)
cax = fig.add_axes([0.30, 0.095, 0.40, 0.022])
cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cm), cax=cax, orientation='horizontal', ticks=[-0.5, -0.25, 0, 0.25, 0.5])
cb.ax.set_xticklabels(['≤ −50%', '−25%', '0', '+25%', '≥ +50%']); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=5.8, length=0)
cb.set_label('ERA5 bias relative to the MIDAS mean (blue: ERA5 lower, red: ERA5 higher)', fontsize=6, color=Q)
fig.text(0.01, 0.105, '●  MIDAS station (47)\n◯  beyond ±50%\n△  model site', ha='left', va='center', linespacing=1.5, fontsize=5.6, color=Q)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
