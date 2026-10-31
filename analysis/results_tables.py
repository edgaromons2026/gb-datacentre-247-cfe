"""Results tables for the flagship paper from the run outputs (no re-solving).
Usage: python results_tables.py FLAGSHIP_DIR CV1_DIR NESO_FUEL_CSV ZONES_SUMMARY OUT_DIR
FLAGSHIP_DIR: design_*.csv, stress_*.csv, robust_main.csv. CV1_DIR: load/ and the MIP file. NESO_FUEL_CSV: df_fuel_ckan.
Life-cycle factors (gCO2e/kWh, IPCC AR5 WGIII Annex III medians, Schloemer et al. 2014): utility PV 48, onshore wind 11.
Batteries and hydrogen equipment are not included in the life-cycle figure."""
import sys, numpy as np, pandas as pd
FL, CV1, NESO, ZS, OUT = sys.argv[1:6]
LCA_PV, LCA_WIND = 48.0, 11.0
ADDER = 50.0
SAME_LOAD = {'Z2': 'Z1_1', 'Z1_3': 'Z1_2', 'Z1_4': 'Z1_2', 'Z9': 'Z8', 'Z16': 'Z14', 'Z17': 'Z13', 'Z4': 'Z3'}
ORDER = ['Z1_1', 'Z1_2', 'Z1_3', 'Z1_4', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9', 'Z10', 'Z11', 'Z12', 'Z13', 'Z14', 'Z15', 'Z16', 'Z17']
zs = pd.read_csv(ZS).set_index('zone')
site_of = {z: zs.loc[SAME_LOAD.get(z, z), 'solar_site'] for z in ORDER}

d = pd.read_csv(f'{FL}/design_main.csv')
d['pv'] = d.pv_fixed + d.pv_tracking
d['gen'] = d.pv_mwh + d.wind_mwh
d['avail'] = d.gen / (1 - d.curtailment_frac)
d['pv_cf_real'] = d.pv_mwh / (d.pv * d.hours)
d['wind_cf_real'] = d.wind_mwh / (d.wind * d.hours)
for k in ('pv_mwh', 'wind_mwh', 'import_mwh', 'export_mwh', 'avail'): d[k + '_per_load'] = d[k] / d.load_mwh
# embodied emissions follow what the plant can generate, so curtailed output is counted too: scale the delivered
# PV and wind energy up by available / delivered (per design; curtailment is not split by technology in the outputs)
d['lca_t'] = (d.pv_mwh * LCA_PV + d.wind_mwh * LCA_WIND) * (d.avail / d.gen) / 1000  # tCO2e per year
d.to_csv(f'{OUT}/designs_enriched.csv', index=False)

isl = d[d['mode'] == 'islanded']
q = lambda s: s.quantile(0.5)
cols = dict(pv_fixed=q, pv_tracking=q, pv=q, wind=q, bat_e=q, bat_p=q, electrolyser=q, h2_store=q, fuel_cell=q,
            cost_gbp_per_mwh=['median', 'min', 'max'], curtailment_frac=q, pv_mwh_per_load=q, wind_mwh_per_load=q,
            avail_per_load=q, pv_cf_real=q, wind_cf_real=q, load_mwh=q)
ti = isl.groupby('zone').agg(cols); ti.columns = ['_'.join(c) if c[1] not in ('<lambda>', '<lambda_0>') else c[0] for c in ti.columns]
ti['h2_years'] = isl.groupby('zone').h2_store.apply(lambda s: int((s > 1).sum()))
ti = ti.reindex(ORDER); ti.to_csv(f'{OUT}/islanded_by_zone.csv')

gr = d[d['mode'] == 'grid']
tg = gr.groupby(['zone', 'cfe_target']).agg(pv=('pv', 'median'), wind=('wind', 'median'), bat_e=('bat_e', 'median'),
        bat_p=('bat_p', 'median'), h2_store=('h2_store', 'median'), grid_conn=('grid_conn', 'median'),
        lco_med=('cost_gbp_per_mwh', 'median'), lco_min=('cost_gbp_per_mwh', 'min'), lco_max=('cost_gbp_per_mwh', 'max'),
        imp=('import_mwh_per_load', 'median'), exp=('export_mwh_per_load', 'median'), pv_share=('pv_mwh_per_load', 'median'),
        wind_share=('wind_mwh_per_load', 'median'), curt=('curtailment_frac', 'median')).reset_index()
tg.to_csv(f'{OUT}/grid_by_zone_target.csv', index=False)

# grid equivalent: the whole load bought from the grid, hourly, 2015-2024
mip = pd.read_csv(f'{CV1}/mip_hourly_utc_gbp_per_mwh_2015_2025.csv', index_col=0); mip.index = pd.to_datetime(mip.index, utc=True)
mip = mip.iloc[:, 0].interpolate(limit=24)
n = pd.read_csv(NESO, usecols=['DATETIME', 'CARBON_INTENSITY', 'NUCLEAR', 'WIND', 'WIND_EMB', 'HYDRO', 'SOLAR', 'GENERATION'])
n.index = pd.to_datetime(n.DATETIME, utc=True)
n['g'] = (n[['NUCLEAR', 'WIND', 'WIND_EMB', 'HYDRO', 'SOLAR']].sum(axis=1) / n.GENERATION).clip(0, 1)
nh = n[['CARBON_INTENSITY', 'g']].groupby(n.index.floor('h') + pd.Timedelta(hours=1)).mean()
rows = []
for z in ORDER:
    ld = pd.read_csv(f'{CV1}/load/{site_of[z]}_load_kw_2000_2025.csv', index_col=0); ld.index = pd.to_datetime(ld.index, utc=True)
    L = ld['load_kw'] / 1000.0
    for y in range(2015, 2025):
        l = L[L.index.year == y]; p = mip.reindex(l.index); c = nh.CARBON_INTENSITY.reindex(l.index); g = nh.g.reindex(l.index)
        ok = p.notna(); okc = c.notna()
        rows.append(dict(zone=z, year=y, load_mwh=l.sum(), grid_cost_gbp_per_mwh=float((l[ok] * (p[ok] + ADDER)).sum() / l[ok].sum()),
                         wholesale_gbp_per_mwh=float((l[ok] * p[ok]).sum() / l[ok].sum()),
                         grid_ci_g_per_kwh=float((l[okc] * c[okc]).sum() / l[okc].sum()),
                         grid_tco2=float((l[okc] * c[okc]).sum() / 1000 * l.sum() / l[okc].sum()),
                         grid_cfe=float((l[okc] * g[okc]).sum() / l[okc].sum())))
ge = pd.DataFrame(rows); ge.to_csv(f'{OUT}/grid_equivalent_by_zone_year.csv', index=False)
ann = ge[ge.zone == 'Z10'][['year', 'wholesale_gbp_per_mwh', 'grid_cost_gbp_per_mwh', 'grid_ci_g_per_kwh', 'grid_cfe']]
ann.to_csv(f'{OUT}/grid_by_year_Z10.csv', index=False)

# emissions of HRES designs: life-cycle of PV and wind output + imports at the design year's load-weighted grid intensity
gm = ge.set_index(['zone', 'year']).grid_ci_g_per_kwh
d2 = d.copy()
d2['ci_year'] = [gm.get((z, int(y)), np.nan) if m == 'grid' else np.nan for z, y, m in zip(d2.zone, d2.design_year, d2['mode'])]
d2['import_t'] = d2.import_mwh * d2.ci_year.fillna(0) / 1000
d2['total_t'] = d2.lca_t + d2.import_t
d2['g_per_kwh_load'] = d2.total_t * 1000 / d2.load_mwh
em = d2.groupby(['zone', 'mode', 'cfe_target']).agg(lca_t=('lca_t', 'median'), import_t=('import_t', 'median'),
        total_t=('total_t', 'median'), g_per_kwh=('g_per_kwh_load', 'median')).reset_index()
em.to_csv(f'{OUT}/emissions_by_zone_case.csv', index=False)

# stress tests
s = pd.read_csv(f'{FL}/stress_main.csv'); s['design_year'] = s.design_year.astype(str)
si = s[s.design_year != 'all'].copy(); si['dy'] = si.design_year.astype(int)
off = si[si.dy != si.test_year]
st = off.groupby('zone').agg(share_years_short=('unserved_mwh', lambda x: (x > 1e-3).mean()), cfe_med=('cfe', 'median'),
                             cfe_p05=('cfe', lambda x: x.quantile(0.05)), cfe_min=('cfe', 'min'),
                             unserved_h_med=('unserved_hours', 'median'), unserved_h_p95=('unserved_hours', lambda x: x.quantile(0.95)),
                             peak_short_mw=('unserved_max_mw', 'max')).reindex(ORDER)
# best single design year per zone: fewest test years with shortfall, then lowest cost
dyr = si.groupby(['zone', 'dy']).agg(n_short=('unserved_mwh', lambda x: int((x > 1e-3).sum())), worst_cfe=('cfe', 'min')).reset_index()
st['best_design_year'] = [dyr[dyr.zone == z].sort_values(['n_short', 'worst_cfe'], ascending=[True, False]).dy.iloc[0] for z in st.index]
st['best_n_short'] = [dyr[dyr.zone == z].n_short.min() for z in st.index]
st.to_csv(f'{OUT}/stress_islanded_by_zone.csv'); dyr.to_csv(f'{OUT}/stress_islanded_by_design_year.csv', index=False)
rb = s[s.design_year == 'all'].groupby('zone').agg(cfe_min=('cfe', 'min'), unserved_mwh=('unserved_mwh', 'sum'),
        unserved_h=('unserved_hours', 'sum'), years_short=('unserved_mwh', lambda x: int((x > 1e-3).sum())),
        peak_short_mw=('unserved_max_mw', 'max')).reindex(ORDER)
rb.to_csv(f'{OUT}/robust_hourly_check.csv')
sg = pd.read_csv(f'{FL}/stress_grid_main.csv')
sgo = sg[sg.design_year != sg.test_year]
sgs = sgo.groupby(['zone', 'cfe_target']).agg(cfe_med=('cfe', 'median'), cfe_min=('cfe', 'min'),
        share_below=('cfe_shortfall', lambda x: (x > 1e-4).mean()), short_med=('cfe_shortfall', 'median'),
        short_max=('cfe_shortfall', 'max'), cost_med=('cost_gbp_per_mwh', 'median')).reset_index()
sgs.to_csv(f'{OUT}/stress_grid_by_zone_target.csv', index=False)

# robust design vs single-year designs
r = pd.read_csv(f'{FL}/robust_main.csv').set_index('zone').reindex(ORDER)
r['pv'] = r.pv_fixed + r.pv_tracking
cmp = pd.DataFrame({'robust_lco': r.cost_gbp_per_mwh, 'single_median_lco': ti.cost_gbp_per_mwh_median,
                    'single_max_lco': ti.cost_gbp_per_mwh_max, 'robust_pv': r.pv, 'robust_wind': r.wind, 'robust_bat_e': r.bat_e,
                    'robust_h2_store': r.h2_store, 'robust_electrolyser': r.electrolyser, 'robust_fuel_cell': r.fuel_cell,
                    'robust_curtail': r.curtailment_frac})
cmp.to_csv(f'{OUT}/robust_vs_single.csv')

# adder
key = ['zone', 'cfe_target', 'design_year']
base = gr[key + ['cost_gbp_per_mwh', 'pv', 'wind', 'bat_e']]
for tag in ('adder30', 'adder70'):
    a = pd.read_csv(f'{FL}/design_{tag}.csv'); a['pv'] = a.pv_fixed + a.pv_tracking
    j = base.merge(a[key + ['cost_gbp_per_mwh', 'pv', 'wind', 'bat_e']], on=key, suffixes=('', '_a'))
    j['d_lco'] = j.cost_gbp_per_mwh_a - j.cost_gbp_per_mwh
    for c in ('pv', 'wind', 'bat_e'): j[f'd_{c}'] = j[f'{c}_a'] - j[c]
    j.groupby('cfe_target').agg(n=('d_lco', 'size'), zones=('zone', 'nunique'), d_lco_med=('d_lco', 'median'),
          d_lco_min=('d_lco', 'min'), d_lco_max=('d_lco', 'max'), d_pv_maxabs=('d_pv', lambda x: x.abs().max()),
          d_wind_maxabs=('d_wind', lambda x: x.abs().max()), d_bat_maxabs=('d_bat_e', lambda x: x.abs().max())).to_csv(f'{OUT}/adder_{tag}.csv')

# wind loss 1.0 vs 0.86, Z10
nl = pd.read_csv(f'{FL}/design_main_noloss.csv'); nl['pv'] = nl.pv_fixed + nl.pv_tracking
k2 = ['zone', 'mode', 'cfe_target', 'design_year']
w = d[d.zone == 'Z10'][k2 + ['cost_gbp_per_mwh', 'pv', 'wind', 'bat_e', 'h2_store']].merge(
    nl[k2 + ['cost_gbp_per_mwh', 'pv', 'wind', 'bat_e', 'h2_store']], on=k2, suffixes=('_086', '_100'))
w.to_csv(f'{OUT}/windloss_Z10.csv', index=False)
print(ti[['pv', 'wind', 'bat_e', 'h2_store', 'cost_gbp_per_mwh_median', 'cost_gbp_per_mwh_min', 'cost_gbp_per_mwh_max', 'curtailment_frac', 'h2_years']].round(1).to_string())
