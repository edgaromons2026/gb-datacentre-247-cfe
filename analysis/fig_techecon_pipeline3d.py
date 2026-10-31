"""Fig. T1: cost data pipeline (gbtea/costs.py and optimise.unit_costs), isometric style of the wind and PV chain figures."""
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
fig, ax = plt.subplots(figsize=(177*MM, 62*MM)); ax.set_xlim(-16, 290); ax.set_ylim(-6, 56); ax.set_aspect('equal'); ax.axis('off')

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


def ic_db(s):
    X, Y = s.p(TW/2, TD/2, Z)
    for k in range(3): vcyl(X, Y-1.5+k*3.6, 5.2, 2.8, c0='#e6eefb', c1='#7f9fd0', cap='#f3f7fd', z=4+k*0.5)
    ax.text(X, Y+12.8, 'PyPSA', ha='center', fontsize=5, color=BLUE_D, fontweight='bold', zorder=7)
def ic_infl(s):
    for k, h in enumerate((5, 6, 7.5, 9.5, 11)):
        s.box(2.5+k*3.2, 5, Z, 2.4, 2.4, h, top=shade(WARM, 1.25), left=shade(WARM, 1.05), right=shade(WARM, 0.85), zo=4+k*0.1)
    X, Y = s.p(TW-2, 5, Z+12); ax.text(X+1, Y+1, 'HICP', fontsize=4.8, color=WARM, ha='left', zorder=7)
def coin(X, Y, sym, c):
    for k in range(4): ax.add_patch(Ellipse((X, Y+k*0.9), 7, 3.4, fc=shade(c, 0.85), ec=EDGE, lw=0.3, zorder=5+k*0.01))
    ax.add_patch(Ellipse((X, Y+3.6), 7, 3.4, fc=shade(c, 1.15), ec=EDGE, lw=0.35, zorder=5.1))
    ax.text(X, Y+3.6, sym, ha='center', va='center', fontsize=6, color=INK, fontweight='bold', zorder=6)
def ic_fx(s):
    X, Y = s.p(5, 6, Z); coin(X, Y, '€', '#c9d8ec')
    X2, Y2 = s.p(15, 6, Z); coin(X2, Y2+1, '£', '#f6d58a')
def ic_ann(s):
    s.box(2, 4, Z, 3, 3, 13, top=shade(BLUE, 1.2), left=shade(BLUE, 1.0), right=shade(BLUE, 0.8), zo=4)
    for k in range(6):
        s.box(7+k*1.9, 4.5, Z, 1.4, 1.4, 3, top=shade(TEAL, 1.2), left=shade(TEAL, 1.0), right=shade(TEAL, 0.8), zo=4.2+k*0.01)
    X, Y = s.p(TW-2, 4, Z+8); ax.text(X+1, Y, 'r = 7%', fontsize=4.8, color=BLUE_D, ha='left', zorder=7)
def ic_lp(s):
    s.box(5, 3, Z, 10, 8, 10, top='#dbe7f8', left='#b9cff0', right='#94b3e3', zo=4)
    nodes = [(5, 6, Z+10), (10, 3, Z+10), (15, 7, Z+10), (10, 11, Z+10), (10, 7, Z+10)]
    for a in nodes[:4]: s.line(a, nodes[4], c=BLUE_D, lw=0.6, z=5)
    for a in nodes: X, Y = s.p(*a); ax.add_patch(Circle((X, Y), 0.9, fc=BLUE_D, ec='white', lw=0.3, zorder=6))
    X, Y = s.p(10, 3, Z+5); ax.text(X+1, Y-0.5, 'LP', fontsize=6.5, fontweight='bold', color=BLUE_D, ha='center', va='center', zorder=6)

ST = [(ic_db, 'Technology data', 'PyPSA technology-data\nv0.15.0; cost years\n2025, 2030 … 2050', '#eef1f6'),
      (ic_infl, 'To 2024 euros', 'each row × HICP$_{2024}$ /\nHICP$_{currency\\ year}$\n(euro area, Eurostat)', '#fbefe6'),
      (ic_fx, 'Euros to pounds', '× 0.8466 £/€\n(ECB 2024 average)', '#fdf3e2'),
      (ic_ann, 'Annual cost', 'capex × annuity(7%, life)\n+ fixed O&M; per MW\nor per MWh each year', '#eaf3fb'),
      (ic_lp, 'Into the LP', 'c$_k$ in the objective;\nVOM on output; η in\nthe storage balances', '#e9f5ef')]
XS = [6 + 60*i for i in range(5)]
for n, (x, (f, a, b, c)) in enumerate(zip(XS, ST), 1):
    s = tile(x, 14, c); f(s); cap(s, n, a, b)
def arrow(a, b, c='#8d929a', lw=1.3):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, mutation_scale=8, shrinkA=0, shrinkB=0), zorder=1.5)
for x0, x1 in zip(XS[:-1], XS[1:]): arrow((x0+20, 26), (x1-14, 26))
ax.text(137, 54, 'From published technology costs to the annual cost of each asset in the optimisation', ha='center', fontsize=7.2, color=INK, fontweight='bold', va='top')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
