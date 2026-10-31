"""Worked example of gbtea.optimise for the Methods write-up: one zone (Z10 Nottingham), one weather
year, islanded and grid-connected. Solves the same LP as the flagship runs (HiGHS) and saves the
hourly dispatch, the capacities and the cost breakdown. Does not write to the flagship outputs.
Usage: GBTEA_DRIVE_ROOT=<root> python opt_worked_example.py GBTEA_PARENT OUT_DIR"""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); OUT = sys.argv[2]
from gbtea import config as C, flagship as F, optimise as O

sites = pd.read_csv(C.OUT / "sites_with_altitude.csv")
z = F.zone_sites(sites).set_index("zone").loc["Z10"]
ts = F.zone_series(z, 5.0)
costs = pd.read_csv(C.OUT / "costs_gbp2024_2025_2050.csv")
ann, eff, vom = O.unit_costs(costs[costs.year == 2025])
json.dump(dict(ann=ann, eff=eff, vom=vom), open(f"{OUT}/unit_costs_2025.json", "w"), indent=1)

for mode, year, target in (("islanded", 2018, 1.0), ("grid", 2018, 0.95)):
    p = O.Params(cfe_target=target, grid=mode == "grid")
    t = F._clean(F.years(ts, [year]), p.grid)
    m = O._model(t, ann, eff, vom, p)
    m.solve(solver_name="highs", **O._opts(p))
    r = O._results(m, t, ann, p)
    s = m.solution
    disp = pd.DataFrame({k: s[k].values for k in s.data_vars if s[k].dims == ("t",)},
                        index=F.years(ts, [year]).index[:len(t)])
    disp["load"] = t["load"].values
    for k in ("cf_fixed", "cf_tracking", "cf_wind"):
        disp[k] = t[k].values
    if p.grid:
        disp["price"] = t["price"].values
    caps = {k: r[k] for k in ann if k in r}
    br = {k: ann[k] * caps[k] for k in caps}
    br["vom"] = float(vom["pv_fixed"] * disp.pvf.sum() + vom["pv_tracking"] * disp.pvt.sum() + vom["wind"] * disp.wd.sum())
    if p.grid:
        br["grid_import"] = float(((disp.price + p.grid_adder_gbp_mwh) * disp.imp).sum())
        br["export_revenue"] = -float((disp.price * disp.exp).sum())
    r["breakdown_gbp"] = br
    r["n_vars"], r["n_cons"] = int(m.nvars), int(m.ncons)
    disp.to_pickle(f"{OUT}/dispatch_{mode}_{year}.pkl")
    json.dump(r, open(f"{OUT}/result_{mode}_{year}.json", "w"), indent=1, default=float)
    print(mode, year, {k: round(v, 2) if isinstance(v, float) else v for k, v in r.items() if k != "breakdown_gbp"})
    print("  breakdown £/MWh:", {k: round(v / r["load_mwh"], 1) for k, v in br.items()})
