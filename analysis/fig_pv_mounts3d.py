"""PV mount geometry in the isometric style of Figs 1-2: (a) fixed 35 deg south, (b) single-axis N-S tracker,
(c) dual-axis tracker. Dimensions follow gbtea/config.py (collector 1.2 m, pitch 3.0 m, GCR 0.40, axis 1.5 m)."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib.colors import to_rgb
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#6b7079'
BLUE, BLUE_D, BLUE_L, AMBER, WARM = '#2c5fa8', '#1d3f73', '#7fa7dd', '#f2a516', '#c8553d'
C30, S30 = np.cos(np.pi/6), 0.5
fig, ax = plt.subplots(figsize=(177*MM, 78*MM)); ax.set_xlim(0, 300); ax.set_ylim(-12, 106); ax.set_aspect('equal'); ax.axis('off')

def shade(c, f): return tuple(min(1, max(0, v*f)) for v in to_rgb(c))
class Iso:
    """x = east, y = north, z = up; k = drawing units per metre."""
    def __init__(s, ox, oy, k): s.ox, s.oy, s.k = ox, oy, k
    def p(s, x, y, z): return (s.ox + s.k*(x - y)*C30, s.oy + s.k*((x + y)*S30 + z))
    def poly(s, pts, fc, ec=EDGE, lw=0.4, z=3, alpha=1):
        ax.add_patch(Polygon([s.p(*q) for q in pts], closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, joinstyle='round'))
    def line(s, a, b, c=EDGE, lw=0.5, z=4, ls='-'):
        P, R = s.p(*a), s.p(*b); ax.plot([P[0], R[0]], [P[1], R[1]], color=c, lw=lw, zorder=z, ls=ls, solid_capstyle='round')
    def text(s, x, y, z, t, **kw): X, Y = s.p(x, y, z); ax.text(X, Y, t, zorder=9, **kw)

def panel(s, corners, z, n_cells=(6, 2)):
    """Module surface with a cell grid; corners in order a-b-c-d (a-b along the row)."""
    a, b, c, d = map(np.array, corners)
    s.poly([a, b, c, d], BLUE, ec='#dfe6f0', lw=0.5, z=z)
    for k in range(1, n_cells[0]):
        t = k/n_cells[0]; s.line(a+(b-a)*t, d+(c-d)*t, c=BLUE_L, lw=0.3, z=z+0.01)
    for k in range(1, n_cells[1]):
        t = k/n_cells[1]; s.line(a+(d-a)*t, b+(c-b)*t, c=BLUE_L, lw=0.3, z=z+0.01)

def ground(s, x0, x1, y0, y1):
    s.poly([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], '#eef3e8', ec='#cdd6c4', lw=0.4, z=1)

def sun(X, Y, r=4.2):
    for a in np.linspace(0, 2*np.pi, 12, endpoint=False):
        ax.plot([X+1.35*r*np.cos(a), X+1.8*r*np.cos(a)], [Y+1.35*r*np.sin(a), Y+1.8*r*np.sin(a)], color=AMBER, lw=0.8, zorder=8)
    ax.add_patch(Circle((X, Y), r, fc='#ffd36b', ec=AMBER, lw=0.6, zorder=8))

def compass(s, x, y):
    for (dx, dy, t) in ((0, 1.6, 'N'), (1.6, 0, 'E')):
        s.line((x, y, 0), (x+dx, y+dy, 0), c=Q, lw=0.6, z=6)
        s.text(x+dx*1.45, y+dy*1.45, 0, t, fontsize=5.5, color=Q, ha='center', va='center')

def title(X, t, sub):
    ax.text(X, 104, t, ha='center', va='top', fontsize=7.4, fontweight='bold', color=INK)
    ax.text(X, 97, sub, ha='center', va='top', fontsize=5.6, color=Q, style='italic', linespacing=1.2)

L, PITCH, H_AX, TILT = 1.2, 3.0, 1.5, np.radians(35)
K = 6.2                                                         # drawing units per metre

# ---------- (a) fixed tilt: rows run east-west, face south (towards -y) ----------
s = Iso(62, 14, K); ROW = 5.0
ground(s, -0.6, ROW+0.6, -0.8, 3*PITCH-0.6)
for j in (2, 1, 0):                                             # back rows first
    y0 = j*PITCH; zlo = H_AX - 0.5*L*np.sin(TILT); dy = L*np.cos(TILT); dz = L*np.sin(TILT)
    for x in (0.3, ROW-0.3):
        s.line((x, y0, 0), (x, y0, zlo), lw=0.7, z=3+j); s.line((x, y0+dy, 0), (x, y0+dy, zlo+dz), lw=0.7, z=3+j)
    panel(s, [(0, y0, zlo), (ROW, y0, zlo), (ROW, y0+dy, zlo+dz), (0, y0+dy, zlo+dz)], z=4+j, n_cells=(8, 2))
# pitch and collector dimensions (on the west end)
s.line((-0.35, 0, 0.02), (-0.35, PITCH, 0.02), c=WARM, lw=0.6, z=8)
for yy in (0, PITCH): s.line((-0.5, yy, 0.02), (-0.2, yy, 0.02), c=WARM, lw=0.6, z=8)
s.text(-0.6, PITCH/2, 0, 'pitch 3.0 m', fontsize=5.4, color=WARM, ha='right', va='center')
y0 = 0; zlo = H_AX - 0.5*L*np.sin(TILT)
s.text(-0.9, 0.5*L*np.cos(TILT), zlo+0.7, '1.2 m', fontsize=5.4, color=WARM, ha='right', va='bottom')
s.line((ROW, 0, zlo), (ROW+1.1, 0, zlo), c=Q, lw=0.4, z=8, ls=(0, (2, 1.5)))
th = np.linspace(0, TILT, 12); r = 0.8
P = [s.p(ROW+0.05, r*np.cos(t), zlo+r*np.sin(t)) for t in th]; ax.plot(*zip(*P), color=WARM, lw=0.6, zorder=8)
s.text(ROW+0.25, 0.9, zlo+0.25, '35°', fontsize=5.6, color=WARM, ha='left', va='bottom')
title(52, 'a  Fixed tilt', '35° facing south\nGCR = 1.2 m / 3.0 m = 0.40')
sun(96, 76, r=3.4)
ax.text(96, 66.5, 'noon sun\n(high, south)', fontsize=5.2, color='#a06a00', ha='center', va='top', style='italic', zorder=9)

# ---------- (b) single-axis tracker: axes run north-south, rotate east-west ----------
s = Iso(150, 14, K); ROWL = 5.4; ROT = np.radians(40)           # afternoon: panels turned to face west
ground(s, -1.0, 2*PITCH+1.0, -0.6, ROWL+0.6)
for i in (2, 1, 0):
    x0 = i*PITCH; hx = 0.5*L*np.cos(ROT); hz = 0.5*L*np.sin(ROT)
    for y in (0.3, ROWL/2, ROWL-0.3): s.line((x0, y, 0), (x0, y, H_AX), lw=0.8, z=3+i*0.1)
    panel(s, [(x0-hx, 0, H_AX-hz), (x0-hx, ROWL, H_AX-hz), (x0+hx, ROWL, H_AX+hz), (x0+hx, 0, H_AX+hz)], z=4+(2-i)*0.1, n_cells=(8, 2))
    s.line((x0, -0.3, H_AX), (x0, ROWL+0.3, H_AX), c=INK, lw=0.9, z=3.9+(2-i)*0.1)
# rotation arc and labels on the front tracker
x0 = 0; R = 0.95
th = np.linspace(np.radians(-60), np.radians(60), 30)
P = [s.p(x0+R*np.cos(t+np.pi/2)*0+R*np.sin(t), -0.35, H_AX+R*np.cos(t)) for t in th]
ax.plot(*zip(*P), color=WARM, lw=0.6, zorder=8)
for t in (th[0], th[-1]):
    s.line((x0, -0.35, H_AX), (x0+R*np.sin(t), -0.35, H_AX+R*np.cos(t)), c=WARM, lw=0.4, z=8, ls=(0, (2, 1.5)))
s.text(x0-0.3, -0.9, 0.2, '±60°', fontsize=5.6, color=WARM, ha='right', va='bottom')
s.text(2*PITCH, ROWL+0.5, H_AX+0.6, 'N–S axis', fontsize=5.4, color=INK, ha='left', va='bottom')
s.line((2*PITCH+0.6, 0, 0), (2*PITCH+0.6, 0, H_AX), c=WARM, lw=0.6, z=8)
s.text(2*PITCH+0.75, 0, 0.55, '1.5 m', fontsize=5.4, color=WARM, ha='left', va='center')
title(150, 'b  Single-axis tracking', 'N–S axis, ±60°, no backtracking\npitch 3.0 m, GCR 0.40')
sun(124, 80, r=3.4)
ax.text(124, 70.5, 'afternoon\nsun (west)', fontsize=5.2, color='#a06a00', ha='center', va='top', style='italic', zorder=9)

# ---------- (c) dual-axis tracker: normal points at the sun ----------
s = Iso(248, 18, K)
ground(s, -1.2, 4.6, -1.2, 4.6)
az, el = np.radians(200), np.radians(38)                        # south-south-west sun, early afternoon
n = np.array([np.sin(az)*np.cos(el), np.cos(az)*np.cos(el), np.sin(el)])
u = np.cross([0, 0, 1], n); u /= np.linalg.norm(u); v = np.cross(n, u)
for (cx, cy), zz in (((3.4, 3.4), 3), ((0, 0), 5)):
    c = np.array([cx, cy, 1.9]); S = 0.95
    s.line((cx, cy, 0), (cx, cy, 1.9), c=EDGE, lw=1.4, z=zz)
    corners = [c - S*u - S*v, c + S*u - S*v, c + S*u + S*v, c - S*u + S*v]
    panel(s, corners, z=zz+0.5, n_cells=(4, 4))
title(250, 'c  Dual-axis tracking', 'panel faces the sun:\ntilt = zenith, azimuth = solar azimuth')
sun(284, 66, r=3.4)
ax.text(284, 56.5, 'sun', fontsize=5.2, color='#a06a00', ha='center', va='top', style='italic', zorder=9)
s.text(-1.2, 4.6, -1.0, 'widely spaced:\nno row shading', fontsize=5.2, color=Q, ha='right', va='top', style='italic')

for (dx, dy, lab) in ((-C30, S30, 'N'), (C30, S30, 'E')):
    ax.annotate('', (286+10*dx, 4+10*dy), (286, 4), arrowprops=dict(arrowstyle='-|>', color=Q, lw=0.6, mutation_scale=6))
    ax.text(286+12.5*dx, 4+12.5*dy, lab, fontsize=5.6, color=Q, ha='center', va='center')
ax.text(150, -9, 'Each site is a 5 MWp plant: 2 blocks × 1,419 strings × 15 First Solar FS-4117-3 CdTe modules (117.8 W), each block on a '
        '1.9 MW Power Electronics FS1901CU inverter (DC/AC 1.32).', ha='center', fontsize=5.4, color=Q, style='italic')
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
