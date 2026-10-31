"""Corrected GLAES land eligibility for solar and wind across GB, plus land caps per site.

Fixes against the original code (land_eligibility_review.md):
1. The 1 km buffer is applied around SETTLEMENTS (CORINE 1-2, urban fabric) as its own step.
   Before, invert=True + buffer=1000 trimmed 1 km off every eligible patch whatever its neighbour.
2. Class lists are written as GLAES value strings, so they are sets, not numeric ranges.
3. Heterogeneous agriculture is CORINE 19-22, not 19 alone.
4. Roads: 200 m from motorways AND A roads ("major roads"), not motorways only.
5. Placements are distributed on the solar and wind calculators, not on the unexcluded `ec`.
Open decision (review item 5): the rules both exclude and include agricultural land. The default
here INCLUDES arable, pasture and heterogeneous agriculture, as the original code did.
Set INCLUDE_AGRICULTURE = False to test the other reading.

Run in Colab: `pip install glaes geokit` (needs GDAL; Colab has it).
"""
from pathlib import Path

import numpy as np

from . import config as C

INCLUDE_AGRICULTURE = True
AGRI = "12,18,[19-22]"            # non-irrigated arable, pastures, heterogeneous agriculture
WIND_EXTRA = "26,31,32"           # natural grassland, bare rock, sparsely vegetated
SETTLEMENTS = "[1-2]"             # continuous and discontinuous urban fabric
SETTLEMENT_BUFFER_M = 1000
ROAD_BUFFER_M = 200
ROAD_WHERE = "class='Motorway' OR class='A Road'"

# 250 m (was 100 m): the 100 m full-GB calculator peaked at ~11 GB on a 16 GB PC. At 5 MW the
# 25 km caps are only a reporting check, so 250 m is ample.
PIXEL_RES_M = 250

# Gross installed power density used to turn eligible land into a capacity cap.
MW_PER_KM2 = {"solar": 50.0, "wind": 5.0}


def eligible_classes(tech):
    base = AGRI if INCLUDE_AGRICULTURE else ""
    if tech == "solar":
        return base
    extra = WIND_EXTRA
    return f"{base},{extra}" if base else extra


def run_glaes(tech, gb_boundary, clc_tif, roads_shp, out_dir=C.OUT / "land", roads_where=ROAD_WHERE):
    import glaes as gl  # imported here so the rest of the package works without GDAL

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ec = gl.ExclusionCalculator(region=str(gb_boundary), srs=27700, pixelRes=PIXEL_RES_M)
    # Keep only the eligible land-cover classes (no buffer here).
    ec.excludeRasterType(source=str(clc_tif), value=eligible_classes(tech), invert=True)
    # 1 km setback from settlements, as its own step.
    ec.excludeRasterType(source=str(clc_tif), value=SETTLEMENTS, buffer=SETTLEMENT_BUFFER_M)
    # 200 m from major roads.
    ec.excludeVectorType(str(roads_shp), where=roads_where, buffer=ROAD_BUFFER_M)  # None if pre-filtered
    tif = out_dir / f"GB_{tech}_eligible_corrected.tif"
    ec.save(str(tif), overwrite=True)
    print(f"{tech}: {ec.percentAvailable:.1f} % of GB eligible -> {tif}")
    return ec, tif


def major_roads(roads_shp, out_dir=C.OUT / "land"):
    """Motorways and A roads only, cached as a small GeoPackage. GB_RoadLink has a 5.5 GB attribute
    table, and GLAES read all of it for every technology. Same features as ROAD_WHERE on the full file."""
    import geopandas as gpd

    out = Path(out_dir) / "GB_RoadLink_major.gpkg"
    if not out.exists():
        g = gpd.read_file(str(roads_shp), where=ROAD_WHERE, columns=["class"])
        g.to_file(out, driver="GPKG")
        print(f"major roads: {len(g)} links -> {out}")
    return out


def run_tech(tech, gb_boundary, clc_tif, roads_shp, include_agriculture=True, out_dir=C.OUT / "land"):
    """One technology end to end (eligibility tif + placements). Meant to run in its own process,
    so the calculator's memory is returned to the OS before the next technology starts."""
    import pandas as pd  # noqa: F401  (place() needs it)

    global INCLUDE_AGRICULTURE
    INCLUDE_AGRICULTURE = include_agriculture
    ec, tif = run_glaes(tech, gb_boundary, clc_tif, roads_shp, out_dir=out_dir, roads_where=None)
    place(ec).to_csv(Path(out_dir) / f"{tech}_placements_corrected.csv", index=False)
    return tif


def place(ec, separation_m=100_000):
    """Representative sites on the CORRECTED calculator. Returns a lat/lon table."""
    import geopandas as gpd
    import pandas as pd

    ec.distributeItems(separation=separation_m)
    xy = pd.DataFrame(ec.itemCoords, columns=["Easting", "Northing"])
    g = gpd.GeoDataFrame(xy, geometry=gpd.points_from_xy(xy.Easting, xy.Northing), crs=27700)
    g = g.to_crs(4326)
    xy["Latitude"], xy["Longitude"] = g.geometry.y, g.geometry.x
    return xy


def land_cap_mw(tif, lat, lon, tech, radius_km=25.0):
    """Eligible area (km2) within radius_km of a point, and the MW cap it implies."""
    import rasterio
    from pyproj import Transformer

    e, n = Transformer.from_crs(4326, 27700, always_xy=True).transform(lon, lat)
    with rasterio.open(tif) as src:
        r = radius_km * 1000
        win = rasterio.windows.from_bounds(e - r, n - r, e + r, n + r, src.transform)
        a = src.read(1, window=win, boundless=True, fill_value=0).astype(float)
        tr = src.window_transform(win)
        px_km2 = abs(src.res[0] * src.res[1]) / 1e6
    rows, cols = np.indices(a.shape)
    xs, ys = rasterio.transform.xy(tr, rows, cols)
    inside = (np.hypot(np.asarray(xs) - e, np.asarray(ys) - n) <= r)
    avail = np.where(np.isfinite(a), a, 0) / 100.0  # GLAES availability is 0-100
    km2 = float((avail * inside).sum() * px_km2)
    return km2, km2 * MW_PER_KM2[tech]
