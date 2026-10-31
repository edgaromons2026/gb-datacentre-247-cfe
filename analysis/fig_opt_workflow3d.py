"""Fig. O4: how flagship.py uses the optimisation LP (experiments A, B, C), isometric style of the method workflow figure.
Icons and helpers are those of fig_workflow3d.py."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, Circle, FancyArrow
from matplotlib.colors import to_rgb
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#6b7079'
TOP, LEFT, RIGHT = '#f2f3f5', '#d9dce1', '#b8bdc5'
BLUE, BLUE_D, BLUE_L, TEAL, TEAL_D, AMBER = '#2c5fa8', '#1d3f73', '#7fa7dd', '#1f9e7d', '#14765d', '#f2a516'
C30, S30 = np.cos(np.pi/6), 0.5
fig, ax = plt.subplots(figsize=(177*MM, 122*MM)); ax.set_xlim(-12, 262); ax.set_ylim(-14, 162); ax.set_aspect('equal'); ax.axis('off')

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
    def line(s, a, b, c='#8d929a', lw=0.4, z=4):
        P, R = s.p(*a), s.p(*b); ax.plot([P[0], R[0]], [P[1], R[1]], color=c, lw=lw, zorder=z, solid_capstyle='round')

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

TW, TD = 20, 13                                       # tile footprint
def tile(ox, oy, tint):
    s = Iso(ox, oy); s.face([(-1.5, -1.5, 0), (TW+1.5, -1.5, 0), (TW+1.5, TD+1.5, 0), (-1.5, TD+1.5, 0)], '#000', ec='none', z=1, alpha=0.06)
    s.box(0, 0, 0, TW, TD, 2.2, top=tint, left=shade(tint, 0.86), right=shade(tint, 0.74), zo=2)
    return s
def cap(s, t, sub):
    X, Y = s.p(TW/2, 0, 0); X -= 3; Y = s.oy - 1
    ax.text(X, Y-2.5, t, ha='center', va='top', fontsize=6.6, color=INK, zorder=9)
    ax.text(X, Y-6.3, sub, ha='center', va='top', fontsize=5.3, color=Q, style='italic', zorder=9, linespacing=1.15)

# ---------- icons (drawn on a tile's top, z = 2.2) ----------
Z = 2.2
def ic_era5(s):
    X, Y = s.p(TW/2, TD/2, Z)
    for k in range(3): vcyl(X, Y-1.5+k*3.6, 5.2, 2.8, c0='#e6eefb', c1='#7f9fd0', cap='#f3f7fd', z=4+k*0.5)
    ax.text(X, Y+12.8, 'ERA5', ha='center', fontsize=5, color=BLUE_D, fontweight='bold', zorder=7)
def ic_midas(s):
    base = s.p(TW/2, TD/2, Z); X, Y = base
    ax.plot([X, X], [Y, Y+15], color='#5a5f66', lw=0.9, zorder=5)
    for d in (-1, 1): ax.plot([X, X+d*3.2], [Y, Y-1.6], color='#5a5f66', lw=0.4, zorder=5); ax.plot([X, X+d*3.2], [Y+8, Y-1.6], color='#9aa0a8', lw=0.3, zorder=4)
    ax.plot([X-3.2, X+3.2], [Y+14, Y+14], color='#5a5f66', lw=0.6, zorder=5)
    for d in (-3.2, 3.2): ax.add_patch(Ellipse((X+d, Y+14.6), 1.6, 1.0, fc='#5a5f66', ec='none', zorder=6))
    ax.add_patch(Polygon([(X, Y+11), (X+4.5, Y+11.6), (X+4.5, Y+10.4)], fc=AMBER, ec='none', zorder=6))
    s2 = Iso(X+4, Y-2); s2.box(0, 0, 0, 2.6, 2, 3.2, zo=5)
def ic_costs(s):
    for i, (x, y, n) in enumerate(((5, 8, 4), (10, 5, 6), (15, 8, 3))):
        X, Y = s.p(x, y, Z)
        for k in range(n): vcyl(X, Y+k*1.25, 2.4, 1.0, c0='#fbe3a6', c1='#c9901c', cap='#fdecc0', z=4+k*0.2+i*0.01)
    X, Y = s.p(10, 5, Z); ax.text(X, Y+n*1.25+3.6, '£', ha='center', fontsize=6, color='#8a5a00', fontweight='bold', zorder=8)
def ic_land(s):
    s.face([(2, 2, Z+0.05), (TW-2, 2, Z+0.05), (TW-2, TD-2, Z+0.05), (2, TD-2, Z+0.05)], '#e8f3e2', z=3)
    for (x, y, w, h, c) in ((3, 3, 6, 4, '#b5dca2'), (10, 6, 6, 4, '#9fd18a'), (4, 8, 4, 2.5, '#cfe8c4'), (12, 2.5, 5, 3, '#cfe8c4')):
        s.face([(x, y, Z+0.1), (x+w, y, Z+0.1), (x+w, y+h, Z+0.1), (x, y+h, Z+0.1)], c, ec='none', z=3.2)
    s.line((2, 7.5, Z+0.15), (TW-2, 6.5, Z+0.15), c='#c9a77a', lw=0.7, z=3.3)
    X, Y = s.p(11, 7, Z)
    ax.plot([X, X], [Y, Y+7], color='#3a3d42', lw=0.6, zorder=6); ax.scatter([X], [Y+8], s=18, c='#d64545', edgecolors='white', linewidths=0.5, zorder=7)
def ic_pv(s):
    s.face([(3, 3, Z+2), (TW-3, 3, Z+2), (TW-3, TD-3, Z+6.5), (3, TD-3, Z+6.5)], BLUE, ec='#dfe6f0', lw=0.4, z=4)
    for k in range(1, 6): s.line((3+(TW-6)*k/6, 3, Z+2), (3+(TW-6)*k/6, TD-3, Z+6.5), c=BLUE_L, lw=0.3, z=5)
    s.line((3, TD/2, Z+4.25), (TW-3, TD/2, Z+4.25), c=BLUE_L, lw=0.3, z=5)
    for x in (4, TW-4): s.line((x, 3, Z), (x, 3, Z+2), c=EDGE, lw=0.6, z=3.5); s.line((x, TD-3, Z), (x, TD-3, Z+6.5), c=EDGE, lw=0.6, z=3.5)
def ic_wind(s):
    X, Y = s.p(TW/2, TD/2, Z); H = 11
    ax.add_patch(Polygon([(X-0.8, Y), (X+0.8, Y), (X+0.35, Y+H), (X-0.35, Y+H)], fc='#f4f5f7', ec=EDGE, lw=0.4, zorder=5))
    for ang in (90, 210, 330):
        a = np.radians(ang); L = 6.5; n = np.array([-np.sin(a), np.cos(a)]); d = np.array([np.cos(a), np.sin(a)]); b = np.array([X, Y+H])
        ax.add_patch(Polygon([b+0.5*n, b+0.25*L*d+0.7*n, b+L*d, b-0.25*n], fc='#fafafa', ec=EDGE, lw=0.35, zorder=6))
    ax.add_patch(Circle((X, Y+H), 0.7, fc=TOP, ec=EDGE, lw=0.4, zorder=7))
def ic_load(s):
    for i, x in enumerate((4, 9.5)):
        s.box(x, 4, Z, 4, 5, 13, top='#3c4f72', left=BLUE_D, right='#162f57', zo=4+i*0.1)
        for r in range(7): s.line((x, 4.6, Z+1.5+r*1.6), (x, 8.4, Z+1.5+r*1.6), c='#62a0ff', lw=0.45, z=5+i*0.1)
    X, Y = s.p(TW-2, 2, Z)
    ax.text(X+1, Y+5, 'PUE(T)', fontsize=4.8, color=Q, ha='center', zorder=7, style='italic')
def ic_valid(s):
    s.face([(3, TD/2, Z), (TW-3, TD/2, Z), (TW-3, TD/2, Z+13), (3, TD/2, Z+13)], 'white', z=4)
    rng = np.random.default_rng(3); u = rng.uniform(0.1, 0.9, 22); v = np.clip(u + rng.normal(0, 0.07, 22), 0.05, 0.95)
    for a, b in zip(u, v):
        X, Y = s.p(3+(TW-6)*a, TD/2, Z+13*b); ax.add_patch(Circle((X, Y), 0.45, fc=BLUE, ec='none', zorder=5))
    s.line((3, TD/2, Z), (TW-3, TD/2, Z+13), c='#d64545', lw=0.6, z=5)
    X, Y = s.p(TW-3, TD/2, Z+13); ax.text(X-1, Y-3.5, 'r', fontsize=5, color='#d64545', style='italic', zorder=6, ha='right')
def ic_lp(s):
    s.box(5, 3, Z, 10, 8, 10, top='#dbe7f8', left='#b9cff0', right='#94b3e3', zo=4)
    nodes = [(5, 6, Z+10), (10, 3, Z+10), (15, 7, Z+10), (10, 11, Z+10), (10, 7, Z+10)]
    for a in nodes[:4]: s.line(a, nodes[4], c=BLUE_D, lw=0.6, z=5)
    for a in nodes: X, Y = s.p(*a); ax.add_patch(Circle((X, Y), 0.9, fc=BLUE_D, ec='white', lw=0.3, zorder=6))
    X, Y = s.p(10, 3, Z+5); ax.text(X+1, Y-0.5, 'LP', fontsize=6.5, fontweight='bold', color=BLUE_D, ha='center', va='center', zorder=6)
def ic_heat(s, n=10):
    cm = plt.get_cmap('YlOrRd'); rng = np.random.default_rng(7)
    for i in range(n):
        for j in range(n):
            v = 0.12 + (0.0 if i == j else 0.25 + 0.15*rng.random()) + (0.45 if j in (3, 7) and i != j else 0)
            x0, y0 = 2+i*(TW-4)/n, 1+j*(TD-2)/n
            s.face([(x0, y0, Z+0.05), (x0+(TW-4)/n, y0, Z+0.05), (x0+(TW-4)/n, y0+(TD-2)/n, Z+0.05), (x0, y0+(TD-2)/n, Z+0.05)],
                   cm(min(v, 0.95)), ec='white', lw=0.15, z=3.2)
def ic_robust(s):
    for k, c in enumerate(('#c9d8ec', '#b2c8e6', '#9ab7df', '#82a5d8')):
        s.box(4+k*0.8, 3+k*0.8, Z+k*2.2, 11, 7, 1.8, top=c, left=shade(c, 0.88), right=shade(c, 0.76), zo=4+k*0.1)
    X, Y = s.p(10, 7, Z+9.5); ax.text(X+1, Y+1.5, '2000–2024', fontsize=4.8, color=BLUE_D, ha='center', zorder=7)
def ic_out(s):
    for k, (h, c) in enumerate(((6, AMBER), (11, '#7fa7dd'), (8, TEAL), (14, '#d06a5a'))):
        s.box(3+k*4, 4.5, Z, 2.8, 2.8, h, top=shade(c, 1.1), left=shade(c, 0.95), right=shade(c, 0.78), zo=4+k*0.1)
    s.line((2, 3, Z), (TW-1, 3, Z), c=EDGE, lw=0.5, z=3.6)


def cap(s, t, sub):
    X, Y = s.p(TW/2, 0, 0); X -= 3; Y = s.oy - 1
    ax.text(X, Y-2.5, t, ha='center', va='top', fontsize=6.6, color=INK, zorder=9, fontweight='bold')
    ax.text(X, Y-6.3, sub, ha='center', va='top', fontsize=5.3, color=Q, style='italic', zorder=9, linespacing=1.15)
def ic_inputs(s):
    X, Y = s.p(6, TD/2, Z)
    for k in range(3): vcyl(X, Y-1+k*3.2, 4.2, 2.4, c0='#e6eefb', c1='#7f9fd0', cap='#f3f7fd', z=4+k*0.5)
    for k, (h, c) in enumerate(((5, AMBER), (8, '#7fa7dd'), (6, TEAL))):
        s.box(12+k*2.4, 4, Z, 1.8, 1.8, h, top=shade(c, 1.1), left=shade(c, 0.95), right=shade(c, 0.78), zo=4.5+k*0.1)
def ic_sheet(s, c):
    s.face([(3, 2, Z+0.05), (17, 2, Z+0.05), (17, 11, Z+0.05), (3, 11, Z+0.05)], 'white', z=3.3)
    s.face([(3, 9, Z+0.06), (17, 9, Z+0.06), (17, 11, Z+0.06), (3, 11, Z+0.06)], shade(c, 1.15), ec=EDGE, z=3.35)
    for y in (3.5, 5.3, 7.1): s.line((4, y, Z+0.07), (16, y, Z+0.07), c='#b8bdc5', lw=0.5, z=3.4)
    for x in (8, 12.5): s.line((x, 2, Z+0.07), (x, 11, Z+0.07), c='#d9dce1', lw=0.4, z=3.4)
    for k, h in enumerate((4, 7, 5)):
        s.box(5+k*4, 4, Z+0.1, 2.2, 2.2, h, top=shade(c, 1.1), left=shade(c, 0.95), right=shade(c, 0.78), zo=4+k*0.1)

TIN, TA, TB, TC, TO = '#eef1f6', '#e9f5ef', '#fbefe6', '#eaf3fb', '#f3eefa'
ti = tile(5, 70, TIN); ic_inputs(ti); cap(ti, 'Inputs for one zone', 'hourly load, CFs, price, g;\nannual costs; Params')
ta = tile(70, 120, TA); ic_lp(ta); cap(ta, 'A  Design, year by year', 'design() on each year alone;\n25 islanded + 40 grid LPs per zone')
tc = tile(70, 20, TC); ic_robust(tc); cap(tc, 'C  Robust design', 'aggregate() 25 years to 3 h,\nthen one design() over all')
tb = tile(135, 70, TB); ic_heat(tb); cap(tb, 'B  Stress test', 'operate(): sizes fixed, CFE free,\nunserved energy at £10,000/MWh')
for y, c, t, sub in ((120, '#7fa7dd', 'design.csv', 'sizes, LCO24/7, CFE,\ncurtailment per year'),
                     (70, '#d06a5a', 'stress.csv', 'unserved MWh and CFE\nfor every test year'),
                     (20, TEAL, 'robust.csv', 'one design for all\n25 weather years')):
    s = tile(205, y, TO); ic_sheet(s, c); cap(s, t, sub)

def arrow(a, b, rad=0.0, c='#8d929a', lw=1.3, ls='-'):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, ls=ls, mutation_scale=8, shrinkA=0, shrinkB=0,
                connectionstyle=f'arc3,rad={rad}'), zorder=1.5)
arrow((25, 84), (55, 126), rad=-0.15); arrow((36, 70), (56, 34), rad=0.1)
arrow((90, 130), (190, 130)); arrow((90, 30), (190, 30)); arrow((155, 80), (190, 80))
arrow((106, 130), (132, 94), rad=0.12); arrow((84, 41), (122, 74), rad=-0.1)
ax.text(124, 114, 'sizes', fontsize=5.6, color=Q, style='italic', ha='left'); ax.text(86, 60, 'sizes', fontsize=5.6, color=Q, style='italic', ha='left')
ax.text(125, 158, 'Every design is judged on weather it was not sized for', ha='center', va='top', fontsize=7.6, fontweight='bold', color=INK)
ax.text(125, -9, 'Zones with identical solar and wind sites are solved once and copied: 14 distinct weather sets cover the 20 zones.',
        ha='center', fontsize=5.6, color=Q, style='italic')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
