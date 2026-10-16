"""Every non-terrain module of Room 01: platforms, hazards, wood structures,
lights, crystals, flora, interactables, characters and background pieces.

Each function returns a px.Sprite. Sizes are multiples of the 32px grid.
"""
import math

import numpy as np

import terrain
from palette import (BANNER, BAT, CLOTH_TRIM, CRUMBLE, CRYSTAL, EYE_AMBER,
                     EYE_RED, FLAME, GLOW_COOL, GLOW_GOLD, GLOW_RED, GLOW_WARM,
                     GOLD, GOLEM, HAZARD, IRON, MOSS, ROCK, ROCK_BG, ROCK_FAR, ROPE,
                     SLIME, WATER, WOOD)
from px import (OUTLINE, Sprite, ellipse, grid, halo, hash2, inner_edge,
                line_mask, outline_of, poly, rect, shade, shift)

T = 32


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def wood(spr, mask, axis="v", seed=0, base=2, outline=True):
    """Planked wood: ramp shading plus grain running along `axis`."""
    if not mask.any():
        return
    shade(spr, mask, WOOD, base=base, noise=0.06, seed=seed, outline=outline)
    xx, yy = grid(spr.w, spr.h)
    across, along = (xx, yy) if axis == "v" else (yy, xx)
    core = mask & ~inner_edge(mask)
    grain = core & ((across + seed) % 3 == 0) & (hash2(across, along // 5, seed) > 0.45)
    spr.put(grain, WOOD[base - 1])
    hi = core & ((across + seed) % 3 == 1) & (hash2(across, along // 7, seed + 1) > 0.8)
    spr.put(hi, WOOD[base + 1])


def nail(spr, x, y):
    spr.px(x, y, IRON[3])
    spr.px(x, y + 1, IRON[0])


def shard(spr, bx, by, h, hw, tilt=0.0, ramp=CRYSTAL, down=False):
    """Faceted crystal shard growing from (bx, by) upwards (or downwards)."""
    sgn = 1 if down else -1
    tx, ty = bx + tilt, by + sgn * h
    pts = [(bx - hw, by), (bx - hw * 0.85 + tilt * 0.7, by + sgn * h * 0.72), (tx, ty),
           (bx + hw * 0.85 + tilt * 0.7, by + sgn * h * 0.72), (bx + hw, by)]
    m = poly(spr.w, spr.h, pts)
    if not m.any():
        return m
    xx, yy = grid(spr.w, spr.h)
    cross = (tx - bx) * (yy + 0.5 - by) - (ty - by) * (xx + 0.5 - bx)
    lit = m & (cross * (-sgn) < 0)
    dark = m & ~lit
    spr.put(outline_of(m), OUTLINE)
    spr.put(dark, ramp[1])
    spr.put(lit, ramp[3])
    edge = inner_edge(m)
    spr.put(edge & dark, ramp[0])
    spr.put(edge & lit, ramp[4])
    axis = line_mask(spr.w, spr.h, bx, by, tx, ty) & m
    spr.put(axis & ~edge, ramp[4])
    spr.put(dark & shift(lit, 1, 0) & ~edge, ramp[2])
    tip = m & (np.abs(yy + 0.5 - ty) < 3) & ~shift(m, 0, -sgn)
    spr.put(tip & lit, ramp[5])
    return m


def sparkle(spr, x, y, color=(255, 255, 255), size=2):
    for d in range(-size, size + 1):
        spr.px(x + d, y, color)
        spr.px(x, y + d, color)


def flame(spr, cx, top, h=6):
    """Tiny lantern flame (cx = centre x, top = top y)."""
    for i in range(h):
        y = top + i
        half = 0 if i < 2 else (1 if i < h - 1 else 1)
        for x in range(cx - half, cx + half + 1):
            spr.px(x, y, FLAME[min(4, 2 + (i < 3) + (i < 1))])
    spr.px(cx, top + h - 2, FLAME[4])
    spr.px(cx, top + h - 3, FLAME[4])


# --------------------------------------------------------------------------
# floating-island underside (decorative rock that hangs below a ledge)
# --------------------------------------------------------------------------
def underside(kind):
    xx, yy = grid(T, T)
    xs = np.arange(T)
    bottom = np.round(13 + 3.2 * np.sin(2 * math.pi * xs / T + 0.4) - 3.2 * math.sin(0.4)
                      + 1.6 * np.sin(2 * math.pi * 3 * xs / T)).astype(int)
    m = yy < bottom[None, :]
    tips = {"m": [(9, 26, 4), (23, 21, 3)], "l": [(22, 24, 4)], "r": [(10, 24, 4)], "s": [(16, 29, 5)]}[kind]
    for (tx, ty, hw) in tips:
        m |= poly(T, T, [(tx - hw, 10), (tx + hw, 10), (tx + 0.5, ty)])
    if kind in ("l", "s"):
        edge = 3 + np.round(15 * (np.arange(T) / 24.0) ** 1.4).astype(int)
        m &= xx >= edge[:, None]
    if kind in ("r", "s"):
        edge = 3 + np.round(15 * (np.arange(T) / 24.0) ** 1.4).astype(int)
        m &= (T - 1 - xx) >= edge[:, None]
    depth = np.where(yy < 8, 8, 4)
    col = terrain.cobble_colors(m, 0, 0, ROCK, 3, dark=0.4, depth=depth)
    spr = Sprite(T, T)
    spr.a[m, :3] = col[m]
    spr.a[m, 3] = 255
    # darken towards the bottom, rim-light the tips
    low = m & (yy > 14)
    spr.put(low & (hash2(xx, yy, 5) < 0.55), ROCK[0])
    spr.put(m & ~shift(m, 0, -1), ROCK[0])
    spr.put(m & ~shift(m, 1, 0) & (yy > 2), ROCK[3])
    spr.put(outline_of(m) & (yy > 0), OUTLINE)
    # hanging roots
    for rx, length in ((5, 6), (14, 9), (27, 5), (19, 4)):
        if not m[0, rx]:
            continue
        top = int(np.argmin(m[:, rx])) if not m[:, rx].all() else T
        for k in range(length):
            y = top + k
            x = rx + (1 if (k // 3) % 2 else 0)
            if y < T and not m[y, x]:
                spr.px(x, y, MOSS[1] if k < length - 1 else MOSS[3])
    return spr


# --------------------------------------------------------------------------
# crumbling platform (منصة متداعية)
# --------------------------------------------------------------------------
def crumble(kind, state):
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    slab = (yy >= 3) & (yy <= 15)
    if kind == "l":
        slab &= ~(((xx < 4) & (yy < 6)) | ((xx < 2)) | ((xx < 5) & (yy > 13)))
    if kind == "r":
        slab &= ~(((xx > 27) & (yy < 6)) | ((xx > 29)) | ((xx > 26) & (yy > 13)))
    pieces = [slab]
    if state == 2:
        cut = poly(T, T, [(14, 0), (17, 0), (16, 7), (18, 12), (17, 20), (14, 20), (15, 12), (13, 7)])
        a = slab & (xx < 16) & ~cut
        b = slab & (xx >= 15) & ~cut
        a &= ~poly(T, T, [(9, 0), (14, 0), (14, 6)])
        b &= ~poly(T, T, [(24, 0), (32, 0), (32, 5), (27, 6)])
        pieces = [shift(a, 0, 1), shift(b, 1, 3)]
    allm = np.zeros((T, T), bool)
    for p in pieces:
        allm |= p
    # bricks: two courses, staggered joints
    course = np.where(yy < 9, 0, 1)
    joint_x = np.where(course == 0, (xx + 3) % 11 == 0, (xx + 8) % 11 == 0)
    mortar = allm & ((yy == 9) | joint_x)
    if state == 2:
        mortar = allm & (shift((yy == 9) | joint_x, 0, 2) | (yy == 9) | joint_x)
    shade(spr, allm, CRUMBLE, base=3, noise=0.05, seed=11 + state, outline=True)
    spr.put(mortar & ~inner_edge(allm), CRUMBLE[1])
    spr.put(allm & ~shift(allm, 0, 1), CRUMBLE[5])
    spr.put(allm & ~shift(allm, 0, -1), CRUMBLE[1])
    # bricks get a lit top row
    lit = allm & shift(mortar, 0, 1) & ~mortar
    spr.put(lit, CRUMBLE[4])
    # drips hanging underneath
    drip_x = [4, 8, 13, 17, 22, 27]
    for i, dx in enumerate(drip_x):
        if not allm[:, dx].any():
            continue
        y0 = int(np.where(allm[:, dx])[0].max()) + 1
        ln = 2 + (i * 7 + state * 3) % 4
        for k in range(ln):
            spr.px(dx, y0 + k, CRUMBLE[2] if k < ln - 1 else CRUMBLE[4])
        spr.px(dx, y0 + ln, OUTLINE)
    # falling debris
    n_bits = (3, 6, 11)[state]
    for i in range(n_bits):
        bx = int(hash2(i, state, 41) * 28) + 2
        by = 19 + int(hash2(i, state, 42) * 11)
        if allm[min(T - 1, by), bx]:
            continue
        spr.px(bx, by, CRUMBLE[3])
        if hash2(i, state, 43) > 0.5:
            spr.px(bx + 1, by, CRUMBLE[2])
            spr.px(bx, by + 1, CRUMBLE[1])
    if state >= 1:
        # cracks
        crack = line_mask(T, T, 6, 4, 9, 9) | line_mask(T, T, 9, 9, 7, 14)
        crack |= line_mask(T, T, 18, 3, 16, 8) | line_mask(T, T, 16, 8, 19, 13)
        crack |= line_mask(T, T, 26, 5, 24, 11)
        spr.put(crack & allm & ~inner_edge(allm), CRUMBLE[0])
    return spr


def debris():
    spr = Sprite(T, T)
    for i in range(16):
        x = int(hash2(i, 1, 51) * 26) + 3
        y = int(hash2(i, 2, 52) * 26) + 3
        s = 1 + (hash2(i, 3, 53) > 0.6)
        m = rect(T, T, x, y, x + s - 1, y + s - 1)
        shade(spr, m, CRUMBLE, base=3, rim=False, noise=0, outline=s > 1)
    return spr


# --------------------------------------------------------------------------
# hazard: red crystals (بلور مؤذٍ)
# --------------------------------------------------------------------------
def hazard(variant):
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    for y0, y1, a in ((4, 11, 22), (11, 18, 40), (18, 26, 64), (26, 31, 90)):
        spr.put(rect(T, T, 0, y0, T - 1, y1), GLOW_RED, a)
    spikes = {
        "a": [(5, 30, 13, 4, -1.5), (13, 30, 22, 5, 0.5), (21, 30, 15, 4, 1.5), (27, 30, 19, 4, -0.5)],
        "b": [(4, 30, 17, 4, 1.0), (11, 30, 11, 4, -1.0), (17, 30, 24, 5, 0.0), (25, 30, 14, 4, 1.5)],
    }[variant]
    for bx, by, h, hw, t in spikes:
        shard(spr, bx, by, h, hw, t, ramp=HAZARD)
    crust = (yy >= 26) & (yy >= 26 + np.round(1.2 * np.sin(xx * 0.9)).astype(int))
    shade(spr, crust, HAZARD, base=1, noise=0.2, seed=61, rim=True, outline=False)
    glow_cracks = crust & (hash2(xx, yy, 62) > 0.86)
    spr.put(glow_cracks, HAZARD[4])
    return spr


# --------------------------------------------------------------------------
# breakable barrier (حاجز يُكسر)
# --------------------------------------------------------------------------
def barrier(state):
    W, H = T, 2 * T
    spr = Sprite(W, H)
    xx, yy = grid(W, H)
    planks = []
    tops = [5, 2, 6]
    for i, x0 in enumerate((4, 12, 20)):
        m = rect(W, H, x0, tops[i], x0 + 7, H - 1)
        m &= ~((yy < tops[i] + 2) & ((xx == x0) | (xx == x0 + 7)))
        planks.append(m)
    if state == 1:
        planks[1] &= ~poly(W, H, [(12, 0), (20, 0), (20, 17), (16, 23), (12, 15)])
        planks[2] &= ~poly(W, H, [(20, 34), (28, 30), (28, 44)])
    if state == 2:
        stubs = [rect(W, H, 4, 50, 11, H - 1) & ~poly(W, H, [(4, 50), (11, 50), (11, 54), (7, 52), (4, 56)]),
                 rect(W, H, 20, 54, 27, H - 1) & ~poly(W, H, [(20, 54), (27, 54), (27, 57), (23, 58)])]
        for i, m in enumerate(stubs):
            wood(spr, m, "v", seed=70 + i, base=2)
        pile = [((2, 58), (14, 54)), ((10, 60), (28, 57)), ((14, 52), (24, 58))]
        for i, ((x0, y0), (x1, y1)) in enumerate(pile):
            m = line_mask(W, H, x0, y0, x1, y1, width=3)
            wood(spr, m, "h", seed=74 + i, base=2)
        for i in range(10):
            x = int(hash2(i, 5, 77) * 28) + 2
            y = 44 + int(hash2(i, 6, 78) * 18)
            if not spr.opaque[y, x]:
                spr.px(x, y, WOOD[3] if i % 2 else WOOD[4])
        return spr
    for i, m in enumerate(planks):
        wood(spr, m, "v", seed=80 + i, base=2)
    # cross straps and a diagonal brace
    straps = [rect(W, H, 2, 14, 29, 18), rect(W, H, 2, 46, 29, 50)]
    diag = line_mask(W, H, 6, 22, 26, 42, width=4)
    if state == 1:
        straps[0] &= ~rect(W, H, 14, 0, 19, H - 1)
        diag &= ~rect(W, H, 15, 30, 18, 34)
    wood(spr, diag, "h", seed=85, base=3)
    for i, m in enumerate(straps):
        wood(spr, m, "h", seed=86 + i, base=1)
        ys = np.where(m.any(axis=1))[0]
        for x in (5, 15, 26):
            if m[ys[0] + 2, x]:
                nail(spr, x, ys[0] + 1)
    if state == 1:
        crack = (line_mask(W, H, 8, 26, 10, 33) | line_mask(W, H, 10, 33, 8, 40)
                 | line_mask(W, H, 23, 20, 25, 27))
        spr.put(crack & spr.opaque, WOOD[0])
        for (x, y) in ((16, 25), (19, 29), (13, 22), (21, 36), (17, 31)):
            spr.px(x, y, GOLD[4])
        sparkle(spr, 16, 27, GOLD[3], 2)
    return spr


# --------------------------------------------------------------------------
# wooden structures
# --------------------------------------------------------------------------
def post(kind):
    spr = Sprite(T, T)
    y0 = 6 if kind == "top" else 0
    y1 = 25 if kind == "base" else T - 1
    m = rect(T, T, 12, y0, 19, y1)
    wood(spr, m, "v", seed=90, base=2, outline=False)
    spr.put(outline_of(m) & ((spr.a[:, :, 3] == 0)), OUTLINE)
    if kind == "top":
        cap = rect(T, T, 10, 3, 21, 6)
        wood(spr, cap, "h", seed=91, base=3)
        band = rect(T, T, 12, 11, 19, 12)
        spr.put(band, IRON[2])
        spr.put(band & (grid(T, T)[1] == 12), IRON[1])
        nail(spr, 15, 11)
    if kind == "mid":
        spr.put(rect(T, T, 15, 14, 16, 16), WOOD[1])
        spr.px(15, 14, WOOD[0])
    if kind == "base":
        foot = rect(T, T, 8, 26, 23, 31) & ~rect(T, T, 8, 26, 8, 26) & ~rect(T, T, 23, 26, 23, 26)
        col = terrain.cobble_colors(foot, 0, 0, ROCK, 5)
        spr.a[foot, :3] = col[foot]
        spr.a[foot, 3] = 255
        spr.put(foot & ~shift(foot, 0, 1), ROCK[4])
        spr.put(outline_of(foot) & ~spr.opaque, OUTLINE)
        band = rect(T, T, 12, 22, 19, 23)
        spr.put(band, IRON[2])
    return spr


def beam(kind):
    spr = Sprite(T, T)
    x0 = 2 if kind == "l" else 0
    x1 = 29 if kind == "r" else T - 1
    m = rect(T, T, x0, 4, x1, 11)
    wood(spr, m, "h", seed=95, base=2, outline=False)
    spr.put(outline_of(m), OUTLINE)
    if kind in ("l", "r"):
        bx = 5 if kind == "l" else 26
        spr.put(rect(T, T, bx - 1, 6, bx + 1, 9), IRON[1])
        spr.px(bx, 7, IRON[3])
    return spr


def brace():
    W = H = 2 * T
    spr = Sprite(W, H)
    frame = rect(W, H, 3, 3, 60, 8) | rect(W, H, 3, 55, 60, 60)
    d1 = line_mask(W, H, 6, 9, 57, 54, width=6)
    d2 = line_mask(W, H, 57, 9, 6, 54, width=6)
    wood(spr, d1, "h", seed=101, base=1)
    wood(spr, d2, "h", seed=102, base=2)
    for i, m in enumerate((rect(W, H, 3, 3, 60, 8), rect(W, H, 3, 55, 60, 60))):
        wood(spr, m, "h", seed=103 + i, base=2)
    spr.put(rect(W, H, 29, 29, 34, 34), IRON[1])
    spr.put(rect(W, H, 30, 30, 33, 33), IRON[2])
    spr.px(31, 31, IRON[3])
    for x in (6, 57):
        nail(spr, x, 5)
        nail(spr, x, 57)
    del frame
    return spr


def bridge(kind):
    """One-way plank walkway; top surface sits at y=3 like the ground."""
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    # support rope under the planks
    sag = 13 + np.round(2.5 * np.sin(math.pi * xx / T)).astype(int)
    rope = (yy == sag) | (yy == sag + 1)
    spr.put(rope & (yy == sag), ROPE[2])
    spr.put(rope & (yy == sag + 1), ROPE[0])
    # planks with joints every 6 px
    for i, x0 in enumerate(range(0, T, 6)):
        x1 = min(T - 1, x0 + 5)
        if kind == "l" and x0 < 4:
            continue
        if kind == "r" and x1 > 27:
            continue
        m = rect(T, T, x0, 3 + (i % 2 == 0 and kind == "m" and i == 2), x1, 9)
        wood(spr, m, "v", seed=110 + i, base=2 + (i % 2), outline=True)
        if i % 2:
            nail(spr, x0 + 2, 5)
    if kind in ("l", "r"):
        px_ = 1 if kind == "l" else 26
        m = rect(T, T, px_, 0, px_ + 4, 22)
        wood(spr, m, "v", seed=118, base=2)
        spr.put(rect(T, T, px_, 11, px_ + 4, 12), IRON[1])
    return spr


def rail(kind):
    """Rope railing that sits in the cell above a bridge."""
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    sag = 14 + np.round(3 * np.sin(math.pi * xx / T)).astype(int)
    spr.put((yy == sag), ROPE[2])
    spr.put((yy == sag + 1), ROPE[0])
    knot = (np.abs(xx - 16) <= 0) & (yy >= sag - 1) & (yy <= sag + 2)
    spr.put(knot, ROPE[1])
    if kind in ("l", "r"):
        px_ = 1 if kind == "l" else 26
        m = rect(T, T, px_, 10, px_ + 4, T - 1)
        wood(spr, m, "v", seed=119, base=2)
        spr.put(rect(T, T, px_ - 1, 9, px_ + 5, 11), WOOD[3])
        spr.put(outline_of(rect(T, T, px_ - 1, 9, px_ + 5, 11)) & ~spr.opaque, OUTLINE)
    return spr


def crate():
    spr = Sprite(T, T)
    box = rect(T, T, 1, 3, 30, 31)
    wood(spr, box, "h", seed=121, base=2)
    inner = rect(T, T, 5, 7, 26, 27)
    frame = box & ~inner
    wood(spr, frame, "v", seed=122, base=3, outline=False)
    d = line_mask(T, T, 6, 8, 25, 26, width=3) & inner
    wood(spr, d, "h", seed=123, base=3, outline=False)
    spr.put(outline_of(d) & inner & ~d, WOOD[0])
    spr.put(outline_of(inner) & ~inner & box & (inner_edge(box) == 0), WOOD[1])
    for (x, y) in ((3, 5), (28, 5), (3, 28), (28, 28)):
        nail(spr, x, y)
    spr.put(outline_of(box), OUTLINE)
    return spr


def ladder(kind):
    spr = Sprite(T, T)
    y0 = 2 if kind == "top" else 0
    for x0 in (7, 21):
        m = rect(T, T, x0, y0, x0 + 3, T - 1)
        wood(spr, m, "v", seed=130 + x0, base=2)
    for y in range(4 if kind == "top" else 3, T, 8):
        m = rect(T, T, 11, y, 20, y + 1)
        wood(spr, m, "h", seed=140 + y, base=3, outline=False)
        spr.put(rect(T, T, 11, y + 2, 20, y + 2), WOOD[0])
    return spr


def sign_arrow():
    spr = Sprite(T, T)
    pole = rect(T, T, 14, 13, 17, 31)
    wood(spr, pole, "v", seed=150, base=1)
    board = poly(T, T, [(3, 5), (22, 5), (29, 10), (22, 15), (3, 15)])
    wood(spr, board, "h", seed=151, base=3)
    arrow = poly(T, T, [(7, 9), (17, 9), (17, 7), (22, 10), (17, 13), (17, 11), (7, 11)])
    spr.put(arrow, FLAME[3])
    spr.put(arrow & ~shift(arrow, 0, -1), FLAME[1])
    nail(spr, 5, 9)
    return spr


# --------------------------------------------------------------------------
# lights
# --------------------------------------------------------------------------
def _lantern_body(spr, cx, top):
    """Iron-capped glass lantern, 10px wide, 15px tall, centred on cx."""
    cap = rect(spr.w, spr.h, cx - 4, top, cx + 3, top + 2) & ~rect(spr.w, spr.h, cx - 4, top, cx - 4, top)
    cap &= ~rect(spr.w, spr.h, cx + 3, top, cx + 3, top)
    glass = rect(spr.w, spr.h, cx - 3, top + 3, cx + 2, top + 11)
    base_ = rect(spr.w, spr.h, cx - 4, top + 12, cx + 3, top + 13)
    spr.put(glass, FLAME[2])
    spr.put(glass & (grid(spr.w, spr.h)[1] > top + 8), FLAME[1])
    flame(spr, cx - 1, top + 4, 6)
    bars = glass & ((grid(spr.w, spr.h)[0] == cx - 3) | (grid(spr.w, spr.h)[0] == cx + 2))
    spr.put(bars, IRON[1])
    for m in (cap, base_):
        shade(spr, m, IRON, base=1, noise=0, outline=False)
    spr.px(cx - 1, top - 1, IRON[2])
    spr.px(cx, top - 1, IRON[2])
    body = cap | glass | base_
    spr.put(outline_of(body) & ~spr.opaque, OUTLINE)
    return body


def lantern(kind):
    spr = Sprite(T, T)
    if kind == "hanging":
        for y in range(0, 12):
            spr.px(15 + (y % 2), y, IRON[2] if y % 2 else IRON[1])
        _lantern_body(spr, 16, 12)
        halo(spr, 16, 19, 12.5, GLOW_WARM, max_alpha=120)
    elif kind == "wall":
        arm = rect(T, T, 0, 7, 17, 8)
        spr.put(arm, IRON[1])
        spr.put(arm & (grid(T, T)[1] == 7), IRON[2])
        spr.put(line_mask(T, T, 1, 15, 8, 8), IRON[1])
        spr.put(rect(T, T, 0, 4, 2, 17), IRON[0])
        spr.px(16, 9, IRON[2])
        spr.px(16, 10, IRON[1])
        _lantern_body(spr, 17, 11)
        halo(spr, 17, 18, 13, GLOW_WARM, max_alpha=120)
    else:  # standing
        handle = (ellipse(T, T, 16, 13, 4.5, 4.5) & ~ellipse(T, T, 16, 13, 3.2, 3.2)) & (grid(T, T)[1] < 14)
        spr.put(handle, IRON[2])
        _lantern_body(spr, 16, 15)
        foot = rect(T, T, 10, 29, 21, 31)
        shade(spr, foot, IRON, base=1, noise=0)
        halo(spr, 16, 21, 13, GLOW_WARM, max_alpha=120)
    return spr


def light_cookie(color, size=2 * T):
    """Additive-blend light pool for the engine (stepped radial alpha)."""
    spr = Sprite(size, size)
    xx, yy = grid(size, size)
    d = np.sqrt((xx + 0.5 - size / 2) ** 2 + (yy + 0.5 - size / 2) ** 2) / (size / 2)
    for i, (r, a) in enumerate(((1.0, 40), (0.78, 70), (0.56, 110), (0.34, 160), (0.16, 210))):
        spr.put(d < r, color, a)
    return spr


# --------------------------------------------------------------------------
# crystals (blue, decorative)
# --------------------------------------------------------------------------
def crystal(kind):
    if kind == "large":
        spr = Sprite(T, 2 * T)
        halo(spr, 16, 44, 15.5, GLOW_COOL, max_alpha=90)
        for bx, h, hw, t in ((7, 22, 4, -4), (25, 26, 4, 4), (12, 40, 5, -1.5), (20, 33, 5, 2), (16, 16, 4, 0)):
            shard(spr, bx, 62, h, hw, t)
        sparkle(spr, 11, 26, CRYSTAL[5], 2)
        return spr
    spr = Sprite(T, T)
    if kind == "small":
        halo(spr, 16, 22, 14, GLOW_COOL, max_alpha=80)
        for bx, h, hw, t in ((9, 11, 3, -3), (22, 13, 3, 3), (15, 19, 4, 0.5)):
            shard(spr, bx, 30, h, hw, t)
    elif kind == "ceiling":
        halo(spr, 16, 10, 14, GLOW_COOL, max_alpha=80)
        for bx, h, hw, t in ((8, 10, 3, -2), (23, 13, 3, 2), (15, 20, 4, 0)):
            shard(spr, bx, 0, h, hw, t, down=True)
    elif kind == "wall":
        for by, h, hw, t in ((8, 14, 3, 2), (17, 20, 4, 0), (25, 12, 3, -2)):
            pts_spr = Sprite(T, T)
            shard(pts_spr, by, 31, h, hw, t)
            rot = np.rot90(pts_spr.a, k=-1)
            spr.paste(rot, 0, 0)
    return spr


# --------------------------------------------------------------------------
# flora & rock decor
# --------------------------------------------------------------------------
def vine(kind):
    spr = Sprite(T, T)
    strands = [(9, 0.0, 26), (22, 1.7, 17)]
    for sx, ph, end in strands:
        y_end = T if kind != "end" else end
        for y in range(0, y_end):
            x = int(round(sx + 1.4 * math.sin(2 * math.pi * y / T + ph)))
            spr.px(x, y, MOSS[1])
            spr.px(x + 1, y, MOSS[0])
            if (y + int(ph * 5)) % 7 == 0:
                side = -1 if (y // 7) % 2 else 1
                lx = x + (2 if side > 0 else -2)
                for dx in (0, side):
                    spr.px(lx + dx, y, MOSS[3])
                spr.px(lx, y + 1, MOSS[2])
                spr.px(lx + side * 2, y - 1, MOSS[4])
        if kind == "end":
            x = int(round(sx + 1.4 * math.sin(2 * math.pi * end / T + ph)))
            for dx, dy, c in ((0, 0, MOSS[3]), (1, 0, MOSS[2]), (0, 1, MOSS[4]), (-1, 1, MOSS[3]),
                              (1, 1, MOSS[3]), (0, 2, GOLD[3])):
                spr.px(x + dx, end + dy, c)
    if kind == "top":
        clump = ellipse(T, T, 16, 1, 14, 4)
        shade(spr, clump, MOSS, base=2, noise=0.3, seed=161, outline=False)
        spr.put(outline_of(clump) & ~spr.opaque & (grid(T, T)[1] > 0), OUTLINE)
    return spr


def stalactite(kind):
    H = 2 * T if kind == "large" else T
    spr = Sprite(T, H)
    if kind == "large":
        m = poly(T, H, [(4, 0), (28, 0), (22, 16), (18, 34), (16.5, 58), (14, 34), (10, 18)])
        m |= poly(T, H, [(22, 0), (30, 0), (27, 14), (25, 22)])
    else:
        m = poly(T, H, [(6, 0), (24, 0), (19, 10), (16.5, 24), (14, 12)])
        m |= poly(T, H, [(22, 0), (29, 0), (26, 9), (24.5, 15)])
    col = terrain.cobble_colors(m, 0, 0, ROCK, 3, dark=0.3)
    spr.a[m, :3] = col[m]
    spr.a[m, 3] = 255
    xx, yy = grid(T, H)
    spr.put(m & ~shift(m, 1, 0), ROCK[4])
    spr.put(m & ~shift(m, -1, 0), ROCK[0])
    spr.put(m & (yy > H * 0.6) & (hash2(xx, yy, 171) < 0.5), ROCK[1])
    spr.put(outline_of(m) & (yy > 0), OUTLINE)
    # drip of water at the tip
    tip_y = int(np.where(m.any(axis=1))[0].max())
    tip_x = int(np.where(m[tip_y])[0].mean())
    spr.px(tip_x, tip_y + 2, WATER[3])
    spr.px(tip_x, tip_y + 3, WATER[4])
    return spr


# --------------------------------------------------------------------------
# interactables
# --------------------------------------------------------------------------
def save_banner(active=False):
    W, H = T, 2 * T
    spr = Sprite(W, H)
    xx, yy = grid(W, H)
    if active:
        halo(spr, 18, 28, 15, BANNER[3], max_alpha=120)
    pole = rect(W, H, 5, 6, 7, H - 1)
    wood(spr, pole, "v", seed=181, base=2)
    bar = rect(W, H, 5, 7, 29, 9)
    wood(spr, bar, "h", seed=182, base=3)
    fin = ellipse(W, H, 6.5, 4, 2.5, 2.5)
    shade(spr, fin, GOLD, base=3, noise=0)
    cloth = poly(W, H, [(10, 10), (27, 10), (27, 48), (18.5, 42), (10, 48)])
    shade(spr, cloth, BANNER, base=2 + active, noise=0.05, seed=183, outline=True)
    folds = cloth & ((xx == 14) | (xx == 23)) & (yy > 12)
    spr.put(folds, BANNER[1 + active])
    trim = cloth & ((xx == 10) | (xx == 27) | (yy == 10) | (yy == 11))
    spr.put(trim, CLOTH_TRIM[2])
    spr.put(cloth & (yy == 11), CLOTH_TRIM[1])
    # eye emblem
    eye = ellipse(W, H, 18.5, 26, 6.5, 3.6)
    spr.put(eye, (230, 245, 225) if not active else (255, 255, 240))
    spr.put(outline_of(eye) & cloth, BANNER[0])
    iris = ellipse(W, H, 18.5, 26, 2.6, 2.6)
    spr.put(iris, BANNER[1] if not active else GOLD[2])
    spr.px(18, 26, OUTLINE)
    spr.px(17, 25, (255, 255, 255))
    for x in (11, 26):
        spr.px(x, 10, GOLD[4])
    # foot plate
    foot = rect(W, H, 3, H - 3, 9, H - 1)
    shade(spr, foot, IRON, base=1, noise=0)
    return spr


def reward(kind):
    spr = Sprite(T, T)
    if kind == "challenge":
        halo(spr, 16, 17, 15.5, GLOW_GOLD, max_alpha=140)
        for bx, h, hw, t in ((8, 12, 3, -4), (24, 14, 3, 4), (12, 20, 4, -1.5), (20, 18, 4, 2), (16, 26, 4, 0)):
            shard(spr, bx, 30, h, hw, t, ramp=GOLD)
        sparkle(spr, 6, 7, GOLD[5], 2)
        sparkle(spr, 26, 5, GOLD[5], 1)
        sparkle(spr, 28, 14, (255, 255, 255), 1)
    else:
        halo(spr, 16, 21, 13, GLOW_GOLD, max_alpha=120)
        for bx, h, hw, t in ((11, 10, 3, -3), (21, 11, 3, 3), (16, 17, 4, 0)):
            shard(spr, bx, 30, h, hw, t, ramp=GOLD)
        sparkle(spr, 25, 12, GOLD[5], 1)
    return spr


def bat_nest():
    W, H = 2 * T, T
    spr = Sprite(W, H)
    xx, yy = grid(W, H)
    for x0, x1 in ((14, 22), (32, 32), (50, 42)):
        spr.put(line_mask(W, H, x0, 0, x1, 12), ROPE[1])
    bowl = ellipse(W, H, 32, 18, 21, 10) & (yy >= 12)
    shade(spr, bowl, WOOD, base=1, noise=0.25, seed=191)
    inner = ellipse(W, H, 32, 15, 16, 5)
    spr.put(inner & bowl, WOOD[0])
    twigs = bowl & ((xx + yy * 2) % 7 == 0) & (hash2(xx, yy, 192) > 0.35)
    spr.put(twigs, WOOD[3])
    twigs2 = bowl & ((xx - yy * 2) % 9 == 0) & (hash2(xx, yy, 193) > 0.4)
    spr.put(twigs2, WOOD[2])
    for x0, y0, x1, y1 in ((9, 14, 2, 10), (55, 15, 62, 11), (14, 24, 8, 28), (50, 24, 57, 28)):
        spr.put(line_mask(W, H, x0, y0, x1, y1), WOOD[2])
    for ex, ey in ((25, 15), (37, 14)):
        spr.px(ex, ey, EYE_RED[1])
        spr.px(ex + 2, ey, EYE_RED[1])
    spr.put(outline_of(spr.opaque & (spr.a[:, :, 3] == 255)) & ~spr.opaque, OUTLINE)
    return spr


# --------------------------------------------------------------------------
# characters (scale references)
# --------------------------------------------------------------------------
def slime():
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    body = ellipse(T, T, 16, 22, 12, 10) & (yy <= 30)
    body |= rect(T, T, 6, 26, 25, 30)
    shade(spr, body, SLIME, base=2, noise=0.04, seed=201)
    spr.put(body & (yy >= 29), SLIME[1])
    shine = ellipse(T, T, 10.5, 17, 2.4, 1.6)
    spr.put(shine & body, SLIME[4])
    for ex in (12, 19):
        eye = rect(T, T, ex, 19, ex + 1, 22)
        spr.put(eye, OUTLINE)
        spr.px(ex, 19, (255, 255, 255))
    spr.put(rect(T, T, 15, 24, 16, 24), SLIME[0])
    spr.px(9, 25, (255, 150, 190))
    spr.px(22, 25, (255, 150, 190))
    return spr


def bat(frame):
    W, H = 2 * T, T
    spr = Sprite(W, H)
    up = frame == "a"
    if up:
        wing_l = [(28, 13), (16, 4), (4, 2), (8, 9), (6, 15), (13, 14), (14, 20), (22, 17), (28, 19)]
    else:
        wing_l = [(28, 13), (18, 15), (6, 18), (9, 22), (5, 27), (13, 25), (16, 29), (22, 23), (28, 19)]
    wing_r = [(W - 1 - x, y) for (x, y) in wing_l]
    for i, pts in enumerate((wing_l, wing_r)):
        m = poly(W, H, pts)
        shade(spr, m, BAT, base=2, noise=0.05, seed=211 + i)
        bones = [pts[0], pts[2]], [pts[0], pts[4]], [pts[0], pts[6]]
        for (a, b) in bones:
            spr.put(line_mask(W, H, a[0], a[1], b[0], b[1]) & m, BAT[1])
    body = ellipse(W, H, 32, 16, 6.5, 8)
    ears = poly(W, H, [(26, 11), (27, 3), (30, 9)]) | poly(W, H, [(38, 11), (37, 3), (34, 9)])
    shade(spr, body | ears, BAT, base=2, noise=0.05, seed=215)
    belly = ellipse(W, H, 32, 19, 3.5, 4.5)
    spr.put(belly & body, BAT[3])
    for ex in (29, 35):
        spr.px(ex, 13, EYE_RED[1])
        spr.px(ex - 1 if ex < 32 else ex + 1, 13, EYE_RED[0])
        spr.px(ex, 12, EYE_RED[2])
    spr.px(30, 17, (240, 240, 240))
    spr.px(34, 17, (240, 240, 240))
    halo(spr, 32, 13, 6, GLOW_RED, max_alpha=60)
    return spr


def golem():
    W = H = 2 * T
    spr = Sprite(W, H)
    xx, yy = grid(W, H)
    # crystals on its back (drawn first so the body overlaps their roots)
    for bx, by, h, hw, t in ((20, 26, 12, 4, -5), (30, 22, 18, 5, -1), (40, 24, 15, 4, 4), (47, 30, 10, 3, 6)):
        shard(spr, bx, by, h, hw, t)
    body = ellipse(W, H, 32, 40, 25, 19)
    feet = ellipse(W, H, 19, 58, 7, 4) | ellipse(W, H, 45, 58, 7, 4)
    shade(spr, feet, GOLEM, base=1, noise=0.05, seed=221)
    col = terrain.cobble_colors(body, 0, 0, GOLEM, 13, dark=0.0)
    spr.a[body, :3] = col[body]
    spr.a[body, 3] = 255
    spr.put(body & ~shift(body, 0, 1), GOLEM[4])
    spr.put(body & ~shift(body, 0, -1), GOLEM[0])
    spr.put(outline_of(body) & ~feet, OUTLINE)
    # brow plate and glowing eyes
    brow = poly(W, H, [(17, 37), (47, 37), (44, 41), (20, 41)])
    shade(spr, brow, GOLEM, base=1, noise=0)
    for ex in (24, 37):
        eye = poly(W, H, [(ex, 42), (ex + 5, 42), (ex + 4, 46), (ex + 1, 46)])
        spr.put(eye, EYE_AMBER[1])
        spr.put(eye & (yy == 42), EYE_AMBER[2])
        spr.put(outline_of(eye) & body, OUTLINE)
    mouth = rect(W, H, 27, 50, 37, 51)
    spr.put(mouth, OUTLINE)
    for x in (29, 33, 36):
        spr.px(x, 50, GOLEM[3])
    return spr


# --------------------------------------------------------------------------
# background
# --------------------------------------------------------------------------
def waterfall(kind):
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    phase = 8 if kind == "b" else 0
    col = (xx >= 9) & (xx <= 22)
    if kind == "top":
        lip = (yy <= 5) & (xx >= 3) & (xx <= 28)
        c = terrain.cobble_colors(lip, 0, 0, ROCK_FAR, 8)
        spr.a[lip, :3] = c[lip]
        spr.a[lip, 3] = 255
        spr.put(lip & (yy == 0), ROCK_FAR[3])
        col &= yy >= 4
    if kind == "splash":
        col &= yy <= 18
    streak = hash2(xx, ((yy + phase) // 4) % 8, 231)
    t = np.where(streak > 0.7, 3, np.where(streak > 0.35, 2, 1))
    t = np.where((xx == 9) | (xx == 22), 3, t)
    t = np.where((xx == 10) | (xx == 21), np.maximum(t, 2), t)
    pal = np.array(WATER, np.uint8)
    spr.a[col, :3] = pal[t[col]]
    spr.a[col, 3] = 215
    if kind == "splash":
        foam = ellipse(T, T, 16, 22, 14, 8) | ellipse(T, T, 9, 26, 7, 5) | ellipse(T, T, 23, 26, 7, 5)
        spr.put(foam, WATER[3], 230)
        spr.put(foam & (hash2(xx, yy, 232) > 0.55), WATER[4], 240)
        spr.put(outline_of(foam) & ~col, WATER[2], 160)
        for i in range(8):
            x = int(hash2(i, 1, 233) * 30) + 1
            y = int(hash2(i, 2, 234) * 12) + 6
            if not spr.opaque[y, x]:
                spr.px(x, y, WATER[4], 220)
    return spr


def water(kind):
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    if kind == "surface":
        top = 8 + np.round(np.sin(2 * math.pi * xx / 16)).astype(int)
        body = yy >= top
        spr.put(body, WATER[1], 200)
        spr.put(body & (yy > 20), WATER[0], 210)
        spr.put(body & (yy == top), WATER[4], 235)
        spr.put(body & (yy == top + 1), WATER[3], 220)
        glint = body & (yy > top + 3) & (hash2(xx // 3, yy, 241) > 0.93)
        spr.put(glint, WATER[3], 210)
    else:
        spr.put(np.ones((T, T), bool), WATER[0], 210)
        glint = (hash2(xx // 3, yy, 242) > 0.95)
        spr.put(glint, WATER[1], 210)
    return spr


def bg_fence():
    """Distant railing silhouette, tiles horizontally."""
    spr = Sprite(T, T)
    xx, yy = grid(T, T)
    c = ROCK_BG[2]
    spr.put(rect(T, T, 0, 12, T - 1, 14), c)
    spr.put(rect(T, T, 0, 21, T - 1, 22), c)
    spr.put(rect(T, T, 4, 8, 7, T - 1), c)
    spr.put(rect(T, T, 20, 8, 23, T - 1), c)
    spr.put(rect(T, T, 3, 7, 8, 8), ROCK_BG[3])
    spr.put(rect(T, T, 19, 7, 24, 8), ROCK_BG[3])
    spr.put(rect(T, T, 0, 12, T - 1, 12), ROCK_BG[3])
    return spr
