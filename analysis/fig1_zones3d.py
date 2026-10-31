"""Fig. 1: 3D (tilted, extruded) map of the 20 GB study zones with solar and wind sites.
Inputs: zones_json.geojson (zone polygons, WGS84) and zones_summary.csv (site coordinates)."""
import sys, numpy as np, pandas as pd, geopandas as gpd
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Ellipse
from matplotlib.colors import to_rgb
from shapely.geometry import Point, Polygon, MultiPolygon
ZONES, SUMMARY, OUT = sys.argv[1:4]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#5d6168'
TILT, H = 0.58, 14.0                  # vertical foreshortening of the map plane, slab thickness (km on screen)
NAMES = {'Z1_1': 'Shetland', 'Z1_2': 'Western Isles', 'Z1_3': 'Highland', 'Z1_4': 'Highland', 'Z2': 'Aberdeenshire',
         'Z3': 'Perth and Kinross', 'Z4': 'Buteshire', 'Z5': 'North Lanarkshire', 'Z6': 'Dumfries and Galloway', 'Z7': 'Northumberland',
         'Z8': 'York', 'Z9': 'Birkenhead', 'Z10': 'Lincolnshire', 'Z11': 'Warwickshire', 'Z12': 'Suffolk',
         'Z13': 'Monmouthshire', 'Z14': 'City of Westminster', 'Z15': 'Kent', 'Z16': 'West Sussex', 'Z17': 'Devon'}   # as in the zone reference map
PAL = ['#8fd3b8', '#f2df9a', '#f3a89b', '#dcb3e0', '#a9d6e8', '#f8d8a8', '#f3e3a2', '#e7a8ee', '#b5e3a1', '#f4a38e',
       '#bfeee4', '#f0dcc0', '#d9f2ee', '#e3e3ec', '#f6c0c8', '#fbe4d8', '#bcdfe0', '#e2cfe0', '#e8f6df', '#f7cfa6']
ORDER = ['Z1_1', 'Z1_2', 'Z1_3', 'Z1_4', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9', 'Z10', 'Z11', 'Z12', 'Z13', 'Z14', 'Z15', 'Z16', 'Z17']

g = gpd.read_file(ZONES).set_crs(4326, allow_override=True)
g = g[g['Name_1'].isin(ORDER)].to_crs(27700)
g['geometry'] = g.geometry.simplify(400)
s = pd.read_csv(SUMMARY)
def proj(x, y, z=0.0): return x/1000.0, y/1000.0*TILT + z
def polys(geom): return [p for p in (list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]) if p.area > 4e6]

fig, ax = plt.subplots(figsize=(150*MM, 175*MM)); ax.set_aspect('equal'); ax.axis('off')
# soft ground shadow
for geom in g.geometry:
    for p in polys(geom):
        if p.area < 2e7: continue
        x, y = p.exterior.xy; X, Y = proj(np.array(x)+9000, np.array(y)-9000/TILT*0.0, -H-4)
        ax.add_patch(MPoly(np.c_[X, Y], fc='#000', alpha=0.05, ec='none', zorder=0))
# paint zones north to south so nearer (southern) slabs overlap farther ones
g['ymax'] = g.geometry.bounds['maxy']; col = {z: PAL[i] for i, z in enumerate(ORDER)}
for _, r in g.sort_values('ymax', ascending=False).iterrows():
    top = to_rgb(col[r.Name_1]); side = tuple(c*0.72 for c in top)
    for p in polys(r.geometry):
        x, y = map(np.array, p.exterior.xy)
        X0, Y0 = proj(x, y, -H); X1, Y1 = proj(x, y, 0)
        for i in range(len(x)-1):                         # side walls on south-facing edges only
            if x[i+1] - x[i] > 0 or (y[i+1] < y[i] and False): pass
            quad = [(X1[i], Y1[i]), (X1[i+1], Y1[i+1]), (X0[i+1], Y0[i+1]), (X0[i], Y0[i])]
            shade = side if (x[i+1]-x[i]) >= 0 else tuple(c*0.85 for c in side)
            ax.add_patch(MPoly(quad, fc=shade, ec=shade, lw=0.2, zorder=1))
        ax.add_patch(MPoly(np.c_[X1, Y1], fc=top, ec=EDGE, lw=0.35, zorder=2))

# sites: 3D pins standing on the slab
def pin(lon, lat, c, dx=0.0):
    pt = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(27700)[0]
    X, Y = proj(pt.x, pt.y, 0); X += dx
    ax.add_patch(Ellipse((X, Y), 9, 9*0.45, fc='#000', alpha=0.25, ec='none', zorder=5))
    ax.plot([X, X], [Y, Y+22], color='#3a3d42', lw=0.7, zorder=6)
    ax.scatter([X], [Y+24], s=26, c=[c], edgecolors='white', linewidths=0.6, zorder=7)
    ax.scatter([X-1.2], [Y+25.2], s=3, c='white', alpha=0.8, zorder=8)
solar = s.drop_duplicates('solar_dup')[['lat', 'lon']].drop_duplicates()
wind = s.drop_duplicates('wind_dup')[['wlat', 'wlon']].drop_duplicates()
shared = set(map(tuple, solar.round(3).values)) & set(map(tuple, wind.round(3).values))
for la, lo in solar.values: pin(lo, la, '#f2a516', dx=(-3.5 if (round(la, 3), round(lo, 3)) in shared else 0))
for la, lo in wind.values: pin(lo, la, '#2c5fa8', dx=(3.5 if (round(la, 3), round(lo, 3)) in shared else 0))

# labels
LOFF = {'Z1_1': (-60, 10), 'Z1_2': (-70, 0), 'Z14': (40, 28), 'Z15': (55, 6), 'Z16': (30, -32), 'Z13': (-20, 0), 'Z12': (35, 24), 'Z7': (45, -12), 'Z2': (30, -14),
        'Z4': (-40, -10), 'Z9': (-25, 5), 'Z17': (-10, -5), 'Z5': (-10, 0), 'Z11': (0, 0), 'Z10': (25, 6), 'Z1_4': (-30, 0)}
for _, r in g.iterrows():
    big = max(polys(r.geometry), key=lambda p: p.area); c = big.representative_point()
    X, Y = proj(c.x, c.y, 0); dx, dy = LOFF.get(r.Name_1, (0, 0))
    if dx or dy: ax.plot([X, X+dx], [Y, Y+dy], color=Q, lw=0.4, zorder=8)
    ax.text(X+dx, Y+dy, f'{r.Name_1}  {NAMES[r.Name_1]}', ha='center', va='center', fontsize=5.6, color=INK, zorder=9,
            bbox=dict(boxstyle='round,pad=0.22,rounding_size=0.3', fc='white', ec='#9a9da3', lw=0.4, alpha=0.92))
# legend and scale
xmin, xmax = ax.get_xlim(); ymin, ymax = ax.get_ylim()
lx, ly = 500, 990*TILT
ax.scatter([lx], [ly], s=26, c='#f2a516', edgecolors='white', linewidths=0.6); ax.text(lx+10, ly, 'Solar site (PV)', va='center')
ax.scatter([lx], [ly-22], s=26, c='#2c5fa8', edgecolors='white', linewidths=0.6); ax.text(lx+10, ly-22, 'Wind site (V126)', va='center')
ax.plot([505, 605], [890*TILT]*2, color=INK, lw=1.2); ax.text(555, 890*TILT+6, '100 km (E–W)', ha='center', fontsize=5.6)
ax.annotate('N', (655, 960*TILT+45), (655, 960*TILT-5), ha='center', fontsize=7, fontweight='bold',
            arrowprops=dict(arrowstyle='-|>', color=INK, lw=0.8))
ax.autoscale_view(); ax.set_xlim(-10, 680); ax.set_ylim(-30, 1230*TILT+40)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
