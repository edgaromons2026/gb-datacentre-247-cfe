"""Flagship model: least-cost 24/7 carbon-free supply for a data centre at one GB zone.

One linear programme per (zone, weather year(s), CFE target, grid mode). Units are MW, MWh and GBP.

Assets (all sized by the LP):
  pv_fixed, pv_tracking   share the zone's solar land cap (MW)
  wind (V126 profile)     limited by the zone's wind land cap (MW)
  battery                 energy (MWh) and inverter power (MW) sized separately
  hydrogen                electrolyser (MW_e), store (MWh_H2) and fuel cell (MW_e)
  grid (grid mode only)   import and export up to a connection size (MW), priced at MIP

Hourly CFE score (Riepin & Brown 2024 style, local supply is carbon free):
  CFE = 1 - sum_t imp_t * (1 - g_t) / sum_t load_t,  g_t = carbon-free share of grid power.
  The constraint is CFE >= target. Islanded mode has no grid, so the target is 1 by construction.

Modes:
  design(...)   sizes everything on the given hours (one year, or several stacked years)
  operate(...)  fixes the capacities of a design and dispatches another weather year; unmet
                load is allowed at a penalty so that the shortfall can be measured
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config as C
from . import costs as K

# PyPSA technology-data names used for each asset
TECH = {"pv_fixed": "solar-utility", "pv_tracking": "solar-utility single-axis tracking",
        "wind": "onwind", "bat_e": "battery storage", "bat_p": "battery inverter",
        "electrolyser": "electrolysis", "fuel_cell": "fuel cell",
        "h2_store": "hydrogen storage tank type 1 including compressor"}


@dataclass
class Params:
    cfe_target: float | None = 1.0
    grid: bool = False                     # False = islanded
    grid_adder_gbp_mwh: float = C.GRID_ADDER_GBP_PER_MWH
    grid_conn_gbp_kw_yr: float = C.GRID_CONNECTION_GBP_PER_KW_YR
    export: bool = True
    # Keep the model a supply design for the data centre, not a merchant generator (otherwise a
    # profitable wind site exports without limit and the LP is unbounded):
    grid_conn_max_x_peak: float = 1.0      # connection size <= this x peak load
    max_export_frac: float = 0.2           # annual exports <= this x annual load (Riepin & Brown 2024)
    voll_gbp_mwh: float = 10_000.0         # only used in operate()
    solar_cap_mw: float = np.inf
    wind_cap_mw: float = np.inf
    allow_h2: bool = True
    h2_store_tech: str = TECH["h2_store"]
    rate: float = C.DISCOUNT_RATE
    solver: str = "highs"
    solver_options: dict = field(default_factory=lambda: {"threads": C.SOLVER_THREADS, "log_to_console": False})


def unit_costs(cost_table, h2_store_tech=TECH["h2_store"], rate=C.DISCOUNT_RATE):
    """GBP per MW-yr (or MWh-yr) and efficiencies from costs_gbp2024_2025_2050.csv rows for one year."""
    t = K.tidy(cost_table)
    names = dict(TECH, h2_store=h2_store_tech)
    ann = {}
    for k, tech in names.items():
        row = t.loc[tech]
        inv, life = row["investment"], row["lifetime"]
        fom = row.get("FOM", 0.0)
        fom = 0.0 if pd.isna(fom) else fom
        ann[k] = 1000.0 * (inv * K.annuity(rate, life) + inv * fom / 100.0)  # per kW -> per MW
    eff = {"bat": float(t.loc[TECH["bat_p"], "efficiency"]),  # one way, inverter
           "electrolyser": float(t.loc[TECH["electrolyser"], "efficiency"]),
           "fuel_cell": float(t.loc[TECH["fuel_cell"], "efficiency"])}
    vom = {k: float(np.nan_to_num(t.loc[tech].get("VOM", 0.0))) for k, tech in names.items()}  # NaN -> 0
    return ann, eff, vom


def _model(ts, ann, eff, vom, p, fixed=None):
    """ts: DataFrame with load (MW), cf_fixed, cf_tracking, cf_wind and, in grid mode, price and g (0-1).
    ts.attrs["dt"] is the step length in hours (1 unless the series was aggregated)."""
    import linopy
    import xarray as xr

    m = linopy.Model()
    T = pd.RangeIndex(len(ts), name="t")
    dt = float(ts.attrs.get("dt", 1.0))
    n_years = len(ts) * dt / 8760.0

    def arr(col):
        return xr.DataArray(ts[col].to_numpy(dtype=float), coords=[T])

    load = arr("load")

    def cap(name, upper=np.inf):
        if fixed is not None:
            v = fixed[name]
            return m.add_variables(lower=v, upper=v, name=name)
        return m.add_variables(lower=0, upper=upper, name=name)

    c = {"pv_fixed": cap("pv_fixed"), "pv_tracking": cap("pv_tracking"),
         "wind": cap("wind", p.wind_cap_mw), "bat_e": cap("bat_e"), "bat_p": cap("bat_p")}
    if p.allow_h2:
        c.update(electrolyser=cap("electrolyser"), h2_store=cap("h2_store"), fuel_cell=cap("fuel_cell"))
    m.add_constraints(c["pv_fixed"] + c["pv_tracking"] <= p.solar_cap_mw, name="solar_land")

    def disp(name):
        return m.add_variables(lower=0, coords=[T], name=name)

    pvf, pvt, wd = disp("pvf"), disp("pvt"), disp("wd")
    m.add_constraints(pvf <= c["pv_fixed"] * arr("cf_fixed"), name="pvf_avail")
    m.add_constraints(pvt <= c["pv_tracking"] * arr("cf_tracking"), name="pvt_avail")
    m.add_constraints(wd <= c["wind"] * arr("cf_wind"), name="wind_avail")

    ch, dis, soc = disp("bat_ch"), disp("bat_dis"), disp("bat_soc")
    m.add_constraints(ch <= c["bat_p"], name="ch_max")
    m.add_constraints(dis <= c["bat_p"], name="dis_max")
    m.add_constraints(soc <= c["bat_e"], name="soc_max")
    e = eff["bat"]
    # cyclic state of charge: soc_t = soc_{t-1} + dt * (e*ch_t - dis_t/e)
    m.add_constraints(soc - soc.roll(t=1) - dt * e * ch + dt / e * dis == 0, name="soc_balance")

    supply = pvf + pvt + wd + dis
    demand_extra = ch
    if p.allow_h2:
        el, fc, h2 = disp("el"), disp("fc"), disp("h2_soc")
        m.add_constraints(el <= c["electrolyser"], name="el_max")
        m.add_constraints(fc <= c["fuel_cell"], name="fc_max")
        m.add_constraints(h2 <= c["h2_store"], name="h2_max")
        m.add_constraints(h2 - h2.roll(t=1) - dt * eff["electrolyser"] * el + dt / eff["fuel_cell"] * fc == 0,
                          name="h2_balance")
        supply = supply + fc
        demand_extra = demand_extra + el

    cost = sum(ann[k] * c[k] for k in c) * n_years
    cost = cost + dt * (vom["pv_fixed"] * pvf.sum() + vom["pv_tracking"] * pvt.sum() + vom["wind"] * wd.sum())

    if p.grid:
        conn = cap("grid_conn", p.grid_conn_max_x_peak * float(ts["load"].max()))
        imp, exp = disp("imp"), disp("exp")
        m.add_constraints(imp <= conn, name="imp_max")
        m.add_constraints(exp <= (conn if p.export else 0 * conn), name="exp_max")
        m.add_constraints(exp.sum() <= p.max_export_frac * float(load.sum()), name="exp_annual")
        price = arr("price")
        supply = supply + imp
        demand_extra = demand_extra + exp
        cost = cost + dt * (((price + p.grid_adder_gbp_mwh) * imp).sum() - (price * exp).sum())
        cost = cost + 1000.0 * p.grid_conn_gbp_kw_yr * conn * n_years
        if p.cfe_target is not None:
            dirty = (1.0 - arr("g")) * imp
            m.add_constraints(dirty.sum() <= (1.0 - p.cfe_target) * float(load.sum()), name="cfe")

    if fixed is not None:  # operate mode: allow shortfall at VOLL so the run is always feasible
        short = disp("unserved")
        supply = supply + short
        cost = cost + dt * p.voll_gbp_mwh * short.sum()

    m.add_constraints(supply - demand_extra >= load, name="balance")  # excess is curtailed
    m.add_objective(cost)
    return m


def _results(m, ts, ann, p):
    sol = {v: m.solution[v] for v in m.solution.data_vars}
    caps = {k: float(sol[k]) for k in ["pv_fixed", "pv_tracking", "wind", "bat_e", "bat_p",
                                       "electrolyser", "h2_store", "fuel_cell", "grid_conn"] if k in sol}
    dt = float(ts.attrs.get("dt", 1.0))
    E = float(ts["load"].sum()) * dt
    gen = {k: float(sol[k].sum()) * dt for k in ("pvf", "pvt", "wd")}
    avail = dt * float((caps["pv_fixed"] * ts.cf_fixed + caps["pv_tracking"] * ts.cf_tracking
                        + caps["wind"] * ts.cf_wind).sum())
    imp = sol["imp"].values * dt if "imp" in sol else np.zeros(len(ts))
    exp = float(sol["exp"].sum()) * dt if "exp" in sol else 0.0
    short = sol["unserved"].values if "unserved" in sol else np.zeros(len(ts))
    unserved = float(short.sum()) * dt
    g = ts["g"].values if "g" in ts else np.zeros(len(ts))
    cfe = 1.0 - (float(((1 - g) * imp).sum()) + unserved) / E
    out = dict(caps)
    out.update(objective_gbp=float(m.objective.value), load_mwh=E, cost_gbp_per_mwh=float(m.objective.value) / E,
               cfe=cfe, unserved_mwh=unserved, import_mwh=float(imp.sum()), export_mwh=exp,
               pv_mwh=gen["pvf"] + gen["pvt"], wind_mwh=gen["wd"],
               curtailment_frac=1.0 - (gen["pvf"] + gen["pvt"] + gen["wd"]) / avail if avail > 0 else 0.0,
               hours=len(ts) * dt,
               unserved_hours=float((short > 1e-6).sum()) * dt, unserved_max_mw=float(short.max()))
    return out


def _opts(p):
    """HiGHS options by default; Gurobi (free academic licence) is much faster on these LPs."""
    if p.solver == "highs":
        return p.solver_options
    if p.solver == "gurobi":
        return {"Method": 2, "Crossover": 0, "Threads": C.SOLVER_THREADS, "OutputFlag": 0}
    return {}


def design(ts, ann, eff, vom, p):
    m = _model(ts, ann, eff, vom, p)
    status, cond = m.solve(solver_name=p.solver, **_opts(p))
    if status != "ok":
        raise RuntimeError(f"design LP {status}/{cond}")
    return _results(m, ts, ann, p)


def operate(ts, ann, eff, vom, p, design_result):
    fixed = {k: design_result[k] for k in ["pv_fixed", "pv_tracking", "wind", "bat_e", "bat_p",
                                           "electrolyser", "h2_store", "fuel_cell", "grid_conn"]
             if k in design_result and pd.notna(design_result[k])}  # NaN = asset not in this design (e.g. no H2)
    q = Params(**{**p.__dict__, "cfe_target": None})  # measure CFE, do not force it
    m = _model(ts, ann, eff, vom, q, fixed=fixed)
    status, cond = m.solve(solver_name=p.solver, **_opts(p))
    if status != "ok":
        raise RuntimeError(f"operate LP {status}/{cond}")
    return _results(m, ts, ann, q)


def aggregate(ts, hours):
    """Average consecutive blocks of `hours`. Powers and CFs are means, so energy is kept
    when every energy term is multiplied by dt (done in _model)."""
    if hours <= 1:
        return ts
    out = ts.groupby(np.arange(len(ts)) // hours).mean()
    out.attrs["dt"] = float(hours)
    return out
