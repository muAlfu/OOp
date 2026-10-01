#!/usr/bin/env python3
"""Turn a short character clip on a plain light background into a game sprite sheet.

Every frame of the video is kept. All frames are cut with the same rectangle
(by default the union of the character's extent over the whole clip plus a
margin), so no frame is clipped and the character never jitters between cells.
Pass --rect to cut several clips of one character with the same rectangle, so
their animations line up with the same pivot. The background is keyed out into
real alpha: flood fill from the border, enclosed gaps (e.g. between a claw and
the face), and closed-form matting on the edge band so outlines and motion blur
keep soft, halo-free edges. Where the clip itself runs out of the video frame
(e.g. a dust effect), those pixels do not exist; the part near that video edge
is faded out instead of ending in a straight cut.

Requires: pip install av pillow numpy scipy pymatting

How assets/sprites was made (all clips share one 1080x756 canvas):
    python3 tools/video_to_spritesheet.py Triple_claw_combo.MOV assets/sprites/triple_claw_combo \
        --name triple_claw_combo --rect 0 135 1080 891 --half --preview
    python3 tools/video_to_spritesheet.py Havvy-claw-attak.MOV assets/sprites/heavy_claw_attack \
        --name heavy_claw_attack --rect 0 135 1080 891 --half --preview
    python3 tools/video_to_spritesheet.py Final_Heavy_Claw_Attack_.MOV assets/sprites/final_heavy_claw_attack \
        --name final_heavy_claw_attack --rect 0 135 1080 891 --columns 10 --edge-fade 8 --half --no-full --preview
    # the jump rises above y 135, so its canvas is taller; the bottom edge (891) and x range stay the same,
    # so with a Bottom pivot it still lines up with the others
    python3 tools/video_to_spritesheet.py Jump_hallow_.MOV assets/sprites/jump_hallow \
        --name jump_hallow --rect 0 39 1080 891 --columns 10 --half --no-full --preview
    # a different character, so its own canvas; one small pocket by the foot needs a manual cut
    python3 tools/video_to_spritesheet.py Rat_Under_Magic_Idle.MOV assets/sprites/rat_under_magic_idle \
        --name rat_under_magic_idle --rect 142 70 854 886 --columns 16 --cut-pocket 611 814 --half --no-full --preview
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
GAP_MATCH = 4          # enclosed pockets must be this close to the background colour (median) to be cut out ...
GAP_LOOSE_MATCH = 12   # ... or, for pockets the video's colour compression tints from the cloth around them,
GAP_LOOSE = ((100, 0.55), (50, 0.75))  # this looser match when (area px, dark share of the ring) reach a pair
EDGE_BAND = 3          # px around the keyed background that are re-solved by matting
TRAIL_LIGHTNESS = 48   # pale pixels touching the background (dust, motion blur) are also re-solved ...
TRAIL_REACH = 48       # ... up to this many px from the background
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


def key_channel(bg):
    """The dominant channel of a green or blue screen, or None for a neutral (e.g. white) background."""
    order = np.argsort(bg)
    return int(order[-1]) if bg[order[-1]] - bg[order[-2]] > 60 else None


def colour_distance(rgb, bg):
    return np.abs(rgb.astype(np.int16) - bg.astype(np.int16)).max(axis=2)


def touching_border(labels):
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return np.isin(labels, np.unique(edge[edge > 0]))


def enclosed_gaps(near_bg, outer_bg, dist, rgb, min_area=20):
    """Background pockets the border flood fill cannot reach.

    A pocket is cut out only if it is ringed mostly by dark outline/cloth pixels and
    matches the background colour: almost exactly, or more loosely (compression bleeds
    the colour of saturated cloth into them) when the pocket is big enough and its ring
    dark enough. Pale highlights on horns and claws are slightly off-white
    and half ringed by the light bone around them, and eye shines and glows are ringed
    by light colours, so they are left alone.
    """
    labels, count = ndi.label(near_bg & ~outer_bg, structure=EIGHT)
    luma = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    gaps = np.zeros_like(near_bg)
    for index, region in enumerate(ndi.find_objects(labels), start=1):
        y, x = region
        y = slice(max(y.start - 4, 0), y.stop + 4)
        x = slice(max(x.start - 4, 0), x.stop + 4)
        blob = labels[y, x] == index
        area = blob.sum()
        if area < min_area:
            continue
        ring = ndi.binary_dilation(blob, EIGHT, iterations=3) & ~ndi.binary_dilation(blob, EIGHT)
        ring &= ~near_bg[y, x]
        if not ring.any():
            continue
        match = np.median(dist[y, x][blob])
        dark = (luma[y, x][ring] < 110).mean()
        loose = match <= GAP_LOOSE_MATCH and any(area >= a and dark >= d for a, d in GAP_LOOSE)
        if (match <= GAP_MATCH and dark > 0.5) or loose:
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


def despill(foreground, key):
    """Remove green/blue screen light from the character's colours.

    Pixels where the key channel clearly leads the other two are pulled down to the
    average of those two (olive turns back to brown, pale green claws to bone); pixels
    where it does not lead, such as yellows, oranges and greys, are left alone. The
    blend between the two is smooth so gradients do not band.
    """
    a, b = [c for c in range(3) if c != key]
    high = np.maximum(foreground[..., a], foreground[..., b])
    mean = (foreground[..., a] + foreground[..., b]) / 2
    lead = foreground[..., key] - high
    weight = np.clip(lead / (20 / 255) + 0.5, 0, 1)
    foreground[..., key] = np.minimum(foreground[..., key], high - weight * (high - mean))
    return foreground


def key_frame(rgb, cut_points=()):
    """Return an RGBA frame with the background removed.

    cut_points are (x, y) spots, in this frame's coordinates, where any enclosed
    background pocket is cut out even if the automatic gap test kept it.
    """
    bg = background_colour(rgb)
    dist = colour_distance(rgb, bg)

    near_bg = dist <= BG_TOLERANCE
    labels, _ = ndi.label(near_bg, structure=EIGHT)
    outer_bg = touching_border(labels)
    known_bg = outer_bg | enclosed_gaps(near_bg, outer_bg, dist, rgb)
    if cut_points:
        labels, _ = ndi.label(near_bg & ~known_bg, structure=EIGHT)
        for x, y in cut_points:
            spot = labels[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4]
            known_bg |= np.isin(labels, np.unique(spot[spot > 0]))

    from_bg = ndi.distance_transform_edt(~known_bg)
    band = ~known_bg & (from_bg <= EDGE_BAND)
    light = ~known_bg & (dist < TRAIL_LIGHTNESS) & (from_bg <= TRAIL_REACH)
    labels, _ = ndi.label(light | band, structure=EIGHT)
    reached = np.unique(labels[band])
    pale = light & np.isin(labels, reached[reached > 0])
    unknown = band | pale

    trimap = np.where(known_bg, 0.0, np.where(unknown, 0.5, 1.0))
    image = rgb.astype(np.float64) / 255.0
    alpha = np.clip(estimate_alpha_cf(image, trimap), 0.0, 1.0)
    alpha[known_bg] = 0.0
    alpha[trimap == 1.0] = 1.0
    # Pale areas that reach the background without crossing an outline (dust, motion
    # blur) are see-through in the clip: cap their opacity by their contrast with the
    # background so they do not turn into solid white patches on a dark backdrop.
    alpha[pale] = np.minimum(alpha[pale], dist[pale] / TRAIL_LIGHTNESS)
    # Those trails also carry the video's 8x8 compression blocks; soften them so the
    # edge does not stair-step. Crisp outlines (the thin edge band) are untouched.
    trail = pale & (from_bg > EDGE_BAND)
    if trail.any():
        zone = ndi.binary_dilation(trail, EIGHT, iterations=4)
        alpha[zone] = ndi.gaussian_filter(alpha, TRAIL_SOFTEN)[zone]
    alpha = drop_specks(alpha)
    foreground = estimate_foreground_ml(image, alpha)
    key = key_channel(bg)
    if key is not None:
        foreground = despill(foreground, key)

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


def cell_rect(box, margin):
    """Centre an even-sized cell on the union box; it may reach past the video (padded)."""
    x0, y0, x1, y1 = box
    w = (x1 - x0 + 2 * margin + 1) // 2 * 2
    h = (y1 - y0 + 2 * margin + 1) // 2 * 2
    left = (x0 + x1) // 2 - w // 2
    top = (y0 + y1) // 2 - h // 2
    return left, top, left + w, top + h


def crop(rgb, rect):
    """Cut rect out of the frame, filling any part outside the video with its background colour."""
    left, top, right, bottom = rect
    height, width = rgb.shape[:2]
    out = np.empty((bottom - top, right - left, 3), np.uint8)
    out[:] = np.rint(background_colour(rgb)).astype(np.uint8)
    x0, y0, x1, y1 = max(left, 0), max(top, 0), min(right, width), min(bottom, height)
    if x0 < x1 and y0 < y1:
        out[y0 - top:y1 - top, x0 - left:x1 - left] = rgb[y0:y1, x0:x1]
    return out


def border_contact(frames):
    """Which video edges the clip's content touches, and in which frames."""
    sides = {}
    for i, rgb in enumerate(frames):
        solid = colour_distance(rgb, background_colour(rgb)) > BG_TOLERANCE
        for side, strip in (("left", solid[:, 0]), ("right", solid[:, -1]), ("top", solid[0]), ("bottom", solid[-1])):
            if strip.any():
                sides.setdefault(side, []).append(i)
    return sides


def fade_edges(cell, rect, width, height, sides, fade):
    """Ramp alpha to zero at the video edges the content runs into, so it trails off instead of ending in a cut."""
    left, top, right, bottom = rect
    xs = np.arange(left, right, dtype=np.float32)
    ys = np.arange(top, bottom, dtype=np.float32)
    ramp = np.ones((bottom - top, right - left), np.float32)
    if "left" in sides:
        ramp *= np.clip(xs / fade, 0, 1)[None, :]
    if "right" in sides:
        ramp *= np.clip((width - 1 - xs) / fade, 0, 1)[None, :]
    if "top" in sides:
        ramp *= np.clip(ys / fade, 0, 1)[:, None]
    if "bottom" in sides:
        ramp *= np.clip((height - 1 - ys) / fade, 0, 1)[:, None]
    cell[..., 3] = np.rint(cell[..., 3] * ramp).astype(np.uint8)
    cell[cell[..., 3] == 0, :3] = 0
    return cell


def halve(cell):
    """50% copy of a cell. Resampling can spread a faint trace of content that sits at the
    cell edge onto the 1 px border; clear it so it cannot bleed into the neighbouring cell."""
    h, w = cell.shape[:2]
    small = np.array(Image.fromarray(cell, "RGBA").resize((w // 2, h // 2), Image.LANCZOS))
    small[[0, -1]] = 0
    small[:, [0, -1]] = 0
    return small


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
    parser.add_argument("--rect", type=int, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                        help="cut every frame with this rectangle (video px) instead of fitting one; "
                             "use the same rect for all clips of a character")
    parser.add_argument("--edge-fade", type=int, default=96,
                        help="px over which content running out of the video is faded out, in the frames where "
                             "it does (0 = keep the hard cut)")
    parser.add_argument("--cut-pocket", type=int, nargs=2, action="append", default=[], metavar=("X", "Y"),
                        help="video px where an enclosed background pocket must always be cut out (repeatable)")
    parser.add_argument("--half", action="store_true", help="also write a 50%% sheet")
    parser.add_argument("--no-full", action="store_true",
                        help="skip the full-resolution sheet (for long clips whose full sheet is too big for a texture)")
    parser.add_argument("--frames", action="store_true", help="also write every frame as its own PNG")
    parser.add_argument("--preview", action="store_true", help="also write an animated GIF preview")
    args = parser.parse_args()

    frames, fps = read_frames(args.video)
    height, width = frames[0].shape[:2]
    box = union_box(frames)
    rect = tuple(args.rect) if args.rect else cell_rect(box, args.margin)
    left, top, right, bottom = rect
    w, h = right - left, bottom - top
    print(f"{len(frames)} frames @ {fps:g} fps, {width}x{height}; character box {box}; cell {w}x{h} at ({left},{top})")
    if box[0] < left or box[1] < top or box[2] > right or box[3] > bottom:
        raise SystemExit(f"the clip reaches {box}, outside the cell {rect} - frames would be cut; widen --rect")
    contact = border_contact(frames) if args.edge_fade > 0 else {}
    key = key_channel(background_colour(frames[0]))
    if key is not None:
        print(f"  {'RGB'[key]} screen background: removing its colour spill from the character")
    for side, hits in contact.items():
        print(f"  content runs out of the video on the {side} in frames {hits}; fading the last {args.edge_fade} px")

    os.makedirs(args.out_dir, exist_ok=True)
    cells = []
    for i, rgb in enumerate(frames):
        cell = key_frame(crop(rgb, rect), [(x - left, y - top) for x, y in args.cut_pocket])
        sides = {side for side, hits in contact.items() if i in hits}
        if sides:
            cell = fade_edges(cell, rect, width, height, sides, args.edge_fade)
        edge = np.concatenate([cell[0, :, 3], cell[-1, :, 3], cell[:, 0, 3], cell[:, -1, 3]])
        if edge.any():
            raise SystemExit(f"frame {i} touches the cell edge - increase --margin or widen --rect")
        cells.append(cell)
        if args.frames:
            frame_dir = os.path.join(args.out_dir, "frames")
            os.makedirs(frame_dir, exist_ok=True)
            Image.fromarray(cell, "RGBA").save(os.path.join(frame_dir, f"{args.name}_{i:02d}.png"), optimize=True)

    outputs = [] if args.no_full else [("", cells, w, h)]
    if args.half or args.preview:
        half = [halve(c) for c in cells]
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
