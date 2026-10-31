"""Results figures R1-R6 for the flagship paper, from results_tables.py outputs.
Usage: python fig_results.py RESULTS_DIR FLAGSHIP_DIR ZONES_SUMMARY ZONES_GEOJSON OUT_DIR"""
import sys, numpy as np, pandas as pd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
RD, FL, ZS, GJ, OUT = sys.argv[1:6]
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.edgecolor': '#b0b3b8', 'axes.linewidth': 0.6,
                     'xtick.color': '#55565a', 'ytick.color': '#55565a', 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
MM = 1/25.4; INK, Q, GRID = '#1d1d1f', '#55565a', '#e6e7e9'
COOL, WARM, DARK, AMBER, TEAL, GREEN, LIGHT = '#2c5fa8', '#c8553d', '#5d6168', '#d08c00', '#1f9e7d', '#6a9a5b', '#9dbbe3'
PVF, PVT, WND, BAT, H2, GRD = '#e3a21a', '#f2cf6b', '#2c5fa8', '#6a9a5b', '#c8553d', '#8d939c'
TGT = {0.9: '#9dbbe3', 0.95: '#5b8bd0', 0.99: '#2c5fa8', 1.0: '#1d3f73'}
DIST = ['Z1_1', 'Z1_2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z10', 'Z11', 'Z12', 'Z13', 'Z14', 'Z15']  # north to south, distinct weather
COPY = {'Z1_1': 'Z2', 'Z1_2': 'Z1_3, Z1_4', 'Z8': 'Z9', 'Z13': 'Z17', 'Z14': 'Z16'}
zs = pd.read_csv(ZS).set_index('zone')
def place(z): return zs.loc[z, 'solar_site'].split('_')[-2].replace("Bishop's", "Bishop's")
LAB = [f"{z}\n{place(z)}" for z in DIST]
def tidy(a, grid='y'):
    for sp in ('top', 'right'): a.spines[sp].set_visible(False)
    if grid: (a.yaxis if grid == 'y' else a.xaxis).grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)
def tag(a, t, x=-0.08, y=1.04): a.text(x, y, t, transform=a.transAxes, fontsize=8.5, fontweight='bold', color=INK)
lab = dict(color=Q, fontsize=6.5)
def save(fig, name):
    for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
        fig.savefig(f'{OUT}/{name}.{ext}', bbox_inches='tight', **kw)
    plt.close(fig)
def zticks(a, rot=0):
    a.set_xticks(range(len(DIST))); a.set_xticklabels(DIST, fontsize=5.8, rotation=rot); a.set_xlim(-0.6, len(DIST) - 0.4)

d = pd.read_csv(f'{RD}/designs_enriched.csv'); isl = d[d['mode'] == 'islanded']; gr = d[d['mode'] == 'grid']
ti = pd.read_csv(f'{RD}/islanded_by_zone.csv', index_col=0).loc[DIST]
tg = pd.read_csv(f'{RD}/grid_by_zone_target.csv')
x = np.arange(len(DIST))

# ---------------- R1 installed capacity ----------------
fig = plt.figure(figsize=(177*MM, 120*MM))
a = fig.add_axes([0.06, 0.58, 0.92, 0.36]); b = fig.add_axes([0.06, 0.08, 0.40, 0.36]); c = fig.add_axes([0.58, 0.08, 0.40, 0.36])
w = 0.27
w = 0.36
for k, (col, cl, nm) in enumerate((('pv_fixed', PVF, 'PV fixed (single-axis never chosen)'), ('wind', WND, 'Wind'))):
    med = [isl[isl.zone == z][col].median() for z in DIST]
    lo = [isl[isl.zone == z][col].quantile(0.25) for z in DIST]; hi = [isl[isl.zone == z][col].quantile(0.75) for z in DIST]
    a.bar(x + (k - 0.5) * w, med, w, color=cl, label=nm, edgecolor='white', lw=0.3)
    a.errorbar(x + (k - 0.5) * w, med, yerr=[np.subtract(med, lo), np.subtract(hi, med)], fmt='none', ecolor=DARK, lw=0.5, capsize=1)
a2 = a.twinx()
a2.plot(x, [isl[isl.zone == z].bat_e.median() for z in DIST], 'o', color=BAT, ms=3.5, label='Battery (MWh, right)')
a2.plot(x, [isl[isl.zone == z].h2_store.median() for z in DIST], 'D', color=H2, ms=3.2, label='H$_2$ tank (MWh, right)')
a2.spines['top'].set_visible(False); a2.set_ylabel('Storage energy, MWh', **lab)
zticks(a); a.set_ylabel('Generation capacity, MW', **lab); tidy(a); tag(a, 'a', -0.05)
h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, frameon=False, fontsize=5.8, ncol=5, loc='upper left')
a.set_ylim(0, 65); a2.set_ylim(0, 845); a.text(0.995, 1.02, 'Islanded, 100% CFE: median of 25 single-year designs (bars: IQR)', transform=a.transAxes, ha='right', fontsize=6, color=Q)
# b: grid targets, median over zones of the per-zone medians
ts_ = [0.9, 0.95, 0.99, 1.0]; gm = tg.groupby('cfe_target').median(numeric_only=True)
im = ti[['pv', 'wind', 'bat_e', 'h2_store']].median()
cats = ['Grid 90%', 'Grid 95%', 'Grid 99%', 'Grid 100%', 'Islanded']
pv_ = list(gm.loc[ts_, 'pv']) + [im.pv]; wd_ = list(gm.loc[ts_, 'wind']) + [im.wind]
xb = np.arange(5)
b.bar(xb - 0.18, pv_, 0.36, color=PVF, label='PV (fixed + single-axis)'); b.bar(xb + 0.18, wd_, 0.36, color=WND, label='Wind')
b.set_xticks(xb); b.set_xticklabels(cats, fontsize=6); b.set_ylabel('Capacity, MW (median of zones)', **lab)
b.axhline(5 * 1.13, color=DARK, lw=0.6, ls=(0, (3, 2)), label='mean facility load ≈ 5.6 MW')
b.legend(frameon=False, fontsize=5.8, loc='upper left'); tidy(b); tag(b, 'b', -0.14)
bt = list(gm.loc[ts_, 'bat_e']) + [im.bat_e]; h2_ = list(gm.loc[ts_, 'h2_store']) + [im.h2_store]
c.bar(xb - 0.18, bt, 0.36, color=BAT, label='Battery energy'); c.bar(xb + 0.18, np.maximum(h2_, 0), 0.36, color=H2, label='H$_2$ tank')
for i, v in enumerate(h2_): c.text(i + 0.18, max(v, 0) + 6, f'{abs(v):.0f}', ha='center', fontsize=5.3, color=H2)
c.set_xticks(xb); c.set_xticklabels(cats, fontsize=6); c.set_ylabel('Storage energy, MWh (median of zones)', **lab)
c.legend(frameon=False, fontsize=5.8, loc='upper left'); tidy(c); tag(c, 'c', -0.14)
save(fig, 'Fig_results_capacity')

# ---------------- R2 energy mix and capacity factors ----------------
fig = plt.figure(figsize=(177*MM, 125*MM))
a = fig.add_axes([0.06, 0.58, 0.42, 0.36]); b = fig.add_axes([0.56, 0.58, 0.42, 0.36]); c = fig.add_axes([0.06, 0.08, 0.92, 0.36])
def mix(sub):
    g = sub.groupby('zone'); r = pd.DataFrame({k: g[k].median() for k in ('pv_mwh_per_load', 'wind_mwh_per_load', 'import_mwh_per_load', 'export_mwh_per_load', 'avail_per_load')}).loc[DIST]
    r['curt'] = r.avail_per_load - r.pv_mwh_per_load - r.wind_mwh_per_load; return r
for ax_, sub, ttl in ((a, isl, 'Islanded, 100% CFE'), (b, gr[gr.cfe_target.round(2) == 0.95], 'Grid-connected, 95% CFE')):
    r = mix(sub); bot = np.zeros(len(DIST))
    for col, cl, nm in (('pv_mwh_per_load', PVF, 'PV used'), ('wind_mwh_per_load', WND, 'Wind used'), ('import_mwh_per_load', GRD, 'Grid import'), ('curt', '#e9d7c8', 'Curtailed')):
        if r[col].max() < 1e-6: continue
        ax_.bar(x, r[col], 0.7, bottom=bot, color=cl, label=nm, edgecolor='white', lw=0.3); bot += r[col].values
    if r.export_mwh_per_load.max() > 1e-6: ax_.bar(x, -r.export_mwh_per_load, 0.7, color=TEAL, label='Export')
    ax_.axhline(1, color=INK, lw=0.6); ax_.axhline(0, color=INK, lw=0.4)
    ax_.set_xticks(x); ax_.set_xticklabels(DIST, fontsize=5.4, rotation=90); ax_.set_xlim(-0.6, len(DIST) - 0.4)
    ax_.set_ylabel('MWh per MWh of data-centre load', **lab); ax_.set_title(ttl, fontsize=6.8, color=INK, loc='left')
    ax_.legend(frameon=False, fontsize=5.4, ncol=3, loc='upper left', bbox_to_anchor=(0, -0.2)); tidy(ax_)
a.set_ylim(-0.3, 2.9); b.set_ylim(-0.3, 2.9); tag(a, 'a', -0.12); tag(b, 'b', -0.12)
cfz = zs.loc[DIST]
w = 0.2
for k, (vals, cl, nm) in enumerate(((cfz.pv_fixed, PVF, 'PV fixed (resource)'), (cfz.pv_track, PVT, 'PV single-axis (resource)'),
                                    (cfz.wind * 0.86, WND, 'Wind V126 after 0.86 loss (resource)'))):
    c.bar(x + (k - 1.5) * w, vals, w, color=cl, label=nm, edgecolor='white', lw=0.3)
c.bar(x + 1.5 * w, [isl[isl.zone == z].wind_cf_real.median() for z in DIST], w, color='#9dbbe3', label='Wind delivered (islanded, after curtailment)')
c.plot(x - 1.5 * w, [isl[isl.zone == z].pv_cf_real.median() for z in DIST], '_', color=INK, ms=6, mew=1.2, label='PV delivered (islanded)')
zticks(c); c.set_ylabel('Capacity factor, 2000–2024 mean', **lab); c.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
c.legend(frameon=False, fontsize=5.6, ncol=3, loc='upper left'); c.set_ylim(0, 0.5); tidy(c); tag(c, 'c', -0.05)
save(fig, 'Fig_results_energy')

# ---------------- R3 economics ----------------
ge = pd.read_csv(f'{RD}/grid_equivalent_by_zone_year.csv'); gy = ge[ge.zone == 'Z10'].set_index('year')
fig = plt.figure(figsize=(177*MM, 125*MM))
a = fig.add_axes([0.07, 0.56, 0.91, 0.38]); b = fig.add_axes([0.07, 0.08, 0.50, 0.34]); c = fig.add_axes([0.66, 0.08, 0.32, 0.34])
bp = a.boxplot([isl[isl.zone == z].cost_gbp_per_mwh for z in DIST], positions=x, widths=0.5, whis=(0, 100), patch_artist=True,
               medianprops=dict(color=INK, lw=1), boxprops=dict(lw=0.5), whiskerprops=dict(lw=0.5), capprops=dict(lw=0.5))
for bb in bp['boxes']: bb.set_facecolor('#e8c9bf')
for t, mk in ((0.9, 'v'), (0.95, 's'), (0.99, '^'), (1.0, 'D')):
    sub = tg[tg.cfe_target.round(2) == t].set_index('zone').loc[DIST]
    a.plot(x + 0.33, sub.lco_med, mk, color=TGT[t], ms=3.3, label=f'Grid-connected {t:.0%} (median of 10 years)', ls='none')
a.fill_between([-0.6, len(DIST)], gy.grid_cost_gbp_per_mwh.min(), gy.grid_cost_gbp_per_mwh.max(), color=GRD, alpha=0.15, lw=0)
a.axhline(ge.grid_cost_gbp_per_mwh.mean(), color=DARK, lw=0.8, ls=(0, (4, 2)))
a.text(-0.5, gy.grid_cost_gbp_per_mwh.min() - 14, f'grid only, MIP + £50: 2015–24 mean £{ge.grid_cost_gbp_per_mwh.mean():.0f} (dashed), yearly range £{gy.grid_cost_gbp_per_mwh.min():.0f}–{gy.grid_cost_gbp_per_mwh.max():.0f} (band)', ha='left', fontsize=5.6, color=DARK)
a.plot([], [], 's', color='#e8c9bf', mec=INK, mew=0.4, label='Islanded 100% (box: 25 design years)')
zticks(a); a.set_ylabel('LCO24/7, £ per MWh of load', **lab); a.set_ylim(0, 560); a.legend(frameon=False, fontsize=5.5, ncol=3, loc='upper left'); tidy(a); tag(a, 'a', -0.05)
# b: cost breakdown for the median-cost design year of each zone
U = dict(pv_fixed=48353, pv_tracking=55526, wind=112498, bat_e=18570, bat_p=34549, electrolyser=236183, fuel_cell=255791, h2_store=5295)
def brk(sub):
    out = []
    for z in DIST:
        s = sub[sub.zone == z]; r = s.iloc[(s.cost_gbp_per_mwh - s.cost_gbp_per_mwh.median()).abs().argsort().iloc[0]]
        L = r.load_mwh; capx = {k: U[k] * max(r[k], 0) for k in U}
        vom = 1.579 * r.wind_mwh
        grid = r.objective_gbp - sum(capx.values()) - vom
        out.append(dict(zone=z, PV=(capx['pv_fixed'] + capx['pv_tracking']) / L, Wind=(capx['wind'] + vom) / L, Battery=(capx['bat_e'] + capx['bat_p']) / L,
                        Hydrogen=(capx['electrolyser'] + capx['fuel_cell'] + capx['h2_store']) / L, Grid=grid / L, total=r.cost_gbp_per_mwh))
    return pd.DataFrame(out).set_index('zone')
bi = brk(isl); bg = brk(gr[gr.cfe_target.round(2) == 0.95]); bi.to_csv(f'{RD}/cost_breakdown_islanded.csv'); bg.to_csv(f'{RD}/cost_breakdown_grid95.csv')
for off, br, hatch in ((-0.2, bi, None), (0.2, bg, '////')):
    bot = np.zeros(len(DIST)); neg = np.zeros(len(DIST))
    for col, cl in (('PV', PVF), ('Wind', WND), ('Battery', BAT), ('Hydrogen', H2), ('Grid', GRD)):
        v = br[col].values; pos = np.where(v > 0, v, 0); ng = np.where(v < 0, v, 0)
        b.bar(x + off, pos, 0.38, bottom=bot, color=cl, hatch=hatch, edgecolor='white', lw=0.3, label=col if off < 0 else None); bot += pos
        b.bar(x + off, ng, 0.38, bottom=neg, color=cl, hatch=hatch, edgecolor='white', lw=0.3); neg += ng
b.axhline(0, color=INK, lw=0.4); b.set_xticks(x); b.set_xticklabels(DIST, fontsize=5.4, rotation=90); b.set_xlim(-0.6, len(DIST) - 0.4)
b.set_ylabel('£ per MWh of load', **lab); b.add_patch(mpl.patches.Rectangle((0, 0), 0, 0, facecolor='white', edgecolor=DARK, hatch='////', label='left: islanded; hatched: grid 95%'))
b.legend(frameon=False, fontsize=5.4, ncol=3, loc='upper left'); b.set_ylim(-30, 330); tidy(b); tag(b, 'b', -0.1)
c.plot(gy.index, gy.wholesale_gbp_per_mwh, color=COOL, lw=1.2, marker='o', ms=2.5, label='Wholesale (MIP), load-weighted')
c.plot(gy.index, gy.grid_cost_gbp_per_mwh, color=WARM, lw=1.2, marker='o', ms=2.5, label='Grid supply = MIP + £50')
c.set_ylabel('£ per MWh of load (Z10 load shape)', **lab); c.set_xticks(range(2015, 2025, 3)); c.legend(frameon=False, fontsize=5.4, loc='upper left')
tidy(c); tag(c, 'c', -0.2); c.set_ylim(0, 280)
save(fig, 'Fig_results_economics')

# ---------------- R4 map of LCO24/7 ----------------
import geopandas as gpd
gj = gpd.read_file(GJ); gj['zone'] = gj['Name_1'].astype(str)
tiz = pd.read_csv(f'{RD}/islanded_by_zone.csv', index_col=0)
g95 = tg[tg.cfe_target.round(2) == 0.95].set_index('zone').lco_med
gj['isl'] = gj.zone.map(tiz.cost_gbp_per_mwh_median); gj['g95'] = gj.zone.map(g95)
fig, axs = plt.subplots(1, 2, figsize=(177*MM, 115*MM))
LEADER = {'Z1_2': (-0.16, 0.06), 'Z1_3': (0.0, 0.16), 'Z1_4': (-0.2, -0.06), 'Z1_1': (0.12, 0.0)}  # label offsets, fraction of map width
for ax_, col, ttl, cmap, vr in ((axs[0], 'isl', 'a   Islanded, 100% CFE (median of 25 years)', 'OrRd', (170, 310)),
                                (axs[1], 'g95', 'b   Grid-connected, 95% CFE (median of 10 years)', 'Blues', (75, 135))):
    gj[gj[col].isna()].plot(ax=ax_, color='#f0f1f3', edgecolor='white', lw=0.3)
    gj[gj[col].notna()].plot(ax=ax_, column=col, cmap=cmap, vmin=vr[0], vmax=vr[1], edgecolor='white', lw=0.4,
                            legend=True, legend_kwds=dict(shrink=0.55, label='LCO24/7, £/MWh'))
    x0, x1 = ax_.get_xlim()
    for _, r in gj[gj[col].notna()].iterrows():
        # label each zone on its largest polygon so island fragments do not pull labels off the mainland
        geom = max(getattr(r.geometry, 'geoms', [r.geometry]), key=lambda g: g.area)
        p = geom.representative_point(); txt = f"{r.zone}\n{r[col]:.0f}"
        if r.zone in LEADER:  # small or crowded Highland zones: label outside with a leader line
            dx, dy = LEADER[r.zone]; w = x1 - x0
            ax_.annotate(txt, (p.x, p.y), xytext=(p.x + dx * w, p.y + dy * w), fontsize=4.2, ha='center', va='center', color=INK,
                         arrowprops=dict(arrowstyle='-', lw=0.3, color=Q, shrinkA=0, shrinkB=0))
        else:
            ax_.text(p.x, p.y, txt, fontsize=4.2, ha='center', va='center', color=INK)
    ax_.set_title(ttl, fontsize=7, color=INK, loc='left'); ax_.axis('off')
save(fig, 'Fig_results_map')

# ---------------- R5 environmental ----------------
em = pd.read_csv(f'{RD}/emissions_by_zone_case.csv'); em['case'] = np.where(em['mode'] == 'islanded', 'Islanded', 'Grid ' + (em.cfe_target * 100).round(0).astype(int).astype(str) + '%')
fig = plt.figure(figsize=(177*MM, 70*MM))
a = fig.add_axes([0.06, 0.16, 0.22, 0.74]); b = fig.add_axes([0.45, 0.16, 0.24, 0.74]); c = fig.add_axes([0.79, 0.16, 0.20, 0.74])
a.bar(gy.index, gy.grid_ci_g_per_kwh, color=GRD, width=0.7)
a.set_ylabel('GB grid carbon intensity, gCO$_2$/kWh\n(load-weighted, NESO)', **lab); a.set_xticks(range(2015, 2025, 3)); tidy(a); tag(a, 'a', -0.22)
a2 = a.twinx(); a2.plot(gy.index, gy.grid_cfe, color=TEAL, marker='o', ms=2.5, lw=1.2); a2.set_ylim(0, 1)
a2.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); a2.set_ylabel('Carbon-free share of grid supply', color=TEAL, fontsize=6.5); a2.spines['top'].set_visible(False)
order = ['Grid only', 'Grid 90%', 'Grid 95%', 'Grid 99%', 'Grid 100%', 'Islanded']
gonly = ge.groupby('zone').grid_ci_g_per_kwh.mean()
vals = {'Grid only': (gonly.median(), 0)}
for cs in order[1:]:
    s = em[em.case == cs].set_index('zone').loc[DIST]; vals[cs] = (s.g_per_kwh.median(), (s.import_t * 1000 / (s.total_t * 1000 / s.g_per_kwh)).median())
xx = np.arange(len(order))
tot = [vals[k][0] for k in order]; imp = [vals[k][1] for k in order]
b.bar(xx, np.subtract(tot, imp), 0.6, color=GREEN, label='PV and wind life-cycle'); b.bar(xx, imp, 0.6, bottom=np.subtract(tot, imp), color=GRD, label='Grid imports')
b.bar([0], [tot[0]], 0.6, color=GRD)
for i, v in enumerate(tot): b.text(i, v + 4, f'{v:.0f}', ha='center', fontsize=5.6, color=INK)
b.set_xticks(xx); b.set_xticklabels(order, fontsize=5.6, rotation=30, ha='right'); b.set_ylabel('gCO$_2$e per kWh of data-centre load', **lab)
b.legend(frameon=False, fontsize=5.6, loc='upper right'); tidy(b); tag(b, 'b', -0.22)
sgs = pd.read_csv(FL + '/stress_grid_main.csv'); sgs = sgs[sgs.design_year != sgs.test_year]
si = pd.read_csv(FL + '/stress_main.csv'); si = si[(si.design_year.astype(str) != 'all')]; si = si[si.design_year.astype(int) != si.test_year]
data = [gy.grid_cfe.values] + [sgs[sgs.cfe_target.round(2) == t].cfe.values for t in (0.9, 0.95, 0.99, 1.0)] + [si.cfe.values]
bp = c.boxplot(data, positions=xx, widths=0.55, whis=(5, 95), showfliers=False, patch_artist=True, medianprops=dict(color=INK, lw=1),
               boxprops=dict(lw=0.5), whiskerprops=dict(lw=0.5), capprops=dict(lw=0.5))
for bb, cl in zip(bp['boxes'], [GRD] + [TGT[t] for t in (0.9, 0.95, 0.99, 1.0)] + ['#e8c9bf']): bb.set_facecolor(cl)
c.plot(xx[1:5], [0.9, 0.95, 0.99, 1.0], '_', color=WARM, ms=9, mew=1.4, label='design target')
c.set_xticks(xx); c.set_xticklabels(order, fontsize=5.6, rotation=30, ha='right'); c.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
c.set_ylabel('Hourly CFE achieved\n(grid only: by year; designs: other weather years)', **lab); c.set_ylim(0.3, 1.02); c.legend(frameon=False, fontsize=5.6, loc='lower right'); tidy(c); tag(c, 'c', -0.3)
save(fig, 'Fig_results_environment')

# ---------------- R6 sensitivity ----------------
s = pd.read_csv(f'{FL}/stress_main.csv'); s = s[s.design_year.astype(str) != 'all']; s['dy'] = s.design_year.astype(int)
st = pd.read_csv(f'{RD}/stress_islanded_by_zone.csv', index_col=0).loc[DIST]
rv = pd.read_csv(f'{RD}/robust_vs_single.csv', index_col=0).loc[DIST]; rh = pd.read_csv(f'{RD}/robust_hourly_check.csv', index_col=0).loc[DIST]
fig = plt.figure(figsize=(177*MM, 175*MM))
a = fig.add_axes([0.07, 0.56, 0.36, 0.39]); cb = fig.add_axes([0.44, 0.56, 0.012, 0.39])
b = fig.add_axes([0.60, 0.56, 0.33, 0.39]); c = fig.add_axes([0.07, 0.07, 0.40, 0.36]); e = fig.add_axes([0.57, 0.07, 0.41, 0.36])
M = s[s.zone == 'Z10'].pivot(index='dy', columns='test_year', values='unserved_frac') * 100
im_ = a.imshow(M.values, origin='lower', cmap='Reds', vmin=0, vmax=2, aspect='auto', extent=[1999.5, 2024.5, 1999.5, 2024.5])
a.set_xlabel('Test (operating) year', **lab); a.set_ylabel('Design year', **lab); a.set_title('Z10 islanded: unserved load, % of annual load', fontsize=6.8, loc='left', color=INK)
fig.colorbar(im_, cax=cb, extend='max'); cb.tick_params(labelsize=5.5); cb.set_ylabel('Unserved, % of annual load', fontsize=6, color=Q); tag(a, 'a', -0.12)
b.bar(x, st.share_years_short, 0.6, color='#e8c9bf', label='Share of other years with any shortfall')
b.set_ylim(0, 1); b.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0)); b.set_ylabel('Share of (design, test) pairs', **lab)
b2 = b.twinx(); b2.plot(x, st.unserved_h_med, 'o', color=WARM, ms=3, label='Median shortfall hours'); b2.plot(x, st.unserved_h_p95, '^', color=INK, ms=3, label='95th pct shortfall hours')
b2.set_ylabel('Hours with shortfall per year', **lab); b2.spines['top'].set_visible(False); b2.set_ylim(0, 800)
b.set_xticks(x); b.set_xticklabels(DIST, fontsize=5.4, rotation=90); b.set_xlim(-0.6, len(DIST) - 0.4); tidy(b)
h1, l1 = b.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels(); b.legend(h1 + h2, l1 + l2, frameon=False, fontsize=5.4, loc='upper left'); tag(b, 'b', -0.1)
c.plot(x, rv.single_median_lco, 'o', color=DARK, ms=3.3, label='Single-year design, median')
c.plot(x, rv.single_max_lco, 'v', color=WARM, ms=3.3, label='Single-year design, costliest year')
c.plot(x, rv.robust_lco, 'D', color=TEAL, ms=3.3, label='Robust 25-year design (3 h)')
for i, z in enumerate(DIST):
    c.plot([i, i], [rv.single_median_lco[z], rv.robust_lco[z]], color=GRID, lw=1.5, zorder=0)
    c.text(i, 15, f"{rh.unserved_h[z]:.0f} h", ha='center', fontsize=4.8, color=TEAL, rotation=90)
c.set_xticks(x); c.set_xticklabels(DIST, fontsize=5.4, rotation=90); c.set_xlim(-0.6, len(DIST) - 0.4); c.set_ylim(0, 520)
c.set_ylabel('LCO24/7, £/MWh (islanded)', **lab); c.legend(frameon=False, fontsize=5.4, loc='upper left', ncol=2)
c.text(0.99, 0.13, 'green labels: shortfall hours in the hourly check (25 years in total)', transform=c.transAxes, ha='right', fontsize=5, color=TEAL); tidy(c); tag(c, 'c', -0.1)
a30 = pd.read_csv(f'{RD}/adder_adder30.csv'); a70 = pd.read_csv(f'{RD}/adder_adder70.csv')
tt = np.array([0.9, 0.95, 0.99, 1.0]); xs = np.arange(4)
e.bar(xs - 0.18, a30.d_lco_med, 0.36, color=LIGHT, label='Adder £30 (all 20 zones)')
e.bar(xs + 0.18, a70.set_index('cfe_target').reindex(tt).d_lco_med, 0.36, color=COOL, label='Adder £70 (partial: Z10, Z11)')
e.plot(xs - 0.18, -20 * (1 - tt), '_', color=WARM, ms=10, mew=1.3, label='±£20 × (1 − target)')
e.plot(xs + 0.18, 20 * (1 - tt), '_', color=WARM, ms=10, mew=1.3)
e.axhline(0, color=INK, lw=0.5); e.set_xticks(xs); e.set_xticklabels([f'Grid {t:.0%}' for t in tt], fontsize=6)
e.set_ylabel('Change in LCO24/7 vs £50, £/MWh', **lab); e.legend(frameon=False, fontsize=5.4, loc='upper right'); e.set_ylim(-3, 3); tidy(e); tag(e, 'd', -0.1)
save(fig, 'Fig_results_sensitivity')
print('done')
