"""Wind results (V126 at 100 m, net of the 0.86 farm-loss factor): (a) mean CF by site, (b) monthly CF,
(c) annual CF 2000-2024, (d) longest low-wind spell per site and year. No validation panel (kept for the validation section)."""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
WIND, SITES, OUT = sys.argv[1:4]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID, NEU = '#1d1d1f', '#55565a', '#e6e7e9', '#9a9ea5'
COOL, WARM, DARK = '#2c5fa8', '#c8553d', '#5d6168'
LOSS = 0.86
NAME = {'Z1_1_Kirkney': 'Kirkney', 'Z1_2_Dundreggan': 'Dundreggan', 'Z3_Muir': 'Muir', 'Z4_East_Croft': 'East Croft',
        'Z6_Hownam': 'Hownam', 'Z7_Bayles': 'Bayles', 'Z8_Lydgate': 'Lydgate', 'Z10_Nottingham': 'Nottingham',
        'Z11_Bickenhill': 'Bickenhill', 'Z12_Woodstock': 'Woodstock', 'Z13_Whitbourne_Springs': 'Whitbourne Springs',
        'Z14_Minley': 'Minley'}
sites = pd.read_csv(SITES).query("tech == 'wind'").drop_duplicates('site').set_index('site')
zones = pd.read_csv(SITES).query("tech == 'wind'").groupby('duplicate_of').zone.apply(
    lambda z: ', '.join(sorted(z, key=lambda v: float(v[1:].replace('_', '.')))))
ann, mon, spell = {}, {}, {}
for k in NAME:
    v = pd.read_csv(f'{WIND}/{k}_wind_wind_cf_2000_2025.csv', index_col=0, parse_dates=True)['wind_cf_v126_100m']
    v = v[v.index.year <= 2024] * LOSS
    ann[k] = v.groupby(v.index.year).mean(); mon[k] = v.groupby(v.index.month).mean()
    low = v.resample('D').mean() < 0.10; out = {}
    for y in range(2000, 2025):
        best = cur = 0
        for x in low[low.index.year == y].values: cur = cur + 1 if x else 0; best = max(best, cur)
        out[y] = best
    spell[k] = out
order = sorted(NAME, key=lambda k: sites.loc[f'{k}_wind', 'lat'])     # south first -> bottom
hi, lo = max(NAME, key=lambda k: ann[k].mean()), min(NAME, key=lambda k: ann[k].mean())
dup = lambda k: zones.get(f'{k}_wind', zones.get(f"{k.replace('_wind', '')}_solar", ''))
def zlabel(k):
    for key in (f'{k}_wind', f'{k}_solar'):
        if key in zones.index: return zones[key]
    return ''

fig = plt.figure(figsize=(177*MM, 132*MM))
ax = fig.add_axes([0.17, 0.57, 0.30, 0.37]); bx = fig.add_axes([0.62, 0.57, 0.36, 0.37])
cx = fig.add_axes([0.17, 0.08, 0.30, 0.34]); dx = fig.add_axes([0.62, 0.08, 0.33, 0.34])
def tidy(a, grid='x'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    (a.xaxis if grid == 'x' else a.yaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.02): a.text(x, 1.11, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK, ha='right')
pct = mpl.ticker.PercentFormatter(1, decimals=0)

# (a) mean net CF and range of annual means, with gross for reference
for i, k in enumerate(order):
    a = ann[k]
    ax.plot([a.min(), a.max()], [i, i], color=COOL, lw=2.0, alpha=0.35, solid_capstyle='round')
    ax.scatter([a.mean()], [i], s=18, color=COOL, edgecolors='white', linewidths=0.6, zorder=3, label='net of 0.86 losses' if i == 0 else None)
    ax.scatter([a.mean()/LOSS], [i], s=14, facecolors='none', edgecolors=DARK, linewidths=0.6, zorder=3, label='gross' if i == 0 else None)
ax.set_yticks(range(len(order))); ax.set_yticklabels([f'{NAME[k]}  ({zlabel(k)})' for k in order], fontsize=6.0, color=INK)
for t, k in zip(ax.get_yticklabels(), order):
    if k in (hi, lo): t.set_fontweight('bold')
ax.tick_params(axis='y', length=0); ax.set_ylim(-0.6, len(order)-0.4); ax.spines['left'].set_visible(False)
ax.set_xlabel('Capacity factor, 2000–2024; sites north (top) to south\n(bar: range of annual means, net)', color=Q, fontsize=6.3)
ax.xaxis.set_major_formatter(pct); tidy(ax)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=6.2, handletextpad=0.2)
tag(ax, 'a', -0.55)

# (b) monthly net CF
mo = np.arange(1, 13); M = pd.DataFrame(mon)
bx.fill_between(mo, M.min(axis=1), M.max(axis=1), color=NEU, alpha=0.2, lw=0, label='range, 12 sites')
bx.plot(mo, M.median(axis=1), color=DARK, lw=1.0, ls=(0, (3, 2)), label='median site')
bx.plot(mo, M[hi], color=COOL, lw=1.6, label=NAME[hi]); bx.plot(mo, M[lo], color=WARM, lw=1.6, label=NAME[lo])
bx.set_xticks(mo); bx.set_xticklabels(list('JFMAMJJASOND')); bx.set_xlim(0.7, 12.3); bx.set_ylim(0, 0.52)
bx.yaxis.set_major_formatter(pct); bx.set_ylabel('Monthly mean CF (net)', color=Q, fontsize=6.5); tidy(bx, 'y')
r_hi = M[hi][[12, 1, 2]].mean() / M[hi][[6, 7, 8]].mean()
bx.text(6.5, 0.47, f'winter (DJF) ≈ {r_hi:.1f} × summer (JJA)', ha='center', fontsize=6, color=Q)
bx.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=6.0, handlelength=1.5, columnspacing=0.8)
tag(bx, 'b', -0.13)

# (c) annual net CF
A = pd.DataFrame(ann); yrs = A.index.values
cx.fill_between(yrs, A.min(axis=1), A.max(axis=1), color=NEU, alpha=0.2, lw=0, label='range, 12 sites')
cx.plot(yrs, A.median(axis=1), color=DARK, lw=1.0, ls=(0, (3, 2)), label='median site')
cx.plot(yrs, A[hi], color=COOL, lw=1.6, label=NAME[hi]); cx.plot(yrs, A[lo], color=WARM, lw=1.6, label=NAME[lo])
for yr in (2010, 2021):
    cx.annotate(str(yr), (yr, A.loc[yr].median()), (yr, A.min().min() - 0.012), ha='center', fontsize=6, color=Q,
                arrowprops=dict(arrowstyle='-', color='#b0b3b8', lw=0.5))
cx.set_xlim(1999.5, 2024.5); cx.yaxis.set_major_formatter(pct); cx.set_ylim(A.min().min() - 0.02, A.max().max() + 0.01)
cx.set_ylabel('Annual mean CF (net)', color=Q, fontsize=6.5); tidy(cx, 'y')
cx.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=6.0, handlelength=1.5, columnspacing=0.8)
tag(cx, 'c', -0.13)

# (d) longest run of days with daily mean net CF below 10%
S = pd.DataFrame(spell)[order[::-1]]                                   # north at top
cm = LinearSegmentedColormap.from_list('w', ['#ffffff', '#f3c9bd', WARM, '#7a2a1c'])
im = dx.imshow(S.T.values, aspect='auto', cmap=cm, vmin=0, vmax=20, interpolation='nearest')
dx.set_yticks(range(len(S.columns))); dx.set_yticklabels([NAME[k] for k in S.columns], fontsize=5.8, color=INK)
dx.set_xticks(range(0, 25, 5)); dx.set_xticklabels(range(2000, 2025, 5))
for i, k in enumerate(S.columns):
    j = int(np.argmax(S[k].values)); dx.text(j, i, S[k].values[j], ha='center', va='center', fontsize=4.8, color='white', fontweight='bold')
for sp in dx.spines.values(): sp.set_visible(False)
dx.tick_params(length=0)
cb = fig.colorbar(im, ax=dx, fraction=0.035, pad=0.02, ticks=[0, 5, 10, 15, 20]); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=5.8, length=0)
cb.set_label('days', color=Q, fontsize=6)
dx.set_title('Longest spell of days with mean CF < 10% (number: worst year)', fontsize=6.3, color=Q, loc='left')
tag(dx, 'd', -0.2)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
