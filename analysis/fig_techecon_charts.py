"""Fig. T2 (costs) and Fig. T3 (Market Index Price) for the techno-economic inputs write-up.
T2: (a) annualised cost by cost year, 2025 = 100; (b) 2025 annualised cost split into capital recovery and fixed O&M;
(c) annualised cost against discount rate, 7% = 100.
T3: (a) monthly mean MIP with 5-95% band, (b) annual distribution, (c) mean daily profile by period, (d) negative-price hours.
Usage: python fig_techecon_charts.py COSTS_BY_YEAR.csv RATE.csv MIP.csv OUT_T2 OUT_T3"""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
CBY, RATE, MIP, OUT2, OUT3 = sys.argv[1:6]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
COOL, WARM, DARK, AMBER, TEAL, GREEN = '#2c5fa8', '#c8553d', '#5d6168', '#d08c00', '#1f9e7d', '#6a9a5b'
NAMES = {'pv_fixed': ('PV fixed', AMBER, '-'), 'pv_tracking': ('PV single-axis', AMBER, (0, (3, 1.5))), 'wind': ('Onshore wind', COOL, '-'),
         'bat_e': ('Battery energy', GREEN, '-'), 'bat_p': ('Battery inverter', GREEN, (0, (3, 1.5))),
         'electrolyser': ('Electrolyser', WARM, '-'), 'h2_store': ('H$_2$ tank', WARM, (0, (1, 1.2))), 'fuel_cell': ('Fuel cell', WARM, (0, (3, 1.5)))}
def tidy(a, grid='y'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    (a.yaxis if grid == 'y' else a.xaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.16): a.text(x, 1.06, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)
lab = dict(color=Q, fontsize=6.5)
def save(fig, out):
    for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
        fig.savefig(f'{out}.{ext}', bbox_inches='tight', **kw)

# ---------------- T2 ----------------
T = pd.read_csv(CBY); R = pd.read_csv(RATE)
fig = plt.figure(figsize=(177*MM, 70*MM))
ax = fig.add_axes([0.06, 0.14, 0.27, 0.74]); bx = fig.add_axes([0.45, 0.14, 0.22, 0.74]); cx = fig.add_axes([0.75, 0.14, 0.24, 0.74])
P = T.pivot(index='cost_year', columns='asset', values='annualised_gbp_per_unit_yr')
ends = {}
for k, (nm, c, ls) in NAMES.items():
    y = 100 * P[k] / P[k].iloc[0]; ax.plot(P.index, y, color=c, ls=ls, lw=1.2, marker='o', ms=2); ends[k] = y.iloc[-1]
order = sorted(ends, key=ends.get); pos = {}; last = -1e9
for k in order: pos[k] = max(ends[k], last + 4.2); last = pos[k]   # push labels apart vertically
for k, (nm, c, ls) in NAMES.items(): ax.text(2051, pos[k], nm, fontsize=5.3, color=c, va='center')
ax.set_xlim(2024, 2060); ax.set_xticks(range(2025, 2051, 5)); ax.set_ylim(25, 105)
ax.set_ylabel('Annualised cost, 2025 = 100', **lab); ax.set_xlabel('Cost year (technology-data)', **lab); tidy(ax); tag(ax, 'a')
t = T[T.cost_year == 2025].set_index('asset').loc[list(NAMES)]
cap_ = t.investment_gbp2024 * t.annuity; fom = t.investment_gbp2024 * t.fom_pct.fillna(0) / 100
share = cap_ / (cap_ + fom); y = np.arange(len(t))
bx.barh(y, share, color=COOL, height=0.6, label='capital recovery'); bx.barh(y, 1 - share, left=share, color='#9dbbe3', height=0.6, label='fixed O&M')
for i, k in enumerate(t.index):
    bx.text(1.02, i, f"£{t.annualised_gbp_per_unit_yr[k]/1000:.1f}k", va='center', fontsize=5.6, color=INK)
bx.set_yticks(y); bx.set_yticklabels([NAMES[k][0] for k in t.index], fontsize=6); bx.invert_yaxis(); bx.set_xlim(0, 1.22)
bx.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); bx.set_xticks([0, 0.5, 1])
bx.set_xlabel('Share of 2025 annualised cost', **lab); bx.legend(frameon=False, fontsize=5.6, loc='lower left', bbox_to_anchor=(-0.02, 1.0), ncol=2)
tidy(bx, 'x'); tag(bx, 'b', -0.38)
base = R[R.rate.round(2) == 0.07].iloc[0]
for k, (nm, c, ls) in NAMES.items():
    cx.plot(R.rate*100, 100*R[k]/base[k], color=c, ls=ls, lw=1.2, marker='o', ms=2, label=nm)
cx.legend(frameon=False, fontsize=4.8, loc='upper left', ncol=1, handlelength=2.2)
cx.axvline(7, color=DARK, lw=0.6, ls=(0, (3, 2))); cx.text(7.2, 66, 'central 7%', fontsize=5.6, color=DARK)
cx.set_xticks([3, 5, 7, 10]); cx.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
cx.set_ylabel('Annualised cost, 7% = 100', **lab); cx.set_xlabel('Discount rate', **lab); tidy(cx); tag(cx, 'c')
save(fig, OUT2)

# ---------------- T3 ----------------
m = pd.read_csv(MIP, index_col=0); m.index = pd.to_datetime(m.index, utc=True); p = m.iloc[:, 0]
p = p[p.index < '2025-01-01']
fig = plt.figure(figsize=(177*MM, 112*MM))
ax = fig.add_axes([0.07, 0.60, 0.92, 0.33]); bx = fig.add_axes([0.07, 0.09, 0.27, 0.36])
cx = fig.add_axes([0.42, 0.09, 0.27, 0.36]); dx = fig.add_axes([0.77, 0.09, 0.22, 0.36])
mo = p.resample('MS'); lo, hi, mean = mo.quantile(0.05), mo.quantile(0.95), mo.mean()
ax.fill_between(mean.index, lo, hi, color=COOL, alpha=0.18, lw=0, label='5–95% of hours')
ax.plot(mean.index, mean, color=COOL, lw=1.3, label='monthly mean')
ax.plot(mean.index, mean + 50, color=WARM, lw=1.0, ls=(0, (3, 1.5)), label='import cost: mean + £50 adder')
ax.axvspan(pd.Timestamp('2021-09-01', tz='UTC'), pd.Timestamp('2023-04-01', tz='UTC'), color=GRID, lw=0, zorder=0)
ax.text(pd.Timestamp('2022-06-01', tz='UTC'), 455, 'gas price crisis', ha='center', fontsize=6, color=Q)
ax.set_ylim(-20, 480); ax.set_ylabel('£/MWh', **lab); ax.legend(frameon=False, fontsize=6, loc='upper left'); tidy(ax); tag(ax, 'a', -0.05)
ax.set_xlim(pd.Timestamp('2015-01-01', tz='UTC'), pd.Timestamp('2025-01-01', tz='UTC'))
yrs = sorted(set(p.index.year))
bp = bx.boxplot([p[p.index.year == y].dropna().values for y in yrs], positions=range(len(yrs)), widths=0.6, whis=(5, 95), showfliers=False,
                patch_artist=True, medianprops=dict(color=INK, lw=1), boxprops=dict(lw=0.5), whiskerprops=dict(lw=0.5), capprops=dict(lw=0.5))
for b, y in zip(bp['boxes'], yrs): b.set_facecolor(WARM if y in (2021, 2022) else '#9dbbe3'); b.set_alpha(0.8)
bx.set_xticks(range(len(yrs))); bx.set_xticklabels([str(y)[2:] for y in yrs]); bx.set_xlabel('Year (20xx); whiskers 5–95%', **lab)
bx.set_ylabel('£/MWh', **lab); bx.set_ylim(-60, 620); tidy(bx); tag(bx, 'b')
for (a, b), c, nm in (((2015, 2020), COOL, '2015–2020'), ((2021, 2022), WARM, '2021–2022'), ((2023, 2024), DARK, '2023–2024')):
    s = p[(p.index.year >= a) & (p.index.year <= b)]; prof = s.groupby(s.index.hour).mean()
    cx.plot(prof.index, prof / prof.mean(), color=c, lw=1.3, label=nm)
cx.axhline(1, color=DARK, lw=0.5); cx.set_xlim(0, 23); cx.set_xticks(range(0, 24, 6))
cx.set_xlabel('Hour of day (UTC)', **lab); cx.set_ylabel('Mean price ÷ period mean', **lab); cx.legend(frameon=False, fontsize=5.8); tidy(cx); tag(cx, 'c')
neg = p.groupby(p.index.year).apply(lambda x: (x < 0).sum())
dx.bar(range(len(neg)), neg.values, color=TEAL, width=0.65); dx.set_xticks(range(len(neg))); dx.set_xticklabels([str(y)[2:] for y in neg.index])
dx.set_ylabel('Hours with MIP < 0', **lab); dx.set_xlabel('Year (20xx)', **lab); tidy(dx); tag(dx, 'd')
save(fig, OUT3)
