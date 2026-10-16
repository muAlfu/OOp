"""Build every output for Room 01 – The Deep Entrance.

    python3 tools/room01_assets/build.py [output_dir]

Writes (default: assets/room01_deep_entrance/):
    asset_sheet.png          presentation sheet (x3, bilingual labels)
    tileset.png / .json      packed 32px atlas + metadata for engines
    modules/<id>.png         every module as its own 1x PNG
    room01_preview.png       room rebuilt from the modules (x2)
    room01_annotated.png     same, with the route callouts (x2)
    room01_map.json          tile grid + placements to rebuild it in-engine
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import catalog  # noqa: E402
import room  # noqa: E402
import sheet  # noqa: E402
import terrain  # noqa: E402
from px import upscale  # noqa: E402

T = 32
ATLAS_W = 16 * T


def pack(assets):
    """Shelf-pack every sprite on the 32px grid, one section per shelf run."""
    frames, x, y, shelf_h = {}, 0, 0, 0
    for sec_id, _, _, items in catalog.SECTIONS:
        if x:
            x, y, shelf_h = 0, y + shelf_h, 0
        for item in items:
            spr, meta = assets[item[0]]
            if x + spr.w > ATLAS_W:
                x, y, shelf_h = 0, y + shelf_h, 0
            frames[item[0]] = (x, y)
            x += spr.w
            shelf_h = max(shelf_h, spr.h)
    height = y + shelf_h
    atlas = Image.new("RGBA", (ATLAS_W, height), (0, 0, 0, 0))
    for aid, (fx, fy) in frames.items():
        atlas.alpha_composite(assets[aid][0].image(), (fx, fy))
    return atlas, frames


def main(out_dir):
    os.makedirs(os.path.join(out_dir, "modules"), exist_ok=True)
    assets = catalog.build()

    atlas, frames = pack(assets)
    atlas.save(os.path.join(out_dir, "tileset.png"), optimize=True)
    meta = {
        "meta": {
            "name": "Room 01 – The Deep Entrance",
            "name_ar": "الغرفة الأولى – المدخل العميق",
            "image": "tileset.png",
            "size": {"w": atlas.width, "h": atlas.height},
            "tile_size": T,
            "surface_inset_px": catalog.SURFACE_INSET,
            "notes": "anchor=ground pieces are drawn offset_y px lower so they rest on the "
                     "carved floor surface. Light pools (light_*) are meant for additive blending.",
        },
        "frames": {
            aid: {"x": frames[aid][0], "y": frames[aid][1], **{k: v for k, v in m.items() if k != "id"}}
            for aid, (_, m) in assets.items()
        },
        "animations": {
            "bat_fly": {"frames": ["bat_a", "bat_b"], "fps": 8},
            "waterfall": {"frames": ["waterfall_a", "waterfall_b"], "fps": 6},
            "crumble": {"frames": ["crumble_m_0", "crumble_m_1", "crumble_m_2"], "fps": 6},
            "barrier_break": {"frames": ["barrier_0", "barrier_1", "barrier_2"], "fps": 10},
        },
        "autotile": {
            "description": "Pick by which of the 4 neighbours are solid (n,e,s,w); when all four are "
                           "solid, an empty diagonal selects the matching inner corner.",
            "rules": {"".join("1" if b else "0" for b in k): v for k, v in terrain.CARDINAL.items()},
            "inner_corners": {"nw": "ground_inner_tl", "ne": "ground_inner_tr",
                              "sw": "ground_inner_bl", "se": "ground_inner_br"},
        },
    }
    with open(os.path.join(out_dir, "tileset.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    for aid, (spr, _) in assets.items():
        spr.image().save(os.path.join(out_dir, "modules", f"{aid}.png"), optimize=True)

    room_spr, grid = room.compose(assets)
    room_img = room_spr.image()
    upscale(room_img, 2).save(os.path.join(out_dir, "room01_preview.png"), optimize=True)
    sheet.annotate(upscale(room_img, 2), scale=2).save(os.path.join(out_dir, "room01_annotated.png"),
                                                       optimize=True)
    room_map = {
        "tile_size": T, "width": room.W, "height": room.H,
        "legend": {"#": "solid ground (autotile)", "u": "island underside", "=": "crumbling platform",
                   "^": "red crystal hazard", "-": "plank bridge", "C": "crate", "H": "ladder",
                   "B": "breakable barrier", ".": "empty"},
        "grid": ["".join(r) for r in grid],
        "terrain": [{"id": a, "x": x, "y": y} for a, x, y in room.terrain_layer(grid)],
        "decor_back": [{"id": a, "x": c * T, "y": r * T + dy, "flip": fl} for a, c, r, dy, fl in room.BACK_DECOR],
        "decor_front": [{"id": a, "x": c * T, "y": r * T + dy, "flip": fl} for a, c, r, dy, fl in room.FRONT_DECOR],
        "lights": [{"x": round(x), "y": round(y), "radius": r, "color": list(c), "strength": s}
                   for x, y, r, c, s in room.LIGHTS],
        "callouts": [{"text": t, "x": round(c * T), "y": round(r * T), "step": n}
                     for t, c, r, n in room.CALLOUTS],
    }
    with open(os.path.join(out_dir, "room01_map.json"), "w", encoding="utf-8") as f:
        json.dump(room_map, f, ensure_ascii=False, indent=1)

    sh = sheet.build_sheet(assets, room_img)
    sh.convert("RGB").save(os.path.join(out_dir, "asset_sheet.png"), optimize=True)
    print(f"{len(assets)} modules · atlas {atlas.width}x{atlas.height} · sheet {sh.width}x{sh.height} -> {out_dir}")


if __name__ == "__main__":
    default = os.path.join(HERE, "..", "..", "assets", "room01_deep_entrance")
    main(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else default))
