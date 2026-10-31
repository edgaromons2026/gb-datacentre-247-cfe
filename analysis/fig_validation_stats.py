"""Validation statistics, ERA5 against MIDAS at 47 GB stations, hourly pairs 2015-2025 (Filton left out):
(a) hourly correlation by variable, (b) relative mean bias by variable, (c) how input bias carries into
output bias, (d) station-mean capacity factor, ERA5 against MIDAS.
Usage: python fig_validation_stats.py METRICS.csv OUT"""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
MET, OUT = sys.argv[1:3]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
COOL, WARM, DARK, AMBER = '#2c5fa8', '#c8553d', '#5d6168', '#d08c00'
d = pd.read_csv(MET); d = d[d.station != 'FILTON']
VARS = (('ghi', 'GHI', AMBER), ('pv_fixed', 'PV fixed 35°', AMBER), ('pv_single_axis', 'PV single-axis', AMBER),
        ('pv_dual_axis', 'PV dual-axis', AMBER), ('wind10', 'Wind 10 m', COOL), ('wind_v126', 'V126 output', COOL))
rel = lambda v: d[f'{v}_mbe'] / d[f'{v}_mean_midas']
rng = np.random.default_rng(1)

fig = plt.figure(figsize=(177*MM, 120*MM))
ax = fig.add_axes([0.08, 0.60, 0.38, 0.33]); bx = fig.add_axes([0.58, 0.60, 0.40, 0.33])
cx = fig.add_axes([0.08, 0.09, 0.38, 0.36]); dx = fig.add_axes([0.58, 0.09, 0.18, 0.36]); ex = fig.add_axes([0.81, 0.09, 0.18, 0.36])
def tidy(a, grid='y'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    (a.yaxis if grid == 'y' else a.xaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.12): a.text(x, 1.08, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)
pct = mpl.ticker.PercentFormatter(1, decimals=0)

# (a) and (b): one dot per station, bar at the median
for a, f, lab in ((ax, lambda v: d[f'{v}_r'], 'Hourly correlation r'), (bx, rel, 'Mean bias, ERA5 vs MIDAS')):
    for i, (v, name, c) in enumerate(VARS):
        y = f(v).values; x = i + rng.uniform(-0.18, 0.18, len(y))
        a.scatter(x, y, s=6, color=c, alpha=0.45, lw=0)
        a.plot([i-0.3, i+0.3], [np.median(y)]*2, color=INK, lw=1.4, solid_capstyle='butt')
        a.text(i+0.33, np.median(y) + (0.04 if (a is bx and v == 'wind10') else 0), f'{np.median(y):.2f}' if a is ax else f'{np.median(y):+.0%}'.replace('-0%', '0%').replace('+0%', '0%'), fontsize=5.6, color=INK, va='center')
    a.set_xticks(range(len(VARS))); a.set_xticklabels([n for _, n, _ in VARS], rotation=30, ha='right', fontsize=6)
    a.set_ylabel(lab, color=Q, fontsize=6.5); a.tick_params(axis='x', length=0); tidy(a)
ax.set_ylim(0.6, 1.0)
bx.axhline(0, color=DARK, lw=0.6); bx.set_ylim(-0.35, 0.75); bx.yaxis.set_major_formatter(pct)
for i, v in ((4, 'wind10'), (5, 'wind_v126')):                  # stations off the axis
    n = int((rel(v) > 0.75).sum())
    if n: bx.annotate(f'{n} above', (i, 0.74), fontsize=5.2, color=Q, ha='center', va='top')
tag(ax, 'a'); tag(bx, 'b', -0.13)

# (c) input bias -> output bias
for vi, vo, c, lab in (('ghi', 'pv_fixed', AMBER, 'GHI → PV fixed'), ('wind10', 'wind_v126', COOL, '10 m wind → V126')):
    x, y = rel(vi).values, rel(vo).values
    cx.scatter(x, y, s=10, color=c, alpha=0.7, lw=0, label=lab)
    k, b = np.polyfit(x, y, 1); xx = np.linspace(x.min(), x.max(), 10)
    cx.plot(xx, k*xx + b, color=c, lw=1.0)
    cx.text(xx[-1], k*xx[-1] + b, f'  slope {k:.1f}', color=c, fontsize=5.8, va='center')
lim = (-0.35, 0.8); cx.plot(lim, lim, color=DARK, lw=0.6, ls=(0, (3, 2))); cx.text(0.55, 0.47, '1:1', fontsize=5.6, color=DARK)
cx.set_xlim(*lim); cx.set_ylim(-0.35, 1.7); cx.axhline(0, color='#cfd2d6', lw=0.5); cx.axvline(0, color='#cfd2d6', lw=0.5)
cx.xaxis.set_major_formatter(pct); cx.yaxis.set_major_formatter(pct)
cx.set_xlabel('Bias in the weather input', color=Q, fontsize=6.5); cx.set_ylabel('Bias in the simulated output', color=Q, fontsize=6.5)
cx.legend(loc='upper left', frameon=False, fontsize=6, handletextpad=0.2); tidy(cx); tag(cx, 'c')

# (d, e) station-mean CF
for a, v, c, lab, lo, hi, t, x0 in ((dx, 'pv_fixed', AMBER, 'PV fixed 35°', 0.08, 0.16, 'd', -0.42), (ex, 'wind_v126', COOL, 'V126', 0.1, 0.65, 'e', -0.3)):
    a.scatter(d[f'{v}_mean_midas'], d[f'{v}_mean_era5'], s=10, color=c, alpha=0.75, lw=0)
    a.plot([lo, hi], [lo, hi], color=DARK, lw=0.6, ls=(0, (3, 2))); a.text(hi, lo + 0.04*(hi-lo), '1:1 ', fontsize=5.6, color=DARK, ha='right')
    a.set_xlim(lo, hi); a.set_ylim(lo, hi); a.set_aspect('equal', adjustable='box')
    a.xaxis.set_major_formatter(pct); a.yaxis.set_major_formatter(pct); a.locator_params(nbins=4)
    a.set_title(lab, fontsize=6.5, color=INK, pad=3); tidy(a); tag(a, t, x0)
dx.set_ylabel('Mean CF driven by ERA5', color=Q, fontsize=6.5)
fig.text(0.785, 0.015, 'Mean CF driven by MIDAS', ha='center', color=Q, fontsize=6.5)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
