"""Fig. O3: cyclic storage balance in gbtea/optimise.py (soc.roll(t=1)), isometric style of the wind and PV chain figures.
Each tile is one time step with the battery's state of charge; the last step feeds the first."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import to_rgb
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#6b7079'
TOP, LEFT, RIGHT = '#f2f3f5', '#d9dce1', '#b8bdc5'
BLUE, TEAL, TEAL_D = '#2c5fa8', '#1f9e7d', '#14765d'
C30, S30 = np.cos(np.pi/6), 0.5
fig, ax = plt.subplots(figsize=(177*MM, 66*MM)); ax.set_xlim(-14, 222); ax.set_ylim(-10, 72); ax.set_aspect('equal'); ax.axis('off')

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

TW, TD, Z = 20, 13, 2.2
def tile(ox, oy, tint='#e9f5ef'):
    s = Iso(ox, oy); s.face([(-1.5, -1.5, 0), (TW+1.5, -1.5, 0), (TW+1.5, TD+1.5, 0), (-1.5, TD+1.5, 0)], '#000', ec='none', z=1, alpha=0.06)
    s.box(0, 0, 0, TW, TD, Z, top=tint, left=shade(tint, 0.86), right=shade(tint, 0.74), zo=2)
    return s
def battery(s, level):
    """Battery cabinet; the teal band on the front face is the state of charge (0-1)."""
    x, y, dx, dy, dz = 4, 3, 12, 7, 11
    s.box(x, y, Z, dx, dy, dz, zo=4)
    s.face([(x+1, y, Z+1), (x+dx-1, y, Z+1), (x+dx-1, y, Z+dz-1), (x+1, y, Z+dz-1)], 'white', z=4.2)
    h = (dz-2)*level
    s.face([(x+1, y, Z+1), (x+dx-1, y, Z+1), (x+dx-1, y, Z+1+h), (x+1, y, Z+1+h)], TEAL, ec='none', z=4.3)
    s.line((x+1, y, Z+1+h), (x+dx-1, y, Z+1+h), c=TEAL_D, lw=0.6, z=4.4)
    X, Y = s.p(x+dx/2, y, Z+dz+0.3); ax.text(X+9, Y+5, f'{level:.0%}', fontsize=5, color=TEAL_D, ha='center', zorder=7)
def cap(s, t, sub):
    X, Y = s.p(TW/2, 0, 0); X -= 3; Y = s.oy - 1
    ax.text(X, Y-2.5, t, ha='center', va='top', fontsize=6.6, color=INK, zorder=9, fontweight='bold')
    ax.text(X, Y-6.6, sub, ha='center', va='top', fontsize=5.2, color=Q, style='italic', zorder=9, linespacing=1.3)

OY = 30; XS = [4 + 39*i for i in range(6)]
LEV = [0.55, 0.70, 0.62, None, 0.38, 0.55]
CAPS = [('hour 0', 'S$_0$ = S$_{T-1}$\n+ Δt(ηC$_0$ − D$_0$/η)'), ('hour 1', 'S$_1$ = S$_0$\n+ Δt(ηC$_1$ − D$_1$/η)'),
        ('hour 2', 'S$_2$ = S$_1$\n+ Δt(ηC$_2$ − D$_2$/η)'), ('…', ''),
        ('hour T−2', 'S$_{T-2}$ = S$_{T-3}$\n+ Δt(…)'), ('hour T−1', 'S$_{T-1}$ = S$_{T-2}$\n+ Δt(…)')]
for i, (x, lv, (t, sub)) in enumerate(zip(XS, LEV, CAPS)):
    s = tile(x, OY, '#e9f5ef' if lv is not None else '#f2f3f5')
    if lv is None:
        X, Y = s.p(TW/2, TD/2, Z); ax.text(X, Y+2, '· · ·', ha='center', va='center', fontsize=11, color=Q, zorder=6)
    else:
        battery(s, lv)
    cap(s, t, sub)

def arrow(a, b, c='#8d929a', lw=1.3, rad=0.0):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=c, lw=lw, mutation_scale=8, shrinkA=0, shrinkB=0,
                connectionstyle=f'arc3,rad={rad}'), zorder=1.5)
for x0, x1 in zip(XS[:-1], XS[1:]): arrow((x0+19, OY+9), (x1-12, OY+9))
# the wrap: last step back to the first, under the captions
yb = 9; xa, xb = XS[-1] + 3, XS[0] + 3
ax.plot([xa, xa, xb], [OY-18, yb, yb], color=BLUE, lw=1.4, zorder=1.5, solid_joinstyle='round')
arrow((xb, yb), (xb, OY-18), c=BLUE, lw=1.4)
ax.text((xa+xb)/2, yb-1.8, 'soc.roll(t=1): the balance for hour 0 starts from the level left at hour T−1',
        ha='center', va='top', fontsize=6.2, color=BLUE, zorder=9)
ax.text(104, 70, 'Storage balance is cyclic: the last time step feeds the first', ha='center', va='top', fontsize=7.4, fontweight='bold', color=INK)
ax.text(104, 64, 'S = energy stored (MWh), C = charging, D = discharging (MW), η = 0.955 each way, Δt = step length (h)',
        ha='center', va='top', fontsize=5.6, color=Q, style='italic')
ax.text(104, 0, 'Storage cannot start full for free. The hydrogen tank follows the same loop (η 0.587 in, 0.50 out);\n'
        'in a 25-year robust design the loop closes once, from the last step of 2024 back to the first of 2000.',
        ha='center', va='top', fontsize=5.6, color=Q, style='italic', linespacing=1.4)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
