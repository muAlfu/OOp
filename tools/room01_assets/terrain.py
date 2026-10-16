"""Solid-ground autotile set (16 cardinal tiles + 4 inner corners).

Every tile is cut from the same 32px-periodic cobblestone texture and all edge
profiles are periodic too, so any two tiles that agree on their shared edge
line up pixel-perfectly.
"""
import functools

import numpy as np

from palette import MOSS, ROCK, ROCK_BG, ROCK_FAR
from px import (OUTLINE, Sprite, depth_map, grid, hash2, outline_of, rnd,
                shift, wave)

T = 32
PAD = 8


# --------------------------------------------------------------------------
# cobblestone texture (periodic, 32x32)
# --------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def cobble(seed=3, cols=3, rows=4):
    pts = []
    for r in range(rows):
        for c in range(cols):
            jx = (rnd(seed, r, c, 1) - 0.5) * 0.55
            jy = (rnd(seed, r, c, 2) - 0.5) * 0.45
            off = 0.5 if r % 2 else 0.0
            pts.append((((c + 0.5 + off + jx) * T / cols) % T,
                        ((r + 0.5 + jy) * T / rows) % T))
    xx, yy = grid(T, T)
    best = np.full((T, T), 1e9)
    second = np.full((T, T), 1e9)
    lab = np.zeros((T, T), int)
    vx = np.zeros((T, T))
    vy = np.zeros((T, T))
    for i, (px_, py_) in enumerate(pts):
        dx = (xx + 0.5 - px_ + T / 2) % T - T / 2
        dy = (yy + 0.5 - py_ + T / 2) % T - T / 2
        d = np.sqrt((dx * 0.82) ** 2 + (dy * 1.12) ** 2)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        best = np.where(closer, d, best)
        lab = np.where(closer, i, lab)
        vx = np.where(closer, dx, vx)
        vy = np.where(closer, dy, vy)
    mortar = (second - best) < 0.95
    tone = np.array([rnd(seed, i, 9) for i in range(len(pts))])
    return lab, mortar, vx, vy, tone


def cobble_colors(mask, ox, oy, ramp, seed=3, dark=0.0, run_top=None, depth=None, cells=(3, 4)):
    """Colour every pixel of `mask` (a window whose (0,0) maps to texture
    coordinate (ox, oy)) with the periodic cobble texture."""
    lab, mortar, vx, vy, tone = cobble(seed, *cells)
    h, w = mask.shape
    xx, yy = grid(w, h)
    tx = (xx + ox) % T
    ty = (yy + oy) % T
    L = lab[ty, tx]
    M = mortar[ty, tx]
    VX = vx[ty, tx]
    VY = vy[ty, tx]
    TONE = tone[L]
    same = lambda dx, dy: (shift(L, dx, dy, -1) == L) & shift(mask, dx, dy) & ~shift(M, dx, dy, True)
    stone = mask & ~M
    up_open = stone & ~same(0, 1)
    left_open = stone & ~same(1, 0)
    down_open = stone & ~same(0, -1)
    right_open = stone & ~same(-1, 0)

    idx = 2.0 + (TONE - 0.5) * 0.9 - dark
    light = -(VX * 0.55 + VY * 1.0) / 6.0
    idx = idx + np.clip(light, -0.8, 0.9)
    idx = np.where(up_open | left_open, idx + 0.9, idx)
    idx = np.where(up_open & left_open, idx + 0.6, idx)
    idx = np.where((down_open | right_open) & ~up_open, idx - 0.8, idx)
    n = hash2(tx, ty, seed + 40)
    idx = idx + np.where(n < 0.06, -0.7, 0) + np.where(n > 0.95, 0.6, 0)
    if depth is not None:
        idx = idx - np.where(depth >= 9, 0.5, 0) - np.where(depth >= 15, 0.4, 0)
    if run_top is not None:
        idx = idx + np.where(run_top <= 4, 0.7, np.where(run_top <= 9, 0.35, 0))
    idx = np.where(M, 0.0, idx)
    idx = np.clip(np.round(idx), 0, len(ramp) - 1).astype(int)
    pal = np.array(ramp, np.uint8)
    return pal[idx]


def run_from_top(m):
    r = np.zeros(m.shape, int)
    acc = np.zeros(m.shape[1], int)
    for y in range(m.shape[0]):
        acc = np.where(m[y], acc + 1, 0)
        r[y] = acc
    return r


def run_from_left(m):
    return run_from_top(m.T).T


# --------------------------------------------------------------------------
# edge profiles (periodic so neighbouring tiles agree)
# --------------------------------------------------------------------------
def _prof(x, terms, base=3):
    return np.round(base + wave(x, T, terms) - wave(0, T, terms)).astype(int)


TOP = [(0.9, 1, 0.0), (0.8, 3, 1.1), (0.45, 5, 0.4)]
BOT = [(1.0, 2, 0.6), (0.7, 3, 2.0)]
LEFT = [(0.9, 2, 0.3), (0.6, 5, 1.7)]
RIGHT = [(0.8, 3, 2.4), (0.7, 2, 0.9)]


def carve_cell(m, x0, y0, nb):
    """Carve the 32x32 cell at (x0, y0) of the big mask m given its 3x3
    solidity nb[dy+1][dx+1]."""
    if not nb[1][1]:
        m[y0:y0 + T, x0:x0 + T] = False
        return
    xs = np.arange(T)
    ys = np.arange(T)
    cell = m[y0:y0 + T, x0:x0 + T]
    xx, yy = grid(T, T)
    n, s = not nb[0][1], not nb[2][1]
    w, e = not nb[1][0], not nb[1][2]
    if n:
        cell &= yy >= _prof(xs, TOP)[None, :]
    if s:
        cell &= (T - 1 - yy) >= _prof(xs, BOT, 3)[None, :]
    if w:
        cell &= xx >= _prof(ys, LEFT)[:, None]
    if e:
        cell &= (T - 1 - xx) >= _prof(ys, RIGHT)[:, None]
    R = 10

    def corner(cx, cy, rad):
        return (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 > rad ** 2

    if n and w:
        cell &= ~((xx < R) & (yy < R) & corner(R, R, R - 3))
    if n and e:
        cell &= ~((xx >= T - R) & (yy < R) & corner(T - R, R, R - 3))
    if s and w:
        cell &= ~((xx < R) & (yy >= T - R) & corner(R, T - R, R - 3))
    if s and e:
        cell &= ~((xx >= T - R) & (yy >= T - R) & corner(T - R, T - R, R - 3))
    # inner corners: both cardinals solid, diagonal empty
    r = 4.2
    if not n and not w and not nb[0][0]:
        cell &= (xx + 0.5) ** 2 + (yy + 0.5) ** 2 > r ** 2
    if not n and not e and not nb[0][2]:
        cell &= (T - xx - 0.5) ** 2 + (yy + 0.5) ** 2 > r ** 2
    if not s and not w and not nb[2][0]:
        cell &= (xx + 0.5) ** 2 + (T - yy - 0.5) ** 2 > r ** 2
    if not s and not e and not nb[2][2]:
        cell &= (T - xx - 0.5) ** 2 + (T - yy - 0.5) ** 2 > r ** 2
    m[y0:y0 + T, x0:x0 + T] = cell


def big_mask(nb):
    """96x96 mask for the 3x3 neighbourhood; the outer ring is extended by
    replication so neighbour cells are carved plausibly too."""
    g = np.zeros((5, 5), bool)
    for j in range(5):
        for i in range(5):
            g[j][i] = nb[min(2, max(0, j - 1))][min(2, max(0, i - 1))]
    m = np.ones((3 * T, 3 * T), bool)
    for j in range(3):
        for i in range(3):
            sub = [[g[j + b][i + a] for a in range(3)] for b in range(3)]
            carve_cell(m, i * T, j * T, sub)
    return m


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def _moss_profile(x):
    """Moss thickness per column (periodic)."""
    blk = (x // 3) % (T // 3 + 1)
    h = hash2(blk, 5, 21)
    v = np.where(h < 0.22, 0, np.where(h < 0.55, 2, np.where(h < 0.85, 3, 5)))
    drip = hash2(x % T, 9, 22) > 0.88
    return np.where(drip & (v > 0), v + 4, v)


def render_ground(nb, ramp=ROCK, seed=3, moss=True, dark=0.0):
    m = big_mask(nb)
    c0, c1 = T - PAD, 2 * T + PAD
    win = m[c0:c1, c0:c1]
    S = win.shape[0]
    depth = depth_map(win, limit=16)
    rt = run_from_top(win)
    col = cobble_colors(win, -PAD, -PAD, ramp, seed, dark=dark, run_top=rt, depth=depth)
    spr = Sprite(S, S)
    spr.a[win, :3] = col[win]
    spr.a[win, 3] = 255
    xx, yy = grid(S, S)
    lx = (xx - PAD) % T

    surface = win & ~shift(win, 0, 1)
    under = win & ~shift(win, 0, -1)
    rl = run_from_left(win)
    rr = run_from_left(win[:, ::-1])[:, ::-1]

    # frosty lip on top surfaces
    spr.put(surface, ramp[5])
    spr.put(win & (rt == 2) & (hash2(lx, yy, 31) < 0.6), ramp[4])
    # shadowed underside
    spr.put(under, ramp[0])
    spr.put(win & shift(under, 0, -1) & (hash2(lx, yy, 32) < 0.5), ramp[1])
    # dark side faces near walls
    side = win & ((rl <= 1) | (rr <= 1)) & (rt > 2)
    spr.put(side & (rr <= 1), ramp[1])

    if moss:
        # a "real" top surface is open above across a 5px window, which
        # keeps single-pixel steps on vertical walls free of moss
        open_above = sum((~shift(win, dx, 2, True)).astype(int) for dx in range(-2, 3))
        valid = surface & (open_above >= 4)
        mp = _moss_profile(lx)
        mz = np.zeros_like(win)
        for k in range(8):
            mz |= shift(valid, 0, k) & win & (mp > k) & (rt > k)
        tone = np.where(rt == 1, 3, np.where(rt == 2, 2, 1))
        tone = np.where((rt > 3) & (rt == mp), 0, tone)
        tone = np.where(hash2(lx, yy, 33) > 0.9, np.minimum(tone + 1, 4), tone)
        pal = np.array(MOSS, np.uint8)
        spr.a[mz, :3] = pal[tone[mz]]
        # grass blades poking above the surface
        blade_x = hash2(lx, 1, 34) > 0.72
        bl_h = (hash2(lx, 2, 35) * 3).astype(int) + 1
        blades = np.zeros_like(win)
        for k in range(1, 4):
            blades |= ~win & shift(valid, 0, -k) & blade_x & (bl_h >= k)
        spr.put(outline_of(win) & ~blades, OUTLINE)
        spr.put(blades, MOSS[3])
        spr.put(blades & ~shift(blades, 0, 1), MOSS[4])
    else:
        spr.put(outline_of(win), OUTLINE)

    # little roots hanging from undersides
    root_x = hash2(lx, 3, 36) > 0.86
    root_len = (hash2(lx, 4, 37) * 4).astype(int) + 1
    roots = np.zeros_like(win)
    for k in range(2, 6):
        roots |= ~win & shift(under, 0, k) & root_x & (root_len >= k - 1)
    spr.put(roots, MOSS[0])

    out = Sprite(T, T)
    out.a = spr.a[PAD:PAD + T, PAD:PAD + T].copy()
    return out


# --------------------------------------------------------------------------
# canonical tiles
# --------------------------------------------------------------------------
def nb_from(n, e, s, w, nw=None, ne=None, sw=None, se=None):
    nw = (n and w) if nw is None else nw
    ne = (n and e) if ne is None else ne
    sw = (s and w) if sw is None else sw
    se = (s and e) if se is None else se
    return ((nw, n, ne), (w, True, e), (sw, s, se))


# name: (n, e, s, w) solidity + inner-corner diagonals
CANON = {
    "ground_tl": nb_from(False, True, True, False),
    "ground_t": nb_from(False, True, True, True),
    "ground_tr": nb_from(False, False, True, True),
    "ground_l": nb_from(True, True, True, False),
    "ground_c": nb_from(True, True, True, True),
    "ground_r": nb_from(True, False, True, True),
    "ground_bl": nb_from(True, True, False, False),
    "ground_b": nb_from(True, True, False, True),
    "ground_br": nb_from(True, False, False, True),
    "ground_inner_tl": nb_from(True, True, True, True, nw=False),
    "ground_inner_tr": nb_from(True, True, True, True, ne=False),
    "ground_inner_bl": nb_from(True, True, True, True, sw=False),
    "ground_inner_br": nb_from(True, True, True, True, se=False),
    "ledge_l": nb_from(False, True, False, False),
    "ledge_m": nb_from(False, True, False, True),
    "ledge_r": nb_from(False, False, False, True),
    "column_t": nb_from(False, False, True, False),
    "column_m": nb_from(True, False, True, False),
    "column_b": nb_from(True, False, False, False),
    "block": nb_from(False, False, False, False),
}

CARDINAL = {}
for _name, _nb in CANON.items():
    if "inner" in _name:
        continue
    CARDINAL[(_nb[0][1], _nb[1][2], _nb[2][1], _nb[1][0])] = _name


def classify(n, e, s, w, nw, ne, sw, se):
    if n and e and s and w:
        if not nw:
            return "ground_inner_tl"
        if not ne:
            return "ground_inner_tr"
        if not sw:
            return "ground_inner_bl"
        if not se:
            return "ground_inner_br"
    return CARDINAL[(n, e, s, w)]


def ground_tiles():
    return {name: render_ground(nb) for name, nb in CANON.items()}


def bg_wall(seed=8):
    """Seamless, low-contrast back wall (sits behind everything)."""
    win = np.ones((T, T), bool)
    col = cobble_colors(win, 0, 0, ROCK_FAR, seed, dark=0.6, cells=(2, 3))
    spr = Sprite(T, T)
    spr.a[:, :, :3] = col
    spr.a[:, :, 3] = 255
    return spr
