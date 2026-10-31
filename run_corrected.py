"""Run the corrected GB solar, wind, price, cost and land inputs locally (no Colab).

Usage (from this folder, in an Anaconda prompt):
    pip install -r requirements.txt
    python run_corrected.py --drive-root "G:/My Drive"                      # steps 1-6
    python run_corrected.py --drive-root "G:/My Drive" --steps validation --max-stations 3
    python run_corrected.py --drive-root "G:/My Drive" --steps land        # needs glaes/GDAL

--drive-root is the folder that contains Energy_System_Modelling_GB and
techno_econs_analysis_green_hydrogen_uk (Google Drive for desktop shows it as "G:/My Drive",
or point it at a local copy of those two folders). Outputs go only to
<drive-root>/Energy_System_Modelling_GB/esm_GB_2025/corrected_v1/.
"""
import argparse
import os
import sys
import time
import warnings
from pathlib import Path

ALL_STEPS = ["prices", "costs", "sites", "profiles", "compare", "validation", "land"]
DEFAULT_STEPS = ["prices", "costs", "sites", "profiles", "compare", "validation"]
GIS_DIR = Path("D:/le")  # CORINE tif, GB boundary and OS Open Roads on this PC


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-root", required=True, help='e.g. "G:/My Drive"')
    ap.add_argument("--steps", nargs="+", default=DEFAULT_STEPS, choices=ALL_STEPS)
    ap.add_argument("--max-stations", type=int, default=None, help="validation on the first N stations only")
    ap.add_argument("--clc-tif", default=str(GIS_DIR / "Results/U2018_CLC2018_V2020_20u1/U2018_CLC2018_V2020_20u1/U2018_CLC2018_V2020_20u1.tif"))
    ap.add_argument("--gb-boundary", default=str(GIS_DIR / "GB_boundary_region_shapefile.shp"))
    ap.add_argument("--roads", default=str(GIS_DIR / "GB_RoadLink.shp"))
    ap.add_argument("--exclude-agriculture", action="store_true", help="land step: test the stricter reading")
    args = ap.parse_args()

    root = Path(args.drive_root)
    if not (root / "Energy_System_Modelling_GB").is_dir():
        sys.exit(f"{root} has no Energy_System_Modelling_GB folder; check --drive-root")
    os.environ["GBTEA_DRIVE_ROOT"] = str(root)  # must be set before gbtea is imported
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    warnings.filterwarnings("ignore", category=FutureWarning)

    from gbtea import config as C, run

    print("Data root:", C.DRIVE_ROOT, "\nOutputs:  ", C.OUT)
    sites = None
    for step in [s for s in ALL_STEPS if s in args.steps]:
        t0 = time.time()
        print(f"\n=== {step} ===")
        if step == "prices":
            print(run.step_prices().describe())
        elif step == "costs":
            run.step_costs()
        elif step == "sites":
            sites = run.step_sites()
            print(sites[["site", "lat", "lon", "alt", "duplicate_of"]].to_string())
        elif step == "profiles":
            run.step_era5_profiles(sites)
        elif step == "compare":
            print(run.step_compare_old(sites).round(3).to_string())
        elif step == "validation":
            val = run.step_validation(max_stations=args.max_stations)
            print(val.filter(regex="station|years|_r$|_mbe$").round(3).to_string())
        elif step == "land":
            from gbtea import land
            land.INCLUDE_AGRICULTURE = not args.exclude_agriculture
            print(run.step_land(args.clc_tif, gb_boundary=args.gb_boundary, roads_shp=args.roads).round(1).to_string())
        print(f"{step} done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
