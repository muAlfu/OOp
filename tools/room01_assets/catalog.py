"""Registry of every module on the sheet, grouped by section.

collision: solid | one_way | hazard | breakable | trigger | none
anchor:    how the piece is placed in a level
           grid    – fills its cells exactly
           ground  – stands on a floor; draw 3px lower so it sits on the
                     carved surface (offset_y = 3)
           ceiling – hangs from the cell above
           free    – placed anywhere (fx, characters, light pools)
"""
from functools import partial

import props as P
import terrain
from palette import GLOW_COOL, GLOW_RED, GLOW_WARM

SURFACE_INSET = 3


def _ground(name):
    return lambda: terrain.render_ground(terrain.CANON[name])


# (section_id, title_en, title_ar, [(id, fn, en, ar, collision, anchor)])
SECTIONS = [
    ("terrain", "Solid ground · autotile", "أرض ثابتة · بلاط تلقائي", [
        (n, _ground(n), n.replace("ground_", "").replace("_", " ").upper(), ar, "solid", "grid")
        for n, ar in [
            ("ground_tl", "زاوية علوية يسرى"), ("ground_t", "سطح"), ("ground_tr", "زاوية علوية يمنى"),
            ("ground_inner_tl", "زاوية داخلية"), ("ground_inner_tr", "زاوية داخلية"),
            ("ground_l", "جدار أيسر"), ("ground_c", "حشوة"), ("ground_r", "جدار أيمن"),
            ("ground_inner_bl", "زاوية داخلية"), ("ground_inner_br", "زاوية داخلية"),
            ("ground_bl", "سقف أيسر"), ("ground_b", "سقف"), ("ground_br", "سقف أيمن"),
            ("ledge_l", "حافة يسرى"), ("ledge_m", "حافة"), ("ledge_r", "حافة يمنى"),
            ("column_t", "عمود - رأس"), ("column_m", "عمود"), ("column_b", "عمود - قاعدة"),
            ("block", "كتلة مفردة"),
        ]
    ]),
    ("islands", "Floating island underside", "أسفل الجزر المعلقة", [
        ("under_l", partial(P.underside, "l"), "UNDER L", "أسفل يسار", "none", "grid"),
        ("under_m", partial(P.underside, "m"), "UNDER M", "أسفل وسط", "none", "grid"),
        ("under_r", partial(P.underside, "r"), "UNDER R", "أسفل يمين", "none", "grid"),
        ("under_s", partial(P.underside, "s"), "UNDER S", "أسفل مفرد", "none", "grid"),
        ("stalactite_s", partial(P.stalactite, "small"), "STALACTITE", "نوازل صغيرة", "none", "ceiling"),
        ("stalactite_l", partial(P.stalactite, "large"), "STALACTITE L", "نوازل كبيرة", "none", "ceiling"),
    ]),
    ("crumble", "Crumbling platform · 3 states", "منصة متداعية · ٣ حالات", [
        (f"crumble_{k}_{s}", partial(P.crumble, k, s), f"{k.upper()} · {lbl}", ar, "one_way", "grid")
        for s, lbl, ar in [(0, "INTACT", "سليمة"), (1, "CRACK", "تتشقق"), (2, "FALL", "تنهار")]
        for k in ("l", "m", "r")
    ] + [("crumble_debris", P.debris, "DEBRIS FX", "فتات", "none", "free")]),
    ("hazards", "Hazards & breakables", "مخاطر وعوائق", [
        ("hazard_a", partial(P.hazard, "a"), "RED CRYSTAL A", "بلور مؤذٍ", "hazard", "grid"),
        ("hazard_b", partial(P.hazard, "b"), "RED CRYSTAL B", "بلور مؤذٍ", "hazard", "grid"),
        ("barrier_0", partial(P.barrier, 0), "BARRIER", "حاجز سليم", "breakable", "ground"),
        ("barrier_1", partial(P.barrier, 1), "BARRIER HIT", "حاجز متصدع", "breakable", "ground"),
        ("barrier_2", partial(P.barrier, 2), "BARRIER BROKEN", "حاجز مكسور", "none", "ground"),
    ]),
    ("wood", "Wooden structures", "هياكل خشبية", [
        ("post_top", partial(P.post, "top"), "POST TOP", "رأس عمود", "none", "grid"),
        ("post_mid", partial(P.post, "mid"), "POST", "عمود", "none", "grid"),
        ("post_base", partial(P.post, "base"), "POST BASE", "قاعدة عمود", "none", "grid"),
        ("beam_l", partial(P.beam, "l"), "BEAM L", "عارضة", "none", "grid"),
        ("beam_m", partial(P.beam, "m"), "BEAM M", "عارضة", "none", "grid"),
        ("beam_r", partial(P.beam, "r"), "BEAM R", "عارضة", "none", "grid"),
        ("brace", P.brace, "X-BRACE", "دعامة متقاطعة", "none", "grid"),
        ("bridge_l", partial(P.bridge, "l"), "BRIDGE L", "جسر", "one_way", "grid"),
        ("bridge_m", partial(P.bridge, "m"), "BRIDGE M", "جسر", "one_way", "grid"),
        ("bridge_r", partial(P.bridge, "r"), "BRIDGE R", "جسر", "one_way", "grid"),
        ("rail_l", partial(P.rail, "l"), "RAIL L", "درابزين", "none", "grid"),
        ("rail_m", partial(P.rail, "m"), "RAIL M", "درابزين", "none", "grid"),
        ("rail_r", partial(P.rail, "r"), "RAIL R", "درابزين", "none", "grid"),
        ("crate", P.crate, "CRATE", "صندوق", "solid", "grid"),
        ("ladder_top", partial(P.ladder, "top"), "LADDER TOP", "سلّم", "trigger", "grid"),
        ("ladder_mid", partial(P.ladder, "mid"), "LADDER", "سلّم", "trigger", "grid"),
        ("sign_exit", P.sign_arrow, "EXIT SIGN", "لافتة المخرج", "none", "ground"),
    ]),
    ("lights", "Lights & crystals", "إضاءة وبلورات", [
        ("lantern_hanging", partial(P.lantern, "hanging"), "LANTERN HANG", "فانوس معلق", "none", "ceiling"),
        ("lantern_wall", partial(P.lantern, "wall"), "LANTERN WALL", "فانوس جداري", "none", "grid"),
        ("lantern_stand", partial(P.lantern, "standing"), "LANTERN STAND", "فانوس أرضي", "none", "ground"),
        ("light_warm", partial(P.light_cookie, GLOW_WARM), "LIGHT WARM", "ضوء دافئ", "none", "free"),
        ("light_cool", partial(P.light_cookie, GLOW_COOL), "LIGHT COOL", "ضوء بارد", "none", "free"),
        ("light_red", partial(P.light_cookie, GLOW_RED), "LIGHT RED", "وهج أحمر", "none", "free"),
        ("crystal_small", partial(P.crystal, "small"), "CRYSTAL S", "بلورة صغيرة", "none", "ground"),
        ("crystal_large", partial(P.crystal, "large"), "CRYSTAL L", "بلورة كبيرة", "none", "ground"),
        ("crystal_ceiling", partial(P.crystal, "ceiling"), "CRYSTAL CEIL", "بلورة سقف", "none", "ceiling"),
        ("crystal_wall", partial(P.crystal, "wall"), "CRYSTAL WALL", "بلورة جدار", "none", "grid"),
        ("vine_top", partial(P.vine, "top"), "VINE TOP", "متسلقة", "none", "ceiling"),
        ("vine_mid", partial(P.vine, "mid"), "VINE", "متسلقة", "none", "grid"),
        ("vine_end", partial(P.vine, "end"), "VINE END", "متسلقة", "none", "grid"),
    ]),
    ("interact", "Interactables & characters", "عناصر تفاعلية وشخصيات", [
        ("save_banner", P.save_banner, "SAVE BANNER", "راية الحفظ", "trigger", "ground"),
        ("save_banner_on", partial(P.save_banner, True), "SAVE · ACTIVE", "راية مفعّلة", "trigger", "ground"),
        ("reward_small", partial(P.reward, "small"), "REWARD", "مكافأة", "trigger", "ground"),
        ("reward_challenge", partial(P.reward, "challenge"), "CHALLENGE REWARD", "مكافأة التحدي", "trigger", "ground"),
        ("bat_nest", P.bat_nest, "BAT NEST", "موطن الخفافيش", "none", "ceiling"),
        ("player_slime", P.slime, "PLAYER", "اللاعب", "none", "ground"),
        ("bat_a", partial(P.bat, "a"), "BAT · F1", "خفاش", "hazard", "free"),
        ("bat_b", partial(P.bat, "b"), "BAT · F2", "خفاش", "hazard", "free"),
        ("golem", P.golem, "CRYSTAL GOLEM", "حارس البلور", "hazard", "ground"),
    ]),
    ("background", "Background layer", "طبقة الخلفية", [
        ("bg_wall", terrain.bg_wall, "BACK WALL", "جدار خلفي", "none", "grid"),
        ("bg_fence", P.bg_fence, "FAR FENCE", "سياج بعيد", "none", "grid"),
        ("waterfall_top", partial(P.waterfall, "top"), "FALLS TOP", "منبع الشلال", "none", "grid"),
        ("waterfall_a", partial(P.waterfall, "a"), "FALLS · F1", "شلال", "none", "grid"),
        ("waterfall_b", partial(P.waterfall, "b"), "FALLS · F2", "شلال", "none", "grid"),
        ("waterfall_splash", partial(P.waterfall, "splash"), "FALLS SPLASH", "رذاذ", "none", "grid"),
        ("water_surface", partial(P.water, "surface"), "WATER TOP", "سطح الماء", "none", "grid"),
        ("water_body", partial(P.water, "body"), "WATER", "ماء", "none", "grid"),
    ]),
]


def build():
    """Render every module once. Returns {id: (sprite, meta)}."""
    out = {}
    for sec_id, _, _, items in SECTIONS:
        for (aid, fn, en, ar, coll, anchor) in items:
            spr = fn()
            out[aid] = (spr, dict(id=aid, section=sec_id, en=en, ar=ar, collision=coll, anchor=anchor,
                                  w=spr.w, h=spr.h,
                                  offset_y=SURFACE_INSET if anchor == "ground" else 0))
    return out
