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
is faded out instead of ending in a straight cut. For a glowing effect drawn on
white, such as an explosion, --effect keeps its white-hot middle as solid white;
for a colourless one, such as a grey magic circle, --shading turns its grey into
see-through shading under solid white lines. When a character bursts into light
that fills the video, --glow-from keys the frames from then on as light drawn on
white, see-through as faint as it looks, with the rocks and the like kept solid.
On a green or blue screen the screen's light is taken off the character's edges;
--screen-hue also cuts every pixel of the screen's own hue, --screen-light keeps
light over the screen, such as a spark's glow, see-through, and --uneven-bg copes
with a background that is not quite even, such as a fade from white to green.

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
    # the walk was exported at 960x960 and 24 fps: scale it to the idle's 1080 so the rat keeps its size; its poses
    # are wider, so the canvas is wider, around the same centre (x 498) and bottom (886) for the Bottom pivot
    python3 tools/video_to_spritesheet.py Rat_under_magic_walk_.MP4 assets/sprites/rat_under_magic_walk \
        --name rat_under_magic_walk --scale 1.125 --rect 80 150 916 886 --columns 9 \
        --cut-region 0 635 820 --cut-region 0 673 642 --half --no-full --preview
    # the projectile on its own canvas; its flame trail runs into the left edge of the video, so that side is
    # faded the same way in every frame
    python3 tools/video_to_spritesheet.py Rat_under_magic_projectile_animation.MP4 \
        assets/sprites/rat_under_magic_projectile --name rat_under_magic_projectile --scale 1.125 \
        --rect 0 342 912 718 --columns 8 --fade-side left --edge-fade 160 --keep-enclosed --seal 6 \
        --hold-still 613 472 726 608 --half --no-full --preview
    # same export as the walk; the staff thrust reaches far right, so an even wider canvas around x 498
    python3 tools/video_to_spritesheet.py Rat_under_magic_Cast_Projectile.MP4 assets/sprites/rat_under_magic_cast_projectile \\
        --name rat_under_magic_cast_projectile --scale 1.125 --rect -68 74 1064 886 --columns 9 \\
        --cut-region 0 635 820 --cut-region 0 673 642 --cut-region 1 669 656 --cut-region 1 639 822 \\
        --cut-region 2 671 669 --cut-region 2 642 822 --cut-region 3 643 823 --cut-region 4 646 823 \\
        --half --no-full --preview
    # the explosion the projectile makes: an effect, not a character. It fills the whole video and its shards fly
    # out of every edge, so all four edges are faded the same way in every frame. Its white-hot middle is white like
    # the background: the middle of the ring stays white, the inside of the ring is background, and the white flash
    # at the start opens up from its middle over frames 13-19
    python3 tools/video_to_spritesheet.py Rat_under_magic_2D_magical_impact_explosion_.MP4 \
        assets/sprites/rat_under_magic_impact_explosion --name rat_under_magic_impact_explosion --scale 1.125 \
        --rect 0 0 1080 1080 --columns 9 --fade-side left --fade-side right --fade-side top --fade-side bottom \
        --effect --flash 12 20 --half --no-full --preview
    # the buff: the same export and rat as the cast. The raised staff reaches higher and further right, so the canvas
    # is taller and wider, again around the idle's centre (x 498) and bottom (886). The background seen through the
    # gaps between the staff, the hand and the robe and by the feet was tinted by compression, so it is cut by hand
    python3 tools/video_to_spritesheet.py Rat_Under_Magic_Cast_Buff.MP4 assets/sprites/rat_under_magic_cast_buff \
        --name rat_under_magic_cast_buff --scale 1.125 --rect -46 18 1042 886 --columns 9 \
        --cut-region 0 674 642 --cut-region 0 635 821 --cut-region 1 671 504 --cut-region 1 667 664 \
        --cut-region 2 668 508 --cut-region 3 667 509 --cut-region 4 665 512 --cut-region 5 664 513 \
        --cut-region 6 663 515 --cut-region 8 614 820 --cut-region 10 749 391 --cut-region 13 772 433 \
        --cut-region 14 779 451 --cut-region 14 670 549 --cut-region 15 790 469 --cut-region 15 673 555 \
        --cut-region 17 801 508 --cut-region 17 362 734 --cut-region 17 676 565 --cut-region 18 815 524 \
        --cut-region 18 680 562 --cut-region 25 879 413 --cut-region 27 880 349 --cut-region 28 769 530 \
        --cut-region 29 772 510 --cut-region 31 713 569 --cut-region 33 818 234 --cut-region 34 811 227 \
        --cut-region 70 737 554 \
        --half --no-full --preview
    # the buff's aura, a ring of blue fire: an effect drawn in the same framing as the rat clips, so its canvas keeps
    # the rat's centre (x 498) and reaches below the rat's bottom edge (886) for the aura's base; a custom pivot at
    # y 886 (X 0.5, Y 50/840) puts it around the rat. White inside the faint wisp loops is background (--faint-ring)
    python3 tools/video_to_spritesheet.py Rat_under_magic_buff_attack_effect_.MP4 \
        assets/sprites/rat_under_magic_buff_attack_effect --name rat_under_magic_buff_attack_effect --scale 1.125 \
        --rect 102 96 894 936 --columns 9 --effect --faint-ring 60 --half --no-full --preview
    # the healing effect, a column of green light, made in the same framing: the same centre, and a custom pivot at
    # y 886 (X 0.5, Y 66/840). The white beam down its middle is about as wide as the gaps --effect closes and runs out
    # of the top of the column, so it would be cut as background; a box marks it as part of the effect
    python3 tools/video_to_spritesheet.py Rat_Under_Magic_healing_effect_.MP4 \
        assets/sprites/rat_under_magic_healing_effect --name rat_under_magic_healing_effect --scale 1.125 \
        --rect 186 112 810 952 --columns 9 --effect --keep-white 522 138 563 905 --half --no-full --preview
    # a looping magic circle, grey with white lines and centred in its own video: the canvas is the full width around
    # the centre (540, 540). As solid grey it would be a grey plate on a dark floor, so the grey is see-through shading
    # (--shading). Its glow touches the right edge in the last frames, so that side fades the same way in every frame
    python3 tools/video_to_spritesheet.py Looping_magical_circle_.MP4 assets/sprites/looping_magical_circle \
        --name looping_magical_circle --scale 1.125 --rect 0 352 1080 728 --columns 7 --fade-side right --edge-fade 16 \
        --effect --shading --half --no-full --preview
    # a third character, the soldier rat, on its own canvas (exported like the later rat clips: 960x960, 24 fps). Its
    # sword's white shine touches the background and its eye's shine is ringed by the dark pupil: --shine keeps pale
    # shine solid and cuts only pockets ringed almost all round by dark, --keep-pocket holds the eye's shine,
    # --thin-lines keeps the whiskers, and the pockets that compression tinted are cut by hand
    python3 tools/video_to_spritesheet.py Soldier_Rat.MP4 assets/sprites/soldier_rat --name soldier_rat --scale 1.125 \
        --rect 172 310 832 790 --columns 9 --shine --thin-lines --keep-pocket 580 380 675 465 \
        --cut-region 1 460 592 --cut-region 1 569 695 --cut-region 2 622 608 --cut-region 2 482 561 \
        --cut-region 3 623 611 --cut-region 3 609 586 --cut-region 4 611 588 --cut-region 4 649 694 \
        --cut-region 16 611 718 --cut-region 21 620 671 --cut-region 33 440 657 --cut-region 38 621 626 \
        --cut-region 38 531 687 --cut-region 48 594 694 --cut-region 50 467 525 --cut-region 53 595 678 \
        --cut-region 65 463 502 --cut-region 72 584 738 \
        --half --no-full --preview
    # an enemy, the crystal creature, on its own canvas from a 1168x768 video, at its own scale. The white-hot middle
    # of its eyes is ringed by red and the white flash of the lightning in its crystals is ringed by glow, so
    # --keep-pocket holds them, and --glow-cores keeps the lightning's white core solid with its glow around it
    python3 tools/video_to_spritesheet.py Enemy_Crystal_boom.MP4 assets/sprites/enemy_crystal_boom \
        --name enemy_crystal_boom --rect 116 33 1052 741 --columns 11 --keep-pocket 320 515 610 610 \
        --keep-pocket 620 50 1010 480 --glow-cores --half --no-full --preview
    # the same creature walking, exported at 960x960: its first frame is the boom's first frame, smaller, so the
    # video is scaled x1.6333 (960 -> 1568) to the boom's size, where the boom's (x, y) is at (x + 199, y + 399). The
    # canvas keeps the boom's centre (x 584, here 783) and reaches 24 px below its bottom edge (741, here 1140) for
    # the lowest steps, so a custom pivot at X 0.5, Y 24/800 lines the two up. Nothing in the walk is see-through
    # background, so every enclosed white stays (the shine on its toes and rocks, its crystals' white facets); in
    # its lightning only the white middle of the bolts is solid, and the air between floating sparks is not
    python3 tools/video_to_spritesheet.py Crystal_Golem_walks_.MP4 assets/sprites/crystal_golem_walk \
        --name crystal_golem_walk --scale 1.6333333 --rect 259 364 1307 1164 --columns 11 --keep-enclosed \
        --glow-cores --core-width 7 --half --no-full --preview
    # its attack, exported like the walk (same first frame, same scale). The raised claw, the burst below its feet and
    # the burst running out of the left edge of the video make the canvas much bigger: from the video's left edge, so
    # the boom's bottom centre (783, 1140) is at X 783/1466, Y 146/1168 of it for the custom pivot. The background the
    # arm and the burst close in under the arm in frames 101-103 is cut by hand
    python3 tools/video_to_spritesheet.py Crystal_Golem_attack_.MP4 assets/sprites/crystal_golem_attack \
        --name crystal_golem_attack --scale 1.6333333 --rect 0 118 1466 1286 --columns 11 --keep-enclosed \
        --glow-cores --core-width 7 --cut-region 101 574 933 --cut-region 102 570 949 --cut-region 103 569 976 \
        --half --no-full --preview
    # its death explosion, exported at 1080x1080 and 30 fps: its first frame is the walk's first frame at 1080, so it
    # is scaled x1.4519 (1080 -> 1568) to the same size, where the boom's (x, y) is again at (x + 199, y + 399). The
    # explosion fills the video and runs out of every edge, so the canvas is the whole video (2 px more on the left,
    # so the boom's centre, x 783, is its middle) with all four edges faded, and its 157 frames go into two sheets
    # that fit 8192 px. From frame 110 the golem bursts into light drawn on white (--glow-from)
    python3 tools/video_to_spritesheet.py Death_Explosion_Crystal_Golem.MOV assets/sprites/crystal_golem_death \
        --name crystal_golem_death --scale 1.4518519 --rect -2 0 1568 1568 --columns 10 --fade-side left \
        --fade-side right --fade-side top --fade-side bottom --keep-enclosed --glow-cores --core-width 7 \
        --glow-from 110 --sheet-frames 100 --half --no-full --preview
    # a second enemy, the Vexbat, on its own canvas at its video's own scale (960x960, 24 fps), centred on the bat's
    # head (x 525, y 477 on average: it bobs as it flaps) for the Center pivot. The light highlight lines along its
    # wings' edges touch the background at the tips, so --shine keeps them solid, and --haze cuts the light smudges
    # the compression left in the corners between the wings' parts
    python3 tools/video_to_spritesheet.py Vexbat_idle_.MP4 assets/sprites/vexbat_idle --name vexbat_idle \
        --rect 23 263 1027 691 --columns 8 --shine --haze 30 --half --no-full --preview
    # its attack, exported the same way (its first frame is the idle's first frame): the canvas keeps the idle's
    # centre (525, 477) for the Center pivot and is bigger, as the bat draws back, swoops and strikes down to the
    # right; its wing tips run past the right edge in a few frames, so the last 16 px there fade. The sparks of its
    # strike are warm light that fades like dust (--shine-lines keeps only the thin highlight lines solid, and
    # --glow-cores their white-hot middle), a fang's white is smaller than a gap (--min-pocket), and the slivers of
    # background between an ear and a wing and between the claws, tinted by compression, are cut by hand
    python3 tools/video_to_spritesheet.py Vexbat_attak.MP4 assets/sprites/vexbat_attack --name vexbat_attack \
        --rect 9 3 1041 951 --columns 9 --shine-lines --haze 30 --glow-cores --min-pocket 60 --edge-fade 16 \
        --cut-region 25 573 502 --cut-region 29 434 429 --cut-region 29 429 447 --cut-region 29 434 424 \
        --cut-region 29 432 433 --cut-region 30 429 458 --cut-region 31 429 488 --cut-region 31 428 481 \
        --cut-region 31 433 494 --cut-region 32 430 493 --cut-region 55 670 755 --cut-region 59 637 798 \
        --cut-region 67 616 723 --half --no-full --preview
    # a third enemy, the crystal spider, on its own canvas at its video's own scale (960x960, 24 fps). The clip starts
    # on white and fades to a green screen over frames 1-4, so the background is measured around each pixel
    # (--uneven-bg); on white the light faces of its crystals would fade like dust behind their dark outline, so
    # --outlined keeps them solid; and the gaps between its legs, where compression darkened the green, and the
    # green fringe along its outline are cut by their hue (--screen-hue)
    python3 tools/video_to_spritesheet.py crystal_spider_walk.MP4 assets/sprites/crystal_spider_walk \
        --name crystal_spider_walk --rect 112 190 858 748 --columns 10 --uneven-bg --outlined --screen-hue --half \
        --no-full --preview
    # its attack, exported the same way (its first frame is the walk's first frame): it lunges to the right and a
    # white spark flashes from its claw, so the canvas is wider, around the walk's centre (x 485) and bottom (748) for
    # the Bottom pivot. The spark's rays run past the right edge in two frames, so the last 16 px there fade, and the
    # spark is light over the green screen, so --screen-light keeps its glow see-through instead of a solid halo
    python3 tools/video_to_spritesheet.py crystal_spider_attack.MP4 assets/sprites/crystal_spider_attack \
        --name crystal_spider_attack --rect 10 190 960 748 --columns 7 --uneven-bg --outlined --screen-hue \
        --screen-light --edge-fade 16 --half --no-full --preview
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
SHINE_GAP_DARK = 0.75  # --shine: a pocket's ring must be at least this dark to be cut (a sword's shine is half light)
HAZE_WIDTH = 2         # --haze: pale areas wider than 2x this + 1 px are haze; thinner ones are lines (a highlight)
HAZE_WARM = 12         # --haze: colour this much shorter of blue than of red and green is warm light (sparks) ...
HAZE_WARM_RIM = 0.5    # ... and a pale area this much ringed by warm light is its soft edge, not haze
EFFECT_SEAL = 6        # --effect: white closed in by the effect except for gaps narrower than 2x this is inside it
EFFECT_THIN = 40       # --effect: white inside the effect up to 2x this across is its white-hot middle and stays ...
EFFECT_SPARKLE = 135   # ... and so does wider white ringed by colour at least this strong (a sparkle on a shard)
FLASH_FEATHER = 12     # --flash: px over which the opening flash fades into its hole
SHADING_SURFACE = 30   # --shading: pixels at least this far from the background are the effect's surface ...
SHADING_REACH = 4      # ... a pixel lighter than the surface within this many px is part of a white line ...
SHADING_LINE = 0.5     # ... by as much as it is lighter beyond this share of the surface's shade
GLOW_LIGHT = 150       # --core-width: coloured glow is at least this light (luma) ...
GLOW_SPREAD = 50       # ... and this saturated (brightest minus darkest channel) ...
GLOW_RIM = 0.2         # ... and a glow's white core has at least this share of it right around it
GLOW_EDGE = 2          # --glow-from: px of a solid thing's soft rim, un-mixed from white exactly (no pale halo)
GLOW_GAIN = 2.5        # --glow-from: light is this many times as opaque as the least that shows its colour over white
GLOW_SOFTEN = 2.0      # --glow-from: gaussian sigma (px) on the light's opacity, against the video's compression blocks
GLOW_NECK = 3          # --glow-from: light narrower than 2x this + 1 px (a crack, a bolt) does not let the white in
BG_FIELD_REACH = 40    # --uneven-bg: the background is what the border reaches through colour this close to its own ...
BG_FIELD_SIGMA = 8     # ... and its colour smoothed over this many px (gaussian sigma) is the background at each pixel
SCREEN_SHARE = 0.8     # --screen-hue: colour whose key channel leads by this share of the screen's own lead is screen
SCREEN_LIGHT_FAINT = 0.04  # --screen-light: light rises from the screen's colour toward white by this share or more ...
SCREEN_LIGHT_WARM = 0.6    # ... in both other channels, red by at most this share more (warm light: a spark's yellow
SCREEN_LIGHT_TINT = 0.2    # glow) and the other by at most this much more (a cyan crystal's edge rises in blue) ...
SCREEN_LIGHT_DIM = 32      # ... with the key channel at most this much below the screen's (an outline darkens it) ...
SCREEN_LIGHT_CORE = 0.5    # ... and it reaches the screen and has a part that rises at least this much, 3 px across or
                           # more (a spark's middle; the light fringe sharpening leaves along an outline is thinner)
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


def background_field(rgb):
    """The background colour at each pixel, for a background that is not quite even (--uneven-bg), such as one
    caught in a fade from white to a green screen: the colour of the background around each pixel, smoothed so
    the video's compression noise stays out of it. Far inside the character the border's colour stands in."""
    bg = background_colour(rgb)
    labels, _ = ndi.label(colour_distance(rgb, bg) <= BG_FIELD_REACH, structure=EIGHT)
    # stay clear of the character's soft edge, whose colours are part character
    sample = ndi.binary_erosion(touching_border(labels), EIGHT, iterations=EDGE_BAND, border_value=1)
    weight = ndi.gaussian_filter(sample.astype(np.float64), BG_FIELD_SIGMA)
    field = np.dstack([ndi.gaussian_filter(np.where(sample, rgb[..., c], 0).astype(np.float64), BG_FIELD_SIGMA)
                       for c in range(3)])
    return np.where(weight[..., None] > 1e-3, field / np.maximum(weight, 1e-12)[..., None], bg)


def background_distance(rgb, uneven=False):
    """How far each pixel's colour is from the background: from the border's median colour, or with uneven=True
    from the colour of the background around it (see background_field)."""
    if not uneven:
        return colour_distance(rgb, background_colour(rgb))
    return np.rint(np.abs(rgb.astype(np.float64) - background_field(rgb)).max(axis=2)).astype(np.int16)


def content(rgb, uneven=False):
    """The pixels that are not background. With uneven=True, tiny faint specks the video's compression leaves in an
    uneven background (fewer than 16 px, within 2x BG_TOLERANCE of it) are not content either."""
    dist = background_distance(rgb, uneven)
    solid = dist > BG_TOLERANCE
    if uneven:
        labels, count = ndi.label(solid, structure=EIGHT)
        if count:
            index = np.arange(1, count + 1)
            area = ndi.sum(np.ones(dist.shape), labels, index)
            peak = ndi.maximum(dist, labels, index)
            solid &= ~np.isin(labels, index[(area < 16) & (peak <= 2 * BG_TOLERANCE)])
    return solid


def key_channel(bg):
    """The dominant channel of a green or blue screen, or None for a neutral (e.g. white) background."""
    order = np.argsort(bg)
    return int(order[-1]) if bg[order[-1]] - bg[order[-2]] > 60 else None


def colour_distance(rgb, bg):
    return np.abs(rgb.astype(np.int16) - bg.astype(np.int16)).max(axis=2)


def touching_border(labels):
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return np.isin(labels, np.unique(edge[edge > 0]))


def enclosed_gaps(near_bg, outer_bg, dist, rgb, min_area=20, loose=True, dark_share=0.5):
    """Background pockets the border flood fill cannot reach.

    A pocket is cut out only if it is ringed mostly by dark outline/cloth pixels and
    matches the background colour: almost exactly, or more loosely (compression bleeds
    the colour of saturated cloth into them) when the pocket is big enough and its ring
    dark enough. Pale highlights on horns and claws are slightly off-white
    and half ringed by the light bone around them, and eye shines and glows are ringed
    by light colours, so they are left alone. With loose=False only the near-exact match
    counts (white shine on a sword next to dark fur would pass the loose one), and
    dark_share is the share of the ring that must be dark.
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
        tinted = loose and match <= GAP_LOOSE_MATCH and any(area >= a and dark >= d for a, d in GAP_LOOSE)
        if (match <= GAP_MATCH and dark > dark_share) or tinted:
            gaps[y, x] |= blob
    return gaps


def effect_white(dist, faint=0):
    """Sort the white inside a glowing effect drawn on white (--effect): returns (body, hollow).

    White is also such an effect's hottest colour: the middle of a glowing ring or flame,
    the sparkle on a crystal. White the effect closes in (gaps narrower than 2 * EFFECT_SEAL
    px count as closed) is body when it is at most 2 * EFFECT_THIN px across or ringed by
    strong colour; it stays. Wider white, such as the inside of the ring, is hollow: background,
    or a flash that fades (flash_rim). Open white and the gaps between flying shards are background.
    With faint > 0, closed-in white ringed only by faint colour (median distance from the
    background below faint), such as the inside of a faint wisp loop, is background too; the
    narrow white lines between strokes stay, unless they border such a patch in faint colour.
    """
    solid = dist > BG_TOLERANCE
    pad = EFFECT_SEAL + 2
    closed = ndi.binary_closing(np.pad(solid, pad), structure=disk(EFFECT_SEAL))[pad:-pad, pad:-pad]
    labels, _ = ndi.label(~closed, structure=EIGHT)
    outer = touching_border(labels)
    sealed = closed & ~solid
    pieces, _ = ndi.label(sealed, structure=EIGHT)
    opening = np.unique(pieces[ndi.binary_dilation(outer, EIGHT) & sealed])
    body = sealed & ~np.isin(pieces, opening[opening > 0])
    hollow = np.zeros_like(solid)
    dropped = np.zeros_like(solid)

    def ring_level(blob, y, x):
        ring = ndi.binary_dilation(blob, EIGHT, iterations=3) & ~ndi.binary_dilation(blob, EIGHT) & solid[y, x]
        return np.median(dist[y, x][ring]) if ring.any() else 0.0

    labels, _ = ndi.label(~closed & ~outer, structure=EIGHT)
    for index, region in enumerate(ndi.find_objects(labels), start=1):
        y, x = region
        y = slice(max(y.start - 4, 0), y.stop + 4)
        x = slice(max(x.start - 4, 0), x.stop + 4)
        blob = labels[y, x] == index
        level = ring_level(blob, y, x)
        if level < faint:
            dropped[y, x] |= blob
        elif level >= EFFECT_SPARKLE or ndi.distance_transform_edt(np.pad(blob, 1)).max() <= EFFECT_THIN:
            body[y, x] |= blob
        else:
            hollow[y, x] |= blob
    if dropped.any():
        bordering = np.unique(pieces[ndi.binary_dilation(dropped, EIGHT) & body])
        objects = ndi.find_objects(pieces)
        for index in bordering[bordering > 0]:
            y, x = objects[index - 1]
            y = slice(max(y.start - 4, 0), y.stop + 4)
            x = slice(max(x.start - 4, 0), x.stop + 4)
            piece = pieces[y, x] == index
            if ring_level(piece, y, x) < faint:
                body[y, x] &= ~piece
    return body, hollow


def flash_rim(hollow, weight):
    """Opacity of hollow white while a flash fades out (weight 1 -> 0): it opens up from its
    middle, leaving a rim along its edge that narrows to nothing."""
    depth = ndi.distance_transform_edt(np.pad(hollow, 1))[1:-1, 1:-1]
    labels, count = ndi.label(hollow, structure=EIGHT)
    deepest = np.zeros(count + 1)
    deepest[1:] = ndi.maximum(depth, labels, np.arange(1, count + 1))
    reach = weight * (deepest[labels] + FLASH_FEATHER) - FLASH_FEATHER / 2
    return np.where(hollow, np.clip((reach - depth) / FLASH_FEATHER + 0.5, 0, 1), 0.0)


def glow_core_lines(white, near_bg, rgb, width):
    """The pieces of white that are the white-hot middle of a glowing line, such as a lightning bolt (--core-width):
    at most width px across, with coloured glow right around them. Wider white, or white that fades out through
    pale glow, such as the air between floating sparks, is not a core."""
    luma = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    glow = (luma >= GLOW_LIGHT) & (rgb.max(axis=2).astype(np.int16) - rgb.min(axis=2) >= GLOW_SPREAD)
    labels, _ = ndi.label(white, structure=EIGHT)
    cores = np.zeros_like(white)
    for index, region in enumerate(ndi.find_objects(labels), start=1):
        y, x = region
        y = slice(max(y.start - 4, 0), y.stop + 4)
        x = slice(max(x.start - 4, 0), x.stop + 4)
        blob = labels[y, x] == index
        if 2 * ndi.distance_transform_edt(np.pad(blob, 1)).max() > width:
            continue
        ring = ndi.binary_dilation(blob, EIGHT, iterations=3) & ~ndi.binary_dilation(blob, EIGHT) & ~near_bg[y, x]
        if ring.any() and glow[y, x][ring].mean() >= GLOW_RIM:
            cores[y, x] |= blob
    return cores


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


def light_over_screen(rgb, bg, key, known_bg):
    """Light drawn over a green or blue screen, such as a white spark and its glow: (where, alpha, colour).

    Light is colour on the way from the screen's toward white or a warm tint of it: both
    other channels rise, by about the same share of the way or red ahead, and the key channel
    stays up (a cyan edge rises in blue only, and an outline's soft edge darkens the key
    channel). Light that reaches the screen and has a wide light middle is a glow the screen
    shows through: its opacity is how much of the screen's lead in the key channel is gone
    (a colour-difference key), and its colour is what is left once that much of the screen
    is taken out. bg is the background colour, or one per pixel (background_field).
    """
    others = [c for c in range(3) if c != key]
    rgb = rgb.astype(np.float64)
    bg = np.broadcast_to(np.asarray(bg, np.float64), rgb.shape)
    rise = (rgb[..., others] - bg[..., others]) / np.maximum(255 - bg[..., others], 1)
    tilt = rise[..., 0] - rise[..., 1]
    light = ((rise.min(axis=2) >= SCREEN_LIGHT_FAINT) & (tilt <= SCREEN_LIGHT_WARM) & (tilt >= -SCREEN_LIGHT_TINT)
             & (rgb[..., key] >= bg[..., key] - SCREEN_LIGHT_DIM))
    labels, _ = ndi.label(light, structure=EIGHT)
    cored = labels[ndi.binary_erosion(light & (rise.min(axis=2) >= SCREEN_LIGHT_CORE), EIGHT)]
    touched = labels[light & ndi.binary_dilation(known_bg, EIGHT)]
    glow = np.isin(labels, np.intersect1d(cored, touched))
    screen = bg[..., key] - bg[..., others].max(axis=2)
    lead = rgb[..., key] - rgb[..., others].max(axis=2)
    alpha = np.clip(1 - lead / np.maximum(screen, 1), 0, 1)
    colour = np.clip(bg + (rgb - bg) / np.maximum(alpha, 1e-3)[..., None], 0, 255) / 255
    return glow, alpha, colour


CUT_REGION_TOLERANCES = (30, 20, 15, 10)  # a hand-picked region may be this far off the background colour ...
CUT_REGION_MAX = 20000     # ... and at most this many px; a tighter tolerance is tried when a pale line joins it
                           # to the background around the character (none at all means the spot was wrong)


def disk(radius):
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return x * x + y * y <= radius * radius


def key_frame(rgb, cut_points=(), cut_regions=(), cut_gaps=True, seal=0, effect=False, flash=0.0, faint=0,
              keep_white=(), shading=False, shine=False, keep_pockets=(), thin_lines=False, glow_cores=False,
              core_width=0, haze=0, shine_lines=False, min_pocket=20, uneven_bg=False, outlined=False,
              screen_hue=False, screen_light=False):
    """Return an RGBA frame with the background removed.

    cut_points are (x, y) spots, in this frame's coordinates, where any enclosed
    background pocket is cut out even if the automatic gap test kept it.
    cut_regions are (x, y) spots inside a pale patch that compression has tinted too
    far from the background for the gap test; the whole connected patch is cut out.
    cut_gaps=False keeps every enclosed pale area, for effects such as a fireball
    whose white-hot glow sits inside the flames. seal > 0 also keeps pale areas that
    reach the outside only through openings narrower than 2 * seal px; they stay as a
    faint glow instead of being flood-filled as background.
    effect=True is for a glowing effect such as an explosion, whose white-hot middle
    is white like the background (see effect_white). flash (1 -> 0) then also keeps
    its wider hollow white, solid at 1 and opening up from the middle as it drops, and
    faint > 0 drops white closed in only by faint colour (see effect_white). keep_white
    boxes (x0, y0, x1, y1) mark white that is part of the effect wherever it reaches,
    such as a light beam that runs out of the tip of a light column. shading=True is for
    a colourless effect such as a grey magic circle (see shading_cell). shine=True is for a
    character with polished metal, whose white shine (the edge of a sword) is solid: no pale
    area is made see-through as a trail, and only pockets that match the background exactly
    and are ringed almost all round by dark are cut out. keep_pockets boxes (x0, y0, x1, y1)
    hold white pockets that are part of the character, such as the shine in an eye: a
    pocket that reaches into one is never cut out. thin_lines=True keeps thin dark lines
    that lie wholly in the soft edge, such as whiskers (see min_alpha). glow_cores=True is
    for a character with a glow, such as lightning on crystals: white the cut leaves
    inside the character is the glow's white-hot core and stays solid, and the pale glow
    around it turns solid toward it instead of fading like dust. core_width > 0 narrows
    that to the white middle of glowing lines, such as lightning bolts (see glow_core_lines):
    other white left inside, such as the air between sparks, fades with its glow as before.
    haze > 0 also takes pale areas within haze of the background colour that touch the
    background, are wider than a thin line and are not warm light (the soft glow of sparks)
    as background: the video's compression leaves such smudges in the corners between a
    wing's parts, while thin highlight lines along the character's edges stay (with
    shine=True, solid). shine_lines=True keeps only such thin pale lines solid, like
    shine=True does all pale areas, while wider pale areas that touch the background still
    fade as trails (the soft glow of sparks, motion blur). min_pocket is the smallest
    enclosed pocket, in px, that the gap test may cut out (smaller white is a detail, such
    as a fang). uneven_bg=True compares each pixel with the colour of the background around it
    instead of one colour for the whole frame, for a background that is not quite even (see
    background_field). outlined=True is for a character with a dark outline all round: pale areas
    inside it, such as light crystal faces on a white background, stay solid even right behind
    the outline; only pale areas that touch the background itself (motion blur) fade as trails.
    screen_hue=True is for a green or blue screen: every pixel of nearly the screen's own hue is
    background, even where compression darkened or tinted it past the gap test: small gaps between
    legs, and the fringe that would turn into a grey haze along the outline once despilled.
    screen_light=True keeps light drawn over such a screen, such as a white spark's glow, see-through by
    how much of the screen shows through it (see light_over_screen) instead of a solid tinted halo.
    """
    bg = background_colour(rgb)
    dist = background_distance(rgb, uneven_bg)
    if seal:
        solid = dist > BG_TOLERANCE
        pad = seal + 2
        closed = ndi.binary_closing(np.pad(solid, pad), structure=disk(seal))[pad:-pad, pad:-pad]
        sealed = closed & ~solid
        rgb = rgb.copy()
        rgb[sealed] = np.clip(bg - (BG_TOLERANCE + 5) * np.sign(bg - 127.5), 0, 255).astype(np.uint8)
        dist = colour_distance(rgb, bg)

    near_bg = dist <= BG_TOLERANCE
    keep = rim = None
    if effect:
        body, hollow = effect_white(dist, faint)
        rim = flash_rim(hollow, flash) if flash > 0 else np.zeros(dist.shape)
        keep = body | (rim > 0)
        for x0, y0, x1, y1 in keep_white:
            keep[max(y0, 0):y1, max(x0, 0):x1] |= near_bg[max(y0, 0):y1, max(x0, 0):x1]
        if shading:
            return shading_cell(rgb, bg, dist, keep, rim)
        known_bg = near_bg & ~keep
    else:
        labels, _ = ndi.label(near_bg, structure=EIGHT)
        outer_bg = touching_border(labels)
        known_bg = outer_bg
        if cut_gaps:
            gaps = enclosed_gaps(near_bg, outer_bg, dist, rgb, min_area=min_pocket, loose=not shine,
                                 dark_share=SHINE_GAP_DARK if shine else 0.5)
            if keep_pockets:
                labels, _ = ndi.label(gaps, structure=EIGHT)
                held = np.zeros_like(gaps)
                for x0, y0, x1, y1 in keep_pockets:
                    held[max(y0, 0):y1, max(x0, 0):x1] = True
                reached = np.unique(labels[held & gaps])
                gaps &= ~np.isin(labels, reached[reached > 0])
            known_bg = outer_bg | gaps
        key = key_channel(bg)
        if screen_hue and key is not None:
            # on a green or blue screen, its own hue is background even where compression darkened or tinted it: in
            # the gaps between legs, and in the fringe it leaves along the outline
            others = [c for c in range(3) if c != key]
            lead = rgb[..., key].astype(np.float64) - rgb[..., others].max(axis=2)
            known_bg = known_bg | (lead >= SCREEN_SHARE * (bg[key] - bg[others].max()))
        if haze:
            pale = ~known_bg & (dist <= haze)
            wide = ndi.binary_opening(pale, structure=disk(HAZE_WIDTH))
            labels, _ = ndi.label(wide, structure=EIGHT)
            touched = np.unique(labels[ndi.binary_dilation(known_bg, EIGHT) & wide])
            # warm light (the yellow glow of sparks) is short of blue most; a pale area ringed by it is its soft edge
            short = bg - rgb.astype(np.float64)
            warm = (short[..., 2] - np.maximum(short[..., 0], short[..., 1]) >= HAZE_WARM) & (dist > haze)
            smudge = np.zeros_like(pale)
            objects = ndi.find_objects(labels)
            for index in touched[touched > 0]:
                y, x = objects[index - 1]
                y = slice(max(y.start - 4, 0), y.stop + 4)
                x = slice(max(x.start - 4, 0), x.stop + 4)
                blob = labels[y, x] == index
                ring = ndi.binary_dilation(blob, EIGHT, iterations=3) & ~blob & ~known_bg[y, x] & (dist[y, x] > haze)
                if not (ring.any() and warm[y, x][ring].mean() >= HAZE_WARM_RIM):
                    smudge[y, x] |= blob
            # the opening also trims the smudge's own tapering tips (into the corner); grow it back over them
            smudge = ndi.binary_dilation(smudge, EIGHT, iterations=HAZE_WIDTH + 1, mask=pale)
            known_bg = known_bg | smudge
    if cut_points:
        labels, _ = ndi.label(near_bg & ~known_bg, structure=EIGHT)
        for x, y in cut_points:
            spot = labels[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4]
            known_bg |= np.isin(labels, np.unique(spot[spot > 0]))
    for x, y in cut_regions:
        for tolerance in CUT_REGION_TOLERANCES:
            labels, _ = ndi.label(dist <= tolerance, structure=EIGHT)
            region = labels == labels[y, x] if labels[y, x] else None
            if region is not None and region.sum() <= CUT_REGION_MAX:
                known_bg |= region
                break
        else:
            print(f"  --cut-region at ({x},{y}) is not on a small pale patch; skipped")
    if glow_cores and keep is None:
        keep = near_bg & ~known_bg
        if core_width:
            keep = glow_core_lines(keep, near_bg, rgb, core_width)

    from_bg = ndi.distance_transform_edt(~known_bg)
    band = ~known_bg & (from_bg <= EDGE_BAND)
    light = ~known_bg & (dist < TRAIL_LIGHTNESS) & (from_bg <= (0 if shine else TRAIL_REACH))
    if keep is not None:
        light &= ~keep  # white-hot parts are solid, not a faint trail
    if shine_lines:
        # thin pale lines (a highlight along an edge) are solid; wider pale areas (and their fringes) are trails
        wide = ndi.binary_opening(light, structure=disk(HAZE_WIDTH))
        light &= ndi.binary_dilation(wide, EIGHT, iterations=HAZE_WIDTH + 1, mask=light)
    if outlined:
        # only pale areas that touch the background itself are trails; those behind a dark outline are solid
        labels, _ = ndi.label(light, structure=EIGHT)
        reached = np.unique(labels[ndi.binary_dilation(known_bg, EIGHT) & light])
    else:
        labels, _ = ndi.label(light | band, structure=EIGHT)
        reached = np.unique(labels[band])
    pale = light & np.isin(labels, reached[reached > 0])
    unknown = band | pale

    trimap = np.where(known_bg, 0.0, np.where(unknown, 0.5, 1.0))
    image = rgb.astype(np.float64) / 255.0
    alpha = np.clip(estimate_alpha_cf(image, trimap), 0.0, 1.0)
    alpha[known_bg] = 0.0
    alpha[trimap == 1.0] = 1.0
    if thin_lines:
        alpha = np.where(known_bg, 0.0, np.maximum(alpha, min_alpha(rgb, bg)))
    # Pale areas that reach the background without crossing an outline (dust, motion
    # blur) are see-through in the clip: cap their opacity by their contrast with the
    # background so they do not turn into solid white patches on a dark backdrop.
    cap = dist / TRAIL_LIGHTNESS
    if keep is not None and keep.any():
        # in an effect, pale glow between the background and a white-hot part turns solid toward that part;
        # white that is not such a part itself (the air between sparks, with --core-width) stays see-through
        from_keep = ndi.distance_transform_edt(~keep)
        cap = np.maximum(cap, np.where(near_bg, 0.0, from_bg / np.maximum(from_bg + from_keep, 1e-6)))
    alpha[pale] = np.minimum(alpha[pale], cap[pale])
    # Those trails also carry the video's 8x8 compression blocks; soften them so the
    # edge does not stair-step. Crisp outlines (the thin edge band) are untouched.
    trail = pale & (from_bg > EDGE_BAND)
    if trail.any():
        zone = ndi.binary_dilation(trail, EIGHT, iterations=4)
        alpha[zone] = ndi.gaussian_filter(alpha, TRAIL_SOFTEN)[zone]
    if rim is not None:
        fading = rim > 0
        alpha[fading] *= rim[fading]
    key = key_channel(bg)
    glow = None
    if screen_light and key is not None:
        glow, glow_alpha, glow_colour = light_over_screen(rgb, background_field(rgb) if uneven_bg else bg, key,
                                                          known_bg)
        alpha[glow] = glow_alpha[glow]
    alpha = drop_specks(alpha)
    foreground = estimate_foreground_ml(image, alpha)
    if key is not None:
        foreground = despill(foreground, key)
    if glow is not None:
        foreground[glow] = glow_colour[glow]  # the screen is already taken out of the light's colour

    out = np.dstack([np.clip(foreground, 0, 1) * 255, alpha * 255])
    out = np.rint(out).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out


def shading_cell(rgb, bg, dist, keep, rim):
    """Key a colourless effect drawn on white, such as a grey magic circle with white lines.

    Over white, a grey pixel looks the same whether it is solid grey or see-through dark
    shading; as solid grey the circle would turn into a grey plate on a dark background.
    So the grey is see-through dark shading, and white lines are solid white on top: the
    white the effect closes in (see effect_white), plus pixels clearly lighter than the
    surface around them (thin lines and their soft edges), which get part of their
    lightness as white. Every pixel still gives the video's colour over the background, so
    over white it looks the same, and on a dark background the white lines show.
    """
    image = rgb.astype(np.float32)
    back = np.asarray(bg, np.float32)
    shade_of = np.clip(((back - image) / np.maximum(back, 1)).max(axis=2), 0, 1)
    # the area the effect covers (its surface, with gaps up to 24 px closed), and how dark
    # that surface is around each pixel
    pad = 14
    surface = ndi.binary_closing(np.pad(dist > SHADING_SURFACE, pad), structure=disk(12))[pad:-pad, pad:-pad]
    surface = ndi.binary_fill_holes(surface)
    around = ndi.grey_dilation(np.where(surface, shade_of, 0), footprint=disk(SHADING_REACH))
    lighter = np.where(surface & (around > 0), 1 - shade_of / np.maximum(around, 1e-6), 0)
    line = np.minimum(np.clip((lighter - SHADING_LINE) / (1 - SHADING_LINE), 0, 1), 1 - shade_of)
    weight = np.where(rim > 0, rim, 1.0)
    line = np.where(keep, weight * (1 - shade_of), line)
    shade = np.where(line < 1, shade_of / np.maximum(1 - line, 1e-6), 0.0)
    shade[keep & (weight < 1)] = 0
    shade_colour = back - (back - image) / np.maximum(shade_of[..., None], 1e-6)
    shade_colour[line > 0] = 0
    alpha = line + (1 - line) * shade
    colour = 255 * line[..., None] + shade_colour * ((1 - line) * shade)[..., None]
    colour /= np.maximum(alpha[..., None], 1e-6)
    alpha[(dist <= BG_TOLERANCE) & ~keep] = 0
    out = np.rint(np.dstack([np.clip(colour, 0, 255), np.clip(alpha, 0, 1) * 255])).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out


def min_alpha(rgb, bg):
    """The least opacity each pixel can have and still show its colour over the background.

    Even a black (or white) character pixel must cover the background this much to make
    the colour seen in the video. Matting the soft edge can let a thin dark line that lies
    wholly in it, such as a whisker away from the face, fade out completely; this floor
    keeps it as dark as the video shows it.
    """
    image = rgb.astype(np.float64)
    back = np.asarray(bg, np.float64)
    darker = (back - image) / np.maximum(back, 1)
    lighter = (image - back) / np.maximum(255 - back, 1)
    return np.clip(np.maximum(darker, lighter).max(axis=2), 0.0, 1.0)


def glow_cell(rgb, core_width=0):
    """Key a frame of light drawn on white, such as an explosion of light (--glow-from).

    Over white, a pale pixel looks the same whether it is a solid pale thing or faint light over the
    background, and an explosion's light fills wide areas, inside its rings too. So everything the
    background reaches through light colour (wider than a crack or a bolt, which would let it into the
    character through its outline) is light, with its colour's hue: GLOW_GAIN times the least opacity that
    shows its colour over white (see min_alpha), less the compression noise near white (BG_TOLERANCE)
    and softened against the video's compression blocks. White turns clear, faint light stays faint,
    strong cyan turns solid, and the light still shows on a dark background. What dark outlines wall in
    (rocks, the character, the shine on them) stays solid, its soft rim against the light is un-mixed from
    white exactly (no pale halo on a dark background), and so is the white middle of glowing lines up to
    core_width px across (see glow_core_lines).
    """
    image = rgb.astype(np.float64)
    white = np.full(3, 255.0)
    dist = colour_distance(rgb, white)
    near_bg = dist <= BG_TOLERANCE
    light = image @ np.array([0.299, 0.587, 0.114]) >= GLOW_LIGHT
    labels, _ = ndi.label(ndi.binary_opening(light, structure=disk(GLOW_NECK)), structure=EIGHT)
    reached = touching_border(labels)
    solid = ndi.binary_erosion(~reached, EIGHT, iterations=GLOW_EDGE, border_value=1)
    if core_width:
        solid |= glow_core_lines(near_bg & reached, near_bg, rgb, core_width)
    least = min_alpha(rgb, white)
    colour = white - (white - image) / np.maximum(np.minimum(GLOW_GAIN * least, 1.0), 1e-6)[..., None]
    noise = BG_TOLERANCE / 255
    alpha = np.minimum(GLOW_GAIN * np.maximum(least - noise, 0) / (1 - noise), 1.0)
    rim = ndi.binary_dilation(solid, EIGHT, iterations=GLOW_EDGE + 1) & ~solid & ~light
    lit = (~solid & ~rim).astype(np.float64)
    soft = ndi.gaussian_filter(alpha * lit, GLOW_SOFTEN) / np.maximum(ndi.gaussian_filter(lit, GLOW_SOFTEN), 1e-6)
    alpha = np.where(solid, 1.0, np.where(rim, least, soft))
    colour = np.where(rim[..., None], white - (white - image) / np.maximum(least, 1e-6)[..., None], colour)
    alpha = drop_specks(alpha)
    colour = np.where(solid[..., None], image, colour)
    out = np.rint(np.dstack([np.clip(colour, 0, 255), alpha * 255])).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out


def union_box(frames, uneven=False):
    x0 = y0 = 10**9
    x1 = y1 = -1
    for rgb in frames:
        ys, xs = np.nonzero(content(rgb, uneven))
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


def border_contact(frames, uneven=False):
    """Which video edges the clip's content touches, and in which frames."""
    sides = {}
    for i, rgb in enumerate(frames):
        solid = content(rgb, uneven)
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


def track_x(frames, box, search=150):
    """Horizontal position of the content in box (video px) in each frame, relative to frame 0."""
    x0, y0, x1, y1 = box
    ref = frames[0][y0:y1, x0:x1].astype(np.float32).mean(axis=2)
    ref -= ref.mean()
    offsets = []
    for rgb in frames:
        grey = rgb.astype(np.float32).mean(axis=2)
        best, best_dx = -np.inf, 0
        for dx in range(max(-search, -x0), min(search, grey.shape[1] - x1) + 1):
            patch = grey[y0:y1, x0 + dx:x1 + dx]
            patch = patch - patch.mean()
            score = float((patch * ref).sum()) / (float(np.linalg.norm(patch)) + 1e-6)
            if score > best:
                best, best_dx = score, dx
        offsets.append(best_dx)
    return np.array(offsets)


def build_sheet(cells, columns):
    h, w = cells[0].shape[:2]
    rows = -(-len(cells) // columns)
    sheet = np.zeros((rows * h, columns * w, 4), np.uint8)
    for i, cell in enumerate(cells):
        r, c = divmod(i, columns)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = cell
    return sheet, rows


def sheet_json(name, image_file, count, columns, w, h, fps, sheet_size, first=0):
    duration = round(1000 / fps)
    frames = []
    for i in range(count):
        r, c = divmod(i, columns)
        frames.append({
            "filename": f"{name}_{first + i:02d}",
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
    parser.add_argument("--fade-side", choices=("left", "right", "top", "bottom"), action="append", default=[],
                        help="fade that video edge in every frame, not only where content touches it, e.g. for a "
                             "flame trail that only sometimes reaches the edge (repeatable)")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="resize the video first, e.g. to match another clip of the same character shot at a "
                             "different resolution (--rect is then in the resized video's px)")
    parser.add_argument("--cut-pocket", type=int, nargs=2, action="append", default=[], metavar=("X", "Y"),
                        help="video px where an enclosed background pocket must always be cut out (repeatable)")
    parser.add_argument("--keep-pocket", type=int, nargs=4, action="append", default=[],
                        metavar=("X0", "Y0", "X1", "Y1"),
                        help="video px box where white pockets are part of the character, such as the shine in an "
                             "eye ringed by the dark pupil: a pocket that reaches into it is never cut (repeatable)")
    parser.add_argument("--cut-region", type=int, nargs=3, action="append", default=[], metavar=("FRAME", "X", "Y"),
                        help="in that one frame, cut out the pale patch around video px X,Y (repeatable)")
    parser.add_argument("--hold-still", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
                        help="video px box around a part that drifts sideways during the clip (e.g. a projectile's "
                             "orb); it is tracked and every frame is shifted so it stays where it is in the last frame")
    parser.add_argument("--shine", action="store_true",
                        help="the character has polished metal (a sword): its white shine stays solid instead of "
                             "being made see-through like dust, and only pockets that match the background exactly "
                             "and are ringed almost all round by dark are cut out")
    parser.add_argument("--glow-cores", action="store_true",
                        help="the character has a glow, such as lightning on crystals: white left inside it is the "
                             "glow's white-hot core and stays solid, and the glow around it turns solid toward it")
    parser.add_argument("--core-width", type=int, default=0, metavar="PX",
                        help="with --glow-cores or --glow-from: only white at most PX px across with coloured glow "
                             "right around it (the white middle of a lightning bolt) is a core; wider white, or white "
                             "that fades out through pale glow (the air between floating sparks), stays see-through")
    parser.add_argument("--glow-from", type=int, metavar="FRAME",
                        help="from this frame on, the clip is light drawn on white, such as an explosion of light "
                             "that fills the video: what the background reaches through light colour is keyed as "
                             "light, see-through as faint as it looks, and what dark outlines wall in stays solid "
                             "(--core-width also keeps the white middle of thin glowing lines solid)")
    parser.add_argument("--screen-hue", action="store_true",
                        help="on a green or blue screen: every pixel of nearly the screen's own hue is background, "
                             "even where the video's compression darkened or tinted it (small gaps between legs, "
                             "the fringe along the outline); not for a character with parts of the screen's hue")
    parser.add_argument("--screen-light", action="store_true",
                        help="on a green or blue screen: light drawn over the screen, such as a white spark and its "
                             "glow, is see-through by how much of the screen shows through it, with the screen's "
                             "colour taken out of it, instead of a solid halo tinted by the screen")
    parser.add_argument("--outlined", action="store_true",
                        help="the character has a dark outline all round: pale areas inside it (light crystal faces "
                             "on a white background) stay solid even right behind the outline; only pale areas that "
                             "touch the background itself, such as motion blur, fade like dust")
    parser.add_argument("--uneven-bg", action="store_true",
                        help="the background is not quite even, e.g. the clip fades from a white background to a "
                             "green screen: compare each pixel with the colour of the background around it instead "
                             "of one colour for the whole frame")
    parser.add_argument("--min-pocket", type=int, default=20, metavar="PX",
                        help="smallest enclosed background pocket, in px, that is cut out automatically; smaller "
                             "white ringed by dark stays, e.g. raise it so a fang's white is not taken for a gap")
    parser.add_argument("--shine-lines", action="store_true",
                        help="thin pale lines along the character's edges, such as the highlight along a wing's "
                             "edge, stay solid where they touch the background; wider pale areas still fade like "
                             "dust, such as the soft glow of sparks (--shine keeps all pale areas solid)")
    parser.add_argument("--haze", type=int, default=0, metavar="DIST",
                        help="pale smudges the video's compression leaves next to the character, such as in the "
                             "corners between a wing's parts: pale areas within DIST of the background colour that "
                             "touch the background and are wider than a thin line are background (thin highlight "
                             "lines along the edges stay)")
    parser.add_argument("--thin-lines", action="store_true",
                        help="keep thin dark lines that lie wholly in the soft edge, such as whiskers: no pixel is "
                             "made more see-through than its colour in the video allows")
    parser.add_argument("--keep-enclosed", action="store_true",
                        help="never cut enclosed pale areas as background (effects whose white glow sits inside)")
    parser.add_argument("--seal", type=int, default=0, metavar="PX",
                        help="also keep pale glow that reaches the outside only through openings narrower than 2*PX")
    parser.add_argument("--effect", action="store_true",
                        help="the clip is a glowing effect on white, such as an explosion: white that the effect "
                             "closes in (the middle of a glowing ring or flame, sparkles) stays solid white, while "
                             "wide white such as the inside of a ring is background")
    parser.add_argument("--keep-white", type=int, nargs=4, action="append", default=[],
                        metavar=("X0", "Y0", "X1", "Y1"),
                        help="with --effect: white inside this video px box is part of the effect, e.g. a light "
                             "beam that opens onto the background at the tip of a light column (repeatable)")
    parser.add_argument("--shading", action="store_true",
                        help="with --effect, for a colourless effect such as a grey magic circle with white lines: "
                             "grey becomes see-through dark shading (exactly the video over white) and the white "
                             "lines stay solid, so on a dark background the lines show instead of a grey plate")
    parser.add_argument("--faint-ring", type=int, default=0, metavar="DIST",
                        help="with --effect: white closed in only by faint colour (median distance from the "
                             "background below DIST), such as the inside of a faint wisp loop, is background too")
    parser.add_argument("--flash", type=int, nargs=2, metavar=("FROM", "TO"),
                        help="with --effect: the wide white inside the effect is a flash, solid up to frame FROM, "
                             "then opening up from its middle until it is gone at frame TO")
    parser.add_argument("--half", action="store_true", help="also write a 50%% sheet")
    parser.add_argument("--no-full", action="store_true",
                        help="skip the full-resolution sheet (for long clips whose full sheet is too big for a texture)")
    parser.add_argument("--sheet-frames", type=int, default=0, metavar="N",
                        help="put at most N frames in each sheet: a longer clip is split into numbered sheets "
                             "(_part1, _part2, ...), each with its own JSON, e.g. to keep each within 8192 px")
    parser.add_argument("--frames", action="store_true", help="also write every frame as its own PNG")
    parser.add_argument("--preview", action="store_true", help="also write an animated GIF preview")
    args = parser.parse_args()

    frames, fps = read_frames(args.video)
    if args.scale != 1:
        size = (round(frames[0].shape[1] * args.scale), round(frames[0].shape[0] * args.scale))
        frames = [np.asarray(Image.fromarray(f).resize(size, Image.LANCZOS)) for f in frames]
    height, width = frames[0].shape[:2]
    box = union_box(frames, args.uneven_bg)
    rect = tuple(args.rect) if args.rect else cell_rect(box, args.margin)
    left, top, right, bottom = rect
    w, h = right - left, bottom - top
    print(f"{len(frames)} frames @ {fps:g} fps, {width}x{height}; character box {box}; cell {w}x{h} at ({left},{top})")
    if box[0] < left or box[1] < top or box[2] > right or box[3] > bottom:
        raise SystemExit(f"the clip reaches {box}, outside the cell {rect} - frames would be cut; widen --rect")
    contact = border_contact(frames, args.uneven_bg) if args.edge_fade > 0 else {}
    if args.hold_still:
        hold = track_x(frames, args.hold_still)
        print(f"  holding the tracked part still: it drifts {hold[-1] - hold[0]:+d} px over the clip")
    key = key_channel(background_colour(frames[0]))
    if key is not None:
        print(f"  {'RGB'[key]} screen background: removing its colour spill from the character")
    for side, hits in contact.items():
        print(f"  content runs out of the video on the {side} in frames {hits}; fading the last {args.edge_fade} px")
    if args.flash:
        flash_from, flash_to = args.flash
        if not args.effect or flash_from >= flash_to:
            raise SystemExit("--flash needs --effect and FROM < TO")
        print(f"  white flash: solid up to frame {flash_from}, opening up until it is gone at frame {flash_to}")
    if (args.faint_ring or args.keep_white or args.shading) and not args.effect:
        raise SystemExit("--faint-ring, --keep-white and --shading need --effect")
    if args.core_width and not args.glow_cores and args.glow_from is None:
        raise SystemExit("--core-width needs --glow-cores or --glow-from")
    if args.glow_from is not None:
        print(f"  from frame {args.glow_from} on: light drawn on white (an explosion's light)")

    os.makedirs(args.out_dir, exist_ok=True)
    cells = []
    for i, rgb in enumerate(frames):
        flash = float(np.clip((flash_to - i) / (flash_to - flash_from), 0, 1)) if args.flash else 0.0
        if args.glow_from is not None and i >= args.glow_from:
            cell = glow_cell(crop(rgb, rect), args.core_width)
        else:
            cell = key_frame(crop(rgb, rect), [(x - left, y - top) for x, y in args.cut_pocket],
                             [(x - left, y - top) for f, x, y in args.cut_region if f == i], not args.keep_enclosed,
                             args.seal, args.effect, flash, args.faint_ring,
                             [(x0 - left, y0 - top, x1 - left, y1 - top) for x0, y0, x1, y1 in args.keep_white],
                             args.shading, args.shine,
                             [(x0 - left, y0 - top, x1 - left, y1 - top) for x0, y0, x1, y1 in args.keep_pocket],
                             args.thin_lines, args.glow_cores, args.core_width, args.haze, args.shine_lines,
                             args.min_pocket, args.uneven_bg, args.outlined, args.screen_hue, args.screen_light)
        sides = {side for side, hits in contact.items() if i in hits} | set(args.fade_side)
        if sides:
            cell = fade_edges(cell, rect, width, height, sides, args.edge_fade)
        if args.hold_still:
            # line every frame up with the last one; the gap left behind is transparent
            shift = int(hold[-1] - hold[i])
            moved = np.zeros_like(cell)
            if shift >= 0:
                moved[:, shift:] = cell[:, :w - shift]
            else:
                moved[:, :w + shift] = cell[:, -shift:]
            if np.abs(shift) and (cell[:, w - shift:] if shift > 0 else cell[:, :-shift]).any():
                raise SystemExit(f"frame {i}: shifting by {shift} px pushes content out of the cell - widen --rect")
            cell = moved
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
    per_sheet = args.sheet_frames or len(cells)
    starts = range(0, len(cells), per_sheet)
    for suffix, sheet_cells, cw, ch in outputs:
        for part, first in enumerate(starts, start=1):
            stem = f"{args.name}_spritesheet{suffix}" + (f"_part{part}" if len(starts) > 1 else "")
            part_cells = sheet_cells[first:first + per_sheet]
            sheet, rows = build_sheet(part_cells, args.columns)
            image_file = f"{stem}.png"
            Image.fromarray(sheet, "RGBA").save(os.path.join(args.out_dir, image_file), optimize=True)
            meta = sheet_json(args.name, image_file, len(part_cells), args.columns, cw, ch, fps,
                              (sheet.shape[1], sheet.shape[0]), first)
            with open(os.path.join(args.out_dir, f"{stem}.json"), "w") as fh:
                json.dump(meta, fh, indent=2)
            print(f"{image_file}: {sheet.shape[1]}x{sheet.shape[0]}, {args.columns}x{rows} grid of {cw}x{ch}"
                  + (f", frames {first}-{first + len(part_cells) - 1}" if len(starts) > 1 else ""))
    if args.preview:
        save_preview(os.path.join(args.out_dir, f"{args.name}_preview.gif"), half, fps)
        print(f"{args.name}_preview.gif written")


if __name__ == "__main__":
    main()
