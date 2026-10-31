"""Facility load for selected zones: (a) daily mean, 2018; (b) hourly, heatwave week July 2022; (c) load-duration curves 2000-2024."""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
LOAD, OUT = sys.argv[1:3]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
SITES = [("Z15_Bishop's_Stortford_solar", "Z15 Bishop's Stortford (warmest)", '#c8553d'),
         ('Z10_Nottingham_solar', 'Z10 Nottingham (Midlands)', '#5d6168'),
         ('Z3_Pubil_solar', 'Z3/Z4 Pubil (coolest)', '#2c5fa8')]
L = {k: pd.read_csv(f'{LOAD}/{k}_load_kw_2000_2025.csv', parse_dates=['time_utc']).set_index('time_utc').load_kw/1000 for k, _, _ in SITES}
FLOOR = 5.0*1.12

def style(a, letter, ylab='Facility load (MW)'):
    a.yaxis.grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    a.set_ylabel(ylab, color=Q, fontsize=6.5)
    a.axhline(FLOOR, color='#9a9ea5', lw=0.7, ls=(0, (3, 2)), zorder=1)
    a.text(-0.13, 1.04, letter, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)

fig = plt.figure(figsize=(177*MM, 110*MM))
ax = fig.add_axes([0.07, 0.58, 0.90, 0.36]); bx = fig.add_axes([0.07, 0.08, 0.40, 0.36]); cx = fig.add_axes([0.57, 0.08, 0.40, 0.36])
for k, lab, c in SITES:
    d = L[k]['2018'].resample('D').mean()
    ax.plot(d.index, d.values, color=c, lw=1.2 if 'Midlands' in lab else 1.6, label=lab, alpha=0.9 if 'Midlands' in lab else 1)
style(ax, 'a'); ax.set_ylim(5.55, 6.12); ax.set_xlim(pd.Timestamp('2018-01-01'), pd.Timestamp('2018-12-31'))
ax.xaxis.set_major_locator(mpl.dates.MonthLocator()); ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
ax.text(pd.Timestamp('2018-01-08'), FLOOR+0.012, 'free-cooling floor, 5 MW × 1.12 = 5.60 MW', fontsize=6, color=Q)
ax.set_title('Daily mean facility load, 2018 (a hot summer)', loc='left', fontsize=7, color=INK, pad=4)
ax.legend(loc='upper left', frameon=False, fontsize=6.3, ncol=1)

for k, lab, c in SITES:
    h = L[k]['2022-07-14':'2022-07-21']
    bx.plot(h.index, h.values, color=c, lw=1.1 if 'Midlands' in lab else 1.4)
style(bx, 'b'); bx.set_ylim(5.55, 6.9)
bx.xaxis.set_major_locator(mpl.dates.DayLocator()); bx.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d %b'))
plt.setp(bx.get_xticklabels(), rotation=0, fontsize=5.6)
wk = pd.DataFrame({lab: L[k]['2022-07-14':'2022-07-21'] for k, lab, _ in SITES}); who = wk.max().idxmax(); pk = wk[who]; t = pk.idxmax()
bx.annotate(f'peak {pk.max():.2f} MW ({who.split(" (")[0]})', (t, pk.max()), (t - pd.Timedelta('4.5D'), pk.max()-0.02), fontsize=6, color=Q,
            arrowprops=dict(arrowstyle='-', color='#b0b3b8', lw=0.5), va='center')
bx.set_title('Hourly load, heatwave week, 14–21 July 2022', loc='left', fontsize=7, color=INK, pad=4)

for k, lab, c in SITES:
    v = np.sort(L[k][:'2024'].values)[::-1]; x = np.arange(1, len(v)+1)/len(v)*100
    cx.plot(x, v, color=c, lw=1.1 if 'Midlands' in lab else 1.5)
    above = (v > FLOOR+0.0005).mean()*100
    i = [s[0] for s in SITES].index(k)
    cx.annotate(f'{above:.0f}% of hours', (above, FLOOR), ((above + 3, FLOOR + 0.42 - 0.13*i) if i < 2 else (above + 4, FLOOR + 0.62)), fontsize=6, color=c,
                ha='left', arrowprops=dict(arrowstyle='-', color=c, lw=0.5))
style(cx, 'c'); cx.set_xlim(0, 40); cx.set_ylim(5.55, 6.9)
cx.set_xlabel('Share of hours, 2000–2024 (%)', color=Q, fontsize=6.5)
cx.set_title('Load-duration curve: hours above the floor', loc='left', fontsize=7, color=INK, pad=4)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
