"""Fig. O1: the system the optimisation LP sizes (gbtea/optimise.py), isometric style of Fig. 2, annotated with the
LP's decision variables, annual costs (2025 data, GBP2024, 7%) and efficiencies. Built from fig2_iso.py."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, Circle
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 7})
MM = 1/25.4
INK, Q = '#1d1d1f', '#55565a'
TOP, LEFT, RIGHT, EDGE = '#f2f3f5', '#d9dce1', '#b8bdc5', '#6b7079'
BLUE, BLUE_D, BLUE_L = '#2c5fa8', '#1d3f73', '#7fa7dd'
TEAL, TEAL_D = '#1f9e7d', '#14765d'
H2C, PWR = '#1f9e7d', '#4a4d52'
fig, ax = plt.subplots(figsize=(177*MM, 124*MM))
ax.set_xlim(0, 206); ax.set_ylim(-6, 140); ax.set_aspect('equal'); ax.axis('off')
C30, S30 = np.cos(np.pi/6), 0.5

class Iso:
    def __init__(s, ox, oy, k=1.0): s.ox, s.oy, s.k = ox, oy, k
    def p(s, x, y, z): return (s.ox + s.k*(x - y)*C30, s.oy + s.k*((x + y)*S30 + z))
    def face(s, pts, fc, ec=EDGE, lw=0.45, z=3):
        ax.add_patch(Polygon([s.p(*q) for q in pts], closed=True, fc=fc, ec=ec, lw=lw, zorder=z, joinstyle='round'))
    def box(s, x, y, z, dx, dy, dz, top=TOP, left=LEFT, right=RIGHT, zo=3, lw=0.45):
        s.face([(x, y, z), (x, y+dy, z), (x, y+dy, z+dz), (x, y, z+dz)], left, lw=lw, z=zo)          # x = x0 face
        s.face([(x, y, z), (x+dx, y, z), (x+dx, y, z+dz), (x, y, z+dz)], right, lw=lw, z=zo)         # y = y0 face
        s.face([(x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)], top, lw=lw, z=zo)
    def line(s, a, b, c='#8d929a', lw=0.4, z=4):
        P, R = s.p(*a), s.p(*b); ax.plot([P[0], R[0]], [P[1], R[1]], color=c, lw=lw, zorder=z, solid_capstyle='round')
    def shadow(s, x, y, dx, dy, pad=2):
        s.face([(x-pad, y-pad, 0), (x+dx+pad, y-pad, 0), (x+dx+pad, y+dy+pad, 0), (x-pad, y+dy+pad, 0)],
               '#000000', ec='none', z=1); ax.patches[-1].set_alpha(0.07)

def vcyl(cx, cy, r, h, col=('#eef0f3', '#c3c8cf', '#9aa1ab'), cap='#f7f8f9', z=3, band=None):
    e = 0.58*r
    n = 14
    for i in range(n):                                 # shaded side strips
        t = i/(n-1); c = np.interp(t, [0, 0.35, 1], [0, 0, 1])
        rgb = [np.interp(t, [0, .35, 1], [int(col[0][j:j+2], 16), int(col[1][j:j+2], 16), int(col[2][j:j+2], 16)])/255 for j in (1, 3, 5)]
        x0 = cx - r + 2*r*i/n
        ax.add_patch(Polygon([(x0, cy), (x0+2*r/n+0.05, cy), (x0+2*r/n+0.05, cy+h), (x0, cy+h)], fc=rgb, ec='none', zorder=z))
    ax.add_patch(Ellipse((cx, cy), 2*r, 2*e, fc=col[2], ec='none', zorder=z-0.1))
    ax.plot([cx-r, cx-r], [cy, cy+h], color=EDGE, lw=0.45, zorder=z+0.1); ax.plot([cx+r, cx+r], [cy, cy+h], color=EDGE, lw=0.45, zorder=z+0.1)
    th = np.linspace(np.pi, 2*np.pi, 40); ax.plot(cx+r*np.cos(th), cy+e*np.sin(th), color=EDGE, lw=0.45, zorder=z+0.1)
    if band: ax.add_patch(Polygon([(cx-r, cy+h*0.55), (cx+r, cy+h*0.55), (cx+r, cy+h*0.7), (cx-r, cy+h*0.7)], fc=band, ec='none', zorder=z+0.05))
    ax.add_patch(Ellipse((cx, cy+h), 2*r, 2*e, fc=cap, ec=EDGE, lw=0.45, zorder=z+0.2))

def label(x, y, t, sub=None, ha='center', size=7.5):
    ax.text(x, y, t, ha=ha, va='top', fontsize=size, color=INK, zorder=9)
    if sub: ax.text(x, y-3.6, sub, ha=ha, va='top', fontsize=6, color=Q, style='italic', zorder=9)

# ---------------- grid pylons ----------------
def pylon(bx, by, h=26, w=7):
    c = '#3a3d42'; lw = 0.6
    L = [(bx-w/2, by), (bx-1.0, by+h)]; R = [(bx+w/2, by), (bx+1.0, by+h)]
    ax.plot(*zip(*L), color=c, lw=lw*1.3, zorder=4); ax.plot(*zip(*R), color=c, lw=lw*1.3, zorder=4)
    lv = np.linspace(0, 1, 7)
    for a, b in zip(lv[:-1], lv[1:]):
        xl0, xr0 = bx-w/2+(w/2-1)*a, bx+w/2-(w/2-1)*a; xl1, xr1 = bx-w/2+(w/2-1)*b, bx+w/2-(w/2-1)*b
        ax.plot([xl0, xr1], [by+h*a, by+h*b], color=c, lw=lw*0.6, zorder=4); ax.plot([xr0, xl1], [by+h*a, by+h*b], color=c, lw=lw*0.6, zorder=4)
        ax.plot([xl1, xr1], [by+h*b, by+h*b], color=c, lw=lw*0.6, zorder=4)
    for yy, half in ((0.62, 7), (0.80, 5.5)):
        y = by+h*yy; ax.plot([bx-half, bx+half], [y, y], color=c, lw=lw*1.2, zorder=4)
        ax.plot([bx-half, bx-1.6], [y, y+2.2], color=c, lw=lw*0.6, zorder=4); ax.plot([bx+half, bx+1.6], [y, y+2.2], color=c, lw=lw*0.6, zorder=4)
        for sx in (-half, half): ax.plot([bx+sx, bx+sx], [y, y-1.6], color=c, lw=lw, zorder=4)
    ax.plot([bx-1, bx, bx+1], [by+h, by+h+2, by+h], color=c, lw=lw, zorder=4)
    return [(bx+s, by+h*yy-1.6) for yy, half in ((0.62, 7), (0.80, 5.5)) for s in (-half, half)]
pa = pylon(14, 108); pb = pylon(42, 112)
for a, b in zip(pa, pb):
    xs = np.linspace(a[0], b[0], 30); ys = np.linspace(a[1], b[1], 30) - 2.2*np.sin(np.linspace(0, np.pi, 30))
    ax.plot(xs, ys, color='#3a3d42', lw=0.35, zorder=3)
    ax.plot([a[0]-8, a[0]], [a[1]+0.8, a[1]], color='#3a3d42', lw=0.35, zorder=3)
label(27, 104.5, 'GB grid (grid mode)', 'M$_t$ at MIP + £50, X$_t$ at MIP (≤ 20%)')

# ---------------- PV arrays ----------------
def pv(ox, oy, tracker=False):
    s = Iso(ox, oy, 0.8); s.shadow(0, 0, 26, 12, pad=1)
    for r in range(2):
        y0 = r*7.5
        tilt = 0.55 if not tracker else 0.0
        z0 = 3.0
        A, B = (0, y0, z0), (24, y0, z0)
        if tracker:   # E-W tilted modules on N-S torque tube: render as row of tilted panels
            for k in range(6):
                x = 1 + k*3.9
                s.face([(x, y0, z0+1.6), (x+3.4, y0, z0+0.2), (x+3.4, y0+5, z0+0.2), (x, y0+5, z0+1.6)], BLUE, ec='#dfe6f0', lw=0.35, z=4)
                s.line((x+1.7, y0, z0+0.9), (x+1.7, y0+5, z0+0.9), c=BLUE_L, lw=0.3, z=5)
            s.line((0, y0+2.5, z0+0.9), (25, y0+2.5, z0+0.9), c='#6b7079', lw=0.7, z=3.5)
            for x in (2, 12, 22): s.line((x, y0+2.5, 0), (x, y0+2.5, z0+0.9), c='#6b7079', lw=0.7, z=3)
        else:
            s.face([(0, y0, z0), (24, y0, z0), (24, y0+5, z0+5*tilt+1), (0, y0+5, z0+5*tilt+1)], BLUE, ec='#dfe6f0', lw=0.4, z=4)
            for k in range(1, 8): s.line((24*k/8, y0, z0), (24*k/8, y0+5, z0+5*tilt+1), c=BLUE_L, lw=0.3, z=5)
            s.line((0, y0+2.5, z0+(5*tilt+1)/2), (24, y0+2.5, z0+(5*tilt+1)/2), c=BLUE_L, lw=0.3, z=5)
            for x in (1.5, 22.5):
                s.line((x, y0, 0), (x, y0, z0), c='#6b7079', lw=0.7, z=3); s.line((x, y0+5, 0), (x, y0+5, z0+5*tilt+1), c='#6b7079', lw=0.7, z=3)
pv(16, 76); label(24, 74, 'PV, fixed 35°', 'K$_{fix}$ × cf$_{fix}$(t); £48.4k/MW-yr')
pv(16, 47, tracker=True); label(24, 45, 'PV, single-axis', 'K$_{trk}$ × cf$_{trk}$(t); £55.5k/MW-yr')

# ---------------- wind turbine ----------------
def turbine(bx, by, H=30):
    ax.add_patch(Ellipse((bx, by), 9, 2.2, fc='#000', alpha=0.07, ec='none', zorder=1))
    ax.add_patch(Polygon([(bx-1.3, by), (bx+1.3, by), (bx+0.55, by+H), (bx-0.55, by+H)], fc='#f4f5f7', ec=EDGE, lw=0.45, zorder=4))
    ax.add_patch(Polygon([(bx+0.25, by), (bx+1.3, by), (bx+0.55, by+H), (bx+0.12, by+H)], fc=LEFT, ec='none', zorder=4.1))
    s = Iso(bx, by+H, 1.0); s.box(-0.8, -0.9, -0.9, 4.2, 1.8, 1.9, zo=5)
    hx, hy = s.p(-0.8, 0, 0.05)
    for ang in (95, 215, 335):
        a = np.radians(ang); L = H*0.55; n = np.array([-np.sin(a), np.cos(a)]); d = np.array([np.cos(a), np.sin(a)]*np.array([1, 1])); b = np.array([hx, hy])
        ax.add_patch(Polygon([b+0.8*n, b+0.25*L*d+1.0*n, b+L*d, b-0.3*n], fc='#fafafa', ec=EDGE, lw=0.4, zorder=6))
    ax.add_patch(Circle((hx, hy), 0.95, fc=TOP, ec=EDGE, lw=0.45, zorder=7))
turbine(26, 5, H=18); label(44, 19, 'Wind, V126', 'K$_w$ × cf$_w$(t) × 0.86\n£112.5k/MW-yr', ha='left')

# ---------------- switchboard (site AC bus) ----------------
sb = Iso(84, 66, 1.0); sb.shadow(0, 0, 8, 6)
sb.box(0, 0, 0, 8, 6, 15, top=TOP, left=LEFT, right=RIGHT)
for k in range(5): sb.line((1.2+k*1.3, 0, 3), (1.2+k*1.3, 0, 12), c='#9aa0a8', lw=0.35)
for i, c in enumerate(('#2fb36b', '#e0a91f', '#2fb36b')):
    P = sb.p(0, 1.5+i*1.4, 12.5); ax.add_patch(Circle(P, 0.45, fc=c, ec='none', zorder=6))
label(100, 64, 'AC bus', 'hourly energy balance', ha='left')

# ---------------- battery ----------------
bt = Iso(90, 30, 1.0); bt.shadow(0, 0, 22, 8)
for x0 in (0, 11.5):
    bt.box(x0, 0, 0, 10.5, 8, 9, top=TOP, left=LEFT, right=RIGHT)
    for k in range(1, 4): bt.line((x0+k*10.5/4, 0, 0.8), (x0+k*10.5/4, 0, 8.2), c='#9aa0a8', lw=0.35)
for k, (a, b) in enumerate([((0, 2.0, 2.5), (0, 6.0, 2.5)), ((0, 6.0, 2.5), (0, 6.0, 6.0)), ((0, 6.0, 6.0), (0, 2.0, 6.0)), ((0, 2.0, 6.0), (0, 2.0, 2.5))]):
    bt.line(a, b, c=TEAL_D, lw=0.8, z=5)
bt.face([(0, 2.4, 2.9), (0, 4.8, 2.9), (0, 4.8, 5.6), (0, 2.4, 5.6)], TEAL, ec='none', z=5)
bt.face([(0, 6.0, 3.7), (0, 6.6, 3.7), (0, 6.6, 4.8), (0, 6.0, 4.8)], TEAL_D, ec='none', z=5)
label(103, 26, 'Battery', 'E$_b$ (MWh), P$_b$ (MW); η 0.955 each way\n£18.6k/MWh-yr + £34.5k/MW-yr')

# ---------------- hydrogen chain ----------------
el = Iso(118, 98, 1.0); el.shadow(0, 0, 12, 7)
el.box(0, 0, 0, 12, 7, 8, top=TOP, left=LEFT, right=RIGHT)
for k in range(4): el.line((1.5+k*2.8, 0, 1.5), (1.5+k*2.8, 0, 6.5), c='#9aa0a8', lw=0.35)
for (x, y) in ((3, 3.5), (8.5, 3.5)):
    P = el.p(x, y, 8); vcyl(P[0], P[1]-0.6, 1.4, 4.5, z=5, band=TEAL)
label(122, 95, 'Electrolyser', 'K$_{el}$ (MW in), η 0.587\n£236k/MW-yr')
for i, x in enumerate((150, 156.5, 163)):
    vcyl(x, 94 + 1.6*i, 2.8, 12, band=TEAL, z=4-0.1*i)
ax.text(163, 113, '', fontsize=1)
label(169, 113, 'H$_2$ tank', 'E$_h$ (MWh H$_2$)\n£5.3k/MWh-yr', ha='left')
fc = Iso(160, 68, 1.0); fc.shadow(0, 0, 10, 7)
fc.box(0, 0, 0, 10, 7, 8, top=TOP, left=LEFT, right=RIGHT)
for k in range(5): fc.line((0, 1+k*1.2, 2), (0, 1+k*1.2, 6.5), c='#9aa0a8', lw=0.35)
P = fc.p(5, 0, 4); ax.text(P[0], P[1], 'FC', fontsize=6.5, fontweight='bold', color=TEAL_D, ha='center', va='center', zorder=6)
label(173, 79, 'Fuel cell', 'K$_{fc}$ (MW out), η 0.50\n£256k/MW-yr', ha='left')

# ---------------- data centre ----------------
dc = Iso(162, 22, 1.0); dc.shadow(0, 0, 30, 20, pad=2.5)
dc.box(0, 0, 0, 30, 20, 13, top=TOP, left=LEFT, right=RIGHT)
for k in range(6): dc.face([(2+k*4.6, 0, 7), (5.4+k*4.6, 0, 7), (5.4+k*4.6, 0, 10.5), (2+k*4.6, 0, 10.5)], '#c9d8ec', ec=EDGE, lw=0.3, z=4)
dc.face([(12, 0, 0), (17, 0, 0), (17, 0, 5), (12, 0, 5)], '#6b7079', ec=EDGE, lw=0.3, z=4)
# server racks visible through open left wall
for j in range(3):
    for i in range(2):
        dc.box(-0.01, 2+j*5.6, 1.0+i*0, 0.01, 4.4, 10.5, top=BLUE_D, left=BLUE_D, right=BLUE_D, zo=4, lw=0.3)
        for r in range(6): dc.line((0, 2.4+j*5.6, 2+r*1.5), (0, 6.0+j*5.6, 2+r*1.5), c='#62a0ff', lw=0.5, z=5)
# rooftop cooling units with fans
for i in range(3):
    dc.box(3+i*9, 5, 13, 7, 9, 2.4, top='#eef0f3', zo=5)
    cx, cy = dc.p(6.5+i*9, 9.5, 15.4); ax.add_patch(Ellipse((cx, cy), 6.0, 3.4, fc='#5a5f66', ec=EDGE, lw=0.3, zorder=6))
    ax.add_patch(Ellipse((cx, cy), 1.0, 0.6, fc='#c8ccd2', ec='none', zorder=7))
    for a in (0, 60, 120): 
        t = np.radians(a); ax.plot([cx-2.6*np.cos(t), cx+2.6*np.cos(t)], [cy-1.45*np.sin(t), cy+1.45*np.sin(t)], color='#8d929a', lw=0.4, zorder=6.5)
label(176, 18, 'Data-centre load L$_t$', '5 MW IT × PUE(t), met in every hour')

# ---------------- flows ----------------
def flow(a, b, rad=0.0, c=PWR, both=False, ls='-', lw=1.0):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle=('<|-|>' if both else '-|>'), color=c, lw=lw, ls=ls, mutation_scale=7,
                shrinkA=0, shrinkB=0, connectionstyle=f'arc3,rad={rad}'), zorder=2)
flow((48, 120), (84, 80), rad=-0.25, both=True, ls=(0, (3, 2)))
flow((34, 85), (83, 74), rad=-0.1)
flow((34, 57), (83, 70), rad=0.15)
flow((38, 21), (84, 66.5), rad=0.3)
flow((94, 82), (162, 50), rad=-0.35, c=BLUE, lw=1.4)                        # to data centre
flow((91, 65.5), (97, 55.5), rad=0.0, both=True)                                 # battery
flow((96, 82), (116, 102), rad=-0.2)                                          # to electrolyser
flow((136, 104), (146, 103), c=H2C)                                           # H2 to tanks
flow((158, 84.5), (163, 79), rad=0.0, c=H2C)                                  # tanks to fuel cell
flow((159, 73), (99, 76), rad=0.15)                                           # fuel cell power back
ax.text(56, 117, 'import / export', fontsize=5.8, color=Q, style='italic', rotation=-22, zorder=9)
# legend
lx, ly = 4, 4
for i, (c, ls, t) in enumerate(((PWR, '-', 'electricity'), (BLUE, '-', 'supply to load'), (H2C, '-', 'hydrogen'), (PWR, (0, (3, 2)), 'grid exchange (grid cases only)'))):
    ax.plot([lx+i*0, lx+6], [ly+i*-0+0]*2, alpha=0)
ax.text(103, -3.5, 'Every hour: PV + wind + discharge + fuel cell + import ≥ load + charge + electrolysis + export; any surplus is curtailed.\n'
        'Costs are annualised capex plus fixed O&M. Dashed: grid mode only; imports count against the hourly carbon-free target.',
        ha='center', fontsize=5.8, color=Q, style='italic', linespacing=1.4)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
