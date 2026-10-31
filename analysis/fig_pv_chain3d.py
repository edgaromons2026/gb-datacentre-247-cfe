"""PV model chain of gbtea/pv.py, isometric style matching the method workflow figure. All icons drawn from primitives."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, Circle
from matplotlib.colors import to_rgb
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#6b7079'
TOP, LEFT, RIGHT = '#f2f3f5', '#d9dce1', '#b8bdc5'
BLUE, BLUE_D, BLUE_L, TEAL, AMBER, WARM = '#2c5fa8', '#1d3f73', '#7fa7dd', '#1f9e7d', '#f2a516', '#c8553d'
C30, S30 = np.cos(np.pi/6), 0.5
fig, ax = plt.subplots(figsize=(177*MM, 104*MM)); ax.set_xlim(-6, 262); ax.set_ylim(-14, 134); ax.set_aspect('equal'); ax.axis('off')

def shade(c, f): return tuple(min(1, max(0, v*f)) for v in to_rgb(c))
class Iso:
    def __init__(s, ox, oy, k=1.0): s.ox, s.oy, s.k = ox, oy, k
    def p(s, x, y, z): return (s.ox + s.k*(x - y)*C30, s.oy + s.k*((x + y)*S30 + z))
    def face(s, pts, fc, ec=EDGE, lw=0.4, z=3, alpha=1):
        ax.add_patch(Polygon([s.p(*q) for q in pts], closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, joinstyle='round'))
    def box(s, x, y, z, dx, dy, dz, top=TOP, left=LEFT, right=RIGHT, zo=3, lw=0.4):
        s.face([(x, y, z), (x, y+dy, z), (x, y+dy, z+dz), (x, y, z+dz)], left, lw=lw, z=zo)
        s.face([(x, y, z), (x+dx, y, z), (x+dx, y, z+dz), (x, y, z+dz)], right, lw=lw, z=zo)
        s.face([(x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)], top, lw=lw, z=zo)
    def line(s, a, b, c='#8d929a', lw=0.4, z=4, ls='-'):
        P, R = s.p(*a), s.p(*b); ax.plot([P[0], R[0]], [P[1], R[1]], color=c, lw=lw, zorder=z, ls=ls, solid_capstyle='round')

def vcyl(cx, cy, r, h, c0='#eef0f3', c1='#9aa1ab', cap='#f7f8f9', z=4):
    e = 0.58*r; n = 12
    for i in range(n):
        t = i/(n-1); col = tuple(np.interp(t, [0, 1], [a, b]) for a, b in zip(to_rgb(c0), to_rgb(c1)))
        x0 = cx - r + 2*r*i/n
        ax.add_patch(Polygon([(x0, cy), (x0+2*r/n+0.05, cy), (x0+2*r/n+0.05, cy+h), (x0, cy+h)], fc=col, ec='none', zorder=z))
    ax.add_patch(Ellipse((cx, cy), 2*r, 2*e, fc=c1, ec='none', zorder=z-0.05))
    for sx in (-r, r): ax.plot([cx+sx]*2, [cy, cy+h], color=EDGE, lw=0.4, zorder=z+0.1)
    th = np.linspace(np.pi, 2*np.pi, 30); ax.plot(cx+r*np.cos(th), cy+e*np.sin(th), color=EDGE, lw=0.4, zorder=z+0.1)
    ax.add_patch(Ellipse((cx, cy+h), 2*r, 2*e, fc=cap, ec=EDGE, lw=0.4, zorder=z+0.2))

def sun(X, Y, r=2.2, z=7):
    for a in np.linspace(0, 2*np.pi, 10, endpoint=False):
        ax.plot([X+1.4*r*np.cos(a), X+1.9*r*np.cos(a)], [Y+1.4*r*np.sin(a), Y+1.9*r*np.sin(a)], color=AMBER, lw=0.6, zorder=z)
    ax.add_patch(Circle((X, Y), r, fc='#ffd36b', ec=AMBER, lw=0.5, zorder=z+0.1))

TW, TD, Z = 20, 13, 2.2
def tile(ox, oy, tint):
    s = Iso(ox, oy); s.face([(-1.5, -1.5, 0), (TW+1.5, -1.5, 0), (TW+1.5, TD+1.5, 0), (-1.5, TD+1.5, 0)], '#000', ec='none', z=1, alpha=0.06)
    s.box(0, 0, 0, TW, TD, Z, top=tint, left=shade(tint, 0.86), right=shade(tint, 0.74), zo=2)
    return s
def cap(s, n, t, sub):
    X, Y = s.p(TW/2, 0, 0); X -= 3; Y = s.oy - 1
    ax.text(X, Y-2.5, f'{n}  {t}', ha='center', va='top', fontsize=6.5, color=INK, zorder=9, fontweight='bold')
    ax.text(X, Y-6.6, sub, ha='center', va='top', fontsize=5.0, color=Q, style='italic', zorder=9, linespacing=1.15)

def panel(s, x0, y0, x1, y1, z0, z1, zo=4):
    s.face([(x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)], BLUE, ec='#dfe6f0', lw=0.4, z=zo)
    for k in range(1, 5): f = k/5; s.line((x0+(x1-x0)*f, y0, z0), (x0+(x1-x0)*f, y1, z1), c=BLUE_L, lw=0.3, z=zo+0.01)
    s.line((x0, (y0+y1)/2, (z0+z1)/2), (x1, (y0+y1)/2, (z0+z1)/2), c=BLUE_L, lw=0.3, z=zo+0.01)

# ---------- icons ----------
def ic_era5(s):
    X, Y = s.p(TW/2, TD/2, Z)
    for k in range(3): vcyl(X, Y-1.5+k*3.6, 5.2, 2.8, c0='#e6eefb', c1='#7f9fd0', cap='#f3f7fd', z=4+k*0.5)
    ax.text(X, Y+12.8, 'ERA5', ha='center', fontsize=5, color=BLUE_D, fontweight='bold', zorder=7)
def ic_sunpos(s):
    pts = [s.p(2+16*t, TD/2 + 4*np.cos(np.pi*t), Z + 11*np.sin(np.pi*t)) for t in np.linspace(0, 1, 40)]
    ax.plot(*zip(*pts), color=AMBER, lw=0.7, ls=(0, (2, 1.4)), zorder=5)
    X, Y = s.p(2+16*0.5, TD/2 + 4*np.cos(np.pi*0.5), Z + 11); sun(X, Y)
    X0, Y0 = s.p(2+16*0.38, TD/2 + 4*np.cos(np.pi*0.38), Z + 11*np.sin(np.pi*0.38))
    ax.add_patch(Circle((X0, Y0), 0.9, fc='white', ec=AMBER, lw=0.5, zorder=6))
    ax.text(X0-1.5, Y0+0.6, 'mid-hour', fontsize=4.4, color='#8a5a00', ha='right', zorder=7, style='italic')
def ic_split(s):
    X, Y = s.p(5, 8, Z+13); sun(X, Y, r=1.9)
    B = s.p(11, 5, Z); ax.annotate('', B, (X+1.5, Y-2), arrowprops=dict(arrowstyle='-|>', color=AMBER, lw=1.0, mutation_scale=6), zorder=6)
    C = s.p(14, 9, Z+12);
    for dx, dy, r in ((0, 0, 2.2), (2.4, 0.4, 2.6), (4.8, 0, 2.0)): ax.add_patch(Circle((C[0]+dx, C[1]+dy), r, fc='#e9edf2', ec='#b8bdc5', lw=0.4, zorder=6))
    for k, t in enumerate((-0.5, 0.0, 0.5)):
        a = (C[0]+2.4+3.2*t, C[1]-2.2); b = (a[0]+4*t, a[1]-6.5)
        ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=BLUE_L, lw=0.7, mutation_scale=5), zorder=6)
    ax.text(X-1, Y-6.5, 'beam', fontsize=4.5, color='#8a5a00', ha='right', zorder=7)
    ax.text(C[0]+7.5, C[1]-7, 'diffuse', fontsize=4.5, color=BLUE_D, ha='left', zorder=7)
def ic_poa(s):
    panel(s, 3, 4, TW-3, TD-3, Z+2.5, Z+7.5)
    for x in (4, TW-4): s.line((x, 4, Z), (x, 4, Z+2.5), c=EDGE, lw=0.6, z=3.5); s.line((x, TD-3, Z), (x, TD-3, Z+7.5), c=EDGE, lw=0.6, z=3.5)
    T = s.p(10, 7, Z+5)
    for (dx, dy, c) in ((-7, 10, AMBER), (2, 12, BLUE_L), (9, -5, '#7aa35b')):
        ax.annotate('', T, (T[0]+dx, T[1]+dy), arrowprops=dict(arrowstyle='-|>', color=c, lw=0.9, mutation_scale=5, shrinkB=1), zorder=6)
    ax.text(T[0]+9.5, T[1]-6.5, 'ground', fontsize=4.4, color='#4f7a32', zorder=7)
def ic_temp(s):
    panel(s, 3, 3, 14, TD-3, Z+2.5, Z+6.5)
    X, Y = s.p(16, 7, Z)
    ax.add_patch(Polygon([(X-0.7, Y+1.5), (X+0.7, Y+1.5), (X+0.7, Y+12), (X-0.7, Y+12)], fc='white', ec=EDGE, lw=0.4, zorder=6))
    ax.add_patch(Polygon([(X-0.4, Y+1.5), (X+0.4, Y+1.5), (X+0.4, Y+8), (X-0.4, Y+8)], fc=WARM, ec='none', zorder=6.1))
    ax.add_patch(Circle((X, Y+1.2), 1.3, fc=WARM, ec=EDGE, lw=0.4, zorder=6.2))
    W = s.p(1, 2, Z+9)
    for k in range(3): ax.plot([W[0]-3+k, W[0]+5+k], [W[1]+k*1.8, W[1]+k*1.8], color='#8aa9cf', lw=0.6, zorder=6)
    ax.text(W[0]-3.5, W[1]+1.5, 'wind', fontsize=4.4, color=BLUE_D, ha='right', zorder=7)
def ic_spec(s):
    cols = ['#6a4c93', '#2c5fa8', '#1f9e7d', '#8ac926', '#f2a516', '#c8553d']
    for i, c in enumerate(cols):
        s.face([(3+i*2.4, 4, Z+0.1), (5.4+i*2.4, 4, Z+0.1), (5.4+i*2.4, 4, Z+9+2*np.sin(i)), (3+i*2.4, 4, Z+9+2*np.sin(i))], c, ec='white', lw=0.2, z=4)
    X, Y = s.p(14, 10, Z+3)
    ax.add_patch(Polygon([(X, Y+7), (X-2.4, Y+2.4), (X+2.4, Y+2.4)], fc='#7fb8e8', ec='none', zorder=6))
    ax.add_patch(Circle((X, Y+2.2), 2.4, fc='#7fb8e8', ec='none', zorder=6))
    ax.text(X+3.2, Y+1.2, 'PW', fontsize=4.6, color=BLUE_D, zorder=7)
def ic_dc(s):
    s.face([(3, TD/2, Z), (TW-3, TD/2, Z), (TW-3, TD/2, Z+13), (3, TD/2, Z+13)], 'white', z=4)
    v = np.linspace(0, 1, 40); i = 1 - np.exp((v - 1)/0.08)
    P = [s.p(4+12*a, TD/2, Z+1.2+10*b) for a, b in zip(v, np.clip(i, 0, 1))]; ax.plot(*zip(*P), color=BLUE, lw=0.9, zorder=5)
    pw = v*np.clip(i, 0, 1); k = pw.argmax(); X, Y = s.p(4+12*v[k], TD/2, Z+1.2+10*i[k])
    ax.add_patch(Circle((X, Y), 0.8, fc=WARM, ec='white', lw=0.3, zorder=6))
    ax.text(X+1.2, Y+0.6, 'MPP', fontsize=4.4, color=WARM, zorder=7)
    s.line((4, TD/2, Z+1.2), (16.5, TD/2, Z+1.2), c=EDGE, lw=0.4, z=5); s.line((4, TD/2, Z+1.2), (4, TD/2, Z+12), c=EDGE, lw=0.4, z=5)
def ic_loss(s):
    hs = [12, 11.6, 11.2, 10.9, 10.7]
    for k, h in enumerate(hs):
        c = BLUE if k == 0 else '#9ab7df' if k < 4 else TEAL
        s.box(2.5+k*3.2, 5, Z, 2.4, 2.4, h, top=shade(c, 1.15), left=shade(c, 1.0), right=shade(c, 0.8), zo=4+k*0.1)
    X, Y = s.p(TW-2, 5, Z+12); ax.text(X+1, Y+1, '−8.7%', fontsize=4.8, color=WARM, ha='left', zorder=7)
def ic_inv(s):
    for k, x in enumerate((3, 11)):
        s.box(x, 4, Z, 6, 5, 9, top='#e9edf2', left='#cfd5dd', right='#aeb6c1', zo=4+k*0.1)
        X, Y = s.p(x, 4+2.5, Z+4.5)
        t = np.linspace(0, 2*np.pi, 40); ax.plot(X-1.6+3.2*t/(2*np.pi)*C30, Y+1.4*np.sin(t)-1.6*t/(2*np.pi)*S30, color=BLUE_D, lw=0.6, zorder=5+k*0.1)
    X, Y = s.p(10, 2, Z+12); ax.text(X+2, Y+2, '2 × 1.9 MW', fontsize=4.6, color=Q, ha='center', zorder=7)
def ic_cf(s):
    rng = np.random.default_rng(2); h = 3 + 9*np.sin(np.linspace(0.15, np.pi-0.15, 12))**1.5 * rng.uniform(0.7, 1.0, 12)
    for k, v in enumerate(h): s.box(2+k*1.4, 6, Z, 1.1, 1.1, v, top=shade(AMBER, 1.15), left=shade(AMBER, 1.0), right=shade(AMBER, 0.8), zo=4+k*0.02)
    X, Y = s.p(TW-2, 4, Z+13); ax.text(X+1, Y, 'CF', fontsize=5.4, color='#8a5a00', fontweight='bold', zorder=7)

# ---------- layout: two rows, left to right then right to left ----------
TINT_IN, TINT_OPT, TINT_EL = '#eef1f6', '#fdf3e2', '#eaf3fb'
XS = [6, 58, 110, 162, 214]
R1 = [(ic_era5, 'Weather', 'ERA5 direct + diffuse,\nT, dew point, albedo;\n100 m → 10 m wind', TINT_IN),
      (ic_sunpos, 'Sun position', 'NREL SPA at mid-hour\n(stamp − 30 min),\nsite pressure and T', TINT_OPT),
      (ic_split, 'Beam and diffuse', 'DNI = direct / cos z\n(z < 87°, ≤ extraterr.);\nDHI = GHI − DNI cos z', TINT_OPT),
      (ic_poa, 'Plane of array', 'Hay–Davies sky model;\ninfinite-sheds rows\n(GCR 0.40, 1.5 m)', TINT_OPT),
      (ic_temp, 'Cell temperature', 'Faiman model,\nu0 = 25, u1 = 6.84,\n10 m wind speed', TINT_EL)]
R2 = [(ic_cf, 'Hourly output', 'AC kW, night tare → 0;\nCF = AC / 5,013 kWp;\nhour-ending stamps', TINT_IN),
      (ic_inv, 'Inverter', 'Sandia model,\n2 × 1.9 MW AC,\nDC/AC ratio 1.32', TINT_EL),
      (ic_loss, 'System losses', 'PVWatts, 8.7% total:\nsoiling, mismatch, wiring,\nLID, nameplate', TINT_EL),
      (ic_dc, 'DC power', 'CEC single-diode,\nFS-4117-3 CdTe;\nphysical AOI loss', TINT_EL),
      (ic_spec, 'Spectral', 'First Solar CdTe\ncorrection from\nprecipitable water', TINT_EL)]
T1 = [tile(x, 92, c) for x, (_, _, _, c) in zip(XS, R1)]
T2 = [tile(x, 18, c) for x, (_, _, _, c) in zip(XS, R2)]
for n, (s, (f, a, b, _)) in enumerate(zip(T1, R1), 1): f(s); cap(s, n, a, b)
for n, (s, (f, a, b, _)) in zip((10, 9, 8, 7, 6), zip(T2, R2)): f(s); cap(s, n, a, b)

def arrow(a, b, rad=0.0, c='#8d929a', lw=1.3):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, mutation_scale=8, shrinkA=0, shrinkB=0,
                connectionstyle=f'arc3,rad={rad}'), zorder=1.5)
for x0, x1 in zip(XS[:-1], XS[1:]): arrow((x0+20, 104), (x1-14, 104))
arrow((XS[-1]+22, 98), (XS[-1]+22, 46), rad=-0.45)
for x0, x1 in zip(XS[1:][::-1], XS[:-1][::-1]): arrow((x0-14, 30), (x1+20, 30))
ax.text(128, 130, 'Irradiance and solar geometry', ha='center', fontsize=7.2, color=INK, fontweight='bold')
ax.text(128, 61, 'Module, inverter and losses (pvlib ModelChain, run from plane-of-array)', ha='center', fontsize=7.2, color=INK, fontweight='bold')
ax.text(128, -13, 'Each step runs hourly for 2000–2024 at each of the 13 solar sites and for three mounts (fixed 35°, single-axis, dual-axis).',
        ha='center', fontsize=5.6, color=Q, style='italic')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
