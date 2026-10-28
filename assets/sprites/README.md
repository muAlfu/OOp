# Character sprite sheets

Every sheet here keeps **all frames of its video, in order**, with the background removed (transparent PNG).
All animations share one canvas: each frame is the same 1080×756 area of the 1080×1080 video (x 0–1080, y 135–891).
The jump is the exception: it goes higher, so its frames are taller (y 39–891) but end at the same bottom edge.
The whole character fits in every frame, and it sits in the same place in every animation.
Use the `Bottom` pivot for all of them and the character stays put when the animation changes.

| Animation | Frames | Grid | Full sheet (frame 1080×756) | Half sheet (frame 540×378) |
| --- | --- | --- | --- | --- |
| `triple_claw_combo/` | 37 | 7 columns × 6 rows (last 5 cells empty) | 7560×4536 | 3780×2268 |
| `heavy_claw_attack/` | 34 | 7 columns × 5 rows (last cell empty) | 7560×3780 | 3780×1890 |
| `final_heavy_claw_attack/` | 92 | 10 columns × 10 rows (last 8 cells empty) | not made (would be 10800×7560) | 5400×3780 |
| `jump_hallow/` | 66 | 10 columns × 7 rows (last 4 cells empty) | not made (would be 10800×5964) | 5400×2982, **frame 540×426** |

A second character, the rat mage, has its own canvas (x 142–854, y 70–886 of the video, 712×816):

| Animation | Frames | Grid | Full sheet (frame 712×816) | Half sheet (frame 356×408) |
| --- | --- | --- | --- | --- |
| `rat_under_magic_idle/` | 183 | 16 columns × 12 rows (last 9 cells empty) | not made (would be 11392×9792) | 5696×4896 |
| `rat_under_magic_walk/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 3762×3312, **frame 418×368** |
| `rat_under_magic_cast_projectile/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 5094×3654, **frame 566×406** |
| `rat_under_magic_projectile/` | 73, **24 fps** | 8 columns × 10 rows (last 7 cells empty) | not made (kept at the idle's scale) | 3648×1880, **frame 456×188** |
| `rat_under_magic_impact_explosion/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 4860×4860, **frame 540×540** |
| `rat_under_magic_cast_buff/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 4896×3906, **frame 544×434** |
| `rat_under_magic_buff_attack_effect/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 3564×3780, **frame 396×420** |
| `rat_under_magic_healing_effect/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the idle's scale) | 2808×3780, **frame 312×420** |
| `looping_magical_circle/` | 73, **24 fps** | 7 columns × 11 rows (last 4 cells empty) | not made (kept at the idle's scale) | 3780×2068, **frame 540×188** |

The projectile (the fireball the rat casts) has its own canvas, at the same scale as the rat (×1.125). In the video
the ball slowly drifts right (62 px over the clip); every frame is shifted so the ball stays in one place and the
animation loops without a jump. Its flame trail runs into the left edge of the video, so the trail's last 160 px fade
out the same way in every frame. The white glow between the ball and the flames is kept as a soft, see-through glow.
Use a custom pivot at the centre of the ball: **X 0.82, Y 0.47**.

The impact explosion (the projectile hitting) is an effect, not a character, so its canvas is the whole video, at the
same scale as the rest of the rat (×1.125, 1080×1080, half 540×540). Its shards fly out of every edge of the video, so
the outer 96 px fade out the same way in every frame. The effect is drawn on white and its hottest parts are white too:
the white middle of the glowing ring and of the flames stays solid white, so the ring still glows on a dark background,
and so do the sparkles on the shards; the empty inside of the ring is see-through. The white flash in the middle of the
burst is solid up to frame 12 (counting from 0), then opens up from its centre and is gone at frame 20, when the
inside of the ring is clear. Use the `Center` pivot: the ring is centred in the frame.

The buff attack effect is an aura: a ring of blue fire around the rat. It was made in the same framing as the rat
clips, so its canvas keeps the rat's centre (x 498) and reaches 50 px below the rat's bottom edge for the aura's base
(×1.125, 792×840, half 396×420). Its custom pivot **X 0.5, Y 0.0595** is the spot the rat's `Bottom` pivot sits on: put
the aura at the rat's position, behind the rat, and it surrounds the rat with its base around the feet. It loops: the
last frame leads straight back into the first. The inside of the aura is see-through, the white-hot middle of the
flames stays white, and inside the faint swirling wisps only their cyan lines stay.

The healing effect is a column of green light with golden ribbons and a glowing ring at its base. It was made in the
same framing too, so its canvas keeps the rat's centre and reaches 66 px below the rat's bottom edge for the ring
(×1.125, 624×840, half 312×420). Its custom pivot **X 0.5, Y 0.0786** is the spot the rat's `Bottom` pivot sits on.
Put it at the rat's position: behind the rat, the rat stands in the light with the ring around its feet; in front, the
column covers the rat, because its light is solid, so lower its opacity (the Sprite Renderer's `Color` alpha) if you
draw it in front. The white beam down the middle of the column stays white along its whole length. The clip does not
loop seamlessly: its last frame does not lead back into the first (the ribbons and sparkles jump), so play it once per
heal; looped, it jumps every 3 seconds.

The looping magical circle is a flat circle on the ground, seen at an angle: grey with white lines and runes, turning.
It is centred in its own video, so its canvas is the video's full width around the centre (×1.125 like the rat clips,
1080×376, half 540×188), and the `Center` pivot is the centre of the circle: put it at the rat's feet, behind the rat.
Over white, grey looks the same whether it is solid grey or see-through dark shading, and as solid grey the circle
would turn into a grey plate on a dark floor. So its grey is see-through dark shading and its lines are solid white:
on a dark or coloured floor the white lines show with a light shadow under the circle, and over white it looks exactly
like the video. It is meant to loop; the last frame leads back into the first with a small jump (about three frames'
worth of turning). Its faint glow touches the right edge of the video in the last 3 frames, so the last 16 px on the
right fade out the same way in every frame.

The walk video was exported at 960×960 and 24 fps. Its frames are scaled ×1.125 so the rat is the same size as in
the idle. The walk's frames are wider (418×368 at half size) because the tail and staff reach further, but they share
the idle's centre and bottom edge, so with the `Bottom` pivot the rat stays in place between idle and walk. Play the
walk at 24 fps. The cast was exported the same way (960×960, 24 fps, scaled ×1.125); the staff thrust reaches far to
the right, so its frames are wider still (566×406 at half size), again around the idle's centre and bottom edge. The
clip shows the casting motion; there is no projectile flying in it. The buff (the rat raises its staff high and opens
its other hand) was exported the same way too; the raised staff reaches higher and further right, so its frames are
taller and wider (544×434 at half size), again around the idle's centre and bottom edge. In frames 54–60 (counting
from 0) the rat holds the pose, so they look almost the same; they are kept so the timing matches the video.

A third character, the soldier rat (armour, sword and shield), has its own canvas: x 172–832, y 310–790 of its video
scaled ×1.125 like the later rat clips (660×480, half 330×240). Use the `Bottom` pivot.

| Animation | Frames | Grid | Full sheet (frame 660×480) | Half sheet (frame 330×240) |
| --- | --- | --- | --- | --- |
| `soldier_rat/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (kept at the rat clips' scale) | 2970×2160 |

The clip starts with the soldier facing the viewer and turning into its walk (frames 0–5), then walks on the spot. The
walk repeats every 24 frames: frames 47–70 loop without a jump, so use those 24 for a looping walk; the whole clip,
looped, jumps from the last frame back to the first. The white shine on the sword's edge and in the eye, and the
whiskers, are kept; the background seen through the gaps between the sword, the legs, the arms and the cloth is cut
out (where the video's compression tinted it, by hand).

An enemy, the crystal creature, has its own canvas too: x 116–1052, y 33–741 of its 1168×768 video, at the video's
own scale (936×708, half 468×354). Use the `Bottom` pivot (the walk, the attack and the death: the custom pivots
below).

| Animation | Frames | Grid | Full sheet (frame 936×708) | Half sheet (frame 468×354) |
| --- | --- | --- | --- | --- |
| `enemy_crystal_boom/` | 121, **24 fps** | 11 columns × 11 rows (every cell used) | not made (would be 10296×7788) | 5148×3894 |
| `crystal_golem_walk/` | 121, **24 fps** | 11 columns × 11 rows (every cell used) | not made (kept at the boom's scale) | 5764×4400, **frame 524×400** |
| `crystal_golem_attack/` | 121, **24 fps** | 11 columns × 11 rows (every cell used) | not made (kept at the boom's scale) | 8063×6424, **frame 733×584** |
| `crystal_golem_death/` | 157, **30 fps**, in 2 sheets | part 1 (frames 0–99): 10 × 10; part 2 (frames 100–156): 10 × 6 (last 3 cells empty) | not made (kept at the boom's scale) | 7850×7840 and 7850×4704, **frame 785×784** |

From frame 72 its eyes close and lightning crackles through its crystals; around frame 90 the eyes open again. The last
four frames (117–120) are the same still frame in the video and are kept so the timing matches. The clip does not loop:
its last frame does not lead back into the first, so play it once. The white-hot middle of the eyes, the white flash of
the lightning inside the crystals and the crystals' white facets stay solid; the glow around the lightning fades out
over the background.

The walk is the same creature (its clip calls it the crystal golem). It was exported at 960×960 and smaller: its
first frame is the boom's first frame at a smaller size. Its frames are scaled ×1.633 (960 → 1568) so the golem is
the same size as in the boom. It sways and steps further than it moves in the boom, and the sparks of its lightning
fly higher, so its canvas is bigger (1048×800, half 524×400): around the boom's centre, and reaching 24 px (12 px at
half size) below the boom's bottom edge, because its lowest steps go a little lower than its feet in the boom. Use a
custom pivot at the boom's bottom edge, **X 0.5, Y 0.03**; then the golem stands in the same place when it switches
between walk and boom. The whole clip does not loop seamlessly: from the last frame back to the first it jumps a
little. Frames 48–108 (61 frames) loop smoothly: the step from frame 108 back to frame 48 is no bigger than the steps
inside the clip. The shine on its toes and rocks and the white facets of its crystals stay; in its lightning, the
white middle of the bolts stays solid, and the white between the sparks floating in the air is see-through.

The attack was exported like the walk (its first frame is the walk's first frame), so it is scaled ×1.633 too. The
golem powers up (lightning on its crystals, frames 37–75), raises its claw high and slams it down to its left: the
fist hits the ground at frame 96 (counting from 0), with a burst of blue lightning. The raised claw, the burst that
spreads below its feet and the burst's run to the left edge of the video make the canvas much bigger (1466×1168,
half 733×584): from the video's left edge to x 1466 and from y 118 to 1286 of the scaled video. The burst runs out
of the video's left edge in frames 99–103, so its last 96 px there fade out. Use a custom pivot at the boom's bottom
edge, **X 0.5341, Y 0.125**. The clip ends close to its first pose but not exactly, so going back to the walk there
is a small jump. The shine on the claw, toes and eyes and the white facets of the crystals stay; the white-hot middle
of the burst stays white, the white between floating sparks is see-through, and so is the background under the arm
in frames 101–103, which the arm and the burst close in (cut by hand).

The death explosion was exported at 1080×1080 and 30 fps; its first frame is the walk's first frame at 1080 instead
of 960, so it is scaled ×1.452 (1080 → 1568), to the same size again. Lightning builds up in the golem and debris
flies; from frame 110 (counting from 0) a sphere of light grows around it, the golem bursts into rings of cyan light
and rock fragments that fly out of every edge of the video, and the last frames are nearly empty. The explosion fills
the whole video, so the canvas is the whole scaled video (1570×1568 with 2 px more on the left, half 785×784), and
all four edges fade out the same way in every frame. 157 frames that big do not fit in one 8192 texture, so the
sheet is split in two: part 1 has frames 0–99 and part 2 frames 100–156. Slice both the same way, then select the
sprites of part 1 and then part 2 together and make one animation of them. Use a custom pivot at the boom's bottom
edge, **X 0.5, Y 0.273**. Over white, the explosion's light looks the same whether it is solid or faint light over
the background, so from frame 110 on it is see-through about as faint as it looks: the empty inside of the rings is
clear, the faintest haze (the video's compression noise next to white) is dropped, and on a dark background the
rings and the light still show. The rocks, the golem's body and the white middle of thin glowing lines stay solid,
with their dark edges and no pale halo. It does not loop: play it once, at 30 fps.

A second enemy, the Vexbat (a bat), has its own canvas: x 23–1027, y 263–691 of its 960×960 video, at the video's
own scale (1004×428, half 502×214).

| Animation | Frames | Grid | Full sheet (frame 1004×428) | Half sheet (frame 502×214) |
| --- | --- | --- | --- | --- |
| `vexbat_idle/` | 73, **24 fps** | 8 columns × 10 rows (last 7 cells empty) | not made (would be 8032×4280) | 4016×2140 |
| `vexbat_attack/` | 73, **24 fps** | 9 columns × 9 rows (last 8 cells empty) | not made (would be 9288×8532) | 4644×4266, **frame 516×474** |

The bat hovers in place, flapping, and bobs up and down about 56 px as it flaps. The canvas is centred on the
head's average position, so use the `Center` pivot: the head stays around the sprite's position and the bob plays
as in the video. The whole clip, looped, jumps a little from the last frame back to the first; frames 1–52 (52
frames, two flaps) loop without a jump, so use those for a looping idle. The white-hot middle of the eyes, the
fangs and the light highlight lines along the wings' edges stay solid; the light smudges the video's compression
left in the corners between the wings' parts (by the claws on the wings and between the feet) are cut out.

The attack was exported the same way, and its first frame is the idle's first frame. Its canvas is bigger
(1032×948, x 9–1041, y 3–951; half 516×474), because the bat draws back, swoops and strikes down to the right, but
it has the same centre as the idle's (x 525, y 477 of the video), so with the `Center` pivot the attack starts
exactly where the idle has the bat. It draws back (frames 10–30, getting smaller as if further away), spreads its
wings and swoops (31–50), and strikes with its claws in frames 51–55, where sparks fly from them (the hit is at
frame 52, counting from 0); then it flaps back up. It ends about 60 px to the right of and 100 px below where it
started (30 and 50 px at half size), so going back to the idle the bat jumps, unless the game moves it. In frames
51, 59–61 and 66–69 its wing tips run past the right edge of the video, so that part of the wing was never
recorded; the last 16 px there fade out instead of ending in a straight cut. The sparks' soft glow is see-through
and their white-hot middle solid; the eyes, the fangs and the highlight lines along the wings' edges stay; the
background in the slivers between an ear and a wing (frames 25–32) and between the claws (frames 55, 59 and 67),
tinted by the video's compression, is cut by hand.

A third enemy, the crystal spider, has its own canvas too: x 112–858, y 190–748 of its 960×960 video, at the video's
own scale (746×558, half 373×279). Use the `Bottom` pivot.

| Animation | Frames | Grid | Full sheet (frame 746×558) | Half sheet (frame 373×279) |
| --- | --- | --- | --- | --- |
| `crystal_spider_walk/` | 97, **24 fps** | 10 columns × 10 rows (last 3 cells empty) | not made (would be 7460×5580) | 3730×2790 |
| `crystal_spider_attack/` | 97, **24 fps** | 7 columns × 14 rows (last cell empty) | not made (would be 6650×7812) | 3325×3906, **frame 475×279** |

The spider walks in place. The clip starts on a white background that fades to a green screen over frames 1–4
(counting from 0); every frame is cut out against its own background, so all 97 frames look alike whatever the
background was. The walk does not repeat exactly: looped as a whole it jumps from the last frame to the first, and
the smoothest loop, frames 41–72 (32 frames), still has a small hitch. The white highlights on the crystals stay
solid; the background seen through the gaps between the legs is cut out, also where the video's compression darkened
its green, and the green screen's light is taken off the edges. In frames 50–57 the claws' motion blur stays as a
soft, see-through smear.

The attack was exported the same way, and its first frame is the walk's first frame. Its canvas is wider (950×558,
x 10–960, y 190–748; half 475×279), because a white spark flashes from its claw out to the right edge of the video,
but it has the same centre (x 485) and bottom edge (748) as the walk's, so with the `Bottom` pivot the attack starts
exactly where the walk has the spider. The spider crouches (frames 8–19, counting from 0), raises its front legs
(20–42), turns to the right and strikes with a front claw in frames 43–46, where the spark flashes from the claw's
tip, stays turned, low and with its legs spread until about frame 63, and then turns back and stands up (64–84). It
ends close to the pose it started in but not exactly in it, so going back to the walk the legs jump a little. In
frames 44 and 45 the spark's rays run past the right edge of the video, so the last 16 px there fade out. The spark
is light over the green screen: its white middle is solid and its glow see-through, so it shows as light on any
background instead of a halo tinted by the screen.

- Frames go left to right, top to bottom: frame `i` is at column `i % columns`, row `i / columns`.
- Play at 30 fps (33 ms per frame), except the rat clips after the idle (walk, cast, projectile, explosion, buff,
  aura, healing and magic circle), the soldier rat, the crystal enemy's boom, walk and attack, the Vexbat and the
  crystal spider: 24 fps (42 ms). The crystal golem's death is 30 fps again. The JSON files carry the right duration.
- Each folder also has the frame rectangles as JSON (Aseprite / TexturePacker "JSON Array" format) and a GIF preview
  on a dark background. The GIF is only for viewing, not for the game.
- `heavy_claw_attack`: in frames 22–24 (counting from 0) the dust from the strike runs past the right edge of the
  video, so that part of the dust was never recorded. It fades out toward that edge instead of ending in a straight cut.
  The character itself is complete in every frame.
- `final_heavy_claw_attack`: 92 frames is too many for a full-resolution sheet that a game can load as one texture, so
  it only has the half-size sheet, at the same scale as the other half sheets. Every 5th frame repeats the one before
  it, because the video was converted from 24 to 30 fps. The repeats are kept so the timing matches the video.
  In frames 62–67 (counting from 0) a few fur tips of the cape cross the left edge of the video; the last 8 px there
  are faded.
- `jump_hallow`: the jump rises above the shared canvas, so this sheet's canvas is taller: x 0–1080, y 39–891
  (1080×852, half 540×426). It has the same bottom edge and width as the others, so with the `Bottom` pivot the
  character still stands in the same place. The clip was shot on a green screen; the green light that spilled onto
  the character (claws, skull, body) is removed. The body and cape in the mid-air frames stay darker and more
  olive/orange than in the other animations, because that is how the video lights them.
- `rat_under_magic_idle`: a slow idle, so many neighbouring frames look almost the same; all are kept so the
  timing matches the video. The red sparks around the staff are kept.
- Gaps where the background shows through the character (between cloak and staff, claw and leg, inside the
  staff head) are cut out. Small pale highlights on horns and claws stay.

## Unity

1. Drop the PNG into `Assets`.
2. Inspector: **Texture Type** `Sprite (2D and UI)`, **Sprite Mode** `Multiple`, **Max Size** at least the sheet's
   larger side: `4096` for the 3780-wide half sheets, `vexbat_idle`, `crystal_spider_walk` and
   `crystal_spider_attack`, `8192` for `final_heavy_claw_attack`, `jump_hallow`, `rat_under_magic_idle`,
   `rat_under_magic_cast_projectile`, `rat_under_magic_impact_explosion`, `rat_under_magic_cast_buff`,
   `enemy_crystal_boom`, `crystal_golem_walk`, `crystal_golem_attack`, both `crystal_golem_death` sheets,
   `vexbat_attack` and the full sheets. The default 2048 shrinks the sheet. Apply.
3. **Sprite Editor → Slice**: **Type** `Grid By Cell Size`, **Pixel Size** `540 × 378` (half) or `1080 × 756` (full),
   except `jump_hallow`: `540 × 426`, the rat idle: `356 × 408`, the rat walk: `418 × 368`, the rat cast: `566 × 406`,
   the projectile: `456 × 188`, the explosion: `540 × 540`, the buff: `544 × 434`, the aura: `396 × 420`, the healing:
   `312 × 420`, the magic circle: `540 × 188`, the soldier rat: `330 × 240`, the crystal enemy's boom: `468 × 354`,
   its walk: `524 × 400`, its attack: `733 × 584` and its death: `785 × 784`, the Vexbat's idle: `502 × 214` and its
   attack: `516 × 474`, and the crystal spider's walk: `373 × 279` and its attack: `475 × 279`. **Pivot** `Bottom`
   (the projectile: `Custom Pivot` X 0.82, Y 0.47; the explosion, the magic circle and the Vexbat: `Center`; the aura:
   `Custom Pivot` X 0.5, Y 0.0595; the healing: `Custom Pivot` X 0.5, Y 0.0786; the crystal golem's walk:
   `Custom Pivot` X 0.5, Y 0.03, its attack: `Custom Pivot` X 0.5341, Y 0.125, and its death: `Custom Pivot` X 0.5,
   Y 0.273). Slice, then Apply. Empty cells at the end are skipped.
4. Select the sprites, drag them into the scene to make the animation, and set **Sample Rate** to `30`
   (`24` for the rat walk, cast, projectile, explosion, buff, aura, healing, magic circle, the soldier rat, the
   crystal enemy's boom, walk and attack, the Vexbat and the crystal spider; the golem's death stays at `30`).

## Java

```java
BufferedImage sheet = ImageIO.read(new File("assets/sprites/heavy_claw_attack/heavy_claw_attack_spritesheet_half.png"));
int w = 540, h = 378, columns = 7, count = 34;
BufferedImage[] frames = new BufferedImage[count];
for (int i = 0; i < count; i++) {
    frames[i] = sheet.getSubimage((i % columns) * w, (i / columns) * h, w, h);
}
// current frame at 30 fps: frames[(int) (elapsedMillis * 30 / 1000) % count]
```

To regenerate a sheet or add another clip of this character, use `tools/video_to_spritesheet.py` with
`--rect 0 135 1080 891`, so the new animation shares the same canvas. The commands are in the script's docstring.
