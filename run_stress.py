"""Cross-year stress test of saved designs (no re-solving of designs).

Each saved design (from flagship/design_<from>.csv) is operated with its capacities fixed on every test
year with optimise.operate. Islanded: unmet load is allowed at VOLL and measured. Grid: the CFE
constraint is dropped and the achieved CFE is measured against the design target.
One row per (zone, [cfe_target,] design_year, test_year) is appended to the output as soon as it is
solved and rows already there are skipped. A locked file (Excel) parks rows in <name>.pending.csv
(see flagship._append_csv). Zones with identical weather are solved once and copied (weather_of).

    python run_stress.py --drive-root "G:/My Drive" --zones Z10 Z14 Z5 Z1_2          # islanded
    python run_stress.py --drive-root "G:/My Drive" --mode grid                      # all zones
Outputs: flagship/stress_<tag>.csv (islanded), flagship/stress_grid_<tag>.csv (grid).
"""
import argparse
import os
import sys
import time
from pathlib import Path

COLS = {"islanded": ["zone", "weather_of", "design_year", "test_year", "wind_loss", "cfe", "unserved_mwh",
                     "unserved_frac", "unserved_hours", "unserved_max_mw", "load_mwh", "objective_gbp"],
        "grid": ["zone", "weather_of", "cfe_target", "design_year", "test_year", "wind_loss", "grid_adder", "cfe",
                 "cfe_shortfall", "import_mwh", "export_mwh", "unserved_mwh", "unserved_frac", "load_mwh",
                 "objective_gbp", "cost_gbp_per_mwh"]}


def _dy(v):
    """design year as int, or 'all' for a multi-year robust design."""
    s = str(v)
    return int(float(s)) if s.replace(".", "", 1).isdigit() else s


def _key(r, mode):
    k = (str(r["zone"]), _dy(r["design_year"]), int(r["test_year"]))
    return k if mode == "islanded" else (k[0], round(float(r["cfe_target"]), 6)) + k[1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--mode", default="islanded", choices=["islanded", "grid"])
    ap.add_argument("--zones", nargs="+", default=None,
                    help="solved in this order, each completed before the next (default: every distinct zone)")
    ap.add_argument("--from-designs", default="design_main.csv", help="file in flagship/")
    ap.add_argument("--targets", nargs="+", type=float, default=[0.9, 0.95, 0.99, 1.0], help="grid mode only")
    ap.add_argument("--test-years", nargs="+", type=int, default=None,
                    help="default 2000-2024 islanded, 2015-2024 grid")
    ap.add_argument("--it-mw", type=float, default=5.0)
    ap.add_argument("--cost-year", type=int, default=2025)
    ap.add_argument("--solver", default="highs", choices=["highs", "gurobi"])
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()

    os.environ["GBTEA_DRIVE_ROOT"] = str(Path(args.drive_root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pandas as pd
    from gbtea import config as C, flagship as F, optimise as O

    grid = args.mode == "grid"
    cols = COLS[args.mode]
    test_years = args.test_years or (F.PRICE_YEARS if grid else F.FULL_YEARS)
    out = C.OUT / "flagship"
    dst = out / (f"stress_grid_{args.tag}.csv" if grid else f"stress_{args.tag}.csv")
    designs = pd.read_csv(out / args.from_designs)
    designs = designs[designs["mode"] == args.mode]
    sites = pd.read_csv(C.OUT / "sites_with_altitude.csv")
    zones = F.zone_sites(sites).set_index("zone")
    groups = F.weather_groups(sites, list(zones.index))
    order = [z for z in (args.zones or list(groups)) if z in groups]  # primaries only; copies follow
    costs = pd.read_csv(C.OUT / "costs_gbp2024_2025_2050.csv")
    ann, eff, vom = O.unit_costs(costs[costs.year == args.cost_year])
    print(f"{args.mode} stress, test years {test_years[0]}-{test_years[-1]}; zones {order}; copies "
          f"{ {k: v for k, v in groups.items() if v and k in order} }", flush=True)

    def existing():
        d = F.read_designs(dst) if dst.exists() or F._pending(dst).exists() else pd.DataFrame(columns=cols)
        return d, {_key(r, args.mode) for _, r in d.iterrows()}

    for zone in order:
        dz = designs[designs.zone == zone]
        if grid:
            dz = dz[dz.cfe_target.round(6).isin([round(t, 6) for t in args.targets])]
        dz = dz.assign(_o=dz.design_year.astype(str)).sort_values(["cfe_target", "_o"]).drop(columns="_o")
        if dz.empty:
            print(f"{zone}: no {args.mode} designs in {args.from_designs}, skipped")
            continue
        wind_loss = float(dz.wind_loss.iloc[0])
        ts = F.zone_series(zones.loc[zone], args.it_mw, wind_loss=wind_loss)
        _, done = existing()
        t0, n = time.time(), 0
        print(f"=== {zone}: {len(dz)} designs x {len(test_years)} test years, wind_loss {wind_loss}", flush=True)
        for _, d in dz.iterrows():
            p = O.Params(cfe_target=float(d.cfe_target), grid=grid, solver=args.solver,
                         allow_h2=pd.notna(d.get("h2_store")))  # designs run with --no-h2 have no H2 assets
            for y in test_years:
                row = dict(zone=zone, weather_of=zone, cfe_target=d.cfe_target, design_year=_dy(d.design_year),
                           test_year=y)
                if _key(row, args.mode) in done:
                    continue
                t1 = time.time()
                r = O.operate(F._clean(F.years(ts, [y]), grid), ann, eff, vom, p, d.to_dict())
                row.update(wind_loss=wind_loss, grid_adder=p.grid_adder_gbp_mwh, cfe=r["cfe"],
                           cfe_shortfall=max(0.0, float(d.cfe_target) - r["cfe"]), import_mwh=r["import_mwh"],
                           export_mwh=r["export_mwh"], unserved_mwh=r["unserved_mwh"],
                           unserved_frac=r["unserved_mwh"] / r["load_mwh"], unserved_hours=r["unserved_hours"],
                           unserved_max_mw=r["unserved_max_mw"], load_mwh=r["load_mwh"],
                           objective_gbp=r["objective_gbp"], cost_gbp_per_mwh=r["cost_gbp_per_mwh"])
                F._append_csv(dst, pd.DataFrame([row]).reindex(columns=cols))
                n += 1
                tgt = f" target {d.cfe_target:g}" if grid else ""
                print(f"  {zone}{tgt} design {_dy(d.design_year)} on {y}: CFE {r['cfe']:.4f}, unserved "
                      f"{row['unserved_frac']:.2%} ({r['unserved_hours']:.0f} h) [{time.time() - t1:.0f} s]", flush=True)
        print(f"{zone} done: {n} operate LPs in {(time.time() - t0) / 60:.1f} min", flush=True)
        for dup in groups[zone]:  # identical weather: copy rows, marked weather_of
            d_all, have = existing()
            new = d_all[d_all.zone == zone].copy()
            new["zone"], new["weather_of"] = dup, zone
            new = new[[_key(r, args.mode) not in have for _, r in new.iterrows()]]
            if len(new):
                F._append_csv(dst, new.reindex(columns=cols))
            print(f"{dup}: copied from {zone} ({len(new)} rows)", flush=True)
    print("Outputs in", dst)


if __name__ == "__main__":
    main()
