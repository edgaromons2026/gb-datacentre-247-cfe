"""Pick each zone's hardest weather years for the critical-period robust design.

A year is hard if (i) its own single-year islanded design is expensive and (ii) other years' designs
leave the most load unserved when operated on it (islanded stress test). Years are ranked on each
criterion and the sum of ranks is used; the N best (lowest sums) are kept.
Writes flagship/crit_years_<N>.csv with columns zone, years ('2001 2006 2021 ...'), plus the scores.

    python pick_critical_years.py --drive-root "G:/My Drive" --n 5 4
"""
import argparse
import os
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--n", nargs="+", type=int, default=[5])
    args = ap.parse_args()
    os.environ["GBTEA_DRIVE_ROOT"] = str(Path(args.drive_root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pandas as pd
    from gbtea import config as C

    out = C.OUT / "flagship"
    d = pd.read_csv(out / "design_main.csv")
    d = d[(d["mode"] == "islanded") & (d.zone == d.weather_of)]
    s = pd.read_csv(out / "stress_main.csv")
    s = s[(s.zone == s.weather_of) & (s.design_year.astype(str) != "all")]
    s = s[s.design_year.astype(int) != s.test_year]
    for n in args.n:
        rows = []
        for zone, dz in d.groupby("zone"):
            cost = dz.set_index("design_year").cost_gbp_per_mwh
            short = s[s.zone == zone].groupby("test_year").unserved_frac.mean()
            t = pd.DataFrame({"cost": cost, "short": short}).dropna()
            t["score"] = t.cost.rank(ascending=False) + t["short"].rank(ascending=False)
            pick = t.sort_values(["score", "cost"], ascending=[True, False]).head(n)
            rows.append(dict(zone=zone, years=" ".join(str(int(y)) for y in sorted(pick.index)),
                             costs=" ".join(f"{c:.0f}" for c in pick.sort_index().cost),
                             mean_unserved_pct=" ".join(f"{100 * u:.2f}" for u in pick.sort_index()["short"])))
        f = out / f"crit_years_{n}.csv"
        pd.DataFrame(rows).to_csv(f, index=False)
        print(f"{f}:")
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
