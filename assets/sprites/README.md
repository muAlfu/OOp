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

- Frames go left to right, top to bottom: frame `i` is at column `i % columns`, row `i / columns`.
- Play at 30 fps (33 ms per frame), except the rat clips after the idle (walk, cast, projectile, explosion, buff,
  aura, healing and magic circle): 24 fps (42 ms). The JSON files carry the right duration.
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
   larger side: `4096` for the 3780-wide half sheets, `8192` for `final_heavy_claw_attack`, `jump_hallow`,
   `rat_under_magic_idle`, `rat_under_magic_cast_projectile`, `rat_under_magic_impact_explosion`,
   `rat_under_magic_cast_buff` and the full sheets. The default 2048 shrinks the sheet. Apply.
3. **Sprite Editor → Slice**: **Type** `Grid By Cell Size`, **Pixel Size** `540 × 378` (half) or `1080 × 756` (full),
   except `jump_hallow`: `540 × 426`, the rat idle: `356 × 408`, the rat walk: `418 × 368`, the rat cast:
   `566 × 406`, the projectile: `456 × 188`, the explosion: `540 × 540`, the buff: `544 × 434`, the aura: `396 × 420`,
   the healing: `312 × 420` and the magic circle: `540 × 188`. **Pivot** `Bottom` (the projectile: `Custom Pivot`
   X 0.82, Y 0.47; the explosion and the magic circle: `Center`; the aura: `Custom Pivot` X 0.5, Y 0.0595; the healing:
   `Custom Pivot` X 0.5, Y 0.0786). Slice, then Apply. Empty cells at the end are skipped.
4. Select the sprites, drag them into the scene to make the animation, and set **Sample Rate** to `30`
   (`24` for the rat walk, cast, projectile, explosion, buff, aura, healing and magic circle).

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
