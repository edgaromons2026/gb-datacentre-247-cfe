"""Wind model chain of gbtea/wind.py and flagship.zone_series, isometric style matching the method workflow figure. All icons drawn from primitives."""
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
fig, ax = plt.subplots(figsize=(177*MM, 104*MM)); ax.set_xlim(-6, 226); ax.set_ylim(-14, 134); ax.set_aspect('equal'); ax.axis('off')

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
def ic_loss(s):
    hs = [12, 11.6, 11.2, 10.9, 10.7]
    for k, h in enumerate(hs):
        c = BLUE if k == 0 else '#9ab7df' if k < 4 else TEAL
        s.box(2.5+k*3.2, 5, Z, 2.4, 2.4, h, top=shade(c, 1.15), left=shade(c, 1.0), right=shade(c, 0.8), zo=4+k*0.1)
    X, Y = s.p(TW-2, 5, Z+12); ax.text(X+1, Y+1, '× 0.86', fontsize=4.8, color=WARM, ha='left', zorder=7)
def ic_cf(s):
    rng = np.random.default_rng(2); h = 3 + 9*np.sin(np.linspace(0.15, np.pi-0.15, 12))**1.5 * rng.uniform(0.7, 1.0, 12)
    for k, v in enumerate(h): s.box(2+k*1.4, 6, Z, 1.1, 1.1, v, top=shade(AMBER, 1.15), left=shade(AMBER, 1.0), right=shade(AMBER, 0.8), zo=4+k*0.02)
    X, Y = s.p(TW-2, 4, Z+13); ax.text(X+1, Y, 'CF', fontsize=5.4, color='#8a5a00', fontweight='bold', zorder=7)


def ic_profile(s):
    X0, Y0 = s.p(4, TD/2, Z)
    ax.plot([X0, X0], [Y0, Y0+14], color=EDGE, lw=0.5, zorder=5)
    for z, r in ((1.5, 0.55), (5, 0.8), (9, 0.93), (13, 1.0)):
        c = BLUE if z in (9, 13) else BLUE_L
        ax.annotate('', (X0+12*r, Y0+z), (X0, Y0+z), arrowprops=dict(arrowstyle='-|>', color=c, lw=0.9, mutation_scale=5), zorder=6)
    ax.text(X0+13.5, Y0+13, '100 m', fontsize=4.4, color='#8a5a00', va='center', zorder=7)
    ax.text(X0+12.5, Y0+9, 'hub', fontsize=4.4, color=BLUE_D, va='center', zorder=7)
def ic_density(s):
    X, Y = s.p(13, 7, Z)
    ax.add_patch(Polygon([(X-0.7, Y+1.5), (X+0.7, Y+1.5), (X+0.7, Y+12), (X-0.7, Y+12)], fc='white', ec=EDGE, lw=0.4, zorder=6))
    ax.add_patch(Polygon([(X-0.4, Y+1.5), (X+0.4, Y+1.5), (X+0.4, Y+6.5), (X-0.4, Y+6.5)], fc=BLUE, ec='none', zorder=6.1))
    ax.add_patch(Circle((X, Y+1.2), 1.3, fc=BLUE, ec=EDGE, lw=0.4, zorder=6.2))
    rng = np.random.default_rng(4); P = s.p(4, 8, Z)
    for k in range(16):
        ax.add_patch(Circle((P[0]-6+rng.uniform(0, 9), P[1]+rng.uniform(1, 12)), 0.7, fc='#c9d8ec', ec='#7fa7dd', lw=0.3, zorder=5.5))
    ax.text(P[0]-1.5, P[1]+13.5, 'ρ', fontsize=6.5, color=BLUE_D, ha='center', fontweight='bold', zorder=7)
def _curve(s, shift=0.0, c=BLUE, lw=0.9, smooth=True, z=5):
    v = np.linspace(0, 1, 50)
    y = (1/(1+np.exp(-(v-0.38-shift)/0.07))) * (1 if not smooth else (1 - 0.35*np.clip((v-0.75)/0.25, 0, 1)**1.2))
    if not smooth: y = np.where(v < 0.88, 1/(1+np.exp(-(v-0.36)/0.05)), 0)
    P = [s.p(3+14*a, TD/2, Z+1.2+10*b) for a, b in zip(v, y)]; ax.plot(*zip(*P), color=c, lw=lw, zorder=z)
def _board(s):
    s.face([(2, TD/2, Z), (TW-2, TD/2, Z), (TW-2, TD/2, Z+13), (2, TD/2, Z+13)], 'white', z=4)
    s.line((3, TD/2, Z+1.2), (17.5, TD/2, Z+1.2), c=EDGE, lw=0.4, z=5); s.line((3, TD/2, Z+1.2), (3, TD/2, Z+12), c=EDGE, lw=0.4, z=5)
def ic_smooth(s):
    _board(s); _curve(s, c=Q, lw=0.6, smooth=False, z=5); _curve(s, c=BLUE, lw=1.0, z=5.1)
    X, Y = s.p(9, TD/2, Z+1.2); g = np.linspace(-1, 1, 30)
    ax.fill_between(X - 3 + 6*(g+1)/2*C30, Y + 4*np.exp(-g**2/0.15) + (g+1)/2*3*S30, Y + (g+1)/2*3*S30, color=AMBER, alpha=0.35, lw=0, zorder=5.2)
def ic_dcorr(s):
    _board(s); _curve(s, c=BLUE, lw=1.0, z=5.1); _curve(s, shift=0.06, c=WARM, lw=1.0, z=5.2)
    X, Y = s.p(10, TD/2, Z+7); ax.annotate('', (X+2.2, Y+1.2), (X-0.8, Y+1.2), arrowprops=dict(arrowstyle='-|>', color=WARM, lw=0.6, mutation_scale=5), zorder=6)
def ic_turbine(s):
    X, Y = s.p(TW/2, TD/2, Z); H = 13
    ax.add_patch(Polygon([(X-0.8, Y), (X+0.8, Y), (X+0.35, Y+H), (X-0.35, Y+H)], fc='#f4f5f7', ec=EDGE, lw=0.4, zorder=5))
    for ang in (90, 210, 330):
        a = np.radians(ang); L = 7.0; n = np.array([-np.sin(a), np.cos(a)]); d = np.array([np.cos(a), np.sin(a)]); b = np.array([X, Y+H])
        ax.add_patch(Polygon([b+0.5*n, b+0.25*L*d+0.7*n, b+L*d, b-0.25*n], fc='#fafafa', ec=EDGE, lw=0.35, zorder=6))
    ax.add_patch(Circle((X, Y+H), 0.7, fc=TOP, ec=EDGE, lw=0.4, zorder=7))
    ax.text(X+5, Y+2, 'kW', fontsize=5, color=BLUE_D, fontweight='bold', zorder=7)

# ---------- layout: two rows of four, left to right then right to left ----------
TINT_IN, TINT_AIR, TINT_PC, TINT_OUT = '#eef1f6', '#eaf3fb', '#e9f5ef', '#fdf3e2'
XS = [8, 70, 132, 194]
R1 = [(ic_era5, 'Weather', 'ERA5 100 m wind, surface\nroughness, 2 m temperature;\nsite altitude', TINT_IN),
      (ic_profile, 'Hub-height wind', 'hub at 100 m = ERA5 level,\nso no extrapolation;\nlog law only if hub ≠ 100 m', TINT_AIR),
      (ic_density, 'Air density', 'T at hub: 2 m T − 6.5 K/km;\np: standard atmosphere\nat altitude + hub; ρ = p / RT', TINT_AIR),
      (ic_smooth, 'Smoothed curve', 'V126/3450 power curve,\nGaussian σ = 0.6 + 0.2 v\n(Staffell–Pfenninger)', TINT_PC)]
R2 = [(ic_cf, 'Hourly CF', 'per kW of nameplate,\nUTC hour-ending;\nto the optimiser', TINT_IN),
      (ic_loss, 'Farm losses', 'in flagship.py: × 0.86\n(wakes, availability,\nelectrical)', TINT_OUT),
      (ic_turbine, 'Turbine output', 'curve interpolated at hub\nwind; clipped ≥ 0;\ncut-out softened by smoothing', TINT_PC),
      (ic_dcorr, 'Density correction', 'curve wind speeds scaled\nby (1.225 / ρ)^(1/3 to 2/3)\n(windpowerlib)', TINT_PC)]
T1 = [tile(x, 92, c) for x, (_, _, _, c) in zip(XS, R1)]
T2 = [tile(x, 18, c) for x, (_, _, _, c) in zip(XS, R2)]
for n, (s, (f, a, b, _)) in enumerate(zip(T1, R1), 1): f(s); cap(s, n, a, b)
for n, (s, (f, a, b, _)) in zip((8, 7, 6, 5), zip(T2, R2)): f(s); cap(s, n, a, b)

def arrow(a, b, rad=0.0, c='#8d929a', lw=1.3):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, mutation_scale=8, shrinkA=0, shrinkB=0,
                connectionstyle=f'arc3,rad={rad}'), zorder=1.5)
for x0, x1 in zip(XS[:-1], XS[1:]): arrow((x0+20, 104), (x1-14, 104))
arrow((XS[-1]+22, 98), (XS[-1]+22, 46), rad=-0.45)
for x0, x1 in zip(XS[1:][::-1], XS[:-1][::-1]): arrow((x0-14, 30), (x1+20, 30))
ax.text(108, 130, 'Wind and air at hub height', ha='center', fontsize=7.2, color=INK, fontweight='bold')
ax.text(108, 61, 'Power curve to capacity factor (windpowerlib)', ha='center', fontsize=7.2, color=INK, fontweight='bold')
ax.text(108, -13, 'Each step runs hourly for 2000–2024 at each of the 12 wind sites.',
        ha='center', fontsize=5.6, color=Q, style='italic')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
