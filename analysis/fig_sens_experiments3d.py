"""Fig. S1: the sensitivity experiments (gbtea/flagship.py, run_flagship.py, run_stress.py), isometric style of the method figures."""
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
fig, ax = plt.subplots(figsize=(177*MM, 62*MM)); ax.set_xlim(-16, 290); ax.set_ylim(-6, 60); ax.set_aspect('equal'); ax.axis('off')

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



GREY, GREY_D, RED = '#c9ced6', '#8d939c', '#c8553d'
def slabs(s, n=10, hi=None, x0=3, y0=2, w=14, d=9, h=0.9, gap=0.25, lock=False):
    for k in range(n):
        c = AMBER if k == hi else GREY
        s.box(x0, y0, Z + k*(h+gap), w, d, h, top=shade(c, 1.12), left=shade(c, 0.97), right=shade(c, 0.82), zo=4+k*0.01, lw=0.3)
    return Z + n*(h+gap)
def padlock(X, Y, z=8):
    ax.add_patch(Polygon([(X-2.2, Y), (X+2.2, Y), (X+2.2, Y+3), (X-2.2, Y+3)], fc='#5d6168', ec=INK, lw=0.3, zorder=z))
    th = np.linspace(0, np.pi, 20); ax.plot(X+1.4*np.cos(th), Y+3+1.8*np.sin(th), color='#5d6168', lw=0.9, zorder=z)
def ic_design(s):
    top = slabs(s, hi=6)
    X, Y = s.p(17, 2, Z+6*1.15+0.5); ax.text(X+1.5, Y, 'design year', fontsize=4.6, color='#8a5a00', ha='left', va='center', zorder=9)
    X, Y = s.p(3, 11, top); ax.text(X-4, Y+3, '25 years', fontsize=4.6, color=Q, ha='center', zorder=9)
def ic_stress(s):
    top = slabs(s, hi=6)
    a = s.p(17, 2, Z+6*1.15+0.4)
    for k in (0, 9):
        b = s.p(17, 2, Z+k*1.15+0.4)
        ax.annotate('', (b[0]+1.2, b[1]), (a[0]+1.2, a[1]), arrowprops=dict(arrowstyle='-|>', color='#8a5a00', lw=0.6, mutation_scale=5,
                    connectionstyle=f"arc3,rad={'-0.6' if k == 9 else '0.6'}"), zorder=9)
    ax.text(a[0]+6.5, a[1], 'every\nyear', fontsize=4.6, color='#8a5a00', ha='left', va='center', zorder=9)
    X, Y = s.p(8, 6, top); padlock(X, Y+1.5)
def ic_robust(s):
    n = 10
    for k in range(n):
        c = shade(TEAL, 1.0 + 0.06*(k % 2))
        s.box(3, 2, Z + k*1.1, 14, 9, 1.1, top=shade(c, 1.15), left=c, right=shade(c, 0.8), zo=4+k*0.01, lw=0.25)
    for j in range(1, 7): s.line((3+14*j/7, 2, Z+n*1.1), (3+14*j/7, 11, Z+n*1.1), c='#0e5a46', lw=0.35, z=5)
    X, Y = s.p(17, 2, Z+n*1.1); ax.text(X+1.5, Y-2, '3 h steps', fontsize=4.6, color='#0e5a46', ha='left', zorder=9)
def ic_check(s):
    n = 10
    for k in range(n):
        c = shade(TEAL, 1.0 + 0.06*(k % 2))
        s.box(3, 2, Z + k*1.1, 14, 9, 1.1, top=shade(c, 1.15), left=c, right=shade(c, 0.8), zo=4+k*0.01, lw=0.25)
    for j in range(1, 21): s.line((3+14*j/21, 2, Z+n*1.1), (3+14*j/21, 11, Z+n*1.1), c='#0e5a46', lw=0.2, z=5)
    X, Y = s.p(10, 6.5, Z+n*1.1); padlock(X, Y+1.5)
    X, Y = s.p(17, 2, Z+n*1.1); ax.text(X+1.5, Y-2, '1 h steps', fontsize=4.6, color='#0e5a46', ha='left', zorder=9)
def ic_adder(s):
    X0, Y0 = s.p(4, 6, Z); ax.plot([X0, X0], [Y0, Y0+15], color='#5a5f66', lw=0.9, zorder=5)
    for d in (-1, 1): ax.plot([X0, X0+d*3], [Y0+15, Y0+12], color='#5a5f66', lw=0.4, zorder=5); ax.plot([X0, X0+d*2.5], [Y0, Y0+9], color='#9aa0a8', lw=0.3, zorder=4)
    ax.plot([X0-3.5, X0+3.5], [Y0+12.5, Y0+12.5], color='#5a5f66', lw=0.6, zorder=5)
    for k, (h, lab) in enumerate(((5, '£30'), (8.3, '£50'), (11.6, '£70'))):
        c = BLUE if k == 1 else BLUE_L
        s.box(12, 1.5+k*3.6, Z, 2.4, 2.4, h, top=shade(c, 1.2), left=c, right=shade(c, 0.8), zo=4.5-k*0.1)
        X, Y = s.p(14.4, 1.5+k*3.6, Z+h); ax.text(X+0.8, Y-0.8, lab, fontsize=4.4, color=BLUE_D if k == 1 else Q, ha='left', va='center', zorder=9,
                                                      fontweight='bold' if k == 1 else 'normal')

ST = [(ic_design, 'Design each year', 'least-cost design for\none weather year\n(25 islanded, 10 grid)', '#fdf3e2'),
      (ic_stress, 'Cross-year stress', 'capacities fixed; operate\non every year; record\nunserved load or CFE', '#fbefe6'),
      (ic_robust, 'Robust design', 'one design over 2000–2024\nstacked, 3 h steps,\nislanded, 100% CFE', '#e9f5ef'),
      (ic_check, 'Hourly check', 'robust design fixed;\noperate each year\nat 1 h resolution', '#e9f5ef'),
      (ic_adder, 'Grid adder', 'grid designs re-solved\nwith £30 and £70/MWh\n(central £50)', '#eaf3fb')]
XS = [6 + 60*i for i in range(5)]
for n, (x, (f, a, b, c)) in enumerate(zip(XS, ST), 1):
    s = tile(x, 14, c); f(s); cap(s, n, a, b)
def arrow(a, b, c='#8d929a', lw=1.3, ls='-'):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, mutation_scale=8, shrinkA=0, shrinkB=0, ls=ls), zorder=1.5)
arrow((XS[0]+20, 26), (XS[1]-14, 26)); arrow((XS[2]+20, 26), (XS[3]-14, 26))
ax.text(137, 58, 'Sensitivity experiments run on the optimisation model', ha='center', fontsize=7.2, color=INK, fontweight='bold', va='top')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
