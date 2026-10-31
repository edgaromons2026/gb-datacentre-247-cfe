"""PV results: (a) mean CF by site and mount, (b) monthly CF, (c) annual fixed-tilt CF 2000-2024.
The ERA5 vs MIDAS check is left for the validation section."""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
PV, SITES, OUT = sys.argv[1:4]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID, NEU = '#1d1d1f', '#55565a', '#e6e7e9', '#9a9ea5'
COOL, WARM, DARK = '#2c5fa8', '#c8553d', '#5d6168'
MOUNT = {'fixed': ('Fixed 35°', COOL), 'single_axis': ('Single-axis', WARM), 'dual_axis': ('Dual-axis', DARK)}
NAME = {'Z1_1_Kirkney': 'Kirkney', 'Z1_2_Dundreggan': 'Dundreggan', 'Z3_Pubil': 'Pubil', 'Z5_Kirkurd': 'Kirkurd',
        'Z6_Hownam': 'Hownam', 'Z7_Bayles': 'Bayles', 'Z8_Huddersfield': 'Huddersfield', 'Z10_Nottingham': 'Nottingham',
        'Z11_Birmingham': 'Birmingham', "Z15_Bishop's_Stortford": "Bishop's Stortford", 'Z12_Woodstock': 'Woodstock',
        'Z14_Minley': 'Minley', 'Z13_Eastcott': 'Eastcott'}
lat = pd.read_csv(SITES).query("tech == 'solar'").set_index('site')['lat']
ann, mon = {}, {}
for k in NAME:
    d = pd.read_csv(f"{PV}/{k}_solar_pv_cf_2000_2025.csv", index_col=0, parse_dates=True)
    d = d[d.index.year <= 2024]; d.columns = [c.replace('pv_cf_', '') for c in d.columns]
    ann[k] = d.groupby(d.index.year).mean(); mon[k] = d.groupby(d.index.month).mean()
order = sorted(NAME, key=lambda k: lat[f'{k}_solar'])                  # south first -> bottom
hi, lo = max(NAME, key=lambda k: ann[k]['fixed'].mean()), min(NAME, key=lambda k: ann[k]['fixed'].mean())

fig = plt.figure(figsize=(177*MM, 128*MM))
ax = fig.add_axes([0.13, 0.56, 0.33, 0.39]); bx = fig.add_axes([0.62, 0.56, 0.36, 0.39])
cx = fig.add_axes([0.13, 0.08, 0.85, 0.32])
def tidy(a, grid='x'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    (a.xaxis if grid == 'x' else a.yaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.02): a.text(x, 1.11, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK, ha='right')

# (a) mean CF per site and mount, with the range of annual means
for i, k in enumerate(order):
    for j, (m, (lab, c)) in enumerate(MOUNT.items()):
        a = ann[k][m]; y = i + (j-1)*0.22
        ax.plot([a.min(), a.max()], [y, y], color=c, lw=1.6, alpha=0.35, solid_capstyle='round')
        ax.scatter([a.mean()], [y], s=13, color=c, edgecolors='white', linewidths=0.5, zorder=3, label=lab if i == 0 else None)
ax.set_yticks(range(len(order))); ax.set_yticklabels([NAME[k] for k in order], fontsize=6.3, color=INK)
for t, k in zip(ax.get_yticklabels(), order):
    if k in (hi, lo): t.set_fontweight('bold')
ax.tick_params(axis='y', length=0); ax.set_ylim(-0.6, len(order)-0.4); ax.spines['left'].set_visible(False)
ax.set_xlabel('Capacity factor, 2000–2024 (dot: mean; bar: range of annual means)', color=Q, fontsize=6.3)
ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); tidy(ax)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, fontsize=6.2, handletextpad=0.2, columnspacing=1.0)
fig.text(0.015, 0.94, 'North', fontsize=6, color=Q); fig.text(0.015, 0.56, 'South', fontsize=6, color=Q); tag(ax, 'a', -0.27)

# (b) monthly CF, south-east (hi) vs Highland (lo), fixed vs single-axis
mo = np.arange(1, 13)
for k, ls in ((hi, '-'), (lo, (0, (3, 1.6)))):
    for m in ('fixed', 'single_axis'):
        bx.plot(mo, mon[k][m], color=MOUNT[m][1], lw=1.5, ls=ls)
    bx.text(12.25, mon[k]['fixed'][12], NAME[k], fontsize=6, color=Q, va='center')
bx.set_xticks(mo); bx.set_xticklabels(list('JFMAMJJASOND')); bx.set_xlim(0.7, 12.3)
bx.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); bx.set_ylabel('Monthly mean CF', color=Q, fontsize=6.5); tidy(bx, 'y')
bx.annotate('tracking wins\nApril–September', (7, mon[hi]['single_axis'][7]), (8.7, 0.225), fontsize=6, color=WARM, ha='left',
            arrowprops=dict(arrowstyle='-', color=WARM, lw=0.5))
bx.annotate('fixed 35° wins\nOctober–March', (1, mon[hi]['fixed'][1]), (0.9, 0.225), fontsize=6, color=COOL, ha='left',
            arrowprops=dict(arrowstyle='-', color=COOL, lw=0.5))
h = [mpl.lines.Line2D([], [], color=MOUNT[m][1], lw=1.5) for m in ('fixed', 'single_axis')] + \
    [mpl.lines.Line2D([], [], color=Q, lw=1.2), mpl.lines.Line2D([], [], color=Q, lw=1.2, ls=(0, (3, 1.6)))]
bx.legend(h, ['Fixed 35°', 'Single-axis', NAME[hi], NAME[lo]], loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False,
          fontsize=6.2, handlelength=1.8, columnspacing=0.9); tag(bx, 'b', -0.13)

# (c) annual fixed-tilt CF
A = pd.DataFrame({k: ann[k]['fixed'] for k in NAME}); yrs = A.index.values
cx.fill_between(yrs, A.min(axis=1), A.max(axis=1), color=NEU, alpha=0.2, lw=0, label='range, 13 sites')
cx.plot(yrs, A.median(axis=1), color=DARK, lw=1.0, ls=(0, (3, 2)), label='median site')
cx.plot(yrs, A[hi], color='#2b2d31', lw=1.6, label=NAME[hi]); cx.plot(yrs, A[lo], color='#8d929a', lw=1.6, label=NAME[lo])
for yr in (2003, 2024):
    v = A.loc[yr, hi]; cx.text(yr + 0.3, v, str(yr), ha='left', va='center', fontsize=6, color=Q)
cx.set_xlim(1999.5, 2025.4); cx.set_xticks(range(2000, 2021, 5)); cx.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
cx.set_ylabel('Annual CF, fixed 35°', color=Q, fontsize=6.5); tidy(cx, 'y')
cx.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=6.0, handlelength=1.5, columnspacing=0.8); tag(cx, 'c', -0.06)

for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
