"""Techno-economic input tables for the write-up: per-asset cost parameters by cost year (GBP2024), annualised
costs as in optimise.unit_costs, discount-rate sensitivity, and Market Index Price statistics.
Usage: python techecon_tables.py COSTS.csv MIP.csv GBTEA_PARENT OUT_DIR"""
import sys, numpy as np, pandas as pd
COSTS, MIP, GB, OUT = sys.argv[1:5]
sys.path.insert(0, GB)
from gbtea import optimise as O, costs as K
TECH = dict(O.TECH)
d = pd.read_csv(COSTS)
rows = []
for y in sorted(d.year.unique()):
    t = K.tidy(d[d.year == y])
    src = d[d.year == y].set_index(['technology', 'parameter'])
    for k, tech in TECH.items():
        r = t.loc[tech]; get = lambda p: float(r[p]) if p in r and pd.notna(r[p]) else np.nan
        inv, life, fom = get('investment'), get('lifetime'), get('FOM')
        fom0 = 0.0 if np.isnan(fom) else fom
        cy = src.loc[(tech, 'investment'), 'currency_year'] if (tech, 'investment') in src.index else np.nan
        raw = src.loc[(tech, 'investment'), 'value'] if (tech, 'investment') in src.index else np.nan
        unit = src.loc[(tech, 'investment'), 'unit'] if (tech, 'investment') in src.index else ''
        rows.append(dict(cost_year=y, asset=k, technology=tech, investment_raw=raw, unit_raw=unit, currency_year=cy,
                         investment_gbp2024=inv, lifetime=life, fom_pct=fom, vom_gbp_mwh=get('VOM'), efficiency=get('efficiency'),
                         annuity=K.annuity(0.07, life), annualised_gbp_per_unit_yr=1000*(inv*K.annuity(0.07, life) + inv*fom0/100),
                         source=str(src.loc[(tech, 'investment'), 'source']) if (tech, 'investment') in src.index else ''))
T = pd.DataFrame(rows); T.to_csv(f'{OUT}/technology_costs_by_year.csv', index=False)
print(T[T.cost_year == 2025].drop(columns=['source', 'technology']).round(3).to_string())
print(T.pivot(index='asset', columns='cost_year', values='annualised_gbp_per_unit_yr').round(0).to_string())
# discount-rate sensitivity (2025 costs)
t = K.tidy(d[d.year == 2025]); S = []
for r in (0.03, 0.05, 0.07, 0.10):
    ann, _, _ = O.unit_costs(d[d.year == 2025], rate=r); S.append(dict(rate=r, **ann))
S = pd.DataFrame(S); S.to_csv(f'{OUT}/annualised_vs_discount_rate.csv', index=False); print(S.round(0).to_string())
# MIP
m = pd.read_csv(MIP, index_col=0); m.index = pd.to_datetime(m.index, utc=True); p = m.iloc[:, 0]
print('MIP span', p.index.min(), p.index.max(), 'n', len(p), 'nan', p.isna().sum(), 'col', m.columns.tolist())
st = p.groupby(p.index.year).agg(['count', 'mean', 'median', 'std', 'min', 'max', lambda x: (x < 0).sum(), lambda x: x.quantile(0.05), lambda x: x.quantile(0.95)])
st.columns = ['hours', 'mean', 'median', 'sd', 'min', 'max', 'neg_hours', 'p05', 'p95']
st.to_csv(f'{OUT}/mip_stats_by_year.csv'); print(st.round(1).to_string())
full = pd.date_range('2015-01-01', '2025-01-01', freq='h', tz='UTC', inclusive='left')
miss = p.reindex(full).isna(); print('missing hours 2015-2024', int(miss.sum()), miss.groupby(full.year).sum().to_dict())
gaps = (miss != miss.shift()).cumsum()[miss]; gl = gaps.value_counts(); print('gaps > 24 h:', int((gl > 24).sum()), 'hours in them', int(gl[gl > 24].sum()))
