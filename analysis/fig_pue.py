"""PUE by zone: (a) mean and annual range per supply site, north to south; (b) annual mean PUE 2000-2024."""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
LOAD, SUMMARY, OUT = sys.argv[1:4]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#1d1d1f', 'xtick.major.width': 0.6, 'ytick.major.size': 0})
MM = 1/25.4; INK, Q, GRID, NEU = '#1d1d1f', '#55565a', '#e6e7e9', '#9a9ea5'
COOL, WARM = '#2c5fa8', '#c8553d'
s = pd.read_csv(SUMMARY)
zones = s.groupby('solar_dup').agg(lat=('lat', 'first'), zones=('zone', lambda z: ', '.join(sorted(z, key=lambda v: float(v[1:].replace('_', '.'))))))
NAME = {'Z1_1_Kirkney': 'Kirkney', 'Z1_2_Dundreggan': 'Dundreggan', 'Z3_Pubil': 'Pubil', 'Z5_Kirkurd': 'Kirkurd',
        'Z6_Hownam': 'Hownam', 'Z7_Bayles': 'Bayles', 'Z8_Huddersfield': 'Huddersfield', 'Z10_Nottingham': 'Nottingham',
        'Z11_Birmingham': 'Birmingham', 'Z15_Bishop\'s_Stortford': 'Bishop\'s Stortford', 'Z12_Woodstock': 'Woodstock',
        'Z14_Minley': 'Minley', 'Z13_Eastcott': 'Eastcott'}
ann, stats = {}, {}
for site in zones.index:
    d = pd.read_csv(f'{LOAD}/{site}_load_kw_2000_2025.csv', parse_dates=['time_utc']).set_index('time_utc')
    p = d.load_kw[d.index.year <= 2024] / 5000.0
    a = p.groupby(p.index.year).mean(); ann[site] = a
    stats[site] = dict(mean=p.mean(), lo=a.min(), hi=a.max(), cool=(p > 1.1201).mean()*100)
st = pd.DataFrame(stats).T.join(zones).sort_values('lat')          # south at bottom ... north at top
lowest, highest = st['mean'].idxmin(), st['mean'].idxmax()

fig = plt.figure(figsize=(177*MM, 92*MM))
ax = fig.add_axes([0.24, 0.13, 0.36, 0.78]); bx = fig.add_axes([0.70, 0.13, 0.28, 0.78])
y = np.arange(len(st))
for i, (site, r) in enumerate(st.iterrows()):
    c = COOL if site == lowest else WARM if site == highest else NEU
    ax.plot([r.lo, r.hi], [i, i], color=c, lw=2.2, solid_capstyle='round', alpha=0.45 if c == NEU else 0.55, zorder=2)
    ax.scatter([r['mean']], [i], s=26, color=c if c != NEU else '#5d6168', edgecolors='white', linewidths=0.8, zorder=3)
    ax.text(1.1365, i, f'{r.cool:.0f}%', va='center', ha='right', fontsize=6.3, color=Q)
ax.set_yticks(y); ax.set_yticklabels([f'{NAME[k.replace("_solar", "")]}  ({st.loc[k, "zones"]})' for k in st.index], fontsize=6.3)
for t, k in zip(ax.get_yticklabels(), st.index):
    if k in (lowest, highest): t.set_color(COOL if k == lowest else WARM); t.set_fontweight('bold')
ax.set_xlim(1.1195, 1.1370); ax.set_xticks([1.120, 1.125, 1.130, 1.135]); ax.set_xticklabels(['1.120', '1.125', '1.130', '1.135']); ax.set_ylim(-0.7, len(st)-0.3)
ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
for sp in ('top', 'right', 'left'): ax.spines[sp].set_visible(False)
ax.set_xlabel('Mean PUE, 2000–2024 (dot) and range of annual means (bar)', color=Q, fontsize=6.5)
ax.text(1.1365, len(st)-0.2, 'hours\n>15 °C', ha='right', va='bottom', fontsize=6, color=Q)
ax.annotate('', (1.1198, -0.55), (1.1198, len(st)-0.6), arrowprops=dict(arrowstyle='-|>', color='#b0b3b8', lw=0.6), annotation_clip=False)
ax.text(-0.02, 1.10, 'a', transform=ax.transAxes, fontsize=8.5, fontweight='bold', color=INK, ha='right')
fig.text(0.015, 0.94, 'North', fontsize=6, color=Q); fig.text(0.015, 0.12, 'South', fontsize=6, color=Q)

A = pd.DataFrame(ann)
yrs = A.index.values
bx.fill_between(yrs, A.min(axis=1), A.max(axis=1), color=NEU, alpha=0.18, lw=0, label='range, all sites')
bx.plot(yrs, A.median(axis=1), color='#5d6168', lw=1.0, ls=(0, (3, 2)), label='median site')
bx.plot(yrs, A[highest], color=WARM, lw=2, label=NAME[highest.replace('_solar', '')])
bx.plot(yrs, A[lowest], color=COOL, lw=2, label=NAME[lowest.replace('_solar', '')])
for yr in (2006, 2018, 2022):
    v = A.loc[yr, highest]; bx.annotate(str(yr), (yr, v), (yr, v+0.0018), ha='center', fontsize=6, color=Q,
                                        arrowprops=dict(arrowstyle='-', color='#b0b3b8', lw=0.5))
bx.set_xlim(1999.5, 2024.5); bx.set_ylim(1.1195, 1.1370); bx.set_yticks([1.120, 1.125, 1.130, 1.135]); bx.set_yticklabels(['1.120', '1.125', '1.130', '1.135'])
bx.yaxis.grid(True, color=GRID, lw=0.6); bx.set_axisbelow(True)
for sp in ('top', 'right'): bx.spines[sp].set_visible(False)
bx.set_ylabel('Annual mean PUE', color=Q, fontsize=6.5); bx.tick_params(axis='y', colors='#55565a')
bx.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=6, handlelength=1.6, columnspacing=1.0)
bx.text(-0.16, 1.10, 'b', transform=bx.transAxes, fontsize=8.5, fontweight='bold', color=INK)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
st.round(4).to_csv(f'{OUT}_data.csv')
