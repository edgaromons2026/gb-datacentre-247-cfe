"""Flagship runs: least-cost 24/7 carbon-free supply for a data centre in each GB zone.

Needs the corrected_v1 outputs from run_corrected.py (pv/, wind/, load/, sites, MIP, costs) and,
if present, land/land_caps_25km_by_gsp.csv. Writes to corrected_v1/flagship/.

Examples (Anaconda prompt, gbtea env):
    python run_flagship.py --drive-root "G:/My Drive" --zones Z10 --years 2010 --targets 1.0      # smoke test
    python run_flagship.py --drive-root "G:/My Drive"                                             # A: all zones, all years
    python run_flagship.py --drive-root "G:/My Drive" --experiments stress robust --zones Z10 Z1_2
"""
import argparse
import os
import sys
import time
from pathlib import Path

EXPERIMENTS = ["design", "stress", "robust"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--experiments", nargs="+", default=["design"], choices=EXPERIMENTS)
    ap.add_argument("--zones", nargs="+", default=None, help="default: every zone")
    ap.add_argument("--years", nargs="+", type=int, default=None, help="design years (default 2000-2024)")
    ap.add_argument("--years-file", default=None,
                    help="CSV with columns zone,years ('2001 2006 2021'): per-zone design years, overriding --years")
    ap.add_argument("--targets", nargs="+", type=float, default=[0.9, 0.95, 0.99, 1.0],
                    help="CFE targets for the grid-connected case (islanded is always 1.0)")
    ap.add_argument("--modes", nargs="+", default=["islanded", "grid"], choices=["islanded", "grid"])
    ap.add_argument("--it-mw", type=float, default=5.0, help="IT load of the data centre, MW")
    ap.add_argument("--cost-year", type=int, default=2025)
    ap.add_argument("--no-h2", action="store_true")
    ap.add_argument("--grid-cfe", default=None, help="CSV of hourly carbon-free grid share (0-1); default 0")
    ap.add_argument("--agg-hours", type=int, default=3, help="time step for the robust multi-year design")
    ap.add_argument("--wind-loss", type=float, default=None,
                    help="factor on the gross wind CF (default config.WIND_LOSS_FACTOR)")
    ap.add_argument("--grid-adder", type=float, default=None,
                    help="GBP/MWh on grid imports on top of MIP (default config.GRID_ADDER_GBP_PER_MWH)")
    ap.add_argument("--solver", default="highs", choices=["highs", "gurobi"])
    ap.add_argument("--tag", default="", help="suffix for output file names")
    args = ap.parse_args()

    os.environ["GBTEA_DRIVE_ROOT"] = str(Path(args.drive_root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pandas as pd
    from gbtea import config as C, flagship as F, optimise as O

    out = C.OUT / "flagship"
    out.mkdir(parents=True, exist_ok=True)
    sites = pd.read_csv(C.OUT / "sites_with_altitude.csv")
    zones = F.zone_sites(sites)
    if args.zones:
        zones = zones.set_index("zone").loc[[z for z in dict.fromkeys(args.zones) if z in set(zones.zone)]].reset_index()
        # (kept in the order given; the first zone of each identical-weather group is the one solved)
    costs = pd.read_csv(C.OUT / "costs_gbp2024_2025_2050.csv")
    unit = O.unit_costs(costs[costs.year == args.cost_year])
    tag = f"_{args.tag}" if args.tag else ""
    wind_loss = C.WIND_LOSS_FACTOR if args.wind_loss is None else args.wind_loss
    groups = F.weather_groups(sites, list(zones.zone))
    zones = zones[zones.zone.isin(groups)]
    print(f"Wind loss factor {wind_loss}. {len(groups)} distinct weather sets; copies:",
          {k: v for k, v in groups.items() if v})
    print("Annualised GBP per MW(h)-yr:", {k: round(v) for k, v in unit[0].items()}, "\nEfficiencies:", unit[1])

    zone_years = {}
    if args.years_file:
        zy = pd.read_csv(args.years_file)
        zone_years = {r.zone: [int(v) for v in str(r.years).split()] for r in zy.itertuples()}
        print("Per-zone design years:", zone_years)
    results = {e: [] for e in EXPERIMENTS}
    for _, z in zones.iterrows():
        t0 = time.time()
        ts = F.zone_series(z, args.it_mw, grid_cfe_path=args.grid_cfe, wind_loss=wind_loss)
        tagz = dict(zone=z.zone, mode=None, it_mw=args.it_mw, wind_loss=wind_loss, weather_of=z.zone)
        n_before = {e: len(f) for e, f in results.items()}
        solar_cap, wind_cap = F.land_caps(z.zone)
        print(f"\n=== {z.zone}: solar {z.solar_site}, wind {z.wind_site}; land caps {solar_cap:.0f}/{wind_cap:.0f} MW")
        for mode in args.modes:
            grid = mode == "grid"
            yrs = zone_years.get(z.zone) or args.years or (F.PRICE_YEARS if grid else F.FULL_YEARS)
            if grid:
                yrs = [y for y in yrs if y in F.PRICE_YEARS]
            for target in (args.targets if grid else [1.0]):
                p = O.Params(cfe_target=target, grid=grid, solar_cap_mw=solar_cap, wind_cap_mw=wind_cap,
                             allow_h2=not args.no_h2, solver=args.solver,
                             **({} if args.grid_adder is None else {"grid_adder_gbp_mwh": args.grid_adder}))
                label = f"{z.zone}|{mode}|{target}"
                d = None
                if "design" in args.experiments or "stress" in args.experiments:
                    # appended to design_<tag>.csv row by row; finished rows are skipped on a rerun
                    d = F.design_years(ts, unit, p, yrs, label, extra=dict(tagz, mode=mode),
                                       out_csv=out / f"design{tag}.csv")
                if "robust" in args.experiments:
                    # appended to robust_<tag>.csv as soon as solved; skipped on a rerun
                    r = F.robust_saved(ts, unit, p, yrs, args.agg_hours, label, dict(tagz, mode=mode),
                                       out / f"robust{tag}.csv")
                    d = r if d is None else pd.concat([d, r], ignore_index=True)
                if "stress" in args.experiments and d is not None:
                    results["stress"].append(F.stress_test(ts, unit, p, d, yrs, label).assign(
                        zone=z.zone, mode=mode, wind_loss=wind_loss, weather_of=z.zone))
        for dup in groups[z.zone]:  # zones with identical weather get copies, marked weather_of
            n = F.copy_designs(out / f"design{tag}.csv", z.zone, dup) if (out / f"design{tag}.csv").exists() else 0
            n += F.copy_rows(out / f"robust{tag}.csv", z.zone, dup, F.robust_key, F.ROBUST_COLS)
            for e, frames in results.items():
                frames += [f.assign(zone=dup) for f in frames[n_before[e]:]]
            print(f"{dup}: copied from {z.zone} ({n} design rows)")
        print(f"{z.zone} done in {(time.time() - t0) / 60:.1f} min")
        for e, frames in results.items():  # stress/robust saved after every zone (design is saved per LP)
            if frames:
                pd.concat(frames, ignore_index=True).to_csv(out / f"{e}{tag}.csv", index=False)
    print("Outputs in", out)


if __name__ == "__main__":
    main()
