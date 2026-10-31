"""Run run_flagship.py or run_stress.py with one input changed, without editing gbtea or the run scripts.

    python sens/run_sens.py flagship [--rate 0.03] [--cf-bias FILE] -- <run_flagship.py args>
    python sens/run_sens.py stress   [same options]                             -- <run_stress.py args>

--rate     real discount rate for every asset (central 0.07, config.DISCOUNT_RATE)
--cf-bias  CSV of monthly multipliers (columns month, pv_fixed, pv_single_axis, wind) applied to the hourly
           capacity factors, e.g. MIDAS/ERA5 ratios from the validation; results are clipped to 0-1
Use a distinct --tag for each case so central outputs are never touched."""
import functools
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CV1 = HERE.parent  # corrected_v1


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("flagship", "stress") or "--" not in sys.argv:
        sys.exit(__doc__)
    which, rest = sys.argv[1], sys.argv[2:]
    cut = rest.index("--")
    own, passed = rest[:cut], rest[cut + 1:]
    opts = dict(zip(own[::2], own[1::2]))
    # config reads the data root when first imported, so set it before importing gbtea
    root = passed[passed.index("--drive-root") + 1]
    os.environ["GBTEA_DRIVE_ROOT"] = str(Path(root))
    sys.path.insert(0, str(CV1))
    import numpy as np
    import pandas as pd
    from gbtea import flagship as F, optimise as O

    if "--rate" in opts:
        rate = float(opts["--rate"])
        O.unit_costs = functools.partial(O.unit_costs, rate=rate)
        print(f"[sens] discount rate {rate}", flush=True)

    bias = pd.read_csv(opts["--cf-bias"]).set_index("month") if "--cf-bias" in opts else None
    if bias is not None:
        base = F.zone_series

        @functools.wraps(base)
        def zone_series(zone_row, *a, **k):
            ts = base(zone_row, *a, **k)
            m = ts.index.month
            for col, b in (("cf_fixed", "pv_fixed"), ("cf_tracking", "pv_single_axis"), ("cf_wind", "wind")):
                ts[col] = (ts[col] * bias[b].reindex(m).to_numpy()).clip(0, 1)
            print(f"[sens] {zone_row.solar_site}: monthly CF bias applied", flush=True)
            return ts
        F.zone_series = zone_series

    script = CV1 / ("run_flagship.py" if which == "flagship" else "run_stress.py")
    sys.argv = [str(script)] + passed
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
