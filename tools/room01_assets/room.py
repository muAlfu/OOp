"""Room 01 – The Deep Entrance, rebuilt only from the modular pieces.

The tilemap is 46 x 20 cells of 32 px (1472 x 640). Terrain cells are
autotiled from their neighbours; everything else is placed from a list.
"""
import numpy as np

import terrain
from palette import BG_BOTTOM, BG_TOP, GLOW_COOL, GLOW_GOLD, GLOW_RED, GLOW_WARM, BANNER
from px import Sprite, grid

T = 32
W, H = 46, 20

# terrain glyphs
SOLID, EMPTY, UNDER = "#", ".", "u"
CRUMBLE, HAZARD, BRIDGE, CRATE, LADDER, BARRIER = "=", "^", "-", "C", "H", "B"


def build_grid():
    g = [[EMPTY] * W for _ in range(H)]

    def fill(x0, y0, x1, y1, ch=SOLID):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = ch

    # ceiling
    fill(0, 0, 45, 1)
    fill(0, 2, 6, 2)
    fill(3, 3, 6, 3)
    fill(9, 2, 11, 3)
    fill(9, 4, 10, 7)                   # rock pillar above the breakable barrier
    fill(15, 2, 27, 2)
    fill(19, 3, 26, 3)
    fill(21, 4, 24, 4)                  # bat-nest outcrop
    fill(32, 2, 45, 2)
    fill(38, 3, 45, 3)                  # roof of the exit passage
    # 01 entry and the stepped left mass
    fill(0, 6, 4, 11)
    fill(5, 8, 7, 11)
    fill(8, 10, 11, 11)
    g[9][9] = BARRIER                   # 2 cells tall, anchored on its bottom cell
    for x in (12, 13, 14):
        g[11][x] = CRUMBLE              # 02 safe trial
    # 03 optional nook + lower-left terraces
    fill(0, 12, 1, 19)
    fill(0, 14, 3, 19)
    fill(4, 16, 6, 19)
    # main floor
    fill(0, 18, 28, 19)
    g[17][8] = CRATE
    g[17][28] = CRATE
    # floating islands (air section)
    fill(11, 15, 13, 15)                # E
    fill(15, 13, 17, 13)                # A
    fill(20, 11, 24, 12)                # B
    fill(25, 11, 26, 11, BRIDGE)        # optional central path
    fill(28, 9, 32, 10)                 # C – challenge reward
    fill(34, 13, 36, 13)                # D – short return
    # 05 hazard pit with sequential crumbling platforms
    fill(29, 19, 37, 19)
    fill(29, 18, 37, 18, HAZARD)
    for x in (29, 30, 32, 33, 35, 36):
        g[16][x] = CRUMBLE
    # right side: floor, wall, ledge, ladders, save island
    fill(38, 18, 45, 19)
    fill(40, 7, 45, 17)
    g[11][39] = SOLID
    fill(38, 11, 38, 17, LADDER)
    fill(39, 7, 39, 10, LADDER)
    fill(34, 7, 38, 8)                  # 06 rest & save
    _add_undersides(g)
    return g


def _add_undersides(g):
    """Hang underside rock below every floating terrain component."""
    seen = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] != SOLID or (x, y) in seen:
                continue
            comp, stack, border = [], [(x, y)], False
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                if cx in (0, W - 1) or cy in (0, H - 1):
                    border = True
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < W and 0 <= ny < H and g[ny][nx] == SOLID and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            if border:
                continue
            for cx, cy in comp:
                if cy + 1 < H and g[cy + 1][cx] == EMPTY:
                    g[cy + 1][cx] = UNDER


def _solid_for_tiling(g, x, y):
    if x < 0 or y < 0 or x >= W or y >= H:
        return True
    return g[y][x] in (SOLID, UNDER, HAZARD, CRATE)


def _run_kind(g, x, y, ch, single="s"):
    left = x > 0 and g[y][x - 1] == ch
    right = x < W - 1 and g[y][x + 1] == ch
    if left and right:
        return "m"
    if right:
        return "l"
    if left:
        return "r"
    return single


def terrain_layer(g):
    """[(asset_id, x_px, y_px)] for every terrain cell."""
    out = []
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            px, py = x * T, y * T
            if c == SOLID:
                s = lambda dx, dy: _solid_for_tiling(g, x + dx, y + dy)
                name = terrain.classify(s(0, -1), s(1, 0), s(0, 1), s(-1, 0),
                                        s(-1, -1), s(1, -1), s(-1, 1), s(1, 1))
                out.append((name, px, py))
            elif c == UNDER:
                out.append(("under_" + _run_kind(g, x, y, UNDER), px, py))
            elif c == CRUMBLE:
                k = _run_kind(g, x, y, CRUMBLE, single="m")
                state = 1 if (x, y) in ((32, 16), (33, 16)) else 0
                out.append((f"crumble_{k}_{state}", px, py))
            elif c == HAZARD:
                out.append(("hazard_a" if x % 2 else "hazard_b", px, py))
            elif c == BRIDGE:
                out.append(("bridge_" + _run_kind(g, x, y, BRIDGE, single="m"), px, py))
            elif c == CRATE:
                out.append(("crate", px, py))
            elif c == LADDER:
                top = y == 0 or g[y - 1][x] != LADDER
                out.append(("ladder_top" if top else "ladder_mid", px, py))
            elif c == BARRIER:
                out.append(("barrier_0", px, py - T + 3))
    return out


# (asset_id, col, row, dy_px, flip) – row is the top cell of the sprite
BACK_DECOR = [
    *[("waterfall_top", 18, 3, 0, False)],
    *[("waterfall_a", 18, r, 0, False) for r in range(4, 17)],
    ("waterfall_splash", 18, 17, 0, False),
    ("waterfall_top", 30, 12, 0, False),
    *[("waterfall_b", 30, r, 0, False) for r in range(13, 17)],
    ("waterfall_splash", 30, 17, 0, False),
    *[("water_surface", x, 17, 0, False) for x in range(9, 28) if x not in (18,)],
    *[("bg_fence", x, 15, 0, False) for x in range(31, 38)],
    ("brace", 25, 13, 0, False),
    *[("post_mid", 26, r, 0, False) for r in range(12, 17)],
    ("post_base", 26, 17, 3, False),
]

FRONT_DECOR = [
    # 01 entry
    ("player_slime", 1, 5, 3, False),
    ("lantern_stand", 3, 5, 3, False),
    ("lantern_hanging", 5, 4, 0, False),
    ("vine_top", 7, 2, 0, False), ("vine_mid", 7, 3, 0, False), ("vine_end", 7, 4, 0, False),
    ("lantern_wall", 8, 5, 0, True),
    ("crystal_wall", 11, 5, 0, False),
    ("stalactite_s", 8, 12, 0, False),
    # 03 optional nook
    ("lantern_wall", 2, 12, 0, False),
    ("crystal_small", 3, 13, 3, False),
    ("reward_small", 5, 15, 3, False),
    ("vine_top", 6, 12, 0, False), ("vine_mid", 6, 13, 0, False), ("vine_end", 6, 14, 0, False),
    ("vine_top", 10, 12, 0, False), ("vine_end", 10, 13, 0, False),
    # air section
    ("crystal_ceiling", 14, 2, 0, False),
    ("stalactite_s", 16, 3, 0, False),
    ("crystal_small", 12, 14, 3, False),
    ("crystal_small", 16, 12, 3, False),
    ("crystal_small", 21, 10, 3, False),
    ("crystal_ceiling", 21, 5, 0, False),
    ("crystal_ceiling", 24, 5, 0, False),
    ("bat_nest", 22, 5, 0, False),
    ("vine_top", 27, 3, 0, False), ("vine_end", 27, 4, 0, False),
    ("stalactite_l", 29, 2, 0, False),
    ("stalactite_s", 31, 2, 0, False),
    ("rail_l", 25, 10, 0, False), ("rail_r", 26, 10, 0, False),
    ("bat_a", 23, 7, 6, False),
    ("bat_b", 29, 5, 10, False),
    ("reward_challenge", 31, 8, 3, False),
    # 04 encounter
    ("golem", 21, 16, 3, False),
    # 06 save + exit
    ("vine_top", 33, 3, 0, False), ("vine_mid", 33, 4, 0, False), ("vine_end", 33, 5, 0, False),
    ("stalactite_s", 36, 3, 0, False),
    ("lantern_hanging", 35, 4, 3, False),
    ("lantern_hanging", 37, 4, 3, False),
    ("post_top", 34, 4, 3, False), ("post_mid", 34, 5, 3, False), ("post_base", 34, 6, 3, False),
    ("beam_m", 35, 4, 3, False), ("beam_m", 36, 4, 3, False), ("beam_r", 37, 4, 3, False),
    ("save_banner_on", 36, 5, 3, False),
    ("crystal_small", 41, 6, 3, False),
    ("vine_top", 42, 4, 0, False), ("vine_end", 42, 5, 0, False),
    ("sign_exit", 44, 6, 3, False),
    ("lantern_wall", 39, 14, 0, True),
    ("lantern_stand", 42, 17, 3, False),
    ("crystal_large", 44, 16, 3, False),
]

# additive light pools: (x_px, y_px, radius_px, colour, strength)
LIGHTS = [
    (3.5 * T, 5.6 * T, 70, GLOW_WARM, 0.55), (5.5 * T, 4.6 * T, 70, GLOW_WARM, 0.5),
    (8.4 * T, 5.6 * T, 60, GLOW_WARM, 0.45), (2.6 * T, 12.6 * T, 62, GLOW_WARM, 0.5),
    (5.5 * T, 15.5 * T, 48, GLOW_GOLD, 0.5), (31.5 * T, 8.4 * T, 64, GLOW_GOLD, 0.6),
    (35.5 * T, 4.9 * T, 64, GLOW_WARM, 0.5), (37.5 * T, 4.9 * T, 64, GLOW_WARM, 0.5),
    (36.5 * T, 6.0 * T, 56, BANNER[3], 0.35), (39.4 * T, 14.6 * T, 60, GLOW_WARM, 0.45),
    (42.5 * T, 17.6 * T, 60, GLOW_WARM, 0.45), (44.5 * T, 17.0 * T, 56, GLOW_COOL, 0.45),
    (18.5 * T, 10.0 * T, 150, GLOW_COOL, 0.22), (30.5 * T, 15.0 * T, 90, GLOW_COOL, 0.22),
    (1.5 * T, 5.6 * T, 40, GLOW_COOL, 0.35), (11.6 * T, 5.5 * T, 44, GLOW_COOL, 0.35),
    (14.5 * T, 2.5 * T, 40, GLOW_COOL, 0.35), (22.5 * T, 5.5 * T, 56, GLOW_COOL, 0.3),
    (22.0 * T, 17.0 * T, 50, GLOW_WARM, 0.25),
    *[(x * T, 18.7 * T, 52, GLOW_RED, 0.55) for x in (29.5, 31.5, 33.5, 35.5, 37.5)],
]


def _additive(canvas, cx, cy, r, color, strength):
    h, w = canvas.shape[:2]
    xx, yy = grid(w, h)
    d = np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) / r
    # quantised falloff keeps the pixel-art look
    f = np.clip(1 - d, 0, 1)
    f = np.floor(f ** 1.4 * 7) / 7
    add = f[:, :, None] * np.array(color, np.float32)[None, None, :] * strength
    canvas[:, :, :3] = np.clip(canvas[:, :, :3] + add, 0, 255)


def compose(assets):
    """Render the room. `assets` = {id: (Sprite, meta)} from catalog.build()."""
    g = build_grid()
    room = Sprite(W * T, H * T)

    # background: back wall + vertical fade + soft cave glow
    bg = assets["bg_wall"][0]
    for y in range(H):
        for x in range(W):
            room.paste(bg, x * T, y * T)
    canvas = room.a.astype(np.float32)
    xx, yy = grid(W * T, H * T)
    t = yy / (H * T)
    tint = (np.array(BG_TOP)[None, None, :] * (1 - t[:, :, None]) + np.array(BG_BOTTOM)[None, None, :] * t[:, :, None])
    canvas[:, :, :3] = canvas[:, :, :3] * 0.6 + tint * 0.3
    _additive(canvas, 24 * T, 11 * T, 15 * T, GLOW_COOL, 0.12)
    room.a = np.clip(canvas, 0, 255).astype(np.uint8)

    def place(layer):
        for aid, col, row, dy, flip in layer:
            spr = assets[aid][0]
            if flip:
                spr = spr.flip_x()
            room.paste(spr, col * T, row * T + dy)

    place(BACK_DECOR)
    for aid, px_, py_ in terrain_layer(g):
        room.paste(assets[aid][0], px_, py_)
    place(FRONT_DECOR)

    canvas = room.a.astype(np.float32)
    for (cx, cy, r, color, s) in LIGHTS:
        _additive(canvas, cx, cy, r, color, s)
    # vignette
    d = np.sqrt(((xx + 0.5) / (W * T) - 0.5) ** 2 * 1.2 + ((yy + 0.5) / (H * T) - 0.5) ** 2)
    v = np.clip(1.08 - d * 0.75, 0.55, 1.0)
    v = np.floor(v * 12) / 12
    canvas[:, :, :3] *= v[:, :, None]
    room.a = np.clip(canvas, 0, 255).astype(np.uint8)
    return room, g


# route callouts for the annotated preview: (text, col, row, numbered)
CALLOUTS = [
    ("٠١ الدخول", 1.6, 3.2, True),
    ("حاجز يُكسر", 9.5, 7.0, False),
    ("٠٢ تجربة آمنة", 13.5, 10.0, True),
    ("٠٣ ممر اختياري", 4.6, 14.0, True),
    ("مكافأة", 5.5, 16.8, False),
    ("٠٤ مواجهة", 22.0, 14.6, True),
    ("موطن الخفافيش", 22.6, 4.3, False),
    ("خفاش ١", 24.0, 6.6, False),
    ("مسار مركزي اختياري", 25.5, 12.4, False),
    ("خفاش ٢", 30.0, 5.0, False),
    ("مكافأة التحدي", 30.5, 7.4, False),
    ("عودة قصيرة", 35.0, 12.0, False),
    ("٠٥ عبور متتابع", 33.0, 15.2, True),
    ("٠٦ استراحة وحفظ", 36.0, 3.0, True),
    ("ممر متصل", 43.0, 4.2, False),
]
