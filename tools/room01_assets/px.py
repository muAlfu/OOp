"""Small pixel-art toolkit on top of numpy + Pillow.

Every sprite is an RGBA numpy array. Shapes are boolean masks, and shading
helpers turn a mask plus a colour ramp into hand-pixelled looking art
(rim light from the top-left, shadow on the bottom-right, 1px dark outline).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

OUTLINE = (6, 8, 22)


# --------------------------------------------------------------------------
# deterministic noise
# --------------------------------------------------------------------------
def hash2(x, y, seed=0):
    """Stable pseudo-random value in [0, 1) for integer coordinates."""
    x = np.asarray(x, np.int64)
    y = np.asarray(y, np.int64)
    h = (x * 374761393 + y * 668265263 + (seed + 1) * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


def rnd(seed, *keys):
    """Scalar pseudo-random value in [0, 1) for a seed and integer keys."""
    v = seed
    for k in keys:
        v = int(hash2(v, k, 7) * 1_000_000)
    return float(hash2(v, len(keys), 11))


# --------------------------------------------------------------------------
# masks
# --------------------------------------------------------------------------
def grid(w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    return xx, yy


def shift(m, dx, dy, fill=False):
    """out[y, x] = m[y - dy, x - dx]; pixels shifted in from outside = fill."""
    h, w = m.shape
    out = np.full_like(m, fill)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs0 < xs1 and ys0 < ys1:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return out


def outline_of(m, diagonal=False):
    """Pixels outside the mask that touch it."""
    n = shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)
    if diagonal:
        n |= shift(m, 1, 1) | shift(m, -1, -1) | shift(m, 1, -1) | shift(m, -1, 1)
    return n & ~m


def inner_edge(m):
    """Pixels inside the mask that touch the outside (4-neighbourhood)."""
    e = ~shift(m, 1, 0, True) | ~shift(m, -1, 0, True)
    e |= ~shift(m, 0, 1, True) | ~shift(m, 0, -1, True)
    return m & e


def erode(m, fill=True):
    return (m & shift(m, 1, 0, fill) & shift(m, -1, 0, fill)
            & shift(m, 0, 1, fill) & shift(m, 0, -1, fill))


def depth_map(m, limit=12, fill=True):
    """Chessboard-ish distance (in px) from each mask pixel to the outside."""
    d = np.zeros(m.shape, np.int32)
    cur = m.copy()
    for i in range(limit):
        d[cur] += 1
        cur = erode(cur, fill)
        if not cur.any():
            break
    return d


def poly(w, h, pts):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
    return np.array(im) > 0


def ellipse(w, h, cx, cy, rx, ry):
    xx, yy = grid(w, h)
    return ((xx + 0.5 - cx) / max(rx, 0.01)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.01)) ** 2 <= 1.0


def rect(w, h, x0, y0, x1, y1):
    """Inclusive rectangle mask."""
    m = np.zeros((h, w), bool)
    m[max(0, y0):max(0, y1 + 1), max(0, x0):max(0, x1 + 1)] = True
    return m


def line_mask(w, h, x0, y0, x1, y1, width=1):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).line([(x0, y0), (x1, y1)], fill=255, width=width)
    return np.array(im) > 0


# --------------------------------------------------------------------------
# sprite
# --------------------------------------------------------------------------
class Sprite:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)

    @property
    def opaque(self):
        """Solid pixels (translucent glow/halo pixels don't count)."""
        return self.a[:, :, 3] > 200

    def put(self, mask, color, alpha=255):
        mask = mask.astype(bool)
        self.a[mask, 0] = color[0]
        self.a[mask, 1] = color[1]
        self.a[mask, 2] = color[2]
        self.a[mask, 3] = alpha

    def px(self, x, y, color, alpha=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x, :3] = color
            self.a[y, x, 3] = alpha

    def glow(self, mask, color, alpha):
        """Composite a translucent colour over existing pixels."""
        mask = mask.astype(bool)
        src_a = alpha / 255.0
        dst = self.a[mask].astype(np.float32)
        dst_a = dst[:, 3:4] / 255.0
        out_a = src_a + dst_a * (1 - src_a)
        col = np.array(color, np.float32)
        rgb = (col * src_a + dst[:, :3] * dst_a * (1 - src_a)) / np.maximum(out_a, 1e-6)
        self.a[mask, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        self.a[mask, 3] = np.clip(out_a[:, 0] * 255, 0, 255).astype(np.uint8)

    def paste(self, other, ox, oy):
        """Alpha-composite another sprite (or RGBA array) at (ox, oy)."""
        src = other.a if isinstance(other, Sprite) else other
        sh, sw = src.shape[:2]
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(self.w, ox + sw), min(self.h, oy + sh)
        if x0 >= x1 or y0 >= y1:
            return
        s = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox].astype(np.float32)
        d = self.a[y0:y1, x0:x1].astype(np.float32)
        sa = s[:, :, 3:4] / 255.0
        da = d[:, :, 3:4] / 255.0
        oa = sa + da * (1 - sa)
        rgb = (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
        self.a[y0:y1, x0:x1, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        self.a[y0:y1, x0:x1, 3] = np.clip(oa[:, :, 0] * 255, 0, 255).astype(np.uint8)

    def outline(self, color=OUTLINE, diagonal=False, mask=None):
        m = self.opaque if mask is None else mask
        self.put(outline_of(m, diagonal), color)

    def flip_x(self):
        s = Sprite(self.w, self.h)
        s.a = self.a[:, ::-1].copy()
        return s

    def image(self):
        return Image.fromarray(self.a, "RGBA")


# --------------------------------------------------------------------------
# shading
# --------------------------------------------------------------------------
def shade(spr, mask, ramp, base=2, outline=True, rim=True, noise=0.12, seed=0,
          spec=True, grad=0.0, outline_color=OUTLINE, inside=None):
    """Fill a mask with a ramp-based, top-left lit pixel-art shading.

    ramp: list of colours from darkest to lightest.
    base: ramp index of the body colour.
    grad: >0 makes the top part lighter and the bottom darker.
    inside: optional mask that counts as "solid" when testing neighbours
            (lets touching shapes share a seamless edge).
    """
    mask = mask.astype(bool)
    if not mask.any():
        return
    solid = mask if inside is None else (mask | inside)
    h, w = mask.shape
    xx, yy = grid(w, h)
    idx = np.full(mask.shape, float(base))
    if grad:
        ys = np.where(mask.any(axis=1))[0]
        t = (yy - ys.min()) / max(1, ys.max() - ys.min())
        idx += grad * (0.5 - t) * 2
    n = hash2(xx, yy, seed)
    idx += np.where(n < noise / 2, -1, 0) + np.where(n > 1 - noise / 2, 1, 0)
    if rim:
        up = ~shift(solid, 0, 1)
        left = ~shift(solid, 1, 0)
        down = ~shift(solid, 0, -1)
        right = ~shift(solid, -1, 0)
        idx = np.where(mask & (up | left), np.maximum(idx, base + 1), idx)
        idx = np.where(mask & (down | right) & ~(up | left), np.minimum(idx, base - 1), idx)
        if spec:
            idx = np.where(mask & up & left, base + 2, idx)
    idx = np.clip(np.round(idx), 0, len(ramp) - 1).astype(int)
    pal = np.array(ramp, np.uint8)
    spr.a[mask, :3] = pal[idx[mask]]
    spr.a[mask, 3] = 255
    if outline:
        o = outline_of(solid) & ~spr.opaque
        spr.put(o, outline_color)


def facet(spr, pts, ramp, seed=0, outline=True, split=None):
    """Crystal shard: polygon split along its axis into lit and dark faces."""
    w, h = spr.w, spr.h
    m = poly(w, h, pts)
    if not m.any():
        return m
    xs = [p[0] for p in pts]
    cx = sum(xs) / len(xs) if split is None else split
    xx, yy = grid(w, h)
    lit = m & (xx + 0.5 < cx)
    dark = m & ~lit
    n = len(ramp)
    spr.put(dark, ramp[max(0, n - 4)])
    spr.put(lit, ramp[n - 2])
    spr.put(inner_edge(m) & lit & ~shift(m, 0, 1), ramp[n - 1])
    spr.put(inner_edge(m) & dark & ~shift(m, -1, 0), ramp[max(0, n - 5)])
    # bright core line
    tip = min(pts, key=lambda p: p[1])
    core = line_mask(w, h, int(cx) - 1, int(tip[1]) + 2, int(cx) - 1, int(max(p[1] for p in pts)) - 2) & m
    spr.put(core, ramp[n - 1])
    if outline:
        spr.put(outline_of(m) & ~spr.opaque, OUTLINE)
    return m


def halo(spr, cx, cy, radius, color, max_alpha=110, steps=4, under=True):
    """Stepped (pixel-art) radial glow; drawn only on transparent pixels by default."""
    xx, yy = grid(spr.w, spr.h)
    d = np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) / radius
    empty = ~spr.opaque if under else np.ones(d.shape, bool)
    for i in range(steps):
        lo = i / steps
        ring = (d < 1 - lo) & empty
        if i == 0:
            spr.glow(ring, color, int(max_alpha * 0.35))
        else:
            spr.glow(ring, color, int(max_alpha * 0.22))


def upscale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def lerp(c0, c1, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c0, c1))


def wave(x, period, terms):
    """Periodic integer-friendly profile: sum of a*sin(2*pi*k*x/period + ph)."""
    return sum(a * np.sin(2 * math.pi * k * np.asarray(x, float) / period + ph) for a, k, ph in terms)
