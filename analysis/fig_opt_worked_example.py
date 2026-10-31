"""Fig. O2, worked example of the design LP at Z10 Nottingham, weather year 2018 (outputs of opt_worked_example.py):
(a) cost per MWh of load by asset, islanded and grid-connected at 95% CFE, (b) islanded dispatch in a
late-December week, (c) the same week grid-connected, (d) state of charge of the battery and hydrogen tank over the year.
Usage: python fig_opt_worked_example.py RUN_DIR OUT"""
import sys, json, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
RUN, OUT = sys.argv[1:3]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
COOL, WARM, DARK, AMBER = '#2c5fa8', '#c8553d', '#5d6168', '#d08c00'
GREEN, LAMB, PALE = '#6a9a5b', '#f0c060', '#9dbbe3'
R = {m: json.load(open(f'{RUN}/result_{m}_2018.json')) for m in ('islanded', 'grid')}
D = {m: pd.read_pickle(f'{RUN}/dispatch_{m}_2018.pkl') for m in ('islanded', 'grid')}
fig = plt.figure(figsize=(177*MM, 128*MM))
ax = fig.add_axes([0.10, 0.62, 0.36, 0.30]); dx = fig.add_axes([0.58, 0.62, 0.41, 0.30])
bx = fig.add_axes([0.10, 0.10, 0.36, 0.36]); cx = fig.add_axes([0.58, 0.10, 0.41, 0.36])
def tidy(a, grid='y'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    (a.yaxis if grid == 'y' else a.xaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.16): a.text(x, 1.07, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)
lab = dict(color=Q, fontsize=6.5)

# (a) cost per MWh of load
seen = set()
parts = (('PV fixed', ('pv_fixed',), LAMB), ('PV single-axis', ('pv_tracking',), AMBER), ('Wind', ('wind', 'vom'), COOL),
         ('Battery energy', ('bat_e',), GREEN), ('Battery inverter', ('bat_p',), '#a9c79c'),
         ('Hydrogen chain', ('electrolyser', 'h2_store', 'fuel_cell'), WARM), ('Grid imports', ('grid_import',), DARK))
for j, (m, name) in enumerate((('islanded', 'Islanded\n(100% CFE)'), ('grid', 'Grid-connected\n(95% CFE)'))):
    b = R[m]['breakdown_gbp']; E = R[m]['load_mwh']; x0 = 0
    for nm, ks, c in parts:
        v = sum(b.get(k, 0) for k in ks) / E
        if v > 0.05:
            ax.barh(j, v, left=x0, color=c, height=0.55, lw=0, label=nm if nm not in seen else None); seen.add(nm)
            if v > 9: ax.text(x0 + v/2, j, f'{v:.0f}', ha='center', va='center', fontsize=5.6, color='white' if c in (COOL, DARK, WARM, GREEN) else INK)
            x0 += v
    ex = b.get('export_revenue', 0) / E
    if ex < 0:
        ax.barh(j, ex, color='white', edgecolor=COOL, hatch='/////', height=0.55, lw=0.6, label='Export revenue')
        ax.text(ex/2, j - 0.42, f'{ex:.0f}', ha='center', va='center', fontsize=5.6, color=COOL)
    ax.text(x0 + 2, j, f"£{R[m]['cost_gbp_per_mwh']:.0f}/MWh net", va='center', fontsize=6.2, color=INK, fontweight='bold')
ax.set_yticks([0, 1]); ax.set_yticklabels(['Islanded\n(100% CFE)', 'Grid-connected\n(95% CFE)'], fontsize=6.3); ax.invert_yaxis()
ax.axvline(0, color=DARK, lw=0.6); ax.set_xlim(-20, 185); ax.set_xlabel('£ per MWh of data-centre load', **lab)
ax.tick_params(axis='y', length=0); tidy(ax, 'x'); tag(ax, 'a', -0.27)
h, l = ax.get_legend_handles_labels(); ax.legend(h, l, frameon=False, fontsize=5.4, ncol=4, loc='lower left', bbox_to_anchor=(-0.27, 1.12), handlelength=1.1, columnspacing=0.8)

# (b, c) dispatch in one winter week
w0, w1 = '2018-12-21', '2018-12-28'
for a, m, t in ((bx, 'islanded', 'b'), (cx, 'grid', 'c')):
    d = D[m].loc[w0:w1]; caps = R[m]; x = d.index
    layers = [('Wind', d.wd, COOL), ('PV', d.pvf + d.pvt, AMBER), ('Battery discharge', d.bat_dis, GREEN), ('Fuel cell', d.get('fc', 0*d.wd), WARM)]
    if m == 'grid': layers.append(('Grid import', d.imp, DARK))
    a.stackplot(x, *[v.values for _, v, _ in layers], colors=[c for _, _, c in layers], labels=[n for n, _, _ in layers], lw=0, alpha=0.9)
    neg = [('Battery charge', -d.bat_ch, '#a9c79c'), ('Electrolysis', -d.get('el', 0*d.wd), '#efb3a3')]
    if m == 'grid': neg.append(('Export', -d.exp, PALE))
    a.stackplot(x, *[v.values for _, v, _ in neg], colors=[c for _, _, c in neg], labels=[n for n, _, _ in neg], lw=0, alpha=0.9)
    avail = caps['pv_fixed'] * d.cf_fixed + caps['pv_tracking'] * d.cf_tracking + caps['wind'] * d.cf_wind
    a.plot(x, avail, color=INK, lw=0.6, ls=(0, (2, 1.5)), label='Wind + PV available')
    a.plot(x, d.load, color=INK, lw=1.2, label='Load')
    a.axhline(0, color=DARK, lw=0.5); a.set_ylim(-12, 30); a.set_xlim(x[0], x[-1])
    a.xaxis.set_major_locator(mpl.dates.DayLocator()); a.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d')); a.set_xlabel('December 2018', **lab)
    a.set_ylabel('MW (below 0: power taken off the bus)', **lab)
    a.set_title(f"{'Islanded' if m == 'islanded' else 'Grid-connected, 95% CFE'}, 21 to 28 Dec 2018", fontsize=6.5, color=INK, pad=3)
    tidy(a); tag(a, t, -0.16 if a is bx else -0.13)
h, l = cx.get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=5.6, ncol=5, loc='lower center', bbox_to_anchor=(0.54, -0.06), handlelength=1.2, columnspacing=1.0)

# (d) state of charge across the year, islanded
d = D['islanded']; c = R['islanded']
dd = d[['bat_soc', 'h2_soc']].resample('D').mean()
dx.plot(dd.index, dd.bat_soc / c['bat_e'], color=GREEN, lw=1.0, label=f"Battery ({c['bat_e']:.0f} MWh)")
dx.plot(dd.index, dd.h2_soc / c['h2_store'], color=WARM, lw=1.2, label=f"Hydrogen tank ({c['h2_store']:.0f} MWh H2)")
dx.axvspan(pd.Timestamp(w0, tz='UTC'), pd.Timestamp(w1, tz='UTC'), color=GRID, lw=0)
dx.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); dx.set_ylim(0, 1.05)
dx.xaxis.set_major_locator(mpl.dates.MonthLocator()); dx.xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
dx.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: mpl.dates.num2date(v).strftime('%b')[0]))
dx.set_ylabel('State of charge, daily mean', **lab); dx.set_title('Islanded design, storage through 2018', fontsize=6.5, color=INK, pad=3)
dx.legend(frameon=False, fontsize=5.8, loc='upper left'); tidy(dx); tag(dx, 'd', -0.13)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
