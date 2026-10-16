"""Presentation sheet: every module at x3 with bilingual labels, an assembled
terrain demo, the rebuilt room, the palette and a usage legend."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import catalog
import room
import terrain
from palette import SWATCHES
from px import Sprite, upscale

S = 3
SHEET_W = 2560
M = 40
GAP = 26
T = 32

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
C = dict(
    bg=(6, 10, 26), panel=(11, 18, 44), edge=(30, 46, 98), head=(16, 26, 62),
    cell_a=(15, 24, 56), cell_b=(18, 29, 66), cell_line=(36, 56, 116),
    text=(234, 240, 252), dim=(134, 154, 204), mono=(112, 134, 196),
    gold=(255, 210, 90), cyan=(124, 212, 255),
)
COLLISION = {
    "solid": ((92, 142, 255), "صلب", "solid"),
    "one_way": ((255, 186, 76), "منصة عبور", "one-way"),
    "hazard": ((255, 76, 108), "ضرر", "hazard"),
    "breakable": ((214, 142, 72), "قابل للكسر", "breakable"),
    "trigger": ((92, 212, 142), "مُحفِّز", "trigger"),
    "none": ((96, 108, 150), "زينة", "decor"),
}
ANCHORS = [
    ("grid", "يملأ خانته على الشبكة", "fills its cells"),
    ("ground", "يقف على الأرض بإزاحة 3px", "stands on floor, +3px"),
    ("ceiling", "يتدلى من الخانة العليا", "hangs from cell above"),
    ("free", "حر الحركة / مؤثرات", "free / fx"),
]


def font(size, bold=False, mono=False):
    name = "DejaVuSansMono.ttf" if mono else ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(FONT_DIR + name, size)


F = dict(
    title_ar=font(66, True), title_en=font(30, True), sub=font(22),
    h_ar=font(30, True), h_en=font(19, True), lbl_ar=font(18), id=font(14, mono=True),
    small=font(17), small_b=font(17, True), call=font(15, True), chip=font(18, True),
)


def is_ar(s):
    return any("؀" <= ch <= "ۿ" for ch in s)


def _kw(s):
    return dict(direction="rtl", language="ar") if is_ar(s) else {}


def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f, **_kw(s))
    return b[2] - b[0], b[3] - b[1]


def text(d, x, y, s, f, fill, align="l"):
    """Draw text with its top-left / top-centre / top-right at (x, y)."""
    w, h = tsize(d, s, f)
    b = d.textbbox((0, 0), s, font=f, **_kw(s))
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    d.text((x - b[0], y - b[1]), s, font=f, fill=fill, **_kw(s))
    return w, h


def backdrop(w, h):
    """Checker with 32px cell lines so each module shows its grid footprint."""
    a = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    chk = ((xx // (8 * S)) + (yy // (8 * S))) % 2 == 0
    a[:] = C["cell_a"]
    a[chk] = C["cell_b"]
    line = (xx % (T * S) == 0) | (yy % (T * S) == 0) | (xx == w - 1) | (yy == h - 1)
    a[line] = C["cell_line"]
    return Image.fromarray(a, "RGB").convert("RGBA")


def item_block(spr, meta):
    pad = 10
    sw, sh = spr.w * S, spr.h * S
    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    aw, ah = tsize(probe, meta["ar"], F["lbl_ar"])
    iw, ih = tsize(probe, meta["id"], F["id"])
    bw = max(sw, aw, iw + 18) + 2 * pad
    bh = pad + sh + 12 + 24 + 4 + 18 + pad
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), 10, fill=(14, 22, 52), outline=(26, 40, 86))
    x0 = (bw - sw) // 2
    im.alpha_composite(backdrop(sw, sh), (x0, pad))
    im.alpha_composite(upscale(spr.image(), S), (x0, pad))
    y = pad + sh + 10
    text(d, bw / 2, y, meta["ar"], F["lbl_ar"], C["text"], "c")
    y += 28
    col = COLLISION[meta["collision"]][0]
    tx = bw / 2 - (iw + 14) / 2
    d.ellipse((tx, y + 3, tx + 9, y + 12), fill=col)
    text(d, tx + 14, y, meta["id"], F["id"], C["mono"])
    return im


def panel_header(d, x, y, w, en, ar, count):
    d.rounded_rectangle((x, y, x + w, y + 58), 12, fill=C["head"])
    d.rectangle((x, y + 40, x + w, y + 58), fill=C["head"])
    text(d, x + w - 22, y + 12, ar, F["h_ar"], C["text"], "r")
    text(d, x + 22, y + 13, en.upper(), F["h_en"], C["cyan"])
    tw, _ = tsize(d, en.upper(), F["h_en"])
    if count:
        text(d, x + 22 + tw + 14, y + 15, f"· {count}", F["small"], C["dim"])


def flow(blocks, width):
    """Place block images left-to-right with wrapping; returns positions, height."""
    pos, x, y, row_h = [], 0, 0, 0
    for b in blocks:
        if x and x + b.width > width:
            x, y = 0, y + row_h + 16
            row_h = 0
        pos.append((x, y))
        x += b.width + 16
        row_h = max(row_h, b.height)
    return pos, y + row_h


class Panel:
    def __init__(self, en, ar, count, body, body_h):
        self.en, self.ar, self.count, self.body, self.body_h = en, ar, count, body, body_h

    def draw(self, sheet, x, y, w, h):
        d = ImageDraw.Draw(sheet)
        d.rounded_rectangle((x, y, x + w, y + h), 14, fill=C["panel"], outline=C["edge"], width=2)
        panel_header(d, x, y, w, self.en, self.ar, self.count)
        self.body(sheet, x + 22, y + 58 + 20, w - 44)


def items_panel(sec, assets, width):
    sec_id, en, ar, items = sec
    blocks = [item_block(*assets[i[0]]) for i in items]
    pos, h = flow(blocks, width - 44)

    def body(sheet, x, y, w):
        for b, (bx, by) in zip(blocks, pos):
            sheet.alpha_composite(b, (x + bx, y + by))
    return Panel(en, ar, f"{len(items)} modules", body, h)


# --------------------------------------------------------------------------
# terrain panel: canonical layout + seamless assembly demo
# --------------------------------------------------------------------------
TERRAIN_SLOTS = {
    "ground_tl": (0, 0), "ground_t": (1, 0), "ground_tr": (2, 0),
    "ground_l": (0, 1), "ground_c": (1, 1), "ground_r": (2, 1),
    "ground_bl": (0, 2), "ground_b": (1, 2), "ground_br": (2, 2),
    "ground_inner_tl": (3, 0), "ground_inner_tr": (4, 0),
    "ground_inner_bl": (3, 1), "ground_inner_br": (4, 1), "block": (3, 2),
    "ledge_l": (5, 0), "ledge_m": (6, 0), "ledge_r": (7, 0),
    "column_t": (5, 1), "column_m": (6, 1), "column_b": (7, 1),
}
DEMO = [
    ".........",
    "..##.....",
    "..####..#",
    "....##..#",
    "###.##.##",
    "#########",
]


def demo_sprite(assets):
    h, w = len(DEMO), len(DEMO[0])
    spr = Sprite(w * T, h * T)
    for y in range(h):
        for x in range(w):
            spr.paste(assets["bg_wall"][0], x * T, y * T)

    def s(x, y):
        if y >= h:
            return True
        if x < 0 or x >= w or y < 0:
            return False
        return DEMO[y][x] == "#"
    for y in range(h):
        for x in range(w):
            if DEMO[y][x] != "#":
                continue
            name = terrain.classify(s(x, y - 1), s(x + 1, y), s(x, y + 1), s(x - 1, y),
                                    s(x - 1, y - 1), s(x + 1, y - 1), s(x - 1, y + 1), s(x + 1, y + 1))
            spr.paste(assets[name][0], x * T, y * T)
    for aid, x, y, dy in (("crystal_small", 3, 0, 3), ("vine_top", 4, 2, 0), ("vine_end", 4, 3, 0),
                          ("lantern_stand", 0, 3, 3), ("crate", 6, 3, 0), ("crystal_large", 7, 2, 3)):
        spr.paste(assets[aid][0], x * T, y * T + dy)
    for aid, x, y in (("crumble_l_0", 6, 1), ("crumble_r_0", 7, 1)):
        spr.paste(assets[aid][0], x * T, y * T)
    return spr


def terrain_panel(assets, width):
    sec = catalog.SECTIONS[0]
    blocks = {i[0]: item_block(*assets[i[0]]) for i in sec[3]}
    sw = max(b.width for b in blocks.values()) + 12
    sh = max(b.height for b in blocks.values()) + 12
    demo = upscale(demo_sprite(assets).image(), S)
    demo_x = 8 * sw + 40
    h = max(3 * sh, demo.height + 46)

    def body(sheet, x, y, w):
        for name, (cx, cy) in TERRAIN_SLOTS.items():
            b = blocks[name]
            sheet.alpha_composite(b, (x + cx * sw + (sw - 12 - b.width) // 2, y + cy * sh))
        d = ImageDraw.Draw(sheet)
        dx = x + demo_x
        text(d, dx + demo.width, y, "مثال تركيب: القطع تتصل بلا فواصل", F["small_b"], C["gold"], "r")
        text(d, dx, y + 2, "ASSEMBLED · SEAMLESS EDGES", F["h_en"], C["dim"])
        sheet.alpha_composite(demo, (dx, y + 36))
        d.rectangle((dx - 1, y + 35, dx + demo.width, y + 36 + demo.height), outline=C["edge"], width=2)
    return Panel(sec[1], sec[2], f"{len(sec[3])} tiles · 16 + 4 inner corners", body, h)


# --------------------------------------------------------------------------
# room + legend
# --------------------------------------------------------------------------
def callout(d, cx, cy, s, numbered, f, k=1):
    w, h = tsize(d, s, f)
    px_, py_ = 9 * k, 7 * k
    x0, y0, x1, y1 = cx - w / 2 - px_, cy - h / 2 - py_, cx + w / 2 + px_, cy + h / 2 + py_
    d.rounded_rectangle((x0 + 2 * k, y0 + 3 * k, x1 + 2 * k, y1 + 3 * k), 7 * k, fill=(0, 0, 0, 150))
    d.rounded_rectangle((x0, y0, x1, y1), 7 * k, fill=(8, 12, 30, 235),
                        outline=C["gold"] if numbered else (210, 220, 240), width=2 * k)
    text(d, cx, cy - h / 2, s, f, C["gold"] if numbered else C["text"], "c")


def annotate(room_img, scale=1):
    im = room_img.copy()
    d = ImageDraw.Draw(im, "RGBA")
    f = F["call"] if scale == 1 else font(13 * scale + 2, True)
    for s, col, row, numbered in room.CALLOUTS:
        callout(d, col * T * scale, row * T * scale, s, numbered, f, k=scale)
    return im


def room_panel(room_img):
    img = annotate(room_img)

    def body(sheet, x, y, w):
        sheet.alpha_composite(img, (x, y))
        d = ImageDraw.Draw(sheet)
        d.rectangle((x - 1, y - 1, x + img.width, y + img.height), outline=C["edge"], width=2)
    return Panel("Room 01 rebuilt from the modules · 1:1", "الغرفة الأولى مبنية من القطع",
                 f"{room.W}×{room.H} tiles · {room.W * T}×{room.H * T} px", body, img.height)


def legend_panel(width):
    def body(sheet, x, y, w):
        d = ImageDraw.Draw(sheet)
        cy = y
        text(d, x + w, cy, "التصادم", F["h_ar"], C["text"], "r")
        text(d, x, cy + 8, "COLLISION", F["h_en"], C["cyan"])
        cy += 50
        items = list(COLLISION.items())
        colw = w // 2
        for i, (k, (col, ar, en)) in enumerate(items):
            ix = x + (i % 2) * colw
            iy = cy + (i // 2) * 36
            d.ellipse((ix, iy + 4, ix + 16, iy + 20), fill=col)
            text(d, ix + 26, iy + 2, en, F["small_b"], C["text"])
            text(d, ix + colw - 48, iy, ar, F["lbl_ar"], C["dim"], "r")
        cy += 3 * 36 + 22
        text(d, x + w, cy, "طريقة التثبيت", F["h_ar"], C["text"], "r")
        text(d, x, cy + 8, "ANCHOR", F["h_en"], C["cyan"])
        cy += 50
        for k, ar, en in ANCHORS:
            text(d, x, cy + 2, k, F["id"], C["gold"])
            text(d, x + 90, cy + 1, en, F["small"], C["dim"])
            text(d, x + w, cy, ar, F["lbl_ar"], C["text"], "r")
            cy += 34
        cy += 18
        text(d, x + w, cy, "لوحة الألوان", F["h_ar"], C["text"], "r")
        text(d, x, cy + 8, "PALETTE", F["h_en"], C["cyan"])
        cy += 52
        sw = 26
        colw = w // 2
        for i, (name, ramp) in enumerate(SWATCHES):
            ix = x + (i % 2) * colw
            iy = cy + (i // 2) * 36
            text(d, ix, iy + 4, name, F["small"], C["dim"])
            for j, c in enumerate(ramp):
                sx = ix + 120 + j * (sw + 3)
                d.rectangle((sx, iy, sx + sw, iy + sw), fill=c, outline=(0, 0, 0))
    h = 50 + 3 * 36 + 22 + 50 + 4 * 34 + 18 + 52 + 7 * 36
    return Panel("Legend", "دليل الاستخدام", "", body, h)


# --------------------------------------------------------------------------
def header(sheet, n_modules):
    d = ImageDraw.Draw(sheet)
    w = SHEET_W
    for i in range(200):
        t = i / 200
        d.line((0, i, w, i), fill=tuple(int(a + (b - a) * t) for a, b in zip((16, 30, 74), C["bg"])))
    text(d, w - M, 34, "الغرفة الأولى – المدخل العميق", F["title_ar"], C["text"], "r")
    text(d, w - M, 122, "استكشاف • قتال أرضي • تحدٍّ جوي", F["sub"], C["gold"], "r")
    text(d, M, 40, "2D MODULAR ENVIRONMENT ASSET SHEET", F["title_en"], C["cyan"])
    text(d, M, 84, "Room 01 — The Deep Entrance", F["sub"], C["text"])
    chips = ["32 px grid", f"{n_modules} modules", f"preview ×{S}", f"room {room.W}×{room.H}"]
    x = M
    for c in chips:
        tw, th = tsize(d, c, F["chip"])
        d.rounded_rectangle((x, 128, x + tw + 28, 128 + th + 18), 16, fill=(20, 34, 80), outline=(48, 72, 150))
        text(d, x + 14, 137, c, F["chip"], C["text"])
        x += tw + 44
    return 200


def build_sheet(assets, room_img):
    inner = SHEET_W - 2 * M
    secs = {s[0]: s for s in catalog.SECTIONS}

    def pw(frac, n):
        return int((inner - GAP * (n - 1)) * frac)

    rows = [
        [(terrain_panel(assets, inner), 1.0)],
        [(items_panel(secs["islands"], assets, pw(0.4, 2)), 0.4),
         (items_panel(secs["hazards"], assets, pw(0.6, 2)), 0.6)],
        [(items_panel(secs["crumble"], assets, pw(0.58, 2)), 0.58),
         (items_panel(secs["background"], assets, pw(0.42, 2)), 0.42)],
        [(items_panel(secs["wood"], assets, inner), 1.0)],
        [(items_panel(secs["lights"], assets, inner), 1.0)],
        [(items_panel(secs["interact"], assets, inner), 1.0)],
    ]
    room_w = room_img.width + 44
    rows.append([(room_panel(room_img), room_w / inner),
                 (legend_panel(inner - room_w - GAP), (inner - room_w - GAP) / inner)])

    heights = [max(p.body_h for p, _ in r) + 58 + 20 + 26 for r in rows]
    n_modules = sum(len(s[3]) for s in catalog.SECTIONS)
    total_h = 200 + 20 + sum(heights) + GAP * len(rows) + 70
    sheet = Image.new("RGBA", (SHEET_W, total_h), C["bg"] + (255,))
    y = header(sheet, n_modules) + 20
    for r, h in zip(rows, heights):
        x = M
        for i, (p, frac) in enumerate(r):
            w = inner - (x - M) if i == len(r) - 1 else int((inner - GAP * (len(r) - 1)) * frac)
            p.draw(sheet, x, y, w, h)
            x += w + GAP
        y += h + GAP
    d = ImageDraw.Draw(sheet)
    text(d, M, y + 8, "Generated by tools/room01_assets/build.py · every module tiles on a 32 px grid",
         F["small"], C["dim"])
    text(d, SHEET_W - M, y + 6, "كل القطع مولّدة برمجياً وقابلة للتعديل", F["lbl_ar"], C["dim"], "r")
    return sheet
