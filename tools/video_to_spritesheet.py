#!/usr/bin/env python3
"""Turn a short character clip on a plain light background into a game sprite sheet.

Every frame of the video is kept. All frames are cut with the same rectangle
(the union of the character's extent over the whole clip plus a margin), so no
frame is clipped and the character never jitters between cells. The background
is keyed out into real alpha: flood fill from the border, enclosed gaps
(e.g. between a claw and the face), and closed-form matting on the edge band so
outlines and motion blur keep soft, halo-free edges.

Requires: pip install av pillow numpy scipy pymatting

Example (how assets/sprites/triple_claw_combo was made):
    python3 tools/video_to_spritesheet.py Triple_claw_combo.MOV \
        assets/sprites/triple_claw_combo --name triple_claw_combo --columns 7 --half --preview
"""
import argparse
import json
import os

import av
import numpy as np
from PIL import Image
from pymatting import estimate_alpha_cf, estimate_foreground_ml
from scipy import ndimage as ndi

BG_TOLERANCE = 10      # max channel distance from the background colour that still counts as background
GAP_MATCH = 4          # enclosed pockets must be this close to the background colour (median) to be cut out
EDGE_BAND = 3          # px around the keyed background that are re-solved by matting
TRAIL_LIGHTNESS = 48   # light pixels touching the background (motion blur) are also re-solved ...
TRAIL_REACH = 24       # ... up to this many px from the background
TRAIL_SOFTEN = 1.5     # gaussian sigma (px) applied to the alpha of those trails
EIGHT = np.ones((3, 3), bool)


def read_frames(path):
    with av.open(path) as container:
        stream = container.streams.video[0]
        fps = float(stream.average_rate or stream.guessed_rate)
        frames = [f.to_ndarray(format="rgb24") for f in container.decode(stream)]
    return frames, fps


def background_colour(rgb):
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    return np.median(border, axis=0)


def colour_distance(rgb, bg):
    return np.abs(rgb.astype(np.int16) - bg.astype(np.int16)).max(axis=2)


def touching_border(labels):
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return np.isin(labels, np.unique(edge[edge > 0]))


def enclosed_gaps(near_bg, outer_bg, dist, rgb, min_area=20):
    """Background pockets the border flood fill cannot reach.

    A pocket is kept only if it matches the background colour almost exactly and
    is ringed mostly by dark outline pixels; pale highlights on horns and claws
    are slightly off-white and are left alone.
    """
    labels, count = ndi.label(near_bg & ~outer_bg, structure=EIGHT)
    luma = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    gaps = np.zeros_like(near_bg)
    for index, region in enumerate(ndi.find_objects(labels), start=1):
        y, x = region
        y = slice(max(y.start - 4, 0), y.stop + 4)
        x = slice(max(x.start - 4, 0), x.stop + 4)
        blob = labels[y, x] == index
        if blob.sum() < min_area or np.median(dist[y, x][blob]) > GAP_MATCH:
            continue
        ring = ndi.binary_dilation(blob, EIGHT, iterations=3) & ~ndi.binary_dilation(blob, EIGHT)
        ring &= ~near_bg[y, x]
        if ring.any() and (luma[y, x][ring] < 110).mean() > 0.5:
            gaps[y, x] |= blob
    return gaps


def drop_specks(alpha, faint=6 / 255, max_area=16, max_peak=0.15):
    """Clear invisible matting noise: near-zero alpha and tiny faint islands off the body."""
    alpha[alpha < faint] = 0.0
    labels, count = ndi.label(alpha > 0, structure=EIGHT)
    if count > 1:
        index = np.arange(1, count + 1)
        area = ndi.sum(np.ones_like(alpha), labels, index)
        peak = ndi.maximum(alpha, labels, index)
        specks = index[(area < max_area) & (peak < max_peak)]
        alpha[np.isin(labels, specks)] = 0.0
    return alpha


def key_frame(rgb):
    """Return an RGBA frame with the background removed."""
    bg = background_colour(rgb)
    dist = colour_distance(rgb, bg)

    near_bg = dist <= BG_TOLERANCE
    labels, _ = ndi.label(near_bg, structure=EIGHT)
    outer_bg = touching_border(labels)
    known_bg = outer_bg | enclosed_gaps(near_bg, outer_bg, dist, rgb)

    from_bg = ndi.distance_transform_edt(~known_bg)
    unknown = ~known_bg & (from_bg <= EDGE_BAND)
    light = ~known_bg & (dist < TRAIL_LIGHTNESS) & (from_bg <= TRAIL_REACH)
    labels, _ = ndi.label(light | unknown, structure=EIGHT)
    reached = np.unique(labels[unknown])
    unknown |= light & np.isin(labels, reached[reached > 0])

    trimap = np.where(known_bg, 0.0, np.where(unknown, 0.5, 1.0))
    image = rgb.astype(np.float64) / 255.0
    alpha = np.clip(estimate_alpha_cf(image, trimap), 0.0, 1.0)
    alpha[known_bg] = 0.0
    alpha[trimap == 1.0] = 1.0
    # Motion-blur trails carry the video's 8x8 compression blocks; soften them so
    # the edge does not stair-step. Crisp outlines (the thin edge band) are untouched.
    trail = unknown & (from_bg > EDGE_BAND)
    if trail.any():
        zone = ndi.binary_dilation(trail, EIGHT, iterations=4)
        alpha[zone] = ndi.gaussian_filter(alpha, TRAIL_SOFTEN)[zone]
    alpha = drop_specks(alpha)
    foreground = estimate_foreground_ml(image, alpha)

    out = np.dstack([np.clip(foreground, 0, 1) * 255, alpha * 255])
    out = np.rint(out).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out


def union_box(frames):
    x0 = y0 = 10**9
    x1 = y1 = -1
    for rgb in frames:
        dist = colour_distance(rgb, background_colour(rgb))
        ys, xs = np.nonzero(dist > BG_TOLERANCE)
        x0, x1 = min(x0, int(xs.min())), max(x1, int(xs.max()))
        y0, y1 = min(y0, int(ys.min())), max(y1, int(ys.max()))
    return x0, y0, x1 + 1, y1 + 1


def cell_rect(box, margin, width, height):
    """Centre an even-sized cell on the union box, clamped to the video."""
    x0, y0, x1, y1 = box
    w = (x1 - x0 + 2 * margin + 1) // 2 * 2
    h = (y1 - y0 + 2 * margin + 1) // 2 * 2
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    left = min(max(cx - w // 2, 0), width - w)
    top = min(max(cy - h // 2, 0), height - h)
    return left, top, left + w, top + h


def build_sheet(cells, columns):
    h, w = cells[0].shape[:2]
    rows = -(-len(cells) // columns)
    sheet = np.zeros((rows * h, columns * w, 4), np.uint8)
    for i, cell in enumerate(cells):
        r, c = divmod(i, columns)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = cell
    return sheet, rows


def sheet_json(name, image_file, count, columns, w, h, fps, sheet_size):
    duration = round(1000 / fps)
    frames = []
    for i in range(count):
        r, c = divmod(i, columns)
        frames.append({
            "filename": f"{name}_{i:02d}",
            "frame": {"x": c * w, "y": r * h, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h},
            "duration": duration,
        })
    return {
        "frames": frames,
        "meta": {
            "app": "tools/video_to_spritesheet.py",
            "version": "1.0",
            "image": image_file,
            "format": "RGBA8888",
            "size": {"w": sheet_size[0], "h": sheet_size[1]},
            "scale": "1",
            "frameTags": [{"name": name, "from": 0, "to": count - 1, "direction": "forward"}],
            "frameWidth": w,
            "frameHeight": h,
            "columns": columns,
            "rows": -(-count // columns),
            "frameCount": count,
            "fps": fps,
        },
    }


def save_preview(path, cells, fps, backdrop=(46, 52, 64)):
    """Animated GIF of the cells over a solid backdrop, for a quick look at the motion."""
    shown = []
    for cell in cells:
        alpha = cell[..., 3:4].astype(np.float32) / 255
        rgb = cell[..., :3] * alpha + np.array(backdrop, np.float32) * (1 - alpha)
        shown.append(Image.fromarray(np.rint(rgb).astype(np.uint8)))
    # GIF delays are whole centiseconds; spread the rounding so the average matches the clip.
    ticks = np.diff(np.rint(np.arange(len(cells) + 1) * 100 / fps)).astype(int) * 10
    shown[0].save(path, save_all=True, append_images=shown[1:], duration=ticks.tolist(), loop=0, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video")
    parser.add_argument("out_dir")
    parser.add_argument("--name", default="sprite")
    parser.add_argument("--columns", type=int, default=7)
    parser.add_argument("--margin", type=int, default=16, help="empty px kept around the union of all poses")
    parser.add_argument("--half", action="store_true", help="also write a 50%% sheet")
    parser.add_argument("--frames", action="store_true", help="also write every frame as its own PNG")
    parser.add_argument("--preview", action="store_true", help="also write an animated GIF preview")
    args = parser.parse_args()

    frames, fps = read_frames(args.video)
    height, width = frames[0].shape[:2]
    box = union_box(frames)
    left, top, right, bottom = cell_rect(box, args.margin, width, height)
    w, h = right - left, bottom - top
    print(f"{len(frames)} frames @ {fps:g} fps, {width}x{height}; character box {box}; cell {w}x{h} at ({left},{top})")

    os.makedirs(args.out_dir, exist_ok=True)
    cells = []
    for i, rgb in enumerate(frames):
        cell = key_frame(rgb[top:bottom, left:right])
        edge = np.concatenate([cell[0, :, 3], cell[-1, :, 3], cell[:, 0, 3], cell[:, -1, 3]])
        if edge.any():
            raise SystemExit(f"frame {i} touches the cell edge - increase --margin")
        cells.append(cell)
        if args.frames:
            frame_dir = os.path.join(args.out_dir, "frames")
            os.makedirs(frame_dir, exist_ok=True)
            Image.fromarray(cell, "RGBA").save(os.path.join(frame_dir, f"{args.name}_{i:02d}.png"), optimize=True)

    outputs = [("", cells, w, h)]
    if args.half or args.preview:
        half = [np.asarray(Image.fromarray(c, "RGBA").resize((w // 2, h // 2), Image.LANCZOS)) for c in cells]
    if args.half:
        outputs.append(("_half", half, w // 2, h // 2))
    for suffix, sheet_cells, cw, ch in outputs:
        sheet, rows = build_sheet(sheet_cells, args.columns)
        image_file = f"{args.name}_spritesheet{suffix}.png"
        Image.fromarray(sheet, "RGBA").save(os.path.join(args.out_dir, image_file), optimize=True)
        meta = sheet_json(args.name, image_file, len(cells), args.columns, cw, ch, fps, (sheet.shape[1], sheet.shape[0]))
        with open(os.path.join(args.out_dir, f"{args.name}_spritesheet{suffix}.json"), "w") as fh:
            json.dump(meta, fh, indent=2)
        print(f"{image_file}: {sheet.shape[1]}x{sheet.shape[0]}, {args.columns}x{rows} grid of {cw}x{ch}")
    if args.preview:
        save_preview(os.path.join(args.out_dir, f"{args.name}_preview.gif"), half, fps)
        print(f"{args.name}_preview.gif written")


if __name__ == "__main__":
    main()
