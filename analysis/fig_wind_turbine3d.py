"""Wind turbine figure: (a) isometric V126 to scale with the log-law wind profile used in gbtea/wind.py;
(b) V126 power curve as published, after Staffell-Pfenninger smoothing, and after density correction."""
import sys, numpy as np
import matplotlib as mpl; mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, Circle
from matplotlib.colors import to_rgb
from windpowerlib import WindTurbine
from windpowerlib.power_curves import smooth_power_curve
from windpowerlib.power_output import power_curve as pc_output
OUT = sys.argv[1]
mpl.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 6.5})
MM = 1/25.4; INK, Q, EDGE = '#1d1d1f', '#55565a', '#6b7079'
COOL, WARM, DARK, AMBER = '#2c5fa8', '#c8553d', '#5d6168', '#f2a516'
C30, S30 = np.cos(np.pi/6), 0.5
fig = plt.figure(figsize=(177*MM, 92*MM))
ax = fig.add_axes([0.0, 0.0, 0.58, 1.0]); ax.set_xlim(-10, 150); ax.set_ylim(-20, 118); ax.set_aspect('equal'); ax.axis('off')

class Iso:
    def __init__(s, ox, oy, k): s.ox, s.oy, s.k = ox, oy, k
    def p(s, x, y, z): return (s.ox + s.k*(x - y)*C30, s.oy + s.k*((x + y)*S30 + z))
    def poly(s, pts, fc, ec=EDGE, lw=0.4, z=3, alpha=1):
        ax.add_patch(Polygon([s.p(*q) for q in pts], closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, joinstyle='round'))
K = 0.52
s = Iso(62, 4, K)
s.poly([(-60, -20, 0), (45, -20, 0), (45, 75, 0), (-60, 75, 0)], '#eef3e8', ec='#cdd6c4', z=1)

def turbine(x, y, hub, D, label, z0=5):
    """Tower along z, rotor in the y-z plane facing -x (into a westerly wind)."""
    R = D/2; base_r, top_r = 0.025*hub+1.2, 0.012*hub+0.8
    P0, P1 = s.p(x, y, 0), s.p(x, y, hub)
    ax.add_patch(Polygon([(P0[0]-base_r*K, P0[1]), (P0[0]+base_r*K, P0[1]), (P1[0]+top_r*K, P1[1]), (P1[0]-top_r*K, P1[1])],
                         fc='#f4f5f7', ec=EDGE, lw=0.4, zorder=z0))
    # swept disc (ellipse of the y-z plane in this projection)
    th = np.linspace(0, 2*np.pi, 80)
    disc = [s.p(x-2, y + R*np.cos(t), hub + R*np.sin(t)) for t in th]
    ax.add_patch(Polygon(disc, closed=True, fc=COOL, alpha=0.07, ec=COOL, lw=0.4, ls=(0, (2, 1.5)), zorder=z0-0.5))
    # nacelle
    for (a, b, c, f) in (((0, 0, 0), (7, 0, 0), (7, 0, 3.2), '#d9dce1'), ((0, 0, 3.2), (7, 0, 3.2), (7, 2.6, 3.2), '#eef0f3')):
        pass
    nb = [s.p(x-1, y-1.3, hub-1.4), s.p(x+8, y-1.3, hub-1.4), s.p(x+8, y-1.3, hub+1.8), s.p(x-1, y-1.3, hub+1.8)]
    nt = [s.p(x-1, y-1.3, hub+1.8), s.p(x+8, y-1.3, hub+1.8), s.p(x+8, y+1.3, hub+1.8), s.p(x-1, y+1.3, hub+1.8)]
    ax.add_patch(Polygon(nb, fc='#d9dce1', ec=EDGE, lw=0.4, zorder=z0+0.3)); ax.add_patch(Polygon(nt, fc='#eef0f3', ec=EDGE, lw=0.4, zorder=z0+0.3))
    # three blades in the rotor plane
    for ang in (90, 210, 330):
        a = np.radians(ang + 15)
        tip = np.array([np.cos(a), np.sin(a)]); n = np.array([-tip[1], tip[0]])
        pts = []
        for r_, w_ in ((0.06, 0.05), (0.25, 0.075), (1.0, 0.012), (0.25, -0.03), (0.06, -0.03)):
            yy, zz = R*(r_*tip + w_*n)
            pts.append(s.p(x-2.5, y+yy, hub+zz))
        ax.add_patch(Polygon(pts, fc='#fbfbfc', ec=EDGE, lw=0.4, zorder=z0+0.6))
    H = s.p(x-2.5, y, hub); ax.add_patch(Circle(H, 0.9, fc='#eef0f3', ec=EDGE, lw=0.4, zorder=z0+0.7))
    # labels: hub height marker and caption
    L = s.p(x+R*0.2+14, y, 0)
    return P0

turbine(10, 30, 100, 126, 'V126', z0=5)

# hub-height dimension lines
for (x, y, hub, D, name, txt, c) in ((10, 30, 100, 126, 'Vestas V126-3.45 MW', 'hub 100 m · rotor 126 m\n277 W/m² specific power', INK),):
    A, B = s.p(x+16, y-16, 0), s.p(x+16, y-16, hub)
    ax.plot([A[0], B[0]], [A[1], B[1]], color=WARM, lw=0.6, zorder=8)
    for P in (A, B): ax.plot([P[0]-1.2, P[0]+1.2], [P[1], P[1]], color=WARM, lw=0.6, zorder=8)
    ax.text(B[0]+2, (A[1]+B[1])/2, f'{hub} m', color=WARM, fontsize=5.6, va='center', zorder=9)
    T = s.p(x+4, y-2, hub + D/2)
    ax.text(T[0]+(14 if hub == 100 else 4), T[1]+(4 if hub == 100 else 14), name, fontsize=6.4, fontweight='bold', color=c, zorder=9)
    ax.text(T[0]+(14 if hub == 100 else 4), T[1]+(4 if hub == 100 else 14)-2, txt, fontsize=5.3, color=Q, style='italic', va='top', zorder=9, linespacing=1.15)

# log-law profile on the upwind side: u(z)/u100 = ln(z/z0)/ln(100/z0), z0 = 0.05 m
z0 = 0.05; X0, Y0 = -48, 30
for z in (10, 30, 60, 100, 140):
    r = np.log(z/z0)/np.log(100/z0)
    A, B = s.p(X0, Y0, z), s.p(X0 + 34*r, Y0, z)
    hi = z == 100
    ax.annotate('', B, A, arrowprops=dict(arrowstyle='-|>', color=COOL if hi else '#7fa7dd', lw=1.1 if hi else 0.7, mutation_scale=6), zorder=7)
    ax.text(A[0]-1.5, A[1], f'{z} m', ha='right', va='center', fontsize=5.4, color=Q, zorder=9)
    ax.text(B[0]+1.2, B[1]+1.2, f'{r:.2f}', ha='left', va='bottom', fontsize=5.2, color=COOL if hi else '#7fa7dd', zorder=9)
zz = np.linspace(2, 145, 80); rr = np.log(zz/z0)/np.log(100/z0)
P = [s.p(X0 + 34*r, Y0, z) for r, z in zip(rr, zz)]; ax.plot(*zip(*P), color=COOL, lw=0.6, ls=(0, (2, 1.5)), zorder=6)
A, B = s.p(X0, Y0, 0), s.p(X0, Y0, 150); ax.plot([A[0], B[0]], [A[1], B[1]], color=EDGE, lw=0.5, zorder=6)
E1, E2 = s.p(X0-6, Y0, 100), s.p(X0+50, Y0, 100)
ax.plot([E1[0], E2[0]], [E1[1], E2[1]], color=AMBER, lw=0.9, ls=(0, (3, 1.5)), zorder=5)
ax.text(E1[0]-1, E1[1]+3.2, 'ERA5 100 m wind', fontsize=5.6, color='#a06a00', ha='right', zorder=9)
T = s.p(X0, Y0, 160); ax.text(T[0], T[1]+3, 'Log-law profile\nu(z) / u(100 m), z₀ = 0.05 m', ha='center', fontsize=5.6, color=COOL, zorder=9, linespacing=1.15)
ax.text(70, -17, 'Hub at the ERA5 100 m level, so no height extrapolation is needed.',
        ha='center', fontsize=5.4, color=Q, style='italic')
ax.text(-8, 114, 'a', fontsize=8.5, fontweight='bold', color=INK)

# (b) power curves
bx = fig.add_axes([0.68, 0.14, 0.31, 0.66])
t = WindTurbine(turbine_type='V126/3450', hub_height=100); c = t.power_curve
sm = smooth_power_curve(c['wind_speed'], c['value'], standard_deviation_method='Staffell_Pfenninger', mean_gauss=0, block_width=0.5)
v = np.linspace(0, 27, 541)
raw = np.interp(v, c['wind_speed'], c['value'], left=0, right=0)
smo = np.interp(v, sm['wind_speed'], sm['value'], left=0, right=0)
den = np.asarray(pc_output(pd_s := __import__('pandas').Series(v), sm['wind_speed'], sm['value'], density=__import__('pandas').Series(np.full(len(v), 1.15)), density_correction=True), float)
bx.plot(v, raw/3.45e6, color=DARK, lw=1.0, ls=(0, (3, 1.6)), label='published curve')
bx.plot(v, smo/3.45e6, color=COOL, lw=1.6, label='smoothed (Staffell–Pfenninger)')
bx.plot(v, den/3.45e6, color=WARM, lw=1.2, label='smoothed, ρ = 1.15 kg/m³')
for sp in ('top', 'right'): bx.spines[sp].set_visible(False)
bx.spines['left'].set_color('#b0b3b8'); bx.spines['bottom'].set_color('#b0b3b8')
bx.yaxis.grid(True, color='#e6e7e9', lw=0.6); bx.set_axisbelow(True)
bx.set_xlim(0, 27); bx.set_ylim(0, 1.07); bx.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
bx.set_xlabel('Hub-height wind speed (m/s)', color=Q); bx.set_ylabel('Output, % of 3.45 MW', color=Q)
bx.tick_params(colors=Q, labelsize=6)
for xv, txt in ((3, 'cut-in 3'), (11, 'rated 11'), (22.5, 'cut-out 22.5')):
    bx.axvline(xv, color='#cfd2d6', lw=0.5, zorder=0); bx.text(xv, 1.075, txt, fontsize=5.2, color=Q, ha='center', va='bottom')
bx.legend(loc='lower center', bbox_to_anchor=(0.45, 1.07), frameon=False, fontsize=5.6, ncol=1, handlelength=2.2)
bx.text(-0.2, 1.33, 'b', transform=bx.transAxes, fontsize=8.5, fontweight='bold', color=INK)
for ext, kw in (('tif', dict(dpi=600, pil_kwargs={'compression': 'tiff_lzw'})), ('png', dict(dpi=300))):
    fig.savefig(f'{OUT}.{ext}', bbox_inches='tight', **kw)
